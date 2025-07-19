import React, { useState, useEffect } from 'react';
import './App.css';
import { AuthProvider, GoogleLoginButton } from './auth';

const cloudIcons = {
  aws: '🟧',
  azure: '🟦',
  gcp: '🟨',
};

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [knowledge, setKnowledge] = useState('');
  const [errorExplanation, setErrorExplanation] = useState('');
  const [history, setHistory] = useState([]);
  const [creds, setCreds] = useState([]);
  const [showCreds, setShowCreds] = useState(false);
  const [credForm, setCredForm] = useState({ provider: 'aws', access_key: '', secret_key: '', azure_subscription_id: '', azure_client_id: '', azure_client_secret: '', azure_tenant_id: '', gcp_project_id: '', gcp_credentials_json: '' });

  useEffect(() => {
    if (token) {
      fetch('/me', { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json())
        .then(u => setUser(u))
        .catch(() => setUser(null));
      fetch('/credentials', { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json())
        .then(setCreds);
    }
  }, [token]);

  const handleGoogleLogin = async (credentialResponse) => {
    // Send credential to backend for session
    const res = await fetch('/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: credentialResponse.credential })
    });
    const data = await res.json();
    if (data.token) {
      setToken(data.token);
      localStorage.setItem('token', data.token);
      setUser(data.user);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const handleCredFormChange = (e) => {
    setCredForm({ ...credForm, [e.target.name]: e.target.value });
  };

  const handleCredSave = async (e) => {
    e.preventDefault();
    await fetch('/credentials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(credForm)
    });
    setShowCreds(false);
    fetch('/credentials', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(setCreds);
  };

  if (!token || !user) {
    return (
      <AuthProvider>
        <div className="App">
          <h1>Multi-Cloud Agent</h1>
          <GoogleLoginButton onSuccess={handleGoogleLogin} onError={() => alert('Login failed')} />
        </div>
      </AuthProvider>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setKnowledge('');
    setErrorExplanation('');
    try {
      const res = await fetch('http://localhost:8000/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResponse(data);
      setHistory([{ prompt, response: data }, ...history.slice(0, 9)]);
      // Try to get knowledge base doc if intent is detected
      if (data.steps && data.steps.length > 1 && data.steps[1].details && Array.isArray(data.steps[1].details)) {
        // Multi-cloud: show docs for first intent
        const firstIntent = data.steps[1].details[0];
        if (firstIntent && firstIntent.cloud && firstIntent.resource !== 'unknown' && firstIntent.operation !== 'unknown') {
          const kres = await fetch('http://localhost:8000/knowledge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              cloud: firstIntent.cloud,
              resource: firstIntent.resource,
              operation: firstIntent.operation
            })
          });
          const kdata = await kres.json();
          setKnowledge(kdata.documentation);
        }
      }
      // Show error explanation if error
      if (data.status === 'error' && data.steps) {
        const errorStep = data.steps.find(s => s.status === 'error');
        if (errorStep && errorStep.details && errorStep.details.error) {
          let errorType = 'unknown';
          if (errorStep.details.error.includes('credentials')) errorType = 'credentials';
          if (errorStep.details.error.includes('not implemented')) errorType = 'not_implemented';
          const expRes = await fetch('http://localhost:8000/knowledge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cloud: '', resource: '', operation: errorType })
          });
          const expData = await expRes.json();
          setErrorExplanation(expData.documentation);
        }
      }
    } catch (err) {
      setResponse({ status: 'error', message: err.message, steps: [] });
    }
    setLoading(false);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Helper to extract per-cloud results from steps
  const getCloudResults = (steps) => {
    return steps.filter(s => s.action && s.action.startsWith('Execute'));
  };

  return (
    <div className="App">
      <h1>Multi-Cloud Agent</h1>
      <div style={{ float: 'right' }}>
        <span>{user.email}</span>
        <button onClick={handleLogout} style={{ marginLeft: '10px' }}>Logout</button>
        <button onClick={() => setShowCreds(!showCreds)} style={{ marginLeft: '10px' }}>Cloud Credentials</button>
      </div>
      {showCreds && (
        <form onSubmit={handleCredSave} style={{ background: '#f8f8fa', padding: '16px', borderRadius: '8px', margin: '24px auto', maxWidth: '600px' }}>
          <h3>Manage Cloud Credentials</h3>
          <select name="provider" value={credForm.provider} onChange={handleCredFormChange}>
            <option value="aws">AWS</option>
            <option value="azure">Azure</option>
            <option value="gcp">GCP</option>
          </select>
          {credForm.provider === 'aws' && (
            <>
              <input name="access_key" placeholder="AWS Access Key" value={credForm.access_key} onChange={handleCredFormChange} />
              <input name="secret_key" placeholder="AWS Secret Key" value={credForm.secret_key} onChange={handleCredFormChange} />
            </>
          )}
          {credForm.provider === 'azure' && (
            <>
              <input name="azure_subscription_id" placeholder="Azure Subscription ID" value={credForm.azure_subscription_id} onChange={handleCredFormChange} />
              <input name="azure_client_id" placeholder="Azure Client ID" value={credForm.azure_client_id} onChange={handleCredFormChange} />
              <input name="azure_client_secret" placeholder="Azure Client Secret" value={credForm.azure_client_secret} onChange={handleCredFormChange} />
              <input name="azure_tenant_id" placeholder="Azure Tenant ID" value={credForm.azure_tenant_id} onChange={handleCredFormChange} />
            </>
          )}
          {credForm.provider === 'gcp' && (
            <>
              <input name="gcp_project_id" placeholder="GCP Project ID" value={credForm.gcp_project_id} onChange={handleCredFormChange} />
              <textarea name="gcp_credentials_json" placeholder="GCP Credentials JSON" value={credForm.gcp_credentials_json} onChange={handleCredFormChange} />
            </>
          )}
          <button type="submit">Save</button>
        </form>
      )}
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
      {/* History Panel */}
      {history.length > 0 && (
        <div style={{ margin: '32px auto', maxWidth: '700px', textAlign: 'left', background: '#f8f8fa', borderRadius: '8px', padding: '16px' }}>
          <h3>History</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {history.map((h, idx) => (
              <li key={idx} style={{ marginBottom: '10px', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>
                <b>Prompt:</b> {h.prompt}
                <button style={{ marginLeft: '10px', fontSize: '0.9em' }} onClick={() => setResponse(h.response)}>View</button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {response && (
        <div style={{ marginTop: '32px', textAlign: 'left', maxWidth: '700px', margin: '32px auto' }}>
          <h2>Status: {response.status}</h2>
          <p>{response.message}</p>
          {/* Per-cloud result cards */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '24px' }}>
            {getCloudResults(response.steps).map((step, idx) => {
              const cloud = (step.action.match(/on (\w+)/) || [])[1];
              return (
                <div key={idx} style={{ background: '#fff', border: '1px solid #eee', borderRadius: '8px', padding: '16px', minWidth: '220px', boxShadow: '0 2px 8px #f0f0f0' }}>
                  <div style={{ fontSize: '2em' }}>{cloudIcons[cloud] || '☁️'} {cloud && cloud.toUpperCase()}</div>
                  <div style={{ marginTop: '8px', fontWeight: 'bold' }}>{step.action}</div>
                  <div style={{ marginTop: '8px', color: step.status === 'error' ? '#d32f2f' : '#388e3c' }}>{step.status}</div>
                  <pre style={{ background: '#f4f4f4', padding: '8px', borderRadius: '4px', marginTop: '8px', fontSize: '0.95em' }}>
                    {typeof step.details === 'object' ? JSON.stringify(step.details, null, 2) : step.details}
                  </pre>
                  <button style={{ marginTop: '8px', fontSize: '0.9em' }} onClick={() => copyToClipboard(typeof step.details === 'object' ? JSON.stringify(step.details, null, 2) : String(step.details))}>Copy Result</button>
                </div>
              );
            })}
          </div>
          <h3 style={{ marginTop: '32px' }}>Workflow Steps:</h3>
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
          {errorExplanation && (
            <div style={{ background: '#ffe9e9', padding: '16px', borderRadius: '6px', marginTop: '24px' }}>
              <h3>Error Explanation</h3>
              <p>{errorExplanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
