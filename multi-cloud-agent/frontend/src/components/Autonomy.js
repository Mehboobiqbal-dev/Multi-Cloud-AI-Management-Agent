import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Box, Typography } from '@mui/material';

function Autonomy() {
  const [goal, setGoal] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    setLogs([]);
    try {
      const response = await api.post('/agent/run', { goal });
      // Handle logs properly whether they're objects or strings
      const logs = response.data.logs || [];
      setLogs(logs.map(log => typeof log === 'object' ? JSON.stringify(log, null, 2) : log));
    } catch (err) {
      setLogs(['Error: ' + err.message]);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Autonomy - Agent Loop</Typography>
      <TextField
        label="Enter your goal"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        fullWidth
        margin="normal"
        multiline
      />
      <Button onClick={handleRun} variant="contained" disabled={loading}>
        Run Agent
      </Button>
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6">Execution Logs:</Typography>
        <pre>{logs.join('\n')}</pre>
      </Box>
    </Box>
  );
}

export default Autonomy;