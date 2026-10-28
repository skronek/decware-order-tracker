import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import HomePage from '../HomePage';
import { SAVED_ORDERS_KEY, getSavedOrderIds } from '../../utils/storage';
import { getOrder } from '../../features/orders/api/get-order';

jest.mock('../../features/orders/api/get-order');

const savedOrder = {
  id: 14775,
  customer_name: 'Weineng P.',
  origin: 'WA',
  model: 'SE34I.6',
  base: 'Walnut',
  volts: '120V',
  order_date: '2026-10-14T18:25:00Z',
  status: 'ON_BENCH',
  estimated_completion: null,
};

const saveIds = (ids) => localStorage.setItem(SAVED_ORDERS_KEY, JSON.stringify(ids));

describe('HomePage saved orders', () => {
  beforeEach(() => {
    localStorage.clear();
    saveIds(['14775']);
    getOrder.mockResolvedValue(savedOrder);
  });

  it('fetches each saved order and links to its details page', async () => {
    render(<HomePage />);

    const card = await screen.findByTestId('order-summary-14775');
    expect(getOrder).toHaveBeenCalledWith('14775');
    expect(card).toHaveTextContent('On Bench');
    expect(screen.getByRole('link', { name: /View details/i })).toHaveAttribute('href', '/orders/14775');
  });

  it('removes an order without fetching again', async () => {
    render(<HomePage />);
    await screen.findByTestId('order-summary-14775');

    fireEvent.click(screen.getByTestId('remove-order-14775'));

    expect(screen.queryByTestId('order-summary-14775')).not.toBeInTheDocument();
    expect(screen.getByText('No saved orders to display.')).toBeInTheDocument();
    expect(getSavedOrderIds()).toEqual([]);
    expect(getOrder).toHaveBeenCalledTimes(1);
  });

  it('drops saved IDs the API no longer knows', async () => {
    saveIds(['14775', '999']);
    getOrder.mockImplementation((id) => (id === '999'
      ? Promise.reject(Object.assign(new Error('Order not found.'), { response: { status: 404 } }))
      : Promise.resolve(savedOrder)));
    render(<HomePage />);

    await screen.findByTestId('order-summary-14775');
    expect(getSavedOrderIds()).toEqual(['14775']);
    expect(screen.queryByTestId('saved-order-error')).not.toBeInTheDocument();
  });

  it('keeps saved IDs that fail for other reasons and says so', async () => {
    getOrder.mockRejectedValue(new Error('Network Error'));
    render(<HomePage />);

    expect(await screen.findByTestId('saved-order-error')).toHaveTextContent('Some orders could not be loaded.');
    expect(getSavedOrderIds()).toEqual(['14775']);
  });
});
