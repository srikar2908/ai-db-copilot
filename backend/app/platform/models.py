from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer
    , UniqueConstraint
)

from app.platform.database import (
    Base
)
from app.utils.time import utc_now


# -------------------------------------------------
# WORKFLOW RUNS
# -------------------------------------------------

from sqlalchemy import JSON


class WorkflowRun(Base):

    __tablename__ = "workflow_runs"

    thread_id = Column(
        String,
        primary_key=True
    )

    tenant_id = Column(
        String,
        nullable=False
    )

    user_id = Column(
        String,
        nullable=False
    )

    connection_ref = Column(
        String,
        nullable=False
    )

    user_prompt = Column(
        Text,
        nullable=False
    )

    # -----------------------------------------
    # SQL
    # -----------------------------------------

    generated_sql = Column(
        Text
    )

    original_generated_sql = Column(
        Text
    )

    approved_sql = Column(
        Text
    )

    # -----------------------------------------
    # REVIEW
    # -----------------------------------------

    approval_status = Column(
        String
    )

    risk_level = Column(
        String
    )

    execution_status = Column(
        String
    )

    approval_timestamp = Column(
        DateTime(timezone=True)
    )

    # -----------------------------------------
    # JSON AUDIT DATA
    # -----------------------------------------

    review_result = Column(
        JSON
    )

    validation_result = Column(
        JSON
    )

    execution_result = Column(
        JSON
    )

    node_trace = Column(
        JSON
    )

    errors = Column(
        JSON
    )

    # -----------------------------------------
    # TIMESTAMPS
    # -----------------------------------------

    created_at = Column(
        DateTime(timezone=True)
    )

    updated_at = Column(
        DateTime(timezone=True)
    )
# -------------------------------------------------
# DATABASE CONNECTIONS
# -------------------------------------------------

class DatabaseConnection(Base):

    __tablename__ = "database_connections"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    tenant_id = Column(
        String,
        nullable=False
    )

    # IMPORTANT
    # connection owner
    owner_user_id = Column(
        Integer,
        nullable=False
    )

    connection_ref = Column(
        String,
        unique=True,
        nullable=False
    )

    encrypted_database_url = Column(
        Text,
        nullable=False
    )

    database_type = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now
    )


# -------------------------------------------------
# PLATFORM USERS
# -------------------------------------------------

class PlatformUser(Base):

    __tablename__ = "platform_users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    tenant_id = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        Text,
        nullable=False
    )

    full_name = Column(
        String,
        nullable=True
    )

    # -------------------------------------------------
    # RBAC ROLE
    # -------------------------------------------------

    role = Column(
        String,
        nullable=False,
        default="analyst"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now
    )


class ConversationMemory(Base):

    __tablename__ = "conversation_memory"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "thread_id",
            name="uq_conversation_memory_scope",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    thread_id = Column(
        String,
        nullable=False
    )

    tenant_id = Column(
        String,
        nullable=False
    )

    user_id = Column(
        String,
        nullable=False
    )

    active_table = Column(
        String,
        nullable=True
    )

    selected_columns = Column(
        Text,
        nullable=True
    )

    active_filters = Column(
        Text,
        nullable=True
    )

    order_by = Column(
        Text,
        nullable=True
    )

    row_limit = Column(
        Integer,
        nullable=True
    )

    last_generated_sql = Column(
        Text,
        nullable=True
    )

    last_user_prompt = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now
    )


class ConversationMessage(Base):

    __tablename__ = "conversation_messages"

    id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
