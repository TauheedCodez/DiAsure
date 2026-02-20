import apiClient from './apiClient';

/**
 * Guest Chat API (unauthenticated, volatile sessions)
 * These sessions are stored in memory and expire on server restart
 */

/**
 * Start a new guest chat session
 * @returns {Promise<{session_id: string, message: string}>}
 */
export const startGuestChat = async () => {
  const response = await apiClient.post('/guest/start');
  return response.data;
};

/**
 * Send a message in a guest chat session
 * @param {string} sessionId - Guest session ID
 * @param {string} content - Message content
 * @returns {Promise<{assistant_message: string, patient_state: object}>}
 */
export const sendGuestMessage = async (sessionId, content) => {
  const response = await apiClient.post(`/guest/${sessionId}/ai-message`, {
    content,
  });
  return response.data;
};

/**
 * Upload an image in a guest chat session
 * @param {string} sessionId - Guest session ID
 * @param {File} file - Image file to upload
 * @returns {Promise<{status: string, prediction: string, assistant_message: string, patient_state: object}>}
 */
export const uploadGuestImage = async (sessionId, file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post(`/guest/${sessionId}/upload-image`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

