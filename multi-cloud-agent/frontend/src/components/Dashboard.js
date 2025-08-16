import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import websocketService from '../services/websocket';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  TextField,
  Paper,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Grid,
  Tabs,
  Tab,
  Drawer,
  CssBaseline,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon
} from '@mui/icons-material';
import ChatInterface from './Chat/ChatInterface';
import TaskResults from './TaskResults';
import CloudCredentials from './CloudCredentials/CloudCredentials';
import FormAutomation from './FormAutomation/FormAutomation';
import ToolManager from './ToolManager/ToolManager';
import Sidebar from './Navigation/Sidebar';

function Dashboard({ navigate }) {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentRunId, setCurrentRunId] = useState(null);
  const [activeView, setActiveView] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [websocketConnected, setWebsocketConnected] = useState(false);
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Add logout from AuthContext and stop relying on navigate prop
  const { logout } = useAuth();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    // Let websocketService handle URL construction and token appending
    websocketService.connect(null, token);

    const unsubscribe = websocketService.subscribe('agent_updates', (update) => {
      if (update.log) {
        setLogs(prevLogs => [...prevLogs, update.log]);
      }
      if (update.status === 'complete' || update.status === 'error') {
        setResponse(update.data);
        setLoading(false);
      }
      if (update.type === 'connection_status') {
        setWebsocketConnected(update.connected);
      }
    });

    // Set initial connection status
    setWebsocketConnected(websocketService.isConnected);

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  useEffect(() => {
    // Auto-close sidebar on mobile
    if (isMobile) {
      setSidebarOpen(false);
    } else {
      setSidebarOpen(true);
    }
  }, [isMobile]);

  useEffect(() => {
    const updateAgentStatus = () => {
      // This would typically fetch the current agent status
      console.log('Checking agent status...');
    };

    const interval = setInterval(updateAgentStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handlePromptSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setResponse('');
    setLogs([]);

    try {
      const result = await api.executeAgent({ prompt });
      setCurrentRunId(result.run_id);
      setResponse(result.message || 'Agent started successfully');
    } catch (error) {
      setResponse(`Error: ${error.message}`);
      setLoading(false);
    }
  };

  const handleNavigationChange = (view) => {
    setActiveView(view);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleToolCall = (toolCall) => {
    // Handle tool calls from chat interface
    console.log('Tool call received:', toolCall);
    setLogs(prev => [...prev, `Tool called: ${toolCall.name}`]);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleAgentControl = (action) => {
    // Placeholder for pause/resume future behavior
    console.log('Agent control:', action, 'for run id', currentRunId);
  };

  const drawerWidth = 280;

  const renderMainContent = () => {
    switch (activeView) {
      case 'chat':
        return (
          <ChatInterface
            onToolCall={handleToolCall}
            websocketConnected={websocketConnected}
            currentRunId={currentRunId}
          />
        );
      case 'tasks':
        return <TaskResults />;
      case 'credentials':
        return <CloudCredentials />;
      case 'automation':
        return <FormAutomation />;
      case 'tools':
        return <ToolManager />;
      case 'legacy':
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
              Legacy Agent Control
            </Typography>
            
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Direct Agent Execution
              </Typography>
              
              <Box component="form" onSubmit={handlePromptSubmit} sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Enter your prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  variant="outlined"
                  sx={{ mb: 2 }}
                  placeholder="e.g., Deploy my React app to AWS, Apply to jobs on LinkedIn, etc."
                />
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                  {loading ? 'Processing...' : 'Execute'}
                </Button>
              </Box>

              {response && (
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="h6" gutterBottom>
                    Response:
                  </Typography>
                  <Typography variant="body1">
                    {typeof response === 'string' ? response : JSON.stringify(response, null, 2)}
                  </Typography>
                </Paper>
              )}

              {logs.length > 0 && (
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="h6" gutterBottom>
                    Logs:
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {logs.map((log, index) => (
                      <Typography key={index} variant="body2" sx={{ fontFamily: 'monospace', mb: 0.5 }}>
                        {log}
                      </Typography>
                    ))}
                  </Box>
                </Paper>
              )}
            </Paper>
          </Box>
        );
      default:
        return (
          <ChatInterface
            onToolCall={handleToolCall}
            websocketConnected={websocketConnected}
            currentRunId={currentRunId}
          />
        );
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          transition: (theme) => theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(sidebarOpen && {
            marginLeft: drawerWidth,
            width: `calc(100% - ${drawerWidth}px)`,
            transition: (theme) => theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={toggleSidebar}
            edge="start"
            sx={{
              marginRight: 5,
              ...(sidebarOpen && { display: 'none' }),
            }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Multi-Cloud AI Management Agent
          </Typography>
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant={isMobile ? 'temporary' : 'persistent'}
        open={sidebarOpen}
        onClose={toggleSidebar}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar>
          <IconButton onClick={toggleSidebar}>
            <ChevronLeftIcon />
          </IconButton>
        </Toolbar>
        <Sidebar
          activeView={activeView}
          onNavigationChange={handleNavigationChange}
          websocketConnected={websocketConnected}
        />
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          height: '100vh',
          overflow: 'hidden',
          transition: (theme) => theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          marginLeft: sidebarOpen && !isMobile ? 0 : `-${drawerWidth}px`,
        }}
      >
        <Toolbar />
        {renderMainContent()}
      </Box>
    </Box>
  );
}


export default Dashboard;
