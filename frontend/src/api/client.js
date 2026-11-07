import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Attach JWT Bearer token & auto-generate Idempotency-Key on mutations
apiClient.interceptors.request.use(
  (config) => {
    // 1. Attach JWT Authorization token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 2. Attach X-Idempotency-Key on state-mutating requests (POST, PUT, DELETE)
    const method = (config.method || '').toUpperCase();
    if (['POST', 'PUT', 'DELETE'].includes(method) && !config.headers['X-Idempotency-Key']) {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        config.headers['X-Idempotency-Key'] = crypto.randomUUID();
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 Unauthorized & 429 Rate Limiting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_profile');
        if (window.location.pathname !== '/login') {
          window.dispatchEvent(new Event('auth_logout'));
        }
      } else if (status === 429) {
        const retryAfter = error.response.headers['retry-after'] || '60';
        console.warn(`[RateLimit] Throttled by server. Retry-After: ${retryAfter}s`);
      }
    }
    return Promise.reject(error);
  }
);
