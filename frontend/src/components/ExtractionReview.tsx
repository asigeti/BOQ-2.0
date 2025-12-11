'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Checkbox,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
  IconButton,
  LinearProgress,
  Tooltip,
  alpha,
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import BlockIcon from '@mui/icons-material/Block';
import LayersIcon from '@mui/icons-material/Layers';
import SquareFootIcon from '@mui/icons-material/SquareFoot';
import api from '@/utils/axios';

interface LayerInfo {
  id: number;
  layer_name: string;
  area_m2: number;
  polyline_count: number;
  hatch_count: number;
  auto_category: string;
  user_selected?: boolean | null;
  group?: string;
  confidence?: number;
  filename?: string;
}

interface LayerGroup {
  layers: LayerInfo[];
  metadata: {
    name_he: string;
    name_en: string;
    icon: string;
    default_selected: boolean;
    description_he: string;
    description_en: string;
    color: string;
  };
  total_area_m2: number;
  layer_count: number;
}

interface FilePreview {
  plan_id: number;
  filename: string;
  processing_status: string;
  has_extraction: boolean;
  layer_groups?: Record<string, LayerGroup>;
}

interface ExtractionPreviewData {
  project_id: number;
  project_name: string;
  total_files: number;
  files_with_extraction: number;
  project_totals?: {
    include_area_m2: number;
    exclude_area_m2: number;
    review_area_m2: number;
    total_area_m2: number;
    selected_area_m2: number;
  };
  group_totals?: {
    [key: string]: {
      metadata: any;
      total_area_m2: number;
      layer_count: number;
    };
  };
  files: FilePreview[];
}

interface ExtractionReviewProps {
  projectId: number;
  onConfirm?: (selectedArea: number) => void;
}

// Category configuration
const categoryConfig = {
  include: {
    title: 'שכבות בנייה מומלצות',
    titleEn: 'Recommended Construction Layers',
    description: 'שכבות אלו מכילות אלמנטים של בנייה כגון קירות, רצפות, חדרים וכו׳. מומלץ לכלול אותן בחישוב.',
    icon: CheckCircleOutlineIcon,
    color: '#10b981',
    bgColor: '#ecfdf5',
    borderColor: '#a7f3d0',
  },
  review: {
    title: 'שכבות לבדיקה',
    titleEn: 'Layers to Review',
    description: 'שכבות אלו לא זוהו אוטומטית. בדוק אם הן מכילות שטחים רלוונטיים לכתב הכמויות.',
    icon: WarningAmberIcon,
    color: '#f59e0b',
    bgColor: '#fffbeb',
    borderColor: '#fde68a',
  },
  exclude: {
    title: 'שכבות שאינן בנייה',
    titleEn: 'Non-Construction Layers',
    description: 'שכבות אלו מכילות הערות, ממדים, סימנים וכו׳. בדרך כלל אין לכלול אותן בחישוב השטח.',
    icon: BlockIcon,
    color: '#ef4444',
    bgColor: '#fef2f2',
    borderColor: '#fecaca',
  },
};

export default function ExtractionReview({ projectId, onConfirm }: ExtractionReviewProps) {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ExtractionPreviewData | null>(null);
  const [selectedLayers, setSelectedLayers] = useState<Set<number>>(new Set()); // Changed to Set<number> for layer IDs
  const [customArea, setCustomArea] = useState<string>('');
  const [useCustomArea, setUseCustomArea] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['include', 'review'])
  );

  useEffect(() => {
    loadExtractionPreview();
  }, [projectId]);

  const loadExtractionPreview = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/projects/${projectId}/extraction-preview`);
      setData(response.data);

      // Auto-select layers based on default_selected from their group metadata
      const autoSelected = new Set<number>();
      response.data.files.forEach((file: FilePreview) => {
        if (file.layer_groups) {
          Object.entries(file.layer_groups).forEach(([groupName, group]: [string, LayerGroup]) => {
            if (group.metadata?.default_selected) {
              group.layers.forEach((layer: LayerInfo) => {
                autoSelected.add(layer.id);
              });
            }
          });
        }
      });
      setSelectedLayers(autoSelected);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load extraction data';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleLayer = (layerId: number) => {
    setSelectedLayers((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(layerId)) {
        newSet.delete(layerId);
      } else {
        newSet.add(layerId);
      }
      return newSet;
    });
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // Map new 8 groups to old 3 categories for display
  const getGroupsForCategory = (category: 'include' | 'exclude' | 'review'): string[] => {
    if (category === 'include') {
      return ['building', 'structural', 'utilities'];
    } else if (category === 'review') {
      return ['unknown'];
    } else {
      return ['site_boundary', 'infrastructure', 'landscape', 'annotations'];
    }
  };

  const selectAllInCategory = (category: 'include' | 'exclude' | 'review') => {
    if (!data) return;
    const newSet = new Set(selectedLayers);
    const targetGroups = getGroupsForCategory(category);

    data.files.forEach((file) => {
      if (file.layer_groups) {
        Object.entries(file.layer_groups).forEach(([groupName, group]: [string, LayerGroup]) => {
          if (targetGroups.includes(groupName)) {
            group.layers.forEach((layer: LayerInfo) => {
              newSet.add(layer.id);
            });
          }
        });
      }
    });
    setSelectedLayers(newSet);
  };

  const deselectAllInCategory = (category: 'include' | 'exclude' | 'review') => {
    if (!data) return;
    const newSet = new Set(selectedLayers);
    const targetGroups = getGroupsForCategory(category);

    data.files.forEach((file) => {
      if (file.layer_groups) {
        Object.entries(file.layer_groups).forEach(([groupName, group]: [string, LayerGroup]) => {
          if (targetGroups.includes(groupName)) {
            group.layers.forEach((layer: LayerInfo) => {
              newSet.delete(layer.id);
            });
          }
        });
      }
    });
    setSelectedLayers(newSet);
  };

  const getAllLayersInCategory = (category: 'include' | 'exclude' | 'review'): LayerInfo[] => {
    if (!data) return [];
    const layers: LayerInfo[] = [];
    const targetGroups = getGroupsForCategory(category);
    const seenIds = new Set<number>();

    data.files.forEach((file) => {
      if (file.layer_groups) {
        Object.entries(file.layer_groups).forEach(([groupName, group]: [string, LayerGroup]) => {
          if (targetGroups.includes(groupName)) {
            group.layers.forEach((layer: LayerInfo) => {
              // Avoid duplicates by layer ID
              if (!seenIds.has(layer.id)) {
                seenIds.add(layer.id);
                layers.push({ ...layer, filename: file.filename });
              }
            });
          }
        });
      }
    });
    // Sort by area descending
    return layers.sort((a, b) => b.area_m2 - a.area_m2);
  };

  const getLayersByFileInCategory = (category: 'include' | 'exclude' | 'review'): { filename: string; layers: LayerInfo[] }[] => {
    if (!data) return [];
    const targetGroups = getGroupsForCategory(category);
    const fileLayersMap: { [filename: string]: LayerInfo[] } = {};

    data.files.forEach((file) => {
      if (file.layer_groups) {
        const fileLayers: LayerInfo[] = [];
        Object.entries(file.layer_groups).forEach(([groupName, group]: [string, LayerGroup]) => {
          if (targetGroups.includes(groupName)) {
            group.layers.forEach((layer: LayerInfo) => {
              fileLayers.push(layer);
            });
          }
        });
        if (fileLayers.length > 0) {
          fileLayersMap[file.filename] = fileLayers.sort((a, b) => b.area_m2 - a.area_m2);
        }
      }
    });

    return Object.entries(fileLayersMap).map(([filename, layers]) => ({ filename, layers }));
  };

  const calculateSelectedArea = (): number => {
    if (!data) return 0;

    let total = 0;
    data.files.forEach((file) => {
      if (file.layer_groups) {
        Object.values(file.layer_groups).forEach((group: LayerGroup) => {
          group.layers.forEach((layer: LayerInfo) => {
            if (selectedLayers.has(layer.id)) {
              total += layer.area_m2;
            }
          });
        });
      }
    });
    return total;
  };

  const handleConfirm = async () => {
    try {
      setSubmitting(true);
      const finalArea = useCustomArea && customArea ? parseFloat(customArea) : undefined;

      await api.post(`/projects/${projectId}/extraction-confirm`, {
        selected_layer_ids: Array.from(selectedLayers), // Changed to send layer IDs
        custom_area_m2: finalArea,
      });

      if (onConfirm) {
        onConfirm(finalArea || calculateSelectedArea());
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to confirm selection';
      setError(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const formatArea = (area: number) => {
    if (area >= 1000000) {
      return `${(area / 1000000).toLocaleString('he-IL', { maximumFractionDigits: 2 })}M`;
    }
    if (area >= 1000) {
      return `${(area / 1000).toLocaleString('he-IL', { maximumFractionDigits: 1 })}K`;
    }
    return area.toLocaleString('he-IL', { maximumFractionDigits: 2 });
  };

  const formatAreaFull = (area: number) => {
    return area.toLocaleString('he-IL', { maximumFractionDigits: 2 });
  };

  if (loading) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={4}>
        <CircularProgress size={40} />
        <Typography sx={{ mt: 2 }} color="text.secondary">
          טוען נתוני חילוץ...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        לא נמצאו נתוני חילוץ
      </Alert>
    );
  }

  const selectedArea = calculateSelectedArea();
  // Support both old and new API structure
  const totalArea = data.project_totals?.total_area_m2 ||
    (data.group_totals ? Object.values(data.group_totals).reduce((sum: number, group: any) => sum + (group.total_area_m2 || 0), 0) : 0);
  const selectedPercentage = totalArea > 0 ? (selectedArea / totalArea) * 100 : 0;

  const renderCategorySection = (category: 'include' | 'exclude' | 'review') => {
    const config = categoryConfig[category];
    const fileLayersGroups = getLayersByFileInCategory(category);
    const isExpanded = expandedSections.has(category);
    const Icon = config.icon;

    // Calculate category totals across all files
    const allLayers = fileLayersGroups.flatMap(fg => fg.layers);
    const categorySelectedCount = allLayers.filter((l) => selectedLayers.has(l.id)).length;
    const categoryTotalArea = allLayers.reduce((sum, l) => sum + l.area_m2, 0);
    const categorySelectedArea = allLayers
      .filter((l) => selectedLayers.has(l.id))
      .reduce((sum, l) => sum + l.area_m2, 0);

    return (
      <Paper
        key={category}
        sx={{
          mb: 2,
          border: `1px solid ${config.borderColor}`,
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        {/* Section Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            bgcolor: config.bgColor,
            cursor: 'pointer',
            '&:hover': { bgcolor: alpha(config.color, 0.1) },
          }}
          onClick={() => toggleSection(category)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Icon sx={{ color: config.color, fontSize: 28 }} />
            <Box>
              <Typography variant="h6" fontWeight={600} color={config.color}>
                {config.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {allLayers.length} שכבות | {formatAreaFull(categoryTotalArea)} מ״ר
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                bgcolor: 'white',
                px: 2,
                py: 0.5,
                borderRadius: 1,
                border: `1px solid ${config.borderColor}`,
              }}
            >
              <Typography variant="body2" fontWeight={600} color={config.color}>
                נבחרו: {categorySelectedCount}/{allLayers.length}
              </Typography>
            </Box>
            <IconButton size="small">
              {isExpanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          </Box>
        </Box>

        {/* Section Content */}
        <Collapse in={isExpanded}>
          <Box sx={{ p: 2 }}>
            {/* Description */}
            <Alert
              severity="info"
              sx={{
                mb: 2,
                bgcolor: 'transparent',
                border: 'none',
                '& .MuiAlert-icon': { color: config.color },
              }}
            >
              {config.description}
            </Alert>

            {/* Quick Actions */}
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                size="small"
                variant="outlined"
                onClick={() => selectAllInCategory(category)}
                sx={{ borderColor: config.color, color: config.color }}
              >
                בחר הכל
              </Button>
              <Button
                size="small"
                variant="outlined"
                onClick={() => deselectAllInCategory(category)}
                color="inherit"
              >
                בטל בחירה
              </Button>
            </Box>

            {/* Layers Tables - Grouped by File */}
            {fileLayersGroups.length > 0 ? (
              fileLayersGroups.map((fileGroup, fileIndex) => (
                <Box key={fileGroup.filename} sx={{ mb: fileIndex < fileLayersGroups.length - 1 ? 4 : 0 }}>
                  {/* File Header */}
                  <Box
                    sx={{
                      mb: 2,
                      p: 1.5,
                      bgcolor: alpha(config.color, 0.08),
                      borderRadius: 1,
                      border: `1px solid ${alpha(config.color, 0.2)}`,
                    }}
                  >
                    <Typography variant="subtitle1" fontWeight={600} color={config.color}>
                      קובץ: {fileGroup.filename}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {fileGroup.layers.length} שכבות | {formatAreaFull(fileGroup.layers.reduce((sum, l) => sum + l.area_m2, 0))} מ״ר
                    </Typography>
                  </Box>

                  {/* Layers Table for this file */}
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: '#f8fafc' }}>
                          <TableCell padding="checkbox" sx={{ width: 50 }}>
                            <Checkbox
                              indeterminate={
                                fileGroup.layers.some(l => selectedLayers.has(l.id)) &&
                                !fileGroup.layers.every(l => selectedLayers.has(l.id))
                              }
                              checked={fileGroup.layers.every(l => selectedLayers.has(l.id))}
                              onChange={() => {
                                const allSelected = fileGroup.layers.every(l => selectedLayers.has(l.id));
                                const newSet = new Set(selectedLayers);
                                fileGroup.layers.forEach(layer => {
                                  if (allSelected) {
                                    newSet.delete(layer.id);
                                  } else {
                                    newSet.add(layer.id);
                                  }
                                });
                                setSelectedLayers(newSet);
                              }}
                              sx={{ color: config.color, '&.Mui-checked': { color: config.color } }}
                            />
                          </TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>שם השכבה</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            שטח (מ״ר)
                          </TableCell>
                          <TableCell align="center" sx={{ fontWeight: 600 }}>
                            פוליליינים
                          </TableCell>
                          <TableCell align="center" sx={{ fontWeight: 600 }}>
                            האצ׳ים
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600, width: 100 }}>
                            % מהכלל
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {fileGroup.layers.map((layer) => {
                          const isSelected = selectedLayers.has(layer.id);
                          const areaPercentage = totalArea > 0 ? (layer.area_m2 / totalArea) * 100 : 0;

                          return (
                            <TableRow
                              key={layer.id}
                              hover
                              onClick={() => toggleLayer(layer.id)}
                              sx={{
                                cursor: 'pointer',
                                bgcolor: isSelected ? alpha(config.color, 0.05) : 'transparent',
                                '&:hover': { bgcolor: alpha(config.color, 0.08) },
                              }}
                            >
                              <TableCell padding="checkbox">
                                <Checkbox
                                  checked={isSelected}
                                  sx={{
                                    color: config.color,
                                    '&.Mui-checked': { color: config.color },
                                  }}
                                />
                              </TableCell>
                              <TableCell>
                                <Typography
                                  variant="body2"
                                  fontWeight={isSelected ? 600 : 400}
                                  sx={{
                                    fontFamily: 'monospace',
                                    fontSize: '0.9rem',
                                  }}
                                >
                                  {layer.layer_name}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Tooltip title={`${formatAreaFull(layer.area_m2)} מ״ר`} arrow>
                                  <Typography variant="body2" fontWeight={500}>
                                    {formatArea(layer.area_m2)}
                                  </Typography>
                                </Tooltip>
                              </TableCell>
                              <TableCell align="center">
                                <Typography variant="body2" color="text.secondary">
                                  {layer.polyline_count}
                                </Typography>
                              </TableCell>
                              <TableCell align="center">
                                <Typography variant="body2" color="text.secondary">
                                  {layer.hatch_count}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <LinearProgress
                                    variant="determinate"
                                    value={Math.min(areaPercentage, 100)}
                                    sx={{
                                      flexGrow: 1,
                                      height: 6,
                                      borderRadius: 3,
                                      bgcolor: alpha(config.color, 0.1),
                                      '& .MuiLinearProgress-bar': {
                                        bgcolor: config.color,
                                        borderRadius: 3,
                                      },
                                    }}
                                  />
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ minWidth: 35 }}
                                  >
                                    {areaPercentage.toFixed(1)}%
                                  </Typography>
                                </Box>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              ))
            ) : (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                אין שכבות בקטגוריה זו
              </Typography>
            )}
          </Box>
        </Collapse>
      </Paper>
    );
  };

  return (
    <Box sx={{ direction: 'rtl' }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          בחירת שכבות לחישוב כתב כמויות
        </Typography>
        <Typography variant="body1" color="text.secondary">
          בחר את השכבות שמכילות שטחי בנייה רלוונטיים. המערכת זיהתה אוטומטית שכבות בנייה וסימנה אותן.
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 2,
          mb: 3,
        }}
      >
        {/* Selected Area */}
        <Paper
          sx={{
            p: 2.5,
            textAlign: 'center',
            bgcolor: '#ecfdf5',
            border: '1px solid #a7f3d0',
            borderRadius: 2,
          }}
        >
          <SquareFootIcon sx={{ fontSize: 32, color: '#10b981', mb: 1 }} />
          <Typography variant="h4" fontWeight={700} color="#10b981">
            {formatAreaFull(selectedArea)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            מ״ר נבחרו לחישוב
          </Typography>
        </Paper>

        {/* Total Extracted */}
        <Paper
          sx={{
            p: 2.5,
            textAlign: 'center',
            bgcolor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: 2,
          }}
        >
          <LayersIcon sx={{ fontSize: 32, color: '#64748b', mb: 1 }} />
          <Typography variant="h4" fontWeight={700} color="#334155">
            {formatAreaFull(totalArea)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            מ״ר סה״כ חולצו
          </Typography>
        </Paper>

        {/* Selected Percentage */}
        <Paper
          sx={{
            p: 2.5,
            textAlign: 'center',
            bgcolor: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: 2,
          }}
        >
          <Box sx={{ position: 'relative', display: 'inline-flex', mb: 1 }}>
            <CircularProgress
              variant="determinate"
              value={selectedPercentage}
              size={48}
              thickness={4}
              sx={{ color: '#3b82f6' }}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="caption" fontWeight={600} color="#3b82f6">
                {selectedPercentage.toFixed(0)}%
              </Typography>
            </Box>
          </Box>
          <Typography variant="h6" fontWeight={600} color="#3b82f6">
            {selectedLayers.size} שכבות
          </Typography>
          <Typography variant="body2" color="text.secondary">
            נבחרו מתוך הכלל
          </Typography>
        </Paper>
      </Box>

      {/* Manual Override */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: '#fefce8', border: '1px solid #fef08a', borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Checkbox
            checked={useCustomArea}
            onChange={(e) => setUseCustomArea(e.target.checked)}
            sx={{ color: '#ca8a04', '&.Mui-checked': { color: '#ca8a04' } }}
          />
          <Typography variant="body1" fontWeight={500}>
            הזן שטח ידנית (מבטל את בחירת השכבות)
          </Typography>
          {useCustomArea && (
            <TextField
              type="number"
              label="שטח במ״ר"
              value={customArea}
              onChange={(e) => setCustomArea(e.target.value)}
              size="small"
              sx={{ width: 200, ml: 2 }}
              InputProps={{
                endAdornment: <Typography color="text.secondary">מ״ר</Typography>,
              }}
            />
          )}
        </Box>
      </Paper>

      <Divider sx={{ my: 3 }} />

      {/* Layer Categories */}
      <Typography variant="h6" fontWeight={600} gutterBottom>
        שכבות לפי קטגוריה
      </Typography>

      {renderCategorySection('include')}
      {renderCategorySection('review')}
      {renderCategorySection('exclude')}

      {/* Confirm Button */}
      <Box
        sx={{
          mt: 4,
          p: 3,
          bgcolor: '#f8fafc',
          borderRadius: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box>
          <Typography variant="body1" fontWeight={500}>
            שטח סופי לחישוב:
          </Typography>
          <Typography variant="h5" fontWeight={700} color="primary">
            {useCustomArea && customArea
              ? formatAreaFull(parseFloat(customArea))
              : formatAreaFull(selectedArea)}{' '}
            מ״ר
          </Typography>
        </Box>
        <Button
          variant="contained"
          size="large"
          onClick={handleConfirm}
          disabled={submitting || (!useCustomArea && selectedLayers.size === 0)}
          sx={{
            px: 4,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            bgcolor: '#10b981',
            '&:hover': { bgcolor: '#059669' },
          }}
        >
          {submitting ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            'אשר והמשך ליצירת כתב כמויות'
          )}
        </Button>
      </Box>
    </Box>
  );
}
