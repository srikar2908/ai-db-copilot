from typing import Any

import sqlglot
from sqlglot import exp


# =================================================
# SAFE PARSE
# =================================================

def parse_sql(
    sql: str
):

    if not sql:

        raise ValueError(
            "SQL query is empty"
        )

    try:

        return sqlglot.parse_one(sql)

    except Exception as e:

        raise ValueError(
            f"SQL parsing failed: {str(e)}"
        )


# =================================================
# EXTRACT TABLES
# =================================================

def extract_tables(
    parsed
) -> list[str]:

    tables = set()

    for table in parsed.find_all(exp.Table):

        if table.name:

            tables.add(table.name)

    return sorted(list(tables))


# =================================================
# EXTRACT COLUMNS
# =================================================

def extract_columns(
    parsed
) -> list[str]:

    columns = set()

    for column in parsed.find_all(exp.Column):

        column_name = column.name

        if column_name:

            columns.add(column_name)

    return sorted(list(columns))


# =================================================
# EXTRACT JOINS
# =================================================

def extract_joins(
    parsed
) -> list[dict]:

    joins = []

    for join in parsed.find_all(exp.Join):

        join_data = {

            "join_type":
                str(join.args.get("kind", "INNER"))
                .upper(),

            "table":
                None,

            "on":
                None
        }

        # -----------------------------------------
        # TABLE
        # -----------------------------------------

        join_table = join.this

        if isinstance(join_table, exp.Table):

            join_data["table"] = (
                join_table.name
            )

        # -----------------------------------------
        # ON CONDITION
        # -----------------------------------------

        on_clause = join.args.get("on")

        if on_clause:

            join_data["on"] = (
                on_clause.sql()
            )

        joins.append(join_data)

    return joins


# =================================================
# EXTRACT WHERE
# =================================================

def extract_where_conditions(
    parsed
) -> list[str]:

    conditions = []

    where_clause = parsed.args.get(
        "where"
    )

    if not where_clause:

        return conditions

    # -----------------------------------------
    # SPLIT CONDITIONS
    # -----------------------------------------

    for node in where_clause.walk():

        if isinstance(
            node,
            (
                exp.EQ,
                exp.GT,
                exp.GTE,
                exp.LT,
                exp.LTE,
                exp.NEQ,
                exp.Like,
                exp.In,
            )
        ):

            conditions.append(
                node.sql()
            )

    return conditions


# =================================================
# EXTRACT ORDER BY
# =================================================

def extract_order_by(
    parsed
) -> list[dict]:

    results = []

    order = parsed.args.get(
        "order"
    )

    if not order:

        return results

    for ordered in order.expressions:

        column = ordered.this.sql()

        direction = "ASC"

        if ordered.args.get("desc"):

            direction = "DESC"

        results.append({

            "column": column,

            "direction": direction
        })

    return results


# =================================================
# EXTRACT GROUP BY
# =================================================

def extract_group_by(
    parsed
) -> list[str]:

    results = []

    group = parsed.args.get(
        "group"
    )

    if not group:

        return results

    for expr in group.expressions:

        results.append(
            expr.sql()
        )

    return results


# =================================================
# EXTRACT LIMIT
# =================================================

def extract_limit(
    parsed
):

    limit = parsed.args.get(
        "limit"
    )

    if not limit:

        return None

    try:

        return int(
            limit.expression.name
        )

    except Exception:

        return None


# =================================================
# DETECT OPERATION
# =================================================

def detect_operation(
    parsed
) -> str:

    if isinstance(parsed, exp.Select):

        return "SELECT"

    if isinstance(parsed, exp.Insert):

        return "INSERT"

    if isinstance(parsed, exp.Update):

        return "UPDATE"

    if isinstance(parsed, exp.Delete):

        return "DELETE"

    return "UNKNOWN"


# =================================================
# HAS WHERE
# =================================================

def has_where_clause(
    parsed
) -> bool:

    return (
        parsed.args.get("where")
        is not None
    )


# =================================================
# MAIN SQL PARSER
# =================================================

def parse_sql_metadata(
    sql: str
) -> dict[str, Any]:

    parsed = parse_sql(sql)

    metadata = {

        "operation":
            detect_operation(parsed),

        "tables":
            extract_tables(parsed),

        "columns":
            extract_columns(parsed),

        "joins":
            extract_joins(parsed),

        "where_conditions":
            extract_where_conditions(
                parsed
            ),

        "group_by":
            extract_group_by(parsed),

        "order_by":
            extract_order_by(parsed),

        "limit":
            extract_limit(parsed),

        "has_where":
            has_where_clause(parsed),

        "normalized_sql":
            parsed.sql(
                pretty=True
            )
    }

    return metadata