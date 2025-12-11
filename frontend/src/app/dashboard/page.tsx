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
} from '@mui/material';
import {
  FolderOpen as ProjectIcon,
  Description as PlanIcon,
  CheckCircle as CompletedIcon,
  TrendingUp as TrendingIcon,
  ArrowForward as ArrowIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';

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

function StatCard({ title, value, icon, color, subtitle }: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}) {
  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.02)} 100%)`,
        border: `1px solid ${alpha(color, 0.15)}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: `0 8px 24px ${alpha(color, 0.2)}`,
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
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 3,
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

function RecentProjectCard({ project, onClick }: { project: Project; onClick: () => void }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'processing': return '#f59e0b';
      case 'pending': return '#6366f1';
      default: return '#64748b';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'הושלם';
      case 'processing': return 'בעיבוד';
      case 'pending': return 'ממתין';
      default: return status;
    }
  };

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'translateX(-4px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        },
      }}
    >
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {project.name}
              </Typography>
              <Chip
                label={getStatusLabel(project.processing_status)}
                size="small"
                sx={{
                  backgroundColor: alpha(getStatusColor(project.processing_status), 0.1),
                  color: getStatusColor(project.processing_status),
                  fontWeight: 500,
                  fontSize: '0.7rem',
                }}
              />
            </Box>
            <Typography variant="body2" color="text.secondary">
              {project.total_files} קבצים | נוצר {new Date(project.created_at).toLocaleDateString('he-IL')}
            </Typography>
            {project.processing_status === 'processing' && (
              <LinearProgress
                variant="determinate"
                value={project.processing_progress}
                sx={{
                  mt: 1.5,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: alpha('#f59e0b', 0.1),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#f59e0b',
                    borderRadius: 3,
                  },
                }}
              />
            )}
          </Box>
          <IconButton size="small" sx={{ ml: 2 }}>
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

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await api.get('/projects/');
      const projectsData = response.data;
      setProjects(projectsData);

      // Calculate stats
      const totalPlans = projectsData.reduce((sum: number, p: Project) => sum + p.total_files, 0);
      const completedProjects = projectsData.filter((p: Project) => p.processing_status === 'completed').length;
      const processingProjects = projectsData.filter((p: Project) => p.processing_status === 'processing').length;

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
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="סה״כ פרויקטים"
            value={stats.totalProjects}
            icon={<ProjectIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#6366f1"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="סה״כ תוכניות"
            value={stats.totalPlans}
            icon={<PlanIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#06b6d4"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="פרויקטים שהושלמו"
            value={stats.completedPlans}
            icon={<CompletedIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#10b981"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="בעיבוד"
            value={stats.processingPlans}
            icon={<PendingIcon sx={{ color: 'white', fontSize: 28 }} />}
            color="#f59e0b"
          />
        </Grid>
      </Grid>

      {/* Recent Projects */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            פרויקטים אחרונים
          </Typography>
          <Typography
            variant="body2"
            color="primary"
            sx={{ cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
            onClick={() => router.push('/dashboard/projects')}
          >
            הצג הכל
          </Typography>
        </Box>

        {loading ? (
          <Card>
            <CardContent>
              <LinearProgress />
            </CardContent>
          </Card>
        ) : projects.length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <ProjectIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                אין פרויקטים עדיין
              </Typography>
              <Typography variant="body2" color="text.secondary">
                צור פרויקט חדש כדי להתחיל
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {projects.slice(0, 5).map((project) => (
              <RecentProjectCard
                key={project.id}
                project={project}
                onClick={() => router.push(`/dashboard/projects/${project.id}`)}
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Quick Actions */}
      <Box>
        <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
          פעולות מהירות
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card
              onClick={() => router.push('/dashboard/projects')}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)',
                },
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: alpha('#6366f1', 0.1),
                  }}
                >
                  <ProjectIcon sx={{ color: '#6366f1' }} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" fontWeight={600}>
                    צור פרויקט חדש
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    התחל לעבוד על פרויקט חדש
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card
              onClick={() => router.push('/dashboard/upload')}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 12px rgba(6, 182, 212, 0.2)',
                },
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: alpha('#06b6d4', 0.1),
                  }}
                >
                  <TrendingIcon sx={{ color: '#06b6d4' }} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" fontWeight={600}>
                    העלה תוכנית
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    העלה קבצי DWG או PDF
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
