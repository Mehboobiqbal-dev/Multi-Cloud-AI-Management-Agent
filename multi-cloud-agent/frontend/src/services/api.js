import axios from 'axios';

const apiClient = axios.create({
  baseURL: (process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000')).replace(/\/$/, ''),

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
    const form_data = new URLSearchParams();
    form_data.append('username', credentials.email);
    form_data.append('password', credentials.password);
    return apiClient.post('/token', form_data, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
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
  runAgent(data) {
    // Accept either old format (string) or new format (object)
    if (typeof data === 'string') {
      const run_id = Date.now().toString();
      return apiClient.post('/agent/run', { user_input: data, run_id });
    }
    // New format with run_id parameter
    const { user_input, run_id = Date.now().toString() } = data;
    return apiClient.post('/agent/run', { user_input, run_id });
  },
  getHistory() {
    return apiClient.get('/chat/history');
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
    return apiClient.post('/form/automate_login', data);
  },
  registrationAutomation(data) {
    return apiClient.post('/form/automate_registration', data);
  },
  // Chat methods
  getChatHistory() {
    return apiClient.get('/chat/history');
  },
  sendChatMessage(message, messageType = 'text', agentRunId = null) {
    return apiClient.post('/chat/message', {
      message,
      message_type: messageType,
      agent_run_id: agentRunId
    });
  },
  // Custom API methods
  post(endpoint, data) {
    return apiClient.post(endpoint, data);
  },
  callTool(toolName, params) {
    return apiClient.post('/call_tool', { tool_name: toolName, params });
  },
  // The redundant WebSocket connection handler has been removed.
  // The application should use the singleton WebSocketService instead.
};

// ... (rest of the exported functions remain the same)
// Form automation endpoints
export const applyJobUpwork = (data) => api.post('/form/apply_job_upwork', data);
export const applyJobFiverr = (data) => api.post('/form/apply_job_fiverr', data);
export const applyJobLinkedin = (data) => api.post('/form/apply_job_linkedin', data);
export const batchApplyJobs = (data) => api.post('/form/batch_apply_jobs', data);
export const automateRegistration = (data) => api.post('/form/automate_registration', data);
export const automateLogin = (data) => api.post('/form/automate_login', data);

// Tool management endpoints
export const getAvailableTools = () => api.get('/tools');
export const callTool = (data) => api.post('/call_tool', data);

// Chat endpoints
export const sendChatMessage = (data) => api.post('/chat/message', data);
export const getChatHistory = () => api.get('/chat/history');

// Cloud credentials endpoints
export const getCredentials = () => api.get('/credentials');
export const saveCredentials = (data) => api.post('/credentials', data);
export const testCredentials = (data) => api.post('/credentials/test', data);

// Agent endpoints
export const runAgent = (data) => api.post('/agent/run', data);
export const getAgentStatus = (runId) => api.get(`/agent/status/${runId}`);
export const stopAgent = (runId) => api.post(`/agent/stop/${runId}`);

// Health check
export const healthCheck = () => api.get('/healthz');

// Additional function exports
export const getTaskResults = (params = { limit: 50, offset: 0, status: undefined }) => {
  const search = new URLSearchParams();
  if (params.limit != null) search.set('limit', String(params.limit));
  if (params.offset != null) search.set('offset', String(params.offset));
  if (params.status) search.set('status', params.status);
  return apiClient.get(`/api/tasks/results?${search.toString()}`);
};
export const getTaskStatistics = (days = 30) => apiClient.get(`/api/tasks/statistics?days=${days}`);
export const getScrapingResults = () => apiClient.get('/tasks/scraping');
export const getTaskDetails = (taskId) => apiClient.get(`/tasks/${taskId}`);

const exportedApi = {
  // Auth
  signup: api.signup,
  login: api.login,
  getCurrentUser: api.getMe,
  // Credentials
  getCredentials: api.getCredentials,
  saveCredentials: api.saveCredentials,
  testCredentials,
  // Agent
  runAgent: api.runAgent,
  getAgentStatus,
  stopAgent,
  // Chat
  getChatHistory: api.getChatHistory,
  sendChatMessage: api.sendChatMessage,
  // Tools
  getAvailableTools,
  callTool: api.callTool,
  // Form automation
  applyJobUpwork: api.applyJobUpwork,
  applyJobFiverr: api.applyJobFiverr,
  applyJobLinkedin: api.applyJobLinkedin,
  batchApplyJobs: api.batchApplyJobs,
  automateRegistration: api.registrationAutomation,
  automateLogin: api.loginAutomation,
  // Tasks
  getHistory: api.getHistory,
  getTaskResults,
  getTaskStatistics,
  getScrapingResults,
  getTaskDetails,
  // Health
  healthCheck
};
export default exportedApi;