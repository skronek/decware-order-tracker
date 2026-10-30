import React from 'react';
import { render, act } from '@testing-library/react';
import { usePageViews } from '../use-page-views';

// Real routing so navigation changes the location
jest.unmock('react-router-dom');
const { MemoryRouter, useNavigate } = jest.requireActual('react-router-dom');

let navigate;
const Tracker = () => {
  usePageViews();
  navigate = useNavigate();
  return null;
};

const renderAt = (path) => render(
  <MemoryRouter initialEntries={[path]}>
    <Tracker />
  </MemoryRouter>
);

describe('usePageViews', () => {
  beforeEach(() => {
    window.goatcounter = { count: jest.fn() };
  });

  afterEach(() => {
    delete window.goatcounter;
  });

  it('leaves the first page load to the GoatCounter script', () => {
    renderAt('/');
    expect(window.goatcounter.count).not.toHaveBeenCalled();
  });

  it('counts navigation within the app', () => {
    renderAt('/');
    act(() => navigate('/orders/42'));
    expect(window.goatcounter.count).toHaveBeenCalledWith({ path: '/orders/42' });
  });

  it('does nothing when the script is blocked', () => {
    delete window.goatcounter;
    renderAt('/');
    expect(() => act(() => navigate('/orders/42'))).not.toThrow();
  });
});
