import React, { useState } from 'react';

function PromptForm({ onSubmit, loading }) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    onSubmit(prompt);
  };

  return (
    <form onSubmit={handleSubmit} className="prompt-form">
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter your prompt here. For example: 'List all EC2 instances in us-east-1 and all VMs in Azure'"
        disabled={loading}
        rows="3"
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Submit'}
      </button>
    </form>
  );
}

export default PromptForm;
