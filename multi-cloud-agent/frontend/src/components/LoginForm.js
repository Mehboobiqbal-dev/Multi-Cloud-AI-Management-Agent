import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import styles from './LoginForm.module.css';

const LoginForm = () => {
  const { login, signup, googleLogin } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGoogleCallback = useCallback((response) => {
    googleLogin(response.credential)
      .catch(err => setError(err.message));
  }, [googleLogin, setError]);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  
    script.onload = () => {
      window.google.accounts.id.initialize({
        client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
        callback: handleGoogleCallback,
      });
      window.google.accounts.id.renderButton(
        document.getElementById('googleSignInButton'),
        { theme: 'outline', size: 'large' }
      );
    };
  
    return () => {
      document.body.removeChild(script);
    };
  }, [handleGoogleCallback]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isSignup) {
        await signup({ email, password, name });
      } else {
        await login({ email, password });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles['login-container']}>
      <h2 className={styles['login-title']}>
        {isSignup ? '🚀 Create Account' : '👋 Welcome Back'}
      </h2>
      
      {error && (
        <div className={styles['error-message']}>
          ⚠️ {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        {isSignup && (
          <div className={styles['form-group']}>
            <input
              type="text"
              placeholder="👤 Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              required={isSignup}
            />
          </div>
        )}
        <div className={styles['form-group']}>
          <input
            type="email"
            placeholder="📧 Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </div>
        <div className={styles['form-group']}>
          <input
            type="password"
            placeholder="🔒 Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className={styles['submit-button']}
        >
          {loading ? (
            <span>⏳ Processing...</span>
          ) : (
            <span>{isSignup ? '🚀 Create Account' : '🔐 Sign In'}</span>
          )}
        </button>
      </form>
      <button
        onClick={() => setIsSignup(!isSignup)}
        className={styles['toggle-button']}
      >
        {isSignup ? '👈 Already have an account? Login' : '✨ Need an account? Sign Up'}
      </button>
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '20px' }}>
        <div id="googleSignInButton"></div>
      </div>
    </div>
  );
};

export default LoginForm;