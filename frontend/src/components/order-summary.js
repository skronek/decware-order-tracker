import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Grid, Paper, Typography } from '@mui/material';
import { formatDate, formatStatus, formatEstCompletion } from '../utils/orderFormat';

const Field = ({ label, children, sm = 4 }) => (
  <Grid size={{ xs: 12, sm }}>
    <Typography><strong>{label}:</strong> {children}</Typography>
  </Grid>
);

// One order as a card, linking to its details page. children are extra actions
// (save, remove) shown next to the link.
export const OrderSummary = ({ order, children }) => (
  <Paper sx={{ p: 3 }} data-testid={`order-summary-${order.id}`}>
    <Grid container spacing={2}>
      <Field label="Customer" sm={6}>{order.customer_name}</Field>
      <Field label="Model" sm={6}>{order.model}</Field>
      <Field label="Origin">{order.origin}</Field>
      <Field label="Base">{order.base || 'N/A'}</Field>
      <Field label="Volts">{order.volts}</Field>
      <Field label="Order Date">{formatDate(order.order_date)}</Field>
      <Field label="Status">{formatStatus(order.status)}</Field>
      <Field label="Best guess">{formatEstCompletion(order.estimated_completion)}</Field>
      {order.estimated_completion?.explanation && (
        <Grid size={{ xs: 12 }}>
          <Typography variant="body2" color="text.secondary">{order.estimated_completion.explanation}</Typography>
        </Grid>
      )}
    </Grid>
    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
      <Button component={Link} to={`/orders/${order.id}`}>
        View details
      </Button>
      {children}
    </Box>
  </Paper>
);
