import { renderHook } from '@testing-library/react';
import { act } from 'react'; 
import { useOrders } from '../useOrders';
import { useApi } from '../useApi'; // This is the mock constructor

jest.mock('../useApi');

// Mock data
const mockSearchResults = [
  { id: 1, name: 'Order 1' },
  { id: 2, name: 'Order 2' },
];
const mockOrderDetails = { id: 1, name: 'Order 1', details: 'some details' };
const mockApiError = new Error('API Error');

describe('useOrders', () => {
  // Define mocks for the two useApi calls (search and details)
  let mockExecuteSearch, mockExecuteDetails;
  let mockSearchState, mockDetailsState;

  beforeEach(() => {
    // Create fresh mocks for each test
    mockExecuteSearch = jest.fn();
    mockExecuteDetails = jest.fn();

    // Initial states returned by the two useApi calls
    mockSearchState = {
      execute: mockExecuteSearch,
      data: null,
      error: null,
      loading: false,
    };
    mockDetailsState = {
      execute: mockExecuteDetails,
      data: null,
      error: null,
      loading: false,
    };

    // Reset the mock before configuring
    useApi.mockReset();

    // Configure the mock useApi constructor to return the specific states
    // for the first and second calls within useOrders
    useApi.mockReturnValueOnce(mockSearchState).mockReturnValueOnce(mockDetailsState);
  });

  it('should search orders successfully', async () => {
    // Arrange: Configure the mock execute for search
    mockExecuteSearch.mockResolvedValueOnce({ data: mockSearchResults });
    const { result, rerender } = renderHook(() => useOrders());

    // Act
    await act(async () => {
      await result.current.searchOrders({ q: 'Test' });
    });

    // Assert: Check if the correct API call was made
    expect(mockExecuteSearch).toHaveBeenCalledWith({ q: 'Test' });
    expect(mockExecuteSearch).toHaveBeenCalledTimes(1);

    // Assert: Check state AFTER the hook updates
    // 1. Update the mock state that useApi would now return
    mockSearchState.data = mockSearchResults;
    // 2. Re-configure the mock for the rerender
    useApi.mockReset();
    useApi.mockReturnValueOnce(mockSearchState).mockReturnValueOnce(mockDetailsState);
    // 3. Rerender the hook
    rerender();
    // 4. Assert the state
    expect(result.current.searchResults).toEqual(mockSearchResults);
    expect(result.current.error).toBeNull();
  });

  it('should get order details successfully', async () => {
    // Arrange: Configure the mock execute for details
    mockExecuteDetails.mockResolvedValueOnce({ data: mockOrderDetails });
    const { result, rerender } = renderHook(() => useOrders());

    // Act
    let details;
    await act(async () => {
      details = await result.current.getOrderDetails('1');
    });

    // Assert: Check direct return value and API call
    expect(details).toEqual({ data: mockOrderDetails }); // Note: useApi returns the raw result
    expect(mockExecuteDetails).toHaveBeenCalledWith('1');
    expect(mockExecuteDetails).toHaveBeenCalledTimes(1);

    // Assert: Check state AFTER the hook updates
    mockDetailsState.data = { data: mockOrderDetails }; // Update mock state
    useApi.mockReset();
    useApi.mockReturnValueOnce(mockSearchState).mockReturnValueOnce(mockDetailsState);
    rerender();
    expect(result.current.orderDetails).toEqual({ data: mockOrderDetails });
    expect(result.current.error).toBeNull();
  });

  it('should handle API errors during search', async () => {
    // Arrange: Configure mock execute for search to reject
    mockExecuteSearch.mockRejectedValueOnce(mockApiError);
    const { result, rerender } = renderHook(() => useOrders());

    // Act
    let caughtError;
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Silence console.error
    try {
      await act(async () => {
        await result.current.searchOrders({ q: 'Fail' });
      });
    } catch (error) {
      caughtError = error;
    }
    consoleErrorSpy.mockRestore(); // Restore console.error

    // Assert: Check error was thrown and API call was made
    expect(caughtError).toBe(mockApiError);
    expect(mockExecuteSearch).toHaveBeenCalledWith({ q: 'Fail' });
    expect(mockExecuteSearch).toHaveBeenCalledTimes(1);

    // Assert: Check state AFTER the hook updates
    mockSearchState.error = mockApiError.message; // Update mock state
    useApi.mockReset();
    useApi.mockReturnValueOnce(mockSearchState).mockReturnValueOnce(mockDetailsState);
    rerender();
    expect(result.current.searchResults).toBeNull();
    expect(result.current.error).toBe(mockApiError.message);
  });

  it('should handle API errors during get details', async () => {
    // Arrange: Configure mock execute for details to reject
    mockExecuteDetails.mockRejectedValueOnce(mockApiError);
    const { result, rerender } = renderHook(() => useOrders());

    // Act
    let caughtError;
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {}); // Silence console.error
    try {
      await act(async () => {
        await result.current.getOrderDetails('2');
      });
    } catch (error) {
      caughtError = error;
    }
    consoleErrorSpy.mockRestore(); // Restore console.error

    // Assert: Check error was thrown and API call was made
    expect(caughtError).toBe(mockApiError);
    expect(mockExecuteDetails).toHaveBeenCalledWith('2');
    expect(mockExecuteDetails).toHaveBeenCalledTimes(1);

    // Assert: Check state AFTER the hook updates
    mockDetailsState.error = mockApiError.message; // Update mock state
    useApi.mockReset();
    useApi.mockReturnValueOnce(mockSearchState).mockReturnValueOnce(mockDetailsState);
    rerender();
    expect(result.current.orderDetails).toBeNull(); // Should be null
    expect(result.current.error).toBe(mockApiError.message);
  });
});
