import sqlglot

from sqlglot import exp

from app.core.policies.models import (
    PolicyResult
)


# -------------------------------------------------
# POLICY CONFIG
# -------------------------------------------------

BLOCKED_OPERATIONS = {

    "DROP",
    "TRUNCATE"
}

MAX_LIMIT = 1000

FORBIDDEN_TABLES = {

    "credit_cards",
    "passwords",
    "secret_keys"
}


# -------------------------------------------------
# MAIN POLICY ENGINE
# -------------------------------------------------

def evaluate_sql_policies(
    sql: str
) -> PolicyResult:

    errors = []

    warnings = []

    risk_level = "low"

    try:

        parsed = sqlglot.parse_one(sql)

    except Exception:

        return PolicyResult(

            allowed=False,

            risk_level="blocked",

            errors=[
                "Failed to parse SQL"
            ],

            warnings=[]
        )

    # -------------------------------------------------
    # BLOCKED OPERATIONS
    # -------------------------------------------------

    operation = parsed.key.upper()

    if operation in BLOCKED_OPERATIONS:

        errors.append(
            f"{operation} operations are blocked"
        )

    # -------------------------------------------------
    # DELETE WITHOUT WHERE
    # -------------------------------------------------

    if isinstance(parsed, exp.Delete):

        if not parsed.args.get("where"):

            errors.append(
                "DELETE without WHERE is blocked"
            )

    # -------------------------------------------------
    # UPDATE WITHOUT WHERE
    # -------------------------------------------------

    if isinstance(parsed, exp.Update):

        if not parsed.args.get("where"):

            errors.append(
                "UPDATE without WHERE is blocked"
            )

    # -------------------------------------------------
    # FORBIDDEN TABLES
    # -------------------------------------------------

    tables = {

        table.name
        for table in parsed.find_all(exp.Table)
    }

    forbidden = tables.intersection(
        FORBIDDEN_TABLES
    )

    if forbidden:

        errors.append(

            f"Forbidden tables accessed: "
            f"{', '.join(forbidden)}"
        )

    # -------------------------------------------------
    # LIMIT ENFORCEMENT
    # ONLY FOR SELECT QUERIES
    # -------------------------------------------------

    if isinstance(parsed, exp.Select):

        limit = parsed.args.get("limit")

        if limit:

            try:

                limit_value = int(
                    limit.expression.name
                )

                if limit_value > MAX_LIMIT:

                    errors.append(

                        f"LIMIT exceeds maximum "
                        f"allowed ({MAX_LIMIT})"
                    )

            except Exception:

                warnings.append(
                    "Unable to validate LIMIT"
                )

        else:

            warnings.append(
                "Query has no LIMIT"
            )

            risk_level = "medium"

    # -------------------------------------------------
    # FINAL RESULT
    # -------------------------------------------------

    allowed = len(errors) == 0

    if not allowed:

        risk_level = "blocked"

    return PolicyResult(

        allowed=allowed,

        risk_level=risk_level,

        errors=errors,

        warnings=warnings
    )