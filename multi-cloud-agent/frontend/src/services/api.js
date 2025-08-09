import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://127.0.0.1:8000',

  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  response => {
    // Ensure response.data is properly handled if it's an object
    return response.data;
  },
  error => {
    // Handle network errors gracefully
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject(new Error('Network error: Please check your connection'));
    }
    
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      // Consider redirecting to login page
    }
    
    // Ensure a consistent error structure is propagated
    let errorMessage = error.message;
    
    // Handle validation errors (422)
    if (error.response?.status === 422 && error.response?.data?.detail) {
      // Format validation errors in a user-friendly way
      const validationErrors = error.response.data.detail;
      if (Array.isArray(validationErrors) && validationErrors.length > 0) {
        // Extract meaningful messages from validation errors
        const messages = validationErrors.map(err => {
          const field = err.loc?.slice(-1)[0] || 'field';
          return `${field}: ${err.msg}`;
        });
        errorMessage = messages.join('\n');
      } else {
        errorMessage = JSON.stringify(error.response.data.detail);
      }
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    }
    
    return Promise.reject(new Error(errorMessage));
  }
);

const api = {
  signup(userData) {
    return apiClient.post('/signup', userData);
  },
  login(credentials) {
    return apiClient.post('/token', credentials);
  },
  getMe() {
    return apiClient.get('/me');
  },
  getCredentials() {
    return apiClient.get('/credentials');
  },
  saveCredentials(credData) {
    return apiClient.post('/credentials', credData);
  },
  runAgent(user_input) {
    const run_id = Date.now().toString(); // Simple unique ID
    return apiClient.post('/agent/run', { user_input, run_id });
  },
  getHistory() {
    return apiClient.get('/history');
  },
  // Form automation methods
  applyJobUpwork(data) {
    return apiClient.post('/form/apply_job_upwork', data);
  },
  applyJobFiverr(data) {
    return apiClient.post('/form/apply_job_fiverr', data);
  },
  applyJobLinkedin(data) {
    return apiClient.post('/form/apply_job_linkedin', data);
  },
  batchApplyJobs(data) {
    return apiClient.post('/form/batch_apply_jobs', data);
  },
  loginAutomation(data) {
    return apiClient.post('/form/login_automation', data);
  },
  registrationAutomation(data) {
    return apiClient.post('/form/registration_automation', data);
  },
  // Custom API methods
  post(endpoint, data) {
    return apiClient.post(endpoint, data);
  },
  callTool(toolName, params) {
    return apiClient.post('/call_tool', { tool_name: toolName, params });
  },
  // WebSocket connection handler with error handling
  createWebSocketConnection(url) {
    try {
      // Try to determine if we need to use a fallback URL
      if (!url) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const apiHost = process.env.REACT_APP_API_URL || '127.0.0.1:8000';
        url = `${protocol}//${apiHost}/ws`;
      }
      
      let socket;
      
      try {
        socket = new WebSocket(url);
      } catch (wsError) {
        // If the initial connection fails, try a fallback port
        if (url.includes(':8000')) {
          const fallbackUrl = url.replace(':8000', ':52828');
          console.log('Attempting fallback WebSocket connection to:', fallbackUrl);
          socket = new WebSocket(fallbackUrl);
        } else {
          throw wsError;
        }
      }
      
      // Add error handling but suppress console errors
      socket.onerror = (error) => {
        // Silently handle the error to avoid console errors
        // console.warn('WebSocket error:', error);
      };
      
      socket.onclose = (event) => {
        if (!event.wasClean) {
          // Silently handle the error to avoid console errors
          // console.warn('WebSocket connection closed unexpectedly');
        }
      };
      
      return socket;
    } catch (error) {
      // Silently handle the error to avoid console errors
      // console.error('Failed to create WebSocket connection:', error);
      return null;
    }
  }
};

export default api;
