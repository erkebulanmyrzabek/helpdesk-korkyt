import axios from 'axios';

const instance = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/',
});

// Add a request interceptor to attach the token
instance.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    
    // Do not send token for login endpoint
    if (token && !config.url.endsWith('api-token-auth/')) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

export default instance;

