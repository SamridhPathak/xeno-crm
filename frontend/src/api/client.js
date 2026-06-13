import axios from 'axios';

// Get backend base URL from Vite environment variables (fallback to localhost:8000)
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
console.log("API Base URL:", baseURL);

const client = axios.create({
  baseURL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for unified error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error details for debugging
    console.error('API client request failure:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });
    
    // Normalize and propagate the error message
    const errorDetails = error.response?.data?.detail || error.message || 'An unexpected error occurred.';
    return Promise.reject(new Error(typeof errorDetails === 'string' ? errorDetails : JSON.stringify(errorDetails)));
  }
);

export default client;
