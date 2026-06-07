from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Depends
)

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.db.registry import (
    get_database_url
)

from app.api.models import QueryRequest

from app.api.connections import (
    router as connection_router
)

from app.api.auth import (
    router as auth_router
)

from app.api.history import (
    router as history_router
)

from app.core.graph.runtime import (
    graph
)

from app.core.schema.registry import (
    extract_schema_context
)

from app.security.dependencies import (
    get_current_user
)

from app.core.policies.engine import (
    evaluate_sql_policies
)

from app.api.resume import (
    router as resume_router
)

from app.api.routes.approval import (
    router as approval_router
)
from app.utils.time import utc_now
from app.platform.messages import append_conversation_message
from app.platform.schema import ensure_platform_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_platform_schema()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
         "http://localhost:3000",
         "https://ai-db-copilot-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(
    history_router
)

app.include_router(
    connection_router
)

app.include_router(
    auth_router
)

app.include_router(
    resume_router
)

app.include_router(
    approval_router
)

# -------------------------------------------------
# ROOT
# -------------------------------------------------

@app.get("/")
async def root():

    return {
        "message":
            "AI Database Copilot Running"
    }


@app.head("/")
async def root_head():
    return None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.head("/health")
async def health_head():
    return None


# -------------------------------------------------
# GET DATABASE SCHEMA
# -------------------------------------------------

@app.get("/schema")
async def schema_endpoint(

    connection_ref: str,

    current_user=Depends(
        get_current_user
    )
):

    # -------------------------------------------------
    # RESOLVE DATABASE URL
    # -------------------------------------------------

    database_url = await get_database_url(

        tenant_id=current_user["tenant_id"],

        user_id=current_user["user_id"],

        connection_ref=connection_ref
    )

    # -------------------------------------------------
    # EXTRACT SCHEMA
    # -------------------------------------------------

    schema = await extract_schema_context(
        database_url
    )

    return {
        "tables": schema.tables,
        "relevant_tables": schema.relevant_tables,
        "schema_version": schema.schema_version,
        "extracted_at": schema.extracted_at
    }



# -------------------------------------------------
# START QUERY WORKFLOW
# -------------------------------------------------

@app.post("/query")
async def query_endpoint(

    request: QueryRequest,

    current_user=Depends(
        get_current_user
    )
):

    # -------------------------------------------------
    # AUTHENTICATED USER CONTEXT
    # -------------------------------------------------

    tenant_id = current_user[
        "tenant_id"
    ]

    user_id = str(
        current_user[
            "user_id"
        ]
    )

    user_role = current_user[
        "role"
    ]

    await append_conversation_message(
        thread_id=request.thread_id,
        tenant_id=tenant_id,
        user_id=user_id,
        role="user",
        content={"text": request.user_prompt},
    )

    # -------------------------------------------------
    # RESOLVE DATABASE URL
    # -------------------------------------------------

    database_url = await get_database_url(

        tenant_id=current_user["tenant_id"],

        user_id=current_user["user_id"],

        connection_ref=request.connection_ref
    )

    # -------------------------------------------------
    # EXTRACT SCHEMA
    # -------------------------------------------------

    schema = await extract_schema_context(
        database_url
    )

    # -------------------------------------------------
    # INITIAL GRAPH STATE
    # -------------------------------------------------

    initial_state = {

        "session_id":
            request.thread_id,

        "tenant_id":
            current_user["tenant_id"],

        "user_id":
            user_id,

        "user_role":
            user_role,

        "connection_ref":
            request.connection_ref,

        "user_prompt":
            request.user_prompt,

        "schema_context":
            schema,


        "extracted_intent":
            None,

        "clarification_response":
            None,

        "query_plan":
            None,

        "generated_sql":
            None,

        "validation_result":
            None,

        "cost_analysis":
            None,

        "risk_level":
            None,

        "approval_status":
            None,

        "approved_sql":
            None,

        "approval_timestamp":
            None,

        "execution_result":
            None,

        "node_trace":
            [],

        "errors":
            [],

        "created_at":
            utc_now(),

        "updated_at":
            utc_now()
    }

    # -------------------------------------------------
    # EXECUTE GRAPH
    # -------------------------------------------------

    result = await graph.ainvoke(

        initial_state,

        config={
            "configurable": {
                "thread_id":
                    request.thread_id
            }
        }
    )

    await append_conversation_message(
        thread_id=request.thread_id,
        tenant_id=tenant_id,
        user_id=user_id,
        role="assistant",
        content={
            "generated_sql": result.get("generated_sql"),
            "workflow_status": str(result.get("workflow_status")),
            "errors": result.get("errors", []),
        },
    )

    return result


# -------------------------------------------------
# APPROVE + RESUME
# -------------------------------------------------

@app.post("/test-policy")
async def test_policy(
    payload: dict
):

    sql = payload.get("sql")

    result = evaluate_sql_policies(
        sql
    )

    return result
