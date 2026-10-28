import { renderHook, waitFor } from '@testing-library/react';
import { useOrderDetails } from '../use-order-details';
import { getOrder } from '../get-order';

jest.mock('../get-order');

describe('useOrderDetails', () => {
  it('is loading from the first render until the order arrives', async () => {
    getOrder.mockResolvedValue({ id: 1, model: 'ZEN' });
    const { result } = renderHook(() => useOrderDetails('1'));

    expect(result.current.loading).toBe(true);
    expect(result.current.order).toBeNull();

    await waitFor(() => expect(result.current.order).toEqual({ id: 1, model: 'ZEN' }));
    expect(getOrder).toHaveBeenCalledWith('1');
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('returns the error message when the request fails', async () => {
    getOrder.mockRejectedValue(new Error('Order not found.'));
    const { result } = renderHook(() => useOrderDetails('999'));

    await waitFor(() => expect(result.current.error).toBe('Order not found.'));
    expect(result.current.loading).toBe(false);
  });

  it('does not fetch without an order id', () => {
    const { result } = renderHook(() => useOrderDetails(undefined));
    expect(getOrder).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });
});
