'use client';

import { useRouter, usePathname } from 'next/navigation';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  alpha,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  FolderOpen as FolderIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  ChevronRight as ChevronRightIcon,
  ChevronLeft as ChevronLeftIcon,
  Architecture as LogoIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { useThemeMode } from '@/contexts/ThemeContext';

export const DRAWER_WIDTH = 280;
export const COLLAPSED_WIDTH = 80;

interface NavItem {
  title: string;
  titleEn: string;
  path: string;
  icon: React.ReactNode;
  color: string;
}

const navItems: NavItem[] = [
  {
    title: 'לוח בקרה',
    titleEn: 'Dashboard',
    path: '/dashboard',
    icon: <DashboardIcon />,
    color: '#0ea5e9',
  },
  {
    title: 'פרויקטים',
    titleEn: 'Projects',
    path: '/dashboard/projects',
    icon: <FolderIcon />,
    color: '#f59e0b',
  },
  {
    title: 'דוחות',
    titleEn: 'Reports',
    path: '/dashboard/reports',
    icon: <AssessmentIcon />,
    color: '#10b981',
  },
  {
    title: 'הגדרות',
    titleEn: 'Settings',
    path: '/dashboard/settings',
    icon: <SettingsIcon />,
    color: '#8b5cf6',
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();
  const { isDark } = useThemeMode();

  const drawerWidth = collapsed ? COLLAPSED_WIDTH : DRAWER_WIDTH;

  // Theme-aware colors
  const colors = {
    bg: isDark ? 'rgba(15, 23, 42, 0.95)' : '#ffffff',
    border: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.1)',
    borderAccent: isDark ? 'rgba(14, 165, 233, 0.5)' : 'rgba(3, 105, 161, 0.5)',
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
    iconInactive: isDark ? '#64748b' : '#64748b',
    hoverBg: isDark ? 'rgba(14, 165, 233, 0.15)' : 'rgba(3, 105, 161, 0.12)',
    buttonBg: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.05)',
  };

  return (
    <Box
      component="nav"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        height: '100vh',
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        background: colors.bg,
        backdropFilter: 'blur(20px) saturate(180%)',
        borderLeft: `1px solid ${colors.border}`,
        transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s ease',
        overflowX: 'hidden',
        overflowY: 'auto',
        zIndex: 1200,
      }}
    >
      {/* Logo Section */}
      <Box
        sx={{
          p: collapsed ? 2 : 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 2,
          minHeight: 80,
          borderBottom: `1px solid ${colors.border}`,
          position: 'relative',
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: -1,
            left: '10%',
            right: '10%',
            height: '1px',
            background: `linear-gradient(90deg, transparent, ${colors.borderAccent}, transparent)`,
          },
        }}
      >
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isDark
              ? '0 8px 32px rgba(14, 165, 233, 0.3)'
              : '0 4px 16px rgba(2, 132, 199, 0.2)',
            position: 'relative',
            flexShrink: 0,
            '&::before': {
              content: '""',
              position: 'absolute',
              inset: -2,
              borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.5), rgba(245, 158, 11, 0.3))',
              zIndex: -1,
              opacity: isDark ? 0.5 : 0.3,
            },
          }}
        >
          <LogoIcon sx={{ color: 'white', fontSize: 26 }} />
        </Box>

        <Box
          sx={{
            overflow: 'hidden',
            whiteSpace: 'nowrap',
            opacity: collapsed ? 0 : 1,
            width: collapsed ? 0 : 'auto',
            transition: 'all 0.2s ease-in-out',
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontWeight: 800,
              fontSize: '1.25rem',
              letterSpacing: '-0.02em',
              background: isDark
                ? 'linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%)'
                : 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              whiteSpace: 'nowrap',
            }}
          >
            BOQ Pro
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: -0.5 }}>
            <AIIcon sx={{ fontSize: 12, color: isDark ? '#0ea5e9' : '#0284c7' }} />
            <Typography
              variant="caption"
              sx={{
                color: colors.textMuted,
                fontSize: '0.7rem',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                fontWeight: 500,
              }}
            >
              AI-Powered
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation Items */}
      <List sx={{ px: collapsed ? 1 : 2, py: 3, flex: 1 }}>
        {navItems.map((item, index) => {
          const isActive = item.path === '/dashboard'
            ? pathname === '/dashboard'
            : pathname === item.path || pathname?.startsWith(item.path + '/');

          return (
            <Box
              key={item.path}
              sx={{
                animation: 'fadeInRight 0.4s ease-out forwards',
                animationDelay: `${index * 0.08}s`,
                opacity: 0,
                '@keyframes fadeInRight': {
                  '0%': { opacity: 0, transform: 'translateX(20px)' },
                  '100%': { opacity: 1, transform: 'translateX(0)' },
                },
              }}
            >
              <Tooltip
                title={collapsed ? item.title : ''}
                placement="left"
                arrow
              >
                <ListItem disablePadding sx={{ mb: 1 }}>
                  <ListItemButton
                    onClick={() => router.push(item.path)}
                    sx={{
                      borderRadius: '14px',
                      minHeight: 50,
                      justifyContent: collapsed ? 'center' : 'flex-start',
                      px: collapsed ? 1.5 : 2,
                      position: 'relative',
                      overflow: 'hidden',
                      transition: 'all 0.3s ease',
                      backgroundColor: isActive
                        ? alpha(item.color, 0.15)
                        : 'transparent',
                      border: isActive
                        ? `1px solid ${alpha(item.color, 0.3)}`
                        : '1px solid transparent',
                      '&::before': isActive ? {
                        content: '""',
                        position: 'absolute',
                        right: 0,
                        top: '20%',
                        bottom: '20%',
                        width: '3px',
                        background: item.color,
                        borderRadius: '3px 0 0 3px',
                        boxShadow: `0 0 12px ${item.color}`,
                      } : {},
                      '&:hover': {
                        backgroundColor: isActive
                          ? alpha(item.color, 0.2)
                          : alpha(item.color, 0.08),
                        transform: 'translateX(-4px)',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        ml: collapsed ? 0 : 1,
                        mr: collapsed ? 0 : 2,
                        justifyContent: 'center',
                        color: isActive ? item.color : colors.iconInactive,
                        transition: 'color 0.2s ease',
                        '& svg': {
                          fontSize: 24,
                          filter: isActive && isDark ? `drop-shadow(0 0 8px ${item.color})` : 'none',
                        },
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <Box
                      sx={{
                        overflow: 'hidden',
                        opacity: collapsed ? 0 : 1,
                        width: collapsed ? 0 : 'auto',
                        transition: 'all 0.2s ease-in-out',
                      }}
                    >
                      <ListItemText
                        primary={item.title}
                        primaryTypographyProps={{
                          fontSize: '0.95rem',
                          fontWeight: isActive ? 600 : 500,
                          color: isActive ? colors.textPrimary : colors.textSecondary,
                          whiteSpace: 'nowrap',
                        }}
                      />
                    </Box>
                  </ListItemButton>
                </ListItem>
              </Tooltip>
            </Box>
          );
        })}
      </List>

      {/* Collapse Button & Version */}
      <Box sx={{ p: 2, borderTop: `1px solid ${colors.border}` }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: collapsed ? 'center' : 'flex-end',
            mb: collapsed ? 0 : 2,
          }}
        >
          <Tooltip title={collapsed ? 'הרחב' : 'צמצם'} placement="left">
            <IconButton
              onClick={onToggle}
              sx={{
                width: 36,
                height: 36,
                backgroundColor: colors.buttonBg,
                color: colors.iconInactive,
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: colors.hoverBg,
                  color: isDark ? '#0ea5e9' : '#0284c7',
                  transform: 'scale(1.1)',
                },
              }}
            >
              {collapsed ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
          </Tooltip>
        </Box>

        {!collapsed && (
          <Typography
            variant="caption"
            sx={{
              color: colors.textSecondary,
              fontSize: '0.65rem',
              letterSpacing: '0.05em',
              display: 'block',
              textAlign: 'center',
            }}
          >
            גרסה 2.0 • מופעל ע״י AI
          </Typography>
        )}
      </Box>
    </Box>
  );
}
