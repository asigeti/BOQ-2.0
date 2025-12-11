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
        <Skeleton variant="rounded" height={60} sx={{ mb: 2 }} />
        <Skeleton variant="rounded" height={200} />
      </Box>
    );
  }

  return (
    <Box>
      {/* View Mode Toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" fontWeight={600}>
          תצוגת כתב כמויות
        </Typography>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={handleViewModeChange}
          size="small"
        >
          <ToggleButton value="aggregated" sx={{ px: 2 }}>
            <AggregateIcon sx={{ mr: 1 }} />
            מאוחד
          </ToggleButton>
          <ToggleButton value="by-plan" sx={{ px: 2 }}>
            <ViewListIcon sx={{ mr: 1 }} />
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
              backgroundColor: alpha('#6366f1', 0.05),
              borderRadius: 2,
              flexWrap: 'wrap',
            }}
          >
            <Tooltip title="מספר קבצי מקור">
              <Chip
                icon={<FileIcon />}
                label={`${aggregatedData.summary.source_file_count} קבצים`}
                variant="outlined"
              />
            </Tooltip>
            <Tooltip title="פריטים מקוריים לפני מיזוג">
              <Chip
                icon={<LayersIcon />}
                label={`${aggregatedData.summary.aggregation_stats.original_items} פריטים מקוריים`}
                variant="outlined"
              />
            </Tooltip>
            <Tooltip title="פריטים אחרי מיזוג">
              <Chip
                icon={<MergeIcon />}
                label={`${aggregatedData.summary.total_items} פריטים מאוחדים`}
                color="primary"
              />
            </Tooltip>
            <Tooltip title="פריטים שמוזגו">
              <Chip
                label={`${aggregatedData.summary.aggregation_stats.items_merged} מוזגו`}
                sx={{
                  backgroundColor: alpha('#10b981', 0.1),
                  color: '#10b981',
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
                  <Chip label={`${chapter.item_count} פריטים`} size="small" variant="outlined" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h6" fontWeight={600} color="primary">
                    {chapter.chapter_total.toLocaleString('he-IL')} ₪
                  </Typography>
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
                        <TableCell align="right">כמות מאוחדת</TableCell>
                        <TableCell>יחידה</TableCell>
                        <TableCell align="right">מחיר יח׳</TableCell>
                        <TableCell align="right">סה״כ</TableCell>
                        <TableCell align="center">מקורות</TableCell>
                        <TableCell align="center">אמינות ממוצעת</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {chapter.items.map((item) => (
                        <>
                          <TableRow
                            key={item.item_code}
                            sx={{
                              backgroundColor:
                                item.source_count > 1 ? alpha('#10b981', 0.03) : 'transparent',
                            }}
                          >
                            <TableCell sx={{ fontWeight: 600 }}>{item.item_code}</TableCell>
                            <TableCell sx={{ maxWidth: 250 }}>{item.description_he}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>
                              {item.total_quantity.toLocaleString('he-IL')}
                            </TableCell>
                            <TableCell>{item.unit}</TableCell>
                            <TableCell align="right">
                              {item.unit_price.toLocaleString('he-IL')} ₪
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 600 }}>
                              {item.total_price.toLocaleString('he-IL')} ₪
                            </TableCell>
                            <TableCell align="center">
                              <Tooltip title={item.source_count > 1 ? 'לחץ לפרטי מקורות' : ''}>
                                <Badge
                                  badgeContent={item.source_count > 1 ? item.source_count : 0}
                                  color="success"
                                  onClick={() =>
                                    item.source_count > 1 && toggleSources(item.item_code)
                                  }
                                  sx={{ cursor: item.source_count > 1 ? 'pointer' : 'default' }}
                                >
                                  <Chip
                                    label={
                                      item.source_count > 1
                                        ? `${item.source_count} קבצים`
                                        : '1 קובץ'
                                    }
                                    size="small"
                                    sx={{
                                      backgroundColor:
                                        item.source_count > 1
                                          ? alpha('#10b981', 0.1)
                                          : alpha('#64748b', 0.1),
                                      color: item.source_count > 1 ? '#10b981' : '#64748b',
                                    }}
                                  />
                                </Badge>
                              </Tooltip>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={`${Math.round(item.avg_confidence * 100)}%`}
                                size="small"
                                sx={{
                                  backgroundColor: alpha(
                                    getConfidenceColor(item.avg_confidence),
                                    0.1
                                  ),
                                  color: getConfidenceColor(item.avg_confidence),
                                  fontWeight: 600,
                                  fontSize: '0.7rem',
                                }}
                              />
                            </TableCell>
                          </TableRow>
                          {/* Sources expansion row */}
                          {item.source_count > 1 && expandedSources.includes(item.item_code) && (
                            <TableRow>
                              <TableCell colSpan={8} sx={{ p: 0 }}>
                                <Box
                                  sx={{
                                    p: 2,
                                    backgroundColor: alpha('#6366f1', 0.02),
                                    borderTop: `1px dashed ${alpha('#6366f1', 0.2)}`,
                                  }}
                                >
                                  <Typography
                                    variant="subtitle2"
                                    fontWeight={600}
                                    sx={{ mb: 1, color: 'text.secondary' }}
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
                                          sx={{ fontSize: 16, color: 'text.secondary' }}
                                        />
                                        <Typography variant="body2" sx={{ flex: 1 }}>
                                          {source.filename}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
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
                                              0.1
                                            ),
                                            color: getConfidenceColor(source.confidence),
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
            <Box sx={{ width: 300, p: 2, backgroundColor: alpha('#6366f1', 0.05), borderRadius: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>סה״כ פרקים:</Typography>
                <Typography fontWeight={600}>{aggregatedData.summary.total_chapters}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>סה״כ פריטים:</Typography>
                <Typography fontWeight={600}>{aggregatedData.summary.total_items}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6" fontWeight={700}>
                  סה״כ:
                </Typography>
                <Typography variant="h6" fontWeight={700} color="primary">
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
            <Card key={plan.plan_id} sx={{ mb: 2 }}>
              <Box
                onClick={() => togglePlan(plan.plan_id)}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 2,
                  backgroundColor: alpha('#f59e0b', 0.05),
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: alpha('#f59e0b', 0.1),
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <FileIcon sx={{ color: '#f59e0b' }} />
                  <Typography variant="h6" fontWeight={600}>
                    {plan.filename}
                  </Typography>
                  <Chip label={plan.file_type.toUpperCase()} size="small" variant="outlined" />
                  <Chip label={`${plan.item_count} פריטים`} size="small" />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h6" fontWeight={600} sx={{ color: '#f59e0b' }}>
                    {plan.total_price.toLocaleString('he-IL')} ₪
                  </Typography>
                  {expandedPlans.includes(plan.plan_id) ? <CollapseIcon /> : <ExpandIcon />}
                </Box>
              </Box>

              <Collapse in={expandedPlans.includes(plan.plan_id)}>
                <CardContent>
                  {plan.chapters.map((chapter) => (
                    <Box key={chapter.chapter_code} sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1 }}>
                        פרק {chapter.chapter_code}: {chapter.chapter_name_he}
                        <Typography
                          component="span"
                          sx={{ ml: 1, color: 'text.secondary', fontSize: '0.9rem' }}
                        >
                          ({chapter.chapter_total.toLocaleString('he-IL')} ₪)
                        </Typography>
                      </Typography>
                      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ backgroundColor: alpha('#f59e0b', 0.02) }}>
                              <TableCell>קוד</TableCell>
                              <TableCell>תיאור</TableCell>
                              <TableCell align="right">כמות</TableCell>
                              <TableCell>יחידה</TableCell>
                              <TableCell align="right">מחיר יח׳</TableCell>
                              <TableCell align="right">סה״כ</TableCell>
                              <TableCell>שכבה</TableCell>
                              <TableCell align="center">אמינות</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {chapter.items.map((item) => (
                              <TableRow key={item.id}>
                                <TableCell sx={{ fontWeight: 600 }}>{item.item_code}</TableCell>
                                <TableCell sx={{ maxWidth: 200 }}>{item.description_he}</TableCell>
                                <TableCell align="right">
                                  {item.quantity.toLocaleString('he-IL')}
                                </TableCell>
                                <TableCell>{item.unit}</TableCell>
                                <TableCell align="right">
                                  {item.unit_price.toLocaleString('he-IL')} ₪
                                </TableCell>
                                <TableCell align="right" sx={{ fontWeight: 600 }}>
                                  {item.total_price.toLocaleString('he-IL')} ₪
                                </TableCell>
                                <TableCell
                                  sx={{ fontFamily: 'monospace', fontSize: '0.8rem', maxWidth: 120 }}
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
                                <TableCell align="center">
                                  <Chip
                                    label={`${Math.round((item.confidence || 0.5) * 100)}%`}
                                    size="small"
                                    sx={{
                                      backgroundColor: alpha(
                                        getConfidenceColor(item.confidence || 0.5),
                                        0.1
                                      ),
                                      color: getConfidenceColor(item.confidence || 0.5),
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
            <Box sx={{ width: 300, p: 2, backgroundColor: alpha('#f59e0b', 0.05), borderRadius: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>סה״כ קבצים:</Typography>
                <Typography fontWeight={600}>{byPlanData.summary.total_plans}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6" fontWeight={700}>
                  סה״כ:
                </Typography>
                <Typography variant="h6" fontWeight={700} sx={{ color: '#f59e0b' }}>
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
