import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
  CircularProgress
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
// Note: You may need to install date-fns: npm install date-fns
// For now, we'll use a simple date formatter
const format = (date, formatStr) => {
  if (!date) return 'Unknown';
  const d = new Date(date);
  if (formatStr === 'MMM dd, yyyy HH:mm') {
    return d.toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  if (formatStr === 'MMM dd, HH:mm') {
    return d.toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  return d.toLocaleString();
};

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`task-results-tabpanel-${index}`}
      aria-labelledby={`task-results-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const TaskResultsDialog = ({ open, onClose, onRefresh }) => {
  const [taskResults, setTaskResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    if (open) {
      fetchTaskResults();
      fetchStatistics();
    }
  }, [open]);

  const fetchTaskResults = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/tasks/results', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTaskResults(data.results || []);
      } else {
        console.error('Failed to fetch task results');
      }
    } catch (error) {
      console.error('Error fetching task results:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/tasks/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'failed':
      case 'error':
        return <ErrorIcon color="error" />;
      case 'running':
      case 'in_progress':
        return <TimelineIcon color="primary" />;
      case 'paused':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'success';
      case 'failed':
      case 'error':
        return 'error';
      case 'running':
      case 'in_progress':
        return 'primary';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.round((end - start) / 1000); // seconds
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.round(duration / 60)}m`;
    return `${Math.round(duration / 3600)}h`;
  };

  const downloadResults = (taskId, format = 'json') => {
    const token = localStorage.getItem('token');
    const url = `/api/tasks/${taskId}/download?format=${format}`;
    
    // Create a temporary link to download the file
    const link = document.createElement('a');
    link.href = url;
    link.download = `task-${taskId}-results.${format}`;
    link.style.display = 'none';
    
    // Add authorization header by creating a fetch request
    fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => response.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    })
    .catch(error => {
      console.error('Error downloading results:', error);
    });
  };

  const renderOverview = () => (
    <Box>
      {statistics && (
        <Card sx={{ mb: 3 }}>
          <CardHeader
            avatar={<AssessmentIcon color="primary" />}
            title="Task Statistics"
            subheader="Overview of all your tasks"
          />
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip 
                label={`Total: ${statistics.total || 0}`} 
                color="default" 
                variant="outlined"
              />
              <Chip 
                label={`Completed: ${statistics.completed || 0}`} 
                color="success" 
                variant="outlined"
              />
              <Chip 
                label={`Failed: ${statistics.failed || 0}`} 
                color="error" 
                variant="outlined"
              />
              <Chip 
                label={`Running: ${statistics.running || 0}`} 
                color="primary" 
                variant="outlined"
              />
            </Box>
            
            {statistics.success_rate !== undefined && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Success Rate: {(statistics.success_rate * 100).toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={statistics.success_rate * 100}
                  color="success"
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      <Typography variant="h6" gutterBottom>
        Recent Tasks
      </Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : taskResults.length === 0 ? (
        <Alert severity="info">
          No task results found. Complete some tasks to see results here.
        </Alert>
      ) : (
        <List>
          {taskResults.slice(0, 5).map((task, index) => (
            <React.Fragment key={task.id || index}>
              <ListItem
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1
                }}
              >
                <ListItemIcon>
                  {getStatusIcon(task.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2">
                        {task.goal || task.description || 'Unnamed Task'}
                      </Typography>
                      <Chip 
                        label={task.status || 'Unknown'} 
                        size="small" 
                        color={getStatusColor(task.status)}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Started: {task.created_at ? format(new Date(task.created_at), 'MMM dd, yyyy HH:mm') : 'Unknown'}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Duration: {formatDuration(task.created_at, task.updated_at)}
                      </Typography>
                      {task.result && (
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          Result: {typeof task.result === 'string' ? task.result.substring(0, 100) + '...' : 'Complex result'}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Download Results">
                    <IconButton 
                      size="small" 
                      onClick={() => downloadResults(task.id)}
                    >
                      <DownloadIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );

  const renderDetailedResults = () => (
    <Box>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : taskResults.length === 0 ? (
        <Alert severity="info">
          No detailed results available.
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Task</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Started</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Steps</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {taskResults.map((task, index) => (
                <TableRow key={task.id || index}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {task.goal || task.description || 'Unnamed Task'}
                    </Typography>
                    {task.result && (
                      <Typography variant="caption" color="text.secondary">
                        {typeof task.result === 'string' ? task.result.substring(0, 50) + '...' : 'Complex result'}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={task.status || 'Unknown'} 
                      size="small" 
                      color={getStatusColor(task.status)}
                      icon={getStatusIcon(task.status)}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {task.created_at ? format(new Date(task.created_at), 'MMM dd, HH:mm') : 'Unknown'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDuration(task.created_at, task.updated_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {task.steps_completed || 0} / {task.total_steps || 0}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="Download JSON">
                        <IconButton 
                          size="small" 
                          onClick={() => downloadResults(task.id, 'json')}
                        >
                          <DownloadIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6">Task Results</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh">
              <IconButton onClick={() => { fetchTaskResults(); fetchStatistics(); }}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={selectedTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Detailed Results" />
        </Tabs>
      </Box>
      
      <DialogContent sx={{ p: 0 }}>
        <TabPanel value={selectedTab} index={0}>
          {renderOverview()}
        </TabPanel>
        <TabPanel value={selectedTab} index={1}>
          {renderDetailedResults()}
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button 
          variant="contained" 
          onClick={() => { fetchTaskResults(); fetchStatistics(); }}
          startIcon={<RefreshIcon />}
        >
          Refresh
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TaskResultsDialog;