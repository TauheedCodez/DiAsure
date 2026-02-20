import apiClient from './apiClient';

/**
 * Fetch nearby doctors within specified radius
 * @param {number} latitude - User's latitude
 * @param {number} longitude - User's longitude
 * @param {number} radius - Search radius in meters (default 5000)
 * @param {string[]} doctorTypes - Array of doctor types to filter
 * @returns {Promise} - API response with places
 */
export const getNearbyDoctors = async (latitude, longitude, radius = 5000, doctorTypes = []) => {
    const params = new URLSearchParams({
        latitude: latitude.toString(),
        longitude: longitude.toString(),
        radius: radius.toString()
    });

    if (doctorTypes.length > 0) {
        params.append('doctor_types', doctorTypes.join(','));
    }

    const response = await apiClient.get(`/places/nearby?${params.toString()}`);
    return response.data;
};
