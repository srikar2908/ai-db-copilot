"""
planner.py
==========
Full deterministic query plan generation pipeline.

BUG FIXES:
  Bug 2 — Primary table inference used raw semantic score only.
           A table like 'employees' would win over 'departments'
           on the query "show department names" because employees.name
           is an exact column match while departments.dept_name is fuzzy.

           Fix: stated_tables (the user's original target_tables after
           resolution) receive a large STATED_TABLE_BONUS in primary
           table selection. This guarantees the user's intended table
           wins when there is reasonable evidence for it.

  Bug 3 — resolve_target_columns ran with restrict_to_tables=[primary_table]
           AFTER primary_table was wrongly inferred (Bug 2), and with no
           context_tables, so the affinity bonus from semantic_mapper was
           never applied.

           Fix: pass context_tables=stated_tables to ALL semantic resolver
           calls. The affinity bonus in semantic_mapper.find_best_column_match
           then pulls columns from stated tables upward in the ranking.

  Threading: context_tables is now threaded through:
    - resolve_target_columns
    - resolve_conditions
    - resolve_group_by
    - resolve_order_by
"""

from __future__ import annotations

from app.models.state import (
    ExtractedIntent,
    QueryPlan,
    SchemaContext,
)

from app.core.schema.semantic_mapper import (
    combined_score,
    resolve_conditions,
    resolve_group_by,
    resolve_joins,
    resolve_order_by,
    resolve_table_name,
    resolve_target_columns,
)

from app.core.schema.relationship_reasoner import (
    rewrite_relationship_conditions,
)

from app.core.schema.join_resolver import repair_joins

from app.core.schema.table_expander import expand_missing_tables


# =========================================================
# STATED-TABLE BONUS
# Applied in primary-table selection when a table was
# explicitly stated by the user (via LLM intent extraction).
# Must be large enough to override a pure column-match score
# difference, but not so large that it ignores the column
# evidence entirely.
# =========================================================

_STATED_TABLE_BONUS = 0.50


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _get_all_valid_columns(
    tables: list[str],
    schema_context: SchemaContext,
) -> set[str]:
    valid: set[str] = set()
    for table in tables:
        valid.update(schema_context.tables.get(table, []))
    return valid


def _extract_join_tables(joins: list[dict]) -> list[str]:
    tables: list[str] = []
    for join in joins:
        for key in ("left_table", "right_table"):
            t = join.get(key)
            if t and t not in tables:
                tables.append(t)
    return tables


# =========================================================
# VALIDATE TABLES
# =========================================================

def validate_tables(
    tables: list[str],
    schema_context: SchemaContext,
) -> None:
    valid_tables = set(schema_context.tables.keys())
    invalid = [t for t in tables if t not in valid_tables]
    if invalid:
        raise ValueError(f"Invalid tables: {invalid}")


# =========================================================
# VALIDATE COLUMNS
# =========================================================

def validate_columns(
    tables: list[str],
    columns: list[str],
    schema_context: SchemaContext,
) -> None:
    if columns == ["*"]:
        return

    _AGG_PREFIXES = ("avg_", "sum_", "count_", "min_", "max_")
    valid_columns = _get_all_valid_columns(tables, schema_context)
    invalid_columns = []

    for column in columns:
        if not column or column == "*":
            continue

        lowered = column.lower()
        if any(lowered.startswith(p) for p in _AGG_PREFIXES):
            continue

        base_column = column.split(".")[-1] if "." in column else column
        if base_column not in valid_columns:
            invalid_columns.append(column)

    if invalid_columns:
        raise ValueError(f"Invalid columns: {invalid_columns}")


# =========================================================
# VALIDATE CONDITIONS
# =========================================================

def validate_conditions(
    tables: list[str],
    conditions: list[dict],
    schema_context: SchemaContext,
) -> None:
    valid_columns = _get_all_valid_columns(tables, schema_context)
    for condition in conditions:
        column = condition.get("column")
        if not column:
            continue
        base_column = column.split(".")[-1] if "." in column else column
        if base_column not in valid_columns:
            raise ValueError(f"Invalid condition column: {column}")


# =========================================================
# VALIDATE JOINS
# =========================================================

def validate_joins(
    joins: list[dict],
    schema_context: SchemaContext,
) -> None:
    valid_tables = set(schema_context.tables.keys())

    for join in joins:
        left_table = join.get("left_table", "")
        right_table = join.get("right_table", "")
        left_column = join.get("left_column", "")
        right_column = join.get("right_column", "")

        if left_table not in valid_tables:
            raise ValueError(f"Invalid join table: {left_table}")
        if right_table not in valid_tables:
            raise ValueError(f"Invalid join table: {right_table}")

        left_table_columns = schema_context.tables.get(left_table, [])
        right_table_columns = schema_context.tables.get(right_table, [])

        if left_column and left_column not in left_table_columns:
            raise ValueError(
                f"Invalid join column '{left_column}' in table '{left_table}'. "
                f"Available: {left_table_columns}"
            )
        if right_column and right_column not in right_table_columns:
            raise ValueError(
                f"Invalid join column '{right_column}' in table '{right_table}'. "
                f"Available: {right_table_columns}"
            )


# =========================================================
# RESOLVE SET VALUES
# =========================================================

def resolve_set_values(
    set_values: list[dict],
    schema_tables: dict[str, list[str]],
) -> list[dict]:
    all_columns: set[str] = set()
    for cols in schema_tables.values():
        all_columns.update(cols)

    resolved = []
    for item in set_values:
        column = item.get("column", "")
        resolved_column = column

        if column and column not in all_columns:
            normalized = column.lower().replace("_", "").replace(" ", "")
            for actual_col in all_columns:
                actual_normalized = actual_col.lower().replace("_", "").replace(" ", "")
                if normalized in actual_normalized or actual_normalized in normalized:
                    resolved_column = actual_col
                    break

        resolved.append({**item, "column": resolved_column})

    return resolved


# =========================================================
# INFER PRIMARY TABLE
# (Bug 2 fix is entirely contained here)
# =========================================================

def _infer_primary_table(
    tables: list[str],
    stated_tables: list[str],
    raw_columns: list[str],
    schema_context: SchemaContext,
) -> str:
    """
    Select the primary table for column resolution.

    Strategy:
    1. Score each table by how well its columns match raw_columns.
    2. Apply a STATED_TABLE_BONUS to tables the user explicitly named.
    3. This guarantees that if the user said "department names",
       `departments` wins even if `employees` has a better raw column
       name match (e.g. exact "name" vs fuzzy "dept_name").

    Args:
        tables        : all resolved tables (may include inferred ones)
        stated_tables : tables from the original LLM intent BEFORE
                        expansion (the user's actual intent)
        raw_columns   : unresolved column names from LLM intent
        schema_context: full schema
    """
    if not tables:
        raise ValueError("No tables to score")

    if len(tables) == 1:
        return tables[0]

    primary_table = tables[0]
    best_score = -1.0

    for table_name in tables:
        table_score = 0.0

        # Score by column evidence
        for requested_column in raw_columns:
            if requested_column == "*":
                continue
            for actual_column in schema_context.tables.get(table_name, []):
                score = combined_score(requested_column, actual_column)
                if score > table_score:
                    table_score = score

        # === BUG 2 FIX: stated-table affinity bonus ===
        # If this table was in the user's original intent, give it
        # a strong bonus that overrides pure column-match evidence.
        if table_name in stated_tables:
            table_score += _STATED_TABLE_BONUS

        if table_score > best_score:
            best_score = table_score
            primary_table = table_name

    print(
        "PRIMARY TABLE:",
        primary_table,
        f"(score={best_score:.3f})",
        f"stated={stated_tables}",
    )

    return primary_table


# =========================================================
# GENERATE QUERY PLAN
# =========================================================

async def generate_query_plan(
    extracted_intent: ExtractedIntent,
    schema_context: SchemaContext,
) -> QueryPlan:
    """
    Full deterministic query plan generation pipeline.

    Pipeline order:
    1.  Expand missing tables (conservative — Bug 1 fix)
    2.  Resolve tables
    3.  Validate tables
    4.  Capture stated_tables (user's original intent, pre-expansion)
    5.  Resolve and repair joins
    6.  Relationship-aware condition rewriting
    7.  Validate joins
    8.  Expand scope to joined tables
    9.  Infer primary table (with stated-table affinity — Bug 2 fix)
    10. Resolve target columns (with context_tables — Bug 3 fix)
    11. Resolve conditions / group_by / having / order_by
        (all receive context_tables — Bug 4 fix propagation)
    12. Validate all resolved items
    13. Build and return QueryPlan
    """

    # =====================================================
    # STEP 1: EXPAND MISSING TABLES (conservative)
    # =====================================================
    extracted_intent = expand_missing_tables(
        extracted_intent=extracted_intent,
        schema_tables=schema_context.tables,
    )
    print("EXPANDED TABLES:", extracted_intent.target_tables)

    # =====================================================
    # STEP 2: RESOLVE TABLES
    # =====================================================
    raw_tables = extracted_intent.target_tables or []
    tables = [
        resolve_table_name(
            requested_table=table,
            schema_tables=schema_context.tables,
        )
        for table in raw_tables
    ]

    if not tables:
        raise ValueError("No target tables identified")

    validate_tables(tables, schema_context)

    # =====================================================
    # STEP 3: CAPTURE STATED TABLES
    # These are the tables the user's LLM intent specified.
    # We preserve this BEFORE any join expansion so that
    # primary table scoring knows what the user actually asked for.
    # =====================================================
    stated_tables = list(tables)

    # =====================================================
    # STEP 4: RESOLVE AND REPAIR JOINS
    # =====================================================
    resolved_joins = resolve_joins(
        joins=extracted_intent.joins,
        schema_tables=schema_context.tables,
    )
    resolved_joins = repair_joins(
        joins=resolved_joins,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 5: RELATIONSHIP-AWARE CONDITION REWRITING
    # =====================================================
    relationship_result = rewrite_relationship_conditions(
        tables=tables,
        conditions=extracted_intent.conditions,
        joins=resolved_joins,
        schema_context=schema_context,
    )
    resolved_conditions = relationship_result["conditions"]
    resolved_joins = relationship_result["joins"]

    validate_joins(
        joins=resolved_joins,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 6: EXPAND TABLE SCOPE (primary + joined tables)
    # =====================================================
    join_tables = _extract_join_tables(resolved_joins)

    all_tables = list(
        dict.fromkeys(
            tables + join_tables
        )
    )

    # =====================================================
    # STEP 7: PREPARE CONTEXT
    # =====================================================

    raw_columns = (
        extracted_intent.target_columns or ["*"]
    )

    # context tables are the ORIGINAL user-intended tables
    context_tables = stated_tables

    # =====================================================
    # STEP 8: RESOLVE TARGET COLUMNS
    # IMPORTANT:
    # Resolve across ALL candidate tables first.
    # DO NOT restrict to primary table yet.
    # =====================================================

    columns = resolve_target_columns(
        target_columns=raw_columns,

        schema_tables=schema_context.tables,

        restrict_to_tables=all_tables,

        context_tables=context_tables,
    )

    validate_columns(
        tables=all_tables,

        columns=columns,

        schema_context=schema_context,
    )

    # =====================================================
    # STEP 9: DETERMINE PRIMARY TABLE
    # Infer AFTER semantic column resolution.
    # =====================================================

    primary_table = _infer_primary_table(
        tables=all_tables,

        stated_tables=stated_tables,

        raw_columns=columns,

        schema_context=schema_context,
    )


    # =====================================================
    # STEP 9: RESOLVE CONDITIONS
    # =====================================================
    resolved_conditions = resolve_conditions(
        conditions=resolved_conditions,
        schema_tables=schema_context.tables,
        context_tables=context_tables,
    )
    validate_conditions(
        tables=all_tables,
        conditions=resolved_conditions,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 10: RESOLVE GROUP BY
    # =====================================================
    resolved_group_by = resolve_group_by(
        group_by=extracted_intent.group_by,
        schema_tables=schema_context.tables,
        context_tables=context_tables,
    )
    validate_columns(
        tables=all_tables,
        columns=resolved_group_by,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 11: RESOLVE HAVING
    # =====================================================
    resolved_having = resolve_conditions(
        conditions=extracted_intent.having,
        schema_tables=schema_context.tables,
        context_tables=context_tables,
    )
    validate_conditions(
        tables=all_tables,
        conditions=resolved_having,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 12: RESOLVE ORDER BY
    # =====================================================
    resolved_order_by = resolve_order_by(
        order_by=extracted_intent.order_by,
        schema_tables=schema_context.tables,
        context_tables=context_tables,
    )
    order_columns = [item.get("column") for item in resolved_order_by]
    validate_columns(
        tables=all_tables,
        columns=order_columns,
        schema_context=schema_context,
    )

    # =====================================================
    # STEP 13: RESOLVE SET VALUES
    # =====================================================
    resolved_set_values = resolve_set_values(
        set_values=extracted_intent.set_values,
        schema_tables=schema_context.tables,
    )

    # =====================================================
    # STEP 14: LIMIT
    # =====================================================
    limit = extracted_intent.row_limit
    if limit is None:
        limit = 10

    # =====================================================
    # STEP 15: BUILD PLAN
    # =====================================================
    return QueryPlan(
        operation=extracted_intent.operation,
        table=primary_table,
        tables=all_tables,
        columns=columns,
        distinct=extracted_intent.distinct,
        conditions=resolved_conditions,
        joins=resolved_joins,
        aggregations=extracted_intent.aggregations,
        group_by=resolved_group_by,
        having=resolved_having,
        order_by=resolved_order_by,
        unions=extracted_intent.unions,
        ctes=extracted_intent.ctes,
        limit=limit,
        set_values=resolved_set_values,
    )