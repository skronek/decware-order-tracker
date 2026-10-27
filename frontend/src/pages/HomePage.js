import React, { useState, useEffect } from 'react';
import { Typography, Container, Box, Paper, Grid, CircularProgress, Divider, Button } from '@mui/material';
import axios from 'axios';
import { getSavedOrderIds, removeOrderId } from '../utils/storage'; // Import storage helpers

// --- Helper functions (consider moving to a utils file later) ---
// Helper to format status
const formatStatus = (status) => {
  const statusMap = {
    NEW: 'New',
    IN_PROGRESS: 'In Progress',
    COMPLETED: 'Completed',
  };
  return statusMap[status] || status;
};

// Helper to format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  // Adjust for timezone offset to display in local time
  const utcDate = new Date(date.getTime() + date.getTimezoneOffset() * 60000);
  return `${utcDate.getMonth() + 1}/${utcDate.getDate()}/${utcDate.getFullYear()}`;
};

// Helper to format estimated completion
// Estimates are calendar dates (YYYY-MM-DD); parse them as local so they don't shift a day
const formatDay = (day) => new Date(`${day}T00:00:00`).toLocaleDateString();

const formatEstCompletion = (completionData) => {
  if (!completionData) return 'N/A';
  const { days_remaining, estimated_date, range_end_date } = completionData;
  if (estimated_date && range_end_date && range_end_date !== estimated_date) {
    return `${formatDay(estimated_date)} – ${formatDay(range_end_date)}`;
  }
  if (estimated_date) return formatDate(estimated_date);
  else if (days_remaining !== undefined && days_remaining !== null) {
    if (days_remaining < 0) return 'Overdue';
    if (days_remaining === 0) return 'Today';
    if (days_remaining === 1) return 'Tomorrow';
    return `${days_remaining} days`;
  }
  return 'N/A';
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
          and view estimated completion times.
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
                    <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
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
