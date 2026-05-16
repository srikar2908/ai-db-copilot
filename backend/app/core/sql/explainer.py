from sqlglot import parse_one

from sqlglot.expressions import (
    Select,
    Update,
    Delete,
    Insert,
    Table,
    Column
)


# -------------------------------------------------
# EXPLAIN SQL
# -------------------------------------------------

def explain_sql(
    sql: str
):

    try:

        parsed = parse_one(sql)

        operation = parsed.key.upper()

        tables = []

        columns = []

        summary = ""

        # -----------------------------------------
        # TABLES
        # -----------------------------------------

        for table in parsed.find_all(Table):

            tables.append(
                table.name
            )

        # -----------------------------------------
        # COLUMNS
        # -----------------------------------------

        for column in parsed.find_all(Column):

            columns.append(
                column.name
            )

        tables = list(set(tables))

        columns = list(set(columns))

        # -----------------------------------------
        # SELECT
        # -----------------------------------------

        if isinstance(parsed, Select):

            summary = (

                f"This query retrieves data from "
                f"{', '.join(tables)} table(s)."
            )

        # -----------------------------------------
        # UPDATE
        # -----------------------------------------

        elif isinstance(parsed, Update):

            summary = (

                f"This query updates records in "
                f"{', '.join(tables)} table(s)."
            )

        # -----------------------------------------
        # DELETE
        # -----------------------------------------

        elif isinstance(parsed, Delete):

            summary = (

                f"This query deletes records from "
                f"{', '.join(tables)} table(s)."
            )

        # -----------------------------------------
        # INSERT
        # -----------------------------------------

        elif isinstance(parsed, Insert):

            summary = (

                f"This query inserts records into "
                f"{', '.join(tables)} table(s)."
            )

        else:

            summary = (
                "SQL operation identified."
            )

        # -----------------------------------------
        # RETURN
        # -----------------------------------------

        return {

            "success": True,

            "operation": operation,

            "tables": tables,

            "columns": columns,

            "summary": summary
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }