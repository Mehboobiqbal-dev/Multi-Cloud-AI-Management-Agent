import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Code as CodeIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

const StructuredMessageRenderer = ({ message, onAction }) => {
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  // Parse structured content from message
  const parseStructuredContent = (content) => {
    try {
      // Try to parse as JSON first
      if (content.startsWith('{') || content.startsWith('[')) {
        return JSON.parse(content);
      }
      
      // Parse different content types based on patterns
      const lines = content.split('\n');
      const structured = {
        type: 'general',
        title: '',
        summary: '',
        sections: [],
        actions: [],
        metadata: {}
      };

      let currentSection = null;
      let inCodeBlock = false;
      let codeContent = '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Detect code blocks
        if (line.startsWith('```')) {
          if (inCodeBlock) {
            if (currentSection) {
              currentSection.content.push({
                type: 'code',
                content: codeContent,
                language: line.substring(3) || 'text'
              });
            }
            codeContent = '';
            inCodeBlock = false;
          } else {
            inCodeBlock = true;
            codeContent = '';
          }
          continue;
        }

        if (inCodeBlock) {
          codeContent += line + '\n';
          continue;
        }

        // Detect headers
        if (line.startsWith('#')) {
          const level = line.match(/^#+/)[0].length;
          const title = line.substring(level).trim();
          
          if (level === 1 && !structured.title) {
            structured.title = title;
          } else {
            if (currentSection) {
              structured.sections.push(currentSection);
            }
            currentSection = {
              title,
              level,
              content: [],
              type: detectSectionType(title)
            };
          }
        }
        // Detect lists
        else if (line.startsWith('-') || line.startsWith('*') || /^\d+\./.test(line)) {
          const item = line.replace(/^[-*]\s*|^\d+\.\s*/, '');
          if (currentSection) {
            if (!currentSection.content.find(c => c.type === 'list')) {
              currentSection.content.push({ type: 'list', items: [] });
            }
            const listContent = currentSection.content.find(c => c.type === 'list');
            listContent.items.push(item);
          }
        }
        // Regular text
        else if (line) {
          if (!structured.title && !currentSection) {
            structured.summary += line + ' ';
          } else if (currentSection) {
            currentSection.content.push({ type: 'text', content: line });
          }
        }
      }

      if (currentSection) {
        structured.sections.push(currentSection);
      }

      return structured;
    } catch (error) {
      return {
        type: 'general',
        title: 'Response',
        summary: content,
        sections: [],
        actions: [],
        metadata: {}
      };
    }
  };

  const detectSectionType = (title) => {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('error') || titleLower.includes('failed')) return 'error';
    if (titleLower.includes('success') || titleLower.includes('completed')) return 'success';
    if (titleLower.includes('warning') || titleLower.includes('caution')) return 'warning';
    if (titleLower.includes('step') || titleLower.includes('action')) return 'steps';
    if (titleLower.includes('result') || titleLower.includes('output')) return 'results';
    if (titleLower.includes('code') || titleLower.includes('script')) return 'code';
    if (titleLower.includes('data') || titleLower.includes('table')) return 'data';
    return 'info';
  };

  const getSectionIcon = (type) => {
    switch (type) {
      case 'error': return <ErrorIcon color="error" />;
      case 'success': return <CheckCircleIcon color="success" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'steps': return <TimelineIcon color="primary" />;
      case 'results': return <AssessmentIcon color="primary" />;
      case 'code': return <CodeIcon color="primary" />;
      case 'data': return <StorageIcon color="primary" />;
      default: return <InfoIcon color="info" />;
    }
  };

  const renderContent = (contentItem) => {
    switch (contentItem.type) {
      case 'text':
        return (
          <Typography variant="body2" sx={{ mb: 1 }}>
            {contentItem.content}
          </Typography>
        );
      
      case 'code':
        return (
          <Paper 
            elevation={0} 
            sx={{ 
              bgcolor: 'grey.100', 
              p: 2, 
              mb: 1, 
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              overflow: 'auto'
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {contentItem.content}
            </pre>
          </Paper>
        );
      
      case 'list':
        return (
          <List dense sx={{ mb: 1 }}>
            {contentItem.items.map((item, index) => (
              <ListItem key={index} sx={{ py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 24 }}>
                  <Box 
                    sx={{ 
                      width: 6, 
                      height: 6, 
                      borderRadius: '50%', 
                      bgcolor: 'primary.main' 
                    }} 
                  />
                </ListItemIcon>
                <ListItemText 
                  primary={item} 
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        );
      
      default:
        return null;
    }
  };

  const renderSection = (section, index) => {
    const sectionId = `section-${index}`;
    const isExpanded = expandedSections[sectionId] !== false; // Default to expanded

    return (
      <Card key={index} elevation={1} sx={{ mb: 2 }}>
        <CardHeader
          avatar={getSectionIcon(section.type)}
          title={
            <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
              {section.title}
            </Typography>
          }
          action={
            <IconButton onClick={() => toggleSection(sectionId)}>
              <ExpandMoreIcon 
                sx={{ 
                  transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s'
                }}
              />
            </IconButton>
          }
          sx={{ pb: 1 }}
        />
        {isExpanded && (
          <CardContent sx={{ pt: 0 }}>
            {section.content.map((contentItem, contentIndex) => (
              <Box key={contentIndex}>
                {renderContent(contentItem)}
              </Box>
            ))}
          </CardContent>
        )}
      </Card>
    );
  };

  const renderTaskProgress = (progress) => {
    if (!progress) return null;
    
    return (
      <Card elevation={1} sx={{ mb: 2 }}>
        <CardHeader
          avatar={<TimelineIcon color="primary" />}
          title="Task Progress"
          subheader={`${progress.completed}/${progress.total} steps completed`}
        />
        <CardContent>
          <LinearProgress 
            variant="determinate" 
            value={(progress.completed / progress.total) * 100}
            sx={{ mb: 2, height: 8, borderRadius: 4 }}
          />
          {progress.currentStep && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Current Step:</strong> {progress.currentStep}
              </Typography>
            </Alert>
          )}
          {progress.steps && (
            <List dense>
              {progress.steps.map((step, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {step.status === 'completed' ? (
                      <CheckCircleIcon color="success" />
                    ) : step.status === 'failed' ? (
                      <ErrorIcon color="error" />
                    ) : step.status === 'running' ? (
                      <PlayArrowIcon color="primary" />
                    ) : (
                      <PauseIcon color="disabled" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={step.name}
                    secondary={step.description}
                    primaryTypographyProps={{
                      sx: {
                        textDecoration: step.status === 'completed' ? 'line-through' : 'none',
                        opacity: step.status === 'completed' ? 0.7 : 1
                      }
                    }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderActionButtons = (actions) => {
    if (!actions || actions.length === 0) return null;

    return (
      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {actions.map((action, index) => (
          <Button
            key={index}
            variant={action.primary ? 'contained' : 'outlined'}
            size="small"
            startIcon={action.icon}
            onClick={() => onAction && onAction(action)}
            sx={{ borderRadius: 2 }}
          >
            {action.label}
          </Button>
        ))}
      </Box>
    );
  };

  // Parse the message content
  const structured = parseStructuredContent(message.content);
  
  // Check if this is an agent response with history
  const isAgentResponse = message.metadata && (message.metadata.history || message.metadata.status);
  const hasProgress = message.metadata && message.metadata.progress;

  return (
    <Box sx={{ mb: 2 }}>
      {/* Main Response Card */}
      <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
        {/* Header */}
        {structured.title && (
          <Box sx={{ mb: 2, pb: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
              {structured.title}
            </Typography>
            {structured.summary && (
              <Typography variant="body1" sx={{ mt: 1, color: 'text.secondary' }}>
                {structured.summary.trim()}
              </Typography>
            )}
          </Box>
        )}

        {/* Task Progress */}
        {hasProgress && renderTaskProgress(message.metadata.progress)}

        {/* Agent Status */}
        {isAgentResponse && message.metadata.status && (
          <Alert 
            severity={
              message.metadata.status === 'completed' ? 'success' :
              message.metadata.status === 'failed' ? 'error' :
              message.metadata.status === 'running' ? 'info' : 'warning'
            }
            sx={{ mb: 2 }}
          >
            <Typography variant="body2">
              <strong>Status:</strong> {message.metadata.status}
              {message.metadata.message && ` - ${message.metadata.message}`}
            </Typography>
          </Alert>
        )}

        {/* Content Sections */}
        {structured.sections.map((section, index) => renderSection(section, index))}

        {/* Simple content fallback */}
        {structured.sections.length === 0 && !structured.title && (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {message.content}
          </Typography>
        )}

        {/* Action Buttons */}
        {structured.actions && renderActionButtons(structured.actions)}

        {/* Agent History Summary */}
        {isAgentResponse && message.metadata.history && message.metadata.history.length > 0 && (
          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TimelineIcon color="primary" />
                <Typography variant="subtitle2">
                  Execution History ({message.metadata.history.length} steps)
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Step</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Result</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {message.metadata.history.map((step, index) => (
                      <TableRow key={index}>
                        <TableCell>{step.step}</TableCell>
                        <TableCell>
                          <Chip 
                            label={step.action?.name || 'Unknown'} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={step.result ? 'Success' : 'Failed'}
                            size="small"
                            color={step.result ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {typeof step.result === 'string' ? step.result.substring(0, 100) + '...' : 'No result'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Metadata */}
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="caption" color="text.secondary">
                Technical Details
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Paper elevation={0} sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <pre style={{ fontSize: '0.75rem', margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(message.metadata, null, 2)}
                </pre>
              </Paper>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Footer */}
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {format(new Date(message.timestamp), 'MMM dd, yyyy HH:mm:ss')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="View Details">
              <IconButton size="small">
                <VisibilityIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download">
              <IconButton size="small">
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share">
              <IconButton size="small">
                <ShareIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default StructuredMessageRenderer;