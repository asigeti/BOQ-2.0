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
        flexDirection: 'row-reverse', // RTL: sidebar on right
        minHeight: '100vh',
      }}
    >
      {/* Sidebar on the right */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: '#f8fafc',
          minHeight: '100vh',
          overflow: 'auto',
          transition: 'margin 0.3s ease-in-out',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
