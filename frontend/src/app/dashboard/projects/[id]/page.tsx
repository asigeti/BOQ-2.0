'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  alpha,
  Chip,
  IconButton,
  Skeleton,
  Grid,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Collapse,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  TextField,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Folder as FolderIcon,
  Description as FileIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Assessment as ReportIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Add as AddIcon,
  PictureAsPdf as PdfIcon,
  Warning as WarningIcon,
  AutoAwesome as AIIcon,
  InsertDriveFile as DocumentIcon,
  Speed as SpeedIcon,
  Layers as LayersIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import ExtractionReview from '@/components/ExtractionReview';
import FileReviewStage from '@/components/FileReviewStage';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';
import { useThemeMode } from '@/contexts/ThemeContext';

interface Plan {
  id: number;
  filename: string;
  file_type: string;
  processing_status: string;
  processing_progress: number;
}

// Helper to check if a filename is a PDF
const isPdfFile = (filename: string): boolean => {
  return filename.toLowerCase().endsWith('.pdf');
};

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
  plans: Plan[];
}

interface BOQItem {
  id?: number;
  item_code: string;
  description_he: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  confidence: number;
  source_files?: number;
  source_filename?: string | null;
  source_layer?: string | null;
  user_notes?: string | null;
  is_modified?: boolean;
}

interface BOQChapter {
  chapter_code: string;
  chapter_name_he: string;
  chapter_name_en: string;
  items: BOQItem[];
  chapter_total: number;
}

interface BOQData {
  project_name: string;
  chapters: BOQChapter[];
  summary: {
    subtotal: number;
    vat_rate: number;
    vat_amount: number;
    grand_total: number;
    total_files: number;
    total_items: number;
  };
  source_files: string[];
  warning?: string;
}

interface ExtractionFileData {
  plan_id: number;
  filename: string;
  processing_status: string;
  area_m2?: number;
  extraction_data?: {
    extraction_method: string;
    blocks_count: number;
    text_count: number;
    layers_count: number;
    total_area_cm2: number;
    polylines_count: number;
    circles_count: number;
    arcs_count: number;
    detected_units?: string;
  };
}

interface ExtractionData {
  project_id: number;
  project_name: string;
  total_files: number;
  extraction_summary: {
    total_area_m2: number;
    total_blocks: number;
    total_text_entities: number;
    total_layers: number;
    total_polylines: number;
  };
  files: ExtractionFileData[];
}

// Dialog common styles
const dialogPaperStyles = {
  backgroundColor: colors.bgDialog,
  border: '1px solid rgba(148, 163, 184, 0.1)',
  borderRadius: '20px',
  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
  backdropFilter: 'blur(20px)',
};

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;
  const [project, setProject] = useState<Project | null>(null);
  const [boqData, setBoqData] = useState<BOQData | null>(null);
  const [extractionData, setExtractionData] = useState<ExtractionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [boqLoading, setBoqLoading] = useState(false);
  const [expandedChapters, setExpandedChapters] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editedValues, setEditedValues] = useState<{
    quantity: number;
    unit_price: number;
    user_notes: string;
  }>({ quantity: 0, unit_price: 0, user_notes: '' });
  const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);
  const [selectedChapter, setSelectedChapter] = useState<BOQChapter | null>(null);
  const [newItemData, setNewItemData] = useState({
    item_code: '',
    description_he: '',
    quantity: 0,
    unit: 'יח׳',
    unit_price: 0,
    user_notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [generatingPdfBoq, setGeneratingPdfBoq] = useState(false);
  const [rerunning, setRerunning] = useState(false);
  const router = useRouter();
  const { showError, showConfirm, showSuccess } = useNotification();
  const { isDark } = useThemeMode();

  // Theme-aware colors
  const colors = {
    bg: isDark ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.95)',
    bgCard: isDark ? 'rgba(15, 23, 42, 0.7)' : '#ffffff',
    bgDialog: isDark ? '#0f172a' : '#ffffff',
    border: isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.1)',
    borderHover: isDark ? 'rgba(14, 165, 233, 0.3)' : 'rgba(3, 105, 161, 0.4)',
    textPrimary: isDark ? '#f1f5f9' : '#0f172a',
    textSecondary: isDark ? '#94a3b8' : '#334155',
    textMuted: isDark ? '#64748b' : '#475569',
    primary: isDark ? '#0ea5e9' : '#0369a1',
    tableBorder: isDark ? 'rgba(148, 163, 184, 0.06)' : 'rgba(15, 23, 42, 0.08)',
    shadow: isDark ? '0 8px 32px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.06)',
  };

  // Check if all files are PDFs (no CAD files)
  const isPdfOnlyProject = project?.plans && project.plans.length > 0 &&
    project.plans.every(plan => isPdfFile(plan.filename));

  const fetchProject = async () => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      setProject(response.data);

      const status = response.data.processing_status;

      if (status === 'processing' || status === 'generating_boq') {
        setPolling(true);
      } else {
        setPolling(false);
      }

      if (status === 'extracted') {
        fetchExtractionData();
      }

      if (status === 'completed' || status === 'generating_boq') {
        fetchBOQ();
        if (status === 'completed') {
          fetchExtractionData();
        }
      }
    } catch (error) {
      console.error('Failed to fetch project', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBOQ = async () => {
    try {
      setBoqLoading(true);
      const response = await api.get(`/projects/${projectId}/boq`);
      setBoqData(response.data);
      setExpandedChapters(response.data.chapters.map((c: BOQChapter) => c.chapter_code));
    } catch (error) {
      console.error('Failed to fetch BOQ', error);
    } finally {
      setBoqLoading(false);
    }
  };

  const fetchExtractionData = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/extraction`);
      setExtractionData(response.data);
    } catch (error) {
      console.error('Failed to fetch extraction data', error);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (polling) {
      interval = setInterval(fetchProject, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [polling]);

  const handleStartProcessing = async () => {
    try {
      await api.post(`/projects/${projectId}/process`);
      fetchProject();
    } catch (error) {
      console.error('Failed to start processing', error);
    }
  };

  const handleDeleteProject = async () => {
    try {
      setDeleting(true);
      await api.delete(`/projects/${projectId}`);
      router.push('/dashboard/projects');
    } catch (error: any) {
      showError(error.response?.data?.detail || 'Failed to delete project');
      setDeleting(false);
    }
  };

  const handleExtractionConfirmed = () => {
    fetchProject();
  };

  const handleRerunBoq = async () => {
    const confirmed = await showConfirm(
      'פעולה זו תאפס את הפרויקט לשלב בחירת השכבות. כתב הכמויות הקיים יימחק. להמשיך?'
    );
    if (!confirmed) return;

    try {
      setRerunning(true);
      await api.post(`/projects/${projectId}/reset-to-extraction`);
      showSuccess('הפרויקט אופס לשלב בחירת השכבות');
      fetchProject();
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה באיפוס הפרויקט');
    } finally {
      setRerunning(false);
    }
  };

  const handleGeneratePdfBoq = async () => {
    if (generatingPdfBoq) return;

    try {
      setGeneratingPdfBoq(true);
      await api.post(`/projects/${projectId}/extraction-confirm`, {
        selected_layer_ids: [],
        custom_area_m2: null,
      });
      fetchProject();
    } catch (error: any) {
      showError(error.response?.data?.detail || 'שגיאה ביצירת כתב הכמויות');
    } finally {
      setGeneratingPdfBoq(false);
    }
  };

  const toggleChapter = (code: string) => {
    setExpandedChapters((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const handleEditItem = (item: BOQItem) => {
    if (!item.id) return;
    setEditingItemId(item.id);
    setEditedValues({
      quantity: item.quantity,
      unit_price: item.unit_price,
      user_notes: item.user_notes || '',
    });
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setEditedValues({ quantity: 0, unit_price: 0, user_notes: '' });
  };

  const handleSaveEdit = async (itemId: number) => {
    try {
      await api.patch(`/projects/${projectId}/boq/items/${itemId}`, editedValues);
      setEditingItemId(null);
      fetchBOQ();
    } catch (error) {
      console.error('Failed to update item', error);
      showError('שגיאה בעדכון הפריט');
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    const confirmed = await showConfirm('האם למחוק פריט זה?');
    if (!confirmed) return;
    try {
      await api.delete(`/projects/${projectId}/boq/items/${itemId}`);
      fetchBOQ();
    } catch (error) {
      console.error('Failed to delete item', error);
      showError('שגיאה במחיקת הפריט');
    }
  };

  const handleOpenAddItemDialog = (chapter: BOQChapter) => {
    setSelectedChapter(chapter);
    const itemCount = chapter.items.length + 1;
    const nextItemCode = `${chapter.chapter_code}.${String(itemCount).padStart(2, '0')}`;
    setNewItemData({
      item_code: nextItemCode,
      description_he: '',
      quantity: 1,
      unit: 'יח׳',
      unit_price: 0,
      user_notes: '',
    });
    setAddItemDialogOpen(true);
  };

  const handleCloseAddItemDialog = () => {
    setAddItemDialogOpen(false);
    setSelectedChapter(null);
    setNewItemData({
      item_code: '',
      description_he: '',
      quantity: 0,
      unit: 'יח׳',
      unit_price: 0,
      user_notes: '',
    });
  };

  const handleCreateNewItem = async () => {
    if (!selectedChapter) return;

    try {
      setSaving(true);
      await api.post(`/projects/${projectId}/boq/items`, {
        project_id: parseInt(projectId),
        plan_id: null,
        chapter_code: selectedChapter.chapter_code,
        chapter_name_he: selectedChapter.chapter_name_he,
        chapter_name_en: selectedChapter.chapter_name_en,
        item_code: newItemData.item_code,
        description_he: newItemData.description_he,
        description_en: '',
        quantity: newItemData.quantity,
        unit: newItemData.unit,
        unit_price: newItemData.unit_price,
        total_price: newItemData.quantity * newItemData.unit_price,
        source_filename: 'ידני',
        source_layer: 'משתמש',
        confidence: 1.0,
        user_notes: newItemData.user_notes,
      });
      handleCloseAddItemDialog();
      fetchBOQ();
    } catch (error) {
      console.error('Failed to create item', error);
      showError('שגיאה ביצירת הפריט');
    } finally {
      setSaving(false);
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return { color: '#10b981', label: 'הושלם', glow: 'rgba(16, 185, 129, 0.4)' };
      case 'processing':
        return { color: '#f59e0b', label: 'מחלץ נתונים...', glow: 'rgba(245, 158, 11, 0.4)' };
      case 'extracted':
        return { color: '#8b5cf6', label: 'ממתין לבחירה', glow: 'rgba(139, 92, 246, 0.4)' };
      case 'generating_boq':
        return { color: colors.primary, label: 'יוצר כתב כמויות...', glow: 'rgba(14, 165, 233, 0.4)' };
      case 'failed':
        return { color: '#ef4444', label: 'נכשל', glow: 'rgba(239, 68, 68, 0.4)' };
      default:
        return { color: colors.textMuted, label: 'ממתין', glow: 'rgba(100, 116, 139, 0.4)' };
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.5) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return (
      <MainLayout>
        <Box sx={{ p: 3 }}>
          <Skeleton variant="text" width={200} height={40} sx={{ backgroundColor: 'rgba(148, 163, 184, 0.1)' }} />
          <Skeleton variant="rounded" height={200} sx={{ mt: 2, borderRadius: '20px', backgroundColor: 'rgba(148, 163, 184, 0.08)' }} />
          <Skeleton variant="rounded" height={400} sx={{ mt: 2, borderRadius: '20px', backgroundColor: 'rgba(148, 163, 184, 0.08)' }} />
        </Box>
      </MainLayout>
    );
  }

  if (!project) {
    return (
      <MainLayout>
        <Box
          sx={{
            textAlign: 'center',
            py: 12,
            px: 4,
            borderRadius: '24px',
            backgroundColor: colors.bg,
            border: `1px solid ${colors.border}`,
          }}
        >
          <FolderIcon sx={{ fontSize: 64, color: colors.textMuted, mb: 2 }} />
          <Typography variant="h5" sx={{ color: colors.textSecondary, mb: 3 }}>
            פרויקט לא נמצא
          </Typography>
          <Button
            onClick={() => router.push('/dashboard/projects')}
            variant="contained"
            sx={{
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
            }}
          >
            חזרה לפרויקטים
          </Button>
        </Box>
      </MainLayout>
    );
  }

  const statusConfig = getStatusConfig(project.processing_status);

  return (
    <MainLayout>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          mb: 4,
          p: 3,
          borderRadius: '20px',
          backgroundColor: colors.bg,
          border: `1px solid ${colors.border}`,
          backdropFilter: 'blur(12px)',
        }}
      >
        <Tooltip title="חזרה לפרויקטים">
          <IconButton
            onClick={() => router.push('/dashboard/projects')}
            sx={{
              width: 44,
              height: 44,
              backgroundColor: 'rgba(148, 163, 184, 0.08)',
              border: '1px solid rgba(148, 163, 184, 0.1)',
              color: colors.textSecondary,
              transition: 'all 0.2s ease',
              '&:hover': {
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                borderColor: 'rgba(14, 165, 233, 0.3)',
                color: colors.primary,
              },
            }}
          >
            <BackIcon sx={{ transform: 'rotate(180deg)' }} />
          </IconButton>
        </Tooltip>
        <Box
          sx={{
            width: 56,
            height: 56,
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <FolderIcon sx={{ color: '#f59e0b', fontSize: 28 }} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 800,
              color: colors.textPrimary,
              fontSize: { xs: '1.3rem', md: '1.75rem' },
              letterSpacing: '-0.02em',
            }}
          >
            {project.name}
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: colors.textMuted, direction: 'ltr', textAlign: 'right' }}
          >
            {project.folder_path}
          </Typography>
        </Box>
        <Chip
          label={statusConfig.label}
          sx={{
            height: 32,
            backgroundColor: alpha(statusConfig.color, 0.12),
            color: statusConfig.color,
            border: `1px solid ${alpha(statusConfig.color, 0.25)}`,
            fontWeight: 600,
            fontSize: '0.85rem',
            boxShadow: `0 0 16px ${statusConfig.glow}`,
          }}
        />
        {project.processing_status === 'completed' && (
          <Button
            variant="outlined"
            startIcon={rerunning ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
            onClick={handleRerunBoq}
            disabled={rerunning}
            sx={{
              borderRadius: '12px',
              borderColor: 'rgba(14, 165, 233, 0.3)',
              color: colors.primary,
              px: 2,
              '&:hover': {
                borderColor: colors.primary,
                backgroundColor: 'rgba(14, 165, 233, 0.08)',
              },
            }}
          >
            {rerunning ? 'מאפס...' : 'הפעל מחדש'}
          </Button>
        )}
        <Tooltip title="מחק פרויקט">
          <IconButton
            onClick={() => setDeleteDialogOpen(true)}
            sx={{
              width: 44,
              height: 44,
              backgroundColor: 'rgba(148, 163, 184, 0.05)',
              color: colors.textMuted,
              transition: 'all 0.2s ease',
              '&:hover': {
                color: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
              },
            }}
          >
            <DeleteIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { label: 'סה״כ קבצים', value: project.total_files, icon: <DocumentIcon />, color: colors.primary },
          { label: 'עובדו', value: project.processed_files, icon: <CheckIcon />, color: '#10b981' },
          { label: 'התקדמות', value: `${project.processing_progress}%`, icon: <SpeedIcon />, color: '#f59e0b' },
          { label: 'פריטים בכתב כמויות', value: boqData?.summary.total_items || 0, icon: <CategoryIcon />, color: '#8b5cf6' },
        ].map((stat, idx) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={idx}>
            <Box
              sx={{
                animation: 'fadeInUp 0.4s ease-out forwards',
                animationDelay: `${idx * 0.1}s`,
                opacity: 0,
                '@keyframes fadeInUp': {
                  '0%': { opacity: 0, transform: 'translateY(20px)' },
                  '100%': { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              <Card
                sx={{
                  borderRadius: '20px',
                  backgroundColor: colors.bgCard,
                  border: `1px solid ${colors.border}`,
                  backdropFilter: 'blur(12px)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    borderColor: alpha(stat.color, 0.3),
                  },
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="body2" sx={{ color: colors.textMuted, fontWeight: 500 }}>
                      {stat.label}
                    </Typography>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: '12px',
                        backgroundColor: alpha(stat.color, 0.1),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        '& svg': { color: stat.color, fontSize: 20 },
                      }}
                    >
                      {stat.icon}
                    </Box>
                  </Box>
                  <Typography
                    variant="h3"
                    sx={{
                      fontWeight: 800,
                      background: `linear-gradient(135deg, ${stat.color} 0%, ${alpha(stat.color, 0.7)} 100%)`,
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      fontSize: '2rem',
                    }}
                  >
                    {stat.value}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* Processing Progress */}
      {project.processing_status === 'processing' && (
        <Card
          sx={{
            mb: 4,
            borderRadius: '20px',
            backgroundColor: colors.bgCard,
            border: '1px solid rgba(245, 158, 11, 0.15)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '14px',
                  background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)',
                  border: '1px solid rgba(245, 158, 11, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  animation: 'pulse 2s infinite',
                  '@keyframes pulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.6 },
                  },
                }}
              >
                <AIIcon sx={{ color: '#f59e0b', fontSize: 24 }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                מעבד קבצים...
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={project.processing_progress}
              sx={{
                height: 10,
                borderRadius: 10,
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 10,
                  background: 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)',
                  boxShadow: '0 0 20px rgba(245, 158, 11, 0.5)',
                },
              }}
            />
            <Typography variant="body2" sx={{ color: colors.textSecondary, mt: 2 }}>
              {project.processed_files} מתוך {project.total_files} קבצים
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* File Review Stage */}
      {project.processing_status === 'pending' && (
        <FileReviewStage
          projectId={project.id}
          files={project.plans}
          onStartProcessing={() => {
            api.post(`/projects/${projectId}/process`);
            fetchProject();
          }}
          onFilesChanged={fetchProject}
        />
      )}

      {/* Files List */}
      {project.processing_status !== 'pending' && (
        <Card
          sx={{
            mb: 4,
            borderRadius: '20px',
            backgroundColor: colors.bgCard,
            border: `1px solid ${colors.border}`,
            backdropFilter: 'blur(12px)',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.05) 100%)',
                  border: '1px solid rgba(14, 165, 233, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <FileIcon sx={{ color: colors.primary, fontSize: 22 }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                קבצי תכניות בפרויקט
              </Typography>
            </Box>

            <TableContainer
              sx={{
                borderRadius: '14px',
                backgroundColor: 'rgba(10, 15, 26, 0.5)',
                border: '1px solid rgba(148, 163, 184, 0.06)',
              }}
            >
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שם קובץ</TableCell>
                    <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>סוג</TableCell>
                    <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>סטטוס</TableCell>
                    <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>התקדמות</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {project.plans.map((plan) => {
                    const planStatus = getStatusConfig(plan.processing_status);
                    return (
                      <TableRow key={plan.id} sx={{ '&:last-child td': { border: 0 } }}>
                        <TableCell sx={{ borderColor: colors.tableBorder }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            {isPdfFile(plan.filename) ? (
                              <PdfIcon sx={{ fontSize: 18, color: '#ef4444' }} />
                            ) : (
                              <FileIcon sx={{ fontSize: 18, color: colors.primary }} />
                            )}
                            <Typography sx={{ color: colors.textPrimary, fontSize: '0.9rem' }}>
                              {plan.filename}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ borderColor: colors.tableBorder }}>
                          <Chip
                            label={plan.file_type}
                            size="small"
                            sx={{
                              height: 24,
                              backgroundColor: 'rgba(148, 163, 184, 0.1)',
                              color: colors.textSecondary,
                              fontSize: '0.75rem',
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ borderColor: colors.tableBorder }}>
                          <Chip
                            label={planStatus.label}
                            size="small"
                            sx={{
                              height: 24,
                              backgroundColor: alpha(planStatus.color, 0.12),
                              color: planStatus.color,
                              fontWeight: 600,
                              fontSize: '0.7rem',
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ borderColor: colors.tableBorder }}>
                          {plan.processing_status === 'processing' ? (
                            <LinearProgress
                              variant="determinate"
                              value={plan.processing_progress}
                              sx={{
                                width: 80,
                                height: 6,
                                borderRadius: 6,
                                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                '& .MuiLinearProgress-bar': {
                                  borderRadius: 6,
                                  background: 'linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)',
                                },
                              }}
                            />
                          ) : (
                            <Typography sx={{ color: colors.textSecondary, fontSize: '0.85rem' }}>
                              {plan.processing_progress}%
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Extraction Review */}
      {project.processing_status === 'extracted' && (
        <Card
          sx={{
            mb: 4,
            borderRadius: '20px',
            backgroundColor: colors.bgCard,
            border: '1px solid rgba(139, 92, 246, 0.15)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {isPdfOnlyProject ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Box
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.05) 100%)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                  }}
                >
                  <PdfIcon sx={{ fontSize: 40, color: '#ef4444' }} />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 700, color: colors.textPrimary, mb: 1 }}>
                  קבצי PDF מוכנים ליצירת כתב כמויות
                </Typography>
                <Typography variant="body1" sx={{ color: colors.textSecondary, mb: 4, maxWidth: 500, mx: 'auto' }}>
                  זוהו {project.plans.length} קבצי PDF בפרויקט.
                  לחץ על הכפתור כדי ליצור כתב כמויות אוטומטי.
                </Typography>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: '14px',
                    backgroundColor: 'rgba(14, 165, 233, 0.08)',
                    border: '1px solid rgba(14, 165, 233, 0.2)',
                    mb: 4,
                    maxWidth: 500,
                    mx: 'auto',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                  }}
                >
                  <AIIcon sx={{ color: colors.primary }} />
                  <Typography variant="body2" sx={{ color: colors.primary, textAlign: 'right' }}>
                    קבצי PDF אינם מכילים שכבות AutoCAD - המערכת תיצור כתב כמויות ישירות מהנתונים שחולצו.
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGeneratePdfBoq}
                  disabled={generatingPdfBoq}
                  startIcon={generatingPdfBoq ? <CircularProgress size={20} color="inherit" /> : <PlayIcon />}
                  sx={{
                    px: 5,
                    py: 1.5,
                    borderRadius: '14px',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                    boxShadow: '0 8px 24px rgba(14, 165, 233, 0.35)',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 32px rgba(14, 165, 233, 0.45)',
                    },
                  }}
                >
                  {generatingPdfBoq ? 'מייצר כתב כמויות...' : 'צור כתב כמויות'}
                </Button>
              </Box>
            ) : (
              <ExtractionReview
                projectId={project.id}
                onConfirm={handleExtractionConfirmed}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Generating BOQ Progress */}
      {project.processing_status === 'generating_boq' && (
        <Card
          sx={{
            mb: 4,
            borderRadius: '20px',
            backgroundColor: colors.bgCard,
            border: '1px solid rgba(14, 165, 233, 0.15)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '14px',
                  background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.05) 100%)',
                  border: '1px solid rgba(14, 165, 233, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CircularProgress size={24} sx={{ color: colors.primary }} />
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                  יוצר כתב כמויות...
                </Typography>
                <Typography variant="body2" sx={{ color: colors.textMuted }}>
                  מערכת ה-AI מעבדת את הנתונים ויוצרת כתב כמויות מפורט עם מחירי דקל
                </Typography>
              </Box>
            </Box>
            <LinearProgress
              sx={{
                height: 8,
                borderRadius: 8,
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 8,
                  background: 'linear-gradient(90deg, #0ea5e9 0%, #38bdf8 100%)',
                  boxShadow: '0 0 16px rgba(14, 165, 233, 0.5)',
                },
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Extraction Summary */}
      {project.processing_status === 'completed' && extractionData && (() => {
        const isPdfProject = extractionData.files.every(f => f.filename.toLowerCase().endsWith('.pdf'));

        return (
          <Card
            sx={{
              mb: 4,
              borderRadius: '20px',
              backgroundColor: colors.bgCard,
              border: `1px solid ${colors.border}`,
              backdropFilter: 'blur(12px)',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: '12px',
                    background: isPdfProject
                      ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.05) 100%)'
                      : 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%)',
                    border: `1px solid ${isPdfProject ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {isPdfProject ? (
                    <PdfIcon sx={{ color: '#ef4444', fontSize: 22 }} />
                  ) : (
                    <LayersIcon sx={{ color: '#10b981', fontSize: 22 }} />
                  )}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                  {isPdfProject ? 'נתוני חילוץ מ-PDF' : 'נתוני חילוץ מ-AutoCAD'}
                </Typography>
              </Box>

              <Grid container spacing={2} sx={{ mb: 3 }}>
                {isPdfProject ? (
                  [
                    { label: 'קבצי PDF', value: extractionData.total_files, color: '#ef4444' },
                    { label: 'פריטים שנמצאו', value: extractionData.extraction_summary.total_text_entities.toLocaleString('he-IL'), color: '#f59e0b' },
                    { label: 'מנוע AI', value: 'Gemini', color: '#10b981' },
                    { label: 'שטח כולל (מ״ר)', value: extractionData.extraction_summary.total_area_m2 > 0 ? extractionData.extraction_summary.total_area_m2.toLocaleString('he-IL') : '-', color: colors.primary },
                  ].map((stat, idx) => (
                    <Grid size={{ xs: 6, sm: 3 }} key={idx}>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: '14px',
                          backgroundColor: alpha(stat.color, 0.06),
                          border: `1px solid ${alpha(stat.color, 0.15)}`,
                          textAlign: 'center',
                        }}
                      >
                        <Typography variant="h4" sx={{ fontWeight: 700, color: stat.color }}>
                          {stat.value}
                        </Typography>
                        <Typography variant="caption" sx={{ color: colors.textMuted }}>
                          {stat.label}
                        </Typography>
                      </Box>
                    </Grid>
                  ))
                ) : (
                  [
                    { label: 'שטח כולל (מ״ר)', value: extractionData.extraction_summary.total_area_m2.toLocaleString('he-IL'), color: colors.primary },
                    { label: 'בלוקים', value: extractionData.extraction_summary.total_blocks.toLocaleString('he-IL'), color: '#10b981' },
                    { label: 'טקסט', value: extractionData.extraction_summary.total_text_entities.toLocaleString('he-IL'), color: '#f59e0b' },
                    { label: 'שכבות', value: extractionData.extraction_summary.total_layers.toLocaleString('he-IL'), color: '#8b5cf6' },
                    { label: 'פוליליינים', value: extractionData.extraction_summary.total_polylines.toLocaleString('he-IL'), color: '#ec4899' },
                    { label: 'קבצים', value: extractionData.total_files, color: colors.textMuted },
                  ].map((stat, idx) => (
                    <Grid size={{ xs: 6, sm: 4, md: 2 }} key={idx}>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: '14px',
                          backgroundColor: alpha(stat.color, 0.06),
                          border: `1px solid ${alpha(stat.color, 0.15)}`,
                          textAlign: 'center',
                        }}
                      >
                        <Typography variant="h4" sx={{ fontWeight: 700, color: stat.color, fontSize: '1.5rem' }}>
                          {stat.value}
                        </Typography>
                        <Typography variant="caption" sx={{ color: colors.textMuted }}>
                          {stat.label}
                        </Typography>
                      </Box>
                    </Grid>
                  ))
                )}
              </Grid>

              <Typography variant="subtitle1" sx={{ fontWeight: 600, color: colors.textPrimary, mb: 2 }}>
                פירוט לפי קובץ
              </Typography>
              <TableContainer
                sx={{
                  borderRadius: '14px',
                  backgroundColor: 'rgba(10, 15, 26, 0.5)',
                  border: '1px solid rgba(148, 163, 184, 0.06)',
                }}
              >
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ backgroundColor: 'rgba(14, 165, 233, 0.03)' }}>
                      <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שם קובץ</TableCell>
                      {isPdfProject ? (
                        <>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>פריטים</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>סוג תכנית</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שטח (מ״ר)</TableCell>
                        </>
                      ) : (
                        <>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שטח (מ״ר)</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>בלוקים</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>טקסט</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שכבות</TableCell>
                          <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>פוליליינים</TableCell>
                        </>
                      )}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {extractionData.files.map((file) => (
                      <TableRow key={file.plan_id} sx={{ '&:last-child td': { border: 0 } }}>
                        <TableCell sx={{ borderColor: colors.tableBorder }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {file.filename.toLowerCase().endsWith('.pdf') ? (
                              <PdfIcon sx={{ fontSize: 18, color: '#ef4444' }} />
                            ) : (
                              <FileIcon sx={{ fontSize: 18, color: colors.primary }} />
                            )}
                            <Typography sx={{ color: colors.textPrimary, fontSize: '0.9rem' }}>
                              {file.filename}
                            </Typography>
                          </Box>
                        </TableCell>
                        {isPdfProject ? (
                          <>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {(file as any).items_count?.toLocaleString('he-IL') || file.extraction_data?.text_count?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.extraction_data?.extraction_method || 'site_development'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.area_m2 && file.area_m2 > 0 ? file.area_m2.toLocaleString('he-IL') : '-'}
                            </TableCell>
                          </>
                        ) : (
                          <>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.area_m2?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.extraction_data?.blocks_count?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.extraction_data?.text_count?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.extraction_data?.layers_count?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                            <TableCell align="right" sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                              {file.extraction_data?.polylines_count?.toLocaleString('he-IL') || '-'}
                            </TableCell>
                          </>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        );
      })()}

      {/* BOQ Section */}
      {project.processing_status === 'completed' && (
        <Card
          sx={{
            borderRadius: '20px',
            backgroundColor: colors.bgCard,
            border: `1px solid ${colors.border}`,
            backdropFilter: 'blur(12px)',
          }}
        >
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: '14px',
                    background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.05) 100%)',
                    border: '1px solid rgba(14, 165, 233, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ReportIcon sx={{ color: colors.primary, fontSize: 24 }} />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                  כתב כמויות מאוחד
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<PdfIcon />}
                  onClick={() => window.open(`http://localhost:7000/projects/${projectId}/boq/export/pdf`, '_blank')}
                  sx={{
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    boxShadow: '0 6px 20px rgba(239, 68, 68, 0.3)',
                    fontWeight: 600,
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 10px 28px rgba(239, 68, 68, 0.4)',
                    },
                  }}
                >
                  ייצא ל-PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => window.open(`http://localhost:7000/projects/${projectId}/boq/export`, '_blank')}
                  sx={{
                    borderRadius: '12px',
                    borderColor: 'rgba(14, 165, 233, 0.3)',
                    color: colors.primary,
                    '&:hover': {
                      borderColor: colors.primary,
                      backgroundColor: 'rgba(14, 165, 233, 0.08)',
                    },
                  }}
                >
                  ייצא ל-Excel
                </Button>
              </Box>
            </Box>

            {boqLoading ? (
              <Box>
                <Skeleton variant="rounded" height={60} sx={{ mb: 2, borderRadius: '14px', backgroundColor: 'rgba(148, 163, 184, 0.08)' }} />
                <Skeleton variant="rounded" height={200} sx={{ borderRadius: '14px', backgroundColor: 'rgba(148, 163, 184, 0.08)' }} />
              </Box>
            ) : boqData ? (
              <>
                {boqData.warning && boqData.chapters.length === 0 && (
                  <Box
                    sx={{
                      p: 4,
                      mb: 3,
                      borderRadius: '16px',
                      backgroundColor: 'rgba(245, 158, 11, 0.08)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      textAlign: 'center',
                    }}
                  >
                    <WarningIcon sx={{ fontSize: 48, color: '#f59e0b', mb: 2 }} />
                    <Typography variant="h6" sx={{ color: '#f59e0b', mb: 1 }}>
                      אין נתוני כתב כמויות
                    </Typography>
                    <Typography sx={{ color: colors.textSecondary }}>
                      {boqData.warning}
                    </Typography>
                  </Box>
                )}

                {boqData.chapters.map((chapter) => (
                  <Box key={chapter.chapter_code} sx={{ mb: 2 }}>
                    <Box
                      onClick={() => toggleChapter(chapter.chapter_code)}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 2.5,
                        borderRadius: '14px',
                        backgroundColor: 'rgba(14, 165, 233, 0.06)',
                        border: '1px solid rgba(14, 165, 233, 0.12)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          backgroundColor: 'rgba(14, 165, 233, 0.1)',
                          borderColor: 'rgba(14, 165, 233, 0.25)',
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                          פרק {chapter.chapter_code}: {chapter.chapter_name_he}
                        </Typography>
                        <Chip
                          label={`${chapter.items.length} פריטים`}
                          size="small"
                          sx={{
                            height: 24,
                            backgroundColor: 'rgba(148, 163, 184, 0.1)',
                            color: colors.textSecondary,
                            fontSize: '0.75rem',
                          }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 700,
                            background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                          }}
                        >
                          {chapter.chapter_total.toLocaleString('he-IL')} ₪
                        </Typography>
                        <Tooltip title="הוסף פריט חדש">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenAddItemDialog(chapter);
                            }}
                            sx={{
                              width: 32,
                              height: 32,
                              backgroundColor: 'rgba(16, 185, 129, 0.1)',
                              color: '#10b981',
                              '&:hover': {
                                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                              },
                            }}
                          >
                            <AddIcon sx={{ fontSize: 18 }} />
                          </IconButton>
                        </Tooltip>
                        {expandedChapters.includes(chapter.chapter_code) ? (
                          <CollapseIcon sx={{ color: colors.textMuted }} />
                        ) : (
                          <ExpandIcon sx={{ color: colors.textMuted }} />
                        )}
                      </Box>
                    </Box>

                    <Collapse in={expandedChapters.includes(chapter.chapter_code)}>
                      <TableContainer
                        sx={{
                          mt: 1,
                          borderRadius: '14px',
                          backgroundColor: 'rgba(10, 15, 26, 0.5)',
                          border: '1px solid rgba(148, 163, 184, 0.06)',
                        }}
                      >
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ backgroundColor: 'rgba(14, 165, 233, 0.03)' }}>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>קוד</TableCell>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>תיאור</TableCell>
                              <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>כמות</TableCell>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>יחידה</TableCell>
                              <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>מחיר יח׳</TableCell>
                              <TableCell align="right" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>סה״כ</TableCell>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>קובץ</TableCell>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>שכבה</TableCell>
                              <TableCell sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>הערות</TableCell>
                              <TableCell align="center" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>אמינות</TableCell>
                              <TableCell align="center" sx={{ color: colors.textMuted, fontWeight: 600, borderColor: 'rgba(148, 163, 184, 0.08)' }}>פעולות</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {chapter.items.map((item, idx) => {
                              const isEditing = editingItemId === item.id;
                              return (
                                <TableRow
                                  key={idx}
                                  sx={{
                                    backgroundColor: isEditing ? 'rgba(14, 165, 233, 0.05)' : 'transparent',
                                    ...(item.is_modified && {
                                      borderRight: '3px solid #f59e0b',
                                    }),
                                    '&:last-child td': { border: 0 },
                                  }}
                                >
                                  <TableCell sx={{ fontWeight: 600, color: colors.textPrimary, borderColor: colors.tableBorder }}>
                                    {item.item_code}
                                  </TableCell>
                                  <TableCell sx={{ color: '#cbd5e1', maxWidth: 200, borderColor: colors.tableBorder }}>
                                    {item.description_he}
                                  </TableCell>
                                  <TableCell align="right" sx={{ borderColor: colors.tableBorder }}>
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        type="number"
                                        value={editedValues.quantity}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, quantity: parseFloat(e.target.value) })
                                        }
                                        sx={{
                                          width: 80,
                                          '& .MuiOutlinedInput-root': {
                                            backgroundColor: 'rgba(10, 15, 26, 0.5)',
                                          },
                                        }}
                                      />
                                    ) : (
                                      <Typography sx={{ color: colors.textPrimary }}>
                                        {item.quantity.toLocaleString('he-IL')}
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell sx={{ color: colors.textSecondary, borderColor: colors.tableBorder }}>
                                    {item.unit}
                                  </TableCell>
                                  <TableCell align="right" sx={{ borderColor: colors.tableBorder }}>
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        type="number"
                                        value={editedValues.unit_price}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, unit_price: parseFloat(e.target.value) })
                                        }
                                        sx={{
                                          width: 90,
                                          '& .MuiOutlinedInput-root': {
                                            backgroundColor: 'rgba(10, 15, 26, 0.5)',
                                          },
                                        }}
                                      />
                                    ) : (
                                      <Typography sx={{ color: colors.textPrimary }}>
                                        {item.unit_price.toLocaleString('he-IL')} ₪
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell align="right" sx={{ borderColor: colors.tableBorder }}>
                                    <Typography sx={{ fontWeight: 600, color: colors.primary }}>
                                      {item.total_price.toLocaleString('he-IL')} ₪
                                    </Typography>
                                  </TableCell>
                                  <TableCell sx={{ fontSize: '0.8rem', color: colors.textMuted, borderColor: colors.tableBorder }}>
                                    {item.source_filename || '-'}
                                  </TableCell>
                                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: colors.textMuted, maxWidth: 120, borderColor: colors.tableBorder }}>
                                    <Tooltip title={item.source_layer || '-'}>
                                      <span>
                                        {item.source_layer
                                          ? item.source_layer.length > 20
                                            ? `${item.source_layer.substring(0, 20)}...`
                                            : item.source_layer
                                          : '-'}
                                      </span>
                                    </Tooltip>
                                  </TableCell>
                                  <TableCell sx={{ minWidth: 120, borderColor: colors.tableBorder }}>
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        value={editedValues.user_notes}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, user_notes: e.target.value })
                                        }
                                        placeholder="הערה..."
                                        fullWidth
                                        sx={{
                                          '& .MuiOutlinedInput-root': {
                                            backgroundColor: 'rgba(10, 15, 26, 0.5)',
                                          },
                                        }}
                                      />
                                    ) : (
                                      <Typography sx={{ fontSize: '0.8rem', color: colors.textMuted }}>
                                        {item.user_notes || '-'}
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell align="center" sx={{ borderColor: colors.tableBorder }}>
                                    <Chip
                                      label={`${Math.round(item.confidence * 100)}%`}
                                      size="small"
                                      sx={{
                                        height: 22,
                                        backgroundColor: alpha(getConfidenceColor(item.confidence), 0.12),
                                        color: getConfidenceColor(item.confidence),
                                        fontWeight: 600,
                                        fontSize: '0.7rem',
                                      }}
                                    />
                                  </TableCell>
                                  <TableCell align="center" sx={{ borderColor: colors.tableBorder }}>
                                    {isEditing ? (
                                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                                        <Tooltip title="שמור">
                                          <IconButton
                                            size="small"
                                            onClick={() => item.id && handleSaveEdit(item.id)}
                                            sx={{
                                              color: '#10b981',
                                              '&:hover': { backgroundColor: 'rgba(16, 185, 129, 0.1)' },
                                            }}
                                          >
                                            <SaveIcon sx={{ fontSize: 18 }} />
                                          </IconButton>
                                        </Tooltip>
                                        <Tooltip title="בטל">
                                          <IconButton
                                            size="small"
                                            onClick={handleCancelEdit}
                                            sx={{
                                              color: colors.textMuted,
                                              '&:hover': { backgroundColor: 'rgba(148, 163, 184, 0.1)' },
                                            }}
                                          >
                                            <CancelIcon sx={{ fontSize: 18 }} />
                                          </IconButton>
                                        </Tooltip>
                                      </Box>
                                    ) : (
                                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                                        <Tooltip title="ערוך">
                                          <IconButton
                                            size="small"
                                            onClick={() => handleEditItem(item)}
                                            sx={{
                                              color: colors.primary,
                                              '&:hover': { backgroundColor: 'rgba(14, 165, 233, 0.1)' },
                                            }}
                                          >
                                            <EditIcon sx={{ fontSize: 18 }} />
                                          </IconButton>
                                        </Tooltip>
                                        <Tooltip title="מחק">
                                          <IconButton
                                            size="small"
                                            onClick={() => item.id && handleDeleteItem(item.id)}
                                            sx={{
                                              color: '#ef4444',
                                              '&:hover': { backgroundColor: 'rgba(239, 68, 68, 0.1)' },
                                            }}
                                          >
                                            <DeleteIcon sx={{ fontSize: 18 }} />
                                          </IconButton>
                                        </Tooltip>
                                      </Box>
                                    )}
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Collapse>
                  </Box>
                ))}

                <Divider sx={{ my: 4, borderColor: 'rgba(148, 163, 184, 0.08)' }} />

                {/* Summary */}
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Box
                    sx={{
                      width: 320,
                      p: 3,
                      borderRadius: '16px',
                      backgroundColor: 'rgba(14, 165, 233, 0.05)',
                      border: '1px solid rgba(14, 165, 233, 0.15)',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Typography sx={{ color: colors.textSecondary }}>סיכום ביניים:</Typography>
                      <Typography sx={{ fontWeight: 600, color: colors.textPrimary }}>
                        {boqData.summary.subtotal.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Typography sx={{ color: colors.textSecondary }}>
                        מע״מ ({(boqData.summary.vat_rate * 100).toFixed(0)}%):
                      </Typography>
                      <Typography sx={{ fontWeight: 600, color: colors.textPrimary }}>
                        {boqData.summary.vat_amount.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                    <Divider sx={{ my: 2, borderColor: 'rgba(14, 165, 233, 0.2)' }} />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
                        סה״כ:
                      </Typography>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 800,
                          background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                        }}
                      >
                        {boqData.summary.grand_total.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </>
            ) : (
              <Typography sx={{ color: colors.textMuted, textAlign: 'center', py: 4 }}>
                לא נמצאו נתונים
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

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
            borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
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
          <Typography variant="body1" sx={{ mb: 3, color: '#cbd5e1' }}>
            האם אתה בטוח שברצונך למחוק את הפרויקט?
          </Typography>
          {project && (
            <Box
              sx={{
                p: 2.5,
                borderRadius: '14px',
                backgroundColor: 'rgba(239, 68, 68, 0.06)',
                border: '1px solid rgba(239, 68, 68, 0.15)',
              }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: colors.textPrimary, mb: 0.5 }}>
                {project.name}
              </Typography>
              <Typography variant="body2" sx={{ color: colors.textSecondary }}>
                {project.total_files} קבצים יימחקו
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
        <DialogActions sx={{ p: 3, pt: 2, borderTop: '1px solid rgba(148, 163, 184, 0.08)' }}>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting} sx={{ color: colors.textSecondary }}>
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleDeleteProject}
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

      {/* Add New Item Dialog */}
      <Dialog
        open={addItemDialogOpen}
        onClose={() => !saving && handleCloseAddItemDialog()}
        maxWidth="sm"
        fullWidth
        dir="rtl"
        PaperProps={{ sx: dialogPaperStyles }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
            pb: 2,
          }}
        >
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AddIcon sx={{ color: '#10b981' }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: colors.textPrimary }}>
              הוסף פריט חדש
            </Typography>
            {selectedChapter && (
              <Chip
                label={`פרק ${selectedChapter.chapter_code}: ${selectedChapter.chapter_name_he}`}
                size="small"
                sx={{
                  mt: 0.5,
                  height: 22,
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  color: '#10b981',
                  fontSize: '0.75rem',
                }}
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3, pb: 2 }}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="קוד פריט"
                fullWidth
                value={newItemData.item_code}
                onChange={(e) => setNewItemData({ ...newItemData, item_code: e.target.value })}
                disabled={saving}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="יחידה"
                fullWidth
                value={newItemData.unit}
                onChange={(e) => setNewItemData({ ...newItemData, unit: e.target.value })}
                disabled={saving}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                label="תיאור"
                fullWidth
                multiline
                rows={2}
                value={newItemData.description_he}
                onChange={(e) => setNewItemData({ ...newItemData, description_he: e.target.value })}
                disabled={saving}
                required
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                label="כמות"
                type="number"
                fullWidth
                value={newItemData.quantity}
                onChange={(e) => setNewItemData({ ...newItemData, quantity: parseFloat(e.target.value) || 0 })}
                disabled={saving}
                required
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                label="מחיר יחידה (₪)"
                type="number"
                fullWidth
                value={newItemData.unit_price}
                onChange={(e) => setNewItemData({ ...newItemData, unit_price: parseFloat(e.target.value) || 0 })}
                disabled={saving}
                required
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                label="סה״כ (₪)"
                fullWidth
                value={(newItemData.quantity * newItemData.unit_price).toLocaleString('he-IL')}
                disabled
                sx={{
                  '& .MuiInputBase-input': {
                    fontWeight: 700,
                    color: colors.primary,
                  },
                }}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                label="הערות"
                fullWidth
                multiline
                rows={2}
                value={newItemData.user_notes}
                onChange={(e) => setNewItemData({ ...newItemData, user_notes: e.target.value })}
                disabled={saving}
                placeholder="הערות נוספות (אופציונלי)"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(148, 163, 184, 0.03)',
                  },
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(148, 163, 184, 0.08)' }}>
          <Button onClick={handleCloseAddItemDialog} disabled={saving} sx={{ color: colors.textSecondary }}>
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateNewItem}
            disabled={saving || !newItemData.description_he || newItemData.quantity === 0}
            startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
            sx={{
              px: 3,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              boxShadow: '0 8px 20px rgba(16, 185, 129, 0.3)',
              fontWeight: 600,
            }}
          >
            {saving ? 'שומר...' : 'הוסף פריט'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  );
}
