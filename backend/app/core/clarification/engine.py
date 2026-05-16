from app.models.state import (
    ExtractedIntent
)

from app.core.clarification.models import (
    ClarificationResult
)


def analyze_clarification(
    intent: ExtractedIntent
) -> ClarificationResult:

    missing_fields = []

    # ---------------------------------------------
    # UPDATE
    # ---------------------------------------------

    if intent.operation == "UPDATE":

        if not intent.conditions:

            missing_fields.append(
                "target_conditions"
            )

        if not intent.set_values:

            missing_fields.append(
                "update_values"
            )

    # ---------------------------------------------
    # DELETE
    # ---------------------------------------------

    if intent.operation == "DELETE":

        if not intent.conditions:

            missing_fields.append(
                "delete_conditions"
            )

    # ---------------------------------------------
    # INSERT
    # ---------------------------------------------

    if intent.operation == "INSERT":

        if not intent.set_values:

            missing_fields.append(
                "insert_values"
            )

    # ---------------------------------------------
    # RESULT
    # ---------------------------------------------

    if missing_fields:

        return ClarificationResult(

            requires_clarification=True,

            missing_fields=missing_fields,

            question=build_question(
                missing_fields
            )
        )

    return ClarificationResult(

        requires_clarification=False,

        missing_fields=[]
    )


def build_question(
    missing_fields: list[str]
) -> str:

    if "target_conditions" in missing_fields:

        return (
            "Which records should "
            "be updated?"
        )

    if "update_values" in missing_fields:

        return (
            "What values should "
            "be updated?"
        )

    if "delete_conditions" in missing_fields:

        return (
            "Which records should "
            "be deleted?"
        )

    if "insert_values" in missing_fields:

        return (
            "What values should "
            "be inserted?"
        )

    return "Please provide more details."