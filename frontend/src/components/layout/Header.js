import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Header = () => {
  return (
    <AppBar position="static" sx={{ bgcolor: '#343A3F' }}>
      <Toolbar>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ flexGrow: 1 }}>
          <Box 
            component="img"
            src="/decwarelogoblack.jpg"
            alt="Decware Logo"
            sx={{ 
              height: 40,
              width: 'auto',
              display: 'block'
            }}
          />
          <Typography variant="h6" component="div">
            Decware Order Tracker
          </Typography>
        </Stack>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
          >
            Home
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
