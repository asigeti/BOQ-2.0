'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import {
  Box,
  Typography,
  Card,
  CardContent,
  alpha,
  Grid,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  Description as FileIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';
import { useThemeMode } from '@/contexts/ThemeContext';

const Header = dynamic(() => import('@/components/layout/Header'), { ssr: false });

interface Report {
  id: number;
  name: string;
  type: string;
  created_at: string;
  status: string;
  total_value?: number;
}

interface ThemeColors {
  bg: string;
  bgCard: string;
  border: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  primary: string;
  shadow: string;
}

function StatCard({ title, value, icon, color, themeColors, isDark }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  themeColors: ThemeColors;
  isDark: boolean;
}) {
  return (
    <Card
      sx={{
        height: '100%',
        backgroundColor: themeColors.bgCard,
        backdropFilter: isDark ? 'blur(20px)' : 'none',
        border: `1px solid ${alpha(color, 0.2)}`,
        borderRadius: '20px',
        boxShadow: isDark ? `0 8px 32px ${alpha(color, 0.15)}` : `0 4px 16px ${alpha(color, 0.1)}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: isDark ? `0 12px 40px ${alpha(color, 0.25)}` : `0 8px 24px ${alpha(color, 0.15)}`,
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography
              variant="body2"
              sx={{
                color: themeColors.textMuted,
                mb: 1,
                fontSize: '0.85rem',
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 800,
                background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.7)} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.7)} 100%)`,
              boxShadow: `0 8px 24px ${alpha(color, isDark ? 0.4 : 0.25)}`,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function ReportCard({ report, themeColors, isDark }: { report: Report; themeColors: ThemeColors; isDark: boolean }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'processing': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#64748b';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'מוכן';
      case 'processing': return 'בעיבוד';
      case 'error': return 'שגיאה';
      default: return status;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Card
      sx={{
        backgroundColor: themeColors.bgCard,
        backdropFilter: isDark ? 'blur(20px)' : 'none',
        border: `1px solid ${themeColors.border}`,
        borderRadius: '16px',
        boxShadow: themeColors.shadow,
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: isDark ? '0 8px 32px rgba(0, 0, 0, 0.3)' : '0 8px 24px rgba(0, 0, 0, 0.12)',
          borderColor: isDark ? 'rgba(14, 165, 233, 0.3)' : 'rgba(3, 105, 161, 0.4)',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isDark
                    ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)'
                    : 'linear-gradient(135deg, rgba(3, 105, 161, 0.15) 0%, rgba(3, 105, 161, 0.08) 100%)',
                  border: isDark ? '1px solid rgba(14, 165, 233, 0.3)' : '1px solid rgba(3, 105, 161, 0.3)',
                }}
              >
                <FileIcon sx={{ color: themeColors.primary }} />
              </Box>
              <Box>
                <Typography
                  variant="subtitle1"
                  sx={{
                    fontWeight: 600,
                    color: themeColors.textPrimary,
                  }}
                >
                  {report.name}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{ color: themeColors.textMuted }}
                >
                  {report.type}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <CalendarIcon sx={{ fontSize: 16, color: themeColors.textMuted }} />
                <Typography variant="body2" sx={{ color: themeColors.textMuted }}>
                  {new Date(report.created_at).toLocaleDateString('he-IL')}
                </Typography>
              </Box>
              {report.total_value && (
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: themeColors.primary,
                  }}
                >
                  {formatCurrency(report.total_value)}
                </Typography>
              )}
              <Chip
                label={getStatusLabel(report.status)}
                size="small"
                sx={{
                  backgroundColor: alpha(getStatusColor(report.status), 0.15),
                  color: getStatusColor(report.status),
                  border: `1px solid ${alpha(getStatusColor(report.status), 0.3)}`,
                  fontWeight: 600,
                  fontSize: '0.7rem',
                }}
              />
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="צפייה">
              <IconButton
                size="small"
                sx={{
                  width: 36,
                  height: 36,
                  backgroundColor: isDark ? 'rgba(14, 165, 233, 0.1)' : 'rgba(3, 105, 161, 0.08)',
                  border: isDark ? '1px solid rgba(14, 165, 233, 0.2)' : '1px solid rgba(3, 105, 161, 0.2)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: isDark ? 'rgba(14, 165, 233, 0.2)' : 'rgba(3, 105, 161, 0.15)',
                    transform: 'scale(1.1)',
                  },
                }}
              >
                <ViewIcon sx={{ fontSize: 18, color: themeColors.primary }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="הורדה">
              <IconButton
                size="small"
                sx={{
                  width: 36,
                  height: 36,
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    transform: 'scale(1.1)',
                  },
                }}
              >
                <DownloadIcon sx={{ fontSize: 18, color: '#10b981' }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalReports: 0,
    completedReports: 0,
    totalValue: 0,
  });
  const { isDark } = useThemeMode();

  // Theme-aware colors
  const colors: ThemeColors = {
    bg: isDark ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.95)',
    bgCard: isDark ? 'rgba(15, 23, 42, 0.8)' : '#ffffff',
    border: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(15, 23, 42, 0.1)',
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
    primary: isDark ? '#0ea5e9' : '#0369a1',
    shadow: isDark ? '0 8px 32px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.06)',
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      // Try to get plans/BOQs as reports
      const response = await api.get('/plans/');
      const plansData = response.data || [];

      // Transform plans to reports format
      const reportsData = plansData.map((plan: any) => ({
        id: plan.id,
        name: plan.original_filename || `כתב כמויות #${plan.id}`,
        type: 'כתב כמויות',
        created_at: plan.created_at,
        status: plan.processing_status || 'completed',
        total_value: plan.boq_result?.grand_total || 0,
      }));

      setReports(reportsData);

      // Calculate stats
      const completed = reportsData.filter((r: Report) => r.status === 'completed').length;
      const totalVal = reportsData.reduce((sum: number, r: Report) => sum + (r.total_value || 0), 0);

      setStats({
        totalReports: reportsData.length,
        completedReports: completed,
        totalValue: totalVal,
      });
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <MainLayout>
      <Header title="דוחות" subtitle="צפייה בכל כתבי הכמויות והדוחות שנוצרו" />

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard
            title="סה״כ דוחות"
            value={stats.totalReports}
            icon={<AssessmentIcon sx={{ color: 'white', fontSize: 24 }} />}
            color="#0ea5e9"
            themeColors={colors}
            isDark={isDark}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard
            title="דוחות מוכנים"
            value={stats.completedReports}
            icon={<TrendingUpIcon sx={{ color: 'white', fontSize: 24 }} />}
            color="#10b981"
            themeColors={colors}
            isDark={isDark}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard
            title="סה״כ שווי"
            value={formatCurrency(stats.totalValue)}
            icon={<TrendingUpIcon sx={{ color: 'white', fontSize: 24 }} />}
            color="#f59e0b"
            themeColors={colors}
            isDark={isDark}
          />
        </Grid>
      </Grid>

      {/* Reports List */}
      <Box>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            color: colors.textPrimary,
            mb: 2,
          }}
        >
          רשימת דוחות
        </Typography>

        {loading ? (
          <Card
            sx={{
              backgroundColor: colors.bgCard,
              backdropFilter: isDark ? 'blur(20px)' : 'none',
              border: `1px solid ${colors.border}`,
              borderRadius: '16px',
            }}
          >
            <CardContent>
              <LinearProgress
                sx={{
                  backgroundColor: isDark ? 'rgba(14, 165, 233, 0.1)' : 'rgba(3, 105, 161, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: 'linear-gradient(90deg, #0ea5e9, #06b6d4)',
                  },
                }}
              />
            </CardContent>
          </Card>
        ) : reports.length === 0 ? (
          <Card
            sx={{
              backgroundColor: colors.bgCard,
              backdropFilter: isDark ? 'blur(20px)' : 'none',
              border: `1px solid ${colors.border}`,
              borderRadius: '20px',
              boxShadow: colors.shadow,
            }}
          >
            <CardContent sx={{ textAlign: 'center', py: 8 }}>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 3,
                  borderRadius: '20px',
                  background: isDark
                    ? 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)'
                    : 'linear-gradient(135deg, rgba(3, 105, 161, 0.15) 0%, rgba(3, 105, 161, 0.08) 100%)',
                  border: isDark ? '1px solid rgba(14, 165, 233, 0.3)' : '1px solid rgba(3, 105, 161, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AssessmentIcon sx={{ fontSize: 40, color: colors.primary }} />
              </Box>
              <Typography
                variant="h6"
                sx={{
                  color: colors.textPrimary,
                  fontWeight: 600,
                  mb: 1,
                }}
              >
                אין דוחות עדיין
              </Typography>
              <Typography variant="body2" sx={{ color: colors.textMuted }}>
                העלה תוכנית כדי ליצור כתב כמויות ראשון
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} themeColors={colors} isDark={isDark} />
            ))}
          </Box>
        )}
      </Box>
    </MainLayout>
  );
}
