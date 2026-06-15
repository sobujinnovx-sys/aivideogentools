import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const register = (data: { email: string; password: string; full_name?: string }) =>
  api.post("/auth/register", data);

export const login = (data: { email: string; password: string }) =>
  api.post("/auth/login", data);

export const getMe = () => api.get("/auth/me");

// Videos
export const generateVideo = (data: {
  prompt: string;
  duration: number;
  aspect_ratio: string;
  model: string;
  image_urls?: string[];
}) => api.post("/videos/generate", data);

export const uploadImage = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/videos/upload-image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getVideos = (page = 1, limit = 20) =>
  api.get(`/videos/?page=${page}&limit=${limit}`);

export const deleteVideo = (id: string) => api.delete(`/videos/${id}`);

export const downloadVideo = async (id: string) => {
  const res = await api.get(`/videos/${id}/download`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = `video_${id}.gif`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

// Jobs
export const getJob = (id: string) => api.get(`/jobs/${id}`);

// Credits
export const getCreditBalance = () => api.get("/credits/balance");
export const getCreditHistory = (page = 1, limit = 20) =>
  api.get(`/credits/history?page=${page}&limit=${limit}`);
export const claimBonus = () => api.post("/credits/bonus");
