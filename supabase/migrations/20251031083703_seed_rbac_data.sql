/*
  # Seed RBAC Data

  ## Overview
  This migration seeds the database with:
  1. Four permission levels: Read, Write, Approve, Admin
  2. Four roles: Project Manager, Discipline Engineer, Review Engineer, Administrator
  3. Role-permission mappings based on the RBAC matrix
  4. Four dummy users (created via Supabase Auth)
  5. User-role assignments

  ## Permission Matrix
  - **Project Manager**: Read, Write, Approve
  - **Discipline Engineer**: Read, Write
  - **Review Engineer**: Read, Approve
  - **Administrator**: Read, Write, Approve, Admin

  ## Dummy Users
  All users have password: `DemoPassword123!`
  **IMPORTANT**: Change passwords in production!

  1. john.manager@example.com - Project Manager
  2. sarah.engineer@example.com - Discipline Engineer
  3. mike.reviewer@example.com - Review Engineer
  4. admin@example.com - Administrator

  ## Notes
  - Passwords are hashed by Supabase Auth
  - Users must be created manually via Supabase Dashboard or signup endpoint
  - This migration only creates roles, permissions, and their mappings
  - After creating users via signup, run the user_role assignments using the update script
*/

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

-- Assign Permissions to Roles

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