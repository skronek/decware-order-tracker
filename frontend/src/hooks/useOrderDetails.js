import { useState, useEffect } from 'react';
import { useApi } from './useApi';
import { getOrder } from '../features/orders/api/get-order';

export const useOrderDetails = (orderId) => {
  const [orderDetails, setOrderDetails] = useState(null);
  const { execute: fetchDetails, loading, error } = useApi(getOrder);

  useEffect(() => {
    const fetchOrderDetails = async () => {
      if (!orderId) return;
      
      try {
        setOrderDetails(await fetchDetails(orderId));
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
