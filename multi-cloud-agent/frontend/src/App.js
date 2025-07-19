import React, { useState } from 'react';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    try {
      const res = await fetch('http://localhost:8000/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({ status: 'error', message: err.message, steps: [] });
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <h1>Multi-Cloud Agent</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Enter your cloud operation prompt..."
          style={{ width: '400px', padding: '8px' }}
        />
        <button type="submit" disabled={loading} style={{ marginLeft: '10px', padding: '8px 16px' }}>
          {loading ? 'Processing...' : 'Submit'}
        </button>
      </form>
      {response && (
        <div style={{ marginTop: '32px', textAlign: 'left', maxWidth: '600px', margin: '32px auto' }}>
          <h2>Status: {response.status}</h2>
          <p>{response.message}</p>
          <h3>Steps:</h3>
          <ol>
            {response.steps.map((step, idx) => (
              <li key={idx}>
                <b>{step.action}</b> - <span>{step.status}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export default App;
