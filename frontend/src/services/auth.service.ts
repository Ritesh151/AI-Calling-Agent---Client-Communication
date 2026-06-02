import apiClient from "./api";
import type { ApiResponse, AuthTokens, LoginRequest, RegisterRequest, User } from "@/types";

export const authService = {
  async login(data: LoginRequest): Promise<ApiResponse<AuthTokens>> {
    const response = await apiClient.post<ApiResponse<AuthTokens>>("/auth/login", data);
    const tokens = response.data.data;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    return response.data;
  },

  async register(data: RegisterRequest): Promise<ApiResponse<User>> {
    const response = await apiClient.post<ApiResponse<User>>("/auth/register", data);
    return response.data;
  },

  async refreshToken(): Promise<ApiResponse<AuthTokens>> {
    const refreshToken = localStorage.getItem("refresh_token");
    const response = await apiClient.post<ApiResponse<AuthTokens>>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    const tokens = response.data.data;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    return response.data;
  },

  async getMe(): Promise<ApiResponse<User>> {
    const response = await apiClient.get<ApiResponse<User>>("/auth/me");
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  },
};
