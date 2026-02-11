'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  alpha,
  Badge,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  HelpOutline as HelpIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  AutoAwesome as AIIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
} from '@mui/icons-material';
import { useThemeMode } from '@/contexts/ThemeContext';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mounted, setMounted] = useState(false);
  const { mode, toggleTheme, isDark } = useThemeMode();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Theme-aware colors
  const colors = {
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
    border: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(15, 23, 42, 0.12)',
    borderAccent: isDark ? 'rgba(14, 165, 233, 0.3)' : 'rgba(3, 105, 161, 0.4)',
    bgSubtle: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.05)',
    bgHover: isDark ? 'rgba(14, 165, 233, 0.08)' : 'rgba(3, 105, 161, 0.1)',
    menuBg: isDark ? '#0f172a' : '#ffffff',
    primary: isDark ? '#0ea5e9' : '#0369a1',
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  if (!mounted) {
    return null;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        mb: 4,
        pb: 3,
        borderBottom: '1px solid',
        borderColor: colors.border,
        position: 'relative',
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: -1,
          left: 0,
          width: '120px',
          height: '2px',
          background: `linear-gradient(90deg, ${colors.primary}, transparent)`,
          borderRadius: '2px',
        },
      }}
    >
      {/* Title Section */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              fontSize: { xs: '1.5rem', md: '2rem' },
              letterSpacing: '-0.02em',
              background: isDark
                ? 'linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%)'
                : 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {title}
          </Typography>
          <Chip
            icon={<AIIcon sx={{ fontSize: 14, color: `${colors.primary} !important` }} />}
            label="AI"
            size="small"
            sx={{
              height: 24,
              backgroundColor: isDark ? 'rgba(14, 165, 233, 0.1)' : 'rgba(2, 132, 199, 0.1)',
              border: `1px solid ${colors.borderAccent}`,
              color: colors.primary,
              fontWeight: 600,
              fontSize: '0.7rem',
              '& .MuiChip-icon': {
                marginLeft: '6px',
              },
            }}
          />
        </Box>
        {subtitle && (
          <Typography
            variant="body2"
            sx={{
              color: colors.textMuted,
              fontSize: '0.9rem',
              letterSpacing: '0.01em',
            }}
          >
            {subtitle}
          </Typography>
        )}
      </Box>

      {/* Actions Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        {/* Search */}
        <Box
          sx={{
            display: { xs: 'none', md: 'flex' },
            alignItems: 'center',
            backgroundColor: colors.bgSubtle,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            px: 2,
            py: 1,
            minWidth: 200,
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            '&:hover': {
              backgroundColor: colors.bgHover,
              borderColor: colors.borderAccent,
            },
          }}
        >
          <SearchIcon sx={{ color: colors.textMuted, mr: 1.5, fontSize: 20 }} />
          <Typography variant="body2" sx={{ color: colors.textMuted, fontSize: '0.875rem' }}>
            חיפוש...
          </Typography>
          <Box
            sx={{
              ml: 'auto',
              display: 'flex',
              gap: 0.5,
            }}
          >
            <Box
              sx={{
                px: 0.8,
                py: 0.2,
                backgroundColor: isDark ? 'rgba(148, 163, 184, 0.15)' : 'rgba(30, 41, 59, 0.1)',
                borderRadius: '4px',
                fontSize: '0.65rem',
                color: colors.textMuted,
                fontWeight: 600,
              }}
            >
              ⌘
            </Box>
            <Box
              sx={{
                px: 0.8,
                py: 0.2,
                backgroundColor: isDark ? 'rgba(148, 163, 184, 0.15)' : 'rgba(30, 41, 59, 0.1)',
                borderRadius: '4px',
                fontSize: '0.65rem',
                color: colors.textMuted,
                fontWeight: 600,
              }}
            >
              K
            </Box>
          </Box>
        </Box>

        {/* Theme Toggle */}
        <Tooltip title={isDark ? 'מצב בהיר' : 'מצב כהה'} arrow>
          <IconButton
            onClick={toggleTheme}
            sx={{
              width: 42,
              height: 42,
              backgroundColor: isDark
                ? 'rgba(251, 191, 36, 0.1)'
                : 'rgba(99, 102, 241, 0.1)',
              border: '1px solid',
              borderColor: isDark
                ? 'rgba(251, 191, 36, 0.3)'
                : 'rgba(99, 102, 241, 0.3)',
              color: isDark ? '#fbbf24' : '#6366f1',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              transform: 'rotate(0deg)',
              '&:hover': {
                backgroundColor: isDark
                  ? 'rgba(251, 191, 36, 0.2)'
                  : 'rgba(99, 102, 241, 0.2)',
                borderColor: isDark
                  ? 'rgba(251, 191, 36, 0.5)'
                  : 'rgba(99, 102, 241, 0.5)',
                transform: 'rotate(15deg) scale(1.1)',
              },
              '&:active': {
                transform: 'rotate(-15deg) scale(0.95)',
              },
            }}
          >
            {isDark ? (
              <LightModeIcon
                sx={{
                  fontSize: 20,
                  transition: 'transform 0.3s ease',
                }}
              />
            ) : (
              <DarkModeIcon
                sx={{
                  fontSize: 20,
                  transition: 'transform 0.3s ease',
                }}
              />
            )}
          </IconButton>
        </Tooltip>

        {/* Help */}
        <IconButton
          sx={{
            width: 42,
            height: 42,
            backgroundColor: colors.bgSubtle,
            border: `1px solid ${colors.border}`,
            color: colors.textMuted,
            transition: 'all 0.2s ease',
            '&:hover': {
              backgroundColor: colors.bgHover,
              borderColor: colors.borderAccent,
              color: colors.primary,
            },
          }}
        >
          <HelpIcon sx={{ fontSize: 20 }} />
        </IconButton>

        {/* Notifications */}
        <IconButton
          sx={{
            width: 42,
            height: 42,
            backgroundColor: colors.bgSubtle,
            border: `1px solid ${colors.border}`,
            color: colors.textMuted,
            transition: 'all 0.2s ease',
            '&:hover': {
              backgroundColor: colors.bgHover,
              borderColor: colors.borderAccent,
              color: colors.primary,
            },
          }}
        >
          <Badge
            badgeContent={3}
            sx={{
              '& .MuiBadge-badge': {
                fontSize: '0.65rem',
                height: 18,
                minWidth: 18,
                backgroundColor: '#f43f5e',
                color: 'white',
                fontWeight: 600,
                boxShadow: '0 0 12px rgba(244, 63, 94, 0.5)',
              },
            }}
          >
            <NotificationsIcon sx={{ fontSize: 20 }} />
          </Badge>
        </IconButton>

        {/* User Menu */}
        <Box
          onClick={handleMenuOpen}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            cursor: 'pointer',
            p: 1,
            pr: 2,
            borderRadius: '14px',
            backgroundColor: colors.bgSubtle,
            border: `1px solid ${colors.border}`,
            transition: 'all 0.2s ease',
            '&:hover': {
              backgroundColor: colors.bgHover,
              borderColor: colors.borderAccent,
            },
          }}
        >
          <Avatar
            sx={{
              width: 34,
              height: 34,
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              fontSize: '0.9rem',
              fontWeight: 700,
              border: `2px solid ${colors.borderAccent}`,
              boxShadow: isDark
                ? '0 4px 16px rgba(14, 165, 233, 0.3)'
                : '0 2px 8px rgba(2, 132, 199, 0.2)',
            }}
          >
            א
          </Avatar>
          <Box sx={{ display: { xs: 'none', md: 'block' } }}>
            <Typography
              sx={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: colors.textPrimary,
                lineHeight: 1.2,
              }}
            >
              משתמש אורח
            </Typography>
            <Typography
              sx={{
                fontSize: '0.7rem',
                color: colors.textMuted,
                lineHeight: 1.2,
              }}
            >
              חשבון חינם
            </Typography>
          </Box>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'left', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
          PaperProps={{
            sx: {
              mt: 1.5,
              minWidth: 220,
              borderRadius: '16px',
              backgroundColor: colors.menuBg,
              border: `1px solid ${colors.border}`,
              boxShadow: isDark
                ? '0 20px 40px -12px rgba(0, 0, 0, 0.5)'
                : '0 12px 32px -8px rgba(0, 0, 0, 0.15)',
              backdropFilter: 'blur(20px)',
            },
          }}
        >
          <Box sx={{ px: 2.5, py: 2 }}>
            <Typography sx={{ fontWeight: 600, color: colors.textPrimary, fontSize: '0.95rem' }}>
              משתמש אורח
            </Typography>
            <Typography sx={{ color: colors.textMuted, fontSize: '0.8rem' }}>
              guest@example.com
            </Typography>
          </Box>
          <Divider sx={{ borderColor: colors.border }} />
          <MenuItem
            onClick={handleMenuClose}
            sx={{
              py: 1.5,
              mx: 1,
              my: 0.5,
              borderRadius: '8px',
              '&:hover': {
                backgroundColor: colors.bgHover,
              },
            }}
          >
            <PersonIcon sx={{ mr: 2, fontSize: 20, color: colors.textMuted }} />
            <Typography sx={{ color: colors.textPrimary, fontSize: '0.9rem' }}>הפרופיל שלי</Typography>
          </MenuItem>
          <MenuItem
            onClick={handleMenuClose}
            sx={{
              py: 1.5,
              mx: 1,
              my: 0.5,
              borderRadius: '8px',
              '&:hover': {
                backgroundColor: colors.bgHover,
              },
            }}
          >
            <SettingsIcon sx={{ mr: 2, fontSize: 20, color: colors.textMuted }} />
            <Typography sx={{ color: colors.textPrimary, fontSize: '0.9rem' }}>הגדרות</Typography>
          </MenuItem>
          <Divider sx={{ borderColor: colors.border }} />
          <MenuItem
            onClick={handleMenuClose}
            sx={{
              py: 1.5,
              mx: 1,
              my: 0.5,
              borderRadius: '8px',
              '&:hover': {
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
              },
            }}
          >
            <LogoutIcon sx={{ mr: 2, fontSize: 20, color: '#f43f5e' }} />
            <Typography sx={{ color: '#f43f5e', fontSize: '0.9rem' }}>התנתקות</Typography>
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
