import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Pagination,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
  Link
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Info,
  Web,
  AccountCircle,
  Description,
  Timeline,
  ExpandMore,
  Link as LinkIcon,
  Image as ImageIcon,
  Article as ArticleIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

const TaskResults = () => {
  const [tasks, setTasks] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [scrapingResults, setScrapingResults] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch statistics
      const statsResponse = await fetch('http://localhost:8000/tasks/statistics', { headers });
      const statsData = await statsResponse.json();
      if (statsData.success) {
        setStatistics(statsData.statistics);
      }

      // Fetch task results
      const tasksResponse = await fetch(`http://localhost:8000/tasks/results?limit=20&offset=${(page - 1) * 20}`, { headers });
      const tasksData = await tasksResponse.json();
      if (tasksData.success) {
        setTasks(tasksData.results);
        setTotalPages(Math.ceil(tasksData.total / 20) || 1);
      }

      // Fetch scraping results
      const scrapingResponse = await fetch('http://localhost:8000/tasks/scraping?limit=10', { headers });
      const scrapingData = await scrapingResponse.json();
      if (scrapingData.success) {
        setScrapingResults(scrapingData.results);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch task data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page]);

  const handleTaskClick = async (taskId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      if (data.success) {
        setSelectedTask(data.task);
        setDialogOpen(true);
      }
    } catch (err) {
      setError('Failed to fetch task details: ' + err.message);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'error':
      case 'failed':
        return <Error color="error" />;
      default:
        return <Info color="info" />;
    }
  };

  const getTaskTypeIcon = (taskType) => {
    switch (taskType) {
      case 'web_scraping':
        return <Web />;
      case 'account_creation':
        return <AccountCircle />;
      default:
        return <Description />;
    }
  };

  const StatisticsCards = () => (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Tasks
            </Typography>
            <Typography variant="h4">
              {statistics.total_tasks || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Successful Tasks
            </Typography>
            <Typography variant="h4" color="success.main">
              {statistics.successful_tasks || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Success Rate
            </Typography>
            <Typography variant="h4">
              {Math.round(statistics.success_rate || 0)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Failed Tasks
            </Typography>
            <Typography variant="h4" color="error.main">
              {statistics.failed_tasks || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const TasksTable = ({ data, title }) => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Created</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((task) => (
            <TableRow key={task.task_id || task.id}>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getTaskTypeIcon(task.task_type)}
                  <Chip label={task.task_type} size="small" />
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getStatusIcon(task.status)}
                  <Chip 
                    label={task.status} 
                    size="small" 
                    color={task.status === 'success' ? 'success' : 'error'}
                  />
                </Box>
              </TableCell>
              <TableCell>
                {task.created_at ? format(new Date(task.created_at), 'MMM dd, yyyy HH:mm') : 'N/A'}
              </TableCell>
              <TableCell>
                <Button 
                  size="small" 
                  onClick={() => handleTaskClick(task.task_id || task.id)}
                >
                  View Details
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const TaskDetailDialog = () => (
    <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {selectedTask && getTaskTypeIcon(selectedTask.task_type)}
          Task Details
        </Box>
      </DialogTitle>
      <DialogContent>
        {selectedTask && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Task ID:</Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>{selectedTask.task_id}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Status:</Typography>
                <Chip 
                  label={selectedTask.status} 
                  color={selectedTask.status === 'success' ? 'success' : 'error'}
                  size="small"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2">Created:</Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {selectedTask.created_at ? format(new Date(selectedTask.created_at), 'MMM dd, yyyy HH:mm:ss') : 'N/A'}
                </Typography>
              </Grid>
              
              {selectedTask.scraping_details && (
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Scraping Details</Typography>
                  <Typography variant="subtitle2">URL:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.scraping_details.url}</Typography>
                  <Typography variant="subtitle2">Scrape Type:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.scraping_details.scrape_type}</Typography>
                  <Typography variant="subtitle2">Data Size:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.scraping_details.data_size} bytes</Typography>
                  {selectedTask.scraping_details.file_path && (
                    <>
                      <Typography variant="subtitle2">File Path:</Typography>
                      <Typography variant="body2">{selectedTask.scraping_details.file_path}</Typography>
                    </>
                  )}
                </Grid>
              )}
              
              {selectedTask.account_details && (
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Account Creation Details</Typography>
                  <Typography variant="subtitle2">Website:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.account_details.website}</Typography>
                  <Typography variant="subtitle2">Email:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.account_details.email}</Typography>
                  <Typography variant="subtitle2">Username:</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>{selectedTask.account_details.username}</Typography>
                </Grid>
              )}
              
              {selectedTask.result_data && Object.keys(selectedTask.result_data).length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Result Data</Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '200px' }}>
                      {JSON.stringify(selectedTask.result_data, null, 2)}
                    </pre>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setDialogOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Timeline />
        Task Results Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <StatisticsCards />
      
      <Card>
        <CardContent>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="All Tasks" />
            <Tab label="Scraping Results" />
          </Tabs>
          
          <Box sx={{ mt: 3 }}>
            {tabValue === 0 && (
              <>
                <TasksTable data={tasks} title="All Tasks" />
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination 
                    count={totalPages} 
                    page={page} 
                    onChange={(e, newPage) => setPage(newPage)}
                    color="primary"
                  />
                </Box>
              </>
            )}
            {tabValue === 1 && (
              <TasksTable data={scrapingResults} title="Scraping Results" />
            )}
          </Box>
        </CardContent>
      </Card>
      
      <TaskDetailDialog />
    </Box>
  );
};

export default TaskResults;