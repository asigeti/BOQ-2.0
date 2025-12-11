import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  user: any | null;
  hydrated: boolean;
}

// Start with null/false to avoid hydration mismatch
// Token will be loaded from localStorage after mount
const initialState: AuthState = {
  token: null,
  isAuthenticated: false,
  user: null,
  hydrated: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Called on client mount to load from localStorage
    hydrateAuth: (state) => {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        state.token = token;
        state.isAuthenticated = !!token;
      }
      state.hydrated = true;
    },
    setCredentials: (
      state,
      action: PayloadAction<{ user: any; token: string }>
    ) => {
      const { user, token } = action.payload;
      state.user = user;
      state.token = token;
      state.isAuthenticated = true;
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', token);
      }
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
      }
    },
  },
});

export const { hydrateAuth, setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
