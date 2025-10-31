import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, requiredPermission, requiredRole }) => {
  const { user, loading, hasPermission, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="unauthorized-container">
        <div className="error-message">
          <h2>Access Denied</h2>
          <p>You don't have the required permission: {requiredPermission}</p>
        </div>
      </div>
    );
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div className="unauthorized-container">
        <div className="error-message">
          <h2>Access Denied</h2>
          <p>You don't have the required role: {requiredRole}</p>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;
