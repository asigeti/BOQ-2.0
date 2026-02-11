'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  alpha,
  Chip,
  IconButton,
  Grid,
  Button,
} from '@mui/material';
import {
  FolderOpen as ProjectIcon,
  Description as PlanIcon,
  CheckCircle as CompletedIcon,
  TrendingUp as TrendingIcon,
  ArrowForward as ArrowIcon,
  Schedule as PendingIcon,
  Add as AddIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';
import { useThemeMode } from '@/contexts/ThemeContext';

const Header = dynamic(() => import('@/components/layout/Header'), { ssr: false });

interface Project {
  id: number;
  name: string;
  processing_status: string;
  processing_progress: number;
  total_files: number;
  processed_files: number;
  created_at: string;
}

interface Stats {
  totalProjects: number;
  totalPlans: number;
  completedPlans: number;
  processingPlans: number;
}

interface ThemeColors {
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
}

function StatCard({ title, value, icon, color, subtitle, delay = 0, themeColors }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  delay?: number;
  themeColors: ThemeColors;
}) {
  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.12)} 0%, ${alpha(color, 0.03)} 100%)`,
        border: `1px solid ${alpha(color, 0.2)}`,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        animation: 'fadeIn 0.6s ease-out forwards',
        animationDelay: `${delay}s`,
        opacity: 0,
        '@keyframes fadeIn': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        '&:hover': {
          transform: 'translateY(-6px)',
          boxShadow: `0 12px 40px ${alpha(color, 0.25)}`,
          borderColor: alpha(color, 0.4),
        },
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: `linear-gradient(90deg, ${color}, ${alpha(color, 0.3)})`,
          borderRadius: '20px 20px 0 0',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography
              variant="body2"
              sx={{
                mb: 1,
                color: themeColors.textSecondary,
                fontSize: '0.85rem',
                fontWeight: 500,
                letterSpacing: '0.02em',
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h2"
              sx={{
                fontWeight: 800,
                fontSize: '2.5rem',
                background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.7)} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.02em',
              }}
            >
              {value}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  mt: 1,
                  display: 'block',
                  color: themeColors.textMuted,
                  fontSize: '0.75rem',
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 60,
              height: 60,
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.7)} 100%)`,
              boxShadow: `0 8px 24px ${alpha(color, 0.35)}`,
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                inset: -2,
                borderRadius: '18px',
                background: `linear-gradient(135deg, ${alpha(color, 0.5)}, transparent)`,
                zIndex: -1,
                opacity: 0.5,
              },
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function RecentProjectCard({ project, onClick, delay = 0, themeColors, isDark }: {
  project: Project;
  onClick: () => void;
  delay?: number;
  themeColors: ThemeColors;
  isDark: boolean;
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'processing': return '#f59e0b';
      case 'extracted': return '#8b5cf6';
      case 'generating_boq': return '#0ea5e9';
      case 'pending': return '#64748b';
      default: return '#64748b';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'הושלם';
      case 'processing': return 'מעבד';
      case 'extracted': return 'ממתין לבחירה';
      case 'generating_boq': return 'יוצר BOQ';
      case 'pending': return 'ממתין';
      default: return status;
    }
  };

  const statusColor = getStatusColor(project.processing_status);

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        animation: 'slideIn 0.5s ease-out forwards',
        animationDelay: `${delay}s`,
        opacity: 0,
        '@keyframes slideIn': {
          '0%': { opacity: 0, transform: 'translateX(30px)' },
          '100%': { opacity: 1, transform: 'translateX(0)' },
        },
        '&:hover': {
          transform: 'translateX(-8px)',
          boxShadow: isDark ? `0 8px 32px rgba(0, 0, 0, 0.3)` : `0 8px 32px rgba(0, 0, 0, 0.12)`,
          borderColor: alpha(statusColor, 0.4),
          '& .arrow-icon': {
            transform: 'rotate(180deg) translateX(-4px)',
            color: statusColor,
          },
        },
      }}
    >
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: themeColors.textPrimary,
                  fontSize: '1.1rem',
                }}
              >
                {project.name}
              </Typography>
              <Chip
                label={getStatusLabel(project.processing_status)}
                size="small"
                sx={{
                  backgroundColor: alpha(statusColor, 0.15),
                  color: statusColor,
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  border: `1px solid ${alpha(statusColor, 0.3)}`,
                  boxShadow: `0 0 12px ${alpha(statusColor, 0.2)}`,
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" sx={{ color: themeColors.textMuted }}>
                {project.total_files} קבצים
              </Typography>
              <Box sx={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: themeColors.textMuted }} />
              <Typography variant="body2" sx={{ color: themeColors.textMuted }}>
                {new Date(project.created_at).toLocaleDateString('he-IL')}
              </Typography>
            </Box>
            {(project.processing_status === 'processing' || project.processing_status === 'generating_boq') && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" sx={{ color: statusColor, fontWeight: 600 }}>
                    {project.processing_progress}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={project.processing_progress}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(statusColor, 0.1),
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${statusColor}, ${alpha(statusColor, 0.6)})`,
                      borderRadius: 3,
                      boxShadow: `0 0 12px ${alpha(statusColor, 0.5)}`,
                    },
                  }}
                />
              </Box>
            )}
          </Box>
          <IconButton
            className="arrow-icon"
            size="small"
            sx={{
              ml: 2,
              color: themeColors.textMuted,
              transition: 'all 0.3s ease',
            }}
          >
            <ArrowIcon sx={{ transform: 'rotate(180deg)' }} />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalProjects: 0,
    totalPlans: 0,
    completedPlans: 0,
    processingPlans: 0,
  });
  const [loading, setLoading] = useState(true);
  const { isDark } = useThemeMode();

  // Theme-aware colors
  const colors: ThemeColors = {
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await api.get('/projects/');
      const projectsData = response.data;
      setProjects(projectsData);

      const totalPlans = projectsData.reduce((sum: number, p: Project) => sum + p.total_files, 0);
      const completedProjects = projectsData.filter((p: Project) => p.processing_status === 'completed').length;
      const processingProjects = projectsData.filter((p: Project) =>
        p.processing_status === 'processing' || p.processing_status === 'generating_boq'
      ).length;

      setStats({
        totalProjects: projectsData.length,
        totalPlans: totalPlans,
        completedPlans: completedProjects,
        processingPlans: processingProjects,
      });
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout>
      <Header title="לוח בקרה" subtitle="ברוכים הבאים למערכת כתב הכמויות החכם" />

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 5 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="סה״כ פרויקטים"
            value={stats.totalProjects}
            icon={<ProjectIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#0ea5e9"
            delay={0.1}
            themeColors={colors}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="סה״כ תוכניות"
            value={stats.totalPlans}
            icon={<PlanIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#f59e0b"
            delay={0.2}
            themeColors={colors}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="פרויקטים שהושלמו"
            value={stats.completedPlans}
            icon={<CompletedIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#10b981"
            delay={0.3}
            themeColors={colors}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="בעיבוד"
            value={stats.processingPlans}
            icon={<PendingIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#8b5cf6"
            delay={0.4}
            themeColors={colors}
          />
        </Grid>
      </Grid>

      {/* Recent Projects */}
      <Box sx={{ mb: 5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                color: colors.textPrimary,
              }}
            >
              פרויקטים אחרונים
            </Typography>
            <Chip
              icon={<AIIcon sx={{ fontSize: 14, color: '#0ea5e9 !important' }} />}
              label="AI Processing"
              size="small"
              sx={{
                height: 24,
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                border: '1px solid rgba(14, 165, 233, 0.3)',
                color: '#0ea5e9',
                fontWeight: 600,
                fontSize: '0.7rem',
              }}
            />
          </Box>
          <Button
            variant="text"
            onClick={() => router.push('/dashboard/projects')}
            sx={{
              color: '#0ea5e9',
              fontWeight: 600,
              '&:hover': {
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
              },
            }}
          >
            הצג הכל
          </Button>
        </Box>

        {loading ? (
          <Card>
            <CardContent sx={{ py: 6 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    border: '3px solid rgba(14, 165, 233, 0.1)',
                    borderTopColor: '#0ea5e9',
                    animation: 'spin 1s linear infinite',
                    '@keyframes spin': {
                      '0%': { transform: 'rotate(0deg)' },
                      '100%': { transform: 'rotate(360deg)' },
                    },
                  }}
                />
                <Typography sx={{ mt: 2, color: colors.textMuted }}>טוען פרויקטים...</Typography>
              </Box>
            </CardContent>
          </Card>
        ) : projects.length === 0 ? (
          <Card
            sx={{
              textAlign: 'center',
              py: 8,
              background: 'rgba(14, 165, 233, 0.03)',
              border: '1px dashed rgba(14, 165, 233, 0.3)',
            }}
          >
            <CardContent>
              <Box
                sx={{
                  width: 80,
                  height: 80,
                  borderRadius: '20px',
                  background: 'rgba(14, 165, 233, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 3,
                }}
              >
                <ProjectIcon sx={{ fontSize: 40, color: '#0ea5e9' }} />
              </Box>
              <Typography variant="h6" sx={{ color: colors.textPrimary, mb: 1, fontWeight: 600 }}>
                אין פרויקטים עדיין
              </Typography>
              <Typography variant="body2" sx={{ color: colors.textMuted, mb: 3 }}>
                צור פרויקט חדש כדי להתחיל לעבוד עם מערכת ה-AI
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => router.push('/dashboard/projects')}
                sx={{
                  background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)',
                  },
                }}
              >
                צור פרויקט חדש
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {projects.slice(0, 5).map((project, index) => (
              <RecentProjectCard
                key={project.id}
                project={project}
                onClick={() => router.push(`/dashboard/projects/${project.id}`)}
                delay={0.1 * index}
                themeColors={colors}
                isDark={isDark}
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Quick Actions */}
      <Box>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            mb: 3,
            color: colors.textPrimary,
          }}
        >
          פעולות מהירות
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card
              onClick={() => router.push('/dashboard/projects')}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(14, 165, 233, 0.02) 100%)',
                border: '1px solid rgba(14, 165, 233, 0.2)',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(14, 165, 233, 0.2)',
                  borderColor: 'rgba(14, 165, 233, 0.4)',
                },
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 3, p: 3 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                    boxShadow: '0 8px 24px rgba(14, 165, 233, 0.3)',
                  }}
                >
                  <AddIcon sx={{ color: 'white', fontSize: 28 }} />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary, mb: 0.5 }}>
                    צור פרויקט חדש
                  </Typography>
                  <Typography variant="body2" sx={{ color: colors.textMuted }}>
                    התחל לעבוד על כתב כמויות חדש
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card
              onClick={() => router.push('/dashboard/reports')}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(245, 158, 11, 0.02) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(245, 158, 11, 0.2)',
                  borderColor: 'rgba(245, 158, 11, 0.4)',
                },
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 3, p: 3 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    boxShadow: '0 8px 24px rgba(245, 158, 11, 0.3)',
                  }}
                >
                  <TrendingIcon sx={{ color: 'white', fontSize: 28 }} />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary, mb: 0.5 }}>
                    צפה בדוחות
                  </Typography>
                  <Typography variant="body2" sx={{ color: colors.textMuted }}>
                    ניתוח וסטטיסטיקות הפרויקטים
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </MainLayout>
  );
}
