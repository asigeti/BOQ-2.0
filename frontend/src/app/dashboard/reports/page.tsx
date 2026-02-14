'use client';

import {
  Box,
  Typography,
  Card,
  CardContent,
} from '@mui/material';
import {
  Assessment as ReportIcon,
  Construction as ConstructionIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { MainLayout, Header } from '@/components/layout';

export default function ReportsPage() {
  return (
    <MainLayout>
      <Header title="דוחות" subtitle="צפייה בדוחות כתב כמויות ונתוני פרויקטים" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card>
          <CardContent sx={{ p: 6, textAlign: 'center' }}>
            <Box
              sx={{
                width: 80,
                height: 80,
                mx: 'auto',
                mb: 3,
                borderRadius: '50%',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ConstructionIcon sx={{ fontSize: 40, color: '#6366f1' }} />
            </Box>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              דוחות בפיתוח
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
              מודול הדוחות נמצא בשלבי פיתוח. בקרוב תוכלו לייצא דוחות כתב כמויות מפורטים בפורמטים שונים.
            </Typography>
          </CardContent>
        </Card>
      </motion.div>
    </MainLayout>
  );
}
