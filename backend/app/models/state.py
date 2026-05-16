from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

from app.core.graph.status import WorkflowStatus


class SchemaContext(BaseModel):
    tables: dict[str, list[str]] = Field(default_factory=dict)
    relevant_tables: list[str] = Field(default_factory=list)
    schema_version: str
    extracted_at: datetime


class ExtractedIntent(BaseModel):

    # -------------------------------------------------
    # OPERATION
    # -------------------------------------------------

    operation: Literal[
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE"
    ]

    confidence: float

    # -------------------------------------------------
    # TABLES
    # -------------------------------------------------

    target_tables: list[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # COLUMNS
    # -------------------------------------------------

    target_columns: list[str] = Field(
        default_factory=list
    )

    distinct: bool = False

    # -------------------------------------------------
    # CONDITIONS
    # -------------------------------------------------

    conditions: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # JOINS
    # -------------------------------------------------

    joins: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # AGGREGATIONS
    # -------------------------------------------------

    aggregations: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # GROUP BY
    # -------------------------------------------------

    group_by: list[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # HAVING
    # -------------------------------------------------

    having: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # ORDERING
    # -------------------------------------------------

    order_by: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # LIMIT
    # -------------------------------------------------

    row_limit: int | None = None

    # -------------------------------------------------
    # INSERT / UPDATE
    # -------------------------------------------------

    set_values: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # UNIONS
    # -------------------------------------------------

    unions: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # CTEs
    # -------------------------------------------------

    ctes: list[dict] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # CLARIFICATION
    # -------------------------------------------------

    requires_clarification: bool = False

    clarification_questions: list[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # RAW OUTPUT
    # -------------------------------------------------

    raw_llm_response: str


class QueryPlan(BaseModel):

    operation: str

    table: str | None = None

    tables: list[str] = Field(
        default_factory=list
    )

    columns: list[str] = Field(
        default_factory=list
    )

    conditions: list[dict] = Field(
        default_factory=list
    )

    joins: list[dict] = Field(
        default_factory=list
    )

    aggregations: list[dict] = Field(
        default_factory=list
    )

    group_by: list[str] = Field(
        default_factory=list
    )

    having: list[dict] = Field(
        default_factory=list
    )

    order_by: list[dict] = Field(
        default_factory=list
    )

    unions: list[dict] = Field(
        default_factory=list
    )

    ctes: list[dict] = Field(
        default_factory=list
    )

    distinct: bool = False

    limit: Optional[int] = None

    set_values: list[dict] = Field(
        default_factory=list
    )


class ValidationResult(BaseModel):
    passed: bool

    ast_valid: bool

    schema_valid: bool

    safety_valid: bool

    hallucinated_tables: list[str] = Field(default_factory=list)

    hallucinated_columns: list[str] = Field(default_factory=list)

    has_where_clause: bool = True

    estimated_cost: Optional[float] = None

    errors: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    success: bool

    rows_affected: int = 0

    rows_returned: int = 0

    data: Optional[list[dict]] = None

    execution_time_ms: float = 0

    error: Optional[str] = None



class ClarificationState(BaseModel):
    required: bool = False

    question: str | None = None

    missing_fields: list[str] = []

    user_response: str | None = None

    resume_from_node: str | None = None



class ApprovalState(BaseModel):
    required: bool = False

    approved: bool | None = None

    reason: str | None = None



class ConversationContext(BaseModel):
    active_table: str | None = None

    active_filters: dict = {}

    selected_columns: list[str] = []

    last_query_type: str | None = None

    referenced_entities: list[str] = []



class WorkflowState(BaseModel):

    # -------------------------------------------------
    # REQUEST INFO
    # -------------------------------------------------

    session_id: str

    user_id: str

    tenant_id: str

    user_prompt: str

    connection_ref: str

    # -------------------------------------------------
    # WORKFLOW STATUS
    # -------------------------------------------------

    workflow_status: WorkflowStatus = (
        WorkflowStatus.RUNNING
    )

    is_resumed: bool = False

    # -------------------------------------------------
    # SCHEMA CONTEXT
    # -------------------------------------------------

    schema_context: SchemaContext | None = None

    # -------------------------------------------------
    # MEMORY / CONVERSATION
    # -------------------------------------------------

    conversation_memory: dict | None = None

    conversation_context: ConversationContext = Field(
        default_factory=ConversationContext
    )

    # -------------------------------------------------
    # AI UNDERSTANDING
    # -------------------------------------------------

    extracted_intent: ExtractedIntent | None = None

    query_plan: QueryPlan | None = None

    generated_sql: str | None = None

    normalized_sql: str | None = None

    sql_explanation: dict | None = None

    # -------------------------------------------------
    # VALIDATION / GOVERNANCE
    # -------------------------------------------------

    validation_result: ValidationResult | None = None

    clarification: ClarificationState = Field(
        default_factory=ClarificationState
    )

    approval: ApprovalState = Field(
        default_factory=ApprovalState
    )

    risk_level: str | None = None

    cost_analysis: dict | None = None

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    execution_result: ExecutionResult | None = None

    # -------------------------------------------------
    # OBSERVABILITY
    # -------------------------------------------------

    node_trace: list[str] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------
    # TIMESTAMPS
    # -------------------------------------------------

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )