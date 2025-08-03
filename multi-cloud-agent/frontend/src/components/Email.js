import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Tabs, Tab, Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

function Email() {
  const [tabValue, setTabValue] = useState(0);
  const [provider, setProvider] = useState('gmail');
  const [emailId, setEmailId] = useState('');
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAction = async (toolName) => {
    setLoading(true);
    try {
      let params = {};
      if (toolName.includes('read')) {
        params = { provider };
      } else if (toolName.includes('reply')) {
        params = { email_id: emailId, reply: body, provider };
      } else if (toolName.includes('send')) {
        params = { to, subject, body };
      }
      const response = await api.callTool(toolName, params);
      setResult(response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  const getToolName = () => {
    if (tabValue === 0) return provider === 'gmail' ? 'read_emails_gmail' : 'read_emails_outlook';
    if (tabValue === 1) return provider === 'gmail' ? 'reply_email_gmail' : 'reply_email_outlook';
    if (tabValue === 2) return provider === 'gmail' ? 'send_email_gmail' : 'send_email_outlook';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Email & Messaging</Typography>
      <FormControl fullWidth margin="normal">
        <InputLabel>Provider</InputLabel>
        <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
          <MenuItem value="gmail">Gmail</MenuItem>
          <MenuItem value="outlook">Outlook</MenuItem>
        </Select>
      </FormControl>
      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Read Emails" />
        <Tab label="Reply to Email" />
        <Tab label="Send Email" />
      </Tabs>
      {tabValue === 1 && (
        <TextField label="Email ID" value={emailId} onChange={(e) => setEmailId(e.target.value)} fullWidth margin="normal" />
      )}
      {tabValue === 2 && (
        <>
          <TextField label="To" value={to} onChange={(e) => setTo(e.target.value)} fullWidth margin="normal" />
          <TextField label="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} fullWidth margin="normal" />
        </>
      )}
      {(tabValue === 1 || tabValue === 2) && (
        <TextField label={tabValue === 1 ? 'Reply' : 'Body'} value={body} onChange={(e) => setBody(e.target.value)} fullWidth margin="normal" multiline />
      )}
      <Button onClick={() => handleAction(getToolName())} variant="contained" disabled={loading}>
        {tabValue === 0 ? 'Read Emails' : tabValue === 1 ? 'Reply' : 'Send'}
      </Button>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Result:</Typography>
          <pre>{result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default Email;