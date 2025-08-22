import React, { useState, useEffect } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton
} from '@mui/material';
import {
  Work as WorkIcon,
  Business as LinkedInIcon,
  PlayArrow as PlayIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  CheckCircle,
  Error,
  ViewList as BatchIcon
} from '@mui/icons-material';
import api from '../../services/api';

const jobPlatforms = {
  upwork: {
    name: 'Upwork',
    icon: WorkIcon,
    color: '#14A800',
    fields: [
      { key: 'browser_id', label: 'Browser Session ID', type: 'text', required: true },
      { key: 'job_url', label: 'Job URL', type: 'url', required: true },
      { key: 'cover_letter', label: 'Cover Letter', type: 'textarea', required: true },
      { key: 'hourly_rate', label: 'Hourly Rate ($)', type: 'number' },
      { key: 'proposal_duration', label: 'Project Duration', type: 'text' }
    ]
  },
  fiverr: {
    name: 'Fiverr',
    icon: WorkIcon,
    color: '#1DBF73',
    fields: [
      { key: 'browser_id', label: 'Browser Session ID', type: 'text', required: true },
      { key: 'gig_url', label: 'Gig URL', type: 'url', required: true },
      { key: 'message', label: 'Custom Message', type: 'textarea', required: true },
      { key: 'package_type', label: 'Package Type', type: 'select', options: ['basic', 'standard', 'premium'], default: 'basic' }
    ]
  },
  linkedin: {
    name: 'LinkedIn',
    icon: LinkedInIcon,
    color: '#0A66C2',
    fields: [
      { key: 'browser_id', label: 'Browser Session ID', type: 'text', required: true },
      { key: 'job_url', label: 'Job URL', type: 'url', required: true },
      { key: 'cover_letter', label: 'Cover Letter', type: 'textarea', required: true },
      { key: 'resume_path', label: 'Resume File Path', type: 'text' }
    ]
  }
};

function FormAutomation() {
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({});
  const [templates, setTemplates] = useState([]);
  const [executing, setExecuting] = useState(false);
  const [message, setMessage] = useState(null);
  const [batchDialog, setBatchDialog] = useState(false);
  const [batchJobs, setBatchJobs] = useState([]);
  const [templateDialog, setTemplateDialog] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [executionHistory, setExecutionHistory] = useState([]);

  const tabs = [
    { id: 'single', label: 'Single Application', icon: PlayIcon },
    { id: 'batch', label: 'Batch Applications', icon: BatchIcon },
    { id: 'templates', label: 'Templates', icon: SaveIcon },
    { id: 'history', label: 'History', icon: CheckCircle }
  ];

  const platforms = Object.keys(jobPlatforms);


  useEffect(() => {
    loadTemplates();
    loadExecutionHistory();
  }, []);

  const loadTemplates = () => {
    // Mock templates - replace with API call
    setTemplates([
      {
        id: 1,
        name: 'Frontend Developer Template',
        platform: 'upwork',
        data: {
          cover_letter: 'I am an experienced frontend developer with expertise in React, Vue, and Angular...',
          hourly_rate: 45,
          proposal_duration: '2-4 weeks'
        }
      },
      {
        id: 2,
        name: 'Full Stack Template',
        platform: 'linkedin',
        data: {
          cover_letter: 'As a full-stack developer with 5+ years of experience...',
          resume_path: '/path/to/resume.pdf'
        }
      }
    ]);
  };

  const loadExecutionHistory = () => {
    // Mock history - replace with API call
    setExecutionHistory([
      {
        id: 1,
        platform: 'upwork',
        job_title: 'React Developer Needed',
        status: 'success',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        details: 'Application submitted successfully'
      },
      {
        id: 2,
        platform: 'linkedin',
        job_title: 'Senior Frontend Engineer',
        status: 'error',
        timestamp: new Date(Date.now() - 172800000).toISOString(),
        details: 'Failed to upload resume'
      }
    ]);
  };

  const handleInputChange = (platform, field, value) => {
    setFormData(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform],
        [field]: value
      }
    }));
  };

  const handleSingleApplication = async (platform) => {
    setExecuting(true);
    try {
      const data = formData[platform] || {};
      
      switch (platform) {
        case 'upwork':
          await api.applyJobUpwork(data);
          break;
        case 'fiverr':
          await api.applyJobFiverr(data);
          break;
        case 'linkedin':
          await api.applyJobLinkedin(data);
          break;
        default:
          throw new Error('Unsupported platform');
      }
      
      setMessage({ type: 'success', text: `Application submitted successfully to ${jobPlatforms[platform].name}!` });
      loadExecutionHistory();
    } catch (error) {
      setMessage({ type: 'error', text: `Application failed: ${error.message}` });
    } finally {
      setExecuting(false);
    }
  };

  const handleBatchApplication = async () => {
    setExecuting(true);
    try {
      const response = await api.batchApplyJobs({ jobs: batchJobs });
      setMessage({ type: 'success', text: `Batch application completed! ${response.successful || 0} successful, ${response.failed || 0} failed.` });
      setBatchDialog(false);
      loadExecutionHistory();
    } catch (error) {
      setMessage({ type: 'error', text: `Batch application failed: ${error.message}` });
    } finally {
      setExecuting(false);
    }
  };

  const addBatchJob = () => {
    setBatchJobs(prev => [...prev, {
      id: Date.now(),
      platform: 'upwork',
      job_url: '',
      cover_letter: '',
      template_id: null
    }]);
  };

  const removeBatchJob = (id) => {
    setBatchJobs(prev => prev.filter(job => job.id !== id));
  };

  const updateBatchJob = (id, field, value) => {
    setBatchJobs(prev => prev.map(job => 
      job.id === id ? { ...job, [field]: value } : job
    ));
  };

  const applyTemplate = (template, platform) => {
    setFormData(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform],
        ...template.data
      }
    }));
    setMessage({ type: 'info', text: `Template "${template.name}" applied to ${jobPlatforms[platform].name} form.` });
  };

  const saveAsTemplate = (platform) => {
    const data = formData[platform];
    if (!data || Object.keys(data).length === 0) {
      setMessage({ type: 'warning', text: 'No data to save as template.' });
      return;
    }
    
    setCurrentTemplate({
      platform,
      data,
      name: ''
    });
    setTemplateDialog(true);
  };

  const saveTemplate = () => {
    if (!currentTemplate.name) {
      setMessage({ type: 'warning', text: 'Please enter a template name.' });
      return;
    }
    
    const newTemplate = {
      id: Date.now(),
      name: currentTemplate.name,
      platform: currentTemplate.platform,
      data: currentTemplate.data
    };
    
    setTemplates(prev => [...prev, newTemplate]);
    setTemplateDialog(false);
    setCurrentTemplate(null);
    setMessage({ type: 'success', text: 'Template saved successfully!' });
  };

  const renderFormFields = (platform) => {
    const config = jobPlatforms[platform];
    const data = formData[platform] || {};
    
    return (
      <Grid container spacing={3}>
        {config.fields.map((field) => {
          const value = data[field.key] || field.default || '';
          
          if (field.type === 'select') {
            return (
              <Grid item xs={12} md={6} key={field.key}>
                <FormControl fullWidth required={field.required}>
                  <InputLabel>{field.label}</InputLabel>
                  <Select
                    value={value}
                    label={field.label}
                    onChange={(e) => handleInputChange(platform, field.key, e.target.value)}
                  >
                    {field.options.map(option => (
                      <MenuItem key={option} value={option}>
                        {option.charAt(0).toUpperCase() + option.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            );
          }
          
          return (
            <Grid item xs={12} md={field.type === 'textarea' ? 12 : 6} key={field.key}>
              <TextField
                fullWidth
                label={field.label}
                required={field.required}
                multiline={field.type === 'textarea'}
                rows={field.type === 'textarea' ? 4 : 1}
                type={field.type === 'number' ? 'number' : 'text'}
                value={value}
                onChange={(e) => handleInputChange(platform, field.key, e.target.value)}
              />
            </Grid>
          );
        })}
      </Grid>
    );
  };

  const renderSingleApplication = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
        Single Job Application
      </Typography>
      
      <Grid container spacing={3}>
        {platforms.map((platform) => {
          const config = jobPlatforms[platform];
          const Icon = config.icon;
          
          return (
            <Grid item xs={12} key={platform}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Icon sx={{ fontSize: 32, color: config.color, mr: 2 }} />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {config.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Apply to jobs on {config.name} automatically
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        onClick={() => saveAsTemplate(platform)}
                        startIcon={<SaveIcon />}
                      >
                        Save Template
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => handleSingleApplication(platform)}
                        disabled={executing}
                        startIcon={executing ? <CircularProgress size={20} /> : <PlayIcon />}
                        sx={{ backgroundColor: config.color }}
                      >
                        {executing ? 'Applying...' : 'Apply Now'}
                      </Button>
                    </Box>
                  </Box>
                  
                  {renderFormFields(platform)}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );

  const renderBatchApplication = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Batch Job Applications
        </Typography>
        <Button
          variant="contained"
          onClick={() => setBatchDialog(true)}
          startIcon={<BatchIcon />}
        >
          Configure Batch
        </Button>
      </Box>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        Batch applications allow you to apply to multiple jobs simultaneously. Configure your job list and templates for efficient automation.
      </Alert>
      
      {batchJobs.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
              Queued Applications ({batchJobs.length})
            </Typography>
            <List>
              {batchJobs.map((job, index) => (
                <ListItem key={job.id}>
                  <ListItemIcon>
                    <Chip label={job.platform} size="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={job.job_url || 'No URL specified'}
                    secondary={`Template: ${job.template_id ? 'Applied' : 'None'}`}
                  />
                  <IconButton onClick={() => removeBatchJob(job.id)}>
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
            <Button
              variant="contained"
              onClick={handleBatchApplication}
              disabled={executing || batchJobs.length === 0}
              startIcon={executing ? <CircularProgress size={20} /> : <PlayIcon />}
              sx={{ mt: 2 }}
            >
              {executing ? 'Processing...' : `Apply to ${batchJobs.length} Jobs`}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderTemplates = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
        Application Templates
      </Typography>
      
      <Grid container spacing={3}>
        {templates.map((template) => {
          const config = jobPlatforms[template.platform];
          const Icon = config.icon;
          
          return (
            <Grid item xs={12} md={6} key={template.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Icon sx={{ fontSize: 24, color: config.color, mr: 2 }} />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {template.name}
                      </Typography>
                      <Chip 
                        label={config.name} 
                        size="small" 
                        sx={{ backgroundColor: config.color + '20', color: config.color }}
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {Object.keys(template.data).length} fields configured
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      onClick={() => applyTemplate(template, template.platform)}
                      startIcon={<PlayIcon />}
                    >
                      Apply
                    </Button>
                    <Button size="small" startIcon={<EditIcon />}>
                      Edit
                    </Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />}>
                      Delete
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
      
      {templates.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <SaveIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No templates saved
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create templates from the application forms to reuse them later
          </Typography>
        </Box>
      )}
    </Box>
  );

  const renderHistory = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
        Execution History
      </Typography>
      
      <List>
        {executionHistory.map((item) => {
          const config = jobPlatforms[item.platform];
          const Icon = config.icon;
          const StatusIcon = item.status === 'success' ? CheckCircle : Error;
          
          return (
            <ListItem key={item.id} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
              <ListItemIcon>
                <Icon sx={{ color: config.color }} />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1">{item.job_title}</Typography>
                    <StatusIcon 
                      sx={{ 
                        fontSize: 16, 
                        color: item.status === 'success' ? 'success.main' : 'error.main' 
                      }} 
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {config.name} • {new Date(item.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.details}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          );
        })}
      </List>
      
      {executionHistory.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <CheckCircle sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No execution history
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your application history will appear here after you start applying to jobs
          </Typography>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Form Automation
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Automate job applications and form submissions across multiple platforms.
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

      <Tabs
        value={activeTab}
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
      >
        {tabs.map((tab, index) => {
          const Icon = tab.icon;
          return (
            <Tab
              key={tab.id}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Icon sx={{ fontSize: 20 }} />
                  {tab.label}
                </Box>
              }
            />
          );
        })}
      </Tabs>

      {activeTab === 0 && renderSingleApplication()}
      {activeTab === 1 && renderBatchApplication()}
      {activeTab === 2 && renderTemplates()}
      {activeTab === 3 && renderHistory()}

      {/* Batch Configuration Dialog */}
      <Dialog open={batchDialog} onClose={() => setBatchDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Configure Batch Applications</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Button onClick={addBatchJob} startIcon={<AddIcon />}>
              Add Job
            </Button>
          </Box>
          
          {batchJobs.map((job, index) => (
            <Card key={job.id} sx={{ mb: 2 }}>
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Platform</InputLabel>
                      <Select
                        value={job.platform}
                        label="Platform"
                        onChange={(e) => updateBatchJob(job.id, 'platform', e.target.value)}
                      >
                        {platforms.map(platform => (
                          <MenuItem key={platform} value={platform}>
                            {jobPlatforms[platform].name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Job URL"
                      value={job.job_url}
                      onChange={(e) => updateBatchJob(job.id, 'job_url', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <IconButton onClick={() => removeBatchJob(job.id)} color="error">
                      <DeleteIcon />
                    </IconButton>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setBatchDialog(false)}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Template Save Dialog */}
      <Dialog open={templateDialog} onClose={() => setTemplateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save as Template</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Template Name"
            value={currentTemplate?.name || ''}
            onChange={(e) => setCurrentTemplate(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplateDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={saveTemplate}>Save Template</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default FormAutomation;