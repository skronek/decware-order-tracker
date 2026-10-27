import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SearchPage from '../../pages/SearchPage';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import theme from '../../theme';
import apiService from '../../services/apiService';

// Mock the API service
jest.mock('../../services/apiService', () => ({
  getOrder: jest.fn()
}));

// Mock order data for testing
const mockOrderResponse = [
  {
    id: 123,
    customer_name: 'Test Customer',
    origin: 'Web',
    model: 'ZMA',
    base: 'Wood',
    volts: '120V',
    options: 'Standard',
    status: 'IN_PROGRESS',
    order_date: '2023-01-15T00:00:00Z',
    estimated_completion: {
      days_remaining: 14,
      estimated_date: '2023-05-15T00:00:00Z'
    }
  }
];

// Wrap component with necessary providers for testing
const renderWithProviders = (ui) => {
  return render(
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </ThemeProvider>
  );
};

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
});

describe('SearchPage Integration Tests', () => {
  test('should fetch and display order details when search form is submitted with valid data', async () => {
    // Mock the API response
    apiService.getOrder.mockResolvedValueOnce(mockOrderResponse);
    
    // Render the SearchPage component
    renderWithProviders(<SearchPage />);
    
    // Fill out the search form
    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: 'Test Customer' } });
    fireEvent.change(screen.getByLabelText(/Origin/i), { target: { value: 'Web' } });
    fireEvent.change(screen.getByLabelText(/Model/i), { target: { value: 'ZMA' } });
    fireEvent.change(screen.getByLabelText(/Base/i), { target: { value: 'Wood' } });
    fireEvent.change(screen.getByLabelText(/Volts/i), { target: { value: '120V' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Search/i));
    
    // Wait for loading state to complete and results to appear
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    });
    
    // Verify API was called with correct parameters
    expect(apiService.getOrder).toHaveBeenCalledWith({
      customer_name: 'Test Customer',
      origin: 'Web',
      model: 'ZMA',
      base: 'Wood',
      volts: '120V'
    });
    
    // Verify order details are displayed
    expect(screen.getByText(/Order Details/i)).toBeInTheDocument();
    expect(screen.getByText(/Test Customer/i)).toBeInTheDocument();
    expect(screen.getByText(/ZMA/i)).toBeInTheDocument();
    expect(screen.getByText(/In Progress/i)).toBeInTheDocument();
    expect(screen.getByText(new Date(mockOrderResponse[0].estimated_completion.estimated_date).toLocaleDateString())).toBeInTheDocument();
  });
  
  test('should display "Order not found" message when no results are returned', async () => {
    // Mock empty API response
    apiService.getOrder.mockResolvedValueOnce([]);
    
    // Render the SearchPage component
    renderWithProviders(<SearchPage />);
    
    // Fill out the search form with data that will return empty results
    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: 'Non Existent' } });
    fireEvent.change(screen.getByLabelText(/Origin/i), { target: { value: 'Web' } });
    fireEvent.change(screen.getByLabelText(/Model/i), { target: { value: 'XYZ' } });
    fireEvent.change(screen.getByLabelText(/Base/i), { target: { value: 'Metal' } });
    fireEvent.change(screen.getByLabelText(/Volts/i), { target: { value: '240V' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Search/i));
    
    // Wait for loading state to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    });
    
    // Verify "Order not found" message is displayed
    expect(screen.getByText(/Order not found/i)).toBeInTheDocument();
  });
  
  test('should display validation error when form is submitted with missing fields', async () => {
    // Render the SearchPage component
    renderWithProviders(<SearchPage />);
    
    // Fill out the search form partially (missing some required fields)
    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: 'Test Customer' } });
    // Leave other fields empty
    
    // Submit the form
    fireEvent.click(screen.getByText(/Search/i));
    
    // Verify error message is displayed
    expect(screen.getByText(/Please fill in customer name, origin, model, and volts/i)).toBeInTheDocument();
    
    // Verify no API call was made
    expect(apiService.getOrder).not.toHaveBeenCalled();
  });
  
  test('should handle API errors gracefully', async () => {
    // Mock API error
    const errorObj = { message: 'Server error' };
    apiService.getOrder.mockRejectedValueOnce(errorObj);
    
    // Render the SearchPage component
    renderWithProviders(<SearchPage />);
    
    // Fill out the search form
    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: 'Test Customer' } });
    fireEvent.change(screen.getByLabelText(/Origin/i), { target: { value: 'Web' } });
    fireEvent.change(screen.getByLabelText(/Model/i), { target: { value: 'ZMA' } });
    fireEvent.change(screen.getByLabelText(/Base/i), { target: { value: 'Wood' } });
    fireEvent.change(screen.getByLabelText(/Volts/i), { target: { value: '120V' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Search/i));
    
    // Wait for loading state to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
    });
    
    // Verify error message is displayed
    expect(screen.getByTestId('error-message')).toBeInTheDocument();
    expect(screen.getByText(/Server error/i)).toBeInTheDocument();
  });
});
