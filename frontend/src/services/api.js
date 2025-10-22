import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Document APIs
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
};

export const getDocuments = async () => {
  return api.get('/documents');
};

export const getDocument = async (documentId) => {
  return api.get(`/documents/${documentId}`);
};

export const deleteDocument = async (documentId) => {
  return api.delete(`/documents/${documentId}`);
};

// Chat API
export const sendChatMessage = async (message, documentIds = null, topK = 5) => {
  return api.post('/chat', {
    message,
    document_ids: documentIds,
    top_k: topK,
  });
};

// Health check
export const checkHealth = async () => {
  return api.get('/health');
};

export default api;


