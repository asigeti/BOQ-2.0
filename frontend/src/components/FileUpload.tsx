'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  LinearProgress,
  Alert,
  alpha,
  Chip,
  IconButton,
  Collapse,
  Fade,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Description as PdfIcon,
  Image as ImageIcon,
  Architecture as CadIcon,
} from '@mui/icons-material';
import api from '@/utils/axios';

interface FileUploadProps {
  onUploadSuccess: (data?: any) => void;
}

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return <PdfIcon sx={{ fontSize: 40, color: '#ef4444' }} />;
    case 'dwg':
    case 'dxf':
      return <CadIcon sx={{ fontSize: 40, color: '#0ea5e9' }} />;
    case 'png':
    case 'jpg':
    case 'jpeg':
      return <ImageIcon sx={{ fontSize: 40, color: '#10b981' }} />;
    default:
      return <FileIcon sx={{ fontSize: 40, color: '#64748b' }} />;
  }
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

// Plan types for PDF extraction
const PLAN_TYPES = [
  { value: 'boq_table', label: '📋 כתב כמויות (טבלה)', label_en: 'BOQ Document' },
  { value: 'architectural', label: 'תכנית אדריכלית / בנייה', label_en: 'Architectural' },
  { value: 'electrical', label: 'תכנית חשמל', label_en: 'Electrical' },
  { value: 'plumbing', label: 'תכנית אינסטלציה', label_en: 'Plumbing' },
  { value: 'structural', label: 'תכנית קונסטרוקציה', label_en: 'Structural' },
  { value: 'hvac', label: 'תכנית מיזוג אוויר', label_en: 'HVAC' },
  { value: 'windows_doors', label: 'לוח חלונות ודלתות', label_en: 'Windows & Doors' },
  { value: 'finishing', label: 'תכנית גמרים', label_en: 'Finishing' },
  { value: 'landscape', label: 'תכנית גינון', label_en: 'Landscape' },
  { value: 'site_development', label: 'תכנית פיתוח (גרפית)', label_en: 'Site Development' },
  { value: 'general', label: 'תכנית כללית', label_en: 'General' },
];

const isPdfFile = (filename: string) => {
  return filename.toLowerCase().endsWith('.pdf');
};

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [planType, setPlanType] = useState<string>('boq_table');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setSelectedFile(file);
    setError(null);
    setSuccess(null);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Build URL with plan_type query parameter for PDF files
    const isPdf = isPdfFile(selectedFile.name);
    const uploadUrl = isPdf
      ? `/plans/upload?plan_type=${encodeURIComponent(planType)}`
      : '/plans/upload';

    try {
      const response = await api.post(uploadUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setProgress(percent);
        },
      });

      const planTypeLabel = isPdf
        ? PLAN_TYPES.find(p => p.value === planType)?.label || planType
        : '';
      setSuccess(`הקובץ ${selectedFile.name} הועלה בהצלחה!${isPdf ? ` (סוג: ${planTypeLabel})` : ''}`);
      setSelectedFile(null);
      setPlanType('boq_table');
      onUploadSuccess(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'העלאת הקובץ נכשלה');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handlePlanTypeChange = (event: SelectChangeEvent<string>) => {
    setPlanType(event.target.value);
  };

  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
    setSuccess(null);
  };

  const { getRootProps, getInputProps, isDragActive, isDragAccept } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/acad': ['.dwg', '.dxf'],
      'application/dxf': ['.dxf'],
      'application/x-autocad': ['.dwg'],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <Box>
      {/* Dropzone */}
      <Box
        sx={{
          animation: 'fadeInUp 0.4s ease-out forwards',
          '@keyframes fadeInUp': {
            '0%': { opacity: 0, transform: 'translateY(20px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box
          {...getRootProps()}
          sx={{
            position: 'relative',
            border: '2px dashed',
            borderColor: isDragActive
              ? '#0ea5e9'
              : isDragAccept
              ? '#10b981'
              : 'rgba(148, 163, 184, 0.3)',
            borderRadius: '20px',
            p: 6,
            textAlign: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer',
            backgroundColor: isDragActive
              ? 'rgba(14, 165, 233, 0.1)'
              : 'rgba(15, 23, 42, 0.5)',
            transition: 'all 0.3s ease-in-out',
            overflow: 'hidden',
            backdropFilter: 'blur(10px)',
            '&:hover': {
              borderColor: '#0ea5e9',
              backgroundColor: 'rgba(14, 165, 233, 0.08)',
            },
          }}
        >
          <input {...getInputProps()} />

          {/* Animated background gradient */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: isDragActive ? 0.15 : 0,
              background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
              transition: 'opacity 0.3s ease-in-out',
              pointerEvents: 'none',
            }}
          />

          {!selectedFile ? (
            <Fade in={true} timeout={300}>
              <Box>
                <Box
                  sx={{
                    transform: isDragActive ? 'translateY(-10px) scale(1.1)' : 'translateY(0) scale(1)',
                    transition: 'transform 0.3s ease-in-out',
                  }}
                >
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      mx: 'auto',
                      mb: 3,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 10px 40px -10px rgba(14, 165, 233, 0.5)',
                    }}
                  >
                    <CloudUploadIcon sx={{ fontSize: 40, color: 'white' }} />
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
                  {isDragActive ? 'שחרר את הקובץ כאן' : 'גרור ושחרר קובץ תכנית'}
                </Typography>

                <Typography
                  variant="body1"
                  sx={{ color: '#64748b', mb: 3 }}
                >
                  או לחץ לבחירת קובץ מהמחשב
                </Typography>

                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Chip
                    label="DWG"
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(14, 165, 233, 0.15)',
                      color: '#0ea5e9',
                      border: '1px solid rgba(14, 165, 233, 0.3)',
                      fontWeight: 600,
                    }}
                  />
                  <Chip
                    label="DXF"
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(14, 165, 233, 0.15)',
                      color: '#0ea5e9',
                      border: '1px solid rgba(14, 165, 233, 0.3)',
                      fontWeight: 600,
                    }}
                  />
                  <Chip
                    label="PDF"
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(239, 68, 68, 0.15)',
                      color: '#ef4444',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      fontWeight: 600,
                    }}
                  />
                  <Chip
                    label="Images"
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      color: '#10b981',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      fontWeight: 600,
                    }}
                  />
                </Box>
              </Box>
            </Fade>
          ) : (
            <Fade in={true} timeout={300}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 3,
                }}
              >
                <Box
                  sx={{
                    width: 70,
                    height: 70,
                    borderRadius: '16px',
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {getFileIcon(selectedFile.name)}
                </Box>

                <Box sx={{ textAlign: 'right', flex: 1 }}>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 600, color: '#f1f5f9' }}
                  >
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748b' }}>
                    {formatFileSize(selectedFile.size)}
                  </Typography>
                </Box>

                <IconButton
                  onClick={(e) => {
                    e.stopPropagation();
                    clearFile();
                  }}
                  sx={{
                    width: 40,
                    height: 40,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      backgroundColor: 'rgba(239, 68, 68, 0.2)',
                      transform: 'scale(1.1)',
                    },
                  }}
                >
                  <CloseIcon sx={{ color: '#ef4444' }} />
                </IconButton>
              </Box>
            </Fade>
          )}
        </Box>
      </Box>

      {/* Plan Type Selector - Only for PDF files */}
      <Collapse in={!!selectedFile && isPdfFile(selectedFile.name) && !uploading}>
        <Box
          sx={{
            mt: 3,
            p: 3,
            borderRadius: '16px',
            backgroundColor: 'rgba(14, 165, 233, 0.08)',
            border: '1px solid rgba(14, 165, 233, 0.2)',
          }}
        >
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 700,
              color: '#0ea5e9',
              mb: 1,
            }}
          >
            📋 בחר סוג תכנית
          </Typography>
          <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>
            בחירת סוג התכנית תעזור לחילוץ מדויק יותר של כמויות מקובץ ה-PDF
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel
              id="plan-type-label"
              sx={{
                color: '#64748b',
                '&.Mui-focused': {
                  color: '#0ea5e9',
                },
              }}
            >
              סוג תכנית
            </InputLabel>
            <Select
              labelId="plan-type-label"
              value={planType}
              label="סוג תכנית"
              onChange={handlePlanTypeChange}
              sx={{
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                color: '#f1f5f9',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(14, 165, 233, 0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#0ea5e9',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#0ea5e9',
                },
                '& .MuiSelect-icon': {
                  color: '#64748b',
                },
              }}
              MenuProps={{
                PaperProps: {
                  sx: {
                    backgroundColor: '#0f172a',
                    border: '1px solid rgba(148, 163, 184, 0.1)',
                    borderRadius: '12px',
                    boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.5)',
                    '& .MuiMenuItem-root': {
                      color: '#f1f5f9',
                      '&:hover': {
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                      },
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(14, 165, 233, 0.2)',
                        '&:hover': {
                          backgroundColor: 'rgba(14, 165, 233, 0.25)',
                        },
                      },
                    },
                  },
                },
              }}
            >
              {PLAN_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Typography sx={{ color: '#f1f5f9' }}>{type.label}</Typography>
                    <Typography variant="body2" sx={{ color: '#64748b', ml: 2 }}>
                      {type.label_en}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Collapse>

      {/* Progress Bar */}
      <Collapse in={uploading}>
        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ color: '#94a3b8' }}>
              מעלה קובץ...
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 700,
                color: '#0ea5e9',
              }}
            >
              {progress}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progress}
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
      </Collapse>

      {/* Upload Button */}
      <Collapse in={!!selectedFile && !uploading}>
        <Box
          component="button"
          onClick={handleUpload}
          sx={{
            width: '100%',
            mt: 3,
            py: 2,
            px: 4,
            border: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
            color: 'white',
            fontSize: '1.1rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.3s ease-in-out',
            boxShadow: '0 8px 32px rgba(14, 165, 233, 0.4)',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 12px 40px rgba(14, 165, 233, 0.5)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
          }}
        >
          העלאה ויצירת כתב כמויות
        </Box>
      </Collapse>

      {/* Error Alert */}
      <Collapse in={!!error}>
        <Alert
          severity="error"
          sx={{
            mt: 3,
            borderRadius: '12px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            '& .MuiAlert-icon': {
              color: '#ef4444',
            },
            '& .MuiAlert-message': {
              color: '#f1f5f9',
            },
          }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      </Collapse>

      {/* Success Alert */}
      <Collapse in={!!success}>
        <Alert
          severity="success"
          icon={<CheckCircleIcon />}
          sx={{
            mt: 3,
            borderRadius: '12px',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            '& .MuiAlert-icon': {
              color: '#10b981',
            },
            '& .MuiAlert-message': {
              color: '#f1f5f9',
            },
          }}
          onClose={() => setSuccess(null)}
        >
          {success}
        </Alert>
      </Collapse>
    </Box>
  );
}
