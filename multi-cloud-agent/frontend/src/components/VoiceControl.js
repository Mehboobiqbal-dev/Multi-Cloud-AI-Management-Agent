import React, { useState } from 'react';
// import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import api from '../services/api';
import { Button, Box, Typography } from '@mui/material';

function VoiceControl() {
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  /*
const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  if (!browserSupportsSpeechRecognition) {
    return <Typography>Browser doesn't support speech recognition.</Typography>;
  }
*/
// Placeholder for speech recognition functionality
const transcript = '';
// const listening = false; // Unused variable removed
const resetTranscript = () => {};


  /*
const handleListen = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      SpeechRecognition.startListening({ continuous: true });
    }
  };
*/

  const handleProcess = async () => {
    setLoading(true);
    try {
      // Assuming we send the transcript to /prompt for processing
      const res = await api.post('/prompt', { prompt: transcript });
      const plan = res.data.plan;
      // Execute plan or get response text
      const execRes = await api.post('/execute_plan', { plan });
      const responseText = execRes.data.result;
      // Ensure response is stringified if it's an object
      setResponse(typeof responseText === 'object' ? JSON.stringify(responseText, null, 2) : responseText);
      // Text-to-speech functionality is not implemented in the API yet
      // Uncomment when API supports this feature
      // await api.callTool('text_to_speech', { text: responseText });
    } catch (err) {
      setResponse('Error: ' + err.message);
    }
    setLoading(false);
    resetTranscript();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">Voice Control</Typography>
      {/* Listening controls temporarily disabled
      <Button onClick={handleListen} variant="contained">
        {listening ? 'Stop Listening' : 'Start Listening'}
      </Button>
      <TextField
        label="Transcript"
        value={transcript}
        fullWidth
        margin="normal"
        multiline
        disabled
      />
      */}
      <Button onClick={handleProcess} variant="contained" disabled={loading || !transcript}>
        Process Command
      </Button>
      {response && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Response:</Typography>
          <pre>{typeof response === 'object' ? JSON.stringify(response, null, 2) : response}</pre>
          <Typography>Response played via TTS.</Typography>
        </Box>
      )}
    </Box>
  );
}

export default VoiceControl;