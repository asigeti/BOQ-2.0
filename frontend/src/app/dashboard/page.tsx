'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Typography,
  Card,
  CardContent,
  alpha,
  Chip,
  IconButton,
  Skeleton,
  Grid,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as TimeIcon,
  ArrowForward as ArrowIcon,
  Architecture as CadIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { MainLayout, Header } from '@/components/layout';
import FileUpload from '@/components/FileUpload';
import api from '@/utils/axios';
import { navigateTo } from '@/utils/navigation';

interface Plan {
  id: number;
  filename: string;
  uploaded_at: string;
  status?: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: string;
  delay?: number;
}

function StatCard({ title, value, icon, color, trend, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card
        sx={{
          height: '100%',
          background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
          border: `1px solid ${alpha(color, 0.2)}`,
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: `0 12px 24px -8px ${alpha(color, 0.3)}`,
          },
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {title}
              </Typography>
              <Typography variant="h3" fontWeight={700} sx={{ color }}>
                {value}
              </Typography>
              {trend && (
                <Chip
                  icon={<TrendingUpIcon sx={{ fontSize: 14 }} />}
                  label={trend}
                  size="small"
                  sx={{
                    mt: 1,
                    backgroundColor: alpha('#10b981', 0.1),
                    color: '#10b981',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                  }}
                />
              )}
            </Box>
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: 2,
                backgroundColor: alpha(color, 0.15),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function RecentProjectCard({ plan, index }: { plan: Plan; index: number }) {
  const router = useRouter();

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'processing':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      default:
        return '#64748b';
    }
  };

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'completed':
        return 'הושלם';
      case 'processing':
        return 'בעיבוד';
      case 'failed':
        return 'נכשל';
      default:
        return 'ממתין';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
    >
      <Box
        onClick={() => navigateTo(`/dashboard/plans/${plan.id}/`)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          p: 2,
          borderRadius: 2,
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            backgroundColor: alpha('#6366f1', 0.04),
          },
        }}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            backgroundColor: alpha('#6366f1', 0.1),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CadIcon sx={{ color: '#6366f1', fontSize: 24 }} />
        </Box>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            variant="subtitle2"
            fontWeight={600}
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {plan.filename}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {new Date(plan.uploaded_at).toLocaleDateString('he-IL')}
            </Typography>
          </Box>
        </Box>

        <Chip
          label={getStatusLabel(plan.status)}
          size="small"
          sx={{
            backgroundColor: alpha(getStatusColor(plan.status), 0.1),
            color: getStatusColor(plan.status),
            fontWeight: 600,
            fontSize: '0.7rem',
          }}
        />

        <IconButton
          size="small"
          sx={{
            backgroundColor: alpha('#6366f1', 0.1),
            '&:hover': {
              backgroundColor: alpha('#6366f1', 0.2),
            },
          }}
        >
          <ArrowIcon sx={{ fontSize: 18, color: '#6366f1', transform: 'rotate(180deg)' }} />
        </IconButton>
      </Box>
    </motion.div>
  );
}

export default function Dashboard() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchPlans = async () => {
    try {
      const response = await api.get('/plans/');
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleUploadSuccess = (data: any) => {
    fetchPlans();
  };

  return (
    <MainLayout>
      <Header title="לוח בקרה" subtitle="ברוכים הבאים למערכת כתב הכמויות החכם" />

      {/* Stats Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="סה״כ פרויקטים"
            value={plans.length}
            icon={<FileIcon sx={{ fontSize: 28, color: '#6366f1' }} />}
            color="#6366f1"
            delay={0}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="פרויקטים החודש"
            value={plans.filter(p => {
              const date = new Date(p.uploaded_at);
              const now = new Date();
              return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
            }).length}
            icon={<TrendingUpIcon sx={{ fontSize: 28, color: '#06b6d4' }} />}
            color="#06b6d4"
            trend="+12%"
            delay={0.1}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="הושלמו בהצלחה"
            value={plans.filter(p => p.status === 'completed').length}
            icon={<ReportIcon sx={{ fontSize: 28, color: '#10b981' }} />}
            color="#10b981"
            delay={0.2}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="בעיבוד"
            value={plans.filter(p => p.status === 'processing').length}
            icon={<TimeIcon sx={{ fontSize: 28, color: '#f59e0b' }} />}
            color="#f59e0b"
            delay={0.3}
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={4}>
        {/* Upload Section */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <Card>
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <UploadIcon sx={{ color: 'white', fontSize: 24 }} />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={600}>
                      העלאת תוכנית חדשה
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      העלה קובץ AutoCAD ליצירת כתב כמויות אוטומטי
                    </Typography>
                  </Box>
                </Box>

                <FileUpload onUploadSuccess={handleUploadSuccess} />
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Recent Projects */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
          >
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    פרויקטים אחרונים
                  </Typography>
                  <Chip
                    label={`${plans.length} פרויקטים`}
                    size="small"
                    sx={{
                      backgroundColor: alpha('#6366f1', 0.1),
                      color: '#6366f1',
                      fontWeight: 600,
                    }}
                  />
                </Box>

                {loading ? (
                  <Box>
                    {[1, 2, 3, 4].map((i) => (
                      <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                        <Skeleton variant="rounded" width={48} height={48} />
                        <Box sx={{ flex: 1 }}>
                          <Skeleton variant="text" width="60%" />
                          <Skeleton variant="text" width="40%" />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                ) : plans.length === 0 ? (
                  <Box
                    sx={{
                      textAlign: 'center',
                      py: 6,
                      color: 'text.secondary',
                    }}
                  >
                    <FileIcon sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
                    <Typography variant="body1">
                      עדיין לא הועלו פרויקטים
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      העלה את הקובץ הראשון שלך
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ mx: -2 }}>
                    {plans.slice(0, 5).map((plan, index) => (
                      <RecentProjectCard key={plan.id} plan={plan} index={index} />
                    ))}
                  </Box>
                )}

                {plans.length > 5 && (
                  <Box
                    onClick={() => navigateTo('/dashboard/projects/')}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 1,
                      mt: 2,
                      py: 1.5,
                      borderRadius: 2,
                      cursor: 'pointer',
                      color: 'primary.main',
                      transition: 'all 0.2s ease-in-out',
                      '&:hover': {
                        backgroundColor: alpha('#6366f1', 0.08),
                      },
                    }}
                  >
                    <Typography variant="body2" fontWeight={600}>
                      הצג את כל הפרויקטים
                    </Typography>
                    <ArrowIcon sx={{ fontSize: 18, transform: 'rotate(180deg)' }} />
                  </Box>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>
    </MainLayout>
  );
}
