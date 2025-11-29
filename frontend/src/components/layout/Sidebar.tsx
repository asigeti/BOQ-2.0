'use client';

import { useState } from 'react';
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
  Divider,
  alpha,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DescriptionIcon,
  CloudUpload as UploadIcon,
  Assessment as AssessmentIcon,
  ChevronRight as ChevronRightIcon,
  ChevronLeft as ChevronLeftIcon,
  Layers as LayersIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

export const DRAWER_WIDTH = 260;
export const COLLAPSED_WIDTH = 72;

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

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const drawerWidth = collapsed ? COLLAPSED_WIDTH : DRAWER_WIDTH;

  return (
    <Box
      component="nav"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        height: '100vh',
        position: 'sticky',
        top: 0,
        borderLeft: '1px solid',
        borderColor: 'divider',
        background: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
        transition: 'width 0.3s ease-in-out',
        overflowX: 'hidden',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Logo Section */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 2,
          minHeight: 72,
        }}
      >
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.4)',
            flexShrink: 0,
          }}
        >
          <LayersIcon sx={{ color: 'white', fontSize: 22 }} />
        </Box>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
              style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}
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
                  fontSize: '1.1rem',
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
      <List sx={{ px: 1.5, py: 2, flex: 1 }}>
        {navItems.map((item, index) => {
          const isActive = pathname === item.path || pathname?.startsWith(item.path + '/');

          return (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Tooltip
                title={collapsed ? item.title : ''}
                placement="left"
                arrow
              >
                <ListItem disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => router.push(item.path)}
                    sx={{
                      borderRadius: 2,
                      minHeight: 44,
                      justifyContent: collapsed ? 'center' : 'flex-start',
                      px: collapsed ? 1.5 : 2,
                      backgroundColor: isActive
                        ? alpha('#6366f1', 0.1)
                        : 'transparent',
                      borderRight: isActive ? '3px solid #6366f1' : '3px solid transparent',
                      '&:hover': {
                        backgroundColor: alpha('#6366f1', 0.08),
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        ml: collapsed ? 0 : 2,
                        justifyContent: 'center',
                        color: isActive ? 'primary.main' : 'text.secondary',
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.div
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          transition={{ duration: 0.2 }}
                          style={{ overflow: 'hidden' }}
                        >
                          <ListItemText
                            primary={item.title}
                            primaryTypographyProps={{
                              fontSize: '0.875rem',
                              fontWeight: isActive ? 600 : 500,
                              color: isActive ? 'primary.main' : 'text.primary',
                              whiteSpace: 'nowrap',
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
      <Box sx={{ p: 1.5 }}>
        <Divider sx={{ mb: 1.5 }} />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <IconButton
            onClick={onToggle}
            size="small"
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
    </Box>
  );
}
