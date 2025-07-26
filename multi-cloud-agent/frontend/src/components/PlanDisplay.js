import React from 'react';

function PlanDisplay({ plan, onConfirm, loading }) {
  return (
    <div className="plan-display">
      <h3>Execution Plan</h3>
      <p>The agent has generated the following plan. Please review and confirm.</p>
      <ul className="plan-steps">
        {plan.map((step, idx) => (
          <li key={idx}>
            <strong>Step {step.step}:</strong> {step.action.replace('_', ' ')} on {step.cloud.toUpperCase()}
            <pre>{JSON.stringify(step.params, null, 2)}</pre>
          </li>
        ))}
      </ul>
      <button onClick={onConfirm} disabled={loading} className="confirm-button">
        {loading ? 'Executing...' : 'Confirm and Execute'}
      </button>
    </div>
  );
}

export default PlanDisplay;
