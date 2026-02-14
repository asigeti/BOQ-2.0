'use client';

import { createContext, useContext, useCallback, useState, ReactNode } from 'react';
import { Snackbar, Alert, Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography } from '@mui/material';

interface NotificationContextType {
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
  showConfirm: (message: string) => Promise<boolean>;
}

const NotificationContext = createContext<NotificationContextType>({
  showError: () => {},
  showSuccess: () => {},
  showConfirm: () => Promise.resolve(false),
});

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'error' | 'success' }>({
    open: false, message: '', severity: 'error',
  });
  const [confirm, setConfirm] = useState<{ open: boolean; message: string; resolve: ((v: boolean) => void) | null }>({
    open: false, message: '', resolve: null,
  });

  const showError = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'error' });
  }, []);

  const showSuccess = useCallback((message: string) => {
    setSnackbar({ open: true, message, severity: 'success' });
  }, []);

  const showConfirm = useCallback((message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirm({ open: true, message, resolve });
    });
  }, []);

  const handleConfirmClose = (result: boolean) => {
    confirm.resolve?.(result);
    setConfirm({ open: false, message: '', resolve: null });
  };

  return (
    <NotificationContext.Provider value={{ showError, showSuccess, showConfirm }}>
      {children}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} variant="filled" onClose={() => setSnackbar((s) => ({ ...s, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
      <Dialog open={confirm.open} onClose={() => handleConfirmClose(false)} dir="rtl">
        <DialogTitle>אישור</DialogTitle>
        <DialogContent>
          <Typography>{confirm.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleConfirmClose(false)}>ביטול</Button>
          <Button onClick={() => handleConfirmClose(true)} variant="contained" color="error">אישור</Button>
        </DialogActions>
      </Dialog>
    </NotificationContext.Provider>
  );
}

export const useNotification = () => useContext(NotificationContext);
