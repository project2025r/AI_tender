# Authentication & RBAC Setup Guide

This guide explains how to set up and use the authentication and role-based access control (RBAC) system in the Tender Document Chatbot application.

## Overview

The system uses:
- **Supabase Auth** for user authentication (JWT-based)
- **PostgreSQL** (via Supabase) for RBAC tables
- **4 Roles**: Project Manager, Discipline Engineer, Review Engineer, Administrator
- **4 Permission Levels**: Read, Write, Approve, Admin

## Setup Instructions

### 1. Configure Supabase

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL and anon key from Project Settings > API
3. Create a `.env` file in the `backend` directory:

```bash
cp backend/.env.example backend/.env
```

4. Update `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
FRONTEND_URL=http://localhost:5173
```

### 2. Run Database Migrations

The migrations have already been applied to your Supabase database. They created:
- `roles` table with 4 predefined roles
- `permissions` table with 4 permission levels
- `user_roles` table for user-role assignments
- `role_permissions` table for role-permission mappings
- Helper functions: `get_user_permissions()` and `user_has_permission()`

### 3. Create Dummy Users

You need to manually create users via the signup endpoint, then assign roles.

#### Option A: Via Frontend (Recommended)

1. Start the backend and frontend servers
2. Navigate to `http://localhost:5173/signup`
3. Create accounts using the emails from SEED_DATA.json:
   - admin@example.com
   - john.manager@example.com
   - sarah.engineer@example.com
   - mike.reviewer@example.com

4. After creating each user, use the admin account to assign roles (see below)

#### Option B: Via API

Use curl or Postman to signup users:

```bash
# Signup admin user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "DemoPassword123!",
    "full_name": "System Administrator"
  }'

# Repeat for other users...
```

### 4. Assign Roles to Users

After creating users, you need to assign roles. This requires admin access.

1. Login as the first created user
2. Manually assign admin role in Supabase Dashboard:
   - Go to Table Editor > user_roles
   - Insert a row: `user_id` = (user UUID), `role_id` = (admin role UUID)
   - Role UUIDs are in the seed migration:
     - Administrator: `dddddddd-dddd-dddd-dddd-dddddddddddd`

3. Once you have an admin user, use the API to assign roles to others:

```bash
# Get admin access token (from login response)
export ADMIN_TOKEN="your_admin_access_token"

# Assign Project Manager role
curl -X POST http://localhost:8000/api/auth/assign-role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_uuid_here",
    "role_name": "Project Manager"
  }'
```

## Role-Permission Matrix

| Role                 | Read | Write | Approve | Admin |
|---------------------|------|-------|---------|-------|
| Project Manager     | ✓    | ✓     | ✓       | ✗     |
| Discipline Engineer | ✓    | ✓     | ✗       | ✗     |
| Review Engineer     | ✓    | ✗     | ✓       | ✗     |
| Administrator       | ✓    | ✓     | ✓       | ✓     |

## API Endpoints

### Auth Endpoints

#### POST /api/auth/signup
Register a new user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "session": {
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
  }
}
```

#### POST /api/auth/login
Login with email and password

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "roles": ["Project Manager"],
    "permissions": ["Read", "Write", "Approve"]
  },
  "session": {
    "access_token": "jwt_token",
    "refresh_token": "refresh_token",
    "expires_at": 1234567890
  }
}
```

#### POST /api/auth/forgot-password
Send password reset email

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Note:** Configure email templates in Supabase Dashboard:
- Go to Authentication > Email Templates
- Customize the "Reset Password" template
- Ensure redirect URL is set to: `http://localhost:5173/reset-password`

#### POST /api/auth/reset-password
Reset password with token

**Request:**
```json
{
  "access_token": "token_from_email_link",
  "new_password": "NewSecurePassword123!"
}
```

#### GET /api/auth/me
Get current user info (requires authentication)

**Headers:**
```
Authorization: Bearer <access_token>
```

#### POST /api/auth/assign-role
Assign role to user (Admin only)

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Request:**
```json
{
  "user_id": "user_uuid",
  "role_name": "Project Manager"
}
```

### Protected Project Endpoints

All project endpoints require authentication and specific permissions.

#### GET /api/projects
List all projects (Read permission required)

#### GET /api/projects/{project_id}
Get specific project (Read permission required)

#### POST /api/projects
Create project (Write permission required)

**Request:**
```json
{
  "name": "New Tender Project",
  "description": "Project description"
}
```

#### PUT /api/projects/{project_id}
Update project (Write permission required)

#### POST /api/projects/{project_id}/approve
Approve project (Approve permission required)

#### DELETE /api/projects/{project_id}
Delete project (Admin permission required)

### Admin Endpoints

#### GET /api/admin/users
List all users with roles (Admin permission required)

## Frontend Integration

### Using Auth Context

```jsx
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { user, hasPermission, hasRole, logout } = useAuth();

  if (hasPermission('Write')) {
    // Show write functionality
  }

  if (hasRole('Administrator')) {
    // Show admin features
  }

  return (
    <div>
      <p>Welcome {user.email}</p>
      <p>Role: {user.roles.join(', ')}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Protected Routes

```jsx
import ProtectedRoute from './components/ProtectedRoute';

<Route
  path="/admin"
  element={
    <ProtectedRoute requiredPermission="Admin">
      <AdminPanel />
    </ProtectedRoute>
  }
/>
```

### Conditional Rendering

```jsx
import { useAuth } from './contexts/AuthContext';

function DocumentActions() {
  const { hasPermission } = useAuth();

  return (
    <div>
      {hasPermission('Write') && (
        <button>Edit Document</button>
      )}
      {hasPermission('Approve') && (
        <button>Approve Document</button>
      )}
      {hasPermission('Admin') && (
        <button>Delete Document</button>
      )}
    </div>
  );
}
```

## JWT Token Storage

Tokens are stored in `localStorage`:
- `access_token`: JWT access token
- `refresh_token`: Refresh token (for future implementation)

**For Production:** Consider using httpOnly cookies instead of localStorage for better security.

## Security Notes

### IMPORTANT: Change Default Passwords

The demo passwords (`DemoPassword123!`) are for **DEVELOPMENT ONLY**.

**Before deploying to production:**
1. Change all user passwords
2. Enforce strong password policies
3. Enable email verification in Supabase
4. Set up MFA (Multi-Factor Authentication)
5. Configure rate limiting
6. Use httpOnly cookies for tokens

### Email Configuration

**For Password Reset to Work:**
1. Go to Supabase Dashboard > Authentication > Email Templates
2. Configure SMTP settings or use Supabase's email service
3. Customize the "Reset Password" email template
4. Ensure the redirect URL points to your frontend

### RLS (Row Level Security)

All RBAC tables have RLS enabled:
- Users can only read their own roles
- Only admins can modify roles and permissions
- Helper functions enforce permission checks

## Troubleshooting

### Users can't login
- Check that user exists in Supabase auth.users table
- Verify password is correct
- Check backend logs for detailed errors

### Permission denied errors
- Verify user has a role assigned in user_roles table
- Check that role has the required permission in role_permissions table
- Use `get_user_permissions(user_id)` function to debug

### Email not sending
- Configure SMTP in Supabase Dashboard
- Check email templates are enabled
- Verify redirect URLs are correct

### JWT token expired
- Implement token refresh logic (future enhancement)
- Re-login to get new token

## Testing the System

1. Create 4 users with different roles
2. Login as each user and test:
   - Project Manager: Can read, create, edit, and approve projects
   - Discipline Engineer: Can read and create/edit projects (no approve)
   - Review Engineer: Can read and approve projects (no edit)
   - Administrator: Can do everything including delete

## Backend Middleware Usage

### Enforcing Permissions

```python
from app.middleware.auth_middleware import require_permissions

@router.get("/api/data")
@require_permissions(["Read"])
async def get_data(request: Request, current_user: dict):
    # current_user contains user info with roles and permissions
    return {"data": "...", "user": current_user['email']}
```

### Enforcing Roles

```python
from app.middleware.auth_middleware import require_roles

@router.post("/api/admin/action")
@require_roles(["Administrator"])
async def admin_action(request: Request, current_user: dict):
    # Only administrators can access this
    return {"message": "Admin action completed"}
```

## Database Helper Functions

### Check User Permission

```sql
SELECT user_has_permission('user_uuid_here', 'Write');
```

### Get All User Permissions

```sql
SELECT * FROM get_user_permissions('user_uuid_here');
```

## Next Steps

1. Implement token refresh logic
2. Add email verification for new signups
3. Set up MFA (Multi-Factor Authentication)
4. Add user profile management
5. Implement session timeout handling
6. Add audit logging for admin actions
7. Create admin dashboard for user management
