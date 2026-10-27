import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Alert,
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
import { formatStatus, statusColor, isFinished, formatEstCompletion, formatConfidence } from '../utils/orderFormat';

const formatDate = (dateString) => (dateString ? new Date(dateString).toLocaleDateString() : 'N/A');

// A label/value pair in the details grid
const Field = ({ label, children, testId, sm = 4 }) => (
  <Grid size={{ xs: 12, sm }}>
    <Typography variant="subtitle2" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="body1" gutterBottom data-testid={testId}>
      {children}
    </Typography>
  </Grid>
);

const EstimateSection = ({ order }) => {
  const estimate = order.estimated_completion;

  if (isFinished(order.status)) {
    return <Typography>This order has passed quality control.</Typography>;
  }
  if (order.removed_at) {
    // Explained by the notice at the top of the page
    return <Typography color="text.secondary">No longer estimated.</Typography>;
  }
  if (!estimate) {
    return <Typography color="text.secondary">No estimate yet.</Typography>;
  }

  return (
    <Grid container spacing={2}>
      <Field label="Estimated to pass QC" testId="completion-date">
        {formatEstCompletion(estimate)}
      </Field>
      {estimate.queue_position !== null && estimate.queue_position !== undefined && (
        <Field label="Place in build queue" testId="queue-position">
          #{(estimate.queue_position + 1).toLocaleString()}
        </Field>
      )}
      <Field label="Confidence" testId="confidence-level">
        {formatConfidence(estimate.confidence_level)}
      </Field>
      {estimate.explanation && (
        <Grid size={{ xs: 12 }}>
          <Typography variant="body2" color="text.secondary">
            {estimate.explanation}
          </Typography>
        </Grid>
      )}
    </Grid>
  );
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
      saveOrderIds([...savedIds, orderId]);
    }
    setIsSaved(true);
  };

  const handleUnsave = () => {
    const savedIds = getSavedOrderIds();
    saveOrderIds(savedIds.filter(id => id !== orderId));
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

  const order = orderDetails;

  return (
    <Box sx={{ py: 3 }}>
      {order.removed_at && (
        <Alert severity="info" sx={{ mb: 3 }} data-testid="removed-notice">
          This order dropped off Decware's order list on {formatDate(order.removed_at)}, which usually
          means it has been finished.
        </Alert>
      )}

      <Paper sx={{ p: 3 }} data-testid="order-details-main">
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Typography variant="h5" component="h2">
              {order.model}
            </Typography>
            <Chip label={formatStatus(order.status)} color={statusColor(order.status)} data-testid="status-chip" />
          </Box>
          <Button
            variant="contained"
            onClick={isSaved ? handleUnsave : handleSave}
            data-testid="save-button"
            sx={{
              bgcolor: '#6c757d',
              '&:hover': {
                bgcolor: '#5a6268',
              }
            }}
          >
            {isSaved ? 'Unsave Order' : 'Save Order'}
          </Button>
        </Box>

        <Grid container spacing={2}>
          <Field label="Customer">{order.customer_name}</Field>
          <Field label="Origin">{order.origin}</Field>
          <Field label="Order Date" testId="order-date">{formatDate(order.order_date)}</Field>
          <Field label="Model">{order.model}</Field>
          <Field label="Base">{order.base || 'N/A'}</Field>
          <Field label="Volts">{order.volts}</Field>
          <Field label="Quantity">{order.quantity}</Field>
          <Field label="Options" sm={8}>{order.options || 'None'}</Field>
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Box data-testid="estimate">
          <Typography variant="h6" gutterBottom>
            Estimated Completion
          </Typography>
          <EstimateSection order={order} />
        </Box>
      </Paper>

      <StatusHistoryTimeline statusHistory={order.status_history} />

      <Box sx={{ mt: 3 }}>
        <Button component={Link} to="/search">
          Back to search
        </Button>
      </Box>
    </Box>
  );
};
