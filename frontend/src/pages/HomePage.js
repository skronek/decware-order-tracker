import React, { useState, useEffect } from 'react';
import { Typography, Container, Box, Paper, Divider, Button, Link as MuiLink } from '@mui/material';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { OrderSummary } from '../components/order-summary';
import { getSavedOrderIds, removeOrderId } from '../utils/storage';
import { getOrder } from '../features/orders/api/get-order';

// Fetches each saved order. IDs the API no longer knows (404) are dropped from storage.
const loadSavedOrders = async (ids) => {
  const results = await Promise.all(
    ids.map((id) => getOrder(id).then((order) => ({ order }), (error) => ({ id, error })))
  );
  const failed = results.filter((result) => result.error);
  const missing = failed.filter((result) => result.error.response?.status === 404);
  missing.forEach((result) => removeOrderId(result.id));

  return {
    orders: results.filter((result) => result.order).map((result) => result.order),
    hasErrors: failed.length > missing.length,
  };
};

const HomePage = () => {
  const [savedOrderIds] = useState(getSavedOrderIds);
  const [savedOrders, setSavedOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(savedOrderIds.length > 0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (savedOrderIds.length === 0) return;
    let ignore = false;

    loadSavedOrders(savedOrderIds).then(({ orders, hasErrors }) => {
      if (ignore) return;
      setSavedOrders(orders);
      setError(hasErrors ? 'Some orders could not be loaded.' : null);
      setIsLoading(false);
    });

    return () => {
      ignore = true;
    };
  }, [savedOrderIds]);

  const handleRemoveOrder = (orderId) => {
    removeOrderId(orderId);
    setSavedOrders((orders) => orders.filter((order) => order.id !== orderId));
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Decware Order Tracker
        </Typography>
        <Typography variant="body1" paragraph>
          Welcome to the Decware Order Tracker. Use this application to track the status of your Decware order
          and view estimated completion times. Order statuses are read nightly from Decware's
          official{' '}
          <MuiLink href="https://orders.decware.com/list_view.php" target="_blank" rel="noopener noreferrer">
            order list
          </MuiLink>
          , and this site keeps a history of each order's progress.
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>How completion dates are estimated:</strong> Decware builds orders roughly first come,
          first served. Almost all of the wait is spent in the queue before a build starts; the build itself
          usually takes about two weeks. We count how many orders are ahead of yours and divide by the
          number of orders Decware has started each week over the past year, then add the typical build
          time. The later date in the range assumes the shop works more slowly than it has recently.
          These are estimates, not dates from Decware, and they're updated every night as the queue moves.
        </Typography>
      </Box>

      {savedOrderIds.length > 0 && (
        <Box sx={{ my: 4 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h5" component="h2" gutterBottom>
            Your Saved Orders
          </Typography>
          {isLoading && <LoadingSpinner />}
          {error && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
              <Typography data-testid="saved-order-error">{error}</Typography>
            </Paper>
          )}
          {savedOrders.length > 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {savedOrders.map((order) => (
                <OrderSummary key={order.id} order={order}>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleRemoveOrder(order.id)}
                    data-testid={`remove-order-${order.id}`}
                  >
                    Remove
                  </Button>
                </OrderSummary>
              ))}
            </Box>
          )}
          {savedOrders.length === 0 && !isLoading && !error && (
            <Paper sx={{ p: 3, bgcolor: 'info.light' }}>
              <Typography>No saved orders to display.</Typography>
            </Paper>
          )}
        </Box>
      )}
    </Container>
  );
};

export default HomePage;
