import React, { useState, useEffect } from 'react';
import api from '../services/api';

function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const data = await api.getHistory();
        setHistory(data);
      } catch (err) {
        console.error('Failed to fetch history:', err);
      }
      setLoading(false);
    };

    fetchHistory();
  }, []);

  if (loading) {
    return <div className="loader"></div>;
  }

  return (
    <div className="history-container">
      <h2>Execution History</h2>
      {history.length === 0 ? (
        <p>No history found.</p>
      ) : (
        <ul className="history-list">
          {history.map((item) => (
            <li key={item.id} className="history-item">
              <div className="history-item-header">
                <span className="history-item-status">{item.status}</span>
                <span className="history-item-timestamp">{new Date(item.timestamp).toLocaleString()}</span>
              </div>
              <div className="history-item-plan">
                <pre>{JSON.stringify(JSON.parse(item.plan), null, 2)}</pre>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default History;
