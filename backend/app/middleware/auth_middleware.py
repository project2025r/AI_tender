import logging
from functools import wraps
from typing import List, Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_auth_service

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(request: Request):
    """
    Middleware to extract and verify JWT token from Authorization header
    Attaches user data to request.state.user
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.replace('Bearer ', '')

    try:
        auth_service = get_auth_service()
        user_data = await auth_service.verify_token(token)
        return user_data['user']
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def require_permissions(required_permissions: List[str]):
    """
    Decorator to enforce permission checks on endpoints
    Usage:
        @require_permissions(["Read"])
        @require_permissions(["Write", "Admin"])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs (works with FastAPI dependency injection)
            request = kwargs.get('request')
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get current user
            user = await get_current_user(request)

            # Check if user has ALL required permissions
            user_permissions = set(user.get('permissions', []))

            for permission in required_permissions:
                if permission not in user_permissions:
                    logger.warning(
                        f"User {user['email']} attempted to access endpoint requiring '{permission}' permission"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required permission: {permission}"
                    )

            # Attach user to kwargs for easy access in endpoint
            kwargs['current_user'] = user

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(required_roles: List[str]):
    """
    Decorator to enforce role checks on endpoints
    Usage:
        @require_roles(["Administrator"])
        @require_roles(["Project Manager", "Administrator"])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get current user
            user = await get_current_user(request)

            # Check if user has ANY of the required roles
            user_roles = set(user.get('roles', []))
            has_required_role = any(role in user_roles for role in required_roles)

            if not has_required_role:
                logger.warning(
                    f"User {user['email']} attempted to access endpoint requiring roles: {required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role. Required: {', '.join(required_roles)}"
                )

            # Attach user to kwargs for easy access in endpoint
            kwargs['current_user'] = user

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class AuthMiddleware:
    """
    Optional: Class-based middleware for global authentication
    Can be added to FastAPI app to protect all routes
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ['/api/auth/login', '/api/auth/signup', '/api/auth/forgot-password', '/docs', '/openapi.json']

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Verify token for protected routes
        try:
            user = await get_current_user(request)
            request.state.user = user
        except HTTPException:
            # Let individual route handlers decide if auth is required
            pass

        return await call_next(request)
