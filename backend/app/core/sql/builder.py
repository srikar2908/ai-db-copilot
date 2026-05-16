from app.models.state import (
    QueryPlan
)


# =================================================
# FORMAT VALUE
# =================================================

def format_sql_value(value):

    if value is None:

        return "NULL"

    if isinstance(value, bool):

        return (
            "TRUE"
            if value
            else "FALSE"
        )

    if isinstance(value, (int, float)):

        return str(value)

    escaped = str(value).replace(
        "'",
        "''"
    )

    return f"'{escaped}'"


# =================================================
# BUILD WHERE CLAUSE
# =================================================

def build_where_clause(
    conditions: list[dict]
) -> str:

    if not conditions:

        return ""

    clauses = []

    for cond in conditions:

        column = cond.get(
            "column"
        )

        operator = cond.get(
            "operator",
            "="
        ).upper()

        value = cond.get(
            "value"
        )

        # NULL

        if value is None:

            if operator in ["=", "IS"]:

                clauses.append(
                    f"{column} IS NULL"
                )

            elif operator in [
                "!=",
                "<>",
                "IS NOT"
            ]:

                clauses.append(
                    f"{column} IS NOT NULL"
                )

            continue

        # LIST

        if isinstance(value, list):

            values_sql = ", ".join([

                format_sql_value(v)

                for v in value
            ])

            if operator == "NOT IN":

                clauses.append(
                    f"{column} NOT IN ({values_sql})"
                )

            else:

                clauses.append(
                    f"{column} IN ({values_sql})"
                )

            continue

        # STRING

        if isinstance(value, str):

            escaped = value.replace(
                "'",
                "''"
            )

            if operator == "=":

                clauses.append(
                    f"LOWER({column}) "
                    f"= LOWER('{escaped}')"
                )

            elif operator in [
                "!=",
                "<>"
            ]:

                clauses.append(
                    f"LOWER({column}) "
                    f"!= LOWER('{escaped}')"
                )

            elif operator == "LIKE":

                clauses.append(
                    f"LOWER({column}) "
                    f"LIKE LOWER('%{escaped}%')"
                )

            else:

                clauses.append(
                    f"{column} "
                    f"{operator} "
                    f"'{escaped}'"
                )

            continue

        # NUMERIC

        clauses.append(
            f"{column} "
            f"{operator} "
            f"{format_sql_value(value)}"
        )

    if not clauses:

        return ""

    return (
        "WHERE "
        + " AND ".join(clauses)
    )


# =================================================
# BUILD ORDER BY
# =================================================

def build_order_by_clause(
    order_by: list[dict]
) -> str:

    if not order_by:

        return ""

    clauses = []

    for item in order_by:

        column = item.get(
            "column"
        )

        direction = item.get(
            "direction",
            "ASC"
        ).upper()

        if direction not in [
            "ASC",
            "DESC"
        ]:

            direction = "ASC"

        clauses.append(
            f"{column} {direction}"
        )

    return (
        "ORDER BY "
        + ", ".join(clauses)
    )


# =================================================
# BUILD GROUP BY
# =================================================

def build_group_by_clause(
    group_by: list[str]
) -> str:

    if not group_by:

        return ""

    return (
        "GROUP BY "
        + ", ".join(group_by)
    )


# =================================================
# BUILD HAVING
# =================================================

def build_having_clause(
    having: list[dict]
) -> str:

    if not having:

        return ""

    conditions = []

    for cond in having:

        column = cond.get(
            "column"
        )

        operator = cond.get(
            "operator",
            "="
        )

        value = cond.get(
            "value"
        )

        conditions.append(
            f"{column} "
            f"{operator} "
            f"{format_sql_value(value)}"
        )

    return (
        "HAVING "
        + " AND ".join(conditions)
    )


# =================================================
# BUILD JOINS
# =================================================

def build_join_clause(
    joins: list[dict]
) -> str:

    if not joins:

        return ""
    
    def qualify_column(
        table: str,
        column: str
    ) -> str:

        if "." in column:
            return column

        return f"{table}.{column}"

    clauses = []

    for join in joins:

        join_type = join.get(
            "join_type",
            "INNER"
        ).upper()

        allowed_join_types = [

            "INNER",
            "LEFT",
            "RIGHT",
            "FULL"
        ]

        if join_type not in allowed_join_types:

            join_type = "INNER"

        left_table = join.get(
            "left_table"
        )

        right_table = join.get(
            "right_table"
        )

        left_column = join.get(
            "left_column"
        )

        right_column = join.get(
            "right_column"
        )

        clauses.append(
            f"{join_type} JOIN "
            f"{right_table} "
            f"ON "
            f"{qualify_column(left_table, left_column)} "
            f"= "
            f"{qualify_column(right_table, right_column)}"
        )

    return "\n".join(clauses)


# =================================================
# BUILD CTE CLAUSE
# =================================================

def build_cte_clause(
    ctes: list[dict]
) -> str:

    if not ctes:

        return ""

    clauses = []

    for cte in ctes:

        name = cte.get(
            "name"
        )

        query = cte.get(
            "query"
        )

        if not name or not query:

            continue

        clauses.append(
            f"{name} AS (\n{query}\n)"
        )

    if not clauses:

        return ""

    return (
        "WITH "
        + ",\n".join(clauses)
    )

# =================================================
# BUILD SELECT
# =================================================

def build_select_query(
    plan: QueryPlan
) -> str:

    select_parts = []

    # -------------------------------------------------
    # DISTINCT
    # -------------------------------------------------

    distinct_sql = ""

    if plan.distinct:

        distinct_sql = "DISTINCT "

    # -------------------------------------------------
    # AGGREGATION DETECTION
    # -------------------------------------------------

    has_aggregations = (
        len(plan.aggregations) > 0
    )

    # -------------------------------------------------
    # GROUP BY COLUMNS
    # -------------------------------------------------

    if has_aggregations:

        # ---------------------------------------------
        # GROUP BY COLUMNS
        # ---------------------------------------------

        if plan.group_by:

            select_parts.extend(
                plan.group_by
            )

        # ---------------------------------------------
        # AGGREGATION EXPRESSIONS
        # ---------------------------------------------

        for agg in plan.aggregations:

            function = agg.get(
                "function"
            )

            column = agg.get(
                "column",
                "*"
            )

            alias = agg.get(
                "alias"
            )

            agg_sql = (
                f"{function}({column})"
            )

            if alias:

                agg_sql += (
                    f" AS {alias}"
                )

            select_parts.append(
                agg_sql
            )

    # -------------------------------------------------
    # NORMAL SELECT
    # -------------------------------------------------

    else:

        if plan.columns:

            select_parts.extend(
                plan.columns
            )

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------

    if not select_parts:

        select_parts.append("*")
    

    # -------------------------------------------------
    # FINAL COLUMN SQL
    # -------------------------------------------------

    columns_sql = ", ".join(
        select_parts
    )
    # -------------------------------------------------
    # TABLES
    # -------------------------------------------------

    # -------------------------------------------------
    # PRIMARY TABLE
    # -------------------------------------------------

    if not plan.table:

        raise ValueError(
            "No primary table provided"
        )

    from_sql = plan.table

    sql = f"""
SELECT {distinct_sql}{columns_sql}
FROM {from_sql}
""".strip()

    # -------------------------------------------------
    # JOINS
    # -------------------------------------------------

    join_clause = build_join_clause(
        plan.joins
    )

    if join_clause:

        sql += f"\n{join_clause}"

    # -------------------------------------------------
    # WHERE
    # -------------------------------------------------

    where_clause = build_where_clause(
        plan.conditions
    )

    if where_clause:

        sql += f"\n{where_clause}"

    # -------------------------------------------------
    # GROUP BY
    # -------------------------------------------------

    group_clause = build_group_by_clause(
        plan.group_by
    )

    if group_clause:

        sql += f"\n{group_clause}"

    # -------------------------------------------------
    # HAVING
    # -------------------------------------------------

    having_clause = build_having_clause(
        plan.having
    )

    if having_clause:

        sql += f"\n{having_clause}"

    # -------------------------------------------------
    # ORDER BY
    # -------------------------------------------------

    order_clause = build_order_by_clause(
        plan.order_by
    )

    if order_clause:

        sql += f"\n{order_clause}"

    # -------------------------------------------------
    # LIMIT
    # -------------------------------------------------

    if plan.limit is not None:

        sql += (
            f"\nLIMIT {plan.limit}"
        )

    return sql


# =================================================
# BUILD INSERT
# =================================================

def build_insert_query(
    plan: QueryPlan
) -> str:

    columns = []
    values = []

    for item in plan.set_values:

        columns.append(
            item.get("column")
        )

        values.append(
            format_sql_value(
                item.get("value")
            )
        )
    
    if not columns:

        raise ValueError(
            "No INSERT values provided"
        )

    columns_sql = ", ".join(columns)

    values_sql = ", ".join(values)

    return f"""
INSERT INTO {plan.table}
({columns_sql})
VALUES ({values_sql})
""".strip()


# =================================================
# BUILD UPDATE
# =================================================

def build_update_query(
    plan: QueryPlan
) -> str:

    set_clauses = []

    for item in plan.set_values:

        column = item.get(
            "column"
        )

        operation = item.get(
            "operation",
            "set"
        )

        value = format_sql_value(
            item.get("value")
        )

        if operation in [
    "increment",
    "add"
]:

            set_clauses.append(
                f"{column} = "
                f"{column} + {value}"
            )

        elif operation in [
    "decrement",
    "subtract"
]:

            set_clauses.append(
                f"{column} = "
                f"{column} - {value}"
            )

        else:

            set_clauses.append(
                f"{column} = {value}"
            )

    # -----------------------------------------
    # SAFETY CHECK
    # -----------------------------------------

    if not set_clauses:

        raise ValueError(
            "No SET values provided"
        )


    sql = f"""
UPDATE {plan.table}
SET {", ".join(set_clauses)}
""".strip()

    where_clause = build_where_clause(
        plan.conditions
    )

    if where_clause:

        sql += f"\n{where_clause}"

    return sql


# =================================================
# BUILD DELETE
# =================================================

def build_delete_query(
    plan: QueryPlan
) -> str:

    sql = f"""
DELETE FROM {plan.table}
""".strip()

    where_clause = build_where_clause(
        plan.conditions
    )

    if where_clause:

        sql += f"\n{where_clause}"

    return sql



# =================================================
# BUILD UNION QUERY
# =================================================

def build_union_query(
    base_query: str,
    unions: list[dict]
) -> str:

    sql = base_query

    for union in unions:

        union_type = union.get(
            "type",
            "UNION"
        ).upper()

        query = union.get(
            "query"
        )

        if not query:

            continue

        sql += (
            f"\n{union_type}\n"
            f"{query}"
        )

    return sql


# =================================================
# MAIN BUILDER
# =================================================

def build_sql_query(
    plan: QueryPlan
) -> str:

    operation = (
        plan.operation.upper()
    )

    # -------------------------------------------------
    # BASE SQL
    # -------------------------------------------------

    if operation == "SELECT":

        sql = build_select_query(
            plan
        )

    elif operation == "INSERT":

        sql = build_insert_query(
            plan
        )

    elif operation == "UPDATE":

        sql = build_update_query(
            plan
        )

    elif operation == "DELETE":

        sql = build_delete_query(
            plan
        )

    else:

        raise ValueError(
            f"Unsupported operation: "
            f"{operation}"
        )

    # -------------------------------------------------
    # UNIONS
    # -------------------------------------------------

    if plan.unions:

        sql = build_union_query(

            base_query=sql,

            unions=plan.unions
        )

    # -------------------------------------------------
    # CTEs
    # -------------------------------------------------

    cte_clause = build_cte_clause(
        plan.ctes
    )

    if cte_clause:

        sql = (
            f"{cte_clause}\n"
            f"{sql}"
        )

    return sql