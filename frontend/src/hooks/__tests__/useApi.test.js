import { renderHook } from '@testing-library/react';
import { act } from 'react'; 
import { useApi } from '../useApi';

describe('useApi', () => {
  it('should handle successful API calls', async () => {
    const mockData = { data: 'test' };
    const mockApi = jest.fn().mockResolvedValue(mockData);
    const { result } = renderHook(() => useApi(mockApi));

    await act(async () => {
      const response = await result.current.execute();
      expect(response).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should handle API errors', async () => {
    const error = new Error('API Error');
    const mockApi = jest.fn().mockRejectedValue(error);
    const { result } = renderHook(() => useApi(mockApi));

    await act(async () => {
      await expect(result.current.execute()).rejects.toThrow('API Error');
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('API Error');
    expect(result.current.loading).toBe(false);
  });

  it('should handle loading state', async () => {
    const mockData = { data: 'test' };
    const mockApi = jest.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => resolve(mockData), 100);
      });
    });

    const { result } = renderHook(() => useApi(mockApi));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 200));
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual(mockData);
  });
});
