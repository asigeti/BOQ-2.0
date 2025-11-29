'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    Container,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    CircularProgress,
    Box,
    Button,
    LinearProgress,
    Alert,
    Grid,
    Card,
    CardContent,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import api from '@/utils/axios';

interface MaterialQuantity {
    id: number;
    material_name: string;
    quantity: number;
    unit: string;
    confidence_score: number;
}

interface ProcessingStatus {
    status: string;
    progress: number;
}

interface SupplyChainRecommendation {
    material: string;
    supplier: string;
    price: number;
    total_cost: number;
    delivery: string;
}

interface WeatherForecast {
    location: string;
    forecast: {
        day: string;
        condition: string;
        temp_high: number;
        temp_low: number;
    }[];
}

export default function PlanDetailPage() {
    const params = useParams();
    const planId = params.id;
    const [materials, setMaterials] = useState<MaterialQuantity[]>([]);
    const [supplyChain, setSupplyChain] = useState<SupplyChainRecommendation[]>([]);
    const [weather, setWeather] = useState<WeatherForecast | null>(null);
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState<ProcessingStatus>({ status: 'pending', progress: 0 });

    // Fetch materials
    const fetchMaterials = async () => {
        try {
            const response = await api.get(`/plans/${planId}/quantities`);
            setMaterials(response.data);
        } catch (error) {
            console.error('Failed to fetch materials', error);
        }
    };

    // Fetch status
    const fetchStatus = async () => {
        try {
            const response = await api.get(`/plans/${planId}/status`);
            setStatus(response.data);

            // If completed, fetch materials and other data
            if (response.data.status === 'completed') {
                await fetchMaterials();
                await fetchSupplyChain();
                await fetchWeather();
                setLoading(false);
            }
        } catch (error) {
            console.error('Failed to fetch status', error);
        }
    };

    // Fetch Supply Chain
    const fetchSupplyChain = async () => {
        try {
            const response = await api.post('/optimization/supply-chain', { plan_id: planId });
            setSupplyChain(response.data);
        } catch (error) {
            console.error('Failed to fetch supply chain', error);
        }
    };

    // Fetch Weather
    const fetchWeather = async () => {
        try {
            const response = await api.get('/optimization/weather', { params: { location: 'Tel Aviv' } });
            setWeather(response.data);
        } catch (error) {
            console.error('Failed to fetch weather', error);
        }
    };

    useEffect(() => {
        // Initial fetch
        fetchStatus();

        // Poll every 2 seconds if not completed
        const interval = setInterval(() => {
            if (status.status !== 'completed' && status.status !== 'failed') {
                fetchStatus();
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [planId, status.status]);

    const handleExportExcel = async () => {
        try {
            const response = await api.get(`/export/plans/${planId}/excel`, {
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `BOQ_${planId}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Failed to export Excel', error);
        }
    };

    const getStatusMessage = () => {
        switch (status.status) {
            case 'pending':
                return 'ממתין לעיבוד...';
            case 'processing':
                return `מעבד קובץ... ${status.progress}%`;
            case 'completed':
                return 'העיבוד הושלם בהצלחה';
            case 'failed':
                return 'העיבוד נכשל';
            default:
                return 'טוען...';
        }
    };

    // Show loading state while processing
    if (status.status === 'pending' || status.status === 'processing') {
        return (
            <Container sx={{ mt: 4, textAlign: 'center' }}>
                <Box sx={{ mb: 3 }}>
                    <CircularProgress size={60} />
                </Box>
                <Typography variant="h5" gutterBottom>
                    {getStatusMessage()}
                </Typography>
                <Box sx={{ width: '100%', maxWidth: 400, mx: 'auto', mt: 3 }}>
                    <LinearProgress variant="determinate" value={status.progress} />
                </Box>
            </Container>
        );
    }

    // Show error state
    if (status.status === 'failed') {
        return (
            <Container sx={{ mt: 4 }}>
                <Alert severity="error">
                    העיבוד נכשל. אנא נסה להעלות את הקובץ שוב.
                </Alert>
            </Container>
        );
    }

    // Show results
    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4">
                    כתב כמויות
                </Typography>
                {materials.length > 0 && (
                    <Button
                        variant="contained"
                        startIcon={<DownloadIcon />}
                        onClick={handleExportExcel}
                    >
                        ייצוא לאקסל
                    </Button>
                )}
            </Box>

            {materials.length === 0 ? (
                <Typography color="text.secondary">
                    לא נמצאו חומרים בקובץ.
                </Typography>
            ) : (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>חומר</TableCell>
                                <TableCell align="right">כמות</TableCell>
                                <TableCell align="right">יחידה</TableCell>
                                <TableCell align="right">רמת ביטחון</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {materials.map((material) => (
                                <TableRow key={material.id}>
                                    <TableCell>{material.material_name}</TableCell>
                                    <TableCell align="right">{material.quantity}</TableCell>
                                    <TableCell align="right">{material.unit}</TableCell>
                                    <TableCell align="right">
                                        {(material.confidence_score * 100).toFixed(1)}%
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* Supply Chain Section */}
            {supplyChain.length > 0 && (
                <Box sx={{ mt: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        המלצות רכש ושרשרת אספקה
                    </Typography>
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>חומר</TableCell>
                                    <TableCell>ספק מומלץ</TableCell>
                                    <TableCell align="right">מחיר ליחידה</TableCell>
                                    <TableCell align="right">סה"כ עלות</TableCell>
                                    <TableCell align="right">זמן אספקה</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {supplyChain.map((item, index) => (
                                    <TableRow key={index}>
                                        <TableCell>{item.material}</TableCell>
                                        <TableCell>{item.supplier}</TableCell>
                                        <TableCell align="right">₪{item.price}</TableCell>
                                        <TableCell align="right">₪{item.total_cost.toFixed(2)}</TableCell>
                                        <TableCell align="right">{item.delivery}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {/* Weather Section */}
            {weather && (
                <Box sx={{ mt: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        תחזית מזג אוויר - {weather.location}
                    </Typography>
                    <Grid container spacing={2}>
                        {weather.forecast.map((day, index) => (
                            <Grid size={{ xs: 12, sm: 6, md: 2 }} key={index}>
                                <Card variant="outlined">
                                    <CardContent>
                                        <Typography variant="subtitle1" gutterBottom>
                                            {day.day}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {day.condition}
                                        </Typography>
                                        <Typography variant="body1">
                                            {day.temp_high}°C / {day.temp_low}°C
                                        </Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Box>
            )}
        </Container>
    );
}
