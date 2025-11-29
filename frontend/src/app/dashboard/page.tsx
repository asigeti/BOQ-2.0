'use client';

import { useEffect, useState } from 'react';
import { Container, Typography, Box, Grid, Card, CardContent, Divider, Button } from '@mui/material';
import FileUpload from '@/components/FileUpload';
import api from '@/utils/axios';
import { useRouter } from 'next/navigation';

interface Plan {
    id: number;
    filename: string;
    uploaded_at: string;
}

export default function Dashboard() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const router = useRouter();

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

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Typography variant="h4" gutterBottom>
                לוח בקרה
            </Typography>

            <Grid container spacing={3}>
                {/* Upload Section */}
                <Grid size={{ xs: 12, md: 8 }}>
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h6" gutterBottom>
                            העלאת תוכנית חדשה
                        </Typography>
                        <FileUpload onUploadSuccess={fetchPlans} />
                    </Box>
                </Grid>

                {/* Recent Plans Section */}
                <Grid size={{ xs: 12, md: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        העלאות אחרונות
                    </Typography>
                    <Card variant="outlined">
                        <CardContent>
                            {plans.length === 0 ? (
                                <Typography color="text.secondary">עדיין לא הועלו תוכניות.</Typography>
                            ) : (
                                plans.map((plan) => (
                                    <Box key={plan.id} sx={{ mb: 2 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <Box>
                                                <Typography variant="subtitle1">{plan.filename}</Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    {new Date(plan.uploaded_at).toLocaleDateString('he-IL')}
                                                </Typography>
                                            </Box>
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                onClick={() => router.push(`/dashboard/plans/${plan.id}`)}
                                            >
                                                צפה
                                            </Button>
                                        </Box>
                                        <Divider sx={{ mt: 1 }} />
                                    </Box>
                                ))
                            )}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Container>
    );
}
