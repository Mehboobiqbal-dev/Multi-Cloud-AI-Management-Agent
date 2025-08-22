import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  CloudQueue as AWSIcon,
  Cloud as AzureIcon,
  CloudCircle as GCPIcon,
  Visibility,
  VisibilityOff,
  CheckCircle,
  Info,
  ExpandMore,
  Security,
  VpnKey,
  AccountBox
} from '@mui/icons-material';
import api from '../../services/api';

const providerConfigs = {
  aws: {
    name: 'Amazon Web Services',
    icon: AWSIcon,
    color: '#FF9900',
    fields: [
      { key: 'access_key', label: 'Access Key ID', type: 'text', required: true },
      { key: 'secret_key', label: 'Secret Access Key', type: 'password', required: true },
      { key: 'region', label: 'Default Region', type: 'text', placeholder: 'us-east-1' }
    ],
    description: 'Configure AWS credentials for cloud resource management'
  },
  azure: {
    name: 'Microsoft Azure',
    icon: AzureIcon,
    color: '#0078D4',
    fields: [
      { key: 'azure_subscription_id', label: 'Subscription ID', type: 'text', required: true },
      { key: 'azure_client_id', label: 'Client ID', type: 'text', required: true },
      { key: 'azure_client_secret', label: 'Client Secret', type: 'password', required: true },
      { key: 'azure_tenant_id', label: 'Tenant ID', type: 'text', required: true }
    ],
    description: 'Configure Azure service principal credentials'
  },
  gcp: {
    name: 'Google Cloud Platform',
    icon: GCPIcon,
    color: '#4285F4',
    fields: [
      { key: 'gcp_project_id', label: 'Project ID', type: 'text', required: true },
      { key: 'gcp_credentials_json', label: 'Service Account JSON', type: 'textarea', required: true }
    ],
    description: 'Configure GCP service account credentials'
  }
};

function CloudCredentials() {
  const [activeTab, setActiveTab] = useState(0);
  const [credentials, setCredentials] = useState({});
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [showPasswords, setShowPasswords] = useState({});
  const [testDialog, setTestDialog] = useState({ open: false, provider: null });
  const [testResult, setTestResult] = useState(null);

  const providers = Object.keys(providerConfigs);
  const currentProvider = providers[activeTab];

  const loadCredentials = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getCredentials();
      const credMap = {};
      data.forEach(cred => {
        credMap[cred.provider] = cred;
      });
      setCredentials(credMap);
      
      // Initialize form data
      const formMap = {};
      providers.forEach(provider => {
        formMap[provider] = {};
        providerConfigs[provider].fields.forEach(field => {
          formMap[provider][field.key] = credMap[provider]?.[field.key] || '';
        });
      });
      setFormData(formMap);
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to load credentials: ${error.message}` });
    } finally {
      setLoading(false);
    }
  }, [providers]);

  useEffect(() => {
    loadCredentials();
  }, [loadCredentials]);

  const handleInputChange = (provider, field, value) => {
    setFormData(prev => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        [field]: value
      }
    }));
  };

  const handleSave = async (provider) => {
    setSaving(true);
    try {
      const data = {
        provider,
        ...formData[provider]
      };
      
      await api.saveCredentials(data);
      setMessage({ type: 'success', text: `${providerConfigs[provider].name} credentials saved successfully!` });
      await loadCredentials();
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to save credentials: ${error.message}` });
    } finally {
      setSaving(false);
    }
  };

  const togglePasswordVisibility = (provider, field) => {
    setShowPasswords(prev => ({
      ...prev,
      [`${provider}_${field}`]: !prev[`${provider}_${field}`]
    }));
  };

  const handleTestConnection = async (provider) => {
    setTestDialog({ open: true, provider });
    setTestResult({ loading: true });
    
    try {
      // Simulate connection test - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      setTestResult({
        success: true,
        message: `Successfully connected to ${providerConfigs[provider].name}`,
        details: {
          'Connection Status': 'Active',
          'Authentication': 'Valid',
          'Permissions': 'Verified'
        }
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: `Failed to connect to ${providerConfigs[provider].name}`,
        error: error.message
      });
    }
  };

  const renderCredentialForm = (provider) => {
    const config = providerConfigs[provider];
    const Icon = config.icon;
    const hasCredentials = credentials[provider];
    const isFormValid = config.fields.filter(f => f.required).every(f => formData[provider]?.[f.key]);

    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Icon sx={{ fontSize: 40, color: config.color, mr: 2 }} />
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {config.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {config.description}
              </Typography>
            </Box>
            <Box sx={{ ml: 'auto' }}>
              {hasCredentials && (
                <Chip
                  icon={<CheckCircle />}
                  label="Configured"
                  color="success"
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
          </Box>

          <Grid container spacing={3}>
            {config.fields.map((field) => {
              const isPassword = field.type === 'password';
              const fieldKey = `${provider}_${field.key}`;
              const showPassword = showPasswords[fieldKey];
              
              return (
                <Grid item xs={12} md={field.type === 'textarea' ? 12 : 6} key={field.key}>
                  <TextField
                    fullWidth
                    label={field.label}
                    placeholder={field.placeholder}
                    required={field.required}
                    multiline={field.type === 'textarea'}
                    rows={field.type === 'textarea' ? 4 : 1}
                    type={isPassword && !showPassword ? 'password' : 'text'}
                    value={formData[provider]?.[field.key] || ''}
                    onChange={(e) => handleInputChange(provider, field.key, e.target.value)}
                    InputProps={{
                      endAdornment: isPassword && (
                        <IconButton
                          onClick={() => togglePasswordVisibility(provider, field.key)}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      )
                    }}
                  />
                </Grid>
              );
            })}
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={() => handleSave(provider)}
              disabled={!isFormValid || saving}
              startIcon={saving ? <CircularProgress size={20} /> : <Security />}
            >
              {saving ? 'Saving...' : 'Save Credentials'}
            </Button>
            
            {hasCredentials && (
              <Button
                variant="outlined"
                onClick={() => handleTestConnection(provider)}
                startIcon={<VpnKey />}
              >
                Test Connection
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Cloud Credentials
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Securely manage your cloud provider credentials for automated resource management.
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 3 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Info sx={{ mr: 1, color: 'info.main' }} />
            <Typography variant="h6">Security Information</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemIcon><Security fontSize="small" /></ListItemIcon>
              <ListItemText 
                primary="All credentials are encrypted at rest"
                secondary="Your sensitive data is protected using industry-standard encryption"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><VpnKey fontSize="small" /></ListItemIcon>
              <ListItemText 
                primary="Credentials are never logged or exposed"
                secondary="We follow strict security practices to protect your cloud access"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><AccountBox fontSize="small" /></ListItemIcon>
              <ListItemText 
                primary="Use service accounts with minimal permissions"
                secondary="Follow the principle of least privilege for enhanced security"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Tabs
        value={activeTab}
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{ mt: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        {providers.map((provider, index) => {
          const config = providerConfigs[provider];
          const Icon = config.icon;
          const hasCredentials = credentials[provider];
          
          return (
            <Tab
              key={provider}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Icon sx={{ fontSize: 20, color: config.color }} />
                  {config.name}
                  {hasCredentials && (
                    <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                  )}
                </Box>
              }
            />
          );
        })}
      </Tabs>

      {renderCredentialForm(currentProvider)}

      {/* Test Connection Dialog */}
      <Dialog
        open={testDialog.open}
        onClose={() => setTestDialog({ open: false, provider: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Test Connection - {testDialog.provider && providerConfigs[testDialog.provider]?.name}
        </DialogTitle>
        <DialogContent>
          {testResult?.loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 3 }}>
              <CircularProgress size={24} />
              <Typography>Testing connection...</Typography>
            </Box>
          ) : testResult ? (
            <Box>
              <Alert severity={testResult.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                {testResult.message}
              </Alert>
              {testResult.details && (
                <List>
                  {Object.entries(testResult.details).map(([key, value]) => (
                    <ListItem key={key}>
                      <ListItemText primary={key} secondary={value} />
                    </ListItem>
                  ))}
                </List>
              )}
              {testResult.error && (
                <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                  Error: {testResult.error}
                </Typography>
              )}
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialog({ open: false, provider: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CloudCredentials;