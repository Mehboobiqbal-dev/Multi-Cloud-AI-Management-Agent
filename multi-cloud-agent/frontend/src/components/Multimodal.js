import React, { useState } from 'react';
import api from '../services/api';
import { Button, Select, MenuItem, FormControl, InputLabel, Box, Typography, TextField } from '@mui/material';
import Dropzone from 'react-dropzone';

function Multimodal() {
  const [type, setType] = useState('analyze_image');
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const onDrop = (acceptedFiles) => {
    setFile(acceptedFiles[0]);
  };

  const handleAction = async () => {
    setLoading(true);
    try {
      let params = {};
      if (type === 'analyze_image' || type === 'speech_to_text') {
        params = { file: file.path }; // Assuming file upload handling in backend
      } else if (type === 'text_to_speech') {
        params = { text };
      }
      const response = await api.callTool(type, params);
      // Ensure response is stringified if it's an object
      setResult(typeof response === 'object' ? JSON.stringify(response, null, 2) : response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Multimodal Support</Typography>
      <FormControl fullWidth margin="normal">
        <InputLabel>Action</InputLabel>
        <Select value={type} onChange={(e) => setType(e.target.value)}>
          <MenuItem value="analyze_image">Analyze Image</MenuItem>
          <MenuItem value="speech_to_text">Speech to Text</MenuItem>
          <MenuItem value="text_to_speech">Text to Speech</MenuItem>
        </Select>
      </FormControl>
      {(type === 'analyze_image' || type === 'speech_to_text') && (
        <Dropzone onDrop={onDrop}>
          {({ getRootProps, getInputProps }) => (
            <Box {...getRootProps()} sx={{ border: '1px dashed gray', p: 2, textAlign: 'center' }}>
              <input {...getInputProps()} />
              <Typography>Drag & drop file here, or click to select</Typography>
              {file && <Typography>Selected: {file.name}</Typography>}
            </Box>
          )}
        </Dropzone>
      )}
      {type === 'text_to_speech' && (
        <TextField
          label="Text to Convert"
          value={text}
          onChange={(e) => setText(e.target.value)}
          fullWidth
          margin="normal"
          multiline
        />
      )}
      <Button onClick={handleAction} variant="contained" disabled={loading || !((type !== 'text_to_speech' && file) || (type === 'text_to_speech' && text))}>
        Process
      </Button>
      {result && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Result:</Typography>
          <pre>{typeof result === 'object' ? JSON.stringify(result, null, 2) : result}</pre>
        </Box>
      )}
    </Box>
  );
}

export default Multimodal;