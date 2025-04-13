import { useState, useCallback } from 'react';

export const useSearchParams = () => {
  const [searchParams, setSearchParams] = useState({
    customerName: '',
    model: '',
    status: '',
    orderDate: '',
  });

  const updateSearchParam = useCallback((key, value) => {
    setSearchParams(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);

  const resetSearchParams = useCallback(() => {
    setSearchParams({
      customerName: '',
      model: '',
      status: '',
      orderDate: '',
    });
  }, []);

  const getQueryString = useCallback(() => {
    const params = new URLSearchParams();
    
    if (searchParams.customerName) {
      params.append('customer_name', searchParams.customerName);
    }
    if (searchParams.model) {
      params.append('model', searchParams.model);
    }
    if (searchParams.status) {
      params.append('status', searchParams.status);
    }
    if (searchParams.orderDate) {
      params.append('order_date', searchParams.orderDate);
    }

    return params.toString();
  }, [searchParams]);

  return {
    searchParams,
    updateSearchParam,
    resetSearchParams,
    getQueryString
  };
};
