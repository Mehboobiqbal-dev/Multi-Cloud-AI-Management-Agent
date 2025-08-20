import React, { createContext, useState, useContext, useEffect } from 'react';
import { login as authLogin, signup as authSignup } from '../auth';
import apiClient from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      console.log("AuthContext: Checking user...");
      try {
        const token = localStorage.getItem('access_token');
        console.log("AuthContext: Token found:", token ? 'Yes' : 'No');
        if (token) {
          const response = await apiClient.get('/users/me');
          setUser(response.data);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('AuthContext: Auth check failed:', error);
        setUser(null);
        localStorage.removeItem('access_token');
      } finally {
        setLoading(false);
      }
    };
    checkUser();
  }, []);

  const login = async (credentials) => {
    console.log("AuthContext: Attempting login...");
    setLoading(true);
    try {
      // Validate input before sending to API
      if (!credentials.email || !credentials.email.includes('@')) {
        throw new Error('Please enter a valid email address');
      }
      
      if (!credentials.password || credentials.password.length < 8) {
        throw new Error('Password must be at least 8 characters long');
      }
      
      const loginData = {
        email: credentials.email,
        password: credentials.password,
      };
      
      console.log("AuthContext: Sending login request...");
      const response = await authLogin(loginData);
      
      if (response.access_token) {
        console.log("AuthContext: Login successful, token received.");
        localStorage.setItem('access_token', response.access_token);
        // In a real application, you might decode the token or make another API call to get user details
        // For now, we'll just set a placeholder user or use info from the login response if available
        setUser({ email: credentials.email }); // Placeholder user
        // const currentUser = await api.getMe(); // If you have a getMe endpoint
        // console.log("AuthContext: User data fetched:", currentUser);
        // setUser(currentUser);

      } else {
        throw new Error('Login failed: Invalid response from server');
      }
    } catch (error) {
      console.error('AuthContext: Login failed:', error);
      localStorage.removeItem('token');
      setUser(null);
      throw error;
    } finally {
      console.log("AuthContext: Login process finished, setting loading to false.");
      setLoading(false);
    }
  };

  const googleLogin = async (credential) => {
    try {
      const response = await apiClient.post('/auth/google', { credential });
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        const userResponse = await apiClient.get('/users/me');
        setUser(userResponse.data);
      }
    } catch (error) {
      throw error;
    }
  };

  const signup = async (userData) => {
    console.log("AuthContext: Attempting signup...");
    setLoading(true);
    try {
      // Validate input before sending to API
      if (!userData.email || !userData.email.includes('@')) {
        throw new Error('Please enter a valid email address');
      }
      
      if (!userData.password || userData.password.length < 8) {
        throw new Error('Password must be at least 8 characters long');
      }
      
      if (!userData.name || userData.name.trim() === '') {
        throw new Error('Please enter your name');
      }
      
      console.log("AuthContext: Sending signup request...");
      await authSignup(userData);
      console.log("AuthContext: Signup successful, now logging in...");
      
      try {
        await login({ email: userData.email, password: userData.password });
      } catch (loginError) {
        // If login fails after successful signup, we still consider signup successful
        // but inform the user they need to login manually
        console.warn('AuthContext: Auto-login after signup failed:', loginError);
        throw new Error('Account created successfully! Please login with your credentials.');
      }
    } catch (error) {
      console.error('AuthContext: Signup failed:', error);
      throw error;
    } finally {
      console.log("AuthContext: Signup process finished, setting loading to false.");
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    login,
    signup,
    googleLogin,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
