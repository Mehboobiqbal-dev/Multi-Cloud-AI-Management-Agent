import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

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

const Dashboard = ({ user, onLogout }) => {
  return (
    <div style={{ maxWidth: '800px', margin: '50px auto', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>Multi-Cloud AI Management</h1>
        <button
          onClick={onLogout}
          style={{
            padding: '10px 20px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Logout
        </button>
      </div>
      
      <div style={{ backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '8px' }}>
        <h3>Welcome, {user?.name || user?.email || 'User'}!</h3>
        <p>This is your dashboard. The full application will be available once we resolve the routing issues.</p>
        
        <div style={{ marginTop: '20px' }}>
          <h4>Current Status:</h4>
          <ul>
            <li>✅ Backend API is configured</li>
            <li>✅ CORS is being fixed</li>
            <li>🔄 Frontend routing is being resolved</li>
            <li>⏳ Full functionality coming soon</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUserSession = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await api.get('/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          setUser(response.data);
        } catch (error) {
          console.error('Session check failed:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    
    checkUserSession();
  }, []);

  const handleLogin = async (credentials) => {
    try {
      console.log('Login attempt:', credentials);
      
      // Try to login with the backend
      const formData = new FormData();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);
      
      const response = await api.post('/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        
        // Get user info
        const userResponse = await api.get('/me', {
          headers: {
            'Authorization': `Bearer ${response.data.access_token}`,
          },
        });
        
        setUser(userResponse.data);
        console.log('Login successful:', userResponse.data);
      }
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please check your credentials.');
    }
  };

  const handleSignup = async (userData) => {
    try {
      console.log('Signup attempt:', userData);
      
      const response = await api.post('/signup', userData);
      
      if (response.data) {
        alert('Account created successfully! Please login.');
        console.log('Signup successful:', response.data);
      }
    } catch (error) {
      console.error('Signup failed:', error);
      alert('Signup failed. Please try again.');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

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
        <Dashboard user={user} onLogout={handleLogout} />
      ) : (
        <LoginForm onLogin={handleLogin} onSignup={handleSignup} />
      )}
    </div>
  );
}

export default App;
