import React from 'react';
import { render, screen } from '@testing-library/react';
import OrderDetailsPage from '../../pages/OrderDetailsPage';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme';

// Use the real router; src/__mocks__/react-router-dom.js has no MemoryRouter or useParams
jest.unmock('react-router-dom');

// Wrap component with necessary providers for testing
const renderWithProviders = (ui, { route = '/orders/123' } = {}) => {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/orders/:orderId" element={ui} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );
};

describe('OrderDetailsPage Integration Tests', () => {
  test('should display order ID from URL parameter', () => {
    // Render the OrderDetailsPage component with a valid order ID route
    renderWithProviders(<OrderDetailsPage />);
    
    // Use more flexible queries
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Order Details/i);
    expect(screen.getByText(/123/)).toBeInTheDocument();
  });
  
  test('should display different order ID when URL changes', () => {
    // Render the OrderDetailsPage component with a non-existent order ID route
    renderWithProviders(<OrderDetailsPage />, { route: '/orders/999' });
    
    // Use more flexible queries
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Order Details/i);
    expect(screen.getByText(/999/)).toBeInTheDocument();
  });
});
