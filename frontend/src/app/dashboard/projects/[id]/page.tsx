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
  Alert,
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
  Close as CloseIcon,
  Add as AddIcon,
  PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import ExtractionReview from '@/components/ExtractionReview';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';

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
  id?: number;  // NEW: for editing
  item_code: string;
  description_he: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  confidence: number;
  source_files?: number;
  source_filename?: string | null;  // NEW: source tracking
  source_layer?: string | null;  // NEW: source tracking
  user_notes?: string | null;  // NEW: user notes
  is_modified?: boolean;  // NEW: modification tracking
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
  const router = useRouter();
  const { showError, showConfirm } = useNotification();

  // Check if all files are PDFs (no CAD files)
  const isPdfOnlyProject = project?.plans?.length > 0 &&
    project.plans.every(plan => isPdfFile(plan.filename));

  const fetchProject = async () => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      setProject(response.data);

      const status = response.data.processing_status;

      // Start polling if processing or generating BOQ
      if (status === 'processing' || status === 'generating_boq') {
        setPolling(true);
      } else {
        setPolling(false);
      }

      // Fetch extraction data when extraction is done (for user review)
      if (status === 'extracted') {
        fetchExtractionData();
      }

      // Fetch BOQ and extraction data if completed
      if (status === 'completed') {
        fetchBOQ();
        fetchExtractionData();
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
      // Expand all chapters by default
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
    // Refresh project data - status will change to "generating_boq"
    fetchProject();
  };

  // Handle PDF-only project BOQ generation (no layer selection needed)
  const handleGeneratePdfBoq = async () => {
    try {
      setGeneratingPdfBoq(true);
      // Call the extraction-confirm endpoint with empty layer selection
      // This will trigger BOQ generation for PDF files
      await api.post(`/projects/${projectId}/extraction-confirm`, {
        selected_layer_ids: [],
        custom_area_m2: null,
      });
      // Refresh project data - status will change to "generating_boq"
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
    // Generate next item code for the chapter
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
      fetchBOQ(); // Refresh BOQ data
    } catch (error) {
      console.error('Failed to create item', error);
      showError('שגיאה ביצירת הפריט');
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'processing':
        return '#f59e0b';
      case 'extracted':
        return '#8b5cf6'; // Purple - waiting for user review
      case 'generating_boq':
        return '#06b6d4'; // Cyan - AI generating BOQ
      case 'failed':
        return '#ef4444';
      default:
        return '#64748b';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'הושלם';
      case 'processing':
        return 'מחלץ נתונים...';
      case 'extracted':
        return 'ממתין לבחירה';
      case 'generating_boq':
        return 'יוצר כתב כמויות...';
      case 'failed':
        return 'נכשל';
      default:
        return 'ממתין';
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
          <Skeleton variant="text" width={200} height={40} />
          <Skeleton variant="rounded" height={200} sx={{ mt: 2 }} />
          <Skeleton variant="rounded" height={400} sx={{ mt: 2 }} />
        </Box>
      </MainLayout>
    );
  }

  if (!project) {
    return (
      <MainLayout>
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h5" color="text.secondary">
            פרויקט לא נמצא
          </Typography>
          <Button onClick={() => router.push('/dashboard/projects')} sx={{ mt: 2 }}>
            חזרה לפרויקטים
          </Button>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/dashboard/projects')}>
          <BackIcon sx={{ transform: 'rotate(180deg)' }} />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={700}>
            {project.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {project.folder_path}
          </Typography>
        </Box>
        <Chip
          label={getStatusLabel(project.processing_status)}
          sx={{
            backgroundColor: alpha(getStatusColor(project.processing_status), 0.1),
            color: getStatusColor(project.processing_status),
            fontWeight: 600,
          }}
        />
        <IconButton
          onClick={() => setDeleteDialogOpen(true)}
          sx={{
            color: '#94a3b8',
            '&:hover': {
              color: '#ef4444',
              backgroundColor: alpha('#ef4444', 0.1),
            },
          }}
        >
          <DeleteIcon />
        </IconButton>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                סה״כ קבצים
              </Typography>
              <Typography variant="h3" fontWeight={700} color="primary">
                {project.total_files}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                עובדו
              </Typography>
              <Typography variant="h3" fontWeight={700} color="success.main">
                {project.processed_files}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                התקדמות
              </Typography>
              <Typography variant="h3" fontWeight={700}>
                {project.processing_progress}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                סה״כ פריטים בכתב כמויות
              </Typography>
              <Typography variant="h3" fontWeight={700} color="secondary.main">
                {boqData?.summary.total_items || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Processing Progress */}
      {project.processing_status === 'processing' && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
              מעבד קבצים...
            </Typography>
            <LinearProgress
              variant="determinate"
              value={project.processing_progress}
              sx={{
                height: 10,
                borderRadius: 5,
                backgroundColor: alpha('#6366f1', 0.1),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 5,
                  background: 'linear-gradient(90deg, #6366f1 0%, #4f46e5 100%)',
                },
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {project.processed_files} מתוך {project.total_files} קבצים
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Files List */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              קבצי DWG בפרויקט
            </Typography>
            {project.processing_status === 'pending' && (
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={handleStartProcessing}
              >
                התחל עיבוד
              </Button>
            )}
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>שם קובץ</TableCell>
                  <TableCell>סוג</TableCell>
                  <TableCell>סטטוס</TableCell>
                  <TableCell>התקדמות</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {project.plans.map((plan) => (
                  <TableRow key={plan.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FileIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                        {plan.filename}
                      </Box>
                    </TableCell>
                    <TableCell>{plan.file_type}</TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(plan.processing_status)}
                        size="small"
                        sx={{
                          backgroundColor: alpha(getStatusColor(plan.processing_status), 0.1),
                          color: getStatusColor(plan.processing_status),
                          fontWeight: 600,
                          fontSize: '0.7rem',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      {plan.processing_status === 'processing' ? (
                        <LinearProgress
                          variant="determinate"
                          value={plan.processing_progress}
                          sx={{ width: 100 }}
                        />
                      ) : (
                        `${plan.processing_progress}%`
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Extraction Review - Show when extraction complete and waiting for user selection */}
      {project.processing_status === 'extracted' && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            {isPdfOnlyProject ? (
              /* PDF-only projects - no layer selection needed */
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <PdfIcon sx={{ fontSize: 64, color: '#dc2626', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  קבצי PDF מוכנים ליצירת כתב כמויות
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
                  זוהו {project.plans.length} קבצי PDF בפרויקט.
                  לחץ על הכפתור למטה כדי ליצור כתב כמויות אוטומטי מהנתונים שחולצו.
                </Typography>
                <Alert severity="info" sx={{ mb: 3, maxWidth: 500, mx: 'auto', textAlign: 'right' }}>
                  <Typography variant="body2">
                    קבצי PDF אינם מכילים שכבות AutoCAD, לכן המערכת תיצור כתב כמויות ישירות מהנתונים שחולצו.
                  </Typography>
                </Alert>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGeneratePdfBoq}
                  disabled={generatingPdfBoq}
                  startIcon={generatingPdfBoq ? <CircularProgress size={20} color="inherit" /> : <PlayIcon />}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                    },
                  }}
                >
                  {generatingPdfBoq ? 'מייצר כתב כמויות...' : 'צור כתב כמויות'}
                </Button>
              </Box>
            ) : (
              /* CAD files - show layer selection */
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
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <CircularProgress size={28} sx={{ color: '#06b6d4' }} />
              <Typography variant="h6" fontWeight={600}>
                יוצר כתב כמויות...
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              מערכת ה-AI מעבדת את הנתונים ויוצרת כתב כמויות מפורט עם מחירי דקל.
              תהליך זה עשוי לקחת מספר דקות.
            </Typography>
            <LinearProgress
              sx={{
                height: 10,
                borderRadius: 5,
                backgroundColor: alpha('#06b6d4', 0.1),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 5,
                  background: 'linear-gradient(90deg, #06b6d4 0%, #0891b2 100%)',
                },
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Extraction Summary - Adapts to PDF vs CAD */}
      {project.processing_status === 'completed' && extractionData && (() => {
        // Check if all files are PDFs
        const isPdfProject = extractionData.files.every(f => f.filename.toLowerCase().endsWith('.pdf'));
        const hasCadFiles = extractionData.files.some(f =>
          f.filename.toLowerCase().endsWith('.dwg') || f.filename.toLowerCase().endsWith('.dxf')
        );

        return (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              {isPdfProject ? (
                <PdfIcon sx={{ color: '#ef4444', fontSize: 28 }} />
              ) : (
                <FolderIcon sx={{ color: '#10b981', fontSize: 28 }} />
              )}
              <Typography variant="h5" fontWeight={600}>
                {isPdfProject ? 'נתוני חילוץ מ-PDF' : 'נתוני חילוץ מ-AutoCAD'}
              </Typography>
            </Box>

            {/* Summary Stats - Different for PDF vs CAD */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              {isPdfProject ? (
                // PDF-specific stats
                <>
                  <Grid xs={6} sm={4} md={3}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#ef4444', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#ef4444' }}>
                        {extractionData.total_files}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        קבצי PDF
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={3}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#f59e0b', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#f59e0b' }}>
                        {extractionData.extraction_summary.total_text_entities.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        פריטים שנמצאו
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={3}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#10b981', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#10b981' }}>
                        Gemini
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        מנוע AI
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={3}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#6366f1', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} color="primary">
                        {extractionData.extraction_summary.total_area_m2 > 0
                          ? extractionData.extraction_summary.total_area_m2.toLocaleString('he-IL')
                          : '-'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        שטח כולל (מ״ר)
                      </Typography>
                    </Box>
                  </Grid>
                </>
              ) : (
                // CAD-specific stats
                <>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#6366f1', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} color="primary">
                        {extractionData.extraction_summary.total_area_m2.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        שטח כולל (מ״ר)
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#10b981', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#10b981' }}>
                        {extractionData.extraction_summary.total_blocks.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        בלוקים
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#f59e0b', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#f59e0b' }}>
                        {extractionData.extraction_summary.total_text_entities.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        טקסט
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#8b5cf6', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#8b5cf6' }}>
                        {extractionData.extraction_summary.total_layers.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        שכבות
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#ec4899', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#ec4899' }}>
                        {extractionData.extraction_summary.total_polylines.toLocaleString('he-IL')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        פוליליינים
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid xs={6} sm={4} md={2}>
                    <Box sx={{ p: 2, backgroundColor: alpha('#64748b', 0.05), borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} sx={{ color: '#64748b' }}>
                        {extractionData.total_files}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        קבצים
                      </Typography>
                    </Box>
                  </Grid>
                </>
              )}
            </Grid>

            {/* Per-file breakdown */}
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
              פירוט לפי קובץ
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: alpha('#6366f1', 0.02) }}>
                    <TableCell>שם קובץ</TableCell>
                    {isPdfProject ? (
                      // PDF columns
                      <>
                        <TableCell align="right">פריטים</TableCell>
                        <TableCell align="right">סוג תכנית</TableCell>
                        <TableCell align="right">שטח (מ״ר)</TableCell>
                      </>
                    ) : (
                      // CAD columns
                      <>
                        <TableCell align="right">שטח (מ״ר)</TableCell>
                        <TableCell align="right">בלוקים</TableCell>
                        <TableCell align="right">טקסט</TableCell>
                        <TableCell align="right">שכבות</TableCell>
                        <TableCell align="right">פוליליינים</TableCell>
                      </>
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {extractionData.files.map((file) => (
                    <TableRow key={file.plan_id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {file.filename.toLowerCase().endsWith('.pdf') ? (
                            <PdfIcon sx={{ fontSize: 18, color: '#ef4444' }} />
                          ) : (
                            <FileIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                          )}
                          {file.filename}
                        </Box>
                      </TableCell>
                      {isPdfProject ? (
                        // PDF data
                        <>
                          <TableCell align="right">
                            {(file as any).items_count?.toLocaleString('he-IL') ||
                              file.extraction_data?.items_count?.toLocaleString('he-IL') || '-'}
                          </TableCell>
                          <TableCell align="right">
                            {file.extraction_data?.plan_type || 'site_development'}
                          </TableCell>
                          <TableCell align="right">
                            {file.area_m2 && file.area_m2 > 0 ? file.area_m2.toLocaleString('he-IL') : '-'}
                          </TableCell>
                        </>
                      ) : (
                        // CAD data
                        <>
                          <TableCell align="right">
                            {file.area_m2?.toLocaleString('he-IL') || '-'}
                          </TableCell>
                          <TableCell align="right">
                            {file.extraction_data?.blocks_count?.toLocaleString('he-IL') || '-'}
                          </TableCell>
                          <TableCell align="right">
                            {file.extraction_data?.text_count?.toLocaleString('he-IL') || '-'}
                          </TableCell>
                          <TableCell align="right">
                            {file.extraction_data?.layers_count?.toLocaleString('he-IL') || '-'}
                          </TableCell>
                          <TableCell align="right">
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
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <ReportIcon sx={{ color: '#6366f1', fontSize: 28 }} />
                <Typography variant="h5" fontWeight={600}>
                  כתב כמויות מאוחד
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<PdfIcon />}
                  onClick={() => window.open(`http://localhost:7000/projects/${projectId}/boq/export/pdf`, '_blank')}
                  sx={{
                    background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%)',
                    },
                  }}
                >
                  ייצא ל-PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => window.open(`http://localhost:7000/projects/${projectId}/boq/export`, '_blank')}
                >
                  ייצא ל-Excel
                </Button>
              </Box>
            </Box>

            {boqLoading ? (
              <Box>
                <Skeleton variant="rounded" height={60} sx={{ mb: 2 }} />
                <Skeleton variant="rounded" height={200} />
              </Box>
            ) : boqData ? (
              <>
                {/* Warning message if BOQ is empty */}
                {boqData.warning && boqData.chapters.length === 0 && (
                  <Box
                    sx={{
                      p: 3,
                      mb: 2,
                      backgroundColor: alpha('#f59e0b', 0.1),
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: alpha('#f59e0b', 0.3),
                      textAlign: 'center',
                    }}
                  >
                    <Typography variant="h6" color="warning.main" gutterBottom>
                      אין נתוני כתב כמויות
                    </Typography>
                    <Typography color="text.secondary">
                      {boqData.warning}
                    </Typography>
                  </Box>
                )}
                {/* Chapters */}
                {boqData.chapters.map((chapter) => (
                  <Box key={chapter.chapter_code} sx={{ mb: 2 }}>
                    <Box
                      onClick={() => toggleChapter(chapter.chapter_code)}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 2,
                        backgroundColor: alpha('#6366f1', 0.05),
                        borderRadius: 2,
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: alpha('#6366f1', 0.1),
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="h6" fontWeight={600}>
                          פרק {chapter.chapter_code}: {chapter.chapter_name_he}
                        </Typography>
                        <Chip
                          label={`${chapter.items.length} פריטים`}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="h6" fontWeight={600} color="primary">
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
                              backgroundColor: alpha('#10b981', 0.1),
                              color: '#10b981',
                              '&:hover': {
                                backgroundColor: alpha('#10b981', 0.2),
                              },
                            }}
                          >
                            <AddIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {expandedChapters.includes(chapter.chapter_code) ? (
                          <CollapseIcon />
                        ) : (
                          <ExpandIcon />
                        )}
                      </Box>
                    </Box>

                    <Collapse in={expandedChapters.includes(chapter.chapter_code)}>
                      <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ backgroundColor: alpha('#6366f1', 0.02) }}>
                              <TableCell>קוד</TableCell>
                              <TableCell>תיאור</TableCell>
                              <TableCell align="right">כמות</TableCell>
                              <TableCell>יחידה</TableCell>
                              <TableCell align="right">מחיר יח׳</TableCell>
                              <TableCell align="right">סה״כ</TableCell>
                              <TableCell>קובץ מקור</TableCell>
                              <TableCell>שכבה</TableCell>
                              <TableCell>הערות</TableCell>
                              <TableCell align="center">אמינות</TableCell>
                              <TableCell align="center">פעולות</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {chapter.items.map((item, idx) => {
                              const isEditing = editingItemId === item.id;
                              return (
                                <TableRow
                                  key={idx}
                                  sx={{
                                    backgroundColor: isEditing ? alpha('#6366f1', 0.03) : 'transparent',
                                    ...(item.is_modified && {
                                      borderLeft: `4px solid ${alpha('#f59e0b', 0.7)}`,
                                    }),
                                  }}
                                >
                                  <TableCell sx={{ fontWeight: 600 }}>{item.item_code}</TableCell>
                                  <TableCell sx={{ maxWidth: 250 }}>{item.description_he}</TableCell>
                                  <TableCell align="right">
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        type="number"
                                        value={editedValues.quantity}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, quantity: parseFloat(e.target.value) })
                                        }
                                        sx={{ width: 80 }}
                                      />
                                    ) : (
                                      item.quantity.toLocaleString('he-IL')
                                    )}
                                  </TableCell>
                                  <TableCell>{item.unit}</TableCell>
                                  <TableCell align="right">
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        type="number"
                                        value={editedValues.unit_price}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, unit_price: parseFloat(e.target.value) })
                                        }
                                        sx={{ width: 90 }}
                                      />
                                    ) : (
                                      `${item.unit_price.toLocaleString('he-IL')} ₪`
                                    )}
                                  </TableCell>
                                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                                    {item.total_price.toLocaleString('he-IL')} ₪
                                  </TableCell>
                                  <TableCell sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>
                                    {item.source_filename || '-'}
                                  </TableCell>
                                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem', maxWidth: 150 }}>
                                    <Tooltip title={item.source_layer || '-'}>
                                      <span>
                                        {item.source_layer
                                          ? item.source_layer.length > 25
                                            ? `${item.source_layer.substring(0, 25)}...`
                                            : item.source_layer
                                          : '-'}
                                      </span>
                                    </Tooltip>
                                  </TableCell>
                                  <TableCell sx={{ minWidth: 150 }}>
                                    {isEditing ? (
                                      <TextField
                                        size="small"
                                        multiline
                                        rows={1}
                                        value={editedValues.user_notes}
                                        onChange={(e) =>
                                          setEditedValues({ ...editedValues, user_notes: e.target.value })
                                        }
                                        placeholder="הוסף הערה..."
                                        fullWidth
                                      />
                                    ) : (
                                      <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                                        {item.user_notes || '-'}
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell align="center">
                                    <Chip
                                      label={`${Math.round(item.confidence * 100)}%`}
                                      size="small"
                                      sx={{
                                        backgroundColor: alpha(getConfidenceColor(item.confidence), 0.1),
                                        color: getConfidenceColor(item.confidence),
                                        fontWeight: 600,
                                        fontSize: '0.7rem',
                                      }}
                                    />
                                  </TableCell>
                                  <TableCell align="center">
                                    {isEditing ? (
                                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                                        <Tooltip title="שמור">
                                          <IconButton
                                            size="small"
                                            color="success"
                                            onClick={() => item.id && handleSaveEdit(item.id)}
                                          >
                                            <SaveIcon fontSize="small" />
                                          </IconButton>
                                        </Tooltip>
                                        <Tooltip title="בטל">
                                          <IconButton size="small" color="default" onClick={handleCancelEdit}>
                                            <CancelIcon fontSize="small" />
                                          </IconButton>
                                        </Tooltip>
                                      </Box>
                                    ) : (
                                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                                        <Tooltip title="ערוך">
                                          <IconButton
                                            size="small"
                                            color="primary"
                                            onClick={() => handleEditItem(item)}
                                          >
                                            <EditIcon fontSize="small" />
                                          </IconButton>
                                        </Tooltip>
                                        <Tooltip title="מחק">
                                          <IconButton
                                            size="small"
                                            color="error"
                                            onClick={() => item.id && handleDeleteItem(item.id)}
                                          >
                                            <DeleteIcon fontSize="small" />
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

                <Divider sx={{ my: 3 }} />

                {/* Summary */}
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Box sx={{ width: 300 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography>סיכום ביניים:</Typography>
                      <Typography fontWeight={600}>
                        {boqData.summary.subtotal.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography>מע״מ ({(boqData.summary.vat_rate * 100).toFixed(0)}%):</Typography>
                      <Typography fontWeight={600}>
                        {boqData.summary.vat_amount.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="h6" fontWeight={700}>
                        סה״כ:
                      </Typography>
                      <Typography variant="h6" fontWeight={700} color="primary">
                        {boqData.summary.grand_total.toLocaleString('he-IL')} ₪
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </>
            ) : (
              <Typography color="text.secondary">לא נמצאו נתונים</Typography>
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
          {project && (
            <Box sx={{ p: 2, bgcolor: alpha('#ef4444', 0.05), borderRadius: 1 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {project.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {project.total_files} קבצים יימחקו
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
            onClick={handleDeleteProject}
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} color="inherit" /> : <DeleteIcon />}
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
      >
        <DialogTitle sx={{ color: '#10b981', borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AddIcon />
            הוסף פריט חדש
            {selectedChapter && (
              <Chip
                label={`פרק ${selectedChapter.chapter_code}: ${selectedChapter.chapter_name_he}`}
                size="small"
                sx={{ backgroundColor: alpha('#10b981', 0.1), color: '#10b981' }}
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 4, pb: 2 }}>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6}>
              <TextField
                label="קוד פריט"
                fullWidth
                value={newItemData.item_code}
                onChange={(e) => setNewItemData({ ...newItemData, item_code: e.target.value })}
                disabled={saving}
              />
            </Grid>
            <Grid xs={12} sm={6}>
              <TextField
                label="יחידה"
                fullWidth
                value={newItemData.unit}
                onChange={(e) => setNewItemData({ ...newItemData, unit: e.target.value })}
                disabled={saving}
              />
            </Grid>
            <Grid xs={12}>
              <TextField
                label="תיאור"
                fullWidth
                multiline
                rows={2}
                value={newItemData.description_he}
                onChange={(e) => setNewItemData({ ...newItemData, description_he: e.target.value })}
                disabled={saving}
                required
              />
            </Grid>
            <Grid xs={12} sm={4}>
              <TextField
                label="כמות"
                type="number"
                fullWidth
                value={newItemData.quantity}
                onChange={(e) => setNewItemData({ ...newItemData, quantity: parseFloat(e.target.value) || 0 })}
                disabled={saving}
                required
              />
            </Grid>
            <Grid xs={12} sm={4}>
              <TextField
                label="מחיר יחידה (₪)"
                type="number"
                fullWidth
                value={newItemData.unit_price}
                onChange={(e) => setNewItemData({ ...newItemData, unit_price: parseFloat(e.target.value) || 0 })}
                disabled={saving}
                required
              />
            </Grid>
            <Grid xs={12} sm={4}>
              <TextField
                label="סה״כ (₪)"
                fullWidth
                value={(newItemData.quantity * newItemData.unit_price).toLocaleString('he-IL')}
                disabled
                sx={{ '& .MuiInputBase-input': { fontWeight: 600, color: 'primary.main' } }}
              />
            </Grid>
            <Grid xs={12}>
              <TextField
                label="הערות"
                fullWidth
                multiline
                rows={2}
                value={newItemData.user_notes}
                onChange={(e) => setNewItemData({ ...newItemData, user_notes: e.target.value })}
                disabled={saving}
                placeholder="הערות נוספות (אופציונלי)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, borderTop: 1, borderColor: 'divider' }}>
          <Button
            onClick={handleCloseAddItemDialog}
            disabled={saving}
            color="inherit"
          >
            ביטול
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateNewItem}
            disabled={saving || !newItemData.description_he || newItemData.quantity === 0}
            startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
            sx={{
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              px: 3,
              py: 1,
              fontSize: '1rem',
              fontWeight: 600,
              '&:hover': {
                background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              },
            }}
          >
            {saving ? 'שומר...' : 'הוסף פריט'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  );
}
