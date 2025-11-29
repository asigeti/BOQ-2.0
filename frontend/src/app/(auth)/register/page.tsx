'use client';

import { useState } from 'react';
import { Button, TextField, Typography, Container, Box, Alert, Link } from '@mui/material';
import api from '@/utils/axios';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            await api.post('/register', {
                email,
                full_name: fullName,
                password,
            });
            router.push('/login');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'ההרשמה נכשלה');
        }
    };

    return (
        <Container maxWidth="xs">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}
            >
                <Typography component="h1" variant="h5">
                    הרשמה
                </Typography>
                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="fullName"
                        label="שם מלא"
                        name="fullName"
                        autoComplete="name"
                        autoFocus
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="email"
                        label="כתובת אימייל"
                        name="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="password"
                        label="סיסמה"
                        type="password"
                        id="password"
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        sx={{ mt: 3, mb: 2 }}
                    >
                        הירשם
                    </Button>
                    <Box sx={{ textAlign: 'center' }}>
                        <Link href="/login" variant="body2">
                            {"יש לך כבר חשבון? התחבר כאן"}
                        </Link>
                    </Box>
                </Box>
            </Box>
        </Container>
    );
}
