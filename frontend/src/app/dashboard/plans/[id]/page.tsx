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
  id?: number;
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
  project_id?: number;
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
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha(color, 0.2)}`,
          borderRadius: '16px',
          boxShadow: `0 8px 32px ${alpha(color, 0.15)}`,
        }}
      >
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 52,
                height: 52,
                borderRadius: '14px',
                background: `linear-gradient(135deg, ${alpha(color, 0.2)} 0%, ${alpha(color, 0.1)} 100%)`,
                border: `1px solid ${alpha(color, 0.3)}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {icon}
            </Box>
            <Box>
              <Typography
                variant="body2"
                sx={{ color: '#64748b', fontSize: '0.85rem' }}
              >
                {title}
              </Typography>
              <Typography
                variant="h5"
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
      onUpdate();
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
      onUpdate();
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
      <Card
        sx={{
          mb: 3,
          overflow: 'hidden',
          backgroundColor: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(148, 163, 184, 0.1)',
          borderRadius: '16px',
          boxShadow: 'none',
        }}
      >
        {/* Chapter Header */}
        <Box
          onClick={() => setExpanded(!expanded)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2.5,
            cursor: 'pointer',
            background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(14, 165, 233, 0.02) 100%)',
            borderBottom: expanded ? '1px solid rgba(148, 163, 184, 0.1)' : 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(14, 165, 233, 0.04) 100%)',
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 700,
                fontSize: '0.875rem',
                boxShadow: '0 4px 16px rgba(14, 165, 233, 0.3)',
              }}
            >
              {chapter.chapter_code}
            </Box>
            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: '#f1f5f9',
                  fontSize: '1rem',
                }}
              >
                {chapter.chapter_name_he}
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748b' }}>
                {chapter.chapter_name_en} - {chapter.items.length} פריטים
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                color: '#0ea5e9',
                fontSize: '1rem',
              }}
            >
              {chapter.chapter_total.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
            </Typography>
            <IconButton
              size="small"
              sx={{ color: '#64748b' }}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        {/* Chapter Items */}
        <Collapse in={expanded}>
          <TableContainer
            sx={{
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
            }}
          >
            <Table size="small">
              <TableHead>
                <TableRow>
                  {[
                    { label: 'קוד', width: '7%' },
                    { label: 'תיאור', width: '20%' },
                    { label: 'כמות', width: '7%', align: 'center' as const },
                    { label: 'יחידה', width: '5%', align: 'center' as const },
                    { label: 'מחיר', width: '8%', align: 'center' as const },
                    { label: 'סה"כ', width: '8%', align: 'center' as const },
                    { label: 'קובץ מקור', width: '10%', align: 'center' as const },
                    { label: 'שכבה', width: '8%', align: 'center' as const },
                    { label: 'הערות', width: '12%' },
                    { label: 'ביטחון', width: '5%', align: 'center' as const },
                    { label: 'פעולות', width: '10%', align: 'center' as const },
                  ].map((col) => (
                    <TableCell
                      key={col.label}
                      align={col.align}
                      sx={{
                        fontWeight: 600,
                        width: col.width,
                        color: '#64748b',
                        fontSize: '0.75rem',
                        borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                        backgroundColor: 'rgba(14, 165, 233, 0.03)',
                      }}
                    >
                      {col.label}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {chapter.items.map((item, itemIndex) => (
                  <TableRow
                    key={itemIndex}
                    sx={{
                      '&:hover': {
                        backgroundColor: 'rgba(14, 165, 233, 0.05)',
                      },
                    }}
                  >
                    <TableCell
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: 600, color: '#f1f5f9' }}
                        >
                          {item.item_code}
                        </Typography>
                        {item.dekel_code && (
                          <Typography variant="caption" sx={{ color: '#64748b' }}>
                            דקל: {item.dekel_code}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Tooltip title={item.description_en} arrow placement="top">
                        <Box>
                          <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                            {item.description_he}
                          </Typography>
                          {item.notes && (
                            <Typography
                              variant="caption"
                              sx={{ color: '#64748b', display: 'block', mt: 0.5 }}
                            >
                              {item.notes}
                            </Typography>
                          )}
                        </Box>
                      </Tooltip>
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          type="number"
                          value={editedValues.quantity}
                          onChange={(e) => setEditedValues({ ...editedValues, quantity: parseFloat(e.target.value) || 0 })}
                          sx={{
                            width: 80,
                            '& .MuiOutlinedInput-root': {
                              backgroundColor: 'rgba(15, 23, 42, 0.8)',
                              color: '#f1f5f9',
                              '& fieldset': {
                                borderColor: 'rgba(14, 165, 233, 0.3)',
                              },
                            },
                          }}
                        />
                      ) : (
                        <Typography variant="body2" sx={{ fontWeight: 500, color: '#f1f5f9' }}>
                          {item.quantity.toLocaleString('he-IL', { maximumFractionDigits: 2 })}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Chip
                        label={item.unit}
                        size="small"
                        sx={{
                          backgroundColor: 'rgba(148, 163, 184, 0.1)',
                          color: '#94a3b8',
                          border: '1px solid rgba(148, 163, 184, 0.2)',
                          fontWeight: 500,
                          fontSize: '0.75rem',
                        }}
                      />
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          type="number"
                          value={editedValues.unit_price}
                          onChange={(e) => setEditedValues({ ...editedValues, unit_price: parseFloat(e.target.value) || 0 })}
                          sx={{
                            width: 90,
                            '& .MuiOutlinedInput-root': {
                              backgroundColor: 'rgba(15, 23, 42, 0.8)',
                              color: '#f1f5f9',
                              '& fieldset': {
                                borderColor: 'rgba(14, 165, 233, 0.3)',
                              },
                            },
                          }}
                        />
                      ) : (
                        <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                          {item.unit_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#0ea5e9' }}>
                        {item.total_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} ש"ח
                      </Typography>
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Typography variant="caption" sx={{ color: '#64748b' }}>
                        {item.source_filename || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{ color: '#64748b', fontFamily: 'monospace' }}
                      >
                        {item.source_layer || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      {editingItemId === item.id ? (
                        <TextField
                          size="small"
                          multiline
                          value={editedValues.user_notes}
                          onChange={(e) => setEditedValues({ ...editedValues, user_notes: e.target.value })}
                          placeholder="הוסף הערה..."
                          fullWidth
                          sx={{
                            minWidth: 120,
                            '& .MuiOutlinedInput-root': {
                              backgroundColor: 'rgba(15, 23, 42, 0.8)',
                              color: '#f1f5f9',
                              '& fieldset': {
                                borderColor: 'rgba(14, 165, 233, 0.3)',
                              },
                            },
                          }}
                        />
                      ) : (
                        <Typography variant="caption" sx={{ color: '#64748b' }}>
                          {item.user_notes || item.notes || '-'}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      <Chip
                        icon={getConfidenceIcon(item.confidence)}
                        label={`${(item.confidence * 100).toFixed(0)}%`}
                        size="small"
                        sx={{
                          backgroundColor: alpha(getConfidenceColor(item.confidence), 0.15),
                          color: getConfidenceColor(item.confidence),
                          border: `1px solid ${alpha(getConfidenceColor(item.confidence), 0.3)}`,
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          '& .MuiChip-icon': {
                            color: getConfidenceColor(item.confidence),
                          },
                        }}
                      />
                    </TableCell>
                    <TableCell
                      align="center"
                      sx={{
                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                      }}
                    >
                      {editingItemId === item.id ? (
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="שמור">
                            <IconButton
                              size="small"
                              onClick={() => handleSave(item.id!)}
                              disabled={saving}
                              sx={{
                                color: '#0ea5e9',
                                '&:hover': {
                                  backgroundColor: 'rgba(14, 165, 233, 0.1)',
                                },
                              }}
                            >
                              <SaveIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="ביטול">
                            <IconButton
                              size="small"
                              onClick={handleCancel}
                              disabled={saving}
                              sx={{
                                color: '#64748b',
                                '&:hover': {
                                  backgroundColor: 'rgba(148, 163, 184, 0.1)',
                                },
                              }}
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
                              sx={{
                                color: '#64748b',
                                '&:hover': {
                                  backgroundColor: 'rgba(14, 165, 233, 0.1)',
                                  color: '#0ea5e9',
                                },
                              }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="מחק">
                            <IconButton
                              size="small"
                              onClick={() => handleDelete(item.id!)}
                              disabled={saving}
                              sx={{
                                color: '#64748b',
                                '&:hover': {
                                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                  color: '#ef4444',
                                },
                              }}
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
                background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(6, 182, 212, 0.1) 100%)',
                border: '1px solid rgba(14, 165, 233, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 4,
              }}
            >
              <CircularProgress
                size={60}
                thickness={4}
                sx={{
                  color: '#0ea5e9',
                }}
              />
            </Box>
          </Box>

          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: '#f1f5f9',
              mb: 1,
            }}
          >
            {status.status === 'pending' ? 'ממתין לעיבוד...' : 'מעבד את הקובץ...'}
          </Typography>

          <Typography
            variant="body1"
            sx={{ color: '#64748b', mb: 4 }}
          >
            {status.status === 'processing'
              ? 'מנתח את התוכנית ומייצר כתב כמויות'
              : 'הקובץ בתור לעיבוד'
            }
          </Typography>

          <Box sx={{ width: 400, maxWidth: '90%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" sx={{ color: '#64748b' }}>
                התקדמות
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, color: '#0ea5e9' }}>
                {status.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={status.progress}
              sx={{
                height: 10,
                borderRadius: 5,
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 5,
                  background: 'linear-gradient(90deg, #0ea5e9, #06b6d4)',
                },
              }}
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
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#f1f5f9' }}>
            כתב כמויות
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b' }}>
            שגיאה בעיבוד
          </Typography>
        </Box>
        <Alert
          severity="error"
          sx={{
            borderRadius: '16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            '& .MuiAlert-icon': {
              color: '#ef4444',
            },
            '& .MuiAlert-message': {
              color: '#f1f5f9',
            },
          }}
          action={
            <Button
              size="small"
              onClick={() => router.push('/dashboard')}
              sx={{
                color: '#f1f5f9',
                '&:hover': {
                  backgroundColor: 'rgba(148, 163, 184, 0.1)',
                },
              }}
            >
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
          <CircularProgress sx={{ color: '#0ea5e9' }} />
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
              width: 44,
              height: 44,
              backgroundColor: 'rgba(148, 163, 184, 0.1)',
              border: '1px solid rgba(148, 163, 184, 0.2)',
              transition: 'all 0.2s ease',
              '&:hover': {
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                borderColor: 'rgba(14, 165, 233, 0.3)',
              },
            }}
          >
            <BackIcon sx={{ transform: 'rotate(180deg)', color: '#64748b' }} />
          </IconButton>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#f1f5f9' }}>
              כתב כמויות
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748b' }}>
              {boqData.project_name} - {boqData.filename}
            </Typography>
          </Box>
        </Box>

        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExportExcel}
          sx={{
            px: 3,
            py: 1.5,
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
            boxShadow: '0 8px 32px rgba(14, 165, 233, 0.4)',
            textTransform: 'none',
            fontWeight: 700,
            '&:hover': {
              boxShadow: '0 12px 40px rgba(14, 165, 233, 0.5)',
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
            icon={<ReceiptIcon sx={{ fontSize: 24, color: '#0ea5e9' }} />}
            color="#0ea5e9"
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
            icon={<LayersIcon sx={{ fontSize: 24, color: '#8b5cf6' }} />}
            color="#8b5cf6"
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
          <Card
            sx={{
              mt: 3,
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(148, 163, 184, 0.1)',
              borderRadius: '16px',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: '#f1f5f9',
                  mb: 2,
                }}
              >
                הערות
              </Typography>
              {boqData.notes.map((note, index) => (
                <Typography
                  key={index}
                  variant="body2"
                  sx={{ color: '#94a3b8', mb: 1 }}
                >
                  {note}
                </Typography>
              ))}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Metadata */}
      <Box
        sx={{
          mt: 4,
          pt: 3,
          borderTop: '1px solid rgba(148, 163, 184, 0.1)',
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: '#64748b',
            textAlign: 'center',
          }}
        >
          שיטת חילוץ: {boqData.metadata.extraction_method} |
          זמן עיבוד: {boqData.metadata.processing_time_seconds.toFixed(2)} שניות |
          תאריך: {new Date(boqData.date).toLocaleDateString('he-IL')}
        </Typography>
      </Box>
    </MainLayout>
  );
}
