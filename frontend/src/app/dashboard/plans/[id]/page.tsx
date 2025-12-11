'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  alpha,
  Collapse,
  Button,
  Grid,
  TextField,
} from '@mui/material';
import {
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ArrowBack as BackIcon,
  Receipt as ReceiptIcon,
  Layers as LayersIcon,
  AttachMoney as MoneyIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';

interface BOQItem {
  id?: number;  // NEW - item ID for editing
  item_code: string;
  dekel_code: string | null;
  description_he: string;
  description_en: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  confidence: number;
  notes: string | null;
  source_filename?: string | null;  // NEW - source file tracking
  source_layer?: string | null;  // NEW - source layer tracking
  user_notes?: string | null;  // NEW - user-added notes
  is_modified?: boolean;  // NEW - modification flag
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
  project_id?: number;  // NEW - for editing BOQ items
  filename: string;
  date: string;
  chapters: BOQChapter[];
  summary: {
    subtotal: number;
    vat_rate: number;
    vat_amount: number;
    grand_total: number;
  };
  notes: string[];
  metadata: {
    extraction_method: string;
    processing_time_seconds: number;
  };
}

interface ProcessingStatus {
  status: string;
  progress: number;
}

function SummaryCard({ title, value, icon, color, delay = 0 }: {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: string;
  delay?: number;
}) {
  return (
    <Box
      sx={{
        animation: 'fadeInUp 0.4s ease-out forwards',
        animationDelay: `${delay}s`,
        opacity: 0,
        '@keyframes fadeInUp': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Card
        sx={{
          background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
          border: `1px solid ${alpha(color, 0.2)}`,
        }}
      >
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                backgroundColor: alpha(color, 0.15),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                {title}
              </Typography>
              <Typography variant="h5" fontWeight={700} sx={{ color }}>
                {value}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

function ChapterSection({ chapter, index, projectId, onUpdate, showError, showConfirm }: {
  chapter: BOQChapter;
  index: number;
  projectId: string;
  onUpdate: () => void;
  showError: (message: string) => void;
  showConfirm: (message: string) => Promise<boolean>;
}) {
  const [expanded, setExpanded] = useState(true);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editedValues, setEditedValues] = useState<{
    quantity: number;
    unit_price: number;
    user_notes: string;
  }>({ quantity: 0, unit_price: 0, user_notes: '' });
  const [saving, setSaving] = useState(false);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckIcon sx={{ fontSize: 16 }} />;
    if (confidence >= 0.6) return <WarningIcon sx={{ fontSize: 16 }} />;
    return <ErrorIcon sx={{ fontSize: 16 }} />;
  };

  const handleEdit = (item: BOQItem) => {
    setEditingItemId(item.id!);
    setEditedValues({
      quantity: item.quantity,
      unit_price: item.unit_price,
      user_notes: item.user_notes || '',
    });
  };

  const handleCancel = () => {
    setEditingItemId(null);
    setEditedValues({ quantity: 0, unit_price: 0, user_notes: '' });
  };

  const handleSave = async (itemId: number) => {
    setSaving(true);
    try {
      await api.patch(`/projects/${projectId}/boq/items/${itemId}`, editedValues);
      setEditingItemId(null);
      onUpdate(); // Refresh BOQ data
    } catch (error) {
      console.error('Failed to update BOQ item:', error);
      showError('שגיאה בשמירת השינויים');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (itemId: number) => {
    const confirmed = await showConfirm('האם אתה בטוח שברצונך למחוק פריט זה?');
    if (!confirmed) return;

    setSaving(true);
    try {
      await api.delete(`/projects/${projectId}/boq/items/${itemId}`);
      onUpdate(); // Refresh BOQ data
    } catch (error) {
      console.error('Failed to delete BOQ item:', error);
      showError('שגיאה במחיקת הפריט');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box
      sx={{
        animation: 'fadeInUp 0.4s ease-out forwards',
        animationDelay: `${index * 0.1}s`,
        opacity: 0,
        '@keyframes fadeInUp': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Card sx={{ mb: 3, overflow: 'hidden' }}>
        {/* Chapter Header */}
        <Box
          onClick={() => setExpanded(!expanded)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2.5,
            cursor: 'pointer',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(99, 102, 241, 0.02) 100%)',
            borderBottom: expanded ? '1px solid' : 'none',
            borderColor: 'divider',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(99, 102, 241, 0.04) 100%)',
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 700,
                fontSize: '0.875rem',
              }}
            >
              {chapter.chapter_code}
            </Box>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {chapter.chapter_name_he}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {chapter.chapter_name_en} - {chapter.items.length} פריטים
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" fontWeight={700} color="primary">
              {chapter.chapter_total.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
            </Typography>
            <IconButton size="small">
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        {/* Chapter Items */}
        <Collapse in={expanded}>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, width: '7%' }}>קוד</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '20%' }}>תיאור</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '7%' }}>כמות</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '5%' }}>יחידה</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '8%' }}>מחיר</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '8%' }}>סה"כ</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '10%' }}>קובץ מקור</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '8%' }}>שכבה</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '12%' }}>הערות</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '5%' }}>ביטחון</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '10%' }}>פעולות</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {chapter.items.map((item, itemIndex) => (
                  <TableRow
                    key={itemIndex}
                    sx={{
                      '&:hover': {
                        backgroundColor: alpha('#6366f1', 0.04),
                      },
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="body2" fontWeight={600}>
                          {item.item_code}
                        </Typography>
                        {item.dekel_code && (
                          <Typography variant="caption" color="text.secondary">
                            דקל: {item.dekel_code}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Tooltip title={item.description_en} arrow placement="top">
                        <Box>
                          <Typography variant="body2">
                            {item.description_he}
                          </Typography>
                          {item.notes && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                              {item.notes}
                            </Typography>
                          )}
                        </Box>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="center">
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          type="number"
                          value={editedValues.quantity}
                          onChange={(e) => setEditedValues({ ...editedValues, quantity: parseFloat(e.target.value) || 0 })}
                          sx={{ width: 80 }}
                        />
                      ) : (
                        <Typography variant="body2" fontWeight={500}>
                          {item.quantity.toLocaleString('he-IL', { maximumFractionDigits: 2 })}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={item.unit}
                        size="small"
                        sx={{
                          backgroundColor: alpha('#64748b', 0.1),
                          fontWeight: 500,
                          fontSize: '0.75rem',
                        }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          type="number"
                          value={editedValues.unit_price}
                          onChange={(e) => setEditedValues({ ...editedValues, unit_price: parseFloat(e.target.value) || 0 })}
                          sx={{ width: 90 }}
                        />
                      ) : (
                        <Typography variant="body2">
                          {item.unit_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" fontWeight={600} color="primary">
                        {item.total_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="caption" color="text.secondary">
                        {item.source_filename || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        {item.source_layer || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          multiline
                          value={editedValues.user_notes}
                          onChange={(e) => setEditedValues({ ...editedValues, user_notes: e.target.value })}
                          placeholder="הוסף הערה..."
                          fullWidth
                          sx={{ minWidth: 120 }}
                        />
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          {item.user_notes || item.notes || '-'}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        icon={getConfidenceIcon(item.confidence)}
                        label={`${(item.confidence * 100).toFixed(0)}%`}
                        size="small"
                        sx={{
                          backgroundColor: alpha(getConfidenceColor(item.confidence), 0.1),
                          color: getConfidenceColor(item.confidence),
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          '& .MuiChip-icon': {
                            color: getConfidenceColor(item.confidence),
                          },
                        }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {editingItemId === item.id ? (
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="שמור">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleSave(item.id!)}
                              disabled={saving}
                            >
                              <SaveIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="ביטול">
                            <IconButton
                              size="small"
                              onClick={handleCancel}
                              disabled={saving}
                            >
                              <CancelIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      ) : (
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="ערוך">
                            <IconButton
                              size="small"
                              onClick={() => handleEdit(item)}
                              disabled={saving}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="מחק">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDelete(item.id!)}
                              disabled={saving}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Collapse>
      </Card>
    </Box>
  );
}

export default function PlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const planId = params.id;
  const { showError, showConfirm } = useNotification();

  const [boqData, setBoqData] = useState<BOQData | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<ProcessingStatus>({ status: 'pending', progress: 0 });
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await api.get(`/plans/${planId}/status`);
      setStatus(response.data);

      if (response.data.status === 'completed') {
        await fetchBOQData();
      } else if (response.data.status === 'failed') {
        setError('העיבוד נכשל. אנא נסה להעלות את הקובץ שוב.');
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to fetch status', err);
    }
  };

  const fetchBOQData = async () => {
    try {
      const response = await api.get(`/plans/${planId}/boq`);
      setBoqData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch BOQ data', err);
      // Fallback to quantities endpoint
      try {
        const materialsResponse = await api.get(`/plans/${planId}/quantities`);
        setBoqData({
          project_name: 'פרויקט',
          filename: '',
          date: new Date().toISOString(),
          chapters: [{
            chapter_code: '01',
            chapter_name_he: 'חומרים',
            chapter_name_en: 'Materials',
            items: materialsResponse.data.map((m: any, i: number) => ({
              item_code: `01.${String(i + 1).padStart(2, '0')}`,
              dekel_code: null,
              description_he: m.material_name,
              description_en: m.material_name,
              quantity: m.quantity,
              unit: m.unit,
              unit_price: 0,
              total_price: 0,
              confidence: m.confidence_score,
              notes: null,
            })),
            chapter_total: 0,
          }],
          summary: {
            subtotal: 0,
            vat_rate: 0.17,
            vat_amount: 0,
            grand_total: 0,
          },
          notes: [],
          metadata: {
            extraction_method: 'legacy',
            processing_time_seconds: 0,
          },
        });
        setLoading(false);
      } catch (fallbackErr) {
        setError('לא ניתן לטעון את נתוני כתב הכמויות');
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchStatus();

    const interval = setInterval(() => {
      if (status.status !== 'completed' && status.status !== 'failed') {
        fetchStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [planId, status.status]);

  const handleExportExcel = async () => {
    try {
      const response = await api.get(`/export/plans/${planId}/excel`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BOQ_${planId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export Excel', err);
    }
  };

  // Processing state
  if (status.status === 'pending' || status.status === 'processing') {
    return (
      <MainLayout>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
          }}
        >
          <Box
            sx={{
              animation: 'scaleIn 0.4s ease-out forwards',
              '@keyframes scaleIn': {
                '0%': { opacity: 0, transform: 'scale(0.9)' },
                '100%': { opacity: 1, transform: 'scale(1)' },
              },
            }}
          >
            <Box
              sx={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 4,
              }}
            >
              <CircularProgress size={60} thickness={4} />
            </Box>
          </Box>

          <Typography variant="h5" fontWeight={600} gutterBottom>
            {status.status === 'pending' ? 'ממתין לעיבוד...' : 'מעבד את הקובץ...'}
          </Typography>

          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            {status.status === 'processing'
              ? 'מנתח את התוכנית ומייצר כתב כמויות'
              : 'הקובץ בתור לעיבוד'
            }
          </Typography>

          <Box sx={{ width: 400, maxWidth: '90%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                התקדמות
              </Typography>
              <Typography variant="body2" fontWeight={600} color="primary">
                {status.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={status.progress}
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>
        </Box>
      </MainLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <MainLayout>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700}>כתב כמויות</Typography>
          <Typography variant="body2" color="text.secondary">שגיאה בעיבוד</Typography>
        </Box>
        <Alert
          severity="error"
          sx={{ borderRadius: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => router.push('/dashboard')}>
              חזרה ללוח הבקרה
            </Button>
          }
        >
          {error}
        </Alert>
      </MainLayout>
    );
  }

  // Loading state
  if (loading || !boqData) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </MainLayout>
    );
  }

  // Results view
  return (
    <MainLayout>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton
            onClick={() => router.push('/dashboard')}
            sx={{
              backgroundColor: alpha('#64748b', 0.1),
              '&:hover': { backgroundColor: alpha('#64748b', 0.2) },
            }}
          >
            <BackIcon sx={{ transform: 'rotate(180deg)' }} />
          </IconButton>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              כתב כמויות
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {boqData.project_name} - {boqData.filename}
            </Typography>
          </Box>
        </Box>

        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExportExcel}
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.4)',
            '&:hover': {
              boxShadow: '0 6px 20px 0 rgba(99, 102, 241, 0.5)',
            },
          }}
        >
          ייצוא לאקסל
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid xs={12} sm={6} md={3}>
          <SummaryCard
            title="סה״כ לפני מע״מ"
            value={`${boqData.summary.subtotal.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח`}
            icon={<ReceiptIcon sx={{ fontSize: 24, color: '#6366f1' }} />}
            color="#6366f1"
            delay={0}
          />
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <SummaryCard
            title={`מע״מ (${(boqData.summary.vat_rate * 100).toFixed(0)}%)`}
            value={`${boqData.summary.vat_amount.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח`}
            icon={<MoneyIcon sx={{ fontSize: 24, color: '#f59e0b' }} />}
            color="#f59e0b"
            delay={0.1}
          />
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <SummaryCard
            title="סה״כ כולל מע״מ"
            value={`${boqData.summary.grand_total.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח`}
            icon={<MoneyIcon sx={{ fontSize: 24, color: '#10b981' }} />}
            color="#10b981"
            delay={0.2}
          />
        </Grid>
        <Grid xs={12} sm={6} md={3}>
          <SummaryCard
            title="פרקים"
            value={boqData.chapters.length.toString()}
            icon={<LayersIcon sx={{ fontSize: 24, color: '#06b6d4' }} />}
            color="#06b6d4"
            delay={0.3}
          />
        </Grid>
      </Grid>

      {/* Chapters */}
      {boqData.chapters.map((chapter, index) => (
        <ChapterSection
          key={chapter.chapter_code}
          chapter={chapter}
          index={index}
          projectId={boqData.project_id?.toString() || ''}
          onUpdate={fetchBOQData}
          showError={showError}
          showConfirm={showConfirm}
        />
      ))}

      {/* Notes */}
      {boqData.notes && boqData.notes.length > 0 && (
        <Box
          sx={{
            animation: 'fadeInUp 0.4s ease-out forwards',
            animationDelay: '0.5s',
            opacity: 0,
            '@keyframes fadeInUp': {
              '0%': { opacity: 0, transform: 'translateY(20px)' },
              '100%': { opacity: 1, transform: 'translateY(0)' },
            },
          }}
        >
          <Card sx={{ mt: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                הערות
              </Typography>
              {boqData.notes.map((note, index) => (
                <Typography key={index} variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {note}
                </Typography>
              ))}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Metadata */}
      <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          שיטת חילוץ: {boqData.metadata.extraction_method} |
          זמן עיבוד: {boqData.metadata.processing_time_seconds.toFixed(2)} שניות |
          תאריך: {new Date(boqData.date).toLocaleDateString('he-IL')}
        </Typography>
      </Box>
    </MainLayout>
  );
}
