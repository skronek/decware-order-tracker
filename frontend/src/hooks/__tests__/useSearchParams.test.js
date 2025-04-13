import { renderHook } from '@testing-library/react';
import { act } from 'react';
import { useSearchParams } from '../useSearchParams';

describe('useSearchParams', () => {
  it('should initialize with empty search params', () => {
    const { result } = renderHook(() => useSearchParams());
    
    expect(result.current.searchParams).toEqual({
      customerName: '',
      model: '',
      status: '',
      orderDate: '',
    });
  });

  it('should update search params correctly', () => {
    const { result } = renderHook(() => useSearchParams());
    
    act(() => {
      result.current.updateSearchParam('customerName', 'John Doe');
    });

    expect(result.current.searchParams.customerName).toBe('John Doe');
  });

  it('should reset search params', () => {
    const { result } = renderHook(() => useSearchParams());
    
    act(() => {
      result.current.updateSearchParam('customerName', 'John Doe');
      result.current.updateSearchParam('model', 'ZEN-III');
    });

    act(() => {
      result.current.resetSearchParams();
    });

    expect(result.current.searchParams).toEqual({
      customerName: '',
      model: '',
      status: '',
      orderDate: '',
    });
  });

  it('should generate correct query string', () => {
    const { result } = renderHook(() => useSearchParams());
    
    act(() => {
      result.current.updateSearchParam('customerName', 'John Doe');
      result.current.updateSearchParam('model', 'ZEN-III');
    });

    const queryString = result.current.getQueryString();
    expect(queryString).toBe('customer_name=John+Doe&model=ZEN-III');
  });

  it('should only include non-empty params in query string', () => {
    const { result } = renderHook(() => useSearchParams());
    
    act(() => {
      result.current.updateSearchParam('customerName', 'John Doe');
      result.current.updateSearchParam('model', '');
    });

    const queryString = result.current.getQueryString();
    expect(queryString).toBe('customer_name=John+Doe');
  });
});
