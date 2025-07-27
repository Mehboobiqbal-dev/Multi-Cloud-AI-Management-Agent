import React, { useState, useEffect } from 'react';
import api from '../services/api';

function CredentialsModal({ isOpen, onClose }) {
  const [provider, setProvider] = useState('aws');
  const [formValues, setFormValues] = useState({});
  const [credentials, setCredentials] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetchCredentials();
    }
  }, [isOpen]);

  const fetchCredentials = async () => {
    try {
      const creds = await api.getCredentials();
      setCredentials(creds);
    } catch (error) {
      console.error('Failed to fetch credentials:', error);
    }
  };

  const handleChange = (e) => {
    setFormValues({
      ...formValues,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.saveCredentials({ provider, ...formValues });
    fetchCredentials();
    setFormValues({});
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
              <input name="access_key" placeholder="AWS Access Key" onChange={handleChange} value={formValues.access_key || ''} />
              <input name="secret_key" placeholder="AWS Secret Key" onChange={handleChange} value={formValues.secret_key || ''} />
            </>
          )}
          {provider === 'azure' && (
            <>
              <input name="azure_subscription_id" placeholder="Azure Subscription ID" onChange={handleChange} value={formValues.azure_subscription_id || ''} />
              <input name="azure_client_id" placeholder="Azure Client ID" onChange={handleChange} value={formValues.azure_client_id || ''} />
              <input name="azure_client_secret" placeholder="Azure Client Secret" onChange={handleChange} value={formValues.azure_client_secret || ''} />
              <input name="azure_tenant_id" placeholder="Azure Tenant ID" onChange={handleChange} value={formValues.azure_tenant_id || ''} />
            </>
          )}
          {provider === 'gcp' && (
            <>
              <input name="gcp_project_id" placeholder="GCP Project ID" onChange={handleChange} value={formValues.gcp_project_id || ''} />
              <textarea name="gcp_credentials_json" placeholder="GCP Credentials JSON" onChange={handleChange} value={formValues.gcp_credentials_json || ''} />
            </>
          )}
          <button type="submit">Save</button>
        </form>
        <div className="credentials-list">
          <h3>Existing Credentials:</h3>
          <ul>
            {credentials.map((cred) => (
              <li key={cred.id}>{cred.provider}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default CredentialsModal;
