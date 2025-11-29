'use client';

import {
  Box,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  alpha,
  InputBase,
  Badge,
} from '@mui/material';
import {
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  HelpOutline as HelpIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useState } from 'react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        mb: 4,
        pb: 3,
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      {/* Title Section */}
      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mb: 0.5,
          }}
        >
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>

      {/* Actions Section */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Search */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: alpha('#64748b', 0.08),
            borderRadius: 2,
            px: 2,
            py: 1,
            minWidth: 240,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: alpha('#64748b', 0.12),
            },
            '&:focus-within': {
              backgroundColor: '#fff',
              boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.2)',
            },
          }}
        >
          <SearchIcon sx={{ color: 'text.secondary', mr: 1, fontSize: 20 }} />
          <InputBase
            placeholder="חיפוש..."
            sx={{
              flex: 1,
              fontSize: '0.875rem',
              '& input::placeholder': {
                color: 'text.secondary',
                opacity: 1,
              },
            }}
          />
        </Box>

        {/* Help */}
        <IconButton
          sx={{
            backgroundColor: alpha('#64748b', 0.08),
            '&:hover': {
              backgroundColor: alpha('#64748b', 0.15),
            },
          }}
        >
          <HelpIcon sx={{ fontSize: 22 }} />
        </IconButton>

        {/* Notifications */}
        <IconButton
          sx={{
            backgroundColor: alpha('#64748b', 0.08),
            '&:hover': {
              backgroundColor: alpha('#64748b', 0.15),
            },
          }}
        >
          <Badge
            badgeContent={3}
            color="error"
            sx={{
              '& .MuiBadge-badge': {
                fontSize: '0.65rem',
                height: 18,
                minWidth: 18,
              },
            }}
          >
            <NotificationsIcon sx={{ fontSize: 22 }} />
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
            borderRadius: 2,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: alpha('#64748b', 0.08),
            },
          }}
        >
          <Avatar
            sx={{
              width: 38,
              height: 38,
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              fontSize: '0.95rem',
              fontWeight: 600,
            }}
          >
            א
          </Avatar>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'left', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
          PaperProps={{
            elevation: 3,
            sx: {
              mt: 1.5,
              minWidth: 200,
              borderRadius: 2,
              overflow: 'visible',
              '&:before': {
                content: '""',
                display: 'block',
                position: 'absolute',
                top: 0,
                left: 24,
                width: 10,
                height: 10,
                bgcolor: 'background.paper',
                transform: 'translateY(-50%) rotate(45deg)',
                zIndex: 0,
              },
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              משתמש אורח
            </Typography>
            <Typography variant="body2" color="text.secondary">
              guest@example.com
            </Typography>
          </Box>
          <Divider />
          <MenuItem onClick={handleMenuClose}>
            <PersonIcon sx={{ mr: 1.5, fontSize: 20, color: 'text.secondary' }} />
            הפרופיל שלי
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <SettingsIcon sx={{ mr: 1.5, fontSize: 20, color: 'text.secondary' }} />
            הגדרות
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>
            <LogoutIcon sx={{ mr: 1.5, fontSize: 20 }} />
            התנתקות
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
