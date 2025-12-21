// src/utils/api.js
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api/';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const tokenString = localStorage.getItem('authTokens');
    if (tokenString) {
        const token = JSON.parse(tokenString).access;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

export default api;