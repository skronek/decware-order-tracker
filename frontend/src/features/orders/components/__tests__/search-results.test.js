import React from 'react';
import { render, screen, within, fireEvent } from '@testing-library/react';
import { SearchResults } from '../search-results';

describe('SearchResults', () => {
  const mockOrder = {
    id: 123,
    customer_name: 'Test Customer',
    origin: 'USA',
    model: 'UFO',
    base: 'STD',
    volts: '120V',
    order_date: '2023-01-15T10:00:00Z',
    status: 'ON_BENCH',
    estimated_completion: {
      days_remaining: 5,
      estimated_date: '2023-01-20T10:00:00Z',
    },
  };

  it('renders nothing when results are null (initial state)', () => {
    const { container } = render(<SearchResults results={null} loading={false} error={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders loading indicator when loading is true', () => {
    render(<SearchResults results={null} loading={true} error={null} />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('renders error message when error is provided', () => {
    const errorMessage = 'Failed to fetch results';
    render(<SearchResults results={null} loading={false} error={errorMessage} />);
    expect(screen.getByTestId('error-message')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders "Order not found" message when results array is empty', () => {
    render(<SearchResults results={[]} loading={false} error={null} />);
    expect(screen.getByText(/Order not found/i)).toBeInTheDocument();
  });

  it('renders the best guess and likely range without shifting the dates', () => {
    const rangedOrder = {
      ...mockOrder,
      estimated_completion: {
        range_start_date: '2027-03-01', estimated_date: '2027-03-03', range_end_date: '2027-03-10', confidence_level: 'LOW',
      },
    };
    render(<SearchResults results={[rangedOrder]} loading={false} error={null} />);

    const start = new Date(2027, 2, 1).toLocaleDateString();
    const best = new Date(2027, 2, 3).toLocaleDateString();
    const end = new Date(2027, 2, 10).toLocaleDateString();
    expect(screen.getByText(`${best} (likely ${start} – ${end})`, { exact: false })).toBeInTheDocument();
  });

  it('renders the estimate explanation', () => {
    const explanation = 'Your order is #2 in the build queue.';
    const explainedOrder = {
      ...mockOrder,
      estimated_completion: { estimated_date: '2027-03-03', range_end_date: '2027-03-10', explanation },
    };
    render(<SearchResults results={[explainedOrder]} loading={false} error={null} />);

    expect(screen.getByText(explanation)).toBeInTheDocument();
  });

  it('renders order details when a single result is provided', () => {
    render(<SearchResults results={[mockOrder]} loading={false} error={null} />);

    expect(screen.getByText('Test Customer')).toBeInTheDocument();
    expect(screen.getByText('UFO')).toBeInTheDocument();
    expect(screen.getByText('USA')).toBeInTheDocument();
    expect(screen.getByText('STD')).toBeInTheDocument();
    expect(screen.getByText('120V')).toBeInTheDocument();
    expect(screen.getByText('On Bench')).toBeInTheDocument();
    expect(screen.getByText(new Date(mockOrder.estimated_completion.estimated_date).toLocaleDateString())).toBeInTheDocument();

    expect(screen.getByRole('button', { name: /Track this order/i })).toBeInTheDocument();
  });

  it('links to the order details page', () => {
    render(<SearchResults results={[mockOrder]} loading={false} error={null} />);
    expect(screen.getByRole('link', { name: /View details/i })).toHaveAttribute('href', '/orders/123');
  });

  it('renders every order when several match', () => {
    render(<SearchResults results={[mockOrder, { ...mockOrder, id: 456, model: 'ZMA' }]} loading={false} error={null} />);
    expect(screen.getByText('2 orders match these details.')).toBeInTheDocument();

    const second = screen.getByTestId('order-summary-456');
    expect(within(second).getByText('ZMA')).toBeInTheDocument();
    expect(within(second).getByRole('link', { name: /View details/i })).toHaveAttribute('href', '/orders/456');
    expect(screen.getAllByRole('button', { name: /Track this order/i })).toHaveLength(2);
  });

  it('passes the picked order to onTrack', () => {
    const onTrack = jest.fn();
    const second = { ...mockOrder, id: 456 };
    render(<SearchResults results={[mockOrder, second]} loading={false} error={null} onTrack={onTrack} />);

    fireEvent.click(within(screen.getByTestId('order-summary-456')).getByRole('button', { name: /Track this order/i }));

    expect(onTrack).toHaveBeenCalledWith(second);
  });

  it('disables orders that are already tracked', () => {
    render(<SearchResults results={[mockOrder, { ...mockOrder, id: 456 }]} loading={false} error={null} trackedIds={['123']} />);

    expect(within(screen.getByTestId('order-summary-123')).getByRole('button', { name: /Tracking/i })).toBeDisabled();
    expect(within(screen.getByTestId('order-summary-456')).getByRole('button', { name: /Track this order/i })).toBeEnabled();
  });
});
