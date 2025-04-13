import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { OrderDetails } from '../OrderDetails';
import { useOrderDetails } from '../../hooks/useOrderDetails';

// Mock the hooks
jest.mock('../../hooks/useOrderDetails');
jest.mock('react-router-dom', () => ({
  useParams: () => ({ orderId: '1' }),
}));

describe('OrderDetails', () => {
  const mockOrderDetails = {
    id: 1,
    customerName: 'John Doe',
    model: 'ZEN',
    status: 'NEW',
    orderDate: '2025-04-10',
    estimatedCompletion: {
      daysRemaining: 45,
      date: '2025-05-25',
      confidenceLevel: 0.85,
    },
    statusHistory: [
      {
        timestamp: '2025-04-01T10:00:00Z',
        status: 'NEW',
      },
      {
        timestamp: '2025-04-05T14:30:00Z',
        status: 'IN_PROGRESS',
      },
    ],
  };

  beforeEach(() => {
    useOrderDetails.mockReturnValue({
      orderDetails: mockOrderDetails,
      loading: false,
      error: null,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders customer information', () => {
    render(<OrderDetails />);
    expect(screen.getByText('Customer Information')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByTestId('order-date')).toHaveTextContent('4/10/2025');
  });

  it('renders product information', () => {
    render(<OrderDetails />);
    expect(screen.getByText('Product Information')).toBeInTheDocument();
    expect(screen.getByText('ZEN')).toBeInTheDocument();
    const mainDetailsSection = screen.getByTestId('order-details-main');
    expect(within(mainDetailsSection).getByTestId('status-chip')).toHaveTextContent('NEW');
  });

  it('renders estimated completion information', () => {
    render(<OrderDetails />);
    expect(screen.getByText('Estimated Completion')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByTestId('completion-date')).toHaveTextContent('5/25/2025');
    expect(screen.getByTestId('confidence-level')).toHaveTextContent('85%');
  });

  it('shows loading state', () => {
    useOrderDetails.mockReturnValue({
      orderDetails: null,
      loading: true,
      error: null,
    });

    render(<OrderDetails />);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const error = 'Failed to fetch order details';
    useOrderDetails.mockReturnValue({
      orderDetails: null,
      loading: false,
      error,
    });

    render(<OrderDetails />);
    expect(screen.getByTestId('error-message')).toHaveTextContent(error);
  });

  it('shows not found message when no order details', () => {
    useOrderDetails.mockReturnValue({
      orderDetails: null,
      loading: false,
      error: null,
    });

    render(<OrderDetails />);
    expect(screen.getByText('Order not found.')).toBeInTheDocument();
  });

  it('renders the status history timeline', () => {
    render(<OrderDetails />);

    const timelineSection = screen.getByTestId('status-history-timeline');

    expect(within(timelineSection).getByText('Status History')).toBeInTheDocument();
    expect(within(timelineSection).getByText('NEW')).toBeInTheDocument();
    expect(within(timelineSection).getByText('IN_PROGRESS')).toBeInTheDocument();
    expect(within(timelineSection).getByText('4/1/2025')).toBeInTheDocument();
    expect(within(timelineSection).getByText('4/5/2025')).toBeInTheDocument();

    const mainDetailsSection = screen.getByTestId('order-details-main');
    expect(within(mainDetailsSection).getByTestId('status-chip')).toHaveTextContent(mockOrderDetails.status);
  });
});
