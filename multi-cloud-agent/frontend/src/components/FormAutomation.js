import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Box, Typography, List, ListItem, IconButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

function FormAutomation() {
  const [url, setUrl] = useState('');
  const [browserId, setBrowserId] = useState('');
  const [fields, setFields] = useState([{ selector: '', value: '' }]);
  const [selector, setSelector] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const addField = () => setFields([...fields, { selector: '', value: '' }]);

  const updateField = (index, key, val) => {
    const newFields = [...fields];
    newFields[index][key] = val;
    setFields(newFields);
  };

  const handleOpen = async () => {
    setLoading(true);
    try {
      const res = await api.callTool('open_browser', { url });
      setBrowserId(res.split('ID: ')[1].split('.')[0]);
      setResults([...results, res]);
    } catch (err) {
      setResults([...results, 'Error: ' + err.message]);
    }
    setLoading(false);
  };

  const handleFill = async () => {
    setLoading(true);
    try {
      const res = await api.callTool('fill_multiple_fields', { browser_id: browserId, fields });
      setResults([...results, res]);
    } catch (err) {
      setResults([...results, 'Error: ' + err.message]);
    }
    setLoading(false);
  };

  const handleClick = async () => {
    setLoading(true);
    try {
      const res = await api.callTool('click_button', { browser_id: browserId, selector });
      setResults([...results, res]);
    } catch (err) {
      setResults([...results, 'Error: ' + err.message]);
    }
    setLoading(false);
  };

  const handleClose = async () => {
    setLoading(true);
    try {
      const res = await api.callTool('close_browser', { browser_id: browserId });
      setResults([...results, res]);
      setBrowserId('');
    } catch (err) {
      setResults([...results, 'Error: ' + err.message]);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Form Filling & Automation</Typography>
      <TextField label="URL" value={url} onChange={(e) => setUrl(e.target.value)} fullWidth margin="normal" />
      <Button onClick={handleOpen} variant="contained" disabled={loading || !url}>Open Browser</Button>
      {browserId && (
        <>
          <Typography>Browser ID: {browserId}</Typography>
          <List>
            {fields.map((field, index) => (
              <ListItem key={index}>
                <TextField label="Selector" value={field.selector} onChange={(e) => updateField(index, 'selector', e.target.value)} />
                <TextField label="Value" value={field.value} onChange={(e) => updateField(index, 'value', e.target.value)} />
              </ListItem>
            ))}
            <IconButton onClick={addField}><AddIcon /></IconButton>
          </List>
          <Button onClick={handleFill} variant="contained" disabled={loading || fields.some(f => !f.selector || !f.value)}>Fill Form</Button>
          <TextField label="Button Selector" value={selector} onChange={(e) => setSelector(e.target.value)} fullWidth margin="normal" />
          <Button onClick={handleClick} variant="contained" disabled={loading || !selector}>Click Button</Button>
          <Button onClick={handleClose} variant="contained" color="secondary">Close Browser</Button>
        </>
      )}
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6">Results:</Typography>
        <pre>{results.join('\n')}</pre>
      </Box>
    </Box>
  );
}

export default FormAutomation;