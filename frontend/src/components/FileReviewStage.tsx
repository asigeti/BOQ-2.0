'use client';

import { useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Button,
    IconButton,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    CircularProgress,
    alpha,
} from '@mui/material';
import {
    Delete as DeleteIcon,
    PlayArrow as PlayIcon,
    Description as FileIcon,
    Warning as WarningIcon,
    Folder as FolderIcon,
} from '@mui/icons-material';
import api from '@/utils/axios';
import { useNotification } from '@/contexts/NotificationContext';

interface Plan {
    id: number;
    filename: string;
    file_type: string;
    file_size?: number;
}

interface FileReviewStageProps {
    projectId: number;
    files: Plan[];
    onStartProcessing: () => void;
    onFilesChanged: () => void;
}

// Common dialog styles
const dialogPaperStyles = {
    backgroundColor: '#0f172a',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: '20px',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(20px)',
};

export default function FileReviewStage({
    projectId,
    files,
    onStartProcessing,
    onFilesChanged,
}: FileReviewStageProps) {
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [fileToDelete, setFileToDelete] = useState<Plan | null>(null);
    const [deleting, setDeleting] = useState(false);
    const [starting, setStarting] = useState(false);
    const { showError, showSuccess } = useNotification();

    const handleDeleteClick = (file: Plan) => {
        setFileToDelete(file);
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!fileToDelete) return;

        try {
            setDeleting(true);
            await api.delete(`/projects/${projectId}/plans/${fileToDelete.id}`);
            showSuccess(`קובץ ${fileToDelete.filename} נמחק בהצלחה`);
            setDeleteDialogOpen(false);
            setFileToDelete(null);
            onFilesChanged(); // Refresh file list
        } catch (error: any) {
            showError(error.response?.data?.detail || 'שגיאה במחיקת הקובץ');
        } finally {
            setDeleting(false);
        }
    };

    const handleStartProcessing = async () => {
        try {
            setStarting(true);
            await api.post(`/projects/${projectId}/process`);
            onStartProcessing();
        } catch (error: any) {
            showError(error.response?.data?.detail || 'שגיאה בהתחלת העיבוד');
            setStarting(false);
        }
    };

    const formatFileSize = (bytes?: number) => {
        if (!bytes) return 'לא ידוע';
        const mb = bytes / (1024 * 1024);
        return `${mb.toFixed(2)} MB`;
    };

    const getFileTypeColor = (fileType: string) => {
        const type = fileType.toLowerCase();
        if (type.includes('pdf')) return '#ef4444';
        if (type.includes('dwg') || type.includes('dxf')) return '#0ea5e9';
        if (type.includes('xls') || type.includes('csv')) return '#10b981';
        return '#8b5cf6';
    };

    return (
        <Card
            sx={{
                backgroundColor: 'rgba(15, 23, 42, 0.8)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                borderRadius: '20px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
            }}
        >
            <CardContent sx={{ p: 3 }}>
                {/* Header */}
                <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Box
                            sx={{
                                width: 44,
                                height: 44,
                                borderRadius: '12px',
                                background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)',
                                border: '1px solid rgba(14, 165, 233, 0.3)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <FolderIcon sx={{ color: '#0ea5e9', fontSize: 24 }} />
                        </Box>
                        <Box>
                            <Typography
                                variant="h6"
                                sx={{
                                    fontWeight: 700,
                                    color: '#f1f5f9',
                                    fontSize: '1.1rem',
                                }}
                            >
                                סקירת קבצים
                            </Typography>
                            <Typography
                                variant="body2"
                                sx={{ color: '#64748b', fontSize: '0.85rem' }}
                            >
                                בדוק את הקבצים שנסרקו. תוכל למחוק קבצים לא רצויים לפני תחילת העיבוד.
                            </Typography>
                        </Box>
                    </Box>
                </Box>

                {files.length === 0 ? (
                    <Alert
                        severity="warning"
                        icon={<WarningIcon />}
                        sx={{
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            borderRadius: '12px',
                            '& .MuiAlert-icon': {
                                color: '#f59e0b',
                            },
                            '& .MuiAlert-message': {
                                color: '#f1f5f9',
                            },
                        }}
                    >
                        לא נמצאו קבצים. העלה קבצים כדי להמשיך.
                    </Alert>
                ) : (
                    <>
                        <TableContainer
                            sx={{
                                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                                borderRadius: '12px',
                                border: '1px solid rgba(148, 163, 184, 0.1)',
                            }}
                        >
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell
                                            sx={{
                                                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                                                color: '#64748b',
                                                fontWeight: 600,
                                                fontSize: '0.8rem',
                                            }}
                                        >
                                            שם קובץ
                                        </TableCell>
                                        <TableCell
                                            sx={{
                                                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                                                color: '#64748b',
                                                fontWeight: 600,
                                                fontSize: '0.8rem',
                                            }}
                                        >
                                            סוג
                                        </TableCell>
                                        <TableCell
                                            sx={{
                                                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                                                color: '#64748b',
                                                fontWeight: 600,
                                                fontSize: '0.8rem',
                                            }}
                                        >
                                            גודל
                                        </TableCell>
                                        <TableCell
                                            align="left"
                                            sx={{
                                                borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                                                color: '#64748b',
                                                fontWeight: 600,
                                                fontSize: '0.8rem',
                                            }}
                                        >
                                            פעולות
                                        </TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {files.map((file, index) => {
                                        const typeColor = getFileTypeColor(file.file_type);
                                        return (
                                            <TableRow
                                                key={file.id}
                                                sx={{
                                                    '&:hover': {
                                                        backgroundColor: 'rgba(14, 165, 233, 0.05)',
                                                    },
                                                    animation: 'fadeInUp 0.4s ease-out forwards',
                                                    animationDelay: `${index * 0.05}s`,
                                                    opacity: 0,
                                                    '@keyframes fadeInUp': {
                                                        '0%': { opacity: 0, transform: 'translateY(10px)' },
                                                        '100%': { opacity: 1, transform: 'translateY(0)' },
                                                    },
                                                }}
                                            >
                                                <TableCell
                                                    sx={{
                                                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                                        color: '#f1f5f9',
                                                    }}
                                                >
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                                                        <Box
                                                            sx={{
                                                                width: 32,
                                                                height: 32,
                                                                borderRadius: '8px',
                                                                backgroundColor: alpha(typeColor, 0.1),
                                                                border: `1px solid ${alpha(typeColor, 0.3)}`,
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                            }}
                                                        >
                                                            <FileIcon sx={{ fontSize: 16, color: typeColor }} />
                                                        </Box>
                                                        <Typography
                                                            sx={{
                                                                fontSize: '0.85rem',
                                                                fontWeight: 500,
                                                                color: '#f1f5f9',
                                                            }}
                                                        >
                                                            {file.filename}
                                                        </Typography>
                                                    </Box>
                                                </TableCell>
                                                <TableCell
                                                    sx={{
                                                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                                    }}
                                                >
                                                    <Chip
                                                        label={file.file_type.toUpperCase()}
                                                        size="small"
                                                        sx={{
                                                            backgroundColor: alpha(typeColor, 0.15),
                                                            color: typeColor,
                                                            border: `1px solid ${alpha(typeColor, 0.3)}`,
                                                            fontWeight: 600,
                                                            fontSize: '0.65rem',
                                                            height: 24,
                                                        }}
                                                    />
                                                </TableCell>
                                                <TableCell
                                                    sx={{
                                                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                                        color: '#94a3b8',
                                                        fontSize: '0.85rem',
                                                    }}
                                                >
                                                    {formatFileSize(file.file_size)}
                                                </TableCell>
                                                <TableCell
                                                    align="left"
                                                    sx={{
                                                        borderBottom: '1px solid rgba(148, 163, 184, 0.05)',
                                                    }}
                                                >
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleDeleteClick(file)}
                                                        sx={{
                                                            width: 32,
                                                            height: 32,
                                                            color: '#64748b',
                                                            backgroundColor: 'rgba(148, 163, 184, 0.08)',
                                                            border: '1px solid rgba(148, 163, 184, 0.1)',
                                                            transition: 'all 0.2s ease',
                                                            '&:hover': {
                                                                color: '#ef4444',
                                                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                                                borderColor: 'rgba(239, 68, 68, 0.3)',
                                                                transform: 'scale(1.1)',
                                                            },
                                                        }}
                                                    >
                                                        <DeleteIcon sx={{ fontSize: 16 }} />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </TableContainer>

                        <Box
                            sx={{
                                mt: 3,
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}
                        >
                            <Box
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    px: 2,
                                    py: 1,
                                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                                    borderRadius: '10px',
                                    border: '1px solid rgba(14, 165, 233, 0.2)',
                                }}
                            >
                                <Typography
                                    sx={{
                                        fontSize: '0.85rem',
                                        color: '#94a3b8',
                                    }}
                                >
                                    סה"כ
                                </Typography>
                                <Typography
                                    sx={{
                                        fontSize: '1rem',
                                        fontWeight: 700,
                                        color: '#0ea5e9',
                                    }}
                                >
                                    {files.length}
                                </Typography>
                                <Typography
                                    sx={{
                                        fontSize: '0.85rem',
                                        color: '#94a3b8',
                                    }}
                                >
                                    קבצים מוכנים לעיבוד
                                </Typography>
                            </Box>
                            <Button
                                variant="contained"
                                size="large"
                                startIcon={
                                    starting ? (
                                        <CircularProgress size={20} sx={{ color: 'inherit' }} />
                                    ) : (
                                        <PlayIcon />
                                    )
                                }
                                onClick={handleStartProcessing}
                                disabled={starting || files.length === 0}
                                sx={{
                                    px: 4,
                                    py: 1.5,
                                    fontSize: '1rem',
                                    fontWeight: 700,
                                    borderRadius: '14px',
                                    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                                    boxShadow: '0 8px 32px rgba(14, 165, 233, 0.3)',
                                    textTransform: 'none',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                                        boxShadow: '0 12px 40px rgba(14, 165, 233, 0.4)',
                                        transform: 'translateY(-2px)',
                                    },
                                    '&:disabled': {
                                        background: 'rgba(148, 163, 184, 0.2)',
                                        color: 'rgba(148, 163, 184, 0.5)',
                                    },
                                }}
                            >
                                {starting ? 'מתחיל עיבוד...' : 'התחל עיבוד'}
                            </Button>
                        </Box>
                    </>
                )}
            </CardContent>

            {/* Delete Confirmation Dialog */}
            <Dialog
                open={deleteDialogOpen}
                onClose={() => !deleting && setDeleteDialogOpen(false)}
                PaperProps={{ sx: dialogPaperStyles }}
            >
                <DialogTitle
                    sx={{
                        color: '#f1f5f9',
                        fontWeight: 700,
                        fontSize: '1.2rem',
                        borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                        pb: 2,
                    }}
                >
                    מחיקת קובץ
                </DialogTitle>
                <DialogContent sx={{ pt: 3 }}>
                    <Typography sx={{ color: '#94a3b8', fontSize: '0.95rem' }}>
                        האם אתה בטוח שברצונך למחוק את הקובץ{' '}
                        <Box
                            component="span"
                            sx={{
                                color: '#0ea5e9',
                                fontWeight: 600,
                            }}
                        >
                            {fileToDelete?.filename}
                        </Box>
                        ?
                    </Typography>
                    <Alert
                        severity="warning"
                        sx={{
                            mt: 2,
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                            borderRadius: '12px',
                            '& .MuiAlert-icon': {
                                color: '#f59e0b',
                            },
                            '& .MuiAlert-message': {
                                color: '#f1f5f9',
                            },
                        }}
                    >
                        פעולה זו אינה ניתנת לביטול.
                    </Alert>
                </DialogContent>
                <DialogActions sx={{ p: 3, pt: 2, gap: 1.5 }}>
                    <Button
                        onClick={() => setDeleteDialogOpen(false)}
                        disabled={deleting}
                        sx={{
                            px: 3,
                            py: 1,
                            color: '#94a3b8',
                            borderRadius: '10px',
                            textTransform: 'none',
                            fontWeight: 600,
                            '&:hover': {
                                backgroundColor: 'rgba(148, 163, 184, 0.1)',
                            },
                        }}
                    >
                        ביטול
                    </Button>
                    <Button
                        onClick={handleDeleteConfirm}
                        variant="contained"
                        disabled={deleting}
                        startIcon={
                            deleting ? (
                                <CircularProgress size={16} sx={{ color: 'inherit' }} />
                            ) : (
                                <DeleteIcon />
                            )
                        }
                        sx={{
                            px: 3,
                            py: 1,
                            borderRadius: '10px',
                            textTransform: 'none',
                            fontWeight: 600,
                            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                            boxShadow: '0 4px 16px rgba(239, 68, 68, 0.3)',
                            '&:hover': {
                                background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                                boxShadow: '0 6px 20px rgba(239, 68, 68, 0.4)',
                            },
                            '&:disabled': {
                                background: 'rgba(148, 163, 184, 0.2)',
                                color: 'rgba(148, 163, 184, 0.5)',
                            },
                        }}
                    >
                        {deleting ? 'מוחק...' : 'מחק'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Card>
    );
}
