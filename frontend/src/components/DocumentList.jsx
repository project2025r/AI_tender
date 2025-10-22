import React, { useState, useEffect } from 'react';
import { getDocuments, deleteDocument } from '../services/api';

const DocumentList = ({ onDocumentSelect, selectedDocuments, onDocumentsChange }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await getDocuments();
      setDocuments(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    
    // Poll for document status updates every 3 seconds
    const interval = setInterval(fetchDocuments, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (onDocumentsChange) {
      onDocumentsChange(documents);
    }
  }, [documents]);

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await deleteDocument(documentId);
      setDocuments(documents.filter(doc => doc.id !== documentId));
      
      // Remove from selected if it was selected
      if (selectedDocuments.includes(documentId)) {
        onDocumentSelect(documentId);
      }
    } catch (err) {
      alert('Failed to delete document');
      console.error(err);
    }
  };

  const handleCheckboxChange = (documentId) => {
    onDocumentSelect(documentId);
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      ready: 'status-ready',
      processing: 'status-processing',
      failed: 'status-failed'
    };

    const statusLabels = {
      ready: '✓ Ready',
      processing: '⏳ Processing...',
      failed: '✗ Failed'
    };

    return (
      <span className={`status-badge ${statusClasses[status]}`}>
        {statusLabels[status]}
      </span>
    );
  };

  const getFileIcon = (fileType) => {
    const icons = {
      pdf: '📕',
      docx: '📘',
      doc: '📘',
      xlsx: '📗',
      xls: '📗'
    };
    return icons[fileType] || '📄';
  };

  if (loading && documents.length === 0) {
    return <div className="loading">Loading documents...</div>;
  }

  if (error && documents.length === 0) {
    return <div className="error-message">{error}</div>;
  }

  if (documents.length === 0) {
    return (
      <div className="empty-state">
        <p>No documents uploaded yet</p>
        <p className="empty-hint">Upload a document to get started</p>
      </div>
    );
  }

  return (
    <div className="document-list">
      <div className="document-list-header">
        <h3>Documents ({documents.length})</h3>
        {selectedDocuments.length > 0 && (
          <span className="selected-count">
            {selectedDocuments.length} selected
          </span>
        )}
      </div>
      
      <div className="documents-container">
        {documents.map((doc) => (
          <div key={doc.id} className={`document-item ${selectedDocuments.includes(doc.id) ? 'selected' : ''}`}>
            <div className="document-checkbox">
              <input
                type="checkbox"
                checked={selectedDocuments.includes(doc.id)}
                onChange={() => handleCheckboxChange(doc.id)}
                disabled={doc.status !== 'ready'}
              />
            </div>
            
            <div className="document-info">
              <div className="document-name">
                <span className="file-icon">{getFileIcon(doc.file_type)}</span>
                <span className="filename" title={doc.filename}>{doc.filename}</span>
              </div>
              
              <div className="document-meta">
                <span className="upload-date">
                  {new Date(doc.upload_date).toLocaleDateString()}
                </span>
                <span className="chunk-count">
                  {doc.total_chunks > 0 ? `${doc.total_chunks} chunks` : ''}
                </span>
              </div>
              
              <div className="document-status">
                {getStatusBadge(doc.status)}
              </div>
              
              {doc.error_message && (
                <div className="error-message small">
                  {doc.error_message}
                </div>
              )}
            </div>
            
            <div className="document-actions">
              <button
                className="btn-delete"
                onClick={() => handleDelete(doc.id)}
                title="Delete document"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentList;


