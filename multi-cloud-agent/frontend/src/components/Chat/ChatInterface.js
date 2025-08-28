import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  History as HistoryIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Code as CodeIcon,
  Terminal as TerminalIcon,
  Cloud as CloudIcon,
  Work as WorkIcon,
  SmartToy as AutoModeIcon,
  ExpandMore,
  ContentCopy as CopyIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import api from '../../services/api';
import websocketService from '../../services/websocket';

const quickActions = [
  {
    id: 'deploy_app',
    label: 'Deploy Application',
    description: 'Deploy your app to cloud platforms',
    icon: CloudIcon,
    prompt: 'Help me deploy my application to AWS/Azure/GCP. Show me the available options and guide me through the process.'
  },
  {
    id: 'apply_jobs',
    label: 'Apply to Jobs',
    description: 'Automate job applications',
    icon: WorkIcon,
    prompt: 'I want to apply to jobs automatically. Help me set up job applications for Upwork, Fiverr, or LinkedIn.'
  },
  {
    id: 'run_command',
    label: 'Execute Command',
    description: 'Run terminal commands',
    icon: TerminalIcon,
    prompt: 'I need to run some terminal commands. Please help me execute them safely.'
  },
  {
    id: 'code_review',
    label: 'Code Review',
    description: 'Review and improve code',
    icon: CodeIcon,
    prompt: 'Please review my code and suggest improvements. I want to ensure best practices and optimization.'
  },
  {
    id: 'automate_task',
    label: 'Automate Task',
    description: 'Create automation workflows',
    icon: AutoModeIcon,
    prompt: 'Help me automate a repetitive task. I want to create a workflow that can run automatically.'
  }
];

function ChatInterface({ onToolCall, websocketConnected, currentRunId }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [historyDialog, setHistoryDialog] = useState(false);
  const [settingsDialog, setSettingsDialog] = useState(false);
  const [settings, setSettings] = useState({
    autoScroll: true,
    soundEnabled: false,
    voiceEnabled: false,
    theme: 'light',
    fontSize: 'medium'
  });
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [agentLogs, setAgentLogs] = useState([]);
  const [agentStatus, setAgentStatus] = useState('idle');

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
    initializeSpeechRecognition();

    const unsubscribeAgent = websocketService.subscribe('agent_updates', (data) => {
      if (data.status) {
        setAgentStatus(data.status);
      }
      if (data.log) {
        setAgentLogs(prev => [...prev, {
          id: Date.now() + Math.random(),
          message: data.log,
          timestamp: new Date().toISOString()
        }]);
      }
    });

    const unsubscribeChat = websocketService.subscribe('chat', (data) => {
      let content = data.message;
      let additionalMetadata = {};
      if (typeof data.message === 'object' && data.message !== null) {
        content = data.message.message || JSON.stringify(data.message);
        if (data.message.conversation_id) {
          additionalMetadata.conversation_id = data.message.conversation_id;
        }
      }
      const newMessage = {
        id: Date.now() + Math.random(),
        type: data.sender === 'user' ? 'user' : 'assistant',
        content,
        timestamp: new Date().toISOString(),
        metadata: { ...data.metadata || {}, ...additionalMetadata }
      };
      setMessages(prev => [...prev, newMessage]);
    });

    return () => {
      unsubscribeAgent();
      unsubscribeChat();
    };
  }, []);

  useEffect(() => {
    if (settings.autoScroll) {
      scrollToBottom();
    }
  }, [messages, settings.autoScroll]);

  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
      };
      
      recognitionInstance.onerror = () => {
        setIsListening(false);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
      };
      
      setRecognition(recognitionInstance);
    }
  };

  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory();
      const chatHistoryArray = Array.isArray(history) ? history : history?.data || [];
      setChatHistory(chatHistoryArray);
      
      if (chatHistoryArray.length > 0) {
        const recentChat = chatHistoryArray[0];
        setMessages(Array.isArray(recentChat.messages) ? recentChat.messages : []);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      setChatHistory([]);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setAgentLogs([]);
    setAgentStatus('processing');

    try {
      await api.sendChatMessage(inputValue, 'text', currentRunId);

      const agentResponse = await api.runAgent({
        user_input: inputValue,
        run_id: currentRunId || Date.now().toString()
      });

      const botMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: agentResponse.final_result || agentResponse.message || agentResponse.response || 'Agent is processing your request...',
        timestamp: new Date().toISOString(),
        metadata: agentResponse.metadata || {}
      };

      setMessages(prev => [...prev, botMessage]);

      if (agentResponse.tool_calls && onToolCall) {
        agentResponse.tool_calls.forEach(toolCall => {
          onToolCall(toolCall);
        });
      }

      if (settings.soundEnabled) {
        playNotificationSound();
      }

      if (settings.voiceEnabled) {
        speakText(botMessage.content);
      }

      if (agentResponse.task_completed || 
          (agentResponse.metadata && agentResponse.metadata.task_status === 'completed') ||
          botMessage.content.toLowerCase().includes('task completed') ||
          botMessage.content.toLowerCase().includes('successfully completed')) {
        
        setTimeout(() => {
          const taskNotificationMessage = {
            id: Date.now() + 2,
            type: 'assistant',
            content: `🎉 **Task Completed Successfully!**\n\nYour task has been completed. You can now:\n\n📋 **Ask Questions** - Ask me about the task details or results\n📥 **Download Data** - Get any files or data generated during the task`,
            timestamp: new Date().toISOString(),
            metadata: { 
              type: 'task_completion_notification',
              taskId: agentResponse.task_id || currentRunId
            }
          };
          setMessages(prev => [...prev, taskNotificationMessage]);
        }, 1000);
      }

    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setAgentStatus('idle');
    }
  };

  const handleQuickAction = (action) => {
    setInputValue(action.prompt);
    inputRef.current?.focus();
  };

  const handleVoiceInput = () => {
    if (!recognition) return;
    
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
      setIsListening(true);
    }
  };

  const playNotificationSound = () => {
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
    audio.play().catch(() => {});
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.8;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      speechSynthesis.speak(utterance);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const exportChat = () => {
    const chatData = {
      timestamp: new Date().toISOString(),
      messages: messages
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${format(new Date(), 'yyyy-MM-dd-HH-mm')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.type === 'error';
    
    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            maxWidth: '80%',
            flexDirection: isUser ? 'row-reverse' : 'row'
          }}
        >
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : isError ? 'error.main' : 'secondary.main',
              mx: 1,
              width: 32,
              height: 32
            }}
          >
            {isUser ? <PersonIcon /> : <BotIcon />}
          </Avatar>
          
          <Paper
            elevation={1}
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.main' : isError ? 'error.light' : 'background.paper',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              borderRadius: 2
            }}
          >
            <Typography
              variant="body1"
              sx={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontSize: settings.fontSize === 'small' ? '0.875rem' : 
                          settings.fontSize === 'large' ? '1.125rem' : '1rem'
              }}
            >
              {message.content}
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  opacity: 0.7,
                  fontSize: '0.75rem'
                }}
              >
                {format(new Date(message.timestamp), 'HH:mm')}
              </Typography>
              
              {!isUser && (
                <Tooltip title="Copy message">
                  <IconButton
                    size="small"
                    onClick={() => copyMessage(message.content)}
                    sx={{ opacity: 0.7, ml: 1 }}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
            
            {message.metadata && Object.keys(message.metadata).length > 0 && (
              <Accordion sx={{ mt: 1 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="caption">Metadata</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <pre style={{ fontSize: '0.75rem', margin: 0 }}>
                    {JSON.stringify(message.metadata, null, 2)}
                  </pre>
                </AccordionDetails>
              </Accordion>
            )}
          </Paper>
        </Box>
      </Box>
    );
  };

  const renderQuickActions = () => (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        Quick Actions
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Tooltip key={action.id} title={action.description}>
              <Chip
                icon={<Icon />}
                label={action.label}
                onClick={() => handleQuickAction(action)}
                variant="outlined"
                clickable
                sx={{ mb: 1 }}
              />
            </Tooltip>
          );
        })}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper elevation={1} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <BotIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              AI Assistant
            </Typography>
            <Chip
              label={websocketConnected ? 'Connected' : 'Disconnected'}
              color={websocketConnected ? 'success' : 'error'}
              size="small"
              sx={{ ml: 2 }}
            />
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Chat History">
              <IconButton onClick={() => setHistoryDialog(true)}>
                <HistoryIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton onClick={() => setSettingsDialog(true)}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Export Chat">
              <IconButton onClick={exportChat}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Clear Chat">
              <IconButton onClick={clearChat}>
                <ClearIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      <Box
        ref={chatContainerRef}
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          bgcolor: 'grey.50'
        }}
      >
        {messages.length === 0 && (
          <Box>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <BotIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" sx={{ mb: 1, fontWeight: 600 }}>
                👋 Welcome to Elch
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                I'm Elch, your intelligent AI agent. I can help you with cloud deployments, job applications, code reviews, and automation tasks.
                Choose a quick action below or type your own message.
              </Typography>
            </Box>
            {renderQuickActions()}
          </Box>
        )}
        
        {messages.map(renderMessage)}
        
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
              <Avatar sx={{ bgcolor: 'secondary.main', mx: 1, width: 32, height: 32 }}>
                <BotIcon />
              </Avatar>
              <Paper elevation={1} sx={{ p: 2, borderRadius: 2, maxWidth: '70%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: agentLogs.length > 0 ? 1 : 0 }}>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  <Typography variant="body2">
                    {agentStatus === 'processing' ? 'Processing your request...' : 'Thinking...'}
                  </Typography>
                </Box>
                {agentLogs.length > 0 && (
                  <Box sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'grey.50', p: 1, borderRadius: 1 }}>
                    {agentLogs.slice(-5).map((log) => (
                      <Typography 
                        key={log.id} 
                        variant="caption" 
                        sx={{ 
                          display: 'block', 
                          fontFamily: 'monospace', 
                          fontSize: '0.75rem',
                          color: 'text.secondary',
                          mb: 0.5,
                          wordBreak: 'break-word'
                        }}
                      >
                        {log.message}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Paper>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      <Paper elevation={3} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message here... (e.g., 'Deploy my app to AWS' or 'Apply to jobs on LinkedIn')"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={isLoading}
            variant="outlined"
            sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
          />
          
          {recognition && (
            <Tooltip title={isListening ? 'Stop listening' : 'Voice input'}>
              <IconButton
                onClick={handleVoiceInput}
                color={isListening ? 'error' : 'default'}
                disabled={isLoading}
              >
                {isListening ? <MicIcon /> : <MicOffIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Send message">
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              color="primary"
              sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}
            >
              <SendIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      <Dialog open={historyDialog} onClose={() => setHistoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Chat History</DialogTitle>
        <DialogContent>
          <List>
            {Array.isArray(chatHistory) && chatHistory.length > 0 ? (
              chatHistory.map((chat, index) => (
                <ListItem key={index} button>
                  <ListItemIcon>
                    <HistoryIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={`Conversation ${index + 1}`}
                    secondary={format(new Date(chat.timestamp), 'PPpp')}
                  />
                </ListItem>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No chat history available
              </Typography>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={settingsDialog} onClose={() => setSettingsDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Chat Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.autoScroll}
                  onChange={(e) => setSettings(prev => ({ ...prev, autoScroll: e.target.checked }))}
                />
              }
              label="Auto-scroll to new messages"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={settings.soundEnabled}
                  onChange={(e) => setSettings(prev => ({ ...prev, soundEnabled: e.target.checked }))}
                />
              }
              label="Sound notifications"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={settings.voiceEnabled}
                  onChange={(e) => setSettings(prev => ({ ...prev, voiceEnabled: e.target.checked }))}
                />
              }
              label="Voice responses"
            />
            
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Font Size</InputLabel>
              <Select
                value={settings.fontSize}
                label="Font Size"
                onChange={(e) => setSettings(prev => ({ ...prev, fontSize: e.target.value }))}
              >
                <MenuItem value="small">Small</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="large">Large</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ChatInterface;