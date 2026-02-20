import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { resendVerification, requestPasswordReset } from '../api/authApi';
import './AuthForm.css';

const AuthForm = ({ onSuccess }) => {
    const { login, register } = useAuth();
    const [mode, setMode] = useState('login'); // login, register, forgot-password, email-sent
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [registeredEmail, setRegisteredEmail] = useState('');
    const [resendTimer, setResendTimer] = useState(0);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
        setError('');
    };

    const startResendTimer = () => {
        setResendTimer(60);
        const interval = setInterval(() => {
            setResendTimer((prev) => {
                if (prev <= 1) {
                    clearInterval(interval);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        console.log('[AuthForm] handleSubmit called, mode:', mode);

        try {
            if (mode === 'login') {
                console.log('[AuthForm] Calling login...');
                const result = await login(formData.email, formData.password);
                console.log('[AuthForm] Login result:', result);
                if (result.success) {
                    if (onSuccess) onSuccess();
                } else {
                    setError(result.error);
                }
            } else if (mode === 'register') {
                console.log('[AuthForm] Calling register with:', formData.name, formData.email);
                const result = await register(formData.name, formData.email, formData.password);
                console.log('[AuthForm] Register result:', result);
                if (result.success) {
                    setRegisteredEmail(formData.email);
                    setMode('email-sent');
                    startResendTimer();
                } else {
                    setError(result.error);
                }
            } else if (mode === 'forgot-password') {
                console.log('[AuthForm] Calling forgot password...');
                await requestPasswordReset(formData.email);
                setMode('email-sent');
            }
        } catch (err) {
            console.error('[AuthForm] Error in handleSubmit:', err);
            if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError('An unexpected error occurred');
            }
        } finally {
            console.log('[AuthForm] Setting loading to false');
            setLoading(false);
        }
    };

    const handleResendVerification = async () => {
        try {
            setLoading(true);
            await resendVerification(registeredEmail);
            startResendTimer();
            alert('Verification email sent! Please check your inbox.');
        } catch (err) {
            alert('Failed to resend email. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const switchMode = (newMode) => {
        setMode(newMode);
        setError('');
        setFormData({ name: '', email: '', password: '' });
    };

    // Email sent confirmation view
    if (mode === 'email-sent') {
        return (
            <div className="auth-form-container">
                <div className="email-sent-container">
                    <div className="email-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <polyline points="22,6 12,13 2,6"></polyline>
                        </svg>
                    </div>
                    <h2>Check Your Email</h2>
                    <p>
                        We've sent a {registeredEmail ? 'verification' : 'password reset'} link to:
                    </p>
                    <p className="email-address">{registeredEmail || formData.email}</p>
                    <p className="instruction">
                        Click the link in the email to {registeredEmail ? 'verify your account' : 'reset your password'}.
                    </p>

                    {registeredEmail && (
                        <div className="resend-section">
                            <p className="resend-text">Didn't receive the email?</p>
                            {resendTimer > 0 ? (
                                <p className="timer-text">Resend available in {resendTimer}s</p>
                            ) : (
                                <button
                                    onClick={handleResendVerification}
                                    disabled={loading}
                                    className="btn btn-secondary btn-sm"
                                >
                                    {loading ? 'Sending...' : 'Resend Email'}
                                </button>
                            )}
                        </div>
                    )}

                    <button
                        onClick={() => switchMode('login')}
                        className="btn btn-link"
                        style={{ marginTop: '1.5rem' }}
                    >
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-form-container">
            {mode !== 'forgot-password' ? (
                <div className="auth-tabs">
                    <button
                        className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
                        onClick={() => switchMode('login')}
                    >
                        Sign In
                    </button>
                    <button
                        className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
                        onClick={() => switchMode('register')}
                    >
                        Register
                    </button>
                </div>
            ) : (
                <div className="forgot-password-header">
                    <h2>Forgot Password</h2>
                    <p>Enter your email to receive a password reset link</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
                {mode === 'register' && (
                    <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="Enter your full name"
                            required
                        />
                    </div>
                )}

                <div className="form-group">
                    <label className="form-label">Email</label>
                    <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="form-input"
                        placeholder="Enter your email"
                        required
                    />
                </div>

                {mode !== 'forgot-password' && (
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="Enter your password"
                            required
                            minLength={6}
                        />
                    </div>
                )}

                {mode === 'login' && (
                    <div className="forgot-password-link">
                        <button
                            type="button"
                            onClick={() => switchMode('forgot-password')}
                            className="btn-link-small"
                        >
                            Forgot Password?
                        </button>
                    </div>
                )}

                {error && <div className="form-error">{error}</div>}

                <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
                    {loading ? (
                        <>
                            <span className="spinner spinner-sm"></span>
                            Processing...
                        </>
                    ) : (
                        <>
                            {mode === 'login' && 'Sign In'}
                            {mode === 'register' && 'Create Account'}
                            {mode === 'forgot-password' && 'Send Reset Link'}
                        </>
                    )}
                </button>

                {mode === 'forgot-password' && (
                    <button
                        type="button"
                        onClick={() => switchMode('login')}
                        className="btn btn-secondary"
                        style={{ marginTop: '0.75rem' }}
                    >
                        Back to Login
                    </button>
                )}
            </form>
        </div>
    );
};

export default AuthForm;
