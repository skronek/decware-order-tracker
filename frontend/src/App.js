import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import OrderDetailsPage from './pages/OrderDetailsPage';
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/orders/:orderId" element={<OrderDetailsPage />} />
            </Routes>
          </Layout>
        </Router>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
