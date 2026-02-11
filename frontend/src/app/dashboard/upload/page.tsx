'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  Box,
  Typography,
  Card,
  CardContent,
  alpha,
  Alert,
  Collapse,
} from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { MainLayout } from '@/components/layout';
import FileUpload from '@/components/FileUpload';

const Header = dynamic(() => import('@/components/layout/Header'), { ssr: false });

export default function UploadPage() {
  const router = useRouter();
  const [uploadResult, setUploadResult] = useState<any>(null);

  const handleUploadSuccess = (data: any) => {
    setUploadResult(data);
    // Navigate to the plan details page if we have an ID
    if (data?.id) {
      setTimeout(() => {
        router.push(`/dashboard/plans/${data.id}`);
      }, 1500);
    }
  };

  return (
    <MainLayout>
      <Header title="העלאת קובץ" subtitle="העלה תוכנית DWG או PDF ליצירת כתב כמויות אוטומטי" />

      <Box sx={{ maxWidth: 800, mx: 'auto' }}>
        {/* Upload Card */}
        <Card
          sx={{
            backgroundColor: 'rgba(15, 23, 42, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            borderRadius: '24px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </CardContent>
        </Card>

        {/* Success Message with Navigation */}
        <Collapse in={!!uploadResult}>
          <Alert
            severity="success"
            icon={<CheckCircleIcon />}
            sx={{
              mt: 3,
              borderRadius: '16px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              '& .MuiAlert-icon': {
                color: '#10b981',
              },
              '& .MuiAlert-message': {
                width: '100%',
                color: '#f1f5f9',
              },
            }}
          >
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 600,
                color: '#f1f5f9',
              }}
            >
              הקובץ הועלה בהצלחה!
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8' }}>
              מעבר אוטומטי לדף כתב הכמויות...
            </Typography>
          </Alert>
        </Collapse>

        {/* Instructions */}
        <Box sx={{ mt: 4 }}>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: '#f1f5f9',
              mb: 2,
            }}
          >
            סוגי קבצים נתמכים
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 3,
                borderRadius: '16px',
                backgroundColor: 'rgba(14, 165, 233, 0.08)',
                border: '1px solid rgba(14, 165, 233, 0.2)',
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: 'rgba(14, 165, 233, 0.12)',
                  borderColor: 'rgba(14, 165, 233, 0.3)',
                },
              }}
            >
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)',
                  border: '1px solid rgba(14, 165, 233, 0.3)',
                  fontWeight: 800,
                  color: '#0ea5e9',
                  fontSize: '0.9rem',
                }}
              >
                DWG
              </Box>
              <Box>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 600,
                    color: '#f1f5f9',
                  }}
                >
                  קבצי AutoCAD
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>
                  תוכניות DWG עם בלוקים וטקסט
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 3,
                borderRadius: '16px',
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: 'rgba(239, 68, 68, 0.12)',
                  borderColor: 'rgba(239, 68, 68, 0.3)',
                },
              }}
            >
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  fontWeight: 800,
                  color: '#ef4444',
                  fontSize: '0.9rem',
                }}
              >
                PDF
              </Box>
              <Box>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 600,
                    color: '#f1f5f9',
                  }}
                >
                  קבצי PDF
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748b' }}>
                  תוכניות סרוקות או מיוצאות
                </Typography>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </MainLayout>
  );
}
