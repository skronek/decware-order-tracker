import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchPage from '../SearchPage'; 

// Mock child components
jest.mock('../../components/SearchForm', () => ({
  SearchForm: () => <div>Mock Search Form</div>
}));
jest.mock('../../components/SearchResults', () => ({
  SearchResults: () => <div>Mock Search Results</div>
}));

jest.mock('../../features/orders/api/get-orders');

describe('SearchPage', () => {
  it('renders the correct page title', () => {
    render(<SearchPage />);
    // Check for the H1 heading with the correct text
    expect(screen.getByRole('heading', { name: /Look Up Order/i, level: 1 })).toBeInTheDocument();
  });

  it('renders mock search form and results components', () => {
    render(<SearchPage />);
    // Check for the unique text rendered by the mocks
    expect(screen.getByText('Mock Search Form')).toBeInTheDocument();
    expect(screen.getByText('Mock Search Results')).toBeInTheDocument();
  });

  // Add more tests if needed, e.g., testing the interaction 
  // where submitting the form calls the search function from the hook.
});
