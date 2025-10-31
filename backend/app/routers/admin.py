import logging
from fastapi import APIRouter, HTTPException, Request, status
from app.services.auth_service import get_auth_service
from app.middleware.auth_middleware import require_permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
@require_permissions(["Admin"])
async def list_users(request: Request, current_user: dict):
    """
    List all users with their roles (Admin permission required)

    Returns list of users with their assigned roles
    """
    try:
        auth_service = get_auth_service()
        users = await auth_service.list_users()

        return {
            "users": users,
            "total": len(users)
        }

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )
