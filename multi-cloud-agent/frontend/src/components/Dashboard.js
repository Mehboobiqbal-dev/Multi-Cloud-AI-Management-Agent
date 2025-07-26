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
    <div>
      <header className="dashboard-header">
        <span>Welcome, {user.name || user.email}</span>
        <div>
          <button onClick={() => setShowCreds(true)}>Manage Credentials</button>
          <button onClick={logout} style={{ marginLeft: '10px' }}>Logout</button>
        </div>
      </header>
      
      <CredentialsModal 
        isOpen={showCreds} 
        onClose={() => setShowCreds(false)} 
      />
      
      <PromptForm onSubmit={handlePromptSubmit} loading={loading} />
      
      {plan && <PlanDisplay plan={plan} onConfirm={handlePlanConfirm} loading={loading} />}
      
      {response && <ResultsDisplay response={response} />}
    </div>
  );
}

export default Dashboard;
