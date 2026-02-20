import React, { createContext, useContext, useState, useEffect } from 'react';
import { register as registerApi, login as loginApi, getMe } from '../api/authApi';
import { saveToken, getToken, removeToken } from '../utils/tokenStorage';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(getToken());
    const [loading, setLoading] = useState(true);

    // Load user on mount if token exists
    useEffect(() => {
        const loadUser = async () => {
            const savedToken = getToken();
            if (savedToken) {
                try {
                    const userData = await getMe();
                    setUser(userData);
                    setToken(savedToken);
                } catch (error) {
                    console.error('Failed to load user:', error);
                    // Token is invalid, clear it
                    removeToken();
                    setToken(null);
                    setUser(null);
                }
            }
            setLoading(false);
        };

        loadUser();
    }, []);

    const register = async (name, email, password) => {
        console.log('[AuthContext] register called with:', { name, email });
        try {
            const response = await registerApi(name, email, password);
            console.log('[AuthContext] registerApi response:', response);

            // Don't auto-login - user must verify email first
            return {
                success: true,
                message: response.message
            };
        } catch (error) {
            console.error('[AuthContext] register error:', error);
            const message = error.response?.data?.detail || 'Registration failed';
            return { success: false, error: message };
        }
    };

    const login = async (email, password) => {
        try {
            const data = await loginApi(email, password);
            saveToken(data.access_token);
            setToken(data.access_token);

            // Fetch user data
            const userData = await getMe();
            setUser(userData);

            return { success: true };
        } catch (error) {
            const message = error.response?.data?.detail || 'Login failed';
            return { success: false, error: message };
        }
    };

    const logout = () => {
        removeToken();
        setToken(null);
        setUser(null);
    };

    // Auto-login helper (used after email verification)
    const autoLogin = (userData, accessToken) => {
        saveToken(accessToken);
        setToken(accessToken);
        setUser(userData);
    };

    const value = {
        user,
        token,
        loading,
        isAuthenticated: !!token && !!user,
        register,
        login,
        logout,
        autoLogin,  // For email verification auto-login
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
