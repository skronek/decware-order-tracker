import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SearchForm } from '../search-form';

describe('SearchForm', () => {
  const mockOnSearch = jest.fn();

  beforeEach(() => {
    // Reset the mock function before each test
    mockOnSearch.mockClear();
  });

  it('renders all input fields and the submit button', () => {
    render(<SearchForm onSearch={mockOnSearch} />);

    expect(screen.getByLabelText(/Customer Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Model/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Origin/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Base/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Volts/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search/i })).toBeInTheDocument();
  });

  it('updates field values on change', () => {
    render(<SearchForm onSearch={mockOnSearch} />);

    const nameInput = screen.getByLabelText(/Customer Name/i);
    const modelInput = screen.getByLabelText(/Model/i);

    fireEvent.change(nameInput, { target: { value: 'Test Customer' } });
    fireEvent.change(modelInput, { target: { value: 'UFO' } });

    expect(nameInput).toHaveValue('Test Customer');
    expect(modelInput).toHaveValue('UFO');
  });

  it('shows an error and does not submit if fields are missing', () => {
    render(<SearchForm onSearch={mockOnSearch} />);

    // Only fill some fields
    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: 'Test' } });
    fireEvent.change(screen.getByLabelText(/Model/i), { target: { value: 'Test Model' } });

    // Click submit
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Check for error message
    expect(screen.getByText(/Please fill in customer name, origin, model, and volts/i)).toBeInTheDocument();

    // Check that onSearch was NOT called
    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  it('calls onSearch with form data and clears error on successful submission', () => {
    render(<SearchForm onSearch={mockOnSearch} />);

    // Fill all fields
    const formData = {
      customer_name: 'Full Name',
      origin: 'USA',
      model: 'SE84UFO', 
      base: 'STD',
      volts: '120V'
    };

    fireEvent.change(screen.getByLabelText(/Customer Name/i), { target: { value: formData.customer_name } });
    fireEvent.change(screen.getByLabelText(/Origin/i), { target: { value: formData.origin } });
    fireEvent.change(screen.getByLabelText(/Model/i), { target: { value: formData.model } });
    fireEvent.change(screen.getByLabelText(/Base/i), { target: { value: formData.base } });
    fireEvent.change(screen.getByLabelText(/Volts/i), { target: { value: formData.volts } });

    // Click submit
    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    // Check that the error message is NOT present
    expect(screen.queryByText(/Please fill in customer name, origin, model, and volts/i)).not.toBeInTheDocument();

    // Check that onSearch was called once with the correct data
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
    expect(mockOnSearch).toHaveBeenCalledWith(formData);
  });
});
