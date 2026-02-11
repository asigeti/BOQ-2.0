'use client';

import { useEffect } from 'react';
import { Provider, useDispatch } from 'react-redux';
import { store } from '../store/store';
import CssBaseline from '@mui/material/CssBaseline';
import { hydrateAuth } from '../store/slices/authSlice';
import EmotionRegistry from './EmotionRegistry';
import { NotificationProvider } from '../contexts/NotificationContext';
import { ThemeContextProvider } from '../contexts/ThemeContext';

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
        <ThemeContextProvider>
          <CssBaseline />
          <NotificationProvider>
            <AuthHydrator>{children}</AuthHydrator>
          </NotificationProvider>
        </ThemeContextProvider>
      </Provider>
    </EmotionRegistry>
  );
}
