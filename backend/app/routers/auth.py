import logging
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from app.services.auth_service import get_auth_service
from app.middleware.auth_middleware import require_permissions, require_roles, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    access_token: str
    new_password: str


class AssignRoleRequest(BaseModel):
    user_id: str
    role_name: str


@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Register a new user

    Default role assignment should be done by admin after signup.
    For testing, you can manually assign roles via /auth/assign-role endpoint.
    """
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    try:
        auth_service = get_auth_service()
        result = await auth_service.signup(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )

        return {
            "message": "User registered successfully",
            "user": result['user'],
            "session": result['session']
        }

    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(request: LoginRequest):
    """
    Login with email and password

    Returns JWT access token and user data with roles/permissions
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.login(
            email=request.email,
            password=request.password
        )

        return {
            "message": "Login successful",
            "user": result['user'],
            "session": result['session']
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset email

    IMPORTANT: Configure email settings in Supabase Dashboard:
    - Go to Authentication > Email Templates
    - Customize the 'Reset Password' template
    - Set up SMTP settings or use Supabase's default email service
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.forgot_password(email=request.email)

        return result

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Return success even on error to prevent email enumeration
        return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email link

    The access_token should come from the URL query parameter
    that Supabase sends in the reset email link.
    """
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    try:
        auth_service = get_auth_service()
        result = await auth_service.reset_password(
            access_token=request.access_token,
            new_password=request.new_password
        )

        return result

    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )


@router.get("/me")
async def get_me(request: Request):
    """
    Get current user information
    Requires authentication
    """
    try:
        user = await get_current_user(request)
        return {"user": user}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get me error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/assign-role")
@require_permissions(["Admin"])
async def assign_role(request: Request, data: AssignRoleRequest, current_user: dict):
    """
    Assign a role to a user (Admin only)

    Available roles:
    - Project Manager
    - Discipline Engineer
    - Review Engineer
    - Administrator
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.assign_role(
            user_id=data.user_id,
            role_name=data.role_name
        )

        return result

    except Exception as e:
        logger.error(f"Assign role error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
