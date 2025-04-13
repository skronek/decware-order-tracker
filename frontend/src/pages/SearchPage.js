import React from 'react';
import { Typography, Container, Box } from '@mui/material';
import { SearchForm } from '../components/SearchForm';
import { SearchResults } from '../components/SearchResults';
import { useApi } from '../hooks/useApi';
import apiService from '../services/apiService';

const SearchPage = () => {
  // Use the API hook to manage state for the order lookup
  const { 
    data: searchResults, // Rename data to searchResults for clarity
    error, 
    loading, 
    execute: performSearch // Rename execute for clarity
  } = useApi(apiService.getOrder); // Pass the API function to the hook

  // Define the handler function to be passed to SearchForm
  const handleSearch = async (formData) => {
    // The useApi hook's execute function takes the parameters for the apiService.getOrder
    await performSearch(formData); 
  };

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
        {/* Pass the state from the useApi hook to SearchResults */}
        <SearchResults results={searchResults} error={error} loading={loading} /> 
      </Box>
    </Container>
  );
};

export default SearchPage;
