import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Box, Typography, List, ListItem } from '@mui/material';

function CustomPlugins() {
  const [pluginPath, setPluginPath] = useState('');
  const [loadedPlugins, setLoadedPlugins] = useState([]);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    try {
      const response = await api.callTool('load_plugin', { path: pluginPath });
      setLoadedPlugins([...loadedPlugins, response]);
      setResult('Plugin loaded successfully');
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Custom Plugins</Typography>
      <TextField
        label="Plugin Path"
        value={pluginPath}
        onChange={(e) => setPluginPath(e.target.value)}
        fullWidth
        margin="normal"
      />
      <Button onClick={handleLoad} variant="contained" disabled={loading}>
        Load Plugin
      </Button>
      {result && <Typography sx={{ mt: 2 }}>{result}</Typography>}
      <Typography variant="h6" sx={{ mt: 2 }}>Loaded Plugins:</Typography>
      <List>
        {loadedPlugins.map((plugin, index) => (
          <ListItem key={index}>{plugin}</ListItem>
        ))}
      </List>
    </Box>
  );
}

export default CustomPlugins;