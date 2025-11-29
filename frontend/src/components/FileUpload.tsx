'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper, LinearProgress, Alert } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import api from '@/utils/axios';

interface FileUploadProps {
    onUploadSuccess: () => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post('/plans/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setSuccess(`הקובץ ${file.name} הועלה בהצלחה`);
            onUploadSuccess();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'העלאת הקובץ נכשלה');
        } finally {
            setUploading(false);
        }
    }, [onUploadSuccess]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'image/*': ['.png', '.jpg', '.jpeg'],
            'application/acad': ['.dwg', '.dxf'],
        },
        multiple: false,
    });

    return (
        <Paper
            variant="outlined"
            sx={{
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? '#f0f9ff' : 'transparent',
                borderStyle: 'dashed',
            }}
            {...getRootProps()}
        >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
                {isDragActive ? 'שחרר את הקבצים כאן ...' : 'גרור ושחרר תוכנית כאן, או לחץ לבחירה'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
                תומך ב-PDF, DWG, DXF, תמונות
            </Typography>

            {uploading && (
                <Box sx={{ width: '100%', mt: 2 }}>
                    <LinearProgress />
                </Box>
            )}

            {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mt: 2 }}>
                    {success}
                </Alert>
            )}
        </Paper>
    );
}
