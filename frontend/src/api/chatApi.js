import apiClient from './apiClient';

/**
 * Create a new chat (authenticated users only)
 * @returns {Promise} Chat response with chat_id
 */
export const createChat = async () => {
    const response = await apiClient.post('/chat/create');
    return response.data;
};

/**
 * Get chat history (authenticated users only)
 * @returns {Promise} Array of chat history items
 */
export const getChatHistory = async () => {
    const response = await apiClient.get('/chat/history');
    return response.data;
};

/**
 * Get a specific chat by ID with messages
 * @param {number} chatId - Chat ID
 * @returns {Promise} Chat with messages
 */
export const getChatById = async (chatId) => {
    const response = await apiClient.get(`/chat/${chatId}`);
    return response.data;
};

/**
 * Delete a chat
 * @param {number} chatId - Chat ID
 * @returns {Promise} Delete confirmation
 */
export const deleteChat = async (chatId) => {
    const response = await apiClient.delete(`/chat/${chatId}`);
    return response.data;
};

/**
 * Send a message to AI chatbot
 * @param {number} chatId - Chat ID (or null for guest mode)
 * @param {string} content - Message content
 * @returns {Promise} AI response
 */
export const sendMessage = async (chatId, content) => {
    const response = await apiClient.post(`/chat/${chatId}/ai-message`, {
        content,
    });
    return response.data;
};

/**
 * Upload image for severity prediction
 * @param {number} chatId - Chat ID
 * @param {File} file - Image file
 * @returns {Promise} Prediction result
 */
export const uploadImage = async (chatId, file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(`/chat/${chatId}/upload-image`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};
