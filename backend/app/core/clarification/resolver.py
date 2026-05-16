from copy import deepcopy

from app.models.state import (
    ExtractedIntent,
    SchemaContext
)


def resolve_clarification(

    intent: ExtractedIntent,

    schema_context: SchemaContext,

    clarification_fields: list[str],

    clarification_response: str
) -> ExtractedIntent:

    # -------------------------------------------------
    # SAFE COPY
    # -------------------------------------------------

    resolved_intent = deepcopy(
        intent
    )

    tables = schema_context.tables

    # -------------------------------------------------
    # AUTO-RESOLVE TARGET TABLE
    # -------------------------------------------------

    if not resolved_intent.target_tables:

        # ---------------------------------------------
        # SINGLE TABLE DATABASE
        # ---------------------------------------------

        if len(tables) == 1:

            inferred_table = list(
                tables.keys()
            )[0]

            resolved_intent.target_tables = [
                inferred_table
            ]

        # ---------------------------------------------
        # COLUMN MATCHING
        # ---------------------------------------------

        elif resolved_intent.target_columns:

            matched_tables = []

            for table_name, columns in tables.items():

                for target_column in (
                    resolved_intent.target_columns
                ):

                    if target_column in columns:

                        matched_tables.append(
                            table_name
                        )

            matched_tables = list(
                set(matched_tables)
            )

            if len(matched_tables) == 1:

                resolved_intent.target_tables = (
                    matched_tables
                )

    # -------------------------------------------------
    # TARGET TABLE
    # -------------------------------------------------

    target_table = None

    if resolved_intent.target_tables:

        target_table = (
            resolved_intent.target_tables[0]
        )

    # -------------------------------------------------
    # TABLE COLUMNS
    # -------------------------------------------------

    table_columns = []

    if target_table:

        table_columns = tables.get(
            target_table,
            []
        )

    # -------------------------------------------------
    # RESOLVE CONDITIONS
    # -------------------------------------------------

    if (

        "target_conditions"

        in

        clarification_fields

        and

        not resolved_intent.conditions
    ):

        candidate_column = None

        priority_columns = [

            "name",
            "title",
            "email",
            "username",
            "id"
        ]

        for col in priority_columns:

            if col in table_columns:

                candidate_column = col

                break

        # ---------------------------------------------
        # FALLBACK
        # ---------------------------------------------

        if not candidate_column and table_columns:

            candidate_column = (
                table_columns[0]
            )

        # ---------------------------------------------
        # PATCH CONDITIONS
        # ---------------------------------------------

        if candidate_column:

            parsed_entity = (
                extract_entity_name(
                    clarification_response
                )
            )

            resolved_intent.conditions = [

                {
                    "column":
                        candidate_column,

                    "operator": "=",

                    "value":
                        parsed_entity
                }
            ]

    # -------------------------------------------------
    # RESOLVE UPDATE VALUES
    # -------------------------------------------------

    if (

        "update_values"

        in

        clarification_fields

        and

        not resolved_intent.set_values
    ):

        target_column = None

        # ---------------------------------------------
        # USE TARGET COLUMN
        # ---------------------------------------------

        if resolved_intent.target_columns:

            target_column = (
                resolved_intent
                .target_columns[0]
            )

        # ---------------------------------------------
        # FALLBACK
        # ---------------------------------------------

        elif table_columns:

            target_column = (
                table_columns[0]
            )

        # ---------------------------------------------
        # EXTRACT NUMERIC VALUE
        # ---------------------------------------------

        numeric_value = extract_numeric_value(
            clarification_response
        )

        # ---------------------------------------------
        # PATCH UPDATE VALUE
        # ---------------------------------------------

        if (

            target_column

            and

            numeric_value is not None
        ):

            resolved_intent.set_values = [

                {
                    "column":
                        target_column,

                    "operation":
                        "set",

                    "value":
                        numeric_value
                }
            ]

    return resolved_intent


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def extract_numeric_value(
    text: str
):

    import re

    matches = re.findall(
        r"\d+",
        text
    )

    if not matches:

        return None

    return int(matches[0])


def extract_entity_name(
    text: str
):

    import re

    cleaned = re.sub(
        r"\d+",
        "",
        text
    )

    cleaned = cleaned.replace(
        "salary",
        ""
    )

    cleaned = cleaned.replace(
        "update",
        ""
    )

    cleaned = cleaned.replace(
        "set",
        ""
    )

    cleaned = cleaned.replace(
        "for",
        ""
    )

    cleaned = cleaned.strip()

    words = cleaned.split()

    if not words:

        return text.strip()

    return words[-1]