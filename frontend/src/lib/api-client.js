import axios from 'axios';

// The one HTTP client for the app. In production the API is same-origin; in
// development the CRA proxy ("proxy" in package.json) forwards /api to Django on :8000.
export const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});
