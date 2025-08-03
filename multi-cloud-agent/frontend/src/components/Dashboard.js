import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import PromptForm from './PromptForm';
import PlanDisplay from './PlanDisplay';
import ResultsDisplay from './ResultsDisplay';
import CredentialsModal from './CredentialsModal';
import Profile from './Profile';
import api from '../services/api';
import { AppBar, Toolbar, Typography, Button, Container, Tabs, Tab, Box } from '@mui/material';
import PluginManager from './PluginManager';
import Browsing from './Browsing';
import FormAutomation from './FormAutomation';
import ScrapingAnalysis from './ScrapingAnalysis';
import SocialMedia from './SocialMedia';
import Ecommerce from './Ecommerce';
import Email from './Email';
import ContentCreation from './ContentCreation';
import ApiIntegration from './ApiIntegration';
import Multimodal from './Multimodal';
import Autonomy from './Autonomy';
import Security from './Security';
import Multilingual from './Multilingual';
import VoiceControl from './VoiceControl';
import CustomPlugins from './CustomPlugins';

function Dashboard({ navigate }) {
  const { user, logout } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [plan, setPlan] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
const [showCreds, setShowCreds] = useState(false);
const [userInteractionMessage, setUserInteractionMessage] = useState(null);

  const handlePromptSubmit = async (prompt) => {
    setLoading(true);
    setPlan(null);
    setResponse(null);
    setUserInteractionMessage(null);
    try {
      const data = await api.runAgent(prompt);
      if (data.status === 'requires_input') {
        setUserInteractionMessage(data.final_result);
        setResponse(data);
      } else {
        setResponse(data);
      }
    } catch (err) {
      console.error('Agent run failed:', err);
      const message = err.message || 'An error occurred while running the agent.';
      setResponse({ status: 'error', message: message, history: [] });
    }
    setLoading(false);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            World Agent IDE
          </Typography>
          <Button color="inherit" onClick={() => setShowCreds(true)}>Manage Credentials</Button>
          <Button color="inherit" onClick={logout}>Logout</Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered>
          <Tab label="Browsing & Searching" />
          <Tab label="Form Filling & Automation" />
          <Tab label="Scraping & Analysis" />
          <Tab label="Social Media Management" />
          <Tab label="E-commerce Automation" />
          <Tab label="Email & Messaging" />
          <Tab label="Content Creation" />
          <Tab label="API Integration" />
          <Tab label="Multimodal Support" />
          <Tab label="Autonomy" />
          <Tab label="Security" />
          <Tab label="Multilingual" />
          <Tab label="Voice Control" />
          <Tab label="Custom Plugins" />
          <Tab label="History" onClick={() => navigate('/history')} />
          <Tab label="Profile" />
        </Tabs>
        {tabValue === 0 && <Browsing />}
        {tabValue === 1 && <FormAutomation />}
        {tabValue === 2 && <ScrapingAnalysis />}
        {tabValue === 3 && <SocialMedia />}
        {tabValue === 4 && <Ecommerce />}
        {tabValue === 5 && <Email />}
        {tabValue === 6 && <ContentCreation />}
        {tabValue === 7 && <ApiIntegration />}
        {tabValue === 8 && <Multimodal />}
        {tabValue === 9 && <Autonomy onSubmit={handlePromptSubmit} loading={loading} plan={plan} response={response} userInteractionMessage={userInteractionMessage} />}
        {tabValue === 10 && <Security />}
        {tabValue === 11 && <Multilingual />}
        {tabValue === 12 && <VoiceControl />}
        {tabValue === 13 && <CustomPlugins />}
        {tabValue === 15 && <Profile />}
      </Container>
      {showCreds && <CredentialsModal onClose={() => setShowCreds(false)} />}
    </Box>
  );
}

export default Dashboard;
