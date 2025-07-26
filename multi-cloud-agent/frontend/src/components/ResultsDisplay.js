import React from 'react';

const cloudIcons = {
  aws: 'fab fa-aws',
  azure: 'fab fa-microsoft',
  gcp: 'fab fa-google',
};

function ResultsDisplay({ response }) {
  const getCloudFromAction = (action) => {
    const match = action.match(/on (\w+)/);
    return match ? match[1].toLowerCase() : null;
  };

  const executionSteps = response.steps.filter(s => s.action && s.action.startsWith('Execute'));

  return (
    <div className="results-display">
      <h3>Execution Results</h3>
      <div className={`status-banner status-${response.status}`}>
        <strong>Overall Status:</strong> {response.message}
      </div>
      
      {executionSteps.length > 0 && (
        <div className="results-grid">
          {executionSteps.map((step, idx) => {
            const cloud = getCloudFromAction(step.action);
            return (
              <div key={idx} className="result-card">
                <div className="card-header">
                  <i className={`${cloudIcons[cloud] || 'fas fa-cloud'} cloud-icon ${cloud}`}></i>
                  <h4>{cloud ? cloud.toUpperCase() : 'Result'}</h4>
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
      )}

      <div className="workflow-steps">
        <h4>Detailed Workflow</h4>
        <ol>
          {response.steps.map((step, idx) => (
            <li key={idx} className={`workflow-step status-${step.status}`}>
              <span className="step-action-name">{step.action}</span>
              <span className="step-status">{step.status}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

export default ResultsDisplay;
