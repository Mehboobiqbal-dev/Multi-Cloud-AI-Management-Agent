import React, { useState } from 'react';
import './DownloadManager.css';

const DownloadManager = ({ taskId, onClose, taskData }) => {
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);

  const formatOptions = [
    {
      value: 'json',
      label: 'JSON',
      description: 'Complete structured data with all scraped information',
      icon: '📄',
      size: 'Large'
    },
    {
      value: 'txt',
      label: 'Text',
      description: 'Clean text content including title, headings, and paragraphs',
      icon: '📝',
      size: 'Medium'
    },
    {
      value: 'csv',
      label: 'CSV',
      description: 'Structured data in spreadsheet format for analysis',
      icon: '📊',
      size: 'Medium'
    }
  ];

  const handleDownload = async () => {
    setIsDownloading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/tasks/${taskId}/download?format=${selectedFormat}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get filename from Content-Disposition header or create default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `scraped_content_${taskId}.${selectedFormat}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Close modal after successful download
      setTimeout(() => {
        onClose();
      }, 1000);

    } catch (err) {
      console.error('Error downloading file:', err);
      setError('Failed to download file. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const getPreviewContent = () => {
    if (!taskData) return 'No preview available';

    switch (selectedFormat) {
      case 'json':
        return JSON.stringify({
          url: taskData.url || 'example.com',
          title: taskData.title || 'Sample Title',
          statistics: {
            word_count: taskData.word_count || 0,
            data_size: taskData.data_size || 0
          },
          data: {
            text_content: '...',
            links: '...',
            images: '...'
          }
        }, null, 2);
      
      case 'txt':
        return `Title: ${taskData.title || 'Sample Title'}\n\nHeadings:\n- Main Section\n- Subsection\n\nContent:\nSample paragraph content...\n\nAnother paragraph...`;
      
      case 'csv':
        return `Type,Content\nTitle,"${taskData.title || 'Sample Title'}"\nHeading,"Main Section"\nParagraph,"Sample content..."\nLink,"Link Text - https://example.com"`;
      
      default:
        return 'Preview not available';
    }
  };

  return (
    <div className="download-overlay">
      <div className="download-container">
        <div className="download-header">
          <h3>📥 Download Scraped Content</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="download-content">
          <div className="format-selection">
            <h4>Choose Download Format:</h4>
            <div className="format-options">
              {formatOptions.map((option) => (
                <div 
                  key={option.value}
                  className={`format-option ${selectedFormat === option.value ? 'selected' : ''}`}
                  onClick={() => setSelectedFormat(option.value)}
                >
                  <div className="format-icon">{option.icon}</div>
                  <div className="format-info">
                    <div className="format-label">{option.label}</div>
                    <div className="format-description">{option.description}</div>
                    <div className="format-size">Size: {option.size}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="preview-section">
            <h4>Preview:</h4>
            <div className="preview-container">
              <pre className="preview-content">{getPreviewContent()}</pre>
            </div>
          </div>
          
          {taskData && (
            <div className="content-info">
              <h4>Content Information:</h4>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">URL:</span>
                  <span className="info-value">{taskData.url || 'N/A'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Title:</span>
                  <span className="info-value">{taskData.title || 'N/A'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Word Count:</span>
                  <span className="info-value">{taskData.word_count || 0}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Data Size:</span>
                  <span className="info-value">{taskData.data_size || 0} chars</span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="download-actions">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button 
            className="download-btn" 
            onClick={handleDownload}
            disabled={isDownloading}
          >
            {isDownloading ? (
              <>
                <span className="spinner"></span>
                Downloading...
              </>
            ) : (
              <>
                📥 Download {selectedFormat.toUpperCase()}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DownloadManager;