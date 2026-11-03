import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user_profile');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMe = async () => {
      if (token) {
        try {
          const res = await apiClient.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('user_profile', JSON.stringify(res.data));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };

    fetchMe();

    const handleLogout = () => logout();
    window.addEventListener('auth_logout', handleLogout);
    return () => window.removeEventListener('auth_logout', handleLogout);
  }, [token]);

  const login = async (email, password) => {
    const res = await apiClient.post('/auth/login', { email, password });
    const accessToken = res.data.access_token;
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);

    const userRes = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    setUser(userRes.data);
    localStorage.setItem('user_profile', JSON.stringify(userRes.data));
    return userRes.data;
  };

  const register = async (email, password, fullName, currency = 'USD') => {
    await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      currency,
    });
    // Automatically log in after registration
    return login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_profile');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

