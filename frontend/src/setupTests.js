// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// Mock window.matchMedia
window.matchMedia = window.matchMedia || function() {
  return {
    matches: false,
    addListener: function() {},
    removeListener: function() {},
    addEventListener: function() {},
    removeEventListener: function() {}
  };
};

// Mock MutationObserver
global.MutationObserver = class {
  disconnect() {}
  observe(element, initObject) {}
};

// Mock axios
const mockAxios = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  },
  create: () => mockAxios,
};

jest.mock('axios', () => mockAxios);

beforeEach(() => {
  jest.clearAllMocks();
});
