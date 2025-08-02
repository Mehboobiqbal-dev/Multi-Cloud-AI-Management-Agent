import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',

  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      // Consider redirecting to login page
    }
    // Ensure a consistent error structure is propagated
    const errorMessage = error.response?.data?.detail || error.message;
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
  submitPrompt(prompt) {
    return apiClient.post('/prompt', { prompt });
  },
  executePlan(plan) {
    return apiClient.post('/execute_plan', plan);
  }
};

export default api;
