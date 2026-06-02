import apiClient from "./api";
import type { ApiResponse, Device } from "@/types";

export const devicesService = {
  async getAll(): Promise<ApiResponse<Device[]>> {
    const response = await apiClient.get<ApiResponse<Device[]>>("/devices");
    return response.data;
  },

  async getConnected(): Promise<ApiResponse<Device[]>> {
    const response = await apiClient.get<ApiResponse<Device[]>>("/devices/connected");
    return response.data;
  },

  async getById(id: number): Promise<ApiResponse<Device>> {
    const response = await apiClient.get<ApiResponse<Device>>(`/devices/${id}`);
    return response.data;
  },

  async create(data: Partial<Device>): Promise<ApiResponse<Device>> {
    const response = await apiClient.post<ApiResponse<Device>>("/devices", data);
    return response.data;
  },

  async update(id: number, data: Partial<Device>): Promise<ApiResponse<Device>> {
    const response = await apiClient.put<ApiResponse<Device>>(`/devices/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<ApiResponse<null>> {
    const response = await apiClient.delete<ApiResponse<null>>(`/devices/${id}`);
    return response.data;
  },

  async discover(): Promise<ApiResponse<Record<string, unknown>[]>> {
    const response = await apiClient.post<ApiResponse<Record<string, unknown>[]>>("/devices/discover");
    return response.data;
  },

  async heartbeat(id: number): Promise<ApiResponse<Device>> {
    const response = await apiClient.post<ApiResponse<Device>>(`/devices/${id}/heartbeat`);
    return response.data;
  },

  async sync(): Promise<ApiResponse<Record<string, number>>> {
    const response = await apiClient.post<ApiResponse<Record<string, number>>>("/devices/sync");
    return response.data;
  },
};
