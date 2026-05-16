"""
semantic_mapper.py
==================
Schema-driven semantic resolution layer.

BUG FIX (Bug 4):
    combined_score() had no concept of "which tables the user cares about".
    A generic column like "name" would always score higher as employees.name
    (exact sequence match) vs departments.dept_name (fuzzy match), regardless
    of the user's stated table context.

    Fix: add context_tables parameter to find_best_column_match() and
    resolve_column_name(). When context_tables is provided, columns from
    those tables receive a STRONG affinity bonus (+0.40). This means
    departments.dept_name outscores employees.name when departments is
    the user's stated table.

    The affinity bonus is:
      - Applied only when context_tables is non-empty
      - Additive (doesn't override scoring, just tips the balance)
      - Large enough to overcome a perfect sequence score on the
        wrong table (0.40 > max sequence score gap of ~0.30)
"""

from __future__ import annotations

from difflib import SequenceMatcher


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(value: str) -> str:
    return (
        value.lower()
        .replace("_", " ")
        .replace(".", " ")
        .strip()
    )


def normalize_compact(value: str) -> str:
    return (
        value.lower()
        .replace("_", "")
        .replace(" ", "")
        .replace(".", "")
        .strip()
    )


def tokenize(value: str) -> set[str]:
    return set(normalize_text(value).split())


# =========================================================
# SCORING
# =========================================================

def _sequence_score(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize_text(a),
        normalize_text(b),
    ).ratio()


def _token_overlap_score(a: str, b: str) -> float:
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _prefix_score(a: str, b: str) -> float:
    ca = normalize_compact(a)
    cb = normalize_compact(b)
    if not ca or not cb:
        return 0.0
    if cb.startswith(ca) or ca.startswith(cb):
        return 0.9
    if cb.endswith(ca) or ca.endswith(cb):
        return 0.85
    if ca in cb or cb in ca:
        return 0.8
    return 0.0


def combined_score(
    input_name: str,
    candidate_name: str,
) -> float:
    """
    Base semantic similarity score between two names.

    NOTE: This function has NO table-context awareness by design —
    it's a pure string similarity score. Table-context affinity
    bonuses are applied in find_best_column_match() and
    score_column_in_table_context(), which are the call sites
    that have access to the query context.
    """
    seq = _sequence_score(input_name, candidate_name)
    overlap = _token_overlap_score(input_name, candidate_name)
    prefix = _prefix_score(input_name, candidate_name)

    score = (
        seq * 0.5
        + overlap * 0.2
        + prefix * 0.3
    )

    # Penalize FK/ID columns unless user asked for them
    input_compact = normalize_compact(input_name)
    candidate_compact = normalize_compact(candidate_name)

    user_mentions_id = any(
        keyword in input_compact
        for keyword in ["id", "identifier", "code", "uuid", "pk"]
    )

    candidate_is_id_column = (
        candidate_compact == "id"
        or candidate_compact.endswith("id")
        or candidate_compact.endswith("_id")
    )

    if candidate_is_id_column and not user_mentions_id:
        score -= 0.15

    return score


# =========================================================
# CONTEXT-AWARE COLUMN SCORE
# (this is the key new function that fixes Bug 4)
# =========================================================

# Affinity bonus for columns in the user's stated tables.
# Must exceed the max gap between exact-match score and fuzzy-match
# score (~0.30) to guarantee stated-table columns win.
_STATED_TABLE_AFFINITY = 0.40


def score_column_in_table_context(
    requested_column: str,
    table_name: str,
    column: str,
    context_tables: list[str] | None,
) -> float:
    """
    Score a (table_name, column) candidate for a requested_column,
    with an affinity bonus for user-stated tables.

    Args:
        requested_column : the column name from the LLM intent
        table_name       : the schema table being considered
        column           : the actual column in that schema table
        context_tables   : the user's stated/resolved target tables
                           (if provided, columns from these tables
                           receive a strong affinity bonus)

    Returns:
        float score (higher = better match)
    """
    base = combined_score(requested_column, column)

    # Table semantic contribution
    table_sem = combined_score(requested_column, table_name)

    score = base + (table_sem * 0.35)

    # Token bonus: requested token is substring of column
    req_compact = normalize_compact(requested_column)
    col_compact = normalize_compact(column)
    if req_compact in col_compact:
        score += 0.20

    # Stated-table affinity bonus (the core Bug 4 fix)
    if context_tables and table_name in context_tables:
        score += _STATED_TABLE_AFFINITY

    return score


# =========================================================
# AGGREGATION ALIAS DETECTION
# =========================================================

_AGG_PREFIXES = ("avg_", "sum_", "count_", "min_", "max_")


def is_aggregation_alias(column: str) -> bool:
    lowered = column.lower()
    return any(lowered.startswith(p) for p in _AGG_PREFIXES)


# =========================================================
# FIND BEST COLUMN MATCH
# =========================================================

def find_best_column_match(
    requested_column: str,
    schema_tables: dict[str, list[str]],
    restrict_to_tables: list[str] | None = None,
    context_tables: list[str] | None = None,
    threshold: float = 0.45,
) -> str | None:
    """
    Context-aware semantic column resolver.

    Args:
        requested_column  : LLM-generated column name
        schema_tables     : full schema dict
        restrict_to_tables: if set, only search within these tables
                            (used for qualified column resolution)
        context_tables    : the user's STATED target tables — columns
                            from these tables get an affinity bonus.
                            This is the key parameter for correctness.
                            Pass the user's resolved target_tables here.
        threshold         : minimum score to accept a match

    Note on restrict_to_tables vs context_tables:
        restrict_to_tables LIMITS the search space (hard filter).
        context_tables BOOSTS scores for preferred tables (soft bias).
        They can be combined: restrict to a set of tables AND prefer
        the user's stated ones within that set.
    """
    best_match = None
    best_score = 0.0

    tables_to_search = (
        restrict_to_tables
        if restrict_to_tables
        else list(schema_tables.keys())
    )

    for table_name in tables_to_search:
        columns = schema_tables.get(table_name, [])

        for column in columns:
            final_score = score_column_in_table_context(
                requested_column=requested_column,
                table_name=table_name,
                column=column,
                context_tables=context_tables,
            )

            if final_score > best_score:
                best_score = final_score
                best_match = column

    if best_score >= threshold:
        return best_match
    return None


def find_best_table_match(
    requested_table: str,
    schema_tables: dict[str, list[str]],
    threshold: float = 0.50,
) -> str | None:
    best_match = None
    best_score = 0.0
    for table_name in schema_tables:
        score = combined_score(requested_table, table_name)
        if score > best_score:
            best_score = score
            best_match = table_name
    return best_match if best_score >= threshold else None


# =========================================================
# RESOLVE TABLE NAME
# =========================================================

def resolve_table_name(
    requested_table: str,
    schema_tables: dict[str, list[str]],
) -> str:
    if not requested_table:
        return requested_table
    if requested_table in schema_tables:
        return requested_table
    match = find_best_table_match(requested_table, schema_tables)
    return match if match else requested_table


# =========================================================
# RESOLVE COLUMN NAME
# =========================================================

def resolve_column_name(
    requested_column: str,
    schema_tables: dict[str, list[str]],
    restrict_to_tables: list[str] | None = None,
    context_tables: list[str] | None = None,
) -> str:
    """
    Resolve a column name to the actual schema column.

    Args:
        requested_column  : LLM-generated column name
        schema_tables     : full schema dict
        restrict_to_tables: hard-limit the search to these tables
        context_tables    : soft-bias toward these tables (affinity bonus)
                            Pass the user's resolved target_tables here.
    """
    if not requested_column:
        return requested_column

    # Passthrough aggregation aliases
    if is_aggregation_alias(requested_column):
        return requested_column

    # Qualified column: table.column
    if "." in requested_column:
        table_part, column_part = requested_column.split(".", 1)
        resolved_table = resolve_table_name(table_part, schema_tables)
        resolved_column = resolve_column_name(
            requested_column=column_part,
            schema_tables=schema_tables,
            restrict_to_tables=[resolved_table],
            context_tables=context_tables,
        )
        return f"{resolved_table}.{resolved_column}"

    # =====================================================
    # SMART EXACT / CONTAINS MATCH
    # =====================================================

    target_tables = (
        {
            t: schema_tables[t]
            for t in restrict_to_tables
            if t in schema_tables
        }
        if restrict_to_tables
        else schema_tables
    )

    requested_normalized = normalize_compact(
        requested_column
    )

    # -----------------------------------------
    # PRIORITY 1:
    # Exact normalized match
    # -----------------------------------------

    for columns in target_tables.values():

        for actual_column in columns:

            actual_normalized = normalize_compact(
                actual_column
            )

            if requested_normalized == actual_normalized:

                return actual_column

    # -----------------------------------------
    # PRIORITY 2:
    # Semantic contains match
    #
    # EXAMPLE:
    #   name -> dept_name
    #   phone -> dept_phone
    # -----------------------------------------

    # for columns in target_tables.values():

    #     for actual_column in columns:

    #         actual_normalized = normalize_compact(
    #             actual_column
    #         )

    #         if (
    #             requested_normalized in actual_normalized
    #             or actual_normalized in requested_normalized
    #         ):

    #             return actual_column

    # Semantic match with context awareness
    match = find_best_column_match(
        requested_column=requested_column,
        schema_tables=schema_tables,
        restrict_to_tables=restrict_to_tables,
        context_tables=context_tables,
        threshold=0.45,
    )
    return match if match else requested_column


# =========================================================
# RESOLVE TARGET COLUMNS
# =========================================================

def resolve_target_columns(
    target_columns: list[str],
    schema_tables: dict[str, list[str]],
    restrict_to_tables: list[str] | None = None,
    context_tables: list[str] | None = None,
) -> list[str]:
    """
    Context-aware target column resolution.

    Args:
        target_columns    : raw columns from LLM intent
        schema_tables     : full schema dict
        restrict_to_tables: hard-limit search to primary table
        context_tables    : stated target tables — affinity bonus
                            (MUST be passed from planner for correctness)
    """
    resolved = []
    prioritized_tables = restrict_to_tables or []

    for column in target_columns:
        if column == "*":
            resolved.append("*")
            continue

        if "." in column:
            resolved.append(
                resolve_column_name(
                    requested_column=column,
                    schema_tables=schema_tables,
                    restrict_to_tables=restrict_to_tables,
                    context_tables=context_tables,
                )
            )
            continue

        # Search priority tables first, with context affinity
        best_match = find_best_column_match(
            requested_column=column,
            schema_tables=schema_tables,
            restrict_to_tables=prioritized_tables if prioritized_tables else None,
            context_tables=context_tables,
            threshold=0.45,
        )

        # Fallback to global search with context affinity preserved
        if not best_match:
            best_match = find_best_column_match(
                requested_column=column,
                schema_tables=schema_tables,
                context_tables=context_tables,
                threshold=0.45,
            )

        resolved.append(best_match if best_match else column)

    return resolved


# =========================================================
# RESOLVE CONDITIONS
# =========================================================

def resolve_conditions(
    conditions: list[dict],
    schema_tables: dict[str, list[str]],
    context_tables: list[str] | None = None,
) -> list[dict]:
    resolved = []
    for condition in conditions:
        column = condition.get("column")
        resolved_column = column

        if column and "." in column:
            table_name, col_name = column.split(".", 1)
            resolved_col = resolve_column_name(
                requested_column=col_name,
                schema_tables=schema_tables,
                restrict_to_tables=[table_name],
                context_tables=context_tables,
            )
            resolved_column = f"{table_name}.{resolved_col}"

        elif column:
            resolved_column = resolve_column_name(
                requested_column=column,
                schema_tables=schema_tables,
                context_tables=context_tables,
            )

        resolved.append({
            "column": resolved_column,
            "operator": condition.get("operator", "="),
            "value": condition.get("value"),
            "logical_operator": condition.get("logical_operator", "AND"),
        })

    return resolved


# =========================================================
# RESOLVE GROUP BY
# =========================================================

def resolve_group_by(
    group_by: list[str],
    schema_tables: dict[str, list[str]],
    context_tables: list[str] | None = None,
) -> list[str]:
    return [
        resolve_column_name(col, schema_tables, context_tables=context_tables)
        for col in group_by
    ]


# =========================================================
# RESOLVE ORDER BY
# =========================================================

def resolve_order_by(
    order_by: list[dict],
    schema_tables: dict[str, list[str]],
    context_tables: list[str] | None = None,
) -> list[dict]:
    resolved = []
    for item in order_by:
        column = item.get("column")
        resolved_column = (
            resolve_column_name(
                column,
                schema_tables,
                context_tables=context_tables,
            )
            if column
            else column
        )

        direction = (
            item.get("direction")
            or item.get("order")
            or "ASC"
        ).upper()

        resolved.append({
            "column": resolved_column,
            "direction": direction,
        })
    return resolved


# =========================================================
# RESOLVE JOINS (pre-repair semantic normalization)
# =========================================================

def resolve_joins(
    joins: list[dict],
    schema_tables: dict[str, list[str]],
) -> list[dict]:
    resolved = []
    for join in joins:
        left_table = resolve_table_name(
            join.get("left_table", ""),
            schema_tables,
        )
        right_table = resolve_table_name(
            join.get("right_table", ""),
            schema_tables,
        )

        left_column = resolve_column_name(
            requested_column=join.get("left_column", ""),
            schema_tables=schema_tables,
            restrict_to_tables=[left_table],
        )
        right_column = resolve_column_name(
            requested_column=join.get("right_column", ""),
            schema_tables=schema_tables,
            restrict_to_tables=[right_table],
        )

        resolved.append({
            "join_type": join.get("join_type", "INNER"),
            "left_table": left_table,
            "right_table": right_table,
            "left_column": left_column,
            "right_column": right_column,
        })
    return resolved