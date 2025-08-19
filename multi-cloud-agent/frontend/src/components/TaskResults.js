import React, { useState, useEffect, useCallback } from 'react';
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
  Article as ArticleIcon,
  Refresh,
  Chat,
  Download
} from '@mui/icons-material';
import { format } from 'date-fns';
import AIContentChat from './AIContentChat';
import DownloadManager from './DownloadManager';

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
  const [showAIChat, setShowAIChat] = useState(false);
  const [showDownloadManager, setShowDownloadManager] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch statistics
      const statsResponse = await fetch(`${process.env.REACT_APP_API_URL}/tasks/statistics`, { headers });
      const statsData = await statsResponse.json();
      if (statsData.success) {
        setStatistics(statsData.statistics);
      }

      // Fetch task results
      const tasksResponse = await fetch(`${process.env.REACT_APP_API_URL}/tasks/results?limit=20&offset=${(page - 1) * 20}`, { headers });
      const tasksData = await tasksResponse.json();
      if (tasksData.success) {
        setTasks(tasksData.results);
        setTotalPages(Math.ceil(tasksData.total / 20) || 1);
      }

      // Fetch scraping results
      const scrapingResponse = await fetch(`${process.env.REACT_APP_API_URL}/tasks/scraping?limit=10`, { headers });
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
  }, [page]);

  useEffect(() => {
    fetchData();
    
    // Set up interval for periodic refresh (optional)
    const intervalId = setInterval(fetchData, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(intervalId); // Clean up on unmount
  }, [fetchData]);

  const handleTaskClick = async (taskId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.REACT_APP_API_URL}/tasks/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      if (data.success) {
        setSelectedTask(data.task);
        setDialogOpen(true);
      } else {
        console.error('API returned success: false', data);
        setError('Failed to fetch task details: ' + (data.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error fetching task details:', err);
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

  const renderScrapedData = (data) => {
    if (!data || typeof data !== 'object') {
      return (
        <Typography variant="body2" color="text.secondary">
          No data available
        </Typography>
      );
    }

    const { text_content, links, images, metadata, ...otherData } = data;

    return (
      <Box>
        {/* Text Content Section */}
        {text_content && (
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ArticleIcon color="primary" />
                <Typography variant="h6">Text Content</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {text_content.title && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Title:</Typography>
                  <Typography variant="h6" sx={{ mb: 1 }}>{text_content.title}</Typography>
                </Box>
              )}
              {text_content.headings && text_content.headings.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Headings:</Typography>
                  <List dense>
                    {text_content.headings.slice(0, 10).map((heading, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <ListItemText 
                          primary={heading.text} 
                          secondary={`Level ${heading.level}`}
                        />
                      </ListItem>
                    ))}
                    {text_content.headings.length > 10 && (
                      <Typography variant="caption" color="text.secondary">
                        ... and {text_content.headings.length - 10} more headings
                      </Typography>
                    )}
                  </List>
                </Box>
              )}
              {text_content.paragraphs && text_content.paragraphs.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">Content Preview:</Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: '300px', overflow: 'auto' }}>
                    {text_content.paragraphs.slice(0, 5).map((paragraph, index) => (
                      <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                        {paragraph.length > 200 ? `${paragraph.substring(0, 200)}...` : paragraph}
                      </Typography>
                    ))}
                    {text_content.paragraphs.length > 5 && (
                      <Typography variant="caption" color="text.secondary">
                        ... and {text_content.paragraphs.length - 5} more paragraphs
                      </Typography>
                    )}
                  </Paper>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        )}

        {/* Links Section */}
        {links && links.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinkIcon color="primary" />
                <Typography variant="h6">Links ({links.length})</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {links.slice(0, 20).map((link, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemText
                      primary={
                        <Link 
                          href={link.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          sx={{ textDecoration: 'none' }}
                        >
                          {link.text || link.url}
                        </Link>
                      }
                      secondary={link.url !== link.text ? link.url : null}
                    />
                  </ListItem>
                ))}
                {links.length > 20 && (
                  <Typography variant="caption" color="text.secondary">
                    ... and {links.length - 20} more links
                  </Typography>
                )}
              </List>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Images Section */}
        {images && images.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ImageIcon color="primary" />
                <Typography variant="h6">Images ({images.length})</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {images.slice(0, 12).map((image, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card>
                      <CardContent sx={{ p: 2 }}>
                        {image.src && (
                          <Box sx={{ mb: 1 }}>
                            <img 
                              src={image.src} 
                              alt={image.alt || 'Scraped image'}
                              style={{ 
                                width: '100%', 
                                height: '120px', 
                                objectFit: 'cover',
                                borderRadius: '4px'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          </Box>
                        )}
                        {image.alt && (
                          <Typography variant="caption" display="block">
                            {image.alt}
                          </Typography>
                        )}
                        {image.src && (
                          <Link 
                            href={image.src} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            variant="caption"
                            sx={{ display: 'block', mt: 0.5 }}
                          >
                            View Original
                          </Link>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
                {images.length > 12 && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      ... and {images.length - 12} more images
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Metadata Section */}
        {metadata && Object.keys(metadata).length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Info color="primary" />
                <Typography variant="h6">Metadata</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {Object.entries(metadata).map(([key, value]) => (
                  <Grid item xs={12} sm={6} key={key}>
                    <Typography variant="subtitle2" color="primary">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                    </Typography>
                    <Typography variant="body2">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                    </Typography>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Other Data Section */}
        {Object.keys(otherData).length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Description color="primary" />
                <Typography variant="h6">Additional Data</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '300px' }}>
                  {JSON.stringify(otherData, null, 2)}
                </pre>
              </Paper>
            </AccordionDetails>
          </Accordion>
        )}
      </Box>
    );
  };

  const StatisticsCards = () => (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Description sx={{ fontSize: 40, mb: 1, opacity: 0.8 }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {statistics.total_tasks || 0}
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Total Tasks
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          color: 'white',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <CheckCircle sx={{ fontSize: 40, mb: 1, opacity: 0.8 }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {statistics.successful_tasks || 0}
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Successful Tasks
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          color: 'white',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Timeline sx={{ fontSize: 40, mb: 1, opacity: 0.8 }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {Math.round(statistics.success_rate || 0)}%
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Success Rate
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
          color: 'white',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Error sx={{ fontSize: 40, mb: 1, opacity: 0.8 }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {statistics.failed_tasks || 0}
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Failed Tasks
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
          color: 'text.primary',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Web sx={{ fontSize: 40, mb: 1, opacity: 0.7, color: 'primary.main' }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {statistics.total_scraped_pages || 0}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Pages Scraped
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} lg={3}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
          color: 'text.primary',
          boxShadow: 3
        }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <AccountCircle sx={{ fontSize: 40, mb: 1, opacity: 0.7, color: 'secondary.main' }} />
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              {statistics.total_accounts_created || 0}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Accounts Created
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
            <TableCell>URL/Description</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Data Size</TableCell>
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
              <TableCell sx={{ maxWidth: '300px' }}>
                {task.url ? (
                  <Link 
                    href={task.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    sx={{ 
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {task.url}
                  </Link>
                ) : (
                  <Typography variant="body2" sx={{ 
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {task.task_description || 'No description'}
                  </Typography>
                )}
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
                {task.data_size ? (
                  <Typography variant="body2">
                    {(task.data_size / 1024).toFixed(1)} KB
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    N/A
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {task.created_at ? format(new Date(task.created_at), 'MMM dd, yyyy HH:mm') : 'N/A'}
              </TableCell>
              <TableCell>
                <Button 
                  size="small" 
                  onClick={() => handleTaskClick(task.task_id || task.id)}
                  variant="outlined"
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

  const handleAgentAction = async (action) => {
  if (!selectedTask) return;
  try {
    const token = localStorage.getItem('access_token');
    const message = `${action} task ${selectedTask.task_id}`;
    await fetch(`${process.env.REACT_APP_API_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    console.log(`Agent ${action} requested`);
    if (action === 'download') {
      // Handle download response if needed
    }
    fetchData(); // Refresh tasks after action
  } catch (err) {
    console.error(`Failed to request agent ${action}:`, err);
    setError(`Failed to request agent ${action}`);
  }
};
const handleAgentAssist = () => handleAgentAction('assist with');
const handleDownload = () => handleAgentAction('download');
const handleDelete = () => handleAgentAction('delete');
const handleRetry = () => handleAgentAction('retry');

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
                  {selectedTask.scraping_details.full_scraped_content && (
                    <>
                      <Typography variant="subtitle2">Full Scraped Content:</Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(JSON.parse(selectedTask.scraping_details.full_scraped_content), null, 2)}
                      </Typography>
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
                  <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Scraped Content</Typography>
                  {selectedTask.scraping_details.full_scraped_content ? renderScrapedData(JSON.parse(selectedTask.scraping_details.full_scraped_content)) : <Typography variant="body2" color="text.secondary">No detailed scraped content available.</Typography>}
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button
          startIcon={<Chat />}
          onClick={() => setShowAIChat(true)}
          variant="outlined"
          color="primary"
        >
          AI Chat
        </Button>
        <Button
          startIcon={<Chat />}
          onClick={handleAgentAssist}
          variant="outlined"
          color="primary"
        >
          Ask Agent
        </Button>
        <Button
          startIcon={<Download />}
          onClick={handleDownload}
          variant="outlined"
          color="secondary"
        >
          Download via Agent
        </Button>
        <Button
          onClick={handleDelete}
          variant="outlined"
          color="error"
        >
          Delete via Agent
        </Button>
        <Button
          onClick={handleRetry}
          variant="outlined"
          color="primary"
        >
          Retry via Agent
        </Button>
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
    <Box sx={{ 
      height: '100vh',
      overflow: 'auto',
      bgcolor: 'background.default'
    }}>
      {/* Header Section */}
      <Box sx={{ 
        p: 3, 
        pb: 2,
        borderBottom: 1, 
        borderColor: 'divider',
        bgcolor: 'background.paper',
        position: 'sticky',
        top: 0,
        zIndex: 1
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1,
              fontWeight: 600,
              color: 'text.primary'
            }}>
              <Timeline color="primary" />
              Task Results
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              View and manage your task execution history
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Content Section */}
      <Box sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        <StatisticsCards />
        
        {/* Main Content Card */}
        <Card sx={{ 
          boxShadow: 2,
          borderRadius: 2,
          overflow: 'hidden'
        }}>
          <Box sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            bgcolor: 'grey.50'
          }}>
            <Tabs 
              value={tabValue} 
              onChange={(e, newValue) => setTabValue(newValue)}
              sx={{ 
                px: 3,
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 500,
                  fontSize: '0.95rem'
                }
              }}
            >
              <Tab 
                label={`All Tasks (${tasks.length})`} 
                icon={<Description />}
                iconPosition="start"
              />
              <Tab 
                label={`Scraping Results (${scrapingResults.length})`} 
                icon={<Web />}
                iconPosition="start"
              />
            </Tabs>
          </Box>
          
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ minHeight: '400px' }}>
              {tabValue === 0 && (
                <Box>
                  <TasksTable data={tasks} title="All Tasks" />
                  {totalPages > 1 && (
                    <Box sx={{ 
                      display: 'flex', 
                      justifyContent: 'center', 
                      p: 3,
                      borderTop: 1,
                      borderColor: 'divider',
                      bgcolor: 'grey.50'
                    }}>
                      <Pagination 
                        count={totalPages} 
                        page={page} 
                        onChange={(e, newPage) => setPage(newPage)}
                        color="primary"
                        size="large"
                      />
                    </Box>
                  )}
                </Box>
              )}
              {tabValue === 1 && (
                <TasksTable data={scrapingResults} title="Scraping Results" />
              )}
            </Box>
          </CardContent>
        </Card>
      </Box>
      
      <TaskDetailDialog />
      
      {/* AI Content Chat Modal */}
      {showAIChat && selectedTask && (
        <AIContentChat
          open={showAIChat}
          onClose={() => setShowAIChat(false)}
          taskData={selectedTask}
        />
      )}
      
      {/* Download Manager Modal */}
      {showDownloadManager && selectedTask && (
        <DownloadManager
          open={showDownloadManager}
          onClose={() => setShowDownloadManager(false)}
          taskData={selectedTask}
        />
      )}
    </Box>
  );
};

export default TaskResults;