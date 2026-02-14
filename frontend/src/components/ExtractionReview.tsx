'use client';

import { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Checkbox, FormControlLabel, LinearProgress, Alert, alpha,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip,
} from '@mui/material';
import { CheckCircle as CheckIcon, PlayArrow as PlayIcon } from '@mui/icons-material';
import api from '@/utils/axios';

interface ExtractionFile {
  plan_id: number;
  filename: string;
  area_m2?: number;
  layers_count?: number;
  selected?: boolean;
}

interface ExtractionReviewProps {
  projectId: number;
  onConfirm: () => void;
}

export default function ExtractionReview({ projectId, onConfirm }: ExtractionReviewProps) {
  const [files, setFiles] = useState<ExtractionFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  useEffect(() => {
    const fetchExtraction = async () => {
      try {
        const response = await api.get(`/projects/${projectId}/extraction`);
        const extractedFiles = response.data.files.map((f: any) => ({
          plan_id: f.plan_id,
          filename: f.filename,
          area_m2: f.area_m2,
          layers_count: f.extraction_data?.layers_count || 0,
          selected: true,
        }));
        setFiles(extractedFiles);
        setSelectedIds(extractedFiles.map((f: ExtractionFile) => f.plan_id));
      } catch (error) {
        console.error('Failed to fetch extraction data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchExtraction();
  }, [projectId]);

  const toggleFile = (planId: number) => {
    setSelectedIds((prev) =>
      prev.includes(planId) ? prev.filter((id) => id !== planId) : [...prev, planId]
    );
  };

  const handleConfirm = async () => {
    try {
      setSubmitting(true);
      await api.post(`/projects/${projectId}/generate-boq`, { plan_ids: selectedIds });
      onConfirm();
    } catch (error) {
      console.error('Failed to generate BOQ', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
        בחירת קבצים ליצירת כתב כמויות
      </Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        בחר את הקבצים שברצונך לכלול בכתב הכמויות. ניתן לבטל בחירה של קבצים לא רלוונטיים.
      </Alert>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>שם קובץ</TableCell>
              <TableCell align="right">שטח (מ"ר)</TableCell>
              <TableCell align="right">שכבות</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {files.map((file) => (
              <TableRow key={file.plan_id}>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedIds.includes(file.plan_id)}
                    onChange={() => toggleFile(file.plan_id)}
                  />
                </TableCell>
                <TableCell>{file.filename}</TableCell>
                <TableCell align="right">{file.area_m2?.toLocaleString('he-IL') || '-'}</TableCell>
                <TableCell align="right">{file.layers_count || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Chip label={`${selectedIds.length} מתוך ${files.length} קבצים נבחרו`} color="primary" variant="outlined" />
        <Button
          variant="contained"
          startIcon={submitting ? null : <PlayIcon />}
          onClick={handleConfirm}
          disabled={submitting || selectedIds.length === 0}
          sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)' }}
        >
          {submitting ? 'מייצר כתב כמויות...' : 'צור כתב כמויות'}
        </Button>
      </Box>
    </Box>
  );
}
