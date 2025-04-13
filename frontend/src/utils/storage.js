// frontend/src/utils/storage.js

export const SAVED_ORDERS_KEY = 'savedOrderIds';

export const getSavedOrderIds = () => {
  const saved = localStorage.getItem(SAVED_ORDERS_KEY);
  return saved ? JSON.parse(saved) : [];
};

export const saveOrderIds = (ids) => {
  localStorage.setItem(SAVED_ORDERS_KEY, JSON.stringify(ids));
};

export const removeOrderId = (idToRemove) => {
  const savedIds = getSavedOrderIds();
  // Convert both to strings for comparison to ensure type consistency
  const idToRemoveStr = String(idToRemove);
  const updatedIds = savedIds.filter(id => String(id) !== idToRemoveStr);
  saveOrderIds(updatedIds);
  return updatedIds;
};
