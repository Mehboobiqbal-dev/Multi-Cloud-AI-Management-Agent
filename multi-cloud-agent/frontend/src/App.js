import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';
import { useAuth } from './contexts/AuthContext';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Simple components without routing for now
const LoginForm = ({ onLogin, onSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignup, setIsSignup] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSignup) {
      onSignup({ email, password, name });
    } else {
      onLogin({ email, password });
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px' }}>
      <h2>{isSignup ? 'Sign Up' : 'Login'}</h2>
      <form onSubmit={handleSubmit}>
        {isSignup && (
          <div style={{ marginBottom: '15px' }}>
            <input
              type="text"
              placeholder="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: '100%', padding: '10px', fontSize: '16px' }}
              autoComplete="name"
              required={isSignup}
            />
          </div>
        )}
        <div style={{ marginBottom: '15px' }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
            autoComplete="email"
            required
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '10px', fontSize: '16px' }}
            autoComplete="current-password"
            required
          />
        </div>
        <button
          type="submit"
          style={{
            width: '100%',
            padding: '10px',
            fontSize: '16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '10px'
          }}
        >
          {isSignup ? 'Sign Up' : 'Login'}
        </button>
      </form>
      <button
        onClick={() => setIsSignup(!isSignup)}
        style={{
          width: '100%',
          padding: '8px',
          fontSize: '14px',
          backgroundColor: 'transparent',
          color: '#007bff',
          border: '1px solid #007bff',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        {isSignup ? 'Already have an account? Login' : 'Need an account? Sign Up'}
      </button>
    </div>
  );
};

function App() {
  const { user, loading, login, signup } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
      </div>
    );
  }

  return (
    <div className="App">
      {user ? (
        <Dashboard />
      ) : (
        <LoginForm onLogin={login} onSignup={signup} />
      )}
    </div>
  );
}

export default App;
