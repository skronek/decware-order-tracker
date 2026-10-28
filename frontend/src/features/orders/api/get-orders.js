import { api } from '../../../lib/api-client';

/**
 * Looks up orders matching the given fields (customer_name, origin, model, base, volts).
 * Returns the array of matching orders from DRF's paginated response.
 */
export const getOrders = async (params) => {
  const response = await api.get('/orders/orders/', { params });
  const data = response.data;

  if (data && Array.isArray(data.results)) {
    return data.results;
  }
  console.error('Unexpected API response structure:', data);
  throw new Error('Received unexpected data format from the server.');
};
