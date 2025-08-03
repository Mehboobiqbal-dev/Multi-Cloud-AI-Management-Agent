import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel, Box, Typography } from '@mui/material';

function ApiIntegration() {
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState('GET');
  const [headers, setHeaders] = useState('');
  const [body, setBody] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.callTool('call_api', { url, method, headers: JSON.parse(headers || '{}'), body: body ? JSON.parse(body) : null });
      setResult(JSON.stringify(response, null, 2));
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">API Integration</Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label="API URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          fullWidth
          margin="normal"
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Method</InputLabel>
          <Select value={method} onChange={(e) => setMethod(e.target.value)}>
            <MenuItem value="GET">GET</MenuItem>
            <MenuItem value="POST">POST</MenuItem>
            <MenuItem value="PUT">PUT</MenuItem>
            <MenuItem value="DELETE">DELETE</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Headers (JSON)"
          value={headers}
          onChange={(e) => setHeaders(e.target.value)}
          fullWidth
          margin="normal"
          multiline
        />
        <TextField
          label="Body (JSON)"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          fullWidth
          margin="normal"
          multiline
        />
        <Button type="submit" variant="contained" disabled={loading}>
          Call API
        </Button>
      </form>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Response:</Typography>
          <pre>{result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default ApiIntegration;