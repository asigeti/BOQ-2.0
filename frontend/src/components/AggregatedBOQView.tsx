'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  alpha,
  Chip,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Collapse,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  ViewList as ViewListIcon,
  AccountTree as AggregateIcon,
  Description as FileIcon,
  Layers as LayersIcon,
  MergeType as MergeIcon,
} from '@mui/icons-material';
import api from '@/utils/axios';

interface BOQItemSource {
  plan_id: number;
  filename: string;
  layer: string | null;
  quantity: number;
  confidence: number;
}

interface AggregatedItem {
  item_code: string;
  chapter_code: string;
  chapter_name_he: string;
  chapter_name_en: string;
  description_he: string;
  description_en: string;
  unit: string;
  unit_price: number;
  total_quantity: number;
  total_price: number;
  source_count: number;
  sources: BOQItemSource[];
  avg_confidence: number;
  item_ids: number[];
}

interface AggregatedChapter {
  chapter_code: string;
  chapter_name_he: string;
  chapter_name_en: string;
  items: AggregatedItem[];
  item_count: number;
  chapter_total: number;
}

interface AggregatedBOQData {
  project_id: number;
  chapters: AggregatedChapter[];
  summary: {
    total_items: number;
    total_chapters: number;
    total_price: number;
    source_files: string[];
    source_file_count: number;
    aggregation_stats: {
      original_items: number;
      aggregated_items: number;
      items_merged: number;
      merge_ratio: number;
    };
  };
}

interface ByPlanItem {
  id: number;
  item_code: string;
  description_he: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  source_layer: string | null;
  confidence: number | null;
}

interface ByPlanChapter {
  chapter_code: string;
  chapter_name_he: string;
  chapter_name_en: string;
  items: ByPlanItem[];
  chapter_total: number;
}

interface ByPlanData {
  plan_id: number;
  filename: string;
  file_type: string;
  item_count: number;
  total_price: number;
  chapters: ByPlanChapter[];
}

interface ByPlanBOQData {
  project_id: number;
  plans: ByPlanData[];
  summary: {
    total_plans: number;
    total_price: number;
  };
}

interface AggregatedBOQViewProps {
  projectId: number;
}

export default function AggregatedBOQView({ projectId }: AggregatedBOQViewProps) {
  const [viewMode, setViewMode] = useState<'aggregated' | 'by-plan'>('aggregated');
  const [aggregatedData, setAggregatedData] = useState<AggregatedBOQData | null>(null);
  const [byPlanData, setByPlanData] = useState<ByPlanBOQData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedChapters, setExpandedChapters] = useState<string[]>([]);
  const [expandedPlans, setExpandedPlans] = useState<number[]>([]);
  const [expandedSources, setExpandedSources] = useState<string[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (viewMode === 'aggregated') {
        const response = await api.get(`/projects/${projectId}/boq/aggregated`);
        setAggregatedData(response.data);
        setExpandedChapters(response.data.chapters.map((c: AggregatedChapter) => c.chapter_code));
      } else {
        const response = await api.get(`/projects/${projectId}/boq/by-plan`);
        setByPlanData(response.data);
        setExpandedPlans(response.data.plans.map((p: ByPlanData) => p.plan_id));
      }
    } catch (error) {
      console.error('Failed to fetch BOQ data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId, viewMode]);

  const handleViewModeChange = (
    _: React.MouseEvent<HTMLElement>,
    newMode: 'aggregated' | 'by-plan' | null
  ) => {
    if (newMode !== null) {
      setViewMode(newMode);
    }
  };

  const toggleChapter = (code: string) => {
    setExpandedChapters((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const togglePlan = (planId: number) => {
    setExpandedPlans((prev) =>
      prev.includes(planId) ? prev.filter((id) => id !== planId) : [...prev, planId]
    );
  };

  const toggleSources = (itemCode: string) => {
    setExpandedSources((prev) =>
      prev.includes(itemCode) ? prev.filter((c) => c !== itemCode) : [...prev, itemCode]
    );
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.5) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return (
      <Box>
        <Skeleton
          variant="rounded"
          height={60}
          sx={{
            mb: 2,
            backgroundColor: 'rgba(148, 163, 184, 0.1)',
          }}
        />
        <Skeleton
          variant="rounded"
          height={200}
          sx={{
            backgroundColor: 'rgba(148, 163, 184, 0.1)',
          }}
        />
      </Box>
    );
  }

  return (
    <Box>
      {/* View Mode Toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            color: '#f1f5f9',
          }}
        >
          תצוגת כתב כמויות
        </Typography>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={handleViewModeChange}
          size="small"
          sx={{
            backgroundColor: 'rgba(148, 163, 184, 0.08)',
            borderRadius: '12px',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            '& .MuiToggleButton-root': {
              border: 'none',
              color: '#64748b',
              px: 2,
              py: 1,
              borderRadius: '10px !important',
              transition: 'all 0.2s ease',
              '&:hover': {
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
              },
              '&.Mui-selected': {
                backgroundColor: 'rgba(14, 165, 233, 0.2)',
                color: '#0ea5e9',
                '&:hover': {
                  backgroundColor: 'rgba(14, 165, 233, 0.25)',
                },
              },
            },
          }}
        >
          <ToggleButton value="aggregated">
            <AggregateIcon sx={{ mr: 1, fontSize: 18 }} />
            מאוחד
          </ToggleButton>
          <ToggleButton value="by-plan">
            <ViewListIcon sx={{ mr: 1, fontSize: 18 }} />
            לפי קובץ
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Aggregated View */}
      {viewMode === 'aggregated' && aggregatedData && (
        <>
          {/* Aggregation Stats */}
          <Box
            sx={{
              display: 'flex',
              gap: 2,
              mb: 3,
              p: 2,
              backgroundColor: 'rgba(14, 165, 233, 0.08)',
              borderRadius: '14px',
              border: '1px solid rgba(14, 165, 233, 0.2)',
              flexWrap: 'wrap',
            }}
          >
            <Tooltip title="מספר קבצי מקור">
              <Chip
                icon={<FileIcon sx={{ color: '#64748b !important' }} />}
                label={`${aggregatedData.summary.source_file_count} קבצים`}
                variant="outlined"
                sx={{
                  borderColor: 'rgba(148, 163, 184, 0.3)',
                  color: '#94a3b8',
                }}
              />
            </Tooltip>
            <Tooltip title="פריטים מקוריים לפני מיזוג">
              <Chip
                icon={<LayersIcon sx={{ color: '#64748b !important' }} />}
                label={`${aggregatedData.summary.aggregation_stats.original_items} פריטים מקוריים`}
                variant="outlined"
                sx={{
                  borderColor: 'rgba(148, 163, 184, 0.3)',
                  color: '#94a3b8',
                }}
              />
            </Tooltip>
            <Tooltip title="פריטים אחרי מיזוג">
              <Chip
                icon={<MergeIcon sx={{ color: '#0ea5e9 !important' }} />}
                label={`${aggregatedData.summary.total_items} פריטים מאוחדים`}
                sx={{
                  backgroundColor: 'rgba(14, 165, 233, 0.2)',
                  color: '#0ea5e9',
                  border: '1px solid rgba(14, 165, 233, 0.3)',
                  fontWeight: 600,
                }}
              />
            </Tooltip>
            <Tooltip title="פריטים שמוזגו">
              <Chip
                label={`${aggregatedData.summary.aggregation_stats.items_merged} מוזגו`}
                sx={{
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  fontWeight: 600,
                }}
              />
            </Tooltip>
          </Box>

          {/* Chapters */}
          {aggregatedData.chapters.map((chapter) => (
            <Box key={chapter.chapter_code} sx={{ mb: 2 }}>
              <Box
                onClick={() => toggleChapter(chapter.chapter_code)}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 2,
                  backgroundColor: 'rgba(14, 165, 233, 0.08)',
                  borderRadius: '14px',
                  border: '1px solid rgba(14, 165, 233, 0.15)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(14, 165, 233, 0.12)',
                    borderColor: 'rgba(14, 165, 233, 0.3)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 700,
                      color: '#f1f5f9',
                      fontSize: '1rem',
                    }}
                  >
                    פרק {chapter.chapter_code}: {chapter.chapter_name_he}
                  </Typography>
                  <Chip
                    label={`${chapter.item_count} פריטים`}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(148, 163, 184, 0.1)',
                      color: '#94a3b8',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                    }}
                  />
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
                    {chapter.chapter_total.toLocaleString('he-IL')} ₪
                  </Typography>
                  {expandedChapters.includes(chapter.chapter_code) ? (
                    <CollapseIcon sx={{ color: '#64748b' }} />
                  ) : (
                    <ExpandIcon sx={{ color: '#64748b' }} />
                  )}
                </Box>
              </Box>

              <Collapse in={expandedChapters.includes(chapter.chapter_code)}>
                <TableContainer
                  component={Paper}
                  sx={{
                    mt: 1,
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '12px',
                    border: '1px solid rgba(148, 163, 184, 0.1)',
                    boxShadow: 'none',
                  }}
                >
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        {['קוד', 'תיאור', 'כמות מאוחדת', 'יחידה', 'מחיר יח׳', 'סה״כ', 'מקורות', 'אמינות ממוצעת'].map((header, idx) => (
                          <TableCell
                            key={header}
                            align={[2, 4, 5].includes(idx) ? 'right' : idx >= 6 ? 'center' : 'inherit'}
                            sx={{
                              borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                              color: '#64748b',
                              fontWeight: 600,
                              fontSize: '0.75rem',
                              backgroundColor: 'rgba(14, 165, 233, 0.03)',
                            }}
                          >
                            {header}
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {chapter.items.map((item) => (
                        <>
                          <TableRow
                            key={item.item_code}
                            sx={{
                              backgroundColor:
                                item.source_count > 1 ? 'rgba(16, 185, 129, 0.05)' : 'transparent',
                              '&:hover': {
                                backgroundColor: 'rgba(14, 165, 233, 0.05)',
                              },
                            }}
                          >
                            <TableCell
                              sx={{
                                fontWeight: 600,
                                color: '#f1f5f9',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.item_code}
                            </TableCell>
                            <TableCell
                              sx={{
                                maxWidth: 250,
                                color: '#94a3b8',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.description_he}
                            </TableCell>
                            <TableCell
                              align="right"
                              sx={{
                                fontWeight: 600,
                                color: '#f1f5f9',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.total_quantity.toLocaleString('he-IL')}
                            </TableCell>
                            <TableCell
                              sx={{
                                color: '#94a3b8',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.unit}
                            </TableCell>
                            <TableCell
                              align="right"
                              sx={{
                                color: '#94a3b8',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.unit_price.toLocaleString('he-IL')} ₪
                            </TableCell>
                            <TableCell
                              align="right"
                              sx={{
                                fontWeight: 600,
                                color: '#0ea5e9',
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              {item.total_price.toLocaleString('he-IL')} ₪
                            </TableCell>
                            <TableCell
                              align="center"
                              sx={{
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              <Tooltip title={item.source_count > 1 ? 'לחץ לפרטי מקורות' : ''}>
                                <Badge
                                  badgeContent={item.source_count > 1 ? item.source_count : 0}
                                  sx={{
                                    '& .MuiBadge-badge': {
                                      backgroundColor: '#10b981',
                                      color: 'white',
                                    },
                                  }}
                                  onClick={() =>
                                    item.source_count > 1 && toggleSources(item.item_code)
                                  }
                                >
                                  <Chip
                                    label={
                                      item.source_count > 1
                                        ? `${item.source_count} קבצים`
                                        : '1 קובץ'
                                    }
                                    size="small"
                                    sx={{
                                      cursor: item.source_count > 1 ? 'pointer' : 'default',
                                      backgroundColor:
                                        item.source_count > 1
                                          ? 'rgba(16, 185, 129, 0.15)'
                                          : 'rgba(148, 163, 184, 0.1)',
                                      color: item.source_count > 1 ? '#10b981' : '#64748b',
                                      border: `1px solid ${item.source_count > 1 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(148, 163, 184, 0.2)'}`,
                                      fontSize: '0.7rem',
                                    }}
                                  />
                                </Badge>
                              </Tooltip>
                            </TableCell>
                            <TableCell
                              align="center"
                              sx={{
                                borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                              }}
                            >
                              <Chip
                                label={`${Math.round(item.avg_confidence * 100)}%`}
                                size="small"
                                sx={{
                                  backgroundColor: alpha(
                                    getConfidenceColor(item.avg_confidence),
                                    0.15
                                  ),
                                  color: getConfidenceColor(item.avg_confidence),
                                  border: `1px solid ${alpha(getConfidenceColor(item.avg_confidence), 0.3)}`,
                                  fontWeight: 600,
                                  fontSize: '0.7rem',
                                }}
                              />
                            </TableCell>
                          </TableRow>
                          {/* Sources expansion row */}
                          {item.source_count > 1 && expandedSources.includes(item.item_code) && (
                            <TableRow>
                              <TableCell
                                colSpan={8}
                                sx={{
                                  p: 0,
                                  borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                }}
                              >
                                <Box
                                  sx={{
                                    p: 2,
                                    backgroundColor: 'rgba(14, 165, 233, 0.03)',
                                    borderTop: '1px dashed rgba(14, 165, 233, 0.2)',
                                  }}
                                >
                                  <Typography
                                    variant="subtitle2"
                                    sx={{
                                      mb: 1,
                                      color: '#64748b',
                                      fontWeight: 600,
                                    }}
                                  >
                                    פירוט מקורות:
                                  </Typography>
                                  <Box
                                    sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}
                                  >
                                    {item.sources.map((source, idx) => (
                                      <Box
                                        key={idx}
                                        sx={{
                                          display: 'flex',
                                          gap: 2,
                                          alignItems: 'center',
                                          fontSize: '0.85rem',
                                        }}
                                      >
                                        <FileIcon
                                          sx={{ fontSize: 16, color: '#64748b' }}
                                        />
                                        <Typography
                                          variant="body2"
                                          sx={{ flex: 1, color: '#94a3b8' }}
                                        >
                                          {source.filename}
                                        </Typography>
                                        <Typography variant="body2" sx={{ color: '#64748b' }}>
                                          כמות: {source.quantity}
                                        </Typography>
                                        <Chip
                                          label={`${Math.round(source.confidence * 100)}%`}
                                          size="small"
                                          sx={{
                                            height: 20,
                                            fontSize: '0.7rem',
                                            backgroundColor: alpha(
                                              getConfidenceColor(source.confidence),
                                              0.15
                                            ),
                                            color: getConfidenceColor(source.confidence),
                                            border: `1px solid ${alpha(getConfidenceColor(source.confidence), 0.3)}`,
                                          }}
                                        />
                                      </Box>
                                    ))}
                                  </Box>
                                </Box>
                              </TableCell>
                            </TableRow>
                          )}
                        </>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Collapse>
            </Box>
          ))}

          {/* Summary */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
            <Box
              sx={{
                width: 300,
                p: 3,
                backgroundColor: 'rgba(14, 165, 233, 0.08)',
                borderRadius: '16px',
                border: '1px solid rgba(14, 165, 233, 0.2)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                <Typography sx={{ color: '#94a3b8' }}>סה״כ פרקים:</Typography>
                <Typography sx={{ fontWeight: 600, color: '#f1f5f9' }}>
                  {aggregatedData.summary.total_chapters}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                <Typography sx={{ color: '#94a3b8' }}>סה״כ פריטים:</Typography>
                <Typography sx={{ fontWeight: 600, color: '#f1f5f9' }}>
                  {aggregatedData.summary.total_items}
                </Typography>
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  pt: 2,
                  borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#f1f5f9' }}>
                  סה״כ:
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0ea5e9' }}>
                  {aggregatedData.summary.total_price.toLocaleString('he-IL')} ₪
                </Typography>
              </Box>
            </Box>
          </Box>
        </>
      )}

      {/* By Plan View */}
      {viewMode === 'by-plan' && byPlanData && (
        <>
          {/* Plans */}
          {byPlanData.plans.map((plan) => (
            <Card
              key={plan.plan_id}
              sx={{
                mb: 2,
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                borderRadius: '16px',
                boxShadow: 'none',
              }}
            >
              <Box
                onClick={() => togglePlan(plan.plan_id)}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 2,
                  backgroundColor: 'rgba(245, 158, 11, 0.08)',
                  borderRadius: '16px 16px 0 0',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(245, 158, 11, 0.12)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <FileIcon sx={{ color: '#f59e0b' }} />
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 700,
                      color: '#f1f5f9',
                      fontSize: '1rem',
                    }}
                  >
                    {plan.filename}
                  </Typography>
                  <Chip
                    label={plan.file_type.toUpperCase()}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(148, 163, 184, 0.1)',
                      color: '#94a3b8',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                    }}
                  />
                  <Chip
                    label={`${plan.item_count} פריטים`}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(245, 158, 11, 0.15)',
                      color: '#f59e0b',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                    }}
                  />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 700,
                      color: '#f59e0b',
                      fontSize: '1rem',
                    }}
                  >
                    {plan.total_price.toLocaleString('he-IL')} ₪
                  </Typography>
                  {expandedPlans.includes(plan.plan_id) ? (
                    <CollapseIcon sx={{ color: '#64748b' }} />
                  ) : (
                    <ExpandIcon sx={{ color: '#64748b' }} />
                  )}
                </Box>
              </Box>

              <Collapse in={expandedPlans.includes(plan.plan_id)}>
                <CardContent sx={{ p: 2 }}>
                  {plan.chapters.map((chapter) => (
                    <Box key={chapter.chapter_code} sx={{ mb: 2 }}>
                      <Typography
                        variant="subtitle1"
                        sx={{
                          fontWeight: 600,
                          color: '#f1f5f9',
                          mb: 1,
                        }}
                      >
                        פרק {chapter.chapter_code}: {chapter.chapter_name_he}
                        <Typography
                          component="span"
                          sx={{ ml: 1, color: '#64748b', fontSize: '0.9rem' }}
                        >
                          ({chapter.chapter_total.toLocaleString('he-IL')} ₪)
                        </Typography>
                      </Typography>
                      <TableContainer
                        component={Paper}
                        sx={{
                          mb: 2,
                          backgroundColor: 'rgba(0, 0, 0, 0.2)',
                          borderRadius: '12px',
                          border: '1px solid rgba(148, 163, 184, 0.1)',
                          boxShadow: 'none',
                        }}
                      >
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              {['קוד', 'תיאור', 'כמות', 'יחידה', 'מחיר יח׳', 'סה״כ', 'שכבה', 'אמינות'].map((header, idx) => (
                                <TableCell
                                  key={header}
                                  align={[2, 4, 5].includes(idx) ? 'right' : idx >= 6 ? 'center' : 'inherit'}
                                  sx={{
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                                    color: '#64748b',
                                    fontWeight: 600,
                                    fontSize: '0.75rem',
                                    backgroundColor: 'rgba(245, 158, 11, 0.03)',
                                  }}
                                >
                                  {header}
                                </TableCell>
                              ))}
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {chapter.items.map((item) => (
                              <TableRow
                                key={item.id}
                                sx={{
                                  '&:hover': {
                                    backgroundColor: 'rgba(245, 158, 11, 0.05)',
                                  },
                                }}
                              >
                                <TableCell
                                  sx={{
                                    fontWeight: 600,
                                    color: '#f1f5f9',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.item_code}
                                </TableCell>
                                <TableCell
                                  sx={{
                                    maxWidth: 200,
                                    color: '#94a3b8',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.description_he}
                                </TableCell>
                                <TableCell
                                  align="right"
                                  sx={{
                                    color: '#f1f5f9',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.quantity.toLocaleString('he-IL')}
                                </TableCell>
                                <TableCell
                                  sx={{
                                    color: '#94a3b8',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.unit}
                                </TableCell>
                                <TableCell
                                  align="right"
                                  sx={{
                                    color: '#94a3b8',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.unit_price.toLocaleString('he-IL')} ₪
                                </TableCell>
                                <TableCell
                                  align="right"
                                  sx={{
                                    fontWeight: 600,
                                    color: '#f59e0b',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  {item.total_price.toLocaleString('he-IL')} ₪
                                </TableCell>
                                <TableCell
                                  sx={{
                                    fontFamily: 'monospace',
                                    fontSize: '0.75rem',
                                    maxWidth: 120,
                                    color: '#64748b',
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
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
                                <TableCell
                                  align="center"
                                  sx={{
                                    borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                  }}
                                >
                                  <Chip
                                    label={`${Math.round((item.confidence || 0.5) * 100)}%`}
                                    size="small"
                                    sx={{
                                      backgroundColor: alpha(
                                        getConfidenceColor(item.confidence || 0.5),
                                        0.15
                                      ),
                                      color: getConfidenceColor(item.confidence || 0.5),
                                      border: `1px solid ${alpha(getConfidenceColor(item.confidence || 0.5), 0.3)}`,
                                      fontWeight: 600,
                                      fontSize: '0.7rem',
                                    }}
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  ))}
                </CardContent>
              </Collapse>
            </Card>
          ))}

          {/* Summary */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
            <Box
              sx={{
                width: 300,
                p: 3,
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                borderRadius: '16px',
                border: '1px solid rgba(245, 158, 11, 0.2)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                <Typography sx={{ color: '#94a3b8' }}>סה״כ קבצים:</Typography>
                <Typography sx={{ fontWeight: 600, color: '#f1f5f9' }}>
                  {byPlanData.summary.total_plans}
                </Typography>
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  pt: 2,
                  borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#f1f5f9' }}>
                  סה״כ:
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#f59e0b' }}>
                  {byPlanData.summary.total_price.toLocaleString('he-IL')} ₪
                </Typography>
              </Box>
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
