'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import {
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material';

interface NotificationContextType {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showInfo: (message: string) => void;
  showConfirm: (message: string) => Promise<boolean>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface ConfirmDialogState {
  open: boolean;
  message: string;
  resolve?: (value: boolean) => void;
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>({
    open: false,
    message: '',
  });

  const showSuccess = (message: string) => {
    setSnackbar({ open: true, message, severity: 'success' });
  };

  const showError = (message: string) => {
    setSnackbar({ open: true, message, severity: 'error' });
  };

  const showInfo = (message: string) => {
    setSnackbar({ open: true, message, severity: 'info' });
  };

  const showConfirm = (message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmDialog({
        open: true,
        message,
        resolve,
      });
    });
  };

  const handleSnackbarClose = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  const handleConfirmClose = (confirmed: boolean) => {
    if (confirmDialog.resolve) {
      confirmDialog.resolve(confirmed);
    }
    setConfirmDialog({ open: false, message: '', resolve: undefined });
  };

  return (
    <NotificationContext.Provider value={{ showSuccess, showError, showInfo, showConfirm }}>
      {children}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        dir="rtl"
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => handleConfirmClose(false)}
        dir="rtl"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: 300,
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: 600, color: '#f59e0b' }}>אישור פעולה</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: '1rem', color: 'text.primary' }}>
            {confirmDialog.message}
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            onClick={() => handleConfirmClose(false)}
            variant="outlined"
            color="inherit"
            sx={{ minWidth: 80 }}
          >
            ביטול
          </Button>
          <Button
            onClick={() => handleConfirmClose(true)}
            variant="contained"
            color="error"
            sx={{ minWidth: 80 }}
            autoFocus
          >
            אישור
          </Button>
        </DialogActions>
      </Dialog>
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}
