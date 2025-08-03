import React from 'react';

function PlanDisplay({ plan, loading }) {
  return (
    <div className="plan-display">
      <h3>Execution Plan</h3>
      <p>The agent has generated the following plan. Please review and confirm to proceed.</p>
      <ol className="plan-steps">
        {plan.map((step, idx) => (
          <li key={idx}>
            <div className="step-header">
              <span className="step-number">Step {step.step}</span>
              <span className="step-action">
                {typeof step.action === 'string' 
                  ? step.action.replace(/_/g, ' ')
                  : typeof step.action === 'object' && step.action.name
                    ? step.action.name.replace(/_/g, ' ')
                    : 'Unknown action'}
              </span>
              {step.cloud && (
                <span className={`step-cloud ${step.cloud}`}>{step.cloud.toUpperCase()}</span>
              )}
            </div>
            {step.params && Object.keys(step.params).length > 0 && (
              <div className="step-params">
                <strong>Parameters:</strong>
                <pre>
                  {typeof step.params === 'object' 
                    ? JSON.stringify(step.params, (key, value) => {
                        // Handle nested objects that might cause circular references
                        if (typeof value === 'object' && value !== null) {
                          try {
                            JSON.stringify(value);
                            return value;
                          } catch (error) {
                            return '[Complex Object]';
                          }
                        }
                        return value;
                      }, 2)
                    : String(step.params)
                  }
                </pre>
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

export default PlanDisplay;
