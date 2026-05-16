from sqlglot import parse_one
from sqlglot.errors import ParseError
from sqlglot.expressions import Select


DEFAULT_LIMIT = 100


# =================================================
# ENSURE LIMIT
# =================================================

def ensure_limit(ast):

    if not isinstance(ast, Select):

        return ast

    limit_clause = ast.args.get("limit")

    if limit_clause:

        return ast

    return ast.limit(DEFAULT_LIMIT)


# =================================================
# NORMALIZE SQL
# =================================================

def normalize_sql(

    sql: str

) -> str:

    try:

        ast = parse_one(sql)

    except ParseError:

        return sql

    # -----------------------------------------
    # FORCE LIMIT
    # -----------------------------------------

    ast = ensure_limit(ast)

    # -----------------------------------------
    # RETURN PRETTY SQL
    # -----------------------------------------

    return ast.sql(
        pretty=True
    )