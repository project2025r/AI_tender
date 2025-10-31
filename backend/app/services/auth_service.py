import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")

        self.client: Client = create_client(supabase_url, supabase_key)

    async def signup(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth
        Returns user data and session
        """
        try:
            user_metadata = {}
            if full_name:
                user_metadata['full_name'] = full_name

            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })

            if response.user:
                logger.info(f"User signed up: {email}")
                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "full_name": full_name
                    },
                    "session": {
                        "access_token": response.session.access_token if response.session else None,
                        "refresh_token": response.session.refresh_token if response.session else None
                    }
                }
            else:
                raise Exception("Signup failed")

        except Exception as e:
            logger.error(f"Signup error: {e}")
            raise

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password
        Returns user data, session, and permissions
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user or not response.session:
                raise Exception("Invalid credentials")

            user_id = response.user.id

            # Get user roles and permissions
            roles = self._get_user_roles(user_id)
            permissions = self._get_user_permissions(user_id)

            logger.info(f"User logged in: {email}")

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get('full_name'),
                    "roles": roles,
                    "permissions": permissions
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at
                }
            }

        except Exception as e:
            logger.error(f"Login error: {e}")
            raise

    async def forgot_password(self, email: str) -> Dict[str, str]:
        """
        Send password reset email
        NOTE: Configure email templates in Supabase Dashboard
        """
        try:
            self.client.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": os.getenv('FRONTEND_URL', 'http://localhost:5173') + '/reset-password'
                }
            )

            logger.info(f"Password reset email sent to: {email}")
            return {"message": "Password reset email sent"}

        except Exception as e:
            logger.error(f"Forgot password error: {e}")
            raise

    async def reset_password(self, access_token: str, new_password: str) -> Dict[str, str]:
        """
        Reset password with access token from email link
        """
        try:
            # Set session with the access token from reset link
            self.client.auth.set_session(access_token, access_token)

            # Update password
            response = self.client.auth.update_user({
                "password": new_password
            })

            if response.user:
                logger.info(f"Password reset for user: {response.user.email}")
                return {"message": "Password reset successful"}
            else:
                raise Exception("Password reset failed")

        except Exception as e:
            logger.error(f"Reset password error: {e}")
            raise

    async def verify_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify JWT access token and return user data with permissions
        """
        try:
            response = self.client.auth.get_user(access_token)

            if not response.user:
                raise Exception("Invalid token")

            user_id = response.user.id
            roles = self._get_user_roles(user_id)
            permissions = self._get_user_permissions(user_id)

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get('full_name'),
                    "roles": roles,
                    "permissions": permissions
                }
            }

        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise

    async def assign_role(self, user_id: str, role_name: str) -> Dict[str, str]:
        """
        Assign a role to a user (Admin only)
        """
        try:
            # Get role ID by name
            role_response = self.client.table('roles').select('id').eq('name', role_name).execute()

            if not role_response.data:
                raise Exception(f"Role '{role_name}' not found")

            role_id = role_response.data[0]['id']

            # Assign role to user
            self.client.table('user_roles').insert({
                "user_id": user_id,
                "role_id": role_id
            }).execute()

            logger.info(f"Role '{role_name}' assigned to user: {user_id}")
            return {"message": f"Role '{role_name}' assigned successfully"}

        except Exception as e:
            logger.error(f"Assign role error: {e}")
            raise

    def _get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user
        """
        try:
            response = self.client.table('user_roles') \
                .select('roles(name)') \
                .eq('user_id', user_id) \
                .execute()

            return [item['roles']['name'] for item in response.data if item.get('roles')]
        except Exception as e:
            logger.error(f"Error fetching user roles: {e}")
            return []

    def _get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user (via their roles)
        """
        try:
            response = self.client.rpc('get_user_permissions', {
                'user_uuid': user_id
            }).execute()

            return [item['permission_name'] for item in response.data]
        except Exception as e:
            logger.error(f"Error fetching user permissions: {e}")
            return []

    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users with their roles (Admin only)
        Note: This uses service role key to access auth.users
        """
        try:
            # Get all user_roles with user and role information
            response = self.client.table('user_roles') \
                .select('user_id, roles(name)') \
                .execute()

            # Group roles by user_id
            user_roles_map = {}
            for item in response.data:
                user_id = item['user_id']
                role_name = item['roles']['name'] if item.get('roles') else None

                if user_id not in user_roles_map:
                    user_roles_map[user_id] = []
                if role_name:
                    user_roles_map[user_id].append(role_name)

            # Note: Getting user email requires service role key
            # For now, return user IDs with roles
            users = []
            for user_id, roles in user_roles_map.items():
                users.append({
                    "user_id": user_id,
                    "roles": roles
                })

            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise


_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create the global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
