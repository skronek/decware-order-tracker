import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  Typography,
} from '@mui/material';

export const SearchForm = ({ onSearch }) => {
  const [formData, setFormData] = useState({
    customer_name: '',
    origin: '',
    model: '',
    base: '',
    volts: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const { customer_name, origin, model, volts } = formData;
    if (!customer_name || !origin || !model || !volts) {
      setError('Please fill in customer name, origin, model, and volts to look up an order.');
      return;
    }
    setError('');
    onSearch(formData);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Customer Name"
            name="customer_name"
            value={formData.customer_name}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Model"
            name="model"
            value={formData.model}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Origin"
            name="origin"
            value={formData.origin}
            onChange={handleChange}
            required
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Base"
            name="base"
            value={formData.base}
            onChange={handleChange}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Volts"
            name="volts"
            value={formData.volts}
            onChange={handleChange}
            required
          />
        </Grid>
        {error && (
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography color="error">{error}</Typography>
          </Grid>
        )}
        <Grid size={{ xs: 12, sm: 6 }}>
          <Button
            type="submit"
            variant="contained"
            color="secondary"
            fullWidth
          >
            Search
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};
