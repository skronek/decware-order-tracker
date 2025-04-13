// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// --- MOCK API HOOK GLOBALLY ---
// Mock the useApi hook to prevent actual network calls during tests
/* jest.mock('./hooks/useApi', () => ({
  useApi: jest.fn(() => ({
    get: jest.fn().mockResolvedValue({ data: {} }), // Default successful response (empty)
    post: jest.fn().mockResolvedValue({ data: {} }), // Default successful response (empty)
    loading: false,
    error: null,
    clearError: jest.fn(),
  })),
})); */ // Removing global mock

// --- END MOCK ---

// Mock window.matchMedia
window.matchMedia = window.matchMedia || function() {
  return {
    matches: false,
    addListener: function() {},
    removeListener: function() {}
  };
};

// Mock MutationObserver
global.MutationObserver = class {
  constructor(callback) {}
  disconnect() {}
  observe(element, initObject) {}
};

// Mock axios
const mockAxios = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  create: () => mockAxios,
};

jest.mock('axios', () => mockAxios);

beforeEach(() => {
  jest.clearAllMocks();
});
