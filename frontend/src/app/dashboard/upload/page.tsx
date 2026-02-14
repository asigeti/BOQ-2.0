'use client';

import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  alpha,
  Chip,
  Alert,
  Grid,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  AccessTime as TimeIcon,
  Architecture as CadIcon,
  ArrowForward as ArrowIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { MainLayout, Header } from '@/components/layout';
import FileUpload from '@/components/FileUpload';
import api from '@/utils/axios';

interface Plan {
  id: number;
  filename: string;
  uploaded_at: string;
  processing_status?: string;
}

export default function UploadPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [recentUpload, setRecentUpload] = useState<Plan | null>(null);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/plans/');
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans', error);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleUploadSuccess = (data: any) => {
    setRecentUpload(data);
    fetchPlans();
  };

  return (
    <MainLayout>
      <Header title="העלאת קובץ" subtitle="העלה קבצי AutoCAD, PDF או תמונות ליצירת כתב כמויות" />

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Card>
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <UploadIcon sx={{ color: 'white', fontSize: 24 }} />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={600}>
                      העלאת תוכנית חדשה
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      העלה קובץ AutoCAD ליצירת כתב כמויות אוטומטי
                    </Typography>
                  </Box>
                </Box>

                <FileUpload onUploadSuccess={handleUploadSuccess} />

                {recentUpload && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Alert severity="info" sx={{ mt: 3, borderRadius: 2 }}>
                      הקובץ {recentUpload.filename} נוסף לתור העיבוד
                    </Alert>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                  העלאות אחרונות
                </Typography>

                {plans.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                    <FileIcon sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
                    <Typography variant="body2">עדיין לא הועלו קבצים</Typography>
                  </Box>
                ) : (
                  <Box>
                    {plans.slice(0, 8).map((plan, index) => (
                      <motion.div
                        key={plan.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <Box
                          onClick={() => window.location.href = `/BOQ-2.0/dashboard/plans/${plan.id}/`}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 2,
                            p: 1.5,
                            borderRadius: 2,
                            cursor: 'pointer',
                            '&:hover': { backgroundColor: alpha('#6366f1', 0.04) },
                          }}
                        >
                          <CadIcon sx={{ color: '#6366f1', fontSize: 20 }} />
                          <Box sx={{ flex: 1, minWidth: 0 }}>
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            >
                              {plan.filename}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <TimeIcon sx={{ fontSize: 12, color: 'text.secondary' }} />
                              <Typography variant="caption" color="text.secondary">
                                {new Date(plan.uploaded_at).toLocaleDateString('he-IL')}
                              </Typography>
                            </Box>
                          </Box>
                          <Chip
                            label={plan.processing_status === 'completed' ? 'הושלם' : 'ממתין'}
                            size="small"
                            sx={{
                              fontSize: '0.65rem',
                              backgroundColor: alpha(
                                plan.processing_status === 'completed' ? '#10b981' : '#64748b',
                                0.1
                              ),
                              color: plan.processing_status === 'completed' ? '#10b981' : '#64748b',
                            }}
                          />
                        </Box>
                      </motion.div>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>
    </MainLayout>
  );
}
