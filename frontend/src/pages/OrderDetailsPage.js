import React from 'react';
import { Typography, Container, Box } from '@mui/material';
import { OrderDetails } from '../components/OrderDetails';

const OrderDetailsPage = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Order Details
        </Typography>
        <OrderDetails />
      </Box>
    </Container>
  );
};

export default OrderDetailsPage;
