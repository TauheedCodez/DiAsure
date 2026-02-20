import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LandingPage.css';

const LandingPage = () => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Redirect to chat if already logged in
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/chat');
        }
    }, [isAuthenticated, navigate]);

    return (
        <div className="landing-page">
            <div className="landing-hero">
                <div className="container">
                    <div className="hero-content fade-in">
                        <h1 className="hero-title">DiAsure</h1>
                        <p className="hero-subtitle">
                            AI-Powered Diabetic Foot Ulcer Assessment System
                        </p>
                        <p className="hero-description">
                            Get instant, intelligent ulcer severity predictions and personalized care recommendations using advanced CNN technology.
                        </p>

                        <div className="hero-actions">
                            <button
                                className="btn btn-primary btn-lg"
                                onClick={() => navigate('/chat')}
                            >
                                Get Started
                            </button>
                            <button
                                className="btn btn-outline btn-lg"
                                onClick={() => navigate('/auth')}
                            >
                                Sign In
                            </button>
                            <button
                                className="btn btn-secondary btn-lg"
                                onClick={() => navigate('/find-doctors')}
                            >
                                Find Nearby Doctors
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="dos-donts-section">
                <div className="container">
                    <h2 className="section-title">Before Uploading Your Image</h2>

                    <div className="dos-donts-grid">
                        <div className="card dos-card slide-up">
                            <div className="card-icon success">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            </div>
                            <h3 className="card-title">DOs</h3>
                            <ul className="dos-donts-list">
                                <li>Use good, natural lighting</li>
                                <li>Ensure clear foot visibility</li>
                                <li>Keep a clean, plain background</li>
                                <li>Upload JPEG or PNG format</li>
                                <li>Take photo at eye level</li>
                                <li>Ensure ulcer is clearly visible</li>
                            </ul>
                        </div>

                        <div className="card donts-card slide-up" style={{ animationDelay: '0.1s' }}>
                            <div className="card-icon danger">❌</div>
                            <h3 className="card-title">DON'Ts</h3>
                            <ul className="dos-donts-list">
                                <li>Don't upload blurry images</li>
                                <li>Avoid poor lighting conditions</li>
                                <li>Don't obstruct the view</li>
                                <li>Avoid uploading random images</li>
                                <li>Don't use excessive filters</li>
                                <li>Avoid cluttered backgrounds</li>
                            </ul>
                        </div>
                    </div>

                    <div className="info-banner">
                        <p>
                            <strong>Note:</strong> Guest users can chat freely but cannot upload images or save chat history.
                            Sign in to unlock full features including image analysis and personalized assessments.
                        </p>
                    </div>
                </div>
            </div>

            <footer className="landing-footer">
                <div className="container">
                    <p>&copy; 2026 DiAsure. AI-powered healthcare assessment system.</p>
                    <p className="text-muted">This is not a substitute for professional medical advice.</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
