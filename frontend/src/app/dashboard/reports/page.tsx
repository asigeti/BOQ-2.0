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

const Header = dynamic(() => import('@/components/layout/Header'), { ssr: false });

interface Report {
  id: number;
  name: string;
  type: string;
  created_at: string;
  status: string;
  total_value?: number;
}

function StatCard({ title, value, icon, color }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.02)} 100%)`,
        border: `1px solid ${alpha(color, 0.15)}`,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700} sx={{ color }}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.7)} 100%)`,
              boxShadow: `0 4px 14px ${alpha(color, 0.4)}`,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function ReportCard({ report }: { report: Report }) {
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
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: alpha('#6366f1', 0.1),
                }}
              >
                <FileIcon sx={{ color: '#6366f1' }} />
              </Box>
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  {report.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {report.type}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <CalendarIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  {new Date(report.created_at).toLocaleDateString('he-IL')}
                </Typography>
              </Box>
              {report.total_value && (
                <Typography variant="body2" fontWeight={600} color="primary.main">
                  {formatCurrency(report.total_value)}
                </Typography>
              )}
              <Chip
                label={getStatusLabel(report.status)}
                size="small"
                sx={{
                  backgroundColor: alpha(getStatusColor(report.status), 0.1),
                  color: getStatusColor(report.status),
                  fontWeight: 500,
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
                  backgroundColor: alpha('#6366f1', 0.1),
                  '&:hover': { backgroundColor: alpha('#6366f1', 0.2) },
                }}
              >
                <ViewIcon sx={{ fontSize: 18, color: '#6366f1' }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="הורדה">
              <IconButton
                size="small"
                sx={{
                  backgroundColor: alpha('#10b981', 0.1),
                  '&:hover': { backgroundColor: alpha('#10b981', 0.2) },
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
            color="#6366f1"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard
            title="דוחות מוכנים"
            value={stats.completedReports}
            icon={<TrendingUpIcon sx={{ color: 'white', fontSize: 24 }} />}
            color="#10b981"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <StatCard
            title="סה״כ שווי"
            value={formatCurrency(stats.totalValue)}
            icon={<TrendingUpIcon sx={{ color: 'white', fontSize: 24 }} />}
            color="#06b6d4"
          />
        </Grid>
      </Grid>

      {/* Reports List */}
      <Box>
        <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
          רשימת דוחות
        </Typography>

        {loading ? (
          <Card>
            <CardContent>
              <LinearProgress />
            </CardContent>
          </Card>
        ) : reports.length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <AssessmentIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                אין דוחות עדיין
              </Typography>
              <Typography variant="body2" color="text.secondary">
                העלה תוכנית כדי ליצור כתב כמויות ראשון
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </Box>
        )}
      </Box>
    </MainLayout>
  );
}
