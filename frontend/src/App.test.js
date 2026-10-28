import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Render the real router; src/__mocks__/react-router-dom.js stubs it out
jest.unmock('react-router-dom');

describe('App', () => {
  it('renders the home page inside the layout', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1, name: /decware order tracker/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /search orders/i })).toBeInTheDocument();
  });
});
