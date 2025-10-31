import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';
import UserInfo from './components/UserInfo';
import { useAuth } from './contexts/AuthContext';

function AppContent() {
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const { hasPermission } = useAuth();

  const handleUploadSuccess = (uploadResponse) => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDocumentSelect = (documentId) => {
    setSelectedDocuments(prev => {
      if (prev.includes(documentId)) {
        return prev.filter(id => id !== documentId);
      } else {
        return [...prev, documentId];
      }
    });
  };

  const handleDocumentsChange = (newDocuments) => {
    setDocuments(newDocuments);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Tender Document Chatbot</h1>
          <p className="app-subtitle">Upload tender documents and chat with AI</p>
        </div>
        <UserInfo />
      </header>

      <div className="app-container">
        <aside className="sidebar">
          {hasPermission('Write') && (
            <div className="sidebar-section">
              <h2>Upload Document</h2>
              <DocumentUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          )}

          <div className="sidebar-section">
            <DocumentList
              key={refreshTrigger}
              onDocumentSelect={handleDocumentSelect}
              selectedDocuments={selectedDocuments}
              onDocumentsChange={handleDocumentsChange}
            />
          </div>
        </aside>

        <main className="main-content">
          <ChatInterface
            selectedDocuments={selectedDocuments}
            documents={documents}
          />
        </main>
      </div>
    </div>
  );
}

export default AppContent;
