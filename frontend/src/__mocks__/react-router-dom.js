const React = require('react');

const mockNavigate = jest.fn();

module.exports = {
  BrowserRouter: ({ children }) => children,
  Routes: ({ children }) => children,
  Route: () => null,
  Link: React.forwardRef(({ to, children, ...rest }, ref) => React.createElement('a', { ref, href: to, ...rest }, children)),
  useNavigate: () => mockNavigate,
};
