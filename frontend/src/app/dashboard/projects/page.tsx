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
  Breadcrumbs,
  Link,
  CircularProgress,
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
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';

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

      // Scan folder and create plans
      await api.post(`/projects/${projectId}/scan`);

      // Start processing
      await api.post(`/projects/${projectId}/process`);

      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      setNewProjectFolder('');
      setScanResult(null);

      // Navigate to project
      router.push(`/dashboard/projects/${projectId}`);
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה ביצירת הפרויקט');
    } finally {
      setCreating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'processing':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      case 'scanning':
        return '#06b6d4';
      default:
        return '#64748b';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'הושלם';
      case 'processing':
        return 'בעיבוד';
      case 'failed':
        return 'נכשל';
      case 'scanning':
        return 'סורק';
      default:
        return 'ממתין';
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

  return (
    <MainLayout>
      <Header title="פרויקטים" subtitle="ניהול פרויקטים וסריקת תיקיות DWG" />

      {/* Action Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" fontWeight={600}>
          כל הפרויקטים ({projects.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchProjects}
          >
            רענן
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            }}
          >
            פרויקט חדש
          </Button>
        </Box>
      </Box>

      {/* Projects Grid */}
      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
              <Skeleton variant="rounded" height={200} />
            </Grid>
          ))}
        </Grid>
      ) : projects.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 8 }}>
          <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            אין פרויקטים עדיין
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            צור פרויקט חדש וסרוק תיקיית DWG
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            צור פרויקט ראשון
          </Button>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={project.id}>
              <Box
                sx={{
                  animation: 'fadeInUp 0.3s ease-out forwards',
                  animationDelay: `${index * 0.1}s`,
                  opacity: 0,
                  '@keyframes fadeInUp': {
                    '0%': { opacity: 0, transform: 'translateY(20px)' },
                    '100%': { opacity: 1, transform: 'translateY(0)' },
                  },
                }}
              >
                <Card
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 12px 24px -8px rgba(99, 102, 241, 0.3)',
                    },
                  }}
                  onClick={() => router.push(`/dashboard/projects/${project.id}`)}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
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
                        <FolderOpenIcon sx={{ color: '#6366f1', fontSize: 24 }} />
                      </Box>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="h6" fontWeight={600} noWrap>
                          {project.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" noWrap>
                          {project.folder_path || 'ללא תיקייה'}
                        </Typography>
                      </Box>
                      <IconButton
                        size="small"
                        onClick={(e) => handleDeleteClick(e, project)}
                        sx={{
                          color: '#94a3b8',
                          '&:hover': {
                            color: '#ef4444',
                            backgroundColor: alpha('#ef4444', 0.1),
                          },
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Chip
                        label={getStatusLabel(project.processing_status)}
                        size="small"
                        sx={{
                          backgroundColor: alpha(getStatusColor(project.processing_status), 0.1),
                          color: getStatusColor(project.processing_status),
                          fontWeight: 600,
                        }}
                      />
                      <Chip
                        icon={<FileIcon sx={{ fontSize: 14 }} />}
                        label={`${project.total_files} קבצים`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    {project.processing_status === 'processing' && (
                      <Box sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {project.processed_files} / {project.total_files} קבצים
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {project.processing_progress}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={project.processing_progress}
                          sx={{
                            height: 6,
                            borderRadius: 3,
                            backgroundColor: alpha('#6366f1', 0.1),
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 3,
                              background: 'linear-gradient(90deg, #6366f1 0%, #4f46e5 100%)',
                            },
                          }}
                        />
                      </Box>
                    )}

                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                      נוצר: {new Date(project.created_at).toLocaleDateString('he-IL')}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => !creating && setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FolderOpenIcon sx={{ color: '#6366f1' }} />
            פרויקט חדש
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="שם הפרויקט"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              fullWidth
              required
              placeholder="לדוגמה: פארק המים DCRC"
            />
            <TextField
              label="תיאור (אופציונלי)"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
              fullWidth
              multiline
              rows={2}
              placeholder="תיאור קצר של הפרויקט..."
            />
            <Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
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
                />
                <Button
                  variant="contained"
                  onClick={openFolderBrowser}
                  sx={{
                    minWidth: 140,
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                    color: '#ffffff',
                    whiteSpace: 'nowrap',
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
                  sx={{ mt: 1 }}
                  startIcon={scanning ? <RefreshIcon className="animate-spin" /> : <FolderOpenIcon />}
                >
                  {scanning ? 'סורק...' : 'סרוק לקבצי DWG'}
                </Button>
              )}
            </Box>

            {scanResult && (
              <Alert severity={scanResult.total_count > 0 ? 'success' : 'warning'}>
                <Typography variant="body2" fontWeight={600}>
                  נמצאו {scanResult.total_count} קבצי DWG/DXF
                </Typography>
                {scanResult.total_count > 0 && (
                  <Box sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
                    {scanResult.dwg_files.slice(0, 10).map((file, i) => (
                      <Typography key={i} variant="caption" display="block" color="text.secondary">
                        {file.split('\\').pop()}
                      </Typography>
                    ))}
                    {scanResult.total_count > 10 && (
                      <Typography variant="caption" color="text.secondary">
                        ...ועוד {scanResult.total_count - 10} קבצים
                      </Typography>
                    )}
                  </Box>
                )}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setCreateDialogOpen(false)} disabled={creating}>
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateProject}
            disabled={!newProjectName.trim() || !newProjectFolder.trim() || creating}
            startIcon={creating ? <RefreshIcon className="animate-spin" /> : <PlayIcon />}
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#ffffff',
              '&:disabled': {
                background: 'rgba(99, 102, 241, 0.3)',
                color: 'rgba(255, 255, 255, 0.5)',
              },
            }}
          >
            {creating ? 'יוצר פרויקט...' : 'צור והתחל עיבוד'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Folder Browser Dialog */}
      <Dialog
        open={folderBrowserOpen}
        onClose={() => setFolderBrowserOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FolderOpenIcon sx={{ color: '#6366f1' }} />
            בחר תיקייה
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Current path breadcrumb */}
          {browseResult && browseResult.current_path && (
            <Box sx={{ mb: 2, p: 1, bgcolor: alpha('#6366f1', 0.05), borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                נתיב נוכחי:
              </Typography>
              <Typography variant="body2" fontWeight={600} dir="ltr">
                {browseResult.current_path}
              </Typography>
            </Box>
          )}

          {/* Navigation buttons */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            {browseResult?.parent_path && (
              <Button
                size="small"
                startIcon={<ArrowUpIcon />}
                onClick={() => browseFolders(browseResult.parent_path!)}
              >
                תיקייה למעלה
              </Button>
            )}
            {browseResult?.current_path && (
              <Button
                size="small"
                variant="contained"
                sx={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#ffffff',
                }}
                onClick={() => selectFolder(browseResult.current_path)}
              >
                בחר תיקייה זו
              </Button>
            )}
          </Box>

          {/* Folder list */}
          {browsing ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List sx={{ maxHeight: 400, overflow: 'auto' }}>
              {browseResult?.folders.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  אין תיקיות משנה
                </Typography>
              )}
              {browseResult?.folders.map((folder) => (
                <ListItem key={folder.path} disablePadding>
                  <ListItemButton
                    onClick={() => browseFolders(folder.path)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      '&:hover': {
                        backgroundColor: alpha('#6366f1', 0.08),
                      },
                    }}
                  >
                    <ListItemIcon>
                      {folder.type === 'drive' ? (
                        <DriveIcon sx={{ color: '#6366f1' }} />
                      ) : (
                        <FolderIcon sx={{ color: '#f59e0b' }} />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={folder.name}
                      secondary={folder.type === 'drive' ? 'כונן' : null}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFolderBrowserOpen(false)}>
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
      >
        <DialogTitle sx={{ color: '#ef4444' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <DeleteIcon />
            מחיקת פרויקט
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            האם אתה בטוח שברצונך למחוק את הפרויקט?
          </Typography>
          {projectToDelete && (
            <Box sx={{ p: 2, bgcolor: alpha('#ef4444', 0.05), borderRadius: 1 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {projectToDelete.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {projectToDelete.total_files} קבצים יימחקו
              </Typography>
            </Box>
          )}
          <Alert severity="warning" sx={{ mt: 2 }}>
            פעולה זו תמחק את כל הקבצים, התוכניות והנתונים הקשורים לפרויקט.
            לא ניתן לבטל פעולה זו.
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleting}
          >
            ביטול
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteConfirm}
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} color="inherit" /> : <DeleteIcon />}
          >
            {deleting ? 'מוחק...' : 'מחק פרויקט'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  );
}
