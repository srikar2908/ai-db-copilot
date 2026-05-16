from sqlglot import parse_one

from sqlglot.errors import ParseError

from sqlglot.expressions import (
    Table,
    Column,
    Delete,
    Update,
    Insert,
    Drop,
    Alter,
    Create,
    Select,
    Union,
    With,
    Join,
    Func,
    Anonymous
)

from app.models.state import (
    ValidationResult,
    SchemaContext
)


# =================================================
# EXTRACT TABLES
# =================================================

def extract_tables(ast):

    return list({

        table.name

        for table in ast.find_all(Table)

        if table.name
    })


# =================================================
# EXTRACT COLUMNS
# =================================================

def extract_columns(ast):

    columns = []

    for col in ast.find_all(Column):

        column_name = col.name

        table_name = col.table

        if table_name:

            columns.append(
                f"{table_name}.{column_name}"
            )

        else:

            columns.append(
                column_name
            )

    return list(set(columns))


# =================================================
# EXTRACT AGGREGATE COLUMNS
# =================================================

def extract_aggregate_columns(ast):

    aggregate_columns = []

    aggregate_functions = {

        "SUM",
        "AVG",
        "COUNT",
        "MIN",
        "MAX"
    }

    for expression in ast.walk():

        if not hasattr(expression, "sql_name"):

            continue

        try:

            func_name = (
                expression.sql_name().upper()
            )

        except Exception:

            continue

        if func_name not in aggregate_functions:

            continue

        for col in expression.find_all(Column):

            if col.table:

                aggregate_columns.append(
                    f"{col.table}.{col.name}"
                )

            else:

                aggregate_columns.append(
                    col.name
                )

    return list(set(aggregate_columns))


# =================================================
# VALIDATE TABLES
# =================================================

def validate_tables(

    extracted_tables,

    valid_tables,

    hallucinated_tables,

    errors

):

    for table in extracted_tables:

        if table not in valid_tables:

            hallucinated_tables.append(
                table
            )

    if hallucinated_tables:

        errors.append(
            f"Unknown tables: "
            f"{hallucinated_tables}"
        )


# =================================================
# VALIDATE COLUMNS
# =================================================

def validate_columns(

    extracted_columns,

    schema_context,

    hallucinated_columns,

    errors

):

    all_valid_columns = set()

    # -----------------------------------------
    # BUILD FULLY QUALIFIED MAP
    # -----------------------------------------

    for table, columns in schema_context.tables.items():

        for column in columns:

            all_valid_columns.add(column)

            all_valid_columns.add(
                f"{table}.{column}"
            )

    # -----------------------------------------
    # VALIDATE
    # -----------------------------------------

    for column in extracted_columns:

        if column == "*":

            continue

        if column not in all_valid_columns:

            hallucinated_columns.append(
                column
            )

    if hallucinated_columns:

        errors.append(

            f"Unknown columns: "
            f"{hallucinated_columns}"
        )


# =================================================
# VALIDATE GROUP BY
# =================================================

def validate_group_by(

    ast,

    errors

):

    if not isinstance(ast, Select):

        return

    group = ast.args.get(
        "group"
    )

    if not group:

        return

    grouped_columns = set()

    for col in group.find_all(Column):

        if col.table:

            grouped_columns.add(
                f"{col.table}.{col.name}"
            )

        else:

            grouped_columns.add(
                col.name
            )

    aggregate_columns = set(
        extract_aggregate_columns(ast)
    )

    selected_columns = set()

    expressions = ast.args.get(
        "expressions",
        []
    )

    for expr in expressions:

        for col in expr.find_all(Column):

            if col.table:

                selected_columns.add(
                    f"{col.table}.{col.name}"
                )

            else:

                selected_columns.add(
                    col.name
                )

    invalid_columns = []

    for col in selected_columns:

        if (

            col not in grouped_columns

            and

            col not in aggregate_columns

        ):

            invalid_columns.append(
                col
            )

    if invalid_columns:

        errors.append(

            "GROUP BY validation failed. "

            f"Columns must be aggregated "
            f"or grouped: {invalid_columns}"
        )


# =================================================
# VALIDATE UNION
# =================================================

def validate_union(

    ast,

    warnings

):

    unions = list(
        ast.find_all(Union)
    )

    if unions:

        warnings.append(
            "UNION query detected"
        )


# =================================================
# VALIDATE CTE
# =================================================

def validate_ctes(

    ast,

    warnings

):

    ctes = list(
        ast.find_all(With)
    )

    if ctes:

        warnings.append(
            "CTE query detected"
        )


# =================================================
# VALIDATE JOINS
# =================================================

def validate_joins(

    ast,

    warnings

):

    joins = list(
        ast.find_all(Join)
    )

    if joins:

        warnings.append(
            "JOIN query detected"
        )


# =================================================
# SAFETY VALIDATION
# =================================================

def validate_mutation_safety(

    ast,

    has_where_clause,

    errors

):

    # UPDATE

    if isinstance(ast, Update):

        if not has_where_clause:

            errors.append(
                "UPDATE statement "
                "missing WHERE clause"
            )

    # DELETE

    if isinstance(ast, Delete):

        if not has_where_clause:

            errors.append(
                "DELETE statement "
                "missing WHERE clause"
            )

    # INSERT

    if isinstance(ast, Insert):

        expression = ast.args.get(
            "expression"
        )

        if not expression:

            errors.append(
                "INSERT statement "
                "missing VALUES"
            )


# =================================================
# BLOCK DDL
# =================================================

def validate_ddl(

    ast,

    errors

):

    if isinstance(

        ast,

        (
            Drop,
            Alter,
            Create
        )
    ):

        errors.append(
            "DDL operations are blocked"
        )



def validate_dangerous_functions(

    ast,

    errors

):

    blocked_functions = {

        "PG_SLEEP",
        "VERSION",
        "CURRENT_DATABASE",
        "CURRENT_USER"
    }

    for func in ast.find_all(Anonymous):

        func_name = func.name.upper()

        if func_name in blocked_functions:

            errors.append(

                f"Blocked function used: "
                f"{func_name}"
            )


def validate_sql_injection_patterns(

    sql,

    errors

):

    dangerous_patterns = [

        ";--",
        "/*",
        "*/",
        " xp_",
        "information_schema",
        "pg_catalog"
    ]

    lowered_sql = sql.lower()

    for pattern in dangerous_patterns:

        if pattern.lower() in lowered_sql:

            errors.append(

                f"Dangerous SQL pattern detected: "
                f"{pattern}"
            )





# =================================================
# VALIDATE LIMIT
# =================================================

def validate_limit(

    ast,

    warnings

):

    if isinstance(ast, Select):

        limit_clause = ast.args.get(
            "limit"
        )

        if not limit_clause:

            warnings.append(
                "No LIMIT clause detected"
            )


# =================================================
# MAIN VALIDATOR
# =================================================

def validate_sql_query(

    sql: str,

    schema_context: SchemaContext

) -> ValidationResult:

    errors = []

    warnings = []

    hallucinated_tables = []

    hallucinated_columns = []

    ast_valid = True

    schema_valid = True

    safety_valid = True

    estimated_cost = None

    

    # =================================================
    # PARSE AST
    # =================================================

    try:

        ast = parse_one(sql)

        where_clause = ast.args.get("where")

        has_where_clause = (
            where_clause is not None
        )

    except ParseError as e:

        return ValidationResult(

            passed=False,

            ast_valid=False,

            schema_valid=False,

            safety_valid=False,

            hallucinated_tables=[],

            hallucinated_columns=[],

            has_where_clause=False,

            estimated_cost=None,

            errors=[str(e)],

            warnings=[]
        )

    # =================================================
    # TABLE EXTRACTION
    # =================================================

    extracted_tables = extract_tables(
        ast
    )

    valid_tables = list(
        schema_context.tables.keys()
    )

    validate_tables(

        extracted_tables=
            extracted_tables,

        valid_tables=
            valid_tables,

        hallucinated_tables=
            hallucinated_tables,

        errors=
            errors
    )

    # =================================================
    # COLUMN EXTRACTION
    # =================================================

    extracted_columns = extract_columns(
        ast
    )

    # valid_columns = []

    # for table in extracted_tables:

    #     valid_columns.extend(

    #         schema_context.tables.get(
    #             table,
    #             []
    #         )
    #     )

    # valid_columns = list(
    #     set(valid_columns)
    # )

    validate_columns(

        extracted_columns=
            extracted_columns,

        schema_context=
            schema_context,

        hallucinated_columns=
            hallucinated_columns,

        errors=
            errors
    )

    # =================================================
    # GROUP BY VALIDATION
    # =================================================

    validate_group_by(

        ast=ast,

        errors=errors
    )

    # =================================================
    # UNION VALIDATION
    # =================================================

    validate_union(

        ast=ast,

        warnings=warnings
    )

    # =================================================
    # CTE VALIDATION
    # =================================================

    validate_ctes(

        ast=ast,

        warnings=warnings
    )

    # =================================================
    # JOIN VALIDATION
    # =================================================

    validate_joins(

        ast=ast,

        warnings=warnings
    )

    # =================================================
    # MUTATION SAFETY
    # =================================================

    validate_mutation_safety(

        ast=ast,

        has_where_clause=
            has_where_clause,

        errors=errors
    )

    # =================================================
    # BLOCK DDL
    # =================================================

    validate_ddl(

        ast=ast,

        errors=errors
    )

    validate_dangerous_functions(

        ast=ast,

        errors=errors
    )

    validate_sql_injection_patterns(

        sql=sql,

        errors=errors
    )


    
    # =================================================
    # LIMIT WARNINGS
    # =================================================

    validate_limit(

        ast=ast,

        warnings=warnings
    )

    # =================================================
    # FINAL STATUS
    # =================================================

    if hallucinated_tables:

        schema_valid = False

    if hallucinated_columns:

        schema_valid = False

    safety_errors = [

        error

        for error in errors

        if not error.startswith(
            "Unknown columns"
        )

        and not error.startswith(
            "Unknown tables"
        )
    ]

    if safety_errors:

        safety_valid = False

    passed = (

        ast_valid

        and

        schema_valid

        and

        safety_valid

        and

        len(errors) == 0
    )

    return ValidationResult(

        passed=passed,

        ast_valid=ast_valid,

        schema_valid=schema_valid,

        safety_valid=safety_valid,

        hallucinated_tables=
            hallucinated_tables,

        hallucinated_columns=
            hallucinated_columns,

        has_where_clause=
            has_where_clause,

        estimated_cost=
            estimated_cost,

        errors=errors,

        warnings=warnings
    )