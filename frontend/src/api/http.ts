import axios from "axios";

const http = axios.create({
  baseURL: "http://127.0.0.1:8000", // Django 后端地址
  timeout: 8000,
});

// 可选：自动带上 JWT
http.interceptors.request.use((config) => {
  const url = config.url || "";

  // 调试：确认每次请求是否拿到了 access_token（需要时可注释掉）
  // console.log("[http]", url, "access_token=", localStorage.getItem("access_token"));

  // 公开接口：注册 / 登录 / 刷新 token，不携带 Authorization
  const isPublicAuthApi =
    url.startsWith("/api/auth/register") ||
    url.startsWith("/api/auth/login") ||
    url.startsWith("/api/auth/refresh");

  if (!isPublicAuthApi) {
    // SimpleJWT 登录返回 { access, refresh, user }
    // 约定：把 access 存到 localStorage 的 access_token
    const accessToken =
      localStorage.getItem("access_token") ||
      localStorage.getItem("access") ||
      localStorage.getItem("token");

    if (accessToken) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
  }

  return config;
});

export default http;
