import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Divider,
  Chip,
  Button,
} from '@mui/material';
import Grid from '@mui/material/Grid'; // Correct import path for MUI v7+ Grid
import { useOrderDetails } from '../hooks/useOrderDetails';
import { StatusHistoryTimeline } from './StatusHistoryTimeline';
import { getSavedOrderIds, saveOrderIds } from '../utils/storage';

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const utcDate = new Date(date.getTime() + date.getTimezoneOffset() * 60000);
  return `${utcDate.getMonth() + 1}/${utcDate.getDate()}/${utcDate.getFullYear()}`;
};

export const OrderDetails = () => {
  const { orderId } = useParams();
  const { orderDetails, loading, error } = useOrderDetails(orderId);
  const [isSaved, setIsSaved] = useState(false);

  // Check saved status on component mount
  useEffect(() => {
    const savedIds = getSavedOrderIds();
    setIsSaved(savedIds.includes(orderId));
  }, [orderId]);

  const handleSave = () => {
    const savedIds = getSavedOrderIds();
    if (!savedIds.includes(orderId)) {
      const newSavedIds = [...savedIds, orderId];
      saveOrderIds(newSavedIds);
      console.log('Saved order:', orderId);
    }
    setIsSaved(true);
  };

  const handleUnsave = () => {
    const savedIds = getSavedOrderIds();
    const newSavedIds = savedIds.filter(id => id !== orderId);
    saveOrderIds(newSavedIds);
    console.log('Unsaved order:', orderId);
    setIsSaved(false);
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

  if (!orderDetails) {
    return (
      <Box sx={{ p: 3 }}>
        <Paper sx={{ p: 2 }}>
          <Typography>Order not found.</Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }} data-testid="order-details-main">
        <Grid container spacing={3}>
          {/* Customer Information */}
          <Grid size={{ xs: 12, sm: 6 }} container justifyContent="space-between" alignItems="center">
            <Typography variant="h5" gutterBottom>
              Customer Information
            </Typography>
            <Button
              variant="contained"
              onClick={isSaved ? handleUnsave : handleSave}
              data-testid="save-button"
              sx={{ 
                mb: { xs: 2, sm: 0 },
                bgcolor: '#6c757d',
                '&:hover': {
                  bgcolor: '#5a6268',
                }
              }}
            >
              {isSaved ? 'Unsave Order' : 'Save Order'}
            </Button>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Name
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {orderDetails.customerName}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Order Date
                </Typography>
                <Typography variant="body1" gutterBottom data-testid="order-date">
                  {formatDate(orderDetails.orderDate)}
                </Typography>
              </Grid>
            </Grid>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Divider />
          </Grid>

          {/* Product Information */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="h5" gutterBottom>
              Product Information
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Model
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {orderDetails.model}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  label={orderDetails.status}
                  color={
                    orderDetails.status === 'NEW'
                      ? 'primary'
                      : orderDetails.status === 'IN_PROGRESS'
                      ? 'warning'
                      : 'success'
                  }
                  sx={{ mt: 1 }}
                  data-testid="status-chip"
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Divider />
          </Grid>

          {/* Estimated Completion */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="h5" gutterBottom>
              Estimated Completion
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Days Remaining
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {orderDetails.estimatedCompletion?.daysRemaining || 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Estimated Completion Date
                </Typography>
                <Typography variant="body1" gutterBottom data-testid="completion-date">
                  {orderDetails.estimatedCompletion?.date
                    ? formatDate(orderDetails.estimatedCompletion.date)
                    : 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Confidence Level
                </Typography>
                <Typography variant="body1" gutterBottom data-testid="confidence-level">
                  {orderDetails.estimatedCompletion?.confidenceLevel
                    ? `${(orderDetails.estimatedCompletion.confidenceLevel * 100).toFixed(0)}%`
                    : 'N/A'}
                </Typography>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>

      {/* Status History Timeline */}
      <Paper sx={{ p: 3, mt: 3 }} data-testid="status-history-timeline">
        <StatusHistoryTimeline statusHistory={orderDetails.statusHistory} />
      </Paper>
    </Box>
  );
};
