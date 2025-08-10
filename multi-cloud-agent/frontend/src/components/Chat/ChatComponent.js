import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Divider,
  CircularProgress
} from '@mui/material';
import { Send, SmartToy, Person, Pause, PlayArrow } from '@mui/icons-material';
import api from '../../services/api';
import websocketService from '../../services/websocket';

const ChatComponent = ({ currentAgentRunId, onAgentControl }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState('idle');
  const messagesEndRef = useRef(null);
  const localCounterRef = useRef(0);

  // Generate a robust unique id (fallback if crypto.randomUUID isn't available)
  const genId = () => {
    try {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
      }
    } catch (_) {}
    const c = localCounterRef.current++;
    return `${Date.now()}-${Math.random().toString(36).slice(2)}-${c}`;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load chat history
    loadChatHistory();

    // Subscribe to WebSocket chat messages
    const unsubscribeChat = websocketService.subscribe('chat', (data) => {
      const newMsg = {
        id: genId(),
        sender: data.sender,
        message: data.message,
        message_type: data.message_type || 'text',
        agent_run_id: data.agent_run_id,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, newMsg]);
    });

    // Subscribe to agent updates
    const unsubscribeAgent = websocketService.subscribe('agent_updates', (data) => {
      if (data.status) {
        setAgentStatus(data.status);
      }
      if (data.log) {
        // Add agent log as a message
        const logMsg = {
          id: genId(),
          sender: 'agent',
          message: data.log,
          message_type: 'log',
          agent_run_id: currentAgentRunId,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, logMsg]);
      }
    });

    return () => {
      unsubscribeChat();
      unsubscribeAgent();
    };
  }, [currentAgentRunId]);

  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory();
      setMessages(history);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    setLoading(true);
    try {
      await api.sendChatMessage(newMessage, 'text', currentAgentRunId);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getMessageIcon = (sender, messageType) => {
    if (sender === 'user') return <Person color="primary" />;
    if (messageType === 'log') return <SmartToy color="secondary" />;
    return <SmartToy color="action" />;
  };

  const getMessageColor = (sender, messageType) => {
    if (sender === 'user') return 'primary.light';
    if (messageType === 'log') return 'grey.100';
    return 'secondary.light';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy />
          Agent Chat
          <Chip 
            label={agentStatus} 
            size="small" 
            color={agentStatus === 'running' ? 'success' : agentStatus === 'error' ? 'error' : 'default'}
          />
        </Typography>
        {currentAgentRunId && (
          <Typography variant="caption" color="textSecondary">
            Run ID: {currentAgentRunId}
          </Typography>
        )}
        
        {/* Agent Control Buttons */}
        <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            startIcon={agentStatus === 'running' ? <Pause /> : <PlayArrow />}
            onClick={() => onAgentControl?.(agentStatus === 'running' ? 'pause' : 'resume')}
            disabled={!currentAgentRunId}
          >
            {agentStatus === 'running' ? 'Pause Agent' : 'Resume Agent'}
          </Button>
        </Box>
      </Box>

      {/* Messages Area */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        <List>
          {messages.map((msg, idx) => (
            <ListItem key={msg.id || `${msg.timestamp}-${msg.sender}-${idx}`} sx={{ py: 0.5 }}>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'flex-start', 
                gap: 1, 
                width: '100%',
                flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row'
              }}>
                {getMessageIcon(msg.sender, msg.message_type)}
                <Box sx={{ 
                  maxWidth: '70%',
                  bgcolor: getMessageColor(msg.sender, msg.message_type),
                  p: 1,
                  borderRadius: 1,
                  ml: msg.sender === 'user' ? 'auto' : 0,
                  mr: msg.sender === 'user' ? 0 : 'auto'
                }}>
                  <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                    {msg.message}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {formatTimestamp(msg.timestamp)}
                    {msg.message_type !== 'text' && (
                      <Chip 
                        label={msg.message_type} 
                        size="small" 
                        sx={{ ml: 1, height: 16, fontSize: '0.6rem' }}
                      />
                    )}
                  </Typography>
                </Box>
              </Box>
            </ListItem>
          ))}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      <Divider />

      {/* Message Input */}
      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          multiline
          maxRows={3}
          placeholder="Type a message to the agent..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          size="small"
        />
        <IconButton 
          onClick={sendMessage} 
          disabled={loading || !newMessage.trim()}
          color="primary"
        >
          {loading ? <CircularProgress size={24} /> : <Send />}
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatComponent;