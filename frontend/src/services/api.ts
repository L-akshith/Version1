import axios from "axios";

// Standardize base URL - proxy via Vite or direct to port 8000
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to attach the access token to every outgoing request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle global errors (like token expiration)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If unauthorized, clean up and redirect (in future we could trigger refresh token logic)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      
      // Redirect to login only if not already there
      if (!window.location.pathname.endsWith("/login")) {
        window.location.href = "/login?expired=true";
      }
    }

    return Promise.reject(error);
  }
);

export default api;
