import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Accept': 'application/json',
  },
  timeout: 60000, // 60s timeout for RAG and embedding tasks
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let message = 'An unexpected error occurred';
    const detail = error.response?.data?.detail;

    if (detail) {
      message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    } else if (error.response?.data?.message) {
      message = error.response.data.message;
    } else if (error.message === 'Network Error') {
      message = 'Network Error: Backend unreachable or CORS request failed (http://localhost:8001)';
    } else if (error.message) {
      message = error.message;
    }

    const customError = new Error(message);
    customError.status = error.response?.status || 500;
    return Promise.reject(customError);
  }
);

export default apiClient;
