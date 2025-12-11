'use client';

import { useEffect } from 'react';
import { Provider, useDispatch } from 'react-redux';
import { store } from '../store/store';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { lightTheme } from '../theme/theme';
import { hydrateAuth } from '../store/slices/authSlice';
import EmotionRegistry from './EmotionRegistry';
import { NotificationProvider } from '../contexts/NotificationContext';

function AuthHydrator({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(hydrateAuth());
  }, [dispatch]);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <EmotionRegistry>
      <Provider store={store}>
        <ThemeProvider theme={lightTheme}>
          <CssBaseline />
          <NotificationProvider>
            <AuthHydrator>{children}</AuthHydrator>
          </NotificationProvider>
        </ThemeProvider>
      </Provider>
    </EmotionRegistry>
  );
}
