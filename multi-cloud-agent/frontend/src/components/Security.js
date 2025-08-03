import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Tabs, Tab, Box, Typography } from '@mui/material';

function Security() {
  const [tabValue, setTabValue] = useState(0);
  const [key, setKey] = useState('');
  const [value, setValue] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAction = async (toolName) => {
    setLoading(true);
    try {
      let params = {};
      if (toolName === 'secure_store_credential') {
        params = { key, value };
      } else if (toolName === 'secure_get_credential') {
        params = { key };
      }
      const response = await api.callTool(toolName, params);
      // Ensure response is stringified if it's an object
      setResult(typeof response === 'object' ? JSON.stringify(response, null, 2) : response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Security - Credential Management</Typography>
      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Store Credential" />
        <Tab label="Get Credential" />
      </Tabs>
      <TextField
        label="Key"
        value={key}
        onChange={(e) => setKey(e.target.value)}
        fullWidth
        margin="normal"
      />
      {tabValue === 0 && (
        <TextField
          label="Value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          fullWidth
          margin="normal"
        />
      )}
      <Button
        onClick={() => handleAction(tabValue === 0 ? 'secure_store_credential' : 'secure_get_credential')}
        variant="contained"
        disabled={loading}
      >
        {tabValue === 0 ? 'Store' : 'Retrieve'}
      </Button>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Result:</Typography>
          <pre>{typeof result === 'object' ? JSON.stringify(result, null, 2) : result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default Security;