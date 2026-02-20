/**
 * Save JWT token to localStorage
 * @param {string} token - JWT token
 */
export const saveToken = (token) => {
    localStorage.setItem('token', token);
};

/**
 * Get JWT token from localStorage
 * @returns {string|null} JWT token or null
 */
export const getToken = () => {
    return localStorage.getItem('token');
};

/**
 * Remove JWT token from localStorage
 */
export const removeToken = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
};
