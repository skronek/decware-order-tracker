import React from 'react';
import { Typography, Container, Box } from '@mui/material';
import { useParams } from 'react-router-dom';

const OrderDetailsPage = () => {
  const { orderId } = useParams();

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Order Details
        </Typography>
        <Typography variant="body1" paragraph>
          Viewing details for order {orderId}
        </Typography>
        {/* Order details will be added here */}
      </Box>
    </Container>
  );
};

export default OrderDetailsPage;
