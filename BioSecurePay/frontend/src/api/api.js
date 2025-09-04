import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://biosecure-pay.onrender.com/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const register = (email, phone, password) =>
  api.post('/register', { email, phone, password });

export const login = (emailOrPhone, password) =>
  api.post('/login', { emailOrPhone, password });

export const verifyKyc = (bvn, documents) =>
  api.post('/kyc/verify', { bvn, documents });

export const enrollBiometrics = (type, template) =>
  api.post('/enroll-biometrics', { type, template });

export const listBiometrics = () => api.get('/biometrics');

export const deleteBiometric = (biometricId) =>
  api.delete(`/biometrics/${biometricId}`);

export const linkAccount = (monoCode) =>
  api.post('/accounts/link', { monoCode });

export const listAccounts = () => api.get('/accounts');

export const initiateTransaction = (amount, recipient, accountId) =>
  api.post('/transaction/initiate', { amount, recipient, accountId });

export const authenticateTransaction = (transactionId, biometricTypes, templates) =>
  api.post(`/transaction/authenticate/${transactionId}`, { biometricTypes, templates });

export const executeTransaction = (transactionId) =>
  api.post(`/transaction/execute/${transactionId}`);

export const listTransactions = () => api.get('/transactions');

export default api;
