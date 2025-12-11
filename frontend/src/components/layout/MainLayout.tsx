'use client';

import { useState } from 'react';
import { Box } from '@mui/material';
import Sidebar, { DRAWER_WIDTH, COLLAPSED_WIDTH } from './Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const sidebarWidth = sidebarCollapsed ? COLLAPSED_WIDTH : DRAWER_WIDTH;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'row',
        minHeight: '100vh',
      }}
    >
      {/* Sidebar FIRST - in RTL, first item goes to the RIGHT */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content SECOND - fills remaining space on the LEFT */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: '#f8fafc',
          minHeight: '100vh',
          overflow: 'auto',
          transition: 'all 0.3s ease-in-out',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
