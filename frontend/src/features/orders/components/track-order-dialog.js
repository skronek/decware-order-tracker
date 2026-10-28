import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { SearchForm } from './search-form';
import { SearchResults } from './search-results';
import { useApi } from '../../../hooks/useApi';
import { getOrders } from '../api/get-orders';

// Lives inside the Dialog, which unmounts it on close, so each opening starts a fresh search.
const TrackOrderSearch = ({ trackedIds, onTrack }) => {
  const { data, error, loading, execute } = useApi(getOrders);

  // useApi keeps the error in state, and SearchResults shows it
  const handleSearch = (formData) => execute(formData).catch(() => {});

  return (
    <>
      <Typography variant="body1">
        Enter your Customer Name, Origin, Model, Base, and Volts as they appear on Decware's order list.
      </Typography>
      <SearchForm onSearch={handleSearch} />
      <SearchResults results={data} error={error} loading={loading} trackedIds={trackedIds} onTrack={onTrack} />
    </>
  );
};

// Search for an order and pick one to track. onTrack(order) gets the picked order.
export const TrackOrderDialog = ({ open, onClose, trackedIds, onTrack }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const handleTrack = (order) => {
    onTrack(order);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullScreen={fullScreen} fullWidth maxWidth="md">
      <DialogTitle>Track an order</DialogTitle>
      <DialogContent>
        <TrackOrderSearch trackedIds={trackedIds} onTrack={handleTrack} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};
