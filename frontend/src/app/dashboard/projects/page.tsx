'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  alpha,
  Chip,
  IconButton,
  Skeleton,
  Grid,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Description as FileIcon,
  PlayArrow as PlayIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ArrowUpward as ArrowUpIcon,
  Storage as DriveIcon,
  Architecture as ArchitectureIcon,
  Search as SearchIcon,
  CalendarMonth as CalendarIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  HourglassTop as PendingIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';
import { useThemeMode } from '@/contexts/ThemeContext';

// Lazy load Header to avoid SSR issues
const Header = dynamic(() => import('@/components/layout/Header'), { ssr: false });

interface FolderItem {
  name: string;
  path: string;
  type: 'drive' | 'folder';
}

interface BrowseResult {
  current_path: string;
  parent_path: string | null;
  folders: FolderItem[];
}

interface Project {
  id: number;
  name: string;
  description?: string;
  folder_path?: string;
  processing_status: string;
  processing_progress: number;
  total_files: number;
  processed_files: number;
  created_at: string;
}

interface FolderScanResult {
  folder_path: string;
  dwg_files: string[];
  total_count: number;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectFolder, setNewProjectFolder] = useState('');
  const [scanResult, setScanResult] = useState<FolderScanResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [creating, setCreating] = useState(false);
  const [folderBrowserOpen, setFolderBrowserOpen] = useState(false);
  const [browseResult, setBrowseResult] = useState<BrowseResult | null>(null);
  const [browsing, setBrowsing] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { showError } = useNotification();
  const { isDark } = useThemeMode();

  // Theme-aware colors
  const colors = {
    bg: isDark ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.95)',
    bgCard: isDark ? 'rgba(15, 23, 42, 0.8)' : '#ffffff',
    bgDialog: isDark ? '#0f172a' : '#ffffff',
    border: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.1)',
    borderHover: isDark ? 'rgba(14, 165, 233, 0.3)' : 'rgba(3, 105, 161, 0.4)',
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
    primary: isDark ? '#0ea5e9' : '#0369a1',
    primaryBg: isDark ? 'rgba(14, 165, 233, 0.1)' : 'rgba(3, 105, 161, 0.08)',
    skeleton: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.04)',
    shadow: isDark ? '0 25px 50px -12px rgba(0, 0, 0, 0.7)' : '0 8px 24px -4px rgba(0, 0, 0, 0.1), 0 20px 48px -12px rgba(0, 0, 0, 0.12)',
    cardShadow: isDark ? '0 8px 32px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.06)',
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await api.get('/projects/');
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const browseFolders = async (path: string = '') => {
    try {
      setBrowsing(true);
      const response = await api.get('/projects/browse-folder', {
        params: { path },
      });
      setBrowseResult(response.data);
    } catch (error: any) {
      console.error('Failed to browse folder', error);
      // On error, fallback to root folder (drive list)
      if (path !== '') {
        // Clear localStorage to prevent repeated errors
        if (typeof window !== 'undefined') {
          localStorage.removeItem('boq_last_folder_path');
        }
        // Retry with empty path to get drive list
        try {
          const rootResponse = await api.get('/projects/browse-folder', {
            params: { path: '' },
          });
          setBrowseResult(rootResponse.data);
        } catch (rootError) {
          console.error('Failed to get root folders', rootError);
          setBrowseResult(null);
        }
      }
    } finally {
      setBrowsing(false);
    }
  };

  const openFolderBrowser = () => {
    setFolderBrowserOpen(true);
    // Try to restore last browsed folder from localStorage
    const lastPath = typeof window !== 'undefined'
      ? localStorage.getItem('boq_last_folder_path') || ''
      : '';
    browseFolders(lastPath);
  };

  const selectFolder = (folderPath: string) => {
    setNewProjectFolder(folderPath);
    setScanResult(null);
    setFolderBrowserOpen(false);
    // Save to localStorage for next time
    if (typeof window !== 'undefined') {
      localStorage.setItem('boq_last_folder_path', folderPath);
    }
  };

  const handleScanFolder = async () => {
    if (!newProjectFolder.trim()) return;

    try {
      setScanning(true);
      const response = await api.post('/projects/scan-folder', {
        folder_path: newProjectFolder,
      });
      setScanResult(response.data);
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה בסריקת התיקייה');
      setScanResult(null);
    } finally {
      setScanning(false);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || !newProjectFolder.trim()) return;

    try {
      setCreating(true);
      // Create project
      const createResponse = await api.post('/projects/', {
        name: newProjectName,
        description: newProjectDescription,
        folder_path: newProjectFolder,
      });

      const projectId = createResponse.data.id;

      // Scan folder and create plans (but don't start processing yet)
      await api.post(`/projects/${projectId}/scan`);

      // NOTE: Removed auto-processing - user will review files first
      // await api.post(`/projects/${projectId}/process`);

      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      setNewProjectFolder('');
      setScanResult(null);

      // Navigate to project detail page where user can review files
      router.push(`/dashboard/projects/${projectId}`);
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה ביצירת הפרויקט');
    } finally {
      setCreating(false);
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: '#10b981', label: 'הושלם', icon: <CheckIcon sx={{ fontSize: 14 }} />, glow: 'rgba(16, 185, 129, 0.4)' };
      case 'processing':
        return { color: '#f59e0b', label: 'בעיבוד', icon: <AIIcon sx={{ fontSize: 14 }} />, glow: 'rgba(245, 158, 11, 0.4)' };
      case 'failed':
        return { color: '#ef4444', label: 'נכשל', icon: <ErrorIcon sx={{ fontSize: 14 }} />, glow: 'rgba(239, 68, 68, 0.4)' };
      case 'scanning':
        return { color: '#0ea5e9', label: 'סורק', icon: <SearchIcon sx={{ fontSize: 14 }} />, glow: 'rgba(14, 165, 233, 0.4)' };
      default:
        return { color: '#64748b', label: 'ממתין', icon: <PendingIcon sx={{ fontSize: 14 }} />, glow: 'rgba(100, 116, 139, 0.4)' };
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, project: Project) => {
    e.stopPropagation(); // Prevent card click
    setProjectToDelete(project);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!projectToDelete) return;

    try {
      setDeleting(true);
      await api.delete(`/projects/${projectToDelete.id}`);
      setProjects(projects.filter(p => p.id !== projectToDelete.id));
      setDeleteDialogOpen(false);
      setProjectToDelete(null);
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה במחיקת הפרויקט');
    } finally {
      setDeleting(false);
    }
  };

  // Dialog common styles
  const dialogPaperStyles = {
    backgroundColor: colors.bgDialog,
    border: `1px solid ${colors.border}`,
    borderRadius: '20px',
    boxShadow: colors.shadow,
    backdropFilter: 'blur(20px)',
  };

  return (
    <MainLayout>
      <Header title="פרויקטים" subtitle="ניהול פרויקטים וסריקת תיקיות DWG/PDF" />

      {/* Action Bar */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 4,
          p: 3,
          borderRadius: '16px',
          backgroundColor: colors.bg,
          border: `1px solid ${colors.border}`,
          backdropFilter: 'blur(12px)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '14px',
              background: `linear-gradient(135deg, ${colors.primaryBg} 0%, ${isDark ? 'rgba(14, 165, 233, 0.05)' : 'rgba(2, 132, 199, 0.05)'} 100%)`,
              border: `1px solid ${colors.borderHover}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ArchitectureIcon sx={{ color: colors.primary, fontSize: 24 }} />
          </Box>
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                color: colors.textPrimary,
                fontSize: '1.1rem',
              }}
            >
              כל הפרויקטים
            </Typography>
            <Typography variant="body2" sx={{ color: colors.textMuted }}>
              {projects.length} פרויקטים במערכת
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="רענן רשימה">
            <IconButton
              onClick={fetchProjects}
              sx={{
                width: 44,
                height: 44,
                backgroundColor: colors.skeleton,
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: colors.primaryBg,
                  borderColor: colors.borderHover,
                  color: colors.primary,
                  transform: 'rotate(180deg)',
                },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{
              px: 3,
              py: 1.2,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              boxShadow: '0 8px 24px rgba(14, 165, 233, 0.35)',
              fontWeight: 600,
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 32px rgba(14, 165, 233, 0.45)',
              },
            }}
          >
            פרויקט חדש
          </Button>
        </Box>
      </Box>

      {/* Projects Grid */}
      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
              <Skeleton
                variant="rounded"
                height={220}
                sx={{
                  borderRadius: '20px',
                  backgroundColor: colors.skeleton,
                }}
              />
            </Grid>
          ))}
        </Grid>
      ) : projects.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 10,
            px: 4,
            borderRadius: '24px',
            backgroundColor: colors.bg,
            border: `1px solid ${colors.border}`,
            backdropFilter: 'blur(12px)',
          }}
        >
          <Box
            sx={{
              width: 100,
              height: 100,
              borderRadius: '24px',
              background: `linear-gradient(135deg, ${colors.primaryBg} 0%, ${isDark ? 'rgba(14, 165, 233, 0.05)' : 'rgba(2, 132, 199, 0.05)'} 100%)`,
              border: `1px solid ${colors.borderHover}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 3,
            }}
          >
            <FolderIcon sx={{ fontSize: 48, color: colors.primary, opacity: 0.8 }} />
          </Box>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: colors.textPrimary,
              mb: 1,
            }}
          >
            אין פרויקטים עדיין
          </Typography>
          <Typography
            variant="body1"
            sx={{ color: colors.textMuted, mb: 4, maxWidth: 400, mx: 'auto' }}
          >
            צור פרויקט חדש וסרוק תיקיית תכניות כדי להתחיל לחלץ כמויות באמצעות AI
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{
              px: 4,
              py: 1.5,
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              boxShadow: '0 8px 24px rgba(14, 165, 233, 0.35)',
              fontWeight: 600,
              fontSize: '1rem',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 32px rgba(14, 165, 233, 0.45)',
              },
            }}
          >
            צור פרויקט ראשון
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project, index) => {
            const statusConfig = getStatusConfig(project.processing_status);

            return (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={project.id}>
                <Box
                  sx={{
                    animation: 'fadeInUp 0.4s ease-out forwards',
                    animationDelay: `${index * 0.08}s`,
                    opacity: 0,
                    '@keyframes fadeInUp': {
                      '0%': { opacity: 0, transform: 'translateY(24px)' },
                      '100%': { opacity: 1, transform: 'translateY(0)' },
                    },
                  }}
                >
                  <Card
                    sx={{
                      cursor: 'pointer',
                      borderRadius: '20px',
                      backgroundColor: colors.bgCard,
                      border: `1px solid ${colors.border}`,
                      backdropFilter: 'blur(12px)',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      overflow: 'visible',
                      boxShadow: colors.cardShadow,
                      '&:hover': {
                        transform: 'translateY(-6px)',
                        borderColor: colors.borderHover,
                        boxShadow: isDark
                          ? `0 20px 40px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(14, 165, 233, 0.1)`
                          : `0 16px 32px -8px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(2, 132, 199, 0.1)`,
                        '& .project-icon': {
                          transform: 'scale(1.1) rotate(-5deg)',
                          boxShadow: '0 12px 32px rgba(245, 158, 11, 0.4)',
                        },
                      },
                    }}
                    onClick={() => router.push(`/dashboard/projects/${project.id}`)}
                  >
                    <CardContent sx={{ p: 3 }}>
                      {/* Header */}
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 3 }}>
                        <Box
                          className="project-icon"
                          sx={{
                            width: 52,
                            height: 52,
                            borderRadius: '16px',
                            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)',
                            border: '1px solid rgba(245, 158, 11, 0.25)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'all 0.3s ease',
                            flexShrink: 0,
                          }}
                        >
                          <FolderOpenIcon sx={{ color: '#f59e0b', fontSize: 26 }} />
                        </Box>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: colors.textPrimary,
                              fontSize: '1.05rem',
                              mb: 0.3,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {project.name}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: colors.textMuted,
                              fontSize: '0.8rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              direction: 'ltr',
                              textAlign: 'right',
                            }}
                          >
                            {project.folder_path || 'ללא תיקייה'}
                          </Typography>
                        </Box>
                        <Tooltip title="מחק פרויקט">
                          <IconButton
                            size="small"
                            onClick={(e) => handleDeleteClick(e, project)}
                            sx={{
                              width: 36,
                              height: 36,
                              color: colors.textMuted,
                              backgroundColor: colors.skeleton,
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                color: '#ef4444',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                transform: 'scale(1.1)',
                              },
                            }}
                          >
                            <DeleteIcon sx={{ fontSize: 18 }} />
                          </IconButton>
                        </Tooltip>
                      </Box>

                      {/* Status & Files */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.5 }}>
                        <Chip
                          icon={statusConfig.icon}
                          label={statusConfig.label}
                          size="small"
                          sx={{
                            height: 28,
                            backgroundColor: alpha(statusConfig.color, 0.12),
                            color: statusConfig.color,
                            border: `1px solid ${alpha(statusConfig.color, 0.25)}`,
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            boxShadow: `0 0 12px ${statusConfig.glow}`,
                            '& .MuiChip-icon': {
                              color: statusConfig.color,
                              marginRight: '-4px',
                            },
                          }}
                        />
                        <Chip
                          icon={<FileIcon sx={{ fontSize: 14 }} />}
                          label={`${project.total_files} קבצים`}
                          size="small"
                          sx={{
                            height: 28,
                            backgroundColor: colors.skeleton,
                            color: colors.textSecondary,
                            border: `1px solid ${colors.border}`,
                            fontWeight: 500,
                            fontSize: '0.75rem',
                            '& .MuiChip-icon': {
                              color: colors.textMuted,
                            },
                          }}
                        />
                      </Box>

                      {/* Progress Bar (when processing) */}
                      {project.processing_status === 'processing' && (
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="caption" sx={{ color: colors.textSecondary, fontWeight: 500 }}>
                              {project.processed_files} / {project.total_files} קבצים
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{
                                color: '#f59e0b',
                                fontWeight: 700,
                              }}
                            >
                              {project.processing_progress}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={project.processing_progress}
                            sx={{
                              height: 6,
                              borderRadius: 6,
                              backgroundColor: 'rgba(245, 158, 11, 0.1)',
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 6,
                                background: 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)',
                                boxShadow: '0 0 16px rgba(245, 158, 11, 0.5)',
                              },
                            }}
                          />
                        </Box>
                      )}

                      {/* Footer */}
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          pt: 2,
                          borderTop: `1px solid ${colors.border}`,
                        }}
                      >
                        <CalendarIcon sx={{ fontSize: 14, color: colors.textMuted }} />
                        <Typography variant="caption" sx={{ color: colors.textMuted }}>
                          נוצר: {new Date(project.created_at).toLocaleDateString('he-IL')}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => !creating && setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: dialogPaperStyles }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            borderBottom: `1px solid ${colors.border}`,
            pb: 2,
          }}
        >
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '12px',
              background: `linear-gradient(135deg, ${colors.primaryBg} 0%, ${isDark ? 'rgba(14, 165, 233, 0.05)' : 'rgba(2, 132, 199, 0.05)'} 100%)`,
              border: `1px solid ${colors.borderHover}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FolderOpenIcon sx={{ color: colors.primary }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
              פרויקט חדש
            </Typography>
            <Typography variant="body2" sx={{ color: colors.textMuted, fontSize: '0.8rem' }}>
              הזן פרטי פרויקט ובחר תיקיית תכניות
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            <TextField
              label="שם הפרויקט"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              fullWidth
              required
              placeholder="לדוגמה: פארק המים DCRC"
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: colors.skeleton,
                  '&:hover': {
                    backgroundColor: isDark ? 'rgba(148, 163, 184, 0.05)' : 'rgba(30, 41, 59, 0.08)',
                  },
                },
                '& .MuiInputLabel-root': { color: colors.textSecondary },
                '& .MuiOutlinedInput-input': { color: colors.textPrimary },
              }}
            />
            <TextField
              label="תיאור (אופציונלי)"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
              fullWidth
              multiline
              rows={2}
              placeholder="תיאור קצר של הפרויקט..."
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: colors.skeleton,
                },
                '& .MuiInputLabel-root': { color: colors.textSecondary },
                '& .MuiOutlinedInput-input': { color: colors.textPrimary },
              }}
            />
            <Box>
              <Box sx={{ display: 'flex', gap: 1.5 }}>
                <TextField
                  label="נתיב תיקייה"
                  value={newProjectFolder}
                  onChange={(e) => {
                    setNewProjectFolder(e.target.value);
                    setScanResult(null);
                  }}
                  fullWidth
                  required
                  placeholder="C:\Projects\MyProject או לחץ על 'בחר תיקייה'"
                  helperText="הדבק נתיב או השתמש בכפתור לבחירה"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: colors.skeleton,
                    },
                    '& .MuiInputLabel-root': { color: colors.textSecondary },
                    '& .MuiOutlinedInput-input': { color: colors.textPrimary },
                    '& .MuiFormHelperText-root': { color: colors.textMuted },
                  }}
                />
                <Button
                  variant="contained"
                  onClick={openFolderBrowser}
                  sx={{
                    minWidth: 130,
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                    whiteSpace: 'nowrap',
                    fontWeight: 600,
                  }}
                  startIcon={<FolderOpenIcon />}
                >
                  בחר תיקייה
                </Button>
              </Box>
              {newProjectFolder && (
                <Button
                  variant="outlined"
                  onClick={handleScanFolder}
                  disabled={!newProjectFolder.trim() || scanning}
                  sx={{
                    mt: 2,
                    borderRadius: '10px',
                    borderColor: colors.borderHover,
                    color: colors.primary,
                    '&:hover': {
                      borderColor: colors.primary,
                      backgroundColor: colors.primaryBg,
                    },
                  }}
                  startIcon={scanning ? <CircularProgress size={16} color="inherit" /> : <SearchIcon />}
                >
                  {scanning ? 'סורק...' : 'סרוק לקבצי תכניות'}
                </Button>
              )}
            </Box>

            {scanResult && (
              <Box
                sx={{
                  p: 2.5,
                  borderRadius: '14px',
                  backgroundColor: scanResult.total_count > 0
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'rgba(245, 158, 11, 0.08)',
                  border: `1px solid ${scanResult.total_count > 0
                    ? 'rgba(16, 185, 129, 0.2)'
                    : 'rgba(245, 158, 11, 0.2)'}`,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                  {scanResult.total_count > 0 ? (
                    <CheckIcon sx={{ color: '#10b981' }} />
                  ) : (
                    <WarningIcon sx={{ color: '#f59e0b' }} />
                  )}
                  <Typography
                    variant="body1"
                    sx={{
                      fontWeight: 700,
                      color: scanResult.total_count > 0 ? '#10b981' : '#f59e0b',
                    }}
                  >
                    נמצאו {scanResult.total_count} קבצי תכניות
                  </Typography>
                </Box>
                {scanResult.total_count > 0 && (
                  <Box
                    sx={{
                      maxHeight: 120,
                      overflow: 'auto',
                      pr: 1,
                      '&::-webkit-scrollbar': { width: 4 },
                      '&::-webkit-scrollbar-thumb': {
                        backgroundColor: 'rgba(148, 163, 184, 0.2)',
                        borderRadius: 4,
                      },
                    }}
                  >
                    {scanResult.dwg_files.slice(0, 10).map((file, i) => (
                      <Typography
                        key={i}
                        variant="caption"
                        sx={{
                          display: 'block',
                          color: colors.textSecondary,
                          py: 0.3,
                          direction: 'ltr',
                          textAlign: 'right',
                        }}
                      >
                        📄 {file.split('\\').pop()}
                      </Typography>
                    ))}
                    {scanResult.total_count > 10 && (
                      <Typography variant="caption" sx={{ color: colors.textMuted, mt: 1, display: 'block' }}>
                        ...ועוד {scanResult.total_count - 10} קבצים
                      </Typography>
                    )}
                  </Box>
                )}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2, borderTop: `1px solid ${colors.border}` }}>
          <Button
            onClick={() => setCreateDialogOpen(false)}
            disabled={creating}
            sx={{ color: colors.textSecondary }}
          >
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateProject}
            disabled={!newProjectName.trim() || !newProjectFolder.trim() || creating}
            startIcon={creating ? <CircularProgress size={18} color="inherit" /> : <PlayIcon />}
            sx={{
              px: 3,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              boxShadow: '0 8px 20px rgba(14, 165, 233, 0.3)',
              fontWeight: 600,
              '&:disabled': {
                background: 'rgba(14, 165, 233, 0.2)',
                color: 'rgba(255, 255, 255, 0.4)',
              },
            }}
          >
            {creating ? 'יוצר פרויקט...' : 'צור פרויקט'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Folder Browser Dialog */}
      <Dialog
        open={folderBrowserOpen}
        onClose={() => setFolderBrowserOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: dialogPaperStyles }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            borderBottom: `1px solid ${colors.border}`,
            pb: 2,
          }}
        >
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FolderOpenIcon sx={{ color: '#f59e0b' }} />
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
            בחר תיקייה
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {/* Current path breadcrumb */}
          {browseResult && browseResult.current_path && (
            <Box
              sx={{
                mb: 2,
                p: 2,
                borderRadius: '12px',
                backgroundColor: colors.primaryBg,
                border: `1px solid ${colors.borderHover}`,
              }}
            >
              <Typography variant="caption" sx={{ color: colors.textMuted, display: 'block', mb: 0.5 }}>
                נתיב נוכחי:
              </Typography>
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, color: colors.textPrimary, direction: 'ltr', textAlign: 'right' }}
              >
                {browseResult.current_path}
              </Typography>
            </Box>
          )}

          {/* Navigation buttons */}
          <Box sx={{ display: 'flex', gap: 1.5, mb: 2 }}>
            <Button
              size="small"
              startIcon={<ArrowUpIcon />}
              onClick={() => browseFolders(browseResult?.parent_path ?? '')}
              disabled={browsing}
              sx={{
                borderRadius: '10px',
                color: colors.textSecondary,
                border: `1px solid ${colors.border}`,
                '&:hover': {
                  borderColor: colors.borderHover,
                  backgroundColor: colors.primaryBg,
                },
              }}
            >
              {browseResult?.current_path ? 'חזור' : 'כוננים'}
            </Button>
            {browseResult?.current_path && (
              <Button
                size="small"
                variant="contained"
                onClick={() => selectFolder(browseResult.current_path)}
                sx={{
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                }}
              >
                בחר תיקייה זו
              </Button>
            )}
          </Box>

          {/* Folder list */}
          {browsing ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress sx={{ color: '#0ea5e9' }} />
            </Box>
          ) : (
            <List
              sx={{
                maxHeight: 350,
                overflow: 'auto',
                '&::-webkit-scrollbar': { width: 6 },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: 'rgba(148, 163, 184, 0.2)',
                  borderRadius: 6,
                },
              }}
            >
              {browseResult?.folders.length === 0 && (
                <Typography
                  variant="body2"
                  sx={{ color: colors.textMuted, textAlign: 'center', py: 6 }}
                >
                  אין תיקיות משנה
                </Typography>
              )}
              {browseResult?.folders.map((folder) => (
                <ListItem key={folder.path} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => browseFolders(folder.path)}
                    sx={{
                      borderRadius: '12px',
                      py: 1.5,
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        backgroundColor: colors.primaryBg,
                        transform: 'translateX(-4px)',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 44 }}>
                      {folder.type === 'drive' ? (
                        <Box
                          sx={{
                            width: 36,
                            height: 36,
                            borderRadius: '10px',
                            backgroundColor: colors.primaryBg,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <DriveIcon sx={{ color: colors.primary, fontSize: 20 }} />
                        </Box>
                      ) : (
                        <Box
                          sx={{
                            width: 36,
                            height: 36,
                            borderRadius: '10px',
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <FolderIcon sx={{ color: '#f59e0b', fontSize: 20 }} />
                        </Box>
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={folder.name}
                      secondary={folder.type === 'drive' ? 'כונן' : null}
                      primaryTypographyProps={{
                        fontWeight: 600,
                        color: colors.textPrimary,
                        fontSize: '0.95rem',
                      }}
                      secondaryTypographyProps={{
                        color: colors.textMuted,
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2, borderTop: `1px solid ${colors.border}` }}>
          <Button
            onClick={() => setFolderBrowserOpen(false)}
            sx={{ color: colors.textSecondary }}
          >
            ביטול
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleting && setDeleteDialogOpen(false)}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: dialogPaperStyles }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            borderBottom: `1px solid ${colors.border}`,
            pb: 2,
          }}
        >
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <DeleteIcon sx={{ color: '#ef4444' }} />
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#ef4444' }}>
            מחיקת פרויקט
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Typography variant="body1" sx={{ mb: 3, color: colors.textSecondary }}>
            האם אתה בטוח שברצונך למחוק את הפרויקט?
          </Typography>
          {projectToDelete && (
            <Box
              sx={{
                p: 2.5,
                borderRadius: '14px',
                backgroundColor: 'rgba(239, 68, 68, 0.06)',
                border: '1px solid rgba(239, 68, 68, 0.15)',
              }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: colors.textPrimary, mb: 0.5 }}>
                {projectToDelete.name}
              </Typography>
              <Typography variant="body2" sx={{ color: colors.textSecondary }}>
                {projectToDelete.total_files} קבצים יימחקו
              </Typography>
            </Box>
          )}
          <Box
            sx={{
              mt: 2.5,
              p: 2,
              borderRadius: '12px',
              backgroundColor: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1.5,
            }}
          >
            <WarningIcon sx={{ color: '#f59e0b', fontSize: 20, mt: 0.2 }} />
            <Typography variant="body2" sx={{ color: '#f59e0b' }}>
              פעולה זו תמחק את כל הקבצים, התוכניות והנתונים הקשורים לפרויקט.
              לא ניתן לבטל פעולה זו.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2, borderTop: `1px solid ${colors.border}` }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleting}
            sx={{ color: colors.textSecondary }}
          >
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleDeleteConfirm}
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={18} color="inherit" /> : <DeleteIcon />}
            sx={{
              px: 3,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              boxShadow: '0 8px 20px rgba(239, 68, 68, 0.3)',
              fontWeight: 600,
            }}
          >
            {deleting ? 'מוחק...' : 'מחק פרויקט'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  );
}
