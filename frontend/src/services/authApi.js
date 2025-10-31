import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

authApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const signup = async (email, password, fullName) => {
  return authApi.post('/auth/signup', {
    email,
    password,
    full_name: fullName,
  });
};

export const login = async (email, password) => {
  return authApi.post('/auth/login', {
    email,
    password,
  });
};

export const forgotPassword = async (email) => {
  return authApi.post('/auth/forgot-password', {
    email,
  });
};

export const resetPassword = async (accessToken, newPassword) => {
  return authApi.post('/auth/reset-password', {
    access_token: accessToken,
    new_password: newPassword,
  });
};

export const getMe = async () => {
  return authApi.get('/auth/me');
};

export const assignRole = async (userId, roleName) => {
  return authApi.post('/auth/assign-role', {
    user_id: userId,
    role_name: roleName,
  });
};

export default authApi;
