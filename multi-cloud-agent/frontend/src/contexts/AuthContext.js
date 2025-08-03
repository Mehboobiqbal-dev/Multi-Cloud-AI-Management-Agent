import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

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
        const token = localStorage.getItem('token');
        console.log("AuthContext: Token found:", token ? 'Yes' : 'No');
        if (token) {
          console.log("AuthContext: Fetching user with token...");
          const currentUser = await api.getMe();
          console.log("AuthContext: User fetched successfully:", currentUser);
          setUser(currentUser);
        } else {
          console.log("AuthContext: No token, setting user to null.");
          setUser(null);
        }
      } catch (error) {
        console.error('AuthContext: Auth check failed:', error);
        setUser(null);
        localStorage.removeItem('token');
      } finally {
        console.log("AuthContext: Finished checking user, setting loading to false.");
        setLoading(false);
      }
    };
    checkUser();
  }, []);

  const login = async (credentials) => {
    console.log("AuthContext: Attempting login...");
    setLoading(true);
    try {
      const loginData = {
        username: credentials.email,
        password: credentials.password,
      };
      
      console.log("AuthContext: Sending login request...");
      const response = await api.login(loginData);
      
      if (response.access_token) {
        console.log("AuthContext: Login successful, token received.");
        localStorage.setItem('token', response.access_token);
        console.log("AuthContext: Fetching user data after login...");
        const currentUser = await api.getMe();
        console.log("AuthContext: User data fetched:", currentUser);
        setUser(currentUser);
      }
    } catch (error) {
      console.error('AuthContext: Login failed:', error.response ? error.response.data : error.message);
      localStorage.removeItem('token');
      setUser(null);
      throw error;
    } finally {
      console.log("AuthContext: Login process finished, setting loading to false.");
      setLoading(false);
    }
  };

  const signup = async (userData) => {
    console.log("AuthContext: Attempting signup...");
    setLoading(true);
    try {
      console.log("AuthContext: Sending signup request...");
      await api.signup(userData);
      console.log("AuthContext: Signup successful, now logging in...");
      await login({ email: userData.email, password: userData.password });
    } catch (error) {
      console.error('AuthContext: Signup failed:', error.response ? error.response.data : error.message);
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
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
