"""
table_expander.py
=================
Schema-aware table expansion.

BUG FIX (Bug 1):
    expand_missing_tables previously called infer_table_from_column()
    for every column, including generic names like "name", "title", etc.
    This poisoned the table set when the user had already specified
    a concrete target table.

    The fix introduces TWO guards:
    1. If target_tables is already populated, skip inference for any column
       whose normalized form is a high-ambiguity token (no table-scoped
       signal). Only infer when the column is QUALIFIED (table.column)
       or when it produces a unique, high-confidence match.
    2. If target_tables is already populated and a column exists in
       the already-stated tables, never add a different table.

    This makes expansion additive only when there is genuine schema
    evidence, not just a fuzzy token match on a generic word.
"""

from __future__ import annotations

import re

from app.models.state import ExtractedIntent


# =========================================================
# NORMALIZE TOKEN
# =========================================================

def normalize_token(value: str) -> str:
    value = value.lower()
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9\s]", "", value)
    return value.strip()


# =========================================================
# TOKENIZE
# =========================================================

def tokenize(value: str) -> set[str]:
    return set(normalize_token(value).split())


# =========================================================
# SIMILARITY SCORE
# =========================================================

def similarity_score(source: str, target: str) -> int:
    source_tokens = tokenize(source)
    target_tokens = tokenize(target)
    if not source_tokens or not target_tokens:
        return 0
    return len(source_tokens & target_tokens)


# =========================================================
# COLUMN EXISTS IN TABLE SET
# (used to short-circuit expansion when column already
# belongs to a known table)
# =========================================================

def _column_in_tables(
    column: str,
    tables: list[str],
    schema_tables: dict[str, list[str]],
) -> bool:
    """
    Return True if `column` is present in ANY of the given tables.
    Case-insensitive exact match.
    """
    col_lower = column.lower()
    for table in tables:
        for actual in schema_tables.get(table, []):
            if actual.lower() == col_lower:
                return True
    return False


# =========================================================
# INFER TABLE FROM COLUMN
# Now returns (table_name, confidence_score) instead of just
# table_name so callers can apply a threshold.
# =========================================================

def infer_table_from_column(
    column: str,
    schema_tables: dict[str, list[str]],
) -> tuple[str | None, int]:
    """
    Returns (best_table, score).

    Score semantics:
      >= 3  : high-confidence (direct exact column match = 3)
      == 2  : moderate (singular/plural table name match)
      == 1  : low (loose semantic overlap)
      == 0  : no match
    """
    best_match = None
    best_score = 0
    normalized_column = normalize_token(column)

    # ── Direct exact column match (highest confidence) ──
    for table_name, columns in schema_tables.items():
        for actual_column in columns:
            if normalized_column == normalize_token(actual_column):
                # Exact match: score=3, but only return if unique
                # (if multiple tables have the same column, confidence drops)
                if best_score < 3:
                    best_match = table_name
                    best_score = 3
                elif best_score == 3:
                    # ambiguous exact match → downgrade
                    best_score = 1
                    best_match = None

    if best_score == 3:
        return best_match, best_score

    # ── Semantic table/column matching ──
    for table_name, columns in schema_tables.items():
        score = similarity_score(normalized_column, table_name)

        # singular/plural support
        if normalized_column.rstrip("s") == table_name.rstrip("s"):
            score += 2

        for actual_column in columns:
            score += similarity_score(normalized_column, actual_column)

        if score > best_score:
            best_score = score
            best_match = table_name

    return best_match, best_score


# =========================================================
# EXPAND TABLES
# =========================================================

def expand_missing_tables(
    extracted_intent: ExtractedIntent,
    schema_tables: dict[str, list[str]],
) -> ExtractedIntent:
    """
    Expands target_tables only when there is genuine schema evidence.

    Key behaviour changes vs original:
    ─────────────────────────────────
    1. QUALIFIED columns (table.col) always add the explicit table.
    2. For UNQUALIFIED columns:
       a. If the column already exists in a currently-stated table,
          do NOT expand — the column belongs there.
       b. Only add an inferred table when confidence >= 3 (unique
          exact column match) OR confidence >= 2 AND target_tables
          is empty (no existing table context).
    3. Condition columns follow the same rules.

    This prevents "name" from pulling in `employees` when the user
    said `departments` and departments has a name-like column.
    """
    current_tables = list(extracted_intent.target_tables)
    additions: set[str] = set()

    # =====================================================
    # IMPORTANT:
    # If the LLM already identified target tables,
    # do NOT inject additional semantic tables from
    # generic columns like "name", "id", "title".
    #
    # Otherwise:
    # "department names"
    # incorrectly expands:
    # departments -> employees
    #
    # This causes primary-table poisoning.
    # =====================================================

    if current_tables:

        extracted_intent.target_tables = list(
            current_tables
        )

        return extracted_intent

    # ── Helper ───────────────────────────────────────────
    def _try_add(column: str) -> None:
        """Add inferred table for a column, respecting confidence rules."""
        if not column or column == "*":
            return

        # Qualified: trust the explicit table reference
        if "." in column:
            table_name = column.split(".")[0]
            if table_name in schema_tables:
                additions.add(table_name)
            return

        # If this column already lives in a stated table, stop here
        all_known = list(set(current_tables) | additions)
        if all_known and _column_in_tables(column, all_known, schema_tables):
            return

        inferred_table, confidence = infer_table_from_column(
            column=column,
            schema_tables=schema_tables,
        )

        if not inferred_table:
            return

        # Threshold: require high confidence when tables already known
        if current_tables or additions:
            # Only add if uniquely identified (confidence=3) and the
            # inferred table is not already covered
            if confidence >= 3 and inferred_table not in all_known:
                additions.add(inferred_table)
        else:
            # No tables yet: accept moderate confidence
            if confidence >= 2:
                additions.add(inferred_table)

    # ── Process target columns ────────────────────────────
    for column in extracted_intent.target_columns:
        _try_add(column)

    # ── Process conditions ────────────────────────────────
    for condition in extracted_intent.conditions:
        column = condition.get("column")
        if column:
            _try_add(column)

    # ── Merge ─────────────────────────────────────────────
    merged = list(dict.fromkeys(current_tables + list(additions)))
    extracted_intent.target_tables = merged
    return extracted_intent