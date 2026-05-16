"""
join_resolver.py
================
Schema-driven deterministic join repair layer.

Placement: app/core/schema/join_resolver.py

REPLACE your entire existing join_resolver.py with this file.

Responsibilities:
- Detect invalid / missing join columns after semantic resolution
- Infer FK -> PK relationships purely from schema column names
- Support forward FK (left->right) and reverse FK (right->left)
- Handle table name variations (departments -> dept_id, etc.)
- Fully generic: works for any database schema with no hardcoding

Run order:
  resolve_joins()        <- semantic_mapper.py   (name normalization)
  repair_joins()         <- join_resolver.py      (FK/PK structural repair)
  validate_joins()       <- planner.py            (final guard)
"""

from __future__ import annotations

from app.models.state import SchemaContext


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def _compact(value: str) -> str:
    """
    Remove underscores, spaces, lower for substring comparison.
    'dept_name' -> 'deptname', 'department' -> 'department'
    """
    return value.lower().replace("_", "").replace(" ", "")


# =========================================================
# PRIMARY KEY INFERENCE
# =========================================================

# Generic primary key column name candidates.
# Order matters: checked first before prefix-based inference.
_PK_CANDIDATES = ["id", "uuid", "pk"]


def find_primary_key(
    table: str,
    schema_context: SchemaContext,
) -> str | None:
    """
    Infer the primary key column for a given table.

    Strategy:
    1. Direct match against common PK names ('id', 'uuid', 'pk')
    2. Table-name prefix match:
       - 'departments' -> look for column containing 'dept' + ending in 'id'
       - 'projects'    -> look for column containing 'project' + ending in 'id'
    3. Any column ending in '_id' that matches any leading prefix of table name
    """
    columns = schema_context.tables.get(table, [])

    # -----------------------------------------------
    # PASS 1: exact known PK names
    # -----------------------------------------------
    for candidate in _PK_CANDIDATES:
        if candidate in columns:
            return candidate

    # -----------------------------------------------
    # PASS 2: table prefix + 'id' suffix
    # e.g. departments -> dept_id, deptid, department_id
    # e.g. projects -> project_id, projectid
    # -----------------------------------------------
    table_compact = _compact(table.rstrip("s"))  # 'departments' -> 'department'

    for column in columns:
        col_compact = _compact(column)
        if not col_compact.endswith("id"):
            continue
        # strip trailing 'id' and check if table prefix matches
        col_base = col_compact[:-2]  # e.g. 'deptid' -> 'dept', 'departmentid' -> 'department'
        if not col_base:
            continue
        # flexible: table prefix is contained in column base, or vice versa
        if (
            table_compact.startswith(col_base)
            or col_base.startswith(table_compact[:4])  # min 4-char prefix guard
            or table_compact in col_base
            or col_base in table_compact
        ):
            return column

    # -----------------------------------------------
    # PASS 3: any *_id column as last resort
    # -----------------------------------------------
    id_columns = [c for c in columns if c.endswith("_id") or c == "id"]
    if len(id_columns) == 1:
        return id_columns[0]

    return None


# =========================================================
# FOREIGN KEY INFERENCE
# =========================================================

def find_foreign_key(
    source_table: str,
    target_table: str,
    schema_context: SchemaContext,
) -> str | None:
    """
    Find the foreign key column in source_table that references target_table.

    Strategy:
    1. Column name contains compact form of target table name AND ends in 'id'
       e.g. source=employees, target=departments -> 'department_id' (compact: 'departmentid')
    2. Any 4+ char prefix of target table compact name inside column compact name
       e.g. target=departments -> compact='department' -> prefix='depa' matches 'department_id'
    3. target table name stripped of trailing 's' prefix match
       e.g. 'employees' -> 'employee' -> matches 'lead_employee_id'
    """
    source_columns = schema_context.tables.get(source_table, [])
    target_compact = _compact(target_table.rstrip("s"))  # 'departments' -> 'department'

    # We need FK columns only — skip anything that looks like a PK
    pk_names = {"id", "uuid", "pk"}
    fk_candidates = [
        c for c in source_columns
        if (c.endswith("_id") or _compact(c).endswith("id"))
        and c not in pk_names
    ]

    for column in fk_candidates:
        col_compact = _compact(column)

        # -----------------------------------------------
        # PASS 1: full target table name contained in FK
        # e.g. 'department_id' contains 'department'
        # -----------------------------------------------
        if target_compact in col_compact:
            return column

        # -----------------------------------------------
        # PASS 2: leading prefix match (min 4 chars)
        # e.g. target='departments' compact='department'
        #       prefix='depa' inside 'deptid'? No.
        # But 'dept' is an abbreviation. We need deeper:
        # Check if col base (without trailing id) is a prefix of target
        # -----------------------------------------------
        col_base = col_compact[:-2] if col_compact.endswith("id") else col_compact
        if col_base and len(col_base) >= 3:
            # col_base is prefix of target OR target is prefix of col_base
            if target_compact.startswith(col_base) or col_base.startswith(target_compact[:4]):
                return column
        
        # PASS 3:
        # Singularized target prefix match

        target_singular = target_compact.rstrip("s")

        if target_singular in col_compact:
            return column

    return None


# =========================================================
# JOIN COLUMN RESOLUTION
# =========================================================

def resolve_join_columns(
    left_table: str,
    right_table: str,
    schema_context: SchemaContext,
) -> tuple[str | None, str | None]:
    """
    Given two join tables, infer the correct FK and PK columns.

    Returns (left_column, right_column) or (None, None) if unresolvable.

    Tries:
    1. left has FK -> right has PK  (employees.department_id = departments.dept_id)
    2. right has FK -> left has PK  (projects.lead_employee_id = employees.id)
    """
    # -----------------------------------------------
    # DIRECTION 1: left_table.FK = right_table.PK
    # -----------------------------------------------
    left_fk = find_foreign_key(left_table, right_table, schema_context)
    right_pk = find_primary_key(right_table, schema_context)

    if left_fk and right_pk:
        return left_fk, right_pk

    # -----------------------------------------------
    # DIRECTION 2: right_table.FK = left_table.PK
    # -----------------------------------------------
    right_fk = find_foreign_key(right_table, left_table, schema_context)
    left_pk = find_primary_key(left_table, schema_context)

    if right_fk and left_pk:
        return left_pk, right_fk

    return None, None


# =========================================================
# VALIDATE JOIN COLUMNS
# =========================================================

def _join_columns_valid(
    join: dict,
    schema_context: SchemaContext,
) -> bool:
    """
    Returns True only if both join columns exist in their respective tables.
    Used to decide whether repair is needed.
    """
    left_table = join.get("left_table", "")
    right_table = join.get("right_table", "")
    left_column = join.get("left_column", "")
    right_column = join.get("right_column", "")

    left_columns = schema_context.tables.get(left_table, [])
    right_columns = schema_context.tables.get(right_table, [])

    return (
        left_column in left_columns
        and right_column in right_columns
    )


# =========================================================
# REPAIR SINGLE JOIN
# =========================================================

def repair_join(
    join: dict,
    schema_context: SchemaContext,
) -> dict:
    """
    Repair a single join dict.

    If the join columns are already valid: return unchanged.
    Otherwise: infer correct FK/PK pair from schema.

    This is non-destructive — if inference fails, the original
    (invalid) values are preserved so validate_joins() can surface
    a clean error to the user.
    """
    left_table = join.get("left_table", "")
    right_table = join.get("right_table", "")

    if not left_table or not right_table:
        return join

    # Skip repair if columns are already valid
    if _join_columns_valid(join, schema_context):
        return join

    resolved_left, resolved_right = resolve_join_columns(
        left_table=left_table,
        right_table=right_table,
        schema_context=schema_context,
    )

    repaired = dict(join)

    if resolved_left:
        repaired["left_column"] = resolved_left

    if resolved_right:
        repaired["right_column"] = resolved_right

    return repaired


# =========================================================
# REPAIR ALL JOINS
# =========================================================

def repair_joins(
    joins: list[dict],
    schema_context: SchemaContext,
) -> list[dict]:
    """
    Repair all joins in a query plan.

    Safe to call even when joins are empty.
    Idempotent: already-valid joins are untouched.
    """
    return [repair_join(join, schema_context) for join in joins]