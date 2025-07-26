import React, { useState } from 'react';
import api from '../services/api';

function CredentialsModal({ isOpen, onClose }) {
  const [provider, setProvider] = useState('aws');
  const [formValues, setFormValues] = useState({});

  const handleChange = (e) => {
    setFormValues({
      ...formValues,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.saveCredentials({ provider, ...formValues });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <button onClick={onClose} className="close-button">&times;</button>
        <h2>Manage Cloud Credentials</h2>
        <select value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="aws">AWS</option>
          <option value="azure">Azure</option>
          <option value="gcp">GCP</option>
        </select>

        <form onSubmit={handleSubmit}>
          {provider === 'aws' && (
            <>
              <input name="access_key" placeholder="AWS Access Key" onChange={handleChange} />
              <input name="secret_key" placeholder="AWS Secret Key" onChange={handleChange} />
            </>
          )}
          {provider === 'azure' && (
            <>
              <input name="azure_subscription_id" placeholder="Azure Subscription ID" onChange={handleChange} />
              <input name="azure_client_id" placeholder="Azure Client ID" onChange={handleChange} />
              <input name="azure_client_secret" placeholder="Azure Client Secret" onChange={handleChange} />
              <input name="azure_tenant_id" placeholder="Azure Tenant ID" onChange={handleChange} />
            </>
          )}
          {provider === 'gcp' && (
            <>
              <input name="gcp_project_id" placeholder="GCP Project ID" onChange={handleChange} />
              <textarea name="gcp_credentials_json" placeholder="GCP Credentials JSON" onChange={handleChange} />
            </>
          )}
          <button type="submit">Save</button>
        </form>
      </div>
    </div>
  );
}

export default CredentialsModal;
