import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
    case 'REGISTER_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
    case 'REGISTER_SUCCESS':
      localStorage.setItem('token', action.payload.token);
      return { ...state, loading: false, isAuthenticated: true, user: action.payload.user, token: action.payload.token, error: null };
    case 'LOGIN_FAIL':
    case 'REGISTER_FAIL':
      localStorage.removeItem('token');
      return { ...state, loading: false, isAuthenticated: false, user: null, token: null, error: action.payload };
    case 'LOGOUT':
      localStorage.removeItem('token');
      return { ...state, isAuthenticated: false, user: null, token: null };
    case 'LOAD_USER':
      return { ...state, isAuthenticated: true, user: action.payload, loading: false, error: null };
    case 'NO_USER':
      return { ...state, isAuthenticated: false, user: null, token: null, loading: false, error: null };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const initialState = {
    token: localStorage.getItem('token'),
    isAuthenticated: false,
    loading: true,
    user: null,
    error: null
  };

  const [state, dispatch] = useReducer(authReducer, initialState);

  // Set auth header for axios globally
  const setAuthToken = (token) => {
    if (token) axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    else delete axios.defaults.headers.common['Authorization'];
  };

  // Restore user from token, or logout if token invalid
  const loadUser = async () => {
    const storedToken = localStorage.getItem('token');
  setAuthToken(storedToken);
  if (storedToken) {
    try {
      const res = await axios.get('http://localhost:5000/api/auth/me');
      dispatch({ type: 'LOAD_USER', payload: res.data.user });
    } catch (err) {
      localStorage.removeItem('token');
      setAuthToken(null);
      dispatch({ type: 'LOGIN_FAIL', payload: 'Session expired. Please login again.' });
    }
  } else {
    dispatch({ type: 'NO_USER' });
  }
  };

  // Register a new user
  const register = async (userData) => {
    dispatch({ type: 'REGISTER_START' });
    try {
      const res = await axios.post('http://localhost:5000/api/auth/register', userData);
      dispatch({ type: 'REGISTER_SUCCESS', payload: res.data });
      await loadUser();
      return { success: true };
    } catch (err) {
      dispatch({ type: 'REGISTER_FAIL', payload: err.response?.data?.message || 'Registration failed' });
      return { success: false, error: err.response?.data?.message };
    }
  };

  // Login logic
  const login = async (email, password) => {
    dispatch({ type: 'LOGIN_START' });
    try {
      const res = await axios.post('http://localhost:5000/api/auth/login', { email, password });
      dispatch({ type: 'LOGIN_SUCCESS', payload: res.data });
      await loadUser();
      return { success: true };
    } catch (err) {
      dispatch({ type: 'LOGIN_FAIL', payload: err.response?.data?.message || 'Login failed' });
      return { success: false, error: err.response?.data?.message };
    }
  };

  // Logout and remove token from everywhere
  const logout = () => {
    localStorage.removeItem('token');
    setAuthToken(null);
    dispatch({ type: 'LOGOUT' });
  };

  // On mount, restore session from localStorage and listen for cross-tab logout
  useEffect(() => {
    loadUser();
    const handleStorage = (e) => {
      if (e.key === 'token' && !e.newValue) {
        logout();
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
    // eslint-disable-next-line
  }, []);

  // Whenever token changes, set it on axios
  useEffect(() => {
    setAuthToken(state.token);
  }, [state.token]);

  return (
    <AuthContext.Provider value={{
      ...state,
      register,
      login,
      logout,
      loadUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for auth
export const useAuth = () => useContext(AuthContext);
