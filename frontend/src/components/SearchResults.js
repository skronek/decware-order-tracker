import React from 'react';
import { Box, Paper, Typography, CircularProgress, Grid, Button } from '@mui/material';
import { useState, useEffect } from 'react';
import { getSavedOrderIds, saveOrderIds } from '../utils/storage'; // Import helpers

// Helper to format status
const formatStatus = (status) => {
  const statusMap = {
    NEW: 'New',
    IN_PROGRESS: 'In Progress',
    COMPLETED: 'Completed',
    // Add other statuses if needed
  };
  return statusMap[status] || status;
};

// Helper to format date
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString();
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
      if (days_remaining < 0) return 'Overdue'; // Handle overdue case
      if (days_remaining === 0) return 'Today';
      if (days_remaining === 1) return 'Tomorrow';
      return `${days_remaining} days`;
  }
  return 'N/A';
};

export const SearchResults = ({ results, loading, error }) => {
  const [isSaved, setIsSaved] = useState(false);

  // Check local storage when results change to see if the current order is saved
  useEffect(() => {
    if (results && results.length === 1) {
      const order = results[0];
      const savedIds = getSavedOrderIds(); // Use helper
      const alreadySaved = order.id ? savedIds.includes(order.id.toString()) : false; // Check if ID is in the list (ensure string comparison if needed)
      setIsSaved(alreadySaved);
    } else {
      setIsSaved(false); // Reset if no single order is displayed
    }
  }, [results]); // Re-run effect when results change

  const handleSave = (orderToSave) => {
    if (!orderToSave || !orderToSave.id) return; // Need an ID to save

    const orderIdToSave = orderToSave.id.toString(); // Ensure ID is a string if necessary

    try {
      const savedIds = getSavedOrderIds(); // Use helper

      // Check if already saved (using the same logic as useEffect)
      const alreadySaved = savedIds.includes(orderIdToSave);

      if (!alreadySaved) {
        const newSavedIds = [...savedIds, orderIdToSave];
        saveOrderIds(newSavedIds); // Use helper
        setIsSaved(true); // Update UI feedback
        console.log('Order saved (ID):', orderIdToSave);
      } else {
        console.log('Order already saved.');
      }
    } catch (error) {
      console.error('Error saving order to localStorage:', error);
      // Optionally show an error message to the user
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress data-testid="loading-indicator" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 2 }}>
          <Typography color="error" data-testid="error-message">
            {error}
          </Typography>
        </Paper>
      </Box>
    );
  }

  // After loading and error checks, handle the results
  if (results) {
    if (results.length === 0) {
      return (
        <Box sx={{ mt: 3, mb: 3 }}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              Order not found. Please verify your details and try again.
            </Typography>
          </Paper>
        </Box>
      );
    }

    if (results.length === 1) {
      const order = results[0];
      return (
        <Box sx={{ mt: 3, mb: 3 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Order Details</Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}><Typography><strong>Customer:</strong> {order.customer_name}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 6 }}><Typography><strong>Model:</strong> {order.model}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Origin:</strong> {order.origin}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Base:</strong> {order.base || 'N/A'}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Volts:</strong> {order.volts}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Order Date:</strong> {formatDate(order.order_date)}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Status:</strong> {formatStatus(order.status)}</Typography></Grid>
              <Grid size={{ xs: 12, sm: 4 }}><Typography><strong>Est. Completion:</strong> {formatEstCompletion(order.estimated_completion)}</Typography></Grid>
              {/* Add other relevant fields if needed, e.g., order.id */}
            </Grid>
            {/* TODO: Optionally display Status History here later */}
            <Box sx={{ mt: 2, textAlign: 'right' }}> 
              <Button 
                variant="contained" 
                onClick={() => handleSave(order)}
                disabled={isSaved}
                sx={{
                  bgcolor: '#6c757d',
                  '&:hover': {
                    bgcolor: '#5a6268',
                  }
                }}
              >
                {isSaved ? 'Saved' : 'Save This Order'}
              </Button>
            </Box>
          </Paper>
        </Box>
      );
    }

    // Optional: Handle unexpected case of multiple results for lookup?
    if (results.length > 1) {
      return (
        <Box sx={{ p: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography color="error">Internal error: Multiple orders found for the provided details.</Typography>
          </Paper>
        </Box>
      );
    }
  }

  // Render nothing if no search has been performed yet (results is null/undefined)
  return null;
};
