import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const UserInfo = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="user-info">
      <div className="user-details">
        <div className="user-avatar">{user.email?.[0].toUpperCase()}</div>
        <div className="user-text">
          <div className="user-name">{user.full_name || user.email}</div>
          <div className="user-role">
            {user.roles && user.roles.length > 0 ? (
              user.roles.join(', ')
            ) : (
              <span className="no-role">No role assigned</span>
            )}
          </div>
          {user.permissions && user.permissions.length > 0 && (
            <div className="user-permissions">
              Permissions: {user.permissions.join(', ')}
            </div>
          )}
        </div>
      </div>
      <button onClick={logout} className="btn-logout">
        Logout
      </button>
    </div>
  );
};

export default UserInfo;
