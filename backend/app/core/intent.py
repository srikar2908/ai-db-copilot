import json
import re

from app.core.llm import client

from app.models.state import (
    ExtractedIntent
)

from app.config import settings


# -------------------------------------------------
# NORMALIZE CONDITIONS
# -------------------------------------------------

def normalize_conditions(
    conditions
):

    normalized = []

    for cond in conditions:

        if isinstance(cond, dict):

            normalized.append({

                "column":
                    cond.get("column"),

                "operator":
                    cond.get(
                        "operator",
                        "="
                    ),

                "value":
                    cond.get("value")
            })

        elif isinstance(cond, str):

            match = re.match(
                r"(\w+)\s*([=<>!]+)\s*['\"]?(.*?)['\"]?$",
                cond
            )

            if match:

                column, operator, value = (
                    match.groups()
                )

                normalized.append({

                    "column": column,

                    "operator": operator,

                    "value": value
                })

    return normalized


# -------------------------------------------------
# NORMALIZE ORDER BY
# -------------------------------------------------

def normalize_order_by(
    order_by
):
 
    normalized = []
 
    for item in order_by:
 
        if isinstance(item, dict):
 
            # BUG FIX: accept "order" as alias for "direction"
            # LLM sometimes emits {"column": "salary", "order": "DESC"}
            direction = (
                item.get("direction")
                or item.get("order")
                or "ASC"
            ).upper()
 
            normalized.append({
 
                "column":
                    item.get("column"),
 
                "direction":
                    direction
            })
 
        elif isinstance(item, str):
 
            parts = item.split()
 
            if len(parts) >= 2:
 
                normalized.append({
 
                    "column":
                        parts[0],
 
                    "direction":
                        parts[1].upper()
                })
 
            elif len(parts) == 1:
 
                normalized.append({
 
                    "column":
                        parts[0],
 
                    "direction":
                        "ASC"
                })
 
    return normalized


# -------------------------------------------------
# NORMALIZE SET VALUES
# -------------------------------------------------

def normalize_set_values(
    set_values
):

    normalized = []

    for item in set_values:

        if not isinstance(item, dict):

            continue

        column = item.get(
            "column"
        )

        value = item.get(
            "value"
        )

        operation = item.get(
            "operation"
        )

        if not operation:

            operator = item.get(
                "operator"
            )

            if operator == "+":

                operation = "increment"

            elif operator == "-":

                operation = "decrement"

            else:

                operation = "set"

        if not column:

            continue

        normalized.append({

            "column": column,

            "operation": operation,

            "value": value
        })

    return normalized


# -------------------------------------------------
# NORMALIZE JOINS
# -------------------------------------------------

def normalize_joins(
    joins
):

    normalized = []

    for join in joins:

        if not isinstance(join, dict):

            continue

        normalized.append({

            "join_type":
                join.get(
                    "join_type",
                    "INNER"
                ),

            "left_table":
                join.get(
                    "left_table"
                ),

            "right_table":
                join.get(
                    "right_table"
                ),

            "left_column":
                join.get(
                    "left_column"
                ),

            "right_column":
                join.get(
                    "right_column"
                )
        })

    return normalized


# -------------------------------------------------
# NORMALIZE AGGREGATIONS
# -------------------------------------------------

def normalize_aggregations(
    aggregations
):

    normalized = []

    for agg in aggregations:

        if not isinstance(agg, dict):

            continue

        normalized.append({

            "function":
                agg.get(
                    "function"
                ),

            "column":
                agg.get(
                    "column"
                ),

            "alias":
                agg.get(
                    "alias"
                )
        })

    return normalized


# -------------------------------------------------
# NORMALIZE GROUP BY
# -------------------------------------------------

def normalize_group_by(
    group_by
):

    if not group_by:

        return []

    if isinstance(group_by, list):

        return group_by

    return []


# -------------------------------------------------
# NORMALIZE HAVING
# -------------------------------------------------

def normalize_having(
    having
):

    return normalize_conditions(
        having
    )


# -------------------------------------------------
# NORMALIZE UNIONS
# -------------------------------------------------

def normalize_unions(
    unions
):

    normalized = []

    for item in unions:

        if not isinstance(item, dict):

            continue

        normalized.append({

            "type":
                item.get(
                    "type",
                    "UNION"
                ),

            "query":
                item.get(
                    "query"
                )
        })

    return normalized


# -------------------------------------------------
# NORMALIZE CTEs
# -------------------------------------------------

def normalize_ctes(
    ctes
):

    normalized = []

    for item in ctes:

        if not isinstance(item, dict):

            continue

        normalized.append({

            "name":
                item.get("name"),

            "query":
                item.get("query")
        })

    return normalized


# -------------------------------------------------
# EXTRACT INTENT
# -------------------------------------------------

async def extract_intent(

    prompt: str,

    memory: dict | None = None

) -> ExtractedIntent:

    system_prompt = f"""
You are an enterprise AI SQL intent extraction engine.

Return ONLY valid JSON.

NO markdown.
NO explanation.
NO code blocks.

--------------------------------------------------
MEMORY
--------------------------------------------------

{memory}

--------------------------------------------------
CAPABILITIES
--------------------------------------------------

You support:

- SELECT
- INSERT
- UPDATE
- DELETE
- JOIN
- UNION
- CTE
- GROUP BY
- HAVING
- DISTINCT
- AGGREGATIONS

--------------------------------------------------
RULES
--------------------------------------------------

1. Never hallucinate schema objects.

2. Preserve conversational context.

3. Infer joins when needed.

4. Conditions format:

[
  {{
    "column": "department",
    "operator": "=",
    "value": "HR"
  }}
]

5. Join format:

[
  {{
    "join_type": "INNER",
    "left_table": "employees",
    "right_table": "departments",
    "left_column": "department_id",
    "right_column": "id"
  }}
]

6. Aggregation format:

[
  {{
    "function": "AVG",
    "column": "salary",
    "alias": "avg_salary"
  }}
]

7. set_values format:

[
  {{
    "column": "salary",
    "operation": "set",
    "value": 50000
  }}
]

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

{{
  "operation": "SELECT",

  "target_tables": [],

  "target_columns": [],

  "distinct": false,

  "conditions": [],

  "joins": [],

  "aggregations": [],

  "group_by": [],

  "having": [],

  "order_by": [],

  "row_limit": 10,

  "set_values": [],

  "unions": [],

  "ctes": [],

  "requires_clarification": false
}}
"""

    response = client.chat.completions.create(

        model=settings.GROQ_MODEL,

        temperature=0,

        messages=[

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[
        0
    ].message.content.strip()

    # -------------------------------------------------
    # CLEAN MARKDOWN
    # -------------------------------------------------

    content = re.sub(
        r"```json|```",
        "",
        content
    ).strip()

    # -------------------------------------------------
    # PARSE JSON
    # -------------------------------------------------

    try:

        parsed = json.loads(
            content
        )

    except Exception:

        parsed = {}

    # -------------------------------------------------
    # SUPPORT LEGACY set
    # -------------------------------------------------

    parsed["set_values"] = parsed.get(
        "set_values",
        parsed.get("set", [])
    )

    # -------------------------------------------------
    # NORMALIZATION
    # -------------------------------------------------

    conditions = normalize_conditions(
        parsed.get("conditions", [])
    )

    order_by = normalize_order_by(
        parsed.get("order_by", [])
    )

    set_values = normalize_set_values(
        parsed.get("set_values", [])
    )

    joins = normalize_joins(
        parsed.get("joins", [])
    )

    aggregations = normalize_aggregations(
        parsed.get(
            "aggregations",
            []
        )
    )

    group_by = normalize_group_by(
        parsed.get("group_by", [])
    )

    having = normalize_having(
        parsed.get("having", [])
    )

    unions = normalize_unions(
        parsed.get("unions", [])
    )

    ctes = normalize_ctes(
        parsed.get("ctes", [])
    )

    # -------------------------------------------------
    # RETURN
    # -------------------------------------------------

    return ExtractedIntent(

        operation=parsed.get(
            "operation",
            "SELECT"
        ),

        confidence=0.95,

        target_tables=parsed.get(
            "target_tables",
            []
        ),

        target_columns=parsed.get(
            "target_columns",
            []
        ),

        distinct=parsed.get(
            "distinct",
            False
        ),

        conditions=conditions,

        joins=joins,

        aggregations=aggregations,

        group_by=group_by,

        having=having,

        order_by=order_by,

        row_limit=parsed.get(
            "row_limit"
        ),

        set_values=set_values,

        unions=unions,

        ctes=ctes,

        requires_clarification=parsed.get(
            "requires_clarification",
            False
        ),

        clarification_questions=parsed.get(
            "clarification_questions",
            []
        ),

        raw_llm_response=content
    )