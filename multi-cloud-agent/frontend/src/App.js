import React, { useState } from 'react';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [knowledge, setKnowledge] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setKnowledge('');
    try {
      const res = await fetch('http://localhost:8000/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResponse(data);
      // Try to get knowledge base doc if intent is detected
      if (data.steps && data.steps.length > 1 && data.steps[1].details) {
        const intent = data.steps[1].details;
        if (intent.cloud && intent.resource !== 'unknown' && intent.operation !== 'unknown') {
          const kres = await fetch('http://localhost:8000/knowledge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              cloud: intent.cloud,
              resource: intent.resource,
              operation: intent.operation
            })
          });
          const kdata = await kres.json();
          setKnowledge(kdata.documentation);
        }
      }
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
        <div style={{ marginTop: '32px', textAlign: 'left', maxWidth: '700px', margin: '32px auto' }}>
          <h2>Status: {response.status}</h2>
          <p>{response.message}</p>
          <h3>Workflow Steps:</h3>
          <ol>
            {response.steps.map((step, idx) => (
              <li key={idx} style={{ marginBottom: '12px' }}>
                <b>{step.action}</b> - <span>{step.status}</span>
                {step.details && (
                  <pre style={{ background: '#f4f4f4', padding: '8px', borderRadius: '4px', marginTop: '4px', fontSize: '0.95em' }}>
                    {typeof step.details === 'object' ? JSON.stringify(step.details, null, 2) : step.details}
                  </pre>
                )}
              </li>
            ))}
          </ol>
          {knowledge && (
            <div style={{ background: '#e9f5ff', padding: '16px', borderRadius: '6px', marginTop: '24px' }}>
              <h3>Knowledge Base</h3>
              <p>{knowledge}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
