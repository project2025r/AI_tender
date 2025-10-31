import React, { createContext, useContext, useState, useEffect } from 'react';
import * as authApi from '../services/authApi';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await authApi.getMe();
      setUser(response.data.user);
    } catch (err) {
      console.error('Auth check failed:', err);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      setError(null);
      const response = await authApi.signup(email, password, fullName);

      const { user: userData, session } = response.data;

      localStorage.setItem('access_token', session.access_token);
      if (session.refresh_token) {
        localStorage.setItem('refresh_token', session.refresh_token);
      }

      setUser(userData);
      return response;
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed');
      throw err;
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      const response = await authApi.login(email, password);

      const { user: userData, session } = response.data;

      localStorage.setItem('access_token', session.access_token);
      if (session.refresh_token) {
        localStorage.setItem('refresh_token', session.refresh_token);
      }

      setUser(userData);
      return response;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const forgotPassword = async (email) => {
    try {
      setError(null);
      return await authApi.forgotPassword(email);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email');
      throw err;
    }
  };

  const resetPassword = async (accessToken, newPassword) => {
    try {
      setError(null);
      return await authApi.resetPassword(accessToken, newPassword);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password');
      throw err;
    }
  };

  const hasPermission = (permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
  };

  const hasRole = (role) => {
    if (!user || !user.roles) return false;
    return user.roles.includes(role);
  };

  const hasAnyPermission = (permissions) => {
    return permissions.some(permission => hasPermission(permission));
  };

  const hasAllPermissions = (permissions) => {
    return permissions.every(permission => hasPermission(permission));
  };

  const value = {
    user,
    loading,
    error,
    signup,
    login,
    logout,
    forgotPassword,
    resetPassword,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
