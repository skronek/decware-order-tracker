import React from 'react';
import { render, screen, within, fireEvent } from '@testing-library/react';
import { OrderDetails } from '../order-details';
import { getOrder } from '../../api/get-order';
import { getSavedOrderIds } from '../../../../utils/storage';

jest.mock('../../api/get-order');
jest.mock('react-router-dom', () => ({
  useParams: () => ({ orderId: '14775' }),
  Link: require('react').forwardRef(({ to, children, ...rest }, ref) => <a ref={ref} href={to} {...rest}>{children}</a>),
}));

// Shaped like a real /api/orders/orders/<id>/ response
const mockOrder = {
  id: 14775,
  customer_name: 'Weineng P.',
  origin: 'WA',
  model: 'SE34I.6',
  base: 'Walnut',
  volts: '120V',
  quantity: 1,
  options: 'Custom Options Requested',
  status: 'NEW',
  order_date: '2026-10-14T18:25:00Z',
  removed_at: null,
  status_history: [
    { id: 3436, order: 14775, previous_status: null, new_status: 'NEW', timestamp: '2026-10-27T20:25:29Z', is_observed: false },
  ],
  estimated_completion: {
    estimated_date: '2030-08-21',
    range_end_date: '2032-09-06',
    days_remaining: 1394,
    queue_position: 2003,
    confidence_level: 'LOW',
    explanation: 'Your order is #2,004 in the build queue.',
  },
};

// Renders and waits for the order to load
const renderWith = async (order) => {
  getOrder.mockResolvedValue(order);
  render(<OrderDetails />);
  await screen.findByTestId('order-details-main');
};

describe('OrderDetails', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('fetches the order from the URL', async () => {
    await renderWith(mockOrder);
    expect(getOrder).toHaveBeenCalledWith('14775');
  });

  it('renders the order information', async () => {
    await renderWith(mockOrder);
    const main = screen.getByTestId('order-details-main');
    expect(within(main).getByText('Weineng P.')).toBeInTheDocument();
    expect(within(main).getByText('WA')).toBeInTheDocument();
    expect(within(main).getByRole('heading', { name: 'SE34I.6' })).toBeInTheDocument();
    expect(within(main).getAllByText('SE34I.6')).toHaveLength(2); // heading and Model field
    expect(within(main).getByText('Walnut')).toBeInTheDocument();
    expect(within(main).getByText('120V')).toBeInTheDocument();
    expect(within(main).getByText('Custom Options Requested')).toBeInTheDocument();
    expect(screen.getByTestId('order-date')).toHaveTextContent(new Date('2026-10-14T18:25:00Z').toLocaleDateString());
    expect(within(main).getByTestId('status-chip')).toHaveTextContent('New');
  });

  it('renders the estimate', async () => {
    await renderWith(mockOrder);
    const estimate = screen.getByTestId('estimate');
    const start = new Date(2030, 7, 21).toLocaleDateString();
    const end = new Date(2032, 8, 6).toLocaleDateString();
    expect(within(estimate).getByTestId('completion-date')).toHaveTextContent(`${start} – ${end}`);
    expect(within(estimate).getByTestId('queue-position')).toHaveTextContent('#2,004');
    expect(within(estimate).getByTestId('confidence-level')).toHaveTextContent('Low');
    expect(within(estimate).getByText('Your order is #2,004 in the build queue.')).toBeInTheDocument();
  });

  it('leaves out the queue position for orders being built', async () => {
    await renderWith({ ...mockOrder, status: 'ON_BENCH', estimated_completion: { ...mockOrder.estimated_completion, queue_position: null } });
    expect(screen.queryByTestId('queue-position')).not.toBeInTheDocument();
    expect(screen.getByTestId('status-chip')).toHaveTextContent('On Bench');
  });

  it('says a finished order has passed QC instead of estimating it', async () => {
    await renderWith({ ...mockOrder, status: 'PASSED_QC_AWAITING_PAYMENT', estimated_completion: null });
    expect(screen.getByTestId('estimate')).toHaveTextContent('This order has passed quality control.');
    expect(screen.queryByTestId('completion-date')).not.toBeInTheDocument();
  });

  it('notes when an order has dropped off Decware\'s list', async () => {
    await renderWith({ ...mockOrder, status: 'TESTING', estimated_completion: null, removed_at: '2026-09-01T12:00:00Z' });
    expect(screen.getByTestId('removed-notice')).toHaveTextContent(new Date('2026-09-01T12:00:00Z').toLocaleDateString());
    expect(screen.getByTestId('estimate')).not.toHaveTextContent('No estimate yet');
  });

  it('says when an active order has no estimate yet', async () => {
    await renderWith({ ...mockOrder, estimated_completion: null });
    expect(screen.getByTestId('estimate')).toHaveTextContent('No estimate yet');
    expect(screen.queryByTestId('removed-notice')).not.toBeInTheDocument();
  });

  it('renders the status history timeline', async () => {
    await renderWith(mockOrder);
    const timeline = screen.getByTestId('status-history-timeline');
    expect(within(timeline).getByText('Status History')).toBeInTheDocument();
    expect(timeline).toHaveTextContent('First seen');
  });

  it('saves and unsaves the order', async () => {
    await renderWith(mockOrder);
    fireEvent.click(screen.getByTestId('save-button'));
    expect(getSavedOrderIds()).toEqual(['14775']);
    expect(screen.getByTestId('save-button')).toHaveTextContent('Unsave Order');

    fireEvent.click(screen.getByTestId('save-button'));
    expect(getSavedOrderIds()).toEqual([]);
    expect(screen.getByTestId('save-button')).toHaveTextContent('Save Order');
  });

  it('shows an order saved under a numeric ID as saved', async () => {
    localStorage.setItem('savedOrderIds', JSON.stringify([14775]));
    await renderWith(mockOrder);
    expect(screen.getByTestId('save-button')).toHaveTextContent('Unsave Order');
  });

  it('links back to search', async () => {
    await renderWith(mockOrder);
    expect(screen.getByRole('link', { name: /Back to search/i })).toHaveAttribute('href', '/search');
  });

  it('shows the loading state, not "not found", until the order arrives', () => {
    getOrder.mockReturnValue(new Promise(() => {}));
    render(<OrderDetails />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    expect(screen.queryByText('Order not found.')).not.toBeInTheDocument();
  });

  it('shows the error message when the request fails', async () => {
    // lib/api-client.js sets this message on a 404
    getOrder.mockRejectedValue(new Error('Order not found.'));
    render(<OrderDetails />);
    expect(await screen.findByTestId('error-message')).toHaveTextContent('Order not found.');
  });
});
