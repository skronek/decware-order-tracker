import { useState, useEffect } from 'react';
import { useApi } from './useApi';
import apiClient from '../api/apiClient';

export const useOrderDetails = (orderId) => {
  const [orderDetails, setOrderDetails] = useState(null);
  const { execute: fetchDetails, loading, error } = useApi(apiClient.get);

  useEffect(() => {
    const fetchOrderDetails = async () => {
      if (!orderId) return;
      
      try {
        const response = await fetchDetails(`/orders/orders/${orderId}/`);
        setOrderDetails(response.data);
      } catch (err) {
        console.error('Failed to fetch order details:', err);
      }
    };

    fetchOrderDetails();
  }, [orderId, fetchDetails]);

  return {
    orderDetails,
    loading,
    error,
  };
};
