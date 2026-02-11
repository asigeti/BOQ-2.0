'use client';

import { createTheme, alpha } from '@mui/material/styles';

// ═══════════════════════════════════════════════════════════════════════════
// BOQ PRO - CONSTRUCTION THEMES
// Dark: Brutalist Construction | Light: Blueprint Paper
// ═══════════════════════════════════════════════════════════════════════════

const colors = {
  // Primary: Electric Teal - Modern, tech-forward
  primary: {
    main: '#0ea5e9',
    light: '#38bdf8',
    dark: '#0284c7',
    contrastText: '#ffffff',
  },
  // Secondary: Warm Amber - Construction warmth
  secondary: {
    main: '#f59e0b',
    light: '#fbbf24',
    dark: '#d97706',
    contrastText: '#0f172a',
  },
  // Accent: Emerald - Success states
  success: {
    main: '#10b981',
    light: '#34d399',
    dark: '#059669',
  },
  // Warning: Orange
  warning: {
    main: '#f97316',
    light: '#fb923c',
    dark: '#ea580c',
  },
  // Error: Rose
  error: {
    main: '#f43f5e',
    light: '#fb7185',
    dark: '#e11d48',
  },
  // Neutral: Slate palette
  slate: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    850: '#172033',
    900: '#0f172a',
    950: '#0a0f1a',
  },
  // Light mode specific - Clean Professional
  paper: {
    cream: '#f1f5f9',      // Cooler gray-blue background (slate-100)
    warm: '#e2e8f0',       // Slightly darker for contrast (slate-200)
    light: '#ffffff',      // Pure white for cards
    border: '#cbd5e1',     // Visible border color (slate-300)
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// DARK THEME - Brutalist Construction
// ═══════════════════════════════════════════════════════════════════════════

const darkGlass = {
  background: 'rgba(30, 41, 59, 0.7)',
  backdropFilter: 'blur(20px) saturate(180%)',
  border: '1px solid rgba(148, 163, 184, 0.1)',
};

const darkShadows = {
  card: `0 4px 24px -4px rgba(0, 0, 0, 0.3), 0 8px 16px -8px rgba(0, 0, 0, 0.2)`,
  elevated: `0 20px 40px -12px rgba(0, 0, 0, 0.5)`,
};

export const darkTheme = createTheme({
  direction: 'rtl',
  palette: {
    mode: 'dark',
    primary: colors.primary,
    secondary: colors.secondary,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    background: {
      default: colors.slate[950],
      paper: colors.slate[900],
    },
    text: {
      primary: colors.slate[100],
      secondary: colors.slate[400],
    },
    divider: alpha(colors.slate[400], 0.12),
  },
  typography: {
    fontFamily: '"Rubik", "Outfit", system-ui, sans-serif',
    h1: {
      fontSize: '3rem',
      fontWeight: 800,
      letterSpacing: '-0.03em',
      lineHeight: 1.1,
      fontFamily: '"Outfit", "Rubik", system-ui, sans-serif',
    },
    h2: {
      fontSize: '2.25rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
      fontFamily: '"Outfit", "Rubik", system-ui, sans-serif',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.3,
    },
    h4: {
      fontSize: '1.375rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.35,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.7,
      letterSpacing: '0.01em',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      letterSpacing: '0.01em',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: '0.02em',
    },
    caption: {
      fontSize: '0.75rem',
      letterSpacing: '0.03em',
    },
  },
  shape: {
    borderRadius: 16,
  },
  shadows: [
    'none',
    '0 1px 3px rgba(0,0,0,0.3)',
    '0 2px 6px rgba(0,0,0,0.3)',
    '0 4px 12px rgba(0,0,0,0.3)',
    darkShadows.card,
    darkShadows.elevated,
    darkShadows.elevated,
    ...Array(18).fill(darkShadows.elevated),
  ] as any,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 28px',
          fontSize: '0.9375rem',
          fontWeight: 600,
          boxShadow: 'none',
          position: 'relative' as const,
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          background: `linear-gradient(135deg, ${colors.primary.main} 0%, ${colors.primary.dark} 100%)`,
          boxShadow: `0 4px 14px ${alpha(colors.primary.main, 0.4)}`,
          '&:hover': {
            background: `linear-gradient(135deg, ${colors.primary.light} 0%, ${colors.primary.main} 100%)`,
            boxShadow: `0 6px 24px ${alpha(colors.primary.main, 0.5)}`,
            transform: 'translateY(-2px)',
          },
        },
        outlined: {
          borderWidth: 2,
          borderColor: alpha(colors.primary.main, 0.5),
          color: colors.primary.light,
          '&:hover': {
            borderWidth: 2,
            borderColor: colors.primary.main,
            backgroundColor: alpha(colors.primary.main, 0.1),
            boxShadow: `0 0 20px ${alpha(colors.primary.main, 0.3)}`,
          },
        },
        text: {
          color: colors.primary.light,
          '&:hover': {
            backgroundColor: alpha(colors.primary.main, 0.1),
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          background: darkGlass.background,
          backdropFilter: darkGlass.backdropFilter,
          border: darkGlass.border,
          boxShadow: darkShadows.card,
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative' as const,
          overflow: 'hidden',
          '&:hover': {
            boxShadow: darkShadows.elevated,
            borderColor: alpha(colors.primary.main, 0.2),
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 24,
          '&:last-child': {
            paddingBottom: 24,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: colors.slate[900],
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(colors.slate[400], 0.1)}`,
          padding: '16px 20px',
        },
        head: {
          backgroundColor: alpha(colors.primary.main, 0.08),
          fontWeight: 700,
          color: colors.slate[200],
          fontSize: '0.8125rem',
          textTransform: 'uppercase' as const,
          letterSpacing: '0.05em',
          borderBottom: `2px solid ${alpha(colors.primary.main, 0.3)}`,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background-color 0.2s ease',
          '&:hover': {
            backgroundColor: alpha(colors.primary.main, 0.05),
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 8,
          height: 28,
          fontSize: '0.8125rem',
        },
        filled: {
          background: alpha(colors.primary.main, 0.15),
          color: colors.primary.light,
          border: `1px solid ${alpha(colors.primary.main, 0.3)}`,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          height: 10,
          backgroundColor: alpha(colors.slate[600], 0.3),
          overflow: 'hidden',
        },
        bar: {
          borderRadius: 12,
          background: `linear-gradient(90deg, ${colors.primary.main} 0%, ${colors.secondary.main} 100%)`,
          boxShadow: `0 0 20px ${alpha(colors.primary.main, 0.5)}`,
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: colors.primary.main,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: alpha(colors.slate[800], 0.5),
            transition: 'all 0.3s ease',
            '& fieldset': {
              borderColor: alpha(colors.slate[400], 0.2),
              borderWidth: 2,
              transition: 'all 0.3s ease',
            },
            '&:hover fieldset': {
              borderColor: alpha(colors.primary.main, 0.4),
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.primary.main,
            },
          },
          '& .MuiInputLabel-root': {
            color: colors.slate[400],
            '&.Mui-focused': {
              color: colors.primary.light,
            },
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 24,
          background: colors.slate[900],
          border: `1px solid ${alpha(colors.slate[400], 0.1)}`,
          boxShadow: `0 32px 64px -12px rgba(0, 0, 0, 0.6)`,
          backdropFilter: 'blur(20px)',
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: '1.5rem',
          fontWeight: 700,
          padding: '28px 32px 16px',
          borderBottom: `1px solid ${alpha(colors.slate[400], 0.1)}`,
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: '24px 32px',
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '16px 32px 28px',
          gap: 12,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid',
          backdropFilter: 'blur(10px)',
        },
        standardSuccess: {
          backgroundColor: alpha(colors.success.main, 0.1),
          borderColor: alpha(colors.success.main, 0.3),
          color: colors.success.light,
        },
        standardWarning: {
          backgroundColor: alpha(colors.warning.main, 0.1),
          borderColor: alpha(colors.warning.main, 0.3),
          color: colors.warning.light,
        },
        standardError: {
          backgroundColor: alpha(colors.error.main, 0.1),
          borderColor: alpha(colors.error.main, 0.3),
          color: colors.error.light,
        },
        standardInfo: {
          backgroundColor: alpha(colors.primary.main, 0.1),
          borderColor: alpha(colors.primary.main, 0.3),
          color: colors.primary.light,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha(colors.primary.main, 0.1),
            transform: 'scale(1.1)',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: colors.slate[800],
          color: colors.slate[100],
          fontSize: '0.8125rem',
          fontWeight: 500,
          borderRadius: 8,
          padding: '8px 14px',
          border: `1px solid ${alpha(colors.slate[400], 0.1)}`,
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
        },
        arrow: {
          color: colors.slate[800],
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: alpha(colors.slate[400], 0.12),
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(colors.slate[600], 0.3),
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha(colors.primary.main, 0.08),
          },
          '&.Mui-selected': {
            backgroundColor: alpha(colors.primary.main, 0.15),
            '&:hover': {
              backgroundColor: alpha(colors.primary.main, 0.2),
            },
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          backgroundColor: colors.slate[850],
          border: `1px solid ${alpha(colors.slate[400], 0.1)}`,
          boxShadow: '0 16px 48px -8px rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(20px)',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '4px 8px',
          padding: '10px 16px',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha(colors.primary.main, 0.1),
          },
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          border: `2px solid ${alpha(colors.primary.main, 0.3)}`,
          boxShadow: `0 0 20px ${alpha(colors.primary.main, 0.2)}`,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          boxShadow: `0 0 10px ${alpha(colors.error.main, 0.5)}`,
        },
      },
    },
  },
});

// ═══════════════════════════════════════════════════════════════════════════
// LIGHT THEME - Blueprint Paper
// Warm, architectural aesthetic with paper-like textures
// ═══════════════════════════════════════════════════════════════════════════

const lightShadows = {
  card: `0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04)`,
  elevated: `0 4px 12px rgba(0, 0, 0, 0.1), 0 16px 32px -8px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.05)`,
};

export const lightTheme = createTheme({
  direction: 'rtl',
  palette: {
    mode: 'light',
    primary: {
      main: '#0284c7', // Slightly darker teal for better contrast
      light: '#0ea5e9',
      dark: '#0369a1',
      contrastText: '#ffffff',
    },
    secondary: colors.secondary,
    success: {
      main: '#059669',
      light: '#10b981',
      dark: '#047857',
    },
    warning: colors.warning,
    error: {
      main: '#dc2626',
      light: '#ef4444',
      dark: '#b91c1c',
    },
    background: {
      default: colors.paper.cream,
      paper: colors.paper.light,
    },
    text: {
      primary: colors.slate[900],  // Darker for better contrast
      secondary: colors.slate[600],
    },
    divider: alpha(colors.slate[400], 0.2),
  },
  typography: {
    fontFamily: '"Rubik", "Outfit", system-ui, sans-serif',
    h1: {
      fontSize: '3rem',
      fontWeight: 800,
      letterSpacing: '-0.03em',
      lineHeight: 1.1,
      fontFamily: '"Outfit", "Rubik", system-ui, sans-serif',
      color: colors.slate[900],
    },
    h2: {
      fontSize: '2.25rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
      fontFamily: '"Outfit", "Rubik", system-ui, sans-serif',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.3,
    },
    h4: {
      fontSize: '1.375rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.35,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.7,
      letterSpacing: '0.01em',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      letterSpacing: '0.01em',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: '0.02em',
    },
    caption: {
      fontSize: '0.75rem',
      letterSpacing: '0.03em',
    },
  },
  shape: {
    borderRadius: 16,
  },
  shadows: [
    'none',
    '0 1px 2px rgba(0,0,0,0.05)',
    '0 2px 4px rgba(0,0,0,0.06)',
    '0 4px 8px rgba(0,0,0,0.08)',
    lightShadows.card,
    lightShadows.elevated,
    lightShadows.elevated,
    ...Array(18).fill(lightShadows.elevated),
  ] as any,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 28px',
          fontSize: '0.9375rem',
          fontWeight: 600,
          boxShadow: 'none',
          position: 'relative' as const,
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          background: `linear-gradient(135deg, #0284c7 0%, #0369a1 100%)`,
          boxShadow: `0 4px 14px ${alpha('#0284c7', 0.25)}`,
          '&:hover': {
            background: `linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)`,
            boxShadow: `0 6px 20px ${alpha('#0284c7', 0.35)}`,
            transform: 'translateY(-2px)',
          },
        },
        outlined: {
          borderWidth: 2,
          borderColor: alpha('#0284c7', 0.5),
          color: '#0284c7',
          '&:hover': {
            borderWidth: 2,
            borderColor: '#0284c7',
            backgroundColor: alpha('#0284c7', 0.06),
          },
        },
        text: {
          color: '#0284c7',
          '&:hover': {
            backgroundColor: alpha('#0284c7', 0.06),
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          background: colors.paper.light,
          border: `1px solid ${colors.paper.border}`,
          boxShadow: lightShadows.card,
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative' as const,
          overflow: 'hidden',
          '&:hover': {
            boxShadow: lightShadows.elevated,
            borderColor: alpha('#0284c7', 0.2),
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 24,
          '&:last-child': {
            paddingBottom: 24,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: colors.paper.light,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(colors.slate[300], 0.5)}`,
          padding: '16px 20px',
          color: colors.slate[700],
        },
        head: {
          backgroundColor: alpha('#0284c7', 0.06),
          fontWeight: 700,
          color: colors.slate[800],
          fontSize: '0.8125rem',
          textTransform: 'uppercase' as const,
          letterSpacing: '0.05em',
          borderBottom: `2px solid ${alpha('#0284c7', 0.2)}`,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background-color 0.2s ease',
          '&:hover': {
            backgroundColor: alpha('#0284c7', 0.03),
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 8,
          height: 28,
          fontSize: '0.8125rem',
        },
        filled: {
          background: alpha('#0284c7', 0.1),
          color: '#0369a1',
          border: `1px solid ${alpha('#0284c7', 0.2)}`,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          height: 10,
          backgroundColor: alpha(colors.slate[300], 0.4),
          overflow: 'hidden',
        },
        bar: {
          borderRadius: 12,
          background: `linear-gradient(90deg, #0284c7 0%, #0ea5e9 100%)`,
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: '#0284c7',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: colors.paper.light,
            transition: 'all 0.3s ease',
            '& fieldset': {
              borderColor: alpha(colors.slate[400], 0.3),
              borderWidth: 2,
              transition: 'all 0.3s ease',
            },
            '&:hover fieldset': {
              borderColor: alpha('#0284c7', 0.4),
            },
            '&.Mui-focused fieldset': {
              borderColor: '#0284c7',
            },
          },
          '& .MuiInputLabel-root': {
            color: colors.slate[500],
            '&.Mui-focused': {
              color: '#0284c7',
            },
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 24,
          background: colors.paper.light,
          border: `1px solid ${colors.paper.border}`,
          boxShadow: `0 32px 64px -12px rgba(0, 0, 0, 0.15)`,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: '1.5rem',
          fontWeight: 700,
          padding: '28px 32px 16px',
          borderBottom: `1px solid ${colors.paper.border}`,
          color: colors.slate[800],
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: '24px 32px',
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '16px 32px 28px',
          gap: 12,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid',
        },
        standardSuccess: {
          backgroundColor: alpha('#059669', 0.08),
          borderColor: alpha('#059669', 0.25),
          color: '#047857',
        },
        standardWarning: {
          backgroundColor: alpha(colors.warning.main, 0.08),
          borderColor: alpha(colors.warning.main, 0.25),
          color: colors.warning.dark,
        },
        standardError: {
          backgroundColor: alpha('#dc2626', 0.08),
          borderColor: alpha('#dc2626', 0.25),
          color: '#b91c1c',
        },
        standardInfo: {
          backgroundColor: alpha('#0284c7', 0.08),
          borderColor: alpha('#0284c7', 0.25),
          color: '#0369a1',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha('#0284c7', 0.08),
            transform: 'scale(1.1)',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: colors.slate[800],
          color: colors.slate[100],
          fontSize: '0.8125rem',
          fontWeight: 500,
          borderRadius: 8,
          padding: '8px 14px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        },
        arrow: {
          color: colors.slate[800],
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: alpha(colors.slate[400], 0.2),
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: alpha(colors.slate[300], 0.4),
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha('#0284c7', 0.06),
          },
          '&.Mui-selected': {
            backgroundColor: alpha('#0284c7', 0.1),
            '&:hover': {
              backgroundColor: alpha('#0284c7', 0.14),
            },
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          backgroundColor: colors.paper.light,
          border: `1px solid ${colors.paper.border}`,
          boxShadow: '0 16px 48px -8px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '4px 8px',
          padding: '10px 16px',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: alpha('#0284c7', 0.06),
          },
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          border: `2px solid ${alpha('#0284c7', 0.2)}`,
          boxShadow: `0 2px 8px ${alpha('#0284c7', 0.15)}`,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          boxShadow: `0 0 8px ${alpha('#dc2626', 0.3)}`,
        },
      },
    },
  },
});

export default darkTheme;
