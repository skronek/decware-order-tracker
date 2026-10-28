import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from '../HomePage';
import { getSavedOrderIds } from '../../utils/storage';
import { getOrder } from '../../features/orders/api/get-order';

jest.mock('../../features/orders/api/get-order');
jest.mock('../../utils/storage', () => ({
  getSavedOrderIds: jest.fn(),
  removeOrderId: jest.fn(),
}));

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

describe('HomePage saved orders', () => {
  beforeEach(() => {
    getSavedOrderIds.mockReturnValue(['14775']);
    getOrder.mockResolvedValue(savedOrder);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('fetches each saved order and links to its details page', async () => {
    render(<HomePage />);

    const card = await screen.findByTestId('saved-order-14775');
    expect(getOrder).toHaveBeenCalledWith('14775');
    expect(card).toHaveTextContent('On Bench');
    expect(screen.getByRole('link', { name: /View details/i })).toHaveAttribute('href', '/orders/14775');
  });
});
