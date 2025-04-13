const mockNavigate = jest.fn();

module.exports = {
  BrowserRouter: ({ children }) => children,
  Routes: ({ children }) => children,
  Route: () => null,
  useNavigate: () => mockNavigate,
};
