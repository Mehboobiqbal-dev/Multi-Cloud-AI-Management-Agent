import React, { useState } from 'react';

function PromptForm({ onSubmit, loading }) {
  const [prompt, setPrompt] = useState('');
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState('en-US');

  /*
useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.onresult = (event) => {
        setPrompt(event.results[0][0].transcript);
      };
      recognitionRef.current.onend = () => setIsListening(false);
    }
  }, []);
*/

  /*
const toggleListening = () => {
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.lang = language;
      recognitionRef.current.start();
    }
    setIsListening(!isListening);
  };
*/

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() && !file) return;
    onSubmit({ prompt, file, language });
    setPrompt('');
    setFile(null);
  };

  return (
    <form onSubmit={handleSubmit} className="prompt-form">
      <select value={language} onChange={(e) => setLanguage(e.target.value)}>
        <option value="en-US">English</option>
        <option value="es-ES">Spanish</option>
        <option value="fr-FR">French</option>
        {/* Add more languages as needed */}
      </select>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter your prompt here..."
        disabled={loading}
        rows="3"
      />
      <input type="file" onChange={handleFileChange} accept="image/*,audio/*,video/*" />
      {/* Voice input button removed until functionality is implemented
      <button type="button" onClick={toggleListening} disabled={loading}>
        {isListening ? 'Stop Listening' : 'Start Voice Input'}
      </button>
      */}
      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Submit'}
      </button>
    </form>
  );
}

export default PromptForm;
