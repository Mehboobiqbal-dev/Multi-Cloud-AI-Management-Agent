import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Tabs, Tab, Box, Typography } from '@mui/material';

function Ecommerce() {
  const [tabValue, setTabValue] = useState(0);
  const [product, setProduct] = useState('');
  const [url, setUrl] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAction = async (toolName) => {
    setLoading(true);
    try {
      let params = {};
      if (toolName === 'compare_prices') {
        params = { product };
      } else if (toolName === 'add_to_cart_amazon') {
        params = { url };
      }
      const response = await api.callTool(toolName, params);
      // Ensure response is stringified if it's an object
      setResult(typeof response === 'object' ? JSON.stringify(response, null, 2) : response);
    } catch (err) {
      setResult('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">E-commerce Automation</Typography>
      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Compare Prices" />
        <Tab label="Add to Cart (Amazon)" />
      </Tabs>
      {tabValue === 0 && (
        <TextField
          label="Product Name"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          fullWidth
          margin="normal"
        />
      )}
      {tabValue === 1 && (
        <TextField
          label="Product URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          fullWidth
          margin="normal"
        />
      )}
      <Button
        onClick={() => handleAction(tabValue === 0 ? 'compare_prices' : 'add_to_cart_amazon')}
        variant="contained"
        disabled={loading}
      >
        {tabValue === 0 ? 'Compare Prices' : 'Add to Cart'}
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

export default Ecommerce;