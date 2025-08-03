import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel, Box, Typography, Tabs, Tab } from '@mui/material';

function Multilingual() {
  const [tabValue, setTabValue] = useState(0);
  const [text, setText] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAction = async (toolName) => {
    setLoading(true);
    try {
      let params = { text };
      if (toolName === 'translate_text') {
        params.source_lang = sourceLang;
        params.target_lang = targetLang;
      }
      const response = await api.callTool(toolName, params);
      setResult(response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Multilingual Support</Typography>
      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Detect Language" />
        <Tab label="Translate Text" />
      </Tabs>
      <TextField
        label="Text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        fullWidth
        margin="normal"
        multiline
      />
      {tabValue === 1 && (
        <>
          <FormControl fullWidth margin="normal">
            <InputLabel>Source Language</InputLabel>
            <Select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
              <MenuItem value="auto">Auto</MenuItem>
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="es">Spanish</MenuItem>
              <MenuItem value="fr">French</MenuItem>
              {/* Add more languages as needed */}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Target Language</InputLabel>
            <Select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="es">Spanish</MenuItem>
              <MenuItem value="fr">French</MenuItem>
              {/* Add more languages as needed */}
            </Select>
          </FormControl>
        </>
      )}
      <Button
        onClick={() => handleAction(tabValue === 0 ? 'detect_language' : 'translate_text')}
        variant="contained"
        disabled={loading}
      >
        {tabValue === 0 ? 'Detect' : 'Translate'}
      </Button>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Result:</Typography>
          <pre>{result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default Multilingual;