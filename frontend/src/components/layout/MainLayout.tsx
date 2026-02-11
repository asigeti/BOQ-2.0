'use client';

import { useState } from 'react';
import { Box } from '@mui/material';
import Sidebar, { DRAWER_WIDTH, COLLAPSED_WIDTH } from './Sidebar';
import { useThemeMode } from '@/contexts/ThemeContext';

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { isDark } = useThemeMode();

  // Theme-aware background colors
  const bgBase = isDark ? '#0a0f1a' : '#f1f5f9';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'row',
        minHeight: '100vh',
        backgroundColor: bgBase,
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
        className="blueprint-grid"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          minHeight: '100vh',
          overflow: 'auto',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          // Gradient mesh background - theme-aware
          background: isDark
            ? `
              radial-gradient(at 40% 20%, rgba(14, 165, 233, 0.12) 0px, transparent 50%),
              radial-gradient(at 80% 0%, rgba(245, 158, 11, 0.08) 0px, transparent 50%),
              radial-gradient(at 0% 50%, rgba(14, 165, 233, 0.08) 0px, transparent 50%),
              radial-gradient(at 80% 50%, rgba(16, 185, 129, 0.06) 0px, transparent 50%),
              radial-gradient(at 0% 100%, rgba(245, 158, 11, 0.08) 0px, transparent 50%),
              #0a0f1a
            `
            : `
              radial-gradient(at 40% 20%, rgba(3, 105, 161, 0.04) 0px, transparent 50%),
              radial-gradient(at 80% 0%, rgba(217, 119, 6, 0.03) 0px, transparent 50%),
              radial-gradient(at 0% 50%, rgba(3, 105, 161, 0.03) 0px, transparent 50%),
              radial-gradient(at 80% 50%, rgba(5, 150, 105, 0.02) 0px, transparent 50%),
              radial-gradient(at 0% 100%, rgba(217, 119, 6, 0.03) 0px, transparent 50%),
              #f1f5f9
            `,
          backgroundAttachment: 'fixed',
          // Subtle grid pattern overlay - theme-aware
          '&::before': {
            content: '""',
            position: 'fixed',
            inset: 0,
            backgroundImage: isDark
              ? `
                linear-gradient(rgba(14, 165, 233, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(14, 165, 233, 0.02) 1px, transparent 1px)
              `
              : `
                linear-gradient(rgba(3, 105, 161, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(3, 105, 161, 0.03) 1px, transparent 1px)
              `,
            backgroundSize: '60px 60px',
            pointerEvents: 'none',
            zIndex: 0,
          },
          // Content wrapper
          '& > *': {
            position: 'relative',
            zIndex: 1,
          },
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
