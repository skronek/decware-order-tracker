import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SearchResults } from '../SearchResults'; 
import * as storage from '../../utils/storage'; 

jest.mock('../../utils/storage', () => ({
  getSavedOrderIds: jest.fn(),
  saveOrderIds: jest.fn(),
}));

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

  beforeEach(() => {
    storage.getSavedOrderIds.mockClear();
    storage.saveOrderIds.mockClear();
    storage.getSavedOrderIds.mockReturnValue([]); 
  });

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

  it('renders the estimated completion range without shifting the dates', () => {
    const rangedOrder = {
      ...mockOrder,
      estimated_completion: { estimated_date: '2027-03-03', range_end_date: '2027-03-10', confidence_level: 'LOW' },
    };
    render(<SearchResults results={[rangedOrder]} loading={false} error={null} />);

    const start = new Date(2027, 2, 3).toLocaleDateString();
    const end = new Date(2027, 2, 10).toLocaleDateString();
    expect(screen.getByText(`${start} – ${end}`, { exact: false })).toBeInTheDocument();
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

    expect(screen.getByRole('button', { name: /Save This Order/i })).toBeInTheDocument();
  });

  it('links to the order details page', () => {
    render(<SearchResults results={[mockOrder]} loading={false} error={null} />);
    expect(screen.getByRole('link', { name: /View details/i })).toHaveAttribute('href', '/orders/123');
  });

  it('renders "Internal error" message when multiple results are provided', () => {
    render(<SearchResults results={[mockOrder, { ...mockOrder, id: 456 }]} loading={false} error={null} />);
    expect(screen.getByText(/Internal error: Multiple orders found/i)).toBeInTheDocument();
  });

  it('shows "Save This Order" button when order is not saved', () => {
    storage.getSavedOrderIds.mockReturnValue([]); 
    render(<SearchResults results={[mockOrder]} loading={false} error={null} />);
    const saveButton = screen.getByRole('button', { name: /Save This Order/i });
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).toBeEnabled();
  });

  it('shows "Saved" button (disabled) when order is already saved', () => {
    storage.getSavedOrderIds.mockReturnValue([mockOrder.id.toString()]); 
    render(<SearchResults results={[mockOrder]} loading={false} error={null} />);
    const savedButton = screen.getByRole('button', { name: /Saved/i });
    expect(savedButton).toBeInTheDocument();
    expect(savedButton).toBeDisabled();
  });

});
