import React from 'react';
import { Typography, Container, Box } from '@mui/material';
import { SearchForm } from '../components/SearchForm';
import { SearchResults } from '../components/SearchResults';
import { useApi } from '../hooks/useApi';
import { getOrders } from '../features/orders/api/get-orders';

const SearchPage = () => {
  const { data, error, loading, execute } = useApi(getOrders);

  // useApi keeps the error in state, and SearchResults shows it
  const handleSearch = (formData) => execute(formData).catch(() => {});

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Look Up Order
        </Typography>
        <Typography variant="body1" paragraph>
          Enter your Customer Name, Origin, Model, Base, and Volts to find your specific order.
        </Typography>
        <SearchForm onSearch={handleSearch} />
        <SearchResults results={data} error={error} loading={loading} />
      </Box>
    </Container>
  );
};

export default SearchPage;
