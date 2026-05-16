from typing import Any

from app.core.sql.parser import (
    parse_sql_metadata
)


# =================================================
# RISK PRIORITY
# =================================================

RISK_PRIORITY = {

    "low": 1,

    "medium": 2,

    "high": 3,

    "blocked": 4
}


# =================================================
# DETECT RISK FROM METADATA
# =================================================

def detect_risk_level(
    metadata: dict[str, Any]
) -> str:

    operation = metadata.get(
        "operation",
        "UNKNOWN"
    ).upper()

    has_where = metadata.get(
        "has_where",
        False
    )

    joins = metadata.get(
        "joins",
        []
    )

    # -----------------------------------------
    # DELETE
    # -----------------------------------------

    if operation == "DELETE":

        if not has_where:

            return "blocked"

        return "high"

    # -----------------------------------------
    # UPDATE
    # -----------------------------------------

    if operation == "UPDATE":

        if not has_where:

            return "blocked"

        return "medium"

    # -----------------------------------------
    # INSERT
    # -----------------------------------------

    if operation == "INSERT":

        return "medium"

    # -----------------------------------------
    # SELECT
    # -----------------------------------------

    if operation == "SELECT":

        if len(joins) >= 3:

            return "medium"

        return "low"

    return "blocked"


# =================================================
# COMPARE TABLES
# =================================================

def compare_tables(
    original_tables: list[str],
    edited_tables: list[str]
):

    original_set = set(original_tables)

    edited_set = set(edited_tables)

    added = list(
        edited_set - original_set
    )

    removed = list(
        original_set - edited_set
    )

    return {

        "changed":
            original_set != edited_set,

        "added":
            added,

        "removed":
            removed
    }


# =================================================
# COMPARE OPERATIONS
# =================================================

def compare_operations(
    original_operation: str,
    edited_operation: str
):

    return {

        "changed":
            original_operation
            !=
            edited_operation,

        "original":
            original_operation,

        "edited":
            edited_operation
    }


# =================================================
# REVIEW SQL EDIT
# =================================================

def review_sql_edit(

    original_sql: str,

    edited_sql: str
) -> dict[str, Any]:

    # -----------------------------------------
    # PARSE SQL
    # -----------------------------------------

    original_metadata = (
        parse_sql_metadata(
            original_sql
        )
    )

    edited_metadata = (
        parse_sql_metadata(
            edited_sql
        )
    )

    # -----------------------------------------
    # OPERATIONS
    # -----------------------------------------

    operation_review = (
        compare_operations(

            original_metadata["operation"],

            edited_metadata["operation"]
        )
    )

    # -----------------------------------------
    # TABLES
    # -----------------------------------------

    table_review = compare_tables(

        original_metadata["tables"],

        edited_metadata["tables"]
    )

    # -----------------------------------------
    # WHERE REMOVAL
    # -----------------------------------------

    removed_where_clause = (

        original_metadata["has_where"]

        and

        not edited_metadata["has_where"]
    )

    # -----------------------------------------
    # RISK ANALYSIS
    # -----------------------------------------

    original_risk = detect_risk_level(
        original_metadata
    )

    edited_risk = detect_risk_level(
        edited_metadata
    )

    risk_escalated = (

        RISK_PRIORITY[edited_risk]

        >

        RISK_PRIORITY[original_risk]
    )

    # -----------------------------------------
    # WARNINGS
    # -----------------------------------------

    warnings = []

    if operation_review["changed"]:

        warnings.append(

            f"Operation changed from "

            f"{operation_review['original']} "

            f"to "

            f"{operation_review['edited']}"
        )

    if table_review["changed"]:

        warnings.append(
            "Target tables changed"
        )

    if removed_where_clause:

        warnings.append(
            "WHERE clause removed"
        )

    if risk_escalated:

        warnings.append(
            f"Risk escalated from "
            f"{original_risk} "
            f"to "
            f"{edited_risk}"
        )

    # -----------------------------------------
    # SAFE EXECUTION
    # -----------------------------------------

    safe_to_execute = True

    if edited_risk == "blocked":

        safe_to_execute = False

    # -----------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------

    return {

        "safe_to_execute":
            safe_to_execute,

        "operation_changed":
            operation_review["changed"],

        "table_changed":
            table_review["changed"],

        "removed_where_clause":
            removed_where_clause,

        "risk_escalated":
            risk_escalated,

        "original_risk":
            original_risk,

        "edited_risk":
            edited_risk,

        "original_metadata":
            original_metadata,

        "edited_metadata":
            edited_metadata,

        "warnings":
            warnings
    }