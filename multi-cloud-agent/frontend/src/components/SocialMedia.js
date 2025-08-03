import React, { useState } from 'react';
import api from '../services/api';
import { TextField, Button, Tabs, Tab, Box, Typography } from '@mui/material';

function SocialMedia() {
  const [tabValue, setTabValue] = useState(0);
  const [content, setContent] = useState('');
  const [tweetId, setTweetId] = useState('');
  const [userId, setUserId] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAction = async (toolName) => {
    setLoading(true);
    try {
      let params = {};
      if (toolName === 'post_to_twitter' || toolName === 'post_to_linkedin') {
        params = { content };
      } else if (toolName === 'comment_on_twitter') {
        params = { tweet_id: tweetId, comment: content };
      } else if (toolName === 'send_dm_twitter') {
        params = { user_id: userId, message: content };
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
      <Typography variant="h5">Social Media Management</Typography>
      <Tabs value={tabValue} onChange={handleTabChange} centered>
        <Tab label="Twitter Post" />
        <Tab label="Twitter Comment" />
        <Tab label="Twitter DM" />
        <Tab label="LinkedIn Post" />
      </Tabs>
      <TextField
        label="Content/Message/Comment"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        fullWidth
        margin="normal"
        multiline
      />
      {tabValue === 1 && (
        <TextField
          label="Tweet ID"
          value={tweetId}
          onChange={(e) => setTweetId(e.target.value)}
          fullWidth
          margin="normal"
        />
      )}
      {tabValue === 2 && (
        <TextField
          label="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          fullWidth
          margin="normal"
        />
      )}
      <Button
        onClick={() => handleAction(tabValue === 0 ? 'post_to_twitter' : tabValue === 1 ? 'comment_on_twitter' : tabValue === 2 ? 'send_dm_twitter' : 'post_to_linkedin')}
        variant="contained"
        disabled={loading}
      >
        {tabValue === 0 ? 'Post to Twitter' : tabValue === 1 ? 'Comment on Twitter' : tabValue === 2 ? 'Send DM on Twitter' : 'Post to LinkedIn'}
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

export default SocialMedia;