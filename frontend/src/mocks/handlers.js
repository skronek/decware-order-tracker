import { rest } from 'msw';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Mock order data for testing
const mockOrderResponse = {
  count: 1,
  next: null,
  previous: null,
  results: [
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
  ]
};

const mockEmptyResponse = {
  count: 0,
  next: null,
  previous: null,
  results: []
};

export const handlers = [
  // Mock search orders
  rest.get(`${API_BASE_URL}/orders/search/`, (req, res, ctx) => {
    // We can use the query parameter if needed
    // const query = req.url.searchParams.get('q');
    
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: 1,
          customer_name: 'John Doe',
          model: 'ZEN-III',
          status: 'NEW',
          time_created: '2025-04-10T10:00:00Z',
          time_updated: '2025-04-10T10:00:00Z',
        },
        {
          id: 2,
          customer_name: 'Jane Smith',
          model: 'HR-1',
          status: 'ON_BENCH',
          time_created: '2025-04-09T10:00:00Z',
          time_updated: '2025-04-10T09:00:00Z',
        },
      ])
    );
  }),

  // Mock get order details
  rest.get(`${API_BASE_URL}/orders/:orderId/`, (req, res, ctx) => {
    const { orderId } = req.params;
    
    if (orderId === '999') {
      return res(
        ctx.status(404),
        ctx.json({ message: 'Order not found' })
      );
    }
    
    if (orderId === '500') {
      return res(
        ctx.status(500),
        ctx.json({ message: 'Server error' })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        id: parseInt(orderId),
        customer_name: 'John Doe',
        model: 'ZEN-III',
        status: 'NEW',
        time_created: '2025-04-10T10:00:00Z',
        time_updated: '2025-04-10T10:00:00Z',
        status_history: [
          {
            previous_status: null,
            new_status: 'NEW',
            timestamp: '2025-04-10T10:00:00Z',
          },
        ],
      })
    );
  }),
  
  // Mock the orders/orders/ endpoint used by the SearchPage
  rest.get(`${API_BASE_URL}/orders/orders/`, (req, res, ctx) => {
    const customerName = req.url.searchParams.get('customer_name');
    const model = req.url.searchParams.get('model');
    
    // Return mock data if the request matches our test criteria
    if (customerName === 'Test Customer' && model === 'ZMA') {
      return res(ctx.status(200), ctx.json(mockOrderResponse));
    }
    
    // Return empty results for other queries
    return res(ctx.status(200), ctx.json(mockEmptyResponse));
  }),
  
  // Handler for API error testing
  rest.get(`${API_BASE_URL}/orders/orders/error`, (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ message: 'Server error' }));
  }),
  
  // Mock get status metrics
  rest.get(`${API_BASE_URL}/metrics/`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          status: 'NEW',
          average_time_days: 7,
          sample_size: 100,
          confidence_level: 'HIGH',
          last_updated: '2025-04-10T10:00:00Z',
        },
        {
          status: 'ON_BENCH',
          average_time_days: 14,
          sample_size: 80,
          confidence_level: 'HIGH',
          last_updated: '2025-04-10T10:00:00Z',
        },
      ])
    );
  }),
];
