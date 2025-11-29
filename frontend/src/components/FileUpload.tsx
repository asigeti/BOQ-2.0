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
import { motion, AnimatePresence } from 'framer-motion';
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
      return <CadIcon sx={{ fontSize: 40, color: '#6366f1' }} />;
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

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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

    try {
      const response = await api.post('/plans/upload', formData, {
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

      setSuccess(`הקובץ ${selectedFile.name} הועלה בהצלחה!`);
      setSelectedFile(null);
      onUploadSuccess(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'העלאת הקובץ נכשלה');
    } finally {
      setUploading(false);
      setProgress(0);
    }
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Box
          {...getRootProps()}
          sx={{
            position: 'relative',
            border: '2px dashed',
            borderColor: isDragActive
              ? 'primary.main'
              : isDragAccept
              ? 'success.main'
              : 'grey.300',
            borderRadius: 3,
            p: 6,
            textAlign: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer',
            backgroundColor: isDragActive
              ? alpha('#6366f1', 0.08)
              : 'background.paper',
            transition: 'all 0.3s ease-in-out',
            overflow: 'hidden',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: alpha('#6366f1', 0.04),
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
              opacity: isDragActive ? 0.1 : 0,
              background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
              transition: 'opacity 0.3s ease-in-out',
              pointerEvents: 'none',
            }}
          />

          <AnimatePresence mode="wait">
            {!selectedFile ? (
              <motion.div
                key="dropzone"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div
                  animate={{
                    y: isDragActive ? -10 : 0,
                    scale: isDragActive ? 1.1 : 1,
                  }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      mx: 'auto',
                      mb: 3,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 10px 40px -10px rgba(99, 102, 241, 0.5)',
                    }}
                  >
                    <CloudUploadIcon sx={{ fontSize: 40, color: 'white' }} />
                  </Box>
                </motion.div>

                <Typography variant="h5" fontWeight={600} gutterBottom>
                  {isDragActive ? 'שחרר את הקובץ כאן' : 'גרור ושחרר קובץ תכנית'}
                </Typography>

                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  או לחץ לבחירת קובץ מהמחשב
                </Typography>

                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Chip
                    label="DWG"
                    size="small"
                    sx={{ backgroundColor: alpha('#6366f1', 0.1), color: '#6366f1' }}
                  />
                  <Chip
                    label="DXF"
                    size="small"
                    sx={{ backgroundColor: alpha('#6366f1', 0.1), color: '#6366f1' }}
                  />
                  <Chip
                    label="PDF"
                    size="small"
                    sx={{ backgroundColor: alpha('#ef4444', 0.1), color: '#ef4444' }}
                  />
                  <Chip
                    label="Images"
                    size="small"
                    sx={{ backgroundColor: alpha('#10b981', 0.1), color: '#10b981' }}
                  />
                </Box>
              </motion.div>
            ) : (
              <motion.div
                key="file-preview"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
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
                      borderRadius: 2,
                      backgroundColor: alpha('#64748b', 0.08),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {getFileIcon(selectedFile.name)}
                  </Box>

                  <Box sx={{ textAlign: 'right', flex: 1 }}>
                    <Typography variant="h6" fontWeight={600}>
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(selectedFile.size)}
                    </Typography>
                  </Box>

                  <IconButton
                    onClick={(e) => {
                      e.stopPropagation();
                      clearFile();
                    }}
                    sx={{
                      backgroundColor: alpha('#ef4444', 0.1),
                      '&:hover': {
                        backgroundColor: alpha('#ef4444', 0.2),
                      },
                    }}
                  >
                    <CloseIcon sx={{ color: '#ef4444' }} />
                  </IconButton>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Box>
      </motion.div>

      {/* Progress Bar */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  מעלה קובץ...
                </Typography>
                <Typography variant="body2" fontWeight={600} color="primary">
                  {progress}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 10,
                  borderRadius: 5,
                }}
              />
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Button */}
      <AnimatePresence>
        {selectedFile && !uploading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            <Box
              component="button"
              onClick={handleUpload}
              sx={{
                width: '100%',
                mt: 3,
                py: 2,
                px: 4,
                border: 'none',
                borderRadius: 2,
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: 'white',
                fontSize: '1.1rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.3s ease-in-out',
                boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.4)',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 20px 0 rgba(99, 102, 241, 0.5)',
                },
                '&:active': {
                  transform: 'translateY(0)',
                },
              }}
            >
              העלאה ויצירת כתב כמויות
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Alerts */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
          >
            <Alert
              severity="error"
              sx={{ mt: 3, borderRadius: 2 }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
          >
            <Alert
              severity="success"
              icon={<CheckCircleIcon />}
              sx={{ mt: 3, borderRadius: 2 }}
              onClose={() => setSuccess(null)}
            >
              {success}
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}
