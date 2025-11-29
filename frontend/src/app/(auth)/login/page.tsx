'use client';

import { useState } from 'react';
import { Button, TextField, Typography, Container, Box, Alert, Link } from '@mui/material';
import { useDispatch } from 'react-redux';
import { setCredentials } from '@/store/slices/authSlice';
import api from '@/utils/axios';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const dispatch = useDispatch();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await api.post('/login/access-token', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            dispatch(setCredentials({ token: response.data.access_token, user: null })); // User info fetched separately or decoded
            router.push('/dashboard');
        } catch (err: any) {
            setError('התחברות נכשלה. אנא בדוק את הפרטים שלך.');
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
                    התחברות
                </Typography>
                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="email"
                        label="כתובת אימייל"
                        name="email"
                        autoComplete="email"
                        autoFocus
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
                        autoComplete="current-password"
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
                        התחבר
                    </Button>
                    <Box sx={{ textAlign: 'center' }}>
                        <Link href="/register" variant="body2">
                            {"אין לך חשבון? הירשם כאן"}
                        </Link>
                    </Box>
                </Box>
            </Box>
        </Container>
    );
}
