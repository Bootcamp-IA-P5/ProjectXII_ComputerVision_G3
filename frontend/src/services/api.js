import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Video endpoints
export const uploadVideo = async (formData) => {
    const response = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getVideos = async () => {
    const response = await api.get('/videos');
    return response.data;
};

export const getVideoResult = async (videoId) => {
    const response = await api.get(`/videos/${videoId}/results`);
    return response.data;
};

export const getTaskStatus = async (taskId) => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
};

export const getConfig = async () => {
    const response = await api.get('/config');
    return response.data;
};

export default api;
