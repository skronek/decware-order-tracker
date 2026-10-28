import { useEffect } from 'react';
import { useApi } from '../../../hooks/useApi';
import { getOrder } from './get-order';

export const useOrderDetails = (orderId) => {
  const { data, loading, error, execute } = useApi(getOrder);

  useEffect(() => {
    if (!orderId) return;
    // useApi keeps the error in state for the caller
    execute(orderId).catch(() => {});
  }, [orderId, execute]);

  return {
    order: data,
    // useApi starts idle, so count the render before the first fetch as loading
    loading: loading || Boolean(orderId && !data && !error),
    error,
  };
};
