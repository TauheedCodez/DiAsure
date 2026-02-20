import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthForm from '../components/AuthForm';
import './AuthPage.css';

const AuthPage = () => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Redirect to chat if already logged in
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/chat');
        }
    }, [isAuthenticated, navigate]);

    const handleAuthSuccess = () => {
        navigate('/chat');
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                <button className="btn btn-secondary back-btn" onClick={() => navigate('/')}>
                    ← Back to Home
                </button>

                <div className="auth-content fade-in">
                    <div className="auth-logo">
                        <h1>DiAsure</h1>
                        <p>Diabetic Foot Ulcer Assessment</p>
                    </div>

                    <AuthForm onSuccess={handleAuthSuccess} />
                </div>
            </div>
        </div>
    );
};

export default AuthPage;
