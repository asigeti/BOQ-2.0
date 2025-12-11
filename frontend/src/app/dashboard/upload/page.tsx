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
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.02) 0%, rgba(6, 182, 212, 0.02) 100%)',
            border: '1px solid',
            borderColor: 'divider',
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
              borderRadius: 2,
              '& .MuiAlert-message': {
                width: '100%',
              },
            }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              הקובץ הועלה בהצלחה!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              מעבר אוטומטי לדף כתב הכמויות...
            </Typography>
          </Alert>
        </Collapse>

        {/* Instructions */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            סוגי קבצים נתמכים
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 2,
                borderRadius: 2,
                backgroundColor: alpha('#6366f1', 0.05),
                border: `1px solid ${alpha('#6366f1', 0.1)}`,
              }}
            >
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: alpha('#6366f1', 0.1),
                  fontWeight: 700,
                  color: '#6366f1',
                }}
              >
                DWG
              </Box>
              <Box>
                <Typography variant="subtitle2" fontWeight={600}>
                  קבצי AutoCAD
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  תוכניות DWG עם בלוקים וטקסט
                </Typography>
              </Box>
            </Box>

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 2,
                borderRadius: 2,
                backgroundColor: alpha('#ef4444', 0.05),
                border: `1px solid ${alpha('#ef4444', 0.1)}`,
              }}
            >
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: alpha('#ef4444', 0.1),
                  fontWeight: 700,
                  color: '#ef4444',
                }}
              >
                PDF
              </Box>
              <Box>
                <Typography variant="subtitle2" fontWeight={600}>
                  קבצי PDF
                </Typography>
                <Typography variant="body2" color="text.secondary">
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
