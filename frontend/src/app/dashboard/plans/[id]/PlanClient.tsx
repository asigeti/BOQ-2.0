'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
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
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { MainLayout } from '@/components/layout';
import api from '@/utils/axios';

interface BOQItem {
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
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
    </motion.div>
  );
}

function ChapterSection({ chapter, index }: { chapter: BOQChapter; index: number }) {
  const [expanded, setExpanded] = useState(true);

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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      <Card sx={{ mb: 3, overflow: 'hidden' }}>
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
                {chapter.chapter_name_en} - {chapter.items.length} items
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" fontWeight={700} color="primary">
              {chapter.chapter_total.toLocaleString('he-IL', { minimumFractionDigits: 2 })} &#x20AA;
            </Typography>
            <IconButton size="small">
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        <Collapse in={expanded}>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, width: '10%' }}>Code</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '35%' }}>Description</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '10%' }}>Qty</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '8%' }}>Unit</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '12%' }}>Price</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '12%' }}>Total</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600, width: '13%' }}>Confidence</TableCell>
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
                            Dekel: {item.dekel_code}
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
                      <Typography variant="body2" fontWeight={500}>
                        {item.quantity.toLocaleString('he-IL', { maximumFractionDigits: 2 })}
                      </Typography>
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
                      <Typography variant="body2">
                        {item.unit_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} &#x20AA;
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" fontWeight={600} color="primary">
                        {item.total_price.toLocaleString('he-IL', { minimumFractionDigits: 2 })} &#x20AA;
                      </Typography>
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
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Collapse>
      </Card>
    </motion.div>
  );
}

function getIdFromPath(): string {
  if (typeof window === 'undefined') return '';
  // Extract ID from URL path: /BOQ-2.0/dashboard/plans/16/ → '16'
  const parts = window.location.pathname.replace(/\/+$/, '').split('/');
  return parts[parts.length - 1] || '';
}

export default function PlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const paramId = params.id as string;
  const queryId = searchParams.get('id');
  const planId = paramId && paramId !== '_' ? paramId : queryId || getIdFromPath();

  // Clean up URL: replace /_/?id=18 with /18/ for a clean browser URL
  useEffect(() => {
    if (queryId && planId) {
      const cleanPath = window.location.pathname.replace(/\/_\/$/, `/${planId}/`);
      window.history.replaceState(null, '', cleanPath);
    }
  }, [queryId, planId]);

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
        setError('Processing failed. Please try uploading the file again.');
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
          project_name: 'Project',
          filename: '',
          date: new Date().toISOString(),
          chapters: [{
            chapter_code: '01',
            chapter_name_he: 'Materials',
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
        setError('Unable to load BOQ data');
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
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4 }}
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
          </motion.div>

          <Typography variant="h5" fontWeight={600} gutterBottom>
            {status.status === 'pending' ? 'Waiting for processing...' : 'Processing file...'}
          </Typography>

          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            {status.status === 'processing'
              ? 'Analyzing the plan and generating BOQ'
              : 'File is queued for processing'
            }
          </Typography>

          <Box sx={{ width: 400, maxWidth: '90%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Progress
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

  if (error) {
    return (
      <MainLayout>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700}>BOQ</Typography>
          <Typography variant="body2" color="text.secondary">Processing error</Typography>
        </Box>
        <Alert
          severity="error"
          sx={{ borderRadius: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          }
        >
          {error}
        </Alert>
      </MainLayout>
    );
  }

  if (loading || !boqData) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
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
              BOQ
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
          Export to Excel
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <SummaryCard
            title="Subtotal"
            value={`${boqData.summary.subtotal.toLocaleString('he-IL', { minimumFractionDigits: 2 })} \u20AA`}
            icon={<ReceiptIcon sx={{ fontSize: 24, color: '#6366f1' }} />}
            color="#6366f1"
            delay={0}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <SummaryCard
            title={`VAT (${(boqData.summary.vat_rate * 100).toFixed(0)}%)`}
            value={`${boqData.summary.vat_amount.toLocaleString('he-IL', { minimumFractionDigits: 2 })} \u20AA`}
            icon={<MoneyIcon sx={{ fontSize: 24, color: '#f59e0b' }} />}
            color="#f59e0b"
            delay={0.1}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <SummaryCard
            title="Grand Total"
            value={`${boqData.summary.grand_total.toLocaleString('he-IL', { minimumFractionDigits: 2 })} \u20AA`}
            icon={<MoneyIcon sx={{ fontSize: 24, color: '#10b981' }} />}
            color="#10b981"
            delay={0.2}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <SummaryCard
            title="Chapters"
            value={boqData.chapters.length.toString()}
            icon={<LayersIcon sx={{ fontSize: 24, color: '#06b6d4' }} />}
            color="#06b6d4"
            delay={0.3}
          />
        </Grid>
      </Grid>

      {boqData.chapters.map((chapter, index) => (
        <ChapterSection key={chapter.chapter_code} chapter={chapter} index={index} />
      ))}

      {boqData.notes && boqData.notes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        >
          <Card sx={{ mt: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Notes
              </Typography>
              {boqData.notes.map((note, index) => (
                <Typography key={index} variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {note}
                </Typography>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          Extraction method: {boqData.metadata.extraction_method} |
          Processing time: {boqData.metadata.processing_time_seconds.toFixed(2)}s |
          Date: {new Date(boqData.date).toLocaleDateString('he-IL')}
        </Typography>
      </Box>
    </MainLayout>
  );
}
