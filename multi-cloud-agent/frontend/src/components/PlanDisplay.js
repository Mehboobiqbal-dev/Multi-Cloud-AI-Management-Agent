import React from 'react';

function PlanDisplay({ plan, onConfirm, loading }) {
  return (
    <div className="plan-display">
      <h3>Execution Plan</h3>
      <p>The agent has generated the following plan. Please review and confirm to proceed.</p>
      <ol className="plan-steps">
        {plan.map((step, idx) => (
          <li key={idx}>
            <div className="step-header">
              <span className="step-number">Step {step.step}</span>
              <span className="step-action">{step.action.replace(/_/g, ' ')}</span>
              <span className={`step-cloud ${step.cloud}`}>{step.cloud.toUpperCase()}</span>
            </div>
            {step.params && Object.keys(step.params).length > 0 && (
              <div className="step-params">
                <strong>Parameters:</strong>
                <pre>{JSON.stringify(step.params, null, 2)}</pre>
              </div>
            )}
          </li>
        ))}
      </ol>
      <button onClick={onConfirm} disabled={loading} className="confirm-button">
        {loading ? 'Executing...' : 'Confirm and Execute Plan'}
      </button>
    </div>
  );
}

export default PlanDisplay;
