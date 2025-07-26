import React from 'react';

const cloudIcons = {
  aws: '🟧',
  azure: '🟦',
  gcp: '🟨',
};

function ResultsDisplay({ response }) {
  const getCloudResults = (steps) => {
    return steps.filter(s => s.action && s.action.startsWith('Execute'));
  };

  return (
    <div className="results-display">
      <h2>Status: <span className={`status-${response.status}`}>{response.status}</span></h2>
      <p>{response.message}</p>
      
      <div className="results-grid">
        {getCloudResults(response.steps).map((step, idx) => {
          const cloud = (step.action.match(/on (\w+)/) || [])[1];
          return (
            <div key={idx} className="result-card">
              <div className="card-header">
                <span className="cloud-icon">{cloudIcons[cloud] || '☁️'}</span>
                <h3>{cloud && cloud.toUpperCase()}</h3>
              </div>
              <div className="card-body">
                <p><strong>Action:</strong> {step.action}</p>
                <p><strong>Status:</strong> <span className={`status-${step.status}`}>{step.status}</span></p>
                <pre>{typeof step.details === 'object' ? JSON.stringify(step.details, null, 2) : step.details}</pre>
              </div>
            </div>
          );
        })}
      </div>

      <div className="workflow-steps">
        <h3>Workflow Steps:</h3>
        <ol>
          {response.steps.map((step, idx) => (
            <li key={idx}>
              <span>{step.action}</span> - <span className={`status-${step.status}`}>{step.status}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

export default ResultsDisplay;
