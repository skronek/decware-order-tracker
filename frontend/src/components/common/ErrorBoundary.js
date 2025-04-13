import React from 'react';
import { Alert, Box } from '@mui/material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ m: 2 }}>
          <Alert severity="error">
            {this.state.error?.message || 'Something went wrong. Please try again later.'}
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
