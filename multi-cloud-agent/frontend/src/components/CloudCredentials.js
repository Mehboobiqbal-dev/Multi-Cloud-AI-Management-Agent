import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, Grid, TextField, Select, MenuItem, FormControl, InputLabel, List, ListItem, ListItemText, IconButton, Alert } from '@mui/material';
import { Add, Check, Delete } from '@mui/icons-material';
import api from '../../services/api';

const providers = ['aws', 'azure', 'gcp'];
const fields = {
  aws: ['access_key_id', 'secret_access_key', 'region'],
  azure: ['tenant_id', 'client_id', 'client_secret', 'subscription_id'],
  gcp: ['service_account_key', 'project_id']
};

const CloudCredentials = () => {
  const [credentials, setCredentials] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('aws');
  const [formData, setFormData] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    try {
      const response = await api.get('/credentials');
      setCredentials(response.data);
    } catch (err) {
      setError('Failed to fetch credentials');
    }
  };

  const handleProviderChange = (e) => {
    setSelectedProvider(e.target.value);
    setFormData({});
  };

  const handleInputChange = (key, value) => {
    setFormData(prev => ({...prev, [key]: value}));
  };

  const handleAdd = async () => {
    let command = `add_cloud_credential provider=${selectedProvider} `;
    Object.keys(formData).forEach(key => {
      command += `${key}=${formData[key]} `;
    });
    try {
      await api.post('/chat/message', { message: command.trim() });
      setSuccess('Command sent to agent. Check chat for response.');
      setFormData({});
      setTimeout(fetchCredentials, 2000);
    } catch (err) {
      setError('Failed to send command');
    }
  };

  const handleTest = async (id) => {
    try {
      await api.post('/chat/message', { message: `test_cloud_credential id=${id}` });
      setSuccess('Test command sent.');
      setTimeout(fetchCredentials, 2000);
    } catch (err) {
      setError('Failed to send test command');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.post('/chat/message', { message: `delete_cloud_credential id=${id}` });
      setSuccess('Delete command sent.');
      setTimeout(fetchCredentials, 2000);
    } catch (err) {
      setError('Failed to send delete command');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">Cloud Credentials</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6">Add New Credential</Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Provider</InputLabel>
            <Select value={selectedProvider} onChange={handleProviderChange}>
              {providers.map(p => <MenuItem key={p} value={p}>{p.toUpperCase()}</MenuItem>)}
            </Select>
          </FormControl>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {fields[selectedProvider].map(field => (
              <Grid item xs={12} key={field}>
                <TextField
                  fullWidth
                  label={field.replace('_', ' ').toUpperCase()}
                  value={formData[field] || ''}
                  onChange={e => handleInputChange(field, e.target.value)}
                  type={field.includes('secret') || field.includes('key') ? 'password' : 'text'}
                  multiline={field === 'service_account_key'}
                  rows={field === 'service_account_key' ? 4 : 1}
                />
              </Grid>
            ))}
          </Grid>
          <Button variant="contained" startIcon={<Add />} onClick={handleAdd} sx={{ mt: 2 }}>
            Add via Agent
          </Button>
        </CardContent>
      </Card>
      <Typography variant="h6" sx={{ mt: 3 }}>Existing Credentials</Typography>
      <List>
        {credentials.map(cred => (
          <ListItem key={cred.id} secondaryAction={
            <>
              <IconButton onClick={() => handleTest(cred.id)}>
                <Check />
              </IconButton>
              <IconButton onClick={() => handleDelete(cred.id)}>
                <Delete />
              </IconButton>
            </>
          }>
            <ListItemText
              primary={`${cred.provider.toUpperCase()} - ${cred.region || cred.project_id || cred.subscription_id}`}
              secondary={`Last tested: ${cred.last_tested || 'Never'}`}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default CloudCredentials;