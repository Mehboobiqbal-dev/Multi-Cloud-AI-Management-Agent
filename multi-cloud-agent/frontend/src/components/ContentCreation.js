import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Select, MenuItem, FormControl, InputLabel, Box, Typography } from '@mui/material';

function ContentCreation() {
  const [type, setType] = useState('text');
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.callTool('generate_content', { type, prompt });
      setResult(response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Content Creation</Typography>
      <form onSubmit={handleSubmit}>
        <FormControl fullWidth margin="normal">
          <InputLabel>Content Type</InputLabel>
          <Select value={type} onChange={(e) => setType(e.target.value)}>
            <MenuItem value="text">Text</MenuItem>
            <MenuItem value="blog">Blog Post</MenuItem>
            <MenuItem value="code">Code</MenuItem>
            <MenuItem value="image">Image</MenuItem>
            <MenuItem value="video">Video</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          fullWidth
          margin="normal"
          multiline
        />
        <Button type="submit" variant="contained" disabled={loading}>
          Generate
        </Button>
      </form>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Generated Content:</Typography>
          {type === 'image' || type === 'video' ? (
            <a href={typeof result === 'object' ? JSON.stringify(result) : result} target="_blank" rel="noopener noreferrer">
              {typeof result === 'object' ? JSON.stringify(result) : result}
            </a>
          ) : (
            <pre>{typeof result === 'object' ? JSON.stringify(result, null, 2) : result}</pre>
          )}
        </Box>
      )}
    </Box>
  );
}

export default ContentCreation;