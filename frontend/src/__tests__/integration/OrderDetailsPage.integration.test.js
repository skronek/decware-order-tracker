import React from 'react';
import { render, screen } from '@testing-library/react';
import OrderDetailsPage from '../../pages/OrderDetailsPage';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme';
import { getOrder } from '../../features/orders/api/get-order';

// Use the real router; src/__mocks__/react-router-dom.js has no MemoryRouter or useParams
jest.unmock('react-router-dom');
jest.mock('../../features/orders/api/get-order');

const renderAt = (route) => render(
  <ThemeProvider theme={theme}>
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/orders/:orderId" element={<OrderDetailsPage />} />
      </Routes>
    </MemoryRouter>
  </ThemeProvider>
);

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
  test('loads and displays the order from the URL parameter', async () => {
    getOrder.mockResolvedValue(order(123));
    renderAt('/orders/123');

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Order Details/i);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    expect(await screen.findByRole('heading', { name: 'ZMA' })).toBeInTheDocument();
    expect(getOrder).toHaveBeenCalledWith('123');
    expect(screen.getByTestId('status-chip')).toHaveTextContent('On Bench');
  });

  test('says the order was not found when the API returns 404', async () => {
    // getOrder rejects with the message lib/api-client.js sets on a 404
    getOrder.mockRejectedValue(new Error('Order not found.'));
    renderAt('/orders/999');

    expect(await screen.findByTestId('error-message')).toHaveTextContent('Order not found.');
    expect(getOrder).toHaveBeenCalledWith('999');
  });
});
