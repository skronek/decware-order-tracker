import React, { useState } from 'react';
import { Box, Paper, Typography, Button } from '@mui/material';
import LoadingSpinner from './common/LoadingSpinner';
import { OrderSummary } from './order-summary';
import { addOrderId, isOrderSaved } from '../utils/storage';

const SaveOrderButton = ({ orderId }) => {
  const [isSaved, setIsSaved] = useState(() => isOrderSaved(orderId));

  const handleSave = () => {
    addOrderId(orderId);
    setIsSaved(true);
  };

  return (
    <Button variant="contained" color="secondary" onClick={handleSave} disabled={isSaved}>
      {isSaved ? 'Saved' : 'Save This Order'}
    </Button>
  );
};

export const SearchResults = ({ results, loading, error }) => {
  if (loading) {
    return <LoadingSpinner />;
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

  // No search yet
  if (!results) {
    return null;
  }

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

  return (
    <Box sx={{ mt: 3, mb: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
      {results.length > 1 && (
        <Typography color="text.secondary">
          {results.length} orders match these details.
        </Typography>
      )}
      {results.map((order) => (
        <OrderSummary key={order.id} order={order}>
          <SaveOrderButton orderId={order.id} />
        </OrderSummary>
      ))}
    </Box>
  );
};
