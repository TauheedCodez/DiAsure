import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { verifyEmail, resendVerification } from '../api/authApi';
import { useAuth } from '../context/AuthContext';
import './VerifyEmail.css';

const VerifyEmail = () => {
    const { token } = useParams();
    const navigate = useNavigate();
    const { autoLogin } = useAuth();

    const [status, setStatus] = useState('verifying'); // verifying, success, error
    const [message, setMessage] = useState('');
    const [email, setEmail] = useState('');
    const [resending, setResending] = useState(false);

    useEffect(() => {
        handleVerification();
    }, [token]);

    const handleVerification = async () => {
        try {
            setStatus('verifying');
            const response = await verifyEmail(token);

            // Auto-login with the returned token and user data
            autoLogin(response.user, response.access_token);

            setStatus('success');
            setMessage(response.message);

            // Redirect to chat after 2 seconds
            setTimeout(() => {
                navigate('/chat');
            }, 2000);

        } catch (error) {
            setStatus('error');
            if (error.response?.data?.detail) {
                setMessage(error.response.data.detail);
            } else {
                setMessage('Verification failed. Please try again.');
            }
        }
    };

    const handleResend = async () => {
        if (!email) {
            alert('Please enter your email address');
            return;
        }

        try {
            setResending(true);
            await resendVerification(email);
            alert('Verification email sent! Please check your inbox.');
        } catch (error) {
            alert('Failed to resend email. Please try again.');
        } finally {
            setResending(false);
        }
    };

    return (
        <div className="verify-email-page">
            <div className="verify-email-container">
                <div className="verify-email-card">
                    {status === 'verifying' && (
                        <>
                            <div className="spinner-large"></div>
                            <h2>Verifying Your Email...</h2>
                            <p>Please wait while we verify your email address.</p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <div className="success-icon">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            </div>
                            <h2>Email Verified!</h2>
                            <p>{message}</p>
                            <p className="redirect-message">Redirecting you to the app...</p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <div className="error-icon">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </div>
                            <h2>Verification Failed</h2>
                            <p className="error-message">{message}</p>

                            {message.includes('expired') && (
                                <div className="resend-section">
                                    <p>Request a new verification link:</p>
                                    <div className="resend-form">
                                        <input
                                            type="email"
                                            placeholder="Enter your email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="email-input"
                                        />
                                        <button
                                            onClick={handleResend}
                                            disabled={resending}
                                            className="btn btn-primary"
                                        >
                                            {resending ? 'Sending...' : 'Resend Link'}
                                        </button>
                                    </div>
                                </div>
                            )}

                            <button
                                onClick={() => navigate('/auth')}
                                className="btn btn-secondary"
                                style={{ marginTop: '1rem' }}
                            >
                                Back to Login
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VerifyEmail;
