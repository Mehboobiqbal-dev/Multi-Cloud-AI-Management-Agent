// WebSocket service for handling real-time connections

class WebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
    this.listeners = {};
    this.subscribers = {};
    this.isConnected = false;
    this.url = null;
  }

  connect(url, token) {
    let finalUrl = url;
    // If no URL is provided, use the default backend WebSocket URL
    if (!finalUrl) {
      // Determine the WebSocket URL based on the current environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Use the API URL from environment or fallback to Render backend URL
      const apiHost = (process.env.REACT_APP_API_URL || 'https://multi-cloud-ai-management-agent.onrender.com').replace(/^https?:\/\//, '');
      let wsUrl = `${protocol}//${apiHost}/ws`;
      if (process.env.NODE_ENV !== 'production' && !process.env.REACT_APP_API_URL) {
        wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
      }
      finalUrl = wsUrl;
    }

    const authToken = token || localStorage.getItem('access_token');
    if (authToken) {
      // Ensure we are appending query params correctly
      if (finalUrl.includes('?')) {
        finalUrl += `&token=${authToken}`;
      } else {
        finalUrl += `?token=${authToken}`;
      }
    }
    
    this.url = finalUrl;
    
    // Close existing connection if any
    if (this.socket) {
      this.disconnect();
    }

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.reconnectAttempts = 0;
        this.isConnected = true;
        this.notifyListeners('open', { status: 'connected' });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notifyListeners('message', data);
          
          // Notify topic subscribers if the message has a topic
          if (data && data.topic && this.subscribers[data.topic]) {
            this.subscribers[data.topic].forEach(callback => {
              try {
                callback(data.payload || data);
              } catch (error) {
                console.error(`Error in WebSocket subscriber for topic ${data.topic}:`, error);
              }
            });
          }
        } catch (error) {
          console.warn('Failed to parse WebSocket message:', error);
          this.notifyListeners('message', { raw: event.data, error: 'Parse error' });
        }
      };

      this.socket.onerror = (error) => {
        // Suppress console error output to avoid the red error in console
        // console.warn('WebSocket error:', error);
        this.isConnected = false;
        this.notifyListeners('error', { error });
      };

      this.socket.onclose = (event) => {
        this.isConnected = false;
        if (event.wasClean) {
          console.log(`WebSocket connection closed cleanly, code=${event.code}, reason=${event.reason}`);
          this.notifyListeners('close', { clean: true, code: event.code, reason: event.reason });
        } else {
          // Suppress console warning to avoid the error in console
          // console.warn('WebSocket connection died');
          this.notifyListeners('close', { clean: false });
          this.attemptReconnect(url);
        }
      };

      return true;
    } catch (error) {
      // Suppress console error to avoid the red error in console
      // console.error('Failed to create WebSocket connection:', error);
      this.notifyListeners('error', { error, message: 'Connection creation failed' });
      return false;
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.isConnected = false;
  }
  
  // Subscribe to a specific topic
  subscribe(topic, callback) {
    if (!this.subscribers[topic]) {
      this.subscribers[topic] = [];
    }
    this.subscribers[topic].push(callback);
    
    // Return an unsubscribe function
    return () => this.unsubscribe(topic, callback);
  }
  
  // Unsubscribe from a topic
  unsubscribe(topic, callback) {
    if (this.subscribers[topic]) {
      this.subscribers[topic] = this.subscribers[topic].filter(cb => cb !== callback);
    }
  }

  attemptReconnect(url) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts} of ${this.maxReconnectAttempts})`);
      
      this.reconnectTimeout = setTimeout(() => {
        console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
        this.connect(url);
      }, delay);
    } else {
      console.error('Maximum reconnection attempts reached');
      this.notifyListeners('reconnect_failed', { attempts: this.reconnectAttempts });
    }
  }

  send(data) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message: WebSocket is not connected');
      return false;
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.socket.send(message);
      return true;
    } catch (error) {
      console.error('Failed to send message:', error);
      return false;
    }
  }

  addListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  removeListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  notifyListeners(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket ${event} listener:`, error);
        }
      });
    }
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();

export default websocketService;
