import React, { isValidElement } from 'react';

function ResultsDisplay({ response }) {
  if (!response || !response.history) {
    return (
      <div className="results-display">
        <h3>Execution Results</h3>
        <div className="status-banner status-error">
          <strong>Overall Status:</strong> Invalid response data.
        </div>
      </div>
    );
  }

  return (
    <div className="results-display">
      <h3>Execution Results</h3>
      <div className={`status-banner status-${response.status}`}>
        <strong>Overall Status:</strong> {response.message}
      </div>
      
      {response.final_result && (
        <div className="final-result">
          <h4>Final Result</h4>
          <p>{typeof response.final_result === 'object' ? JSON.stringify(response.final_result) : response.final_result}</p>
        </div>
      )}

      <div className="workflow-steps">
        <h4>Detailed Workflow</h4>
        <ol>
          {response.history.map((step, idx) => (
            <li key={idx} className={`workflow-step`}>
              <span className="step-action-name">{step.action.name}</span>
              <span className="step-status">{typeof step.result === 'object' ? JSON.stringify(step.result) : step.result}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

export default ResultsDisplay;
