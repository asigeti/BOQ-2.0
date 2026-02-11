'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { darkTheme, lightTheme } from '@/theme/theme';

type ThemeMode = 'dark' | 'light';

interface ThemeContextType {
  mode: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'boq-theme-mode';

export function ThemeContextProvider({ children }: { children: ReactNode }) {
  // Initialize with dark theme, will update from localStorage after mount
  const [mode, setMode] = useState<ThemeMode>('dark');
  const [mounted, setMounted] = useState(false);

  // Load theme from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (stored && (stored === 'dark' || stored === 'light')) {
      setMode(stored);
    }
    setMounted(true);
  }, []);

  // Save to localStorage when mode changes
  useEffect(() => {
    if (mounted) {
      localStorage.setItem(STORAGE_KEY, mode);
      // Update body class for global CSS
      document.body.classList.remove('theme-dark', 'theme-light');
      document.body.classList.add(`theme-${mode}`);
    }
  }, [mode, mounted]);

  const toggleTheme = () => {
    setMode((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const setTheme = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  const theme = useMemo(() => {
    return mode === 'dark' ? darkTheme : lightTheme;
  }, [mode]);

  const contextValue = useMemo(
    () => ({
      mode,
      toggleTheme,
      setTheme,
      isDark: mode === 'dark',
    }),
    [mode]
  );

  // Always provide context, but hide content until mounted to prevent hydration mismatch
  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        {!mounted ? (
          <div style={{ visibility: 'hidden' }}>{children}</div>
        ) : (
          children
        )}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}

export function useThemeMode() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useThemeMode must be used within a ThemeContextProvider');
  }
  return context;
}
