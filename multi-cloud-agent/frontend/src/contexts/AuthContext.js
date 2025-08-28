import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api'; // Make sure this points to your api.js file

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Effect to check for an existing token from localStorage or URL on initial load
  useEffect(() => {
    const checkUser = async () => {
      // First, check for a token in the URL (from OAuth redirect)
      const queryParams = new URLSearchParams(window.location.search);
      const tokenFromUrl = queryParams.get('token');
      
      let token = null;

      if (tokenFromUrl) {
        console.log("AuthContext: Token found in URL from OAuth redirect.");
        localStorage.setItem('access_token', tokenFromUrl);
        token = tokenFromUrl;
        // Clean the URL to remove the token for security
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        // Fallback to checking localStorage
        token = localStorage.getItem('access_token');
      }

      if (token) {
        try {
          console.log("AuthContext: Token found, fetching user data...");
          const userData = await api.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('AuthContext: Failed to fetch user with token, removing token.', error);
          localStorage.removeItem('access_token');
          setUser(null);
        }
      }
      setLoading(false);
    };
    checkUser();
  }, []);

  const login = async (credentials) => {
    setLoading(true);
    console.log("AuthContext: Attempting login with credentials:", { email: credentials.email });

    try {
      const response = await api.login(credentials);
      
      if (response.access_token) {
        console.log("AuthContext: Login successful, token received.");
        localStorage.setItem('access_token', response.access_token);
        const currentUser = await api.getCurrentUser();
        console.log("AuthContext: User data fetched:", currentUser);
        setUser(currentUser);
      } else {
        throw new Error('Login failed: Invalid response from server');
      }
    } catch (error) {
      console.error('AuthContext: Login failed.', error);
      // This makes the original error available to the component for display
      throw error; 
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * This function correctly handles the server-side redirect flow.
   * It redirects the user to your backend, which then redirects to Google.
   */
  const googleLogin = () => {
    // The base URL of your backend API
    const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    // Redirect the user's browser to the backend endpoint that starts the Google OAuth flow
    window.location.href = `${apiUrl}/login/google`;
  };

  const signup = async (userData) => {
    setLoading(true);
    try {
      console.log("AuthContext: Attempting signup for:", { email: userData.email });
      await api.signup(userData);
      console.log("AuthContext: Signup successful. Now logging in...");
      // After a successful signup, automatically log the user in
      await login({ email: userData.email, password: userData.password });
    } catch (error) {
      console.error('AuthContext: Signup failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    console.log("AuthContext: Logging out.");
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    googleLogin,
    signup,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}