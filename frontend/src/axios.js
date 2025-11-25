import axios from 'axios';

const instance = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/',
});

// Add a request interceptor to attach the token
instance.interceptors.request.use(config => {
    const token = localStorage.getItem('token'); // We will use Basic Auth or Token? 
    // DRF Session auth is default, but for SPA usually Token or JWT.
    // Let's stick to Basic Auth for simplicity if no Token Auth installed, 
    // BUT I installed djangorestframework, which supports TokenAuthentication but I didn't add it to INSTALLED_APPS.
    // Wait, I added `rest_framework` but didn't configure TokenAuth.
    // SessionAuth is tricky with CORS and CSRF.
    // Let's use Basic Auth for simplicity in this "University Project" context, OR just Session Auth with credentials=true.
    // Session Auth requires CSRF token handling.
    
    // EASIER: Basic Auth.
    // But user credentials need to be stored? No, base64 encoded.
    
    // BETTER: Use djangorestframework.authtoken.
    // I will enable `rest_framework.authtoken` in backend settings.
    
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

export default instance;

