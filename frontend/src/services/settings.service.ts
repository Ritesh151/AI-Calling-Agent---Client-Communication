import apiClient from "./api";
import type { ApiResponse, Setting } from "@/types";

export const settingsService = {
  async getAll(category?: string): Promise<ApiResponse<Setting[]>> {
    const params = category ? { category } : {};
    const response = await apiClient.get<ApiResponse<Setting[]>>("/settings/", { params });
    return response.data;
  },

  async getById(id: number): Promise<ApiResponse<Setting>> {
    const response = await apiClient.get<ApiResponse<Setting>>(`/settings/${id}/`);
    return response.data;
  },

  async getByKey(key: string): Promise<ApiResponse<Setting>> {
    const response = await apiClient.get<ApiResponse<Setting>>(`/settings/key/${key}/`);
    return response.data;
  },

  async create(data: Partial<Setting>): Promise<ApiResponse<Setting>> {
    const response = await apiClient.post<ApiResponse<Setting>>("/settings/", data);
    return response.data;
  },

  async update(id: number, data: Partial<Setting>): Promise<ApiResponse<Setting>> {
    const response = await apiClient.put<ApiResponse<Setting>>(`/settings/${id}/`, data);
    return response.data;
  },

  async upsert(key: string, data: Partial<Setting>): Promise<ApiResponse<Setting>> {
    const response = await apiClient.put<ApiResponse<Setting>>(`/settings/key/${key}/`, data);
    return response.data;
  },

  async delete(id: number): Promise<ApiResponse<null>> {
    const response = await apiClient.delete<ApiResponse<null>>(`/settings/${id}/`);
    return response.data;
  },
};
