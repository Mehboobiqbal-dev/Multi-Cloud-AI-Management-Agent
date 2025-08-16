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
  ListItemText,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Construction as BuildIcon,
  Search as SearchIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Code as CodeIcon,
  Description as DescIcon,
  Settings as SettingsIcon,
  ExpandMore,
  CheckCircle,
  Error,
  Warning,
  Info,
  CloudQueue,
  Web,
  Storage,
  Security,
  AutoMode,
  Psychology,
  Memory,
  Analytics
} from '@mui/icons-material';
import api from '../../services/api';

// Mock tool registry - replace with actual API call
const mockTools = {
  // Cloud Tools
  'aws_list_instances': {
    name: 'List AWS Instances',
    description: 'List all EC2 instances in your AWS account',
    category: 'cloud',
    parameters: {
      region: { type: 'string', description: 'AWS region', default: 'us-east-1' },
      state: { type: 'string', description: 'Instance state filter', enum: ['running', 'stopped', 'all'], default: 'all' }
    },
    icon: 'CloudQueue'
  },
  'azure_list_vms': {
    name: 'List Azure VMs',
    description: 'List all virtual machines in your Azure subscription',
    category: 'cloud',
    parameters: {
      resource_group: { type: 'string', description: 'Resource group name' },
      subscription_id: { type: 'string', description: 'Azure subscription ID' }
    },
    icon: 'CloudQueue'
  },
  // Web Tools
  'open_browser': {
    name: 'Open Browser',
    description: 'Open a new browser session for web automation',
    category: 'web',
    parameters: {
      headless: { type: 'boolean', description: 'Run browser in headless mode', default: true },
      user_agent: { type: 'string', description: 'Custom user agent string' }
    },
    icon: 'Web'
  },
  'get_page_content': {
    name: 'Get Page Content',
    description: 'Extract content from a web page',
    category: 'web',
    parameters: {
      browser_id: { type: 'string', description: 'Browser session ID', required: true },
      url: { type: 'string', description: 'URL to visit', required: true },
      selector: { type: 'string', description: 'CSS selector for specific content' }
    },
    icon: 'Web'
  },
  'fill_form': {
    name: 'Fill Form',
    description: 'Fill out form fields on a web page',
    category: 'automation',
    parameters: {
      browser_id: { type: 'string', description: 'Browser session ID', required: true },
      form_data: { type: 'object', description: 'Form field data as key-value pairs', required: true }
    },
    icon: 'AutoMode'
  },
  // Data Tools
  'search_web': {
    name: 'Web Search',
    description: 'Search the web using various search engines',
    category: 'data',
    parameters: {
      query: { type: 'string', description: 'Search query', required: true },
      engine: { type: 'string', description: 'Search engine', enum: ['google', 'bing', 'duckduckgo'], default: 'google' },
      num_results: { type: 'number', description: 'Number of results', default: 10 }
    },
    icon: 'Search'
  },
  'analyze_sentiment': {
    name: 'Analyze Sentiment',
    description: 'Analyze the sentiment of text content',
    category: 'ai',
    parameters: {
      text: { type: 'string', description: 'Text to analyze', required: true },
      model: { type: 'string', description: 'AI model to use', enum: ['basic', 'advanced'], default: 'basic' }
    },
    icon: 'Psychology'
  }
};

const categoryIcons = {
  cloud: CloudQueue,
  web: Web,
  automation: AutoMode,
  data: Storage,
  security: Security,
  ai: Psychology,
  memory: Memory,
  analytics: Analytics
};

const categoryColors = {
  cloud: '#FF9900',
  web: '#4285F4',
  automation: '#34A853',
  data: '#9C27B0',
  security: '#F44336',
  ai: '#FF5722',
  memory: '#607D8B',
  analytics: '#795548'
};

function ToolManager() {
  const [tools, setTools] = useState(mockTools);
  const [filteredTools, setFilteredTools] = useState(mockTools);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState(null);
  const [toolDialog, setToolDialog] = useState(false);
  const [parameters, setParameters] = useState({});
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [message, setMessage] = useState(null);

  const categories = ['all', ...new Set(Object.values(tools).map(tool => tool.category))];

  useEffect(() => {
    filterTools();
  }, [searchQuery, selectedCategory, tools]);

  const filterTools = () => {
    let filtered = Object.entries(tools);
    
    if (searchQuery) {
      filtered = filtered.filter(([key, tool]) => 
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(([key, tool]) => tool.category === selectedCategory);
    }
    
    setFilteredTools(Object.fromEntries(filtered));
  };

  const handleToolSelect = (toolKey) => {
    const tool = tools[toolKey];
    setSelectedTool({ key: toolKey, ...tool });
    
    // Initialize parameters with defaults
    const initialParams = {};
    Object.entries(tool.parameters || {}).forEach(([key, param]) => {
      initialParams[key] = param.default || '';
    });
    setParameters(initialParams);
    setExecutionResult(null);
    setToolDialog(true);
  };

  const handleParameterChange = (paramKey, value) => {
    setParameters(prev => ({
      ...prev,
      [paramKey]: value
    }));
  };

  const handleExecuteTool = async () => {
    if (!selectedTool) return;
    
    setExecuting(true);
    setExecutionResult(null);
    
    try {
      const result = await api.callTool(selectedTool.key, parameters);
      setExecutionResult({
        success: true,
        data: result,
        timestamp: new Date().toISOString()
      });
      setMessage({ type: 'success', text: `Tool "${selectedTool.name}" executed successfully!` });
    } catch (error) {
      setExecutionResult({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      setMessage({ type: 'error', text: `Tool execution failed: ${error.message}` });
    } finally {
      setExecuting(false);
    }
  };

  const renderParameterInput = (paramKey, param) => {
    const value = parameters[paramKey] || '';
    
    if (param.type === 'boolean') {
      return (
        <FormControlLabel
          control={
            <Switch
              checked={value}
              onChange={(e) => handleParameterChange(paramKey, e.target.checked)}
            />
          }
          label={param.description}
        />
      );
    }
    
    if (param.enum) {
      return (
        <FormControl fullWidth>
          <InputLabel>{paramKey}</InputLabel>
          <Select
            value={value}
            label={paramKey}
            onChange={(e) => handleParameterChange(paramKey, e.target.value)}
          >
            {param.enum.map(option => (
              <MenuItem key={option} value={option}>{option}</MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }
    
    return (
      <TextField
        fullWidth
        label={paramKey}
        value={value}
        onChange={(e) => handleParameterChange(paramKey, e.target.value)}
        type={param.type === 'number' ? 'number' : 'text'}
        multiline={param.type === 'object'}
        rows={param.type === 'object' ? 3 : 1}
        required={param.required}
        helperText={param.description}
        placeholder={param.default ? `Default: ${param.default}` : ''}
      />
    );
  };

  const renderToolCard = (toolKey, tool) => {
    const CategoryIcon = categoryIcons[tool.category] || BuildIcon;
    const categoryColor = categoryColors[tool.category] || '#666';
    
    return (
      <Grid item xs={12} sm={6} md={4} key={toolKey}>
        <Card 
          sx={{ 
            height: '100%',
            cursor: 'pointer',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4
            }
          }}
          onClick={() => handleToolSelect(toolKey)}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CategoryIcon sx={{ fontSize: 32, color: categoryColor, mr: 2 }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                  {tool.name}
                </Typography>
                <Chip 
                  label={tool.category} 
                  size="small" 
                  sx={{ 
                    backgroundColor: categoryColor + '20',
                    color: categoryColor,
                    fontWeight: 500
                  }}
                />
              </Box>
            </Box>
            
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                mb: 2,
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}
            >
              {tool.description}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                {Object.keys(tool.parameters || {}).length} parameters
              </Typography>
              <Button size="small" startIcon={<PlayIcon />}>
                Execute
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Tool Manager
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Browse and execute tools directly. Each tool provides specific functionality for automation and data processing.
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

      {/* Search and Filter Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                label="Category"
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {categories.map(category => (
                  <MenuItem key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
              {Object.keys(filteredTools).length} tools
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Tools Grid */}
      <Grid container spacing={3}>
        {Object.entries(filteredTools).map(([toolKey, tool]) => 
          renderToolCard(toolKey, tool)
        )}
      </Grid>

      {Object.keys(filteredTools).length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <BuildIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No tools found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search or filter criteria
          </Typography>
        </Box>
      )}

      {/* Tool Execution Dialog */}
      <Dialog
        open={toolDialog}
        onClose={() => setToolDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedTool && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <BuildIcon sx={{ mr: 2, color: categoryColors[selectedTool.category] }} />
                <Box>
                  <Typography variant="h6">{selectedTool.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedTool.description}
                  </Typography>
                </Box>
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Parameters
                </Typography>
                
                {Object.keys(selectedTool.parameters || {}).length === 0 ? (
                  <Alert severity="info">This tool doesn't require any parameters.</Alert>
                ) : (
                  <Grid container spacing={2}>
                    {Object.entries(selectedTool.parameters || {}).map(([paramKey, param]) => (
                      <Grid item xs={12} sm={6} key={paramKey}>
                        {renderParameterInput(paramKey, param)}
                      </Grid>
                    ))}
                  </Grid>
                )}
              </Box>
              
              {executionResult && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {executionResult.success ? (
                        <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                      ) : (
                        <Error sx={{ color: 'error.main', mr: 1 }} />
                      )}
                      <Typography variant="subtitle1">
                        Execution Result
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ backgroundColor: 'grey.50', p: 2, borderRadius: 1 }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                        {executionResult.success 
                          ? JSON.stringify(executionResult.data, null, 2)
                          : executionResult.error
                        }
                      </pre>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Executed at: {new Date(executionResult.timestamp).toLocaleString()}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              )}
            </DialogContent>
            
            <DialogActions>
              <Button onClick={() => setToolDialog(false)}>
                Close
              </Button>
              <Button
                variant="contained"
                onClick={handleExecuteTool}
                disabled={executing}
                startIcon={executing ? <CircularProgress size={20} /> : <PlayIcon />}
              >
                {executing ? 'Executing...' : 'Execute Tool'}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}

export default ToolManager;