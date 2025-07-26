import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import PromptForm from './PromptForm';
import PlanDisplay from './PlanDisplay';
import ResultsDisplay from './ResultsDisplay';
import CredentialsModal from './CredentialsModal';
import api from '../services/api';

function Dashboard() {
  const { user, logout } = useAuth();
  const [plan, setPlan] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCreds, setShowCreds] = useState(false);

  const handlePromptSubmit = async (prompt) => {
    setLoading(true);
    setPlan(null);
    setResponse(null);
    try {
      const data = await api.submitPrompt(prompt);
      setPlan(data.plan);
    } catch (err) {
      setResponse({ status: 'error', message: err.detail || 'An error occurred', steps: [] });
    }
    setLoading(false);
  };

  const handlePlanConfirm = async () => {
    setLoading(true);
    try {
      const data = await api.executePlan(plan);
      setResponse(data);
    } catch (err) {
      setResponse({ status: 'error', message: err.detail || 'An error occurred', steps: [] });
    }
    setLoading(false);
    setPlan(null);
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h2>Universal Agent</h2>
        <div className="user-info">
          <span>Welcome, {user.name || user.email}</span>
          <button onClick={() => setShowCreds(true)} className="btn">Manage Credentials</button>
          <button onClick={logout} className="btn btn-logout">Logout</button>
        </div>
      </header>
      
      <CredentialsModal 
        isOpen={showCreds} 
        onClose={() => setShowCreds(false)} 
      />
      
      <main className="dashboard-main">
        <div className="prompt-section">
          <PromptForm onSubmit={handlePromptSubmit} loading={loading} />
        </div>
        
        {loading && <div className="loader"></div>}

        {plan && (
          <div className="plan-section">
            <PlanDisplay plan={plan} onConfirm={handlePlanConfirm} loading={loading} />
          </div>
        )}
        
        {response && (
          <div className="results-section">
            <ResultsDisplay response={response} />
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
