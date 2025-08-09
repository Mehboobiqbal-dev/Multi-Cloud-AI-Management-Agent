import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import websocketService from '../services/websocket';
import { AppBar, Toolbar, Typography, Button, Container, Box, TextField, Paper, CircularProgress, List, ListItem, ListItemText } from '@mui/material';

function Dashboard({ navigate }) {
  const { user, logout } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const wsConnection = websocketService.connect(null, token);
    const unsubscribe = websocketService.subscribe('agent_updates', (update) => {
      if (update.log) {
        setLogs(prevLogs => [...prevLogs, update.log]);
      }
      if (update.status === 'complete' && update.data) {
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
      </Container>
    </Box>
  );
}


export default Dashboard;
