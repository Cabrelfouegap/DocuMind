import axios from 'axios';

const api = axios.create({ 
  baseURL: '/api' 
});

export const fetchDocuments = () => {
  return api.get('/documents');
};

export const uploadDocument = (formData) => {
  return api.post('/documents/upload', formData);
};

export const updateDocument = (id, donnees) => {
  return api.patch('/documents/' + id, donnees);
};

export const analyzeDocument = (id) => {
  return api.post('/documents/' + id + '/analyze');
};
