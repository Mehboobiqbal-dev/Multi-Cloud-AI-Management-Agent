import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel, Box, Typography } from '@mui/material';

function Browsing() {
  const [query, setQuery] = useState('');
  const [engine, setEngine] = useState('google');
  const [results, setResults] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.callTool('search_web', { query, engine });
      setResults(response);
    } catch (err) {
      setResults('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Browsing & Searching</Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label="Search Query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          fullWidth
          margin="normal"
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Search Engine</InputLabel>
          <Select value={engine} onChange={(e) => setEngine(e.target.value)}>
            <MenuItem value="google">Google</MenuItem>
            <MenuItem value="bing">Bing</MenuItem>
            <MenuItem value="duckduckgo">DuckDuckGo</MenuItem>
          </Select>
        </FormControl>
        <Button type="submit" variant="contained" disabled={loading}>
          Search
        </Button>
      </form>
      {results && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Results:</Typography>
          <pre>{results}</pre>
        </Box>
      )}
    </Box>
  );
}

export default Browsing;