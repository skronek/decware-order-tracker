import React, { useState, useEffect } from 'react';
import { Typography, Container, Box, Paper, Grid, CircularProgress, Divider, Button, Link as MuiLink } from '@mui/material';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { getSavedOrderIds, removeOrderId } from '../utils/storage'; // Import storage helpers
import { formatStatus, formatEstCompletion } from '../utils/orderFormat';

// --- Helper functions ---
// Helper to format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  // Adjust for timezone offset to display in local time
  const utcDate = new Date(date.getTime() + date.getTimezoneOffset() * 60000);
  return `${utcDate.getMonth() + 1}/${utcDate.getDate()}/${utcDate.getFullYear()}`;
};
// --- End Helper Functions ---

const HomePage = () => {
  const [savedOrderIds, setSavedOrderIds] = useState([]);
  const [savedOrdersDetails, setSavedOrdersDetails] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Effect to get all saved order IDs on mount
  useEffect(() => {
    const savedIds = getSavedOrderIds();
    setSavedOrderIds(savedIds);
  }, []); // Empty dependency array means run once on mount

  // Effect to fetch order details when savedOrderIds changes
  useEffect(() => {
    if (savedOrderIds.length > 0) {
      const fetchSavedOrders = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
          // Create an array of promises for each order fetch
          const orderPromises = savedOrderIds.map(id => 
            axios.get(`/api/orders/orders/${String(id).trim()}/`)
              .then(response => response.data)
              .catch(err => {
                console.error(`Error fetching order ${id}:`, err);
                return null; // Return null for failed requests
              })
          );
          
          // Wait for all promises to resolve
          const results = await Promise.all(orderPromises);
          
          // Filter out null results (failed requests)
          const validResults = results.filter(result => result !== null);
          
          setSavedOrdersDetails(validResults);
          
          if (validResults.length < results.length) {
            setError('Some orders could not be loaded.');
          }
        } catch (err) {
          console.error('Error fetching saved orders:', err);
          setError('Failed to load saved order details.');
        } finally {
          setIsLoading(false);
        }
      };
      
      fetchSavedOrders();
    } else {
      setSavedOrdersDetails([]);
    }
  }, [savedOrderIds]); // Run when savedOrderIds changes
  
  // Function to handle removing an order
  const handleRemoveOrder = (orderId) => {
    // Ensure orderId is treated as a string for consistency
    orderId = String(orderId);
    const updatedIds = removeOrderId(orderId);
    setSavedOrderIds(updatedIds);
    // Log for debugging
    console.log('Removed order ID:', orderId);
    console.log('Updated saved IDs:', updatedIds);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        {/* Welcome Section */}
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

      {/* Saved Order Section */}
      {savedOrderIds.length > 0 && (
        <Box sx={{ my: 4 }}>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h5" component="h2" gutterBottom>
            Your Saved Orders
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mb: 2 }}>
            The estimated delivery date is based on the average time it takes from the order date to when the order is marked PASSED_QC_AWAITING_PAYMENT.
          </Typography>
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress data-testid="saved-order-loading" />
            </Box>
          )}
          {error && (
            <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
              <Typography data-testid="saved-order-error">{error}</Typography>
            </Paper>
          )}
          {savedOrdersDetails.length > 0 && !isLoading && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {savedOrdersDetails.map((order) => (
                <Paper key={order.id} sx={{ p: 3 }} data-testid={`saved-order-${order.id}`}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}><Typography><strong>Customer:</strong> {order.customer_name}</Typography></Grid>
                    <Grid item xs={12} sm={6}><Typography><strong>Model:</strong> {order.model}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Origin:</strong> {order.origin}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Base:</strong> {order.base || 'N/A'}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Volts:</strong> {order.volts}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Order Date:</strong> {formatDate(order.order_date)}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Status:</strong> {formatStatus(order.status)}</Typography></Grid>
                    <Grid item xs={12} sm={4}><Typography><strong>Est. Completion:</strong> {formatEstCompletion(order.estimated_completion)}</Typography></Grid>
                    {order.estimated_completion?.explanation && (
                      <Grid item xs={12}><Typography variant="body2" color="text.secondary">{order.estimated_completion.explanation}</Typography></Grid>
                    )}
                    <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
                      <Button component={Link} to={`/orders/${order.id}`}>
                        View details
                      </Button>
                      <Button 
                        variant="outlined" 
                        color="error" 
                        onClick={() => handleRemoveOrder(order.id)}
                        data-testid={`remove-order-${order.id}`}
                      >
                        Remove
                      </Button>
                    </Grid>
                  </Grid>
                </Paper>
              ))}
            </Box>
          )}
          {savedOrdersDetails.length === 0 && !isLoading && !error && (
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
