import React from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import HomePage from '../HomePage';
import { SAVED_ORDERS_KEY, getSavedOrderIds } from '../../utils/storage';
import { getOrder } from '../../features/orders/api/get-order';
import { getOrders } from '../../features/orders/api/get-orders';

jest.mock('../../features/orders/api/get-order');
jest.mock('../../features/orders/api/get-orders');

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
    expect(screen.getByText(/You aren't tracking any orders yet/)).toBeInTheDocument();
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

describe('HomePage track order dialog', () => {
  const newOrder = { ...savedOrder, id: 15001, customer_name: 'Pat Q.', model: 'ZMA', status: 'IN_QUEUE' };

  const searchFor = (fields) => {
    const dialog = screen.getByRole('dialog');
    fields.forEach(([label, value]) => {
      fireEvent.change(within(dialog).getByLabelText(label), { target: { value } });
    });
    fireEvent.click(within(dialog).getByRole('button', { name: /^Search$/ }));
  };

  const fields = [[/Customer Name/, 'Pat Q.'], [/Origin/, 'WA'], [/Model/, 'ZMA'], [/Volts/, '120V']];

  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('shows the Track order button even with nothing saved', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { name: 'Your Saved Orders' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Track order' })).toBeInTheDocument();
    expect(getOrder).not.toHaveBeenCalled();
  });

  it('searches in the dialog and adds the picked order as a card', async () => {
    getOrders.mockResolvedValue([newOrder]);
    render(<HomePage />);

    fireEvent.click(screen.getByRole('button', { name: 'Track order' }));
    searchFor(fields);

    expect(getOrders).toHaveBeenCalledWith({ customer_name: 'Pat Q.', origin: 'WA', model: 'ZMA', base: '', volts: '120V' });
    const result = await within(screen.getByRole('dialog')).findByTestId('order-summary-15001');
    fireEvent.click(within(result).getByRole('button', { name: /Track this order/i }));

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByTestId('order-summary-15001')).toHaveTextContent('Pat Q.');
    expect(getSavedOrderIds()).toEqual(['15001']);
  });

  it('adds more orders next to the saved ones and marks tracked results', async () => {
    saveIds(['14775']);
    getOrder.mockResolvedValue(savedOrder);
    getOrders.mockResolvedValue([savedOrder, newOrder]);
    render(<HomePage />);
    await screen.findByTestId('order-summary-14775');

    fireEvent.click(screen.getByRole('button', { name: 'Track order' }));
    searchFor(fields);

    const dialog = screen.getByRole('dialog');
    const saved = await within(dialog).findByTestId('order-summary-14775');
    expect(within(saved).getByRole('button', { name: /Tracking/i })).toBeDisabled();
    fireEvent.click(within(within(dialog).getByTestId('order-summary-15001')).getByRole('button', { name: /Track this order/i }));

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.getByTestId('order-summary-14775')).toBeInTheDocument();
    expect(screen.getByTestId('order-summary-15001')).toBeInTheDocument();
    expect(getSavedOrderIds()).toEqual(['14775', '15001']);
  });

  it('shows search errors inside the dialog', async () => {
    getOrders.mockRejectedValue(new Error('Server error'));
    render(<HomePage />);

    fireEvent.click(screen.getByRole('button', { name: 'Track order' }));
    searchFor(fields);

    expect(await within(screen.getByRole('dialog')).findByTestId('error-message')).toHaveTextContent('Server error');
  });
});
