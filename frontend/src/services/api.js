import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const orderService = {
  searchOrders: async (params) => {
    const response = await api.get('/orders/search/', { params });
    return response.data;
  },
  
  getOrderDetails: async (orderId) => {
    const response = await api.get(`/orders/${orderId}/`);
    return response.data;
  },
};

export default api;
