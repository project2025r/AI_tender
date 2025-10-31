# Quick Start Guide - Auth & RBAC

## Prerequisites

- Supabase account ([supabase.com](https://supabase.com))
- Python 3.9+ with pip
- Node.js 18+ with npm
- Ollama running with llama3.1:8b model
- Qdrant vector database running

## 5-Minute Setup

### 1. Configure Environment

```bash
# Backend - Copy and edit .env
cd backend
cp .env.example .env

# Edit .env and add your Supabase credentials:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_anon_key_here
```

### 2. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Database Setup

The migrations have already been applied to Supabase:
- ✓ Roles table with 4 roles
- ✓ Permissions table with 4 permission levels
- ✓ User roles and role permissions tables
- ✓ RLS policies enabled
- ✓ Helper functions created

### 4. Start Servers

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Create First Admin User

1. Open browser: `http://localhost:5173/signup`
2. Signup with: `admin@example.com` / `DemoPassword123!`
3. Get user ID from Supabase Dashboard > Authentication > Users
4. Assign admin role manually in Supabase:
   - Go to Table Editor > user_roles
   - Insert: `user_id` = your UUID, `role_id` = `dddddddd-dddd-dddd-dddd-dddddddddddd`

### 6. Create Other Users

Now login as admin and use these endpoints to create and assign roles:

**Via API:**
```bash
# Login as admin to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"DemoPassword123!"}'

# Use the access_token from response
export TOKEN="your_token_here"

# Assign role to another user
curl -X POST http://localhost:8000/api/auth/assign-role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_uuid","role_name":"Project Manager"}'
```

**Or Via Frontend:**
After implementing an admin UI (future enhancement).

## Role UUIDs (for manual assignment)

- Project Manager: `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa`
- Discipline Engineer: `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb`
- Review Engineer: `cccccccc-cccc-cccc-cccc-cccccccccccc`
- Administrator: `dddddddd-dddd-dddd-dddd-dddddddddddd`

## Test the System

### Login as Different Roles

1. **Admin** (admin@example.com)
   - Can access all endpoints
   - See admin panel at `/api/admin/users`
   - Delete projects

2. **Project Manager** (john.manager@example.com)
   - Can read, write, and approve projects
   - Upload documents
   - Cannot delete projects

3. **Discipline Engineer** (sarah.engineer@example.com)
   - Can read and write
   - Upload and edit documents
   - Cannot approve or delete

4. **Review Engineer** (mike.reviewer@example.com)
   - Can read and approve
   - Cannot upload or edit documents
   - Cannot delete

### Try Protected Endpoints

```bash
# Get your access token from login
export TOKEN="your_token"

# Test Read permission (works for all)
curl http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN"

# Test Write permission (fails for Review Engineer)
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","description":"Testing"}'

# Test Approve permission (fails for Discipline Engineer)
curl -X POST http://localhost:8000/api/projects/{id}/approve \
  -H "Authorization: Bearer $TOKEN"

# Test Admin permission (fails for non-admins)
curl -X DELETE http://localhost:8000/api/projects/{id} \
  -H "Authorization: Bearer $TOKEN"
```

## Frontend Routes

- `/login` - Login page
- `/signup` - Registration page
- `/forgot-password` - Password reset request
- `/reset-password` - Password reset with token
- `/` - Main app (protected, requires Read permission)

## Common Issues

### Can't login
- Check Supabase credentials in `.env`
- Verify user exists in Supabase Dashboard
- Check backend logs for errors

### Permission denied
- Ensure user has a role assigned
- Check role has the required permission
- Use SQL: `SELECT * FROM get_user_permissions('user_id');`

### Email not working
- Configure SMTP in Supabase Dashboard
- Go to: Authentication > Email Templates
- Enable and customize templates

### Token expired
- Re-login to get new token
- Tokens expire after time set in Supabase

## Next Steps

1. ✓ System is working!
2. Create additional users with different roles
3. Test permission boundaries
4. Customize for your use case
5. **IMPORTANT**: Change all passwords before production!

## File Structure

```
project/
├── AUTH_SETUP_GUIDE.md         # Detailed auth documentation
├── SEED_DATA.json              # Dummy user data
├── QUICK_START.md              # This file
├── README.md                   # Main readme with auth section
├── backend/
│   ├── .env.example            # Environment template
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py         # Auth endpoints
│   │   │   ├── projects.py     # Protected project endpoints
│   │   │   └── admin.py        # Admin endpoints
│   │   ├── services/
│   │   │   └── auth_service.py # Auth business logic
│   │   └── middleware/
│   │       └── auth_middleware.py # JWT & permission checks
│   └── requirements.txt        # Updated with supabase
└── frontend/
    ├── src/
    │   ├── contexts/
    │   │   └── AuthContext.jsx  # Auth state management
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   ├── Signup.jsx
    │   │   ├── ForgotPassword.jsx
    │   │   └── ResetPassword.jsx
    │   ├── components/
    │   │   ├── ProtectedRoute.jsx
    │   │   └── UserInfo.jsx
    │   ├── services/
    │   │   └── authApi.js
    │   ├── App.jsx              # Updated with routing
    │   └── AppContent.jsx       # Main app with permission checks
    └── package.json             # Updated with react-router-dom
```

## API Documentation

Full API docs available at: `http://localhost:8000/docs`

Key endpoints:
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- GET /api/auth/me
- POST /api/auth/assign-role (Admin)
- GET /api/admin/users (Admin)
- GET /api/projects (Read)
- POST /api/projects (Write)
- POST /api/projects/:id/approve (Approve)
- DELETE /api/projects/:id (Admin)

## Production Checklist

Before deploying to production:

- [ ] Change all demo passwords
- [ ] Enable email verification in Supabase
- [ ] Set up proper SMTP for emails
- [ ] Configure HTTPS
- [ ] Use httpOnly cookies for tokens
- [ ] Set up rate limiting
- [ ] Enable MFA for admin accounts
- [ ] Review and test all RLS policies
- [ ] Add audit logging
- [ ] Set up monitoring
- [ ] Configure backup strategy

## Support

For detailed information:
- [AUTH_SETUP_GUIDE.md](AUTH_SETUP_GUIDE.md) - Complete authentication guide
- [README.md](README.md) - Main project documentation
- `http://localhost:8000/docs` - Interactive API documentation
