import axios from 'axios';
import { getOrder } from '../get-order';
import { getOrders } from '../get-orders';

// setupTests.js mocks axios globally, and axios.create() returns that same mock,
// so axios.get here is the client's get.

describe('getOrder', () => {
  it('fetches one order by id and returns its data', async () => {
    axios.get.mockResolvedValueOnce({ data: { id: 14775 } });

    await expect(getOrder('14775')).resolves.toEqual({ id: 14775 });
    expect(axios.get).toHaveBeenCalledWith('/orders/orders/14775/');
  });
});

describe('getOrders', () => {
  const params = { customer_name: 'Test', origin: 'WA', model: 'ZMA', base: '', volts: '120V' };

  it('passes the lookup fields as query params and returns the results array', async () => {
    axios.get.mockResolvedValueOnce({ data: { count: 1, results: [{ id: 1 }] } });

    await expect(getOrders(params)).resolves.toEqual([{ id: 1 }]);
    expect(axios.get).toHaveBeenCalledWith('/orders/orders/', { params });
  });

  it('throws when the response is not a paginated list', async () => {
    axios.get.mockResolvedValueOnce({ data: { id: 1 } });
    jest.spyOn(console, 'error').mockImplementation(() => {});

    await expect(getOrders(params)).rejects.toThrow('unexpected data format');
    console.error.mockRestore();
  });
});
