import apiClient from './apiClient';

/**
 * Register a new user and send verification email
 * @param {string} name - User's full name
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise} Message response
 */
export const register = async (name, email, password) => {
    const response = await apiClient.post('/auth/register', {
        name,
        email,
        password,
    });
    return response.data;
};

/**
 * Login user (requires verified email)
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise} Token and user response
 */
export const login = async (email, password) => {
    const response = await apiClient.post('/auth/login', {
        email,
        password,
    });
    return response.data;
};

/**
 * Verify email with token
 * @param {string} token - Verification token from email
 * @returns {Promise} Token and user response (auto-login)
 */
export const verifyEmail = async (token) => {
    const response = await apiClient.get(`/auth/verify-email/${token}`);
    return response.data;
};

/**
 * Resend verification email
 * @param {string} email - User's email
 * @returns {Promise} Message response
 */
export const resendVerification = async (email) => {
    const response = await apiClient.post('/auth/resend-verification', {
        email,
    });
    return response.data;
};

/**
 * Request password reset email
 * @param {string} email - User's email
 * @returns {Promise} Message response
 */
export const requestPasswordReset = async (email) => {
    const response = await apiClient.post('/auth/forgot-password', {
        email,
    });
    return response.data;
};

/**
 * Reset password with token
 * @param {string} token - Reset token from email
 * @param {string} newPassword - New password
 * @returns {Promise} Message response
 */
export const resetPassword = async (token, newPassword) => {
    const response = await apiClient.post(`/auth/reset-password/${token}`, {
        new_password: newPassword,
    });
    return response.data;
};

/**
 * Get current user info
 * @returns {Promise} User response
 */
export const getMe = async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
};
