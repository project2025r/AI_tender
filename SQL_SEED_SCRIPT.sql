-- =====================================================
-- Tender Document Chatbot - RBAC Seed Data
-- =====================================================
-- This script inserts roles, permissions, and their mappings
-- Run this AFTER the migrations have been applied
--
-- IMPORTANT: This only seeds roles and permissions
-- Users must be created via Supabase Auth (signup endpoint)
-- Then roles can be assigned using the user_roles table
-- =====================================================

-- Insert Permissions
INSERT INTO permissions (id, name, description) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Read', 'Can view/read data'),
  ('22222222-2222-2222-2222-222222222222', 'Write', 'Can create and edit data'),
  ('33333333-3333-3333-3333-333333333333', 'Approve', 'Can approve submissions'),
  ('44444444-4444-4444-4444-444444444444', 'Admin', 'Full administrative access')
ON CONFLICT (name) DO NOTHING;

-- Insert Roles
INSERT INTO roles (id, name, description) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Project Manager', 'Manages projects, can read, write, and approve'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Discipline Engineer', 'Works on engineering tasks, can read and write'),
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Review Engineer', 'Reviews work, can read and approve'),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Administrator', 'Full system access with all permissions')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- Assign Permissions to Roles
-- =====================================================

-- Project Manager: Read, Write, Approve
INSERT INTO role_permissions (role_id, permission_id) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222'),
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '33333333-3333-3333-3333-333333333333')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Discipline Engineer: Read, Write
INSERT INTO role_permissions (role_id, permission_id) VALUES
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Review Engineer: Read, Approve
INSERT INTO role_permissions (role_id, permission_id) VALUES
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', '11111111-1111-1111-1111-111111111111'),
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', '33333333-3333-3333-3333-333333333333')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Administrator: Read, Write, Approve, Admin
INSERT INTO role_permissions (role_id, permission_id) VALUES
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', '11111111-1111-1111-1111-111111111111'),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', '22222222-2222-2222-2222-222222222222'),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', '33333333-3333-3333-3333-333333333333'),
  ('dddddddd-dddd-dddd-dddd-dddddddddddd', '44444444-4444-4444-4444-444444444444')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- =====================================================
-- Verify the seed data
-- =====================================================

-- Check roles
SELECT * FROM roles ORDER BY name;

-- Check permissions
SELECT * FROM permissions ORDER BY name;

-- Check role-permission mappings
SELECT
  r.name as role_name,
  p.name as permission_name
FROM role_permissions rp
JOIN roles r ON rp.role_id = r.id
JOIN permissions p ON rp.permission_id = p.id
ORDER BY r.name, p.name;

-- =====================================================
-- Manual User Role Assignment (After Signup)
-- =====================================================

-- After users signup via the API, assign roles manually:

-- Example: Assign Administrator role to a user
-- Replace 'USER_UUID_HERE' with actual user ID from auth.users
/*
INSERT INTO user_roles (user_id, role_id) VALUES
  ('USER_UUID_HERE', 'dddddddd-dddd-dddd-dddd-dddddddddddd')
ON CONFLICT (user_id, role_id) DO NOTHING;
*/

-- Example: Assign Project Manager role to a user
/*
INSERT INTO user_roles (user_id, role_id) VALUES
  ('USER_UUID_HERE', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
ON CONFLICT (user_id, role_id) DO NOTHING;
*/

-- Example: Assign Discipline Engineer role to a user
/*
INSERT INTO user_roles (user_id, role_id) VALUES
  ('USER_UUID_HERE', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
ON CONFLICT (user_id, role_id) DO NOTHING;
*/

-- Example: Assign Review Engineer role to a user
/*
INSERT INTO user_roles (user_id, role_id) VALUES
  ('USER_UUID_HERE', 'cccccccc-cccc-cccc-cccc-cccccccccccc')
ON CONFLICT (user_id, role_id) DO NOTHING;
*/

-- =====================================================
-- Helper Queries
-- =====================================================

-- Get all users with their roles
SELECT
  ur.user_id,
  r.name as role_name
FROM user_roles ur
JOIN roles r ON ur.role_id = r.id
ORDER BY ur.user_id;

-- Get all permissions for a specific user
SELECT * FROM get_user_permissions('USER_UUID_HERE');

-- Check if a user has a specific permission
SELECT user_has_permission('USER_UUID_HERE', 'Write');

-- Get all roles and their permissions
SELECT
  r.name as role,
  ARRAY_AGG(p.name ORDER BY p.name) as permissions
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
GROUP BY r.name
ORDER BY r.name;

-- =====================================================
-- Demo User Creation Guide
-- =====================================================

/*
STEP 1: Create users via Supabase Auth (use signup endpoint or Supabase Dashboard)

POST /api/auth/signup
{
  "email": "admin@example.com",
  "password": "DemoPassword123!",
  "full_name": "System Administrator"
}

POST /api/auth/signup
{
  "email": "john.manager@example.com",
  "password": "DemoPassword123!",
  "full_name": "John Manager"
}

POST /api/auth/signup
{
  "email": "sarah.engineer@example.com",
  "password": "DemoPassword123!",
  "full_name": "Sarah Engineer"
}

POST /api/auth/signup
{
  "email": "mike.reviewer@example.com",
  "password": "DemoPassword123!",
  "full_name": "Mike Reviewer"
}

STEP 2: Get user IDs from Supabase Dashboard > Authentication > Users

STEP 3: Assign roles using the INSERT statements above (uncomment and replace USER_UUID_HERE)

OR use the API endpoint (requires existing admin):

POST /api/auth/assign-role
Authorization: Bearer <admin_token>
{
  "user_id": "USER_UUID",
  "role_name": "Project Manager"
}
*/

-- =====================================================
-- IMPORTANT NOTES
-- =====================================================

/*
1. NEVER commit passwords to version control
2. Change all demo passwords before production
3. Enable email verification in Supabase for production
4. Set up proper SMTP for password reset emails
5. RLS policies are already enabled and enforced
6. All user data is protected by RLS
7. Only admins can modify RBAC tables
8. Users can only see their own role assignments
9. Helper functions run with SECURITY DEFINER
10. Test permission boundaries thoroughly before production

SECURITY CHECKLIST:
☐ All users created with strong passwords
☐ Email verification enabled
☐ MFA enabled for admin accounts
☐ SMTP configured for emails
☐ RLS policies tested and verified
☐ No hardcoded secrets in code
☐ API rate limiting configured
☐ Audit logging enabled
☐ Session timeout configured
☐ HTTPS enforced in production
*/
