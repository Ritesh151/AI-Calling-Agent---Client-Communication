import apiClient from "./api";
import type { ApiResponse, CallSession } from "@/types";

export const callsService = {
  async getAll(): Promise<ApiResponse<CallSession[]>> {
    const response = await apiClient.get<ApiResponse<CallSession[]>>("/calls");
    return response.data;
  },

  async getActive(): Promise<ApiResponse<CallSession[]>> {
    const response = await apiClient.get<ApiResponse<CallSession[]>>("/calls/active");
    return response.data;
  },

  async getById(id: number): Promise<ApiResponse<CallSession>> {
    const response = await apiClient.get<ApiResponse<CallSession>>(`/calls/${id}`);
    return response.data;
  },
  

  async getByDevice(deviceId: number): Promise<ApiResponse<CallSession[]>> {
    const response = await apiClient.get<ApiResponse<CallSession[]>>(`/calls/device/${deviceId}`);
    return response.data;
  },
};
