import axios from 'axios';

// Define the base URL for the API
const getBaseUrl = () => {
  // In local development, use the proxy setting or explicit URL
  if (['localhost', '127.0.0.1'].includes(window.location.hostname)) {
    return process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
  }
  // In production (Heroku or a custom domain), use relative URLs
  return '/api';
};

// Create an Axios instance with default configuration
const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
    // Add any other default headers here (e.g., Authorization)
  },
});

// You can add interceptors here if needed (e.g., for error handling or token refresh)
// apiClient.interceptors.response.use(...);

export default apiClient;
