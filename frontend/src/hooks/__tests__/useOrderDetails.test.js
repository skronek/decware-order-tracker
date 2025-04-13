import { renderHook, waitFor } from '@testing-library/react';
import { useOrderDetails } from '../useOrderDetails';
import { useApi } from '../useApi';

jest.mock('../useApi');

const mockOrderDetails = {
  id: 1,
  customerName: 'John Doe',
  model: 'ZEN',
  status: 'NEW',
  orderDate: '2025-04-10',
  estimatedCompletion: {
    daysRemaining: 45,
    date: '2025-05-25',
  },
};

const mockExecute = jest.fn();

describe('useOrderDetails', () => {
  beforeEach(() => {
    mockExecute.mockReset();

    useApi.mockReturnValue({
      execute: mockExecute.mockResolvedValue({ data: mockOrderDetails }),
      loading: false,
      error: null,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('fetches order details when orderId is provided', async () => {
    const { result } = renderHook(() => useOrderDetails('1'));

    await waitFor(() => {
      expect(result.current.orderDetails).toEqual(mockOrderDetails);
    });

    expect(mockExecute).toHaveBeenCalledWith('/orders/1');
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('handles loading state', () => {
    useApi.mockReturnValue({
      execute: jest.fn(),
      loading: true,
      error: null,
    });

    const { result } = renderHook(() => useOrderDetails('1'));

    expect(result.current.loading).toBe(true);
  });

  it('handles error state', async () => {
    const errorMessage = 'Failed to fetch order details';
    const mockError = new Error(errorMessage);

    useApi.mockReturnValueOnce({
      execute: jest.fn().mockRejectedValue(mockError),
      loading: false,
      error: errorMessage,
    });

    const { result } = renderHook(() => useOrderDetails('1'));

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });

  it('does not fetch when orderId is not provided', () => {
    const getMock = jest.fn();
    useApi.mockReturnValue({
      execute: getMock,
      loading: false,
      error: null,
    });

    renderHook(() => useOrderDetails());

    expect(getMock).not.toHaveBeenCalled();
  });
});
