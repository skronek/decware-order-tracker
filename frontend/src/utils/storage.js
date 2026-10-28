// Saved order IDs live in localStorage as an array of strings.

export const SAVED_ORDERS_KEY = 'savedOrderIds';

export const getSavedOrderIds = () => {
  try {
    const ids = JSON.parse(localStorage.getItem(SAVED_ORDERS_KEY));
    return Array.isArray(ids) ? ids.map(String) : [];
  } catch {
    return [];
  }
};

const saveOrderIds = (ids) => {
  localStorage.setItem(SAVED_ORDERS_KEY, JSON.stringify(ids));
};

export const isOrderSaved = (id) => getSavedOrderIds().includes(String(id));

export const addOrderId = (id) => {
  const savedIds = getSavedOrderIds();
  if (!savedIds.includes(String(id))) {
    saveOrderIds([...savedIds, String(id)]);
  }
};

export const removeOrderId = (id) => {
  saveOrderIds(getSavedOrderIds().filter((savedId) => savedId !== String(id)));
};
