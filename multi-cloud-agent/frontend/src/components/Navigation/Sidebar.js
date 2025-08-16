import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Typography,
  Box,
  Chip,
  useTheme,
  alpha
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Chat as ChatIcon,
  Cloud as CloudIcon,
  SmartToy as AutoModeIcon,
  Construction as BuildIcon,
  Language as WebIcon,
  Memory as MemoryIcon,
  Analytics as AnalyticsIcon,
  Assignment as TaskIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';

const DRAWER_WIDTH = 280;

const navigationItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: DashboardIcon,
    description: 'Main control center'
  },
  {
    id: 'chat',
    label: 'AI Chat',
    icon: ChatIcon,
    description: 'Conversational AI interface',
    badge: 'Active'
  },
  {
    id: 'divider1',
    type: 'divider',
    label: 'Automation & Tools'
  },
  {
    id: 'tools',
    label: 'Tool Manager',
    icon: BuildIcon,
    description: 'Execute tools directly'
  },
  {
    id: 'form-automation',
    label: 'Form Automation',
    icon: AutoModeIcon,
    description: 'Job applications & forms'
  },
  {
    id: 'web-browsing',
    label: 'Web Browsing',
    icon: WebIcon,
    description: 'Web scraping & automation'
  },
  {
    id: 'plan-execution',
    label: 'Plan Execution',
    icon: PsychologyIcon,
    description: 'Multi-step workflows'
  },
  {
    id: 'divider2',
    type: 'divider',
    label: 'Data & Configuration'
  },
  {
    id: 'cloud-credentials',
    label: 'Cloud Credentials',
    icon: CloudIcon,
    description: 'AWS, Azure, GCP settings'
  },
  {
    id: 'task-results',
    label: 'Task Results',
    icon: TaskIcon,
    description: 'View execution history'
  },
  {
    id: 'memory',
    label: 'Agent Memory',
    icon: MemoryIcon,
    description: 'Knowledge & learning'
  },
  {
    id: 'divider3',
    type: 'divider',
    label: 'Monitoring'
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: AnalyticsIcon,
    description: 'Performance & usage'
  },
  {
    id: 'history',
    label: 'Chat History',
    icon: HistoryIcon,
    description: 'Conversation logs'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: SettingsIcon,
    description: 'Preferences & config'
  }
];

function Sidebar({ open, onNavigate, currentSection, onClose }) {
  const theme = useTheme();

  const handleItemClick = (item) => {
    if (item.type !== 'divider') {
      onNavigate(item.id);
      if (onClose) onClose();
    }
  };

  const renderListItem = (item) => {
    if (item.type === 'divider') {
      return (
        <Box key={item.id} sx={{ mt: 2, mb: 1 }}>
          <Divider />
          <Typography
            variant="overline"
            sx={{
              px: 2,
              py: 1,
              display: 'block',
              color: 'text.secondary',
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.1em'
            }}
          >
            {item.label}
          </Typography>
        </Box>
      );
    }

    const Icon = item.icon;
    const isActive = currentSection === item.id;

    return (
      <ListItem key={item.id} disablePadding>
        <ListItemButton
          onClick={() => handleItemClick(item)}
          sx={{
            mx: 1,
            mb: 0.5,
            borderRadius: 2,
            minHeight: 48,
            backgroundColor: isActive ? alpha(theme.palette.primary.main, 0.12) : 'transparent',
            color: isActive ? theme.palette.primary.main : 'text.primary',
            '&:hover': {
              backgroundColor: isActive 
                ? alpha(theme.palette.primary.main, 0.16)
                : alpha(theme.palette.action.hover, 0.08)
            },
            transition: 'all 0.2s ease-in-out'
          }}
        >
          <ListItemIcon
            sx={{
              color: 'inherit',
              minWidth: 40
            }}
          >
            <Icon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" fontWeight={isActive ? 600 : 400}>
                  {item.label}
                </Typography>
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </Box>
            }
            secondary={
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.7rem',
                  lineHeight: 1.2,
                  mt: 0.5
                }}
              >
                {item.description}
              </Typography>
            }
          />
        </ListItemButton>
      </ListItem>
    );
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          borderRight: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
          backgroundImage: 'none'
        }
      }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: `1px solid ${theme.palette.divider}`,
          backgroundColor: alpha(theme.palette.primary.main, 0.04)
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            color: theme.palette.primary.main,
            textAlign: 'center'
          }}
        >
          Multi-Cloud AI Agent
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            textAlign: 'center',
            display: 'block',
            mt: 0.5
          }}
        >
          Intelligent Automation Platform
        </Typography>
      </Box>
      
      <Box sx={{ overflow: 'auto', flex: 1, py: 1 }}>
        <List>
          {navigationItems.map(renderListItem)}
        </List>
      </Box>
      
      <Box
        sx={{
          p: 2,
          borderTop: `1px solid ${theme.palette.divider}`,
          backgroundColor: alpha(theme.palette.background.default, 0.5)
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            textAlign: 'center',
            display: 'block'
          }}
        >
          v2.0.0 • Enhanced UI
        </Typography>
      </Box>
    </Drawer>
  );
}

export default Sidebar;
export { DRAWER_WIDTH };