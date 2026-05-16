from langgraph.graph import (
    StateGraph,
    END
)

from app.core.graph.checkpointer import (
    checkpointer
)

from app.core.graph.state import (
    CopilotState
)

from app.core.graph.nodes import (

    load_memory_node,

    extract_intent_node,

    clarification_node,

    generate_query_plan_node,

    authorize_query_node,

    validate_sql_node,

    classify_risk_node,

    request_sql_review_node,

    execute_query_node
)

from app.core.graph.routing import (

    route_after_clarification,

    route_after_validation,

    route_after_risk,

    route_after_sql_review
)


def build_graph():

    workflow = StateGraph(
        CopilotState
    )

    # -------------------------------------------------
    # NODES
    # -------------------------------------------------

    workflow.add_node(
        "load_memory_node",
        load_memory_node
    )

    workflow.add_node(
        "extract_intent_node",
        extract_intent_node
    )

    workflow.add_node(
        "clarification_node",
        clarification_node
    )

    workflow.add_node(
        "generate_query_plan_node",
        generate_query_plan_node
    )

    # -------------------------------------------------
    # NEW RBAC NODE
    # -------------------------------------------------

    workflow.add_node(
        "authorize_query_node",
        authorize_query_node
    )

    workflow.add_node(
        "validate_sql_node",
        validate_sql_node
    )

    workflow.add_node(
        "classify_risk_node",
        classify_risk_node
    )

    workflow.add_node(
        "request_sql_review_node",
        request_sql_review_node
    )

    workflow.add_node(
        "execute_query_node",
        execute_query_node
    )

    # -------------------------------------------------
    # ENTRY POINT
    # -------------------------------------------------

    workflow.set_entry_point(
        "load_memory_node"
    )

    # -------------------------------------------------
    # FLOW
    # -------------------------------------------------

    workflow.add_edge(
        "load_memory_node",
        "extract_intent_node"
    )

    workflow.add_edge(
        "extract_intent_node",
        "clarification_node"
    )

    # -------------------------------------------------
    # CLARIFICATION ROUTING
    # -------------------------------------------------

    workflow.add_conditional_edges(

        "clarification_node",

        route_after_clarification,

        {

            "generate_query_plan":
                "generate_query_plan_node",

            "validate_sql":
                "validate_sql_node",

            "end":
                END
        }
    )

    # -------------------------------------------------
    # PLAN → RBAC
    # -------------------------------------------------

    workflow.add_edge(
        "generate_query_plan_node",
        "authorize_query_node"
    )

    # -------------------------------------------------
    # RBAC → VALIDATION
    # -------------------------------------------------

    workflow.add_edge(
        "authorize_query_node",
        "validate_sql_node"
    )

    # -------------------------------------------------
    # VALIDATION ROUTING
    # -------------------------------------------------

    workflow.add_conditional_edges(

        "validate_sql_node",

        route_after_validation,

        {

            "classify_risk":
                "classify_risk_node",

            "end":
                END
        }
    )

    # -------------------------------------------------
    # RISK ROUTING
    # -------------------------------------------------

    workflow.add_conditional_edges(

        "classify_risk_node",

        route_after_risk,

        {

            "request_sql_review":
                "request_sql_review_node",

            "end":
                END
        }
    )

    # -------------------------------------------------
    # SQL REVIEW ROUTING
    # -------------------------------------------------

    workflow.add_conditional_edges(

        "request_sql_review_node",

        route_after_sql_review,

        {

            "execute_query":
                "execute_query_node",

            "end":
                END
        }
    )

    # -------------------------------------------------
    # EXECUTION → END
    # -------------------------------------------------

    workflow.add_edge(
        "execute_query_node",
        END
    )

    # -------------------------------------------------
    # COMPILE
    # -------------------------------------------------

    return workflow.compile(
        checkpointer=checkpointer
    )