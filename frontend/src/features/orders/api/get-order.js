import { api } from '../../../lib/api-client';

export const getOrder = async (orderId) => {
  const response = await api.get(`/orders/orders/${orderId}/`);
  return response.data;
};
