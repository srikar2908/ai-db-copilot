from datetime import datetime
from typing import Optional, Literal, Dict, Any

from pydantic import BaseModel, Field

from app.models.state import (
    SchemaContext,
    ExtractedIntent,
    QueryPlan,
    ValidationResult,
    ExecutionResult,
    ClarificationState,
    ApprovalState,
    ConversationContext
)

from app.core.cost.models import (
    QueryCostAnalysis
)

from app.core.graph.status import WorkflowStatus


# -------------------------------------------------
# MAIN WORKFLOW STATE
# -------------------------------------------------

class CopilotState(BaseModel):

    # -------------------------------------------------
    # IDENTITY
    # -------------------------------------------------

    session_id: str

    tenant_id: str

    user_id: str

    user_role: str | None = None

    connection_ref: str

    # -------------------------------------------------
    # USER INPUT
    # -------------------------------------------------

    user_prompt: str

    # -------------------------------------------------
    # WORKFLOW STATUS
    # -------------------------------------------------

    workflow_status: WorkflowStatus = (
        WorkflowStatus.RUNNING
    )

    is_resumed: bool = False

    # -------------------------------------------------
    # SCHEMA + MEMORY
    # -------------------------------------------------

    schema_context: Optional[
        SchemaContext
    ] = None

    conversation_memory: Optional[
        Dict[str, Any]
    ] = None

    conversation_context: ConversationContext = Field(
        default_factory=ConversationContext
    )

    # -------------------------------------------------
    # INTENT + PLANNING
    # -------------------------------------------------

    extracted_intent: Optional[
        ExtractedIntent
    ] = None

    clarification: ClarificationState = Field(
        default_factory=ClarificationState
    )

    query_plan: Optional[
        QueryPlan
    ] = None

    # -------------------------------------------------
    # SQL GENERATION
    # -------------------------------------------------

    generated_sql: Optional[
        str
    ] = None

    original_generated_sql: Optional[
        str
    ] = None

    normalized_sql: Optional[
        str
    ] = None

    validation_result: Optional[
        ValidationResult
    ] = None

    cost_analysis: Optional[
        QueryCostAnalysis
    ] = None

    risk_level: Optional[
        Literal[
            "low",
            "medium",
            "high",
            "blocked"
        ]
    ] = None

    # -------------------------------------------------
    # APPROVAL
    # -------------------------------------------------

    approval: ApprovalState = Field(
        default_factory=ApprovalState
    )

    approved_sql: Optional[
        str
    ] = None

    approval_timestamp: Optional[
        datetime
    ] = None

    # -------------------------------------------------
    # EXECUTION
    # -------------------------------------------------

    execution_result: Optional[
        ExecutionResult
    ] = None


    sql_explanation: dict | None = None

    review_result: dict | None = None

    
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