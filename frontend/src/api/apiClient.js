import axios from 'axios';

// Define the base URL for the API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// Create an Axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Add any other default headers here (e.g., Authorization)
  },
});

// You can add interceptors here if needed (e.g., for error handling or token refresh)
// apiClient.interceptors.response.use(...);

export default apiClient;
