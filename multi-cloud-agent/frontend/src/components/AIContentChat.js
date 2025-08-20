import React, { useState } from 'react';
import './AIContentChat.css';

const AIContentChat = ({ taskId, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      message: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/tasks/${taskId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: inputMessage })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage = {
        id: Date.now() + 1,
        sender: 'ai',
        message: data.response,
        timestamp: new Date().toLocaleTimeString(),
        context: data.context
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="ai-chat-overlay">
      <div className="ai-chat-container">
        <div className="ai-chat-header">
          <h3>AI Content Analysis</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="ai-chat-messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>👋 Hi! I can help you analyze the scraped content. Ask me anything about:</p>
              <ul>
                <li>Content summary and key points</li>
                <li>Specific information extraction</li>
                <li>Data analysis and insights</li>
                <li>Content structure and organization</li>
              </ul>
            </div>
          )}
          
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.sender}`}>
              <div className="message-content">
                <div className="message-text">{msg.message}</div>
                <div className="message-time">{msg.timestamp}</div>
                {msg.context && (
                  <div className="message-context">
                    <small>
                      📄 {msg.context.title} | 📊 {msg.context.word_count} words
                    </small>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message ai loading">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="ai-chat-input">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about the scraped content..."
            rows={3}
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            disabled={!inputMessage.trim() || isLoading}
            className="send-btn"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIContentChat;