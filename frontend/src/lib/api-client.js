import axios from 'axios';

// The one HTTP client for the app. In production the API is same-origin; in
// development the CRA proxy ("proxy" in package.json) forwards /api to Django on :8000.
export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// A message fit to show the user. DRF puts its error text in `detail`.
export const getErrorMessage = (error) => {
  if (error.response?.status === 404) return 'Order not found.';
  return error.response?.data?.detail || error.message || 'Something went wrong. Please try again.';
};

// Rewrite every failed request's message once, here, so callers can show error.message.
// The original response stays on the error (e.g. error.response.status).
export const handleResponseError = (error) => {
  error.message = getErrorMessage(error);
  return Promise.reject(error);
};

api.interceptors.response.use((response) => response, handleResponseError);
