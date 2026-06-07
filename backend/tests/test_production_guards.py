from datetime import timezone

from app.core.sql.validator import validate_sql_query
from app.models.state import SchemaContext
from app.security.auth import create_access_token, verify_access_token
from app.utils.time import utc_now


def schema_context() -> SchemaContext:
    return SchemaContext(
        tables={"employees": ["id", "name"]},
        relevant_tables=["employees"],
        schema_version="test",
        extracted_at=utc_now(),
    )


def test_utc_now_is_timezone_aware():
    value = utc_now()

    assert value.tzinfo is timezone.utc
    assert value.utcoffset().total_seconds() == 0


def test_jwt_round_trip_preserves_tenant_identity():
    token = create_access_token(
        {"user_id": 7, "tenant_id": "tenant-a", "role": "analyst"}
    )

    payload = verify_access_token(token)

    assert payload["user_id"] == 7
    assert payload["tenant_id"] == "tenant-a"


def test_validator_blocks_mutation_without_where():
    result = validate_sql_query(
        "DELETE FROM employees",
        schema_context=schema_context(),
    )

    assert result.passed is False
    assert "DELETE statement missing WHERE clause" in result.errors


def test_validator_accepts_bounded_select():
    result = validate_sql_query(
        "SELECT id, name FROM employees LIMIT 10",
        schema_context=schema_context(),
    )

    assert result.passed is True
