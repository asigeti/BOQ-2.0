'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  Divider,
  alpha,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DescriptionIcon,
  CloudUpload as UploadIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  ChevronRight as ChevronRightIcon,
  ChevronLeft as ChevronLeftIcon,
  Layers as LayersIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const DRAWER_WIDTH = 280;
const COLLAPSED_WIDTH = 80;

interface NavItem {
  title: string;
  titleEn: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    title: 'לוח בקרה',
    titleEn: 'Dashboard',
    path: '/dashboard',
    icon: <DashboardIcon />,
  },
  {
    title: 'העלאת קובץ',
    titleEn: 'Upload',
    path: '/dashboard/upload',
    icon: <UploadIcon />,
  },
  {
    title: 'הפרויקטים שלי',
    titleEn: 'My Projects',
    path: '/dashboard/projects',
    icon: <DescriptionIcon />,
  },
  {
    title: 'דוחות',
    titleEn: 'Reports',
    path: '/dashboard/reports',
    icon: <AssessmentIcon />,
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const drawerWidth = collapsed ? COLLAPSED_WIDTH : DRAWER_WIDTH;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderLeft: 'none',
          borderRight: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
          transition: 'width 0.3s ease-in-out',
          overflowX: 'hidden',
        },
      }}
    >
      {/* Logo Section */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 2,
          minHeight: 80,
        }}
      >
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: 2,
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.4)',
          }}
        >
          <LayersIcon sx={{ color: 'white', fontSize: 24 }} />
        </Box>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  whiteSpace: 'nowrap',
                }}
              >
                BOQ Pro
              </Typography>
              <Typography
                variant="caption"
                sx={{ color: 'text.secondary', display: 'block', mt: -0.5 }}
              >
                כתב כמויות חכם
              </Typography>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      <Divider sx={{ mx: 2 }} />

      {/* Navigation Items */}
      <List sx={{ px: 2, py: 3, flex: 1 }}>
        {navItems.map((item, index) => {
          const isActive = pathname === item.path || pathname?.startsWith(item.path + '/');

          return (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
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
                      borderRadius: 2,
                      minHeight: 48,
                      justifyContent: collapsed ? 'center' : 'flex-start',
                      px: collapsed ? 2 : 2.5,
                      backgroundColor: isActive
                        ? alpha('#6366f1', 0.1)
                        : 'transparent',
                      borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
                      '&:hover': {
                        backgroundColor: alpha('#6366f1', 0.08),
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: collapsed ? 0 : 2,
                        justifyContent: 'center',
                        color: isActive ? 'primary.main' : 'text.secondary',
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ListItemText
                            primary={item.title}
                            primaryTypographyProps={{
                              fontSize: '0.9375rem',
                              fontWeight: isActive ? 600 : 500,
                              color: isActive ? 'primary.main' : 'text.primary',
                            }}
                          />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </ListItemButton>
                </ListItem>
              </Tooltip>
            </motion.div>
          );
        })}
      </List>

      {/* Collapse Button */}
      <Box sx={{ p: 2 }}>
        <Divider sx={{ mb: 2 }} />
        <Box
          sx={{
            display: 'flex',
            justifyContent: collapsed ? 'center' : 'flex-end',
          }}
        >
          <IconButton
            onClick={() => setCollapsed(!collapsed)}
            sx={{
              backgroundColor: alpha('#6366f1', 0.1),
              '&:hover': {
                backgroundColor: alpha('#6366f1', 0.2),
              },
            }}
          >
            {collapsed ? <ChevronLeftIcon /> : <ChevronRightIcon />}
          </IconButton>
        </Box>
      </Box>
    </Drawer>
  );
}
