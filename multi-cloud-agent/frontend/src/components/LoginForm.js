import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import styles from './LoginForm.module.css';

const LoginForm = () => {
  const { login, signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
    </div>
  );
};

export default LoginForm;