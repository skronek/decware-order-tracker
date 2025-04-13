import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock react-router-dom
jest.mock('react-router-dom');

// Mock components
jest.mock('./components/SearchForm', () => ({
  SearchForm: () => <div data-testid="search-form">Search Form</div>,
}));

jest.mock('./components/SearchResults', () => ({
  SearchResults: () => <div data-testid="search-results">Search Results</div>,
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/decware order tracker/i)).toBeInTheDocument();
  });
});
