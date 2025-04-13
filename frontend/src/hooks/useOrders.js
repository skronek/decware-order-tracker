import { useCallback } from 'react';
import { useApi } from './useApi';
import { orderService } from '../services/api';

export const useOrders = () => {
  const { execute: executeSearch, data: searchResults, error: searchError, loading: searchLoading } = useApi(orderService.searchOrders);
  const { execute: executeDetails, data: orderDetails, error: detailsError, loading: detailsLoading } = useApi(orderService.getOrderDetails);

  const searchOrders = useCallback(async (params) => {
    try {
      const results = await executeSearch(params);
      return results;
    } catch (error) {
      console.error('Failed to search orders:', error);
      throw error;
    }
  }, [executeSearch]);

  const getOrderDetails = useCallback(async (orderId) => {
    try {
      const details = await executeDetails(orderId);
      return details;
    } catch (error) {
      console.error('Failed to get order details:', error);
      throw error;
    }
  }, [executeDetails]);

  return {
    searchOrders,
    getOrderDetails,
    searchResults,
    orderDetails,
    error: searchError || detailsError,
    loading: searchLoading || detailsLoading
  };
};

export default useOrders;
