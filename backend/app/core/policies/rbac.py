# =========================================================
# RBAC POLICY ENGINE
# =========================================================

"""
Purpose
-------
Central authorization engine for:

- SQL operation permissions
- Role enforcement
- Workflow governance

This is intentionally lightweight and
deterministic.
"""

from typing import Dict


# =========================================================
# ROLE -> ALLOWED OPERATIONS
# =========================================================

ROLE_PERMISSIONS = {

    # -------------------------------------------------
    # ANALYST
    # -------------------------------------------------

    "analyst": {

        "SELECT"
    },

    # -------------------------------------------------
    # DEVELOPER
    # -------------------------------------------------

    "developer": {

        "SELECT",
        "INSERT",
        "UPDATE"
    },

    # -------------------------------------------------
    # ADMIN
    # -------------------------------------------------

    "admin": {

        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "ALTER",
        "DROP",
        "TRUNCATE"
    }
}


# =========================================================
# AUTHORIZE OPERATION
# =========================================================

def authorize_operation(

    role: str,

    operation: str

) -> Dict:

    # -----------------------------------------
    # NORMALIZE
    # -----------------------------------------

    role = (
        role
        .lower()
        .strip()
    )

    operation = (
        operation
        .upper()
        .strip()
    )

    # -----------------------------------------
    # UNKNOWN ROLE
    # -----------------------------------------

    if role not in ROLE_PERMISSIONS:

        return {

            "allowed": False,

            "reason":
                f"Unknown role: {role}"
        }

    # -----------------------------------------
    # CHECK PERMISSION
    # -----------------------------------------

    allowed_operations = (
        ROLE_PERMISSIONS[role]
    )

    if operation not in allowed_operations:

        return {

            "allowed": False,

            "reason": (
                f"{role.title()} role "
                f"cannot execute "
                f"{operation} queries"
            )
        }

    # -----------------------------------------
    # ALLOWED
    # -----------------------------------------

    return {

        "allowed": True,

        "reason": None
    }