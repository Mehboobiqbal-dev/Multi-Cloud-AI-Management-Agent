import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import websocketService from '../services/websocket';
import { AppBar, Toolbar, Typography, Button, Container, Box, TextField, Paper, CircularProgress, List, ListItem, ListItemText, Grid } from '@mui/material';
import ChatComponent from './Chat/ChatComponent';

function Dashboard({ navigate }) {
  const { user, logout } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentRunId, setCurrentRunId] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    // Pass the token as a query parameter for WebSocket authentication
    const wsUrl = `ws://${window.location.hostname}:8000/ws?token=${token}`;
    websocketService.connect(wsUrl);

    const unsubscribe = websocketService.subscribe('agent_updates', (update) => {
      if (update.log) {
        setLogs(prevLogs => [...prevLogs, update.log]);
      }
      if (update.status === 'complete' || update.status === 'error') {
        setResponse(update.data);
        setLoading(false);
      }
    });

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  const handlePromptSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setLogs([]);
    try {
      const run_id = Date.now().toString();
      setCurrentRunId(run_id);
      const data = await api.runAgent(prompt);
      setResponse(data);
    } catch (err) {
      console.error('Agent run failed:', err);
      const message = err.message || 'An error occurred while running the agent.';
      setResponse({ status: 'error', message: message });
    } finally {
      setLoading(false);
    }
  };

  const handleAgentControl = (action) => {
    // Placeholder for pause/resume future behavior
    console.log('Agent control:', action, 'for run id', currentRunId);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Universal AI Agent
          </Typography>
          <Button color="inherit" onClick={logout}>Logout</Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <form onSubmit={handlePromptSubmit}>
                <TextField
                  fullWidth
                  label="Enter your command"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  variant="outlined"
                  disabled={loading}
                />
                <Button type="submit" variant="contained" sx={{ mt: 1 }} disabled={loading}>
                  {loading ? <CircularProgress size={24} /> : 'Run'}
                </Button>
              </form>
            </Paper>

            {response && (
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6">Result</Typography>
                <pre>{JSON.stringify(response, null, 2)}</pre>
              </Paper>
            )}

            <Paper sx={{ p: 2 }}>
              <Typography variant="h6">Logs</Typography>
              <List>
                {logs.map((log, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={log} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <ChatComponent currentAgentRunId={currentRunId} onAgentControl={handleAgentControl} />
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}


export default Dashboard;
