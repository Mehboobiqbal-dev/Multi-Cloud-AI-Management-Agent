import React, { useState } from 'react';
import { Box, Button, TextField, List, ListItem, ListItemText, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

function PluginManager() {
  const [plugins, setPlugins] = useState([]);
  const [newPlugin, setNewPlugin] = useState('');

  const addPlugin = () => {
    if (newPlugin) {
      setPlugins([...plugins, newPlugin]);
      setNewPlugin('');
    }
  };

  const removePlugin = (index) => {
    setPlugins(plugins.filter((_, i) => i !== index));
  };

  return (
    <Box sx={{ p: 2, border: '1px solid grey', borderRadius: 2 }}>
      <h3>Custom Plugins</h3>
      <TextField
        value={newPlugin}
        onChange={(e) => setNewPlugin(e.target.value)}
        placeholder="Enter plugin URL or name"
        fullWidth
      />
      <Button onClick={addPlugin} variant="contained" sx={{ mt: 1 }}>Add Plugin</Button>
      <List>
        {plugins.map((plugin, index) => (
          <ListItem key={index} secondaryAction={
            <IconButton edge="end" onClick={() => removePlugin(index)}>
              <DeleteIcon />
            </IconButton>
          }>
            <ListItemText primary={plugin} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export default PluginManager;