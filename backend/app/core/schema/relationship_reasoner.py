from __future__ import annotations

from copy import deepcopy

from app.models.state import (
    SchemaContext
)


# =========================================================
# DISPLAY COLUMN CANDIDATES
# =========================================================

DISPLAY_COLUMN_PRIORITY = [

    "name",

    "title",

    "label",

    "dept_name",

    "department_name",

    "project_name",

    "employee_name",

    "full_name"
]


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(
    value: str
) -> str:

    return (

        value.lower()
        .replace("_", "")
        .replace(" ", "")
        .replace("-", "")
    )


# =========================================================
# FIND RELATED LOOKUP TABLE
# =========================================================

def find_related_lookup_table(

    base_table: str,

    foreign_key_column: str,

    schema_context: SchemaContext
):

    """
    Example:

    employees.department_id
        ->
    departments
    """

    normalized_fk = normalize_text(
        foreign_key_column
    )

    # remove _id suffix
    normalized_fk = normalized_fk.replace(
        "id",
        ""
    )

    schema_tables = schema_context.tables

    for table_name in schema_tables.keys():

        normalized_table = normalize_text(
            table_name
        )

        singular_table = (
            normalized_table.rstrip("s")
        )

        if (

            singular_table in normalized_fk

            or

            normalized_fk in singular_table
        ):

            if table_name != base_table:

                return table_name

    return None


# =========================================================
# FIND PRIMARY KEY COLUMN
# =========================================================

def find_primary_key_column(

    table_name: str,

    schema_context: SchemaContext
):

    columns = schema_context.tables.get(
        table_name,
        []
    )

    # priority
    priority = [

        "id",

        f"{table_name.rstrip('s')}_id",

        f"{table_name}_id",

        "dept_id",

        "project_id"
    ]

    for candidate in priority:

        if candidate in columns:

            return candidate

    # fallback
    for col in columns:

        if col.endswith("_id"):

            return col

    return None


# =========================================================
# FIND DISPLAY COLUMN
# =========================================================

def find_lookup_display_column(

    table_name: str,

    schema_context: SchemaContext
):

    columns = schema_context.tables.get(
        table_name,
        []
    )

    normalized_map = {

        normalize_text(col): col

        for col in columns
    }

    # strict priority first
    for candidate in DISPLAY_COLUMN_PRIORITY:

        normalized = normalize_text(
            candidate
        )

        if normalized in normalized_map:

            return normalized_map[normalized]

    # fallback to any *_name
    for col in columns:

        if col.endswith("_name"):

            return col

    # final fallback
    if "name" in columns:

        return "name"

    return None


# =========================================================
# CHECK IF JOIN EXISTS
# =========================================================

def join_already_exists(

    joins: list[dict],

    left_table: str,

    right_table: str
):

    for join in joins:

        l = join.get("left_table")
        r = join.get("right_table")

        if (

            (l == left_table and r == right_table)

            or

            (l == right_table and r == left_table)
        ):

            return True

    return False


# =========================================================
# REWRITE RELATIONSHIP CONDITIONS
# =========================================================

def rewrite_relationship_conditions(

    tables: list[str],

    conditions: list[dict],

    joins: list[dict],

    schema_context: SchemaContext
):

    """
    Converts semantic filters like:

        department = 'IT'

    into:

        JOIN departments
        WHERE departments.dept_name = 'IT'
    """

    rewritten_conditions = []

    rewritten_joins = deepcopy(joins)

    schema_tables = schema_context.tables

    primary_table = tables[0]

    primary_columns = schema_tables.get(
        primary_table,
        []
    )

    for condition in conditions:

        column = condition.get("column")

        operator = condition.get("operator")

        value = condition.get("value")

        logical_operator = condition.get(
            "logical_operator",
            "AND"
        )

        # -----------------------------------------
        # SKIP INVALID
        # -----------------------------------------

        if not column:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # DIRECT COLUMN EXISTS
        # -----------------------------------------

        if column in primary_columns:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # TRY FK LOOKUP REASONING
        # -----------------------------------------

        matched_fk = None

        for primary_col in primary_columns:

            if not primary_col.endswith("_id"):

                continue

            normalized_fk = normalize_text(
                primary_col.replace("_id", "")
            )

            normalized_requested = normalize_text(
                column
            )

            if (

                normalized_requested in normalized_fk

                or

                normalized_fk in normalized_requested
            ):

                matched_fk = primary_col
                break

        # -----------------------------------------
        # NO FK MATCH
        # -----------------------------------------

        if not matched_fk:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # FIND LOOKUP TABLE
        # -----------------------------------------

        lookup_table = find_related_lookup_table(

            base_table=primary_table,

            foreign_key_column=matched_fk,

            schema_context=schema_context
        )

        if not lookup_table:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # FIND LOOKUP PK
        # -----------------------------------------

        lookup_pk = find_primary_key_column(

            lookup_table,

            schema_context
        )

        if not lookup_pk:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # FIND DISPLAY COLUMN
        # -----------------------------------------

        display_column = find_lookup_display_column(

            lookup_table,

            schema_context
        )

        if not display_column:

            rewritten_conditions.append(
                condition
            )

            continue

        # -----------------------------------------
        # CREATE JOIN
        # -----------------------------------------

        if not join_already_exists(

            joins=rewritten_joins,

            left_table=primary_table,

            right_table=lookup_table
        ):

            rewritten_joins.append({

                "join_type": "INNER",

                "left_table": primary_table,

                "right_table": lookup_table,

                "left_column": matched_fk,

                "right_column": lookup_pk
            })

        # -----------------------------------------
        # REWRITE CONDITION
        # -----------------------------------------

        rewritten_conditions.append({

            "column":
                f"{lookup_table}.{display_column}",

            "operator":
                operator,

            "value":
                value,

            "logical_operator":
                logical_operator
        })

    return {

        "conditions":
            rewritten_conditions,

        "joins":
            rewritten_joins
    }