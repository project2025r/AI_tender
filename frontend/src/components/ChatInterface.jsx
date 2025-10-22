import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendChatMessage } from '../services/api';

const ChatInterface = ({ selectedDocuments, documents }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;

    // Check if any documents are ready
    const readyDocs = documents.filter(doc => doc.status === 'ready');
    if (readyDocs.length === 0) {
      setError('Please upload and wait for at least one document to be processed before chatting.');
      return;
    }

    // Add user message
    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      // Send to API
      const documentIds = selectedDocuments.length > 0 ? selectedDocuments : null;
      const response = await sendChatMessage(inputMessage, documentIds, 5);

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get response');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Clear all messages?')) {
      setMessages([]);
      setError(null);
    }
  };

  const getSelectedDocumentNames = () => {
    if (selectedDocuments.length === 0) {
      return 'all documents';
    }
    
    const selectedDocs = documents.filter(doc => selectedDocuments.includes(doc.id));
    return selectedDocs.map(doc => doc.filename).join(', ');
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat with Documents</h2>
        {documents.length > 0 && (
          <div className="chat-context">
            Searching in: <strong>{getSelectedDocumentNames()}</strong>
          </div>
        )}
        {messages.length > 0 && (
          <button className="btn-clear" onClick={handleClearChat}>
            Clear Chat
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>👋 Welcome to the Tender Document Chatbot!</p>
            <p>Upload documents and ask questions about them.</p>
            <div className="example-queries">
              <p><strong>Example questions:</strong></p>
              <ul>
                <li>What is the project scope?</li>
                <li>What are the key deadlines?</li>
                <li>What are the technical requirements?</li>
                <li>Summarize the main deliverables</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-header">
                <strong>{message.role === 'user' ? '👤 You' : '🤖 Assistant'}</strong>
                <span className="timestamp">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              
              <div className="message-content">
                {message.role === 'assistant' ? (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                ) : (
                  <p>{message.content}</p>
                )}
              </div>

              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  <details>
                    <summary>📚 Sources ({message.sources.length})</summary>
                    <div className="sources-list">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-header">
                            <strong>{source.document_name}</strong>
                            {source.page_number && <span> - Page {source.page_number}</span>}
                            {source.sheet_name && <span> - Sheet: {source.sheet_name}</span>}
                            <span className="source-score"> (Score: {source.score.toFixed(3)})</span>
                          </div>
                          <div className="source-text">
                            {source.chunk_text}
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
            </div>
          ))
        )}
        
        {loading && (
          <div className="message assistant loading-message">
            <div className="message-header">
              <strong>🤖 Assistant</strong>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question about your documents..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          disabled={loading || documents.filter(d => d.status === 'ready').length === 0}
        />
        <button
          type="submit"
          className="btn-send"
          disabled={loading || !inputMessage.trim() || documents.filter(d => d.status === 'ready').length === 0}
        >
          {loading ? '⏳' : '📤'} Send
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;


