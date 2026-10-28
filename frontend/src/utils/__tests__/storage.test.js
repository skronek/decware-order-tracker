import { SAVED_ORDERS_KEY, getSavedOrderIds, isOrderSaved, addOrderId, removeOrderId } from '../storage';

describe('saved order storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts empty', () => {
    expect(getSavedOrderIds()).toEqual([]);
  });

  it('adds IDs once, as strings, whatever type they are passed as', () => {
    addOrderId(14775);
    addOrderId('14775');
    addOrderId(12);
    expect(getSavedOrderIds()).toEqual(['14775', '12']);
    expect(isOrderSaved('14775')).toBe(true);
    expect(isOrderSaved(12)).toBe(true);
    expect(isOrderSaved(99)).toBe(false);
  });

  it('removes an ID passed as a number or a string', () => {
    localStorage.setItem(SAVED_ORDERS_KEY, JSON.stringify([14775, '12']));
    removeOrderId('14775');
    removeOrderId(12);
    expect(getSavedOrderIds()).toEqual([]);
  });

  it('treats corrupted storage as empty instead of throwing', () => {
    localStorage.setItem(SAVED_ORDERS_KEY, '{not json');
    expect(getSavedOrderIds()).toEqual([]);
    localStorage.setItem(SAVED_ORDERS_KEY, '{"a":1}');
    expect(getSavedOrderIds()).toEqual([]);
  });
});
