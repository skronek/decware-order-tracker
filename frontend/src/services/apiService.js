const BASE_URL = '/api'; // Assuming your Django API is served under /api

/**
 * Fetches a specific order record from the backend based on lookup criteria.
 * 
 * @param {object} params - The lookup parameters.
 * @param {string} params.customer_name - Customer's name.
 * @param {string} params.origin - Order origin.
 * @param {string} params.model - Product model.
 * @param {string} params.base - Product base.
 * @param {string} params.volts - Product volts.
 * @returns {Promise<Array>} A promise that resolves to an array containing the matching order (or an empty array if not found).
 * @throws {Error} Throws an error if the network response is not ok.
 */
const getOrder = async (params) => {
  // Construct URL query parameters from the formData object
  const queryParams = new URLSearchParams(params).toString();
  const url = `${BASE_URL}/orders/orders/?${queryParams}`; // Corrected endpoint path

  const response = await fetch(url);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Failed to fetch order details' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  const data = await response.json();

  // Expecting DRF's paginated response structure { count, next, previous, results }
  if (data && Array.isArray(data.results)) {
    return data.results; // Return only the array of orders
  } else {
    // Handle cases where the response is not as expected
    console.error('Unexpected API response structure:', data);
    throw new Error('Received unexpected data format from the server.');
  }
};

// You might add other API functions here later (e.g., getMetrics)
const apiService = {
  getOrder,
};

export default apiService;
