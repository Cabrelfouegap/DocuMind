import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

export const fetchValidationResults = () => {
  return api.get('/validation/results');
};

