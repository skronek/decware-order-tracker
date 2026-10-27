import React from 'react';
import { render, screen } from '@testing-library/react';
import OrderDetailsPage from '../../pages/OrderDetailsPage';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme';
import { useOrderDetails } from '../../hooks/useOrderDetails';

// Use the real router; src/__mocks__/react-router-dom.js has no MemoryRouter or useParams
jest.unmock('react-router-dom');
jest.mock('../../hooks/useOrderDetails');

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

const order = (id) => ({
  id,
  customer_name: 'Test Customer',
  origin: 'WA',
  model: 'ZMA',
  base: '',
  volts: '120V',
  quantity: 1,
  options: '',
  status: 'ON_BENCH',
  order_date: '2026-01-15T12:00:00Z',
  removed_at: null,
  status_history: [],
  estimated_completion: null,
});

describe('OrderDetailsPage Integration Tests', () => {
  test('should load and display the order from the URL parameter', () => {
    useOrderDetails.mockReturnValue({ orderDetails: order(123), loading: false, error: null });
    renderWithProviders(<OrderDetailsPage />);

    expect(useOrderDetails).toHaveBeenCalledWith('123');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Order Details/i);
    expect(screen.getByRole('heading', { name: 'ZMA' })).toBeInTheDocument();
    expect(screen.getByTestId('status-chip')).toHaveTextContent('On Bench');
  });

  test('should load a different order when the URL changes', () => {
    useOrderDetails.mockReturnValue({ orderDetails: null, loading: false, error: null });
    renderWithProviders(<OrderDetailsPage />, { route: '/orders/999' });

    expect(useOrderDetails).toHaveBeenCalledWith('999');
    expect(screen.getByText('Order not found.')).toBeInTheDocument();
  });
});
