import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel, Box, Typography } from '@mui/material';

function ScrapingAnalysis() {
  const [url, setUrl] = useState('');
  const [analysis, setAnalysis] = useState('summarize');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.callTool('scrape_and_analyze', { url, analysis });
      setResult(response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Scraping & Analysis</Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label="URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          fullWidth
          margin="normal"
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Analysis Type</InputLabel>
          <Select value={analysis} onChange={(e) => setAnalysis(e.target.value)}>
            <MenuItem value="summarize">Summarize</MenuItem>
            <MenuItem value="extract_data">Extract Data</MenuItem>
          </Select>
        </FormControl>
        <Button type="submit" variant="contained" disabled={loading}>
          Analyze
        </Button>
      </form>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Result:</Typography>
          <pre>{result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default ScrapingAnalysis;