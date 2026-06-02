import apiClient from "./api";
import type { ApiResponse, ADBStatus, Device, DeviceActionResult } from "@/types";

export interface DeviceListParams {
  skip?: number;
  limit?: number;
  sync?: boolean;
  adb_present_only?: boolean;
  search?: string;
  connected_only?: boolean;
}

export const devicesService = {
  async getAll(params?: DeviceListParams): Promise<ApiResponse<Device[]>> {
    const queryParams: Record<string, string | number | boolean> = {};
    if (params) {
      if (params.skip !== undefined) queryParams.skip = params.skip;
      if (params.limit !== undefined) queryParams.limit = params.limit;
      if (params.sync !== undefined) queryParams.sync = params.sync;
      if (params.adb_present_only !== undefined) queryParams.adb_present_only = params.adb_present_only;
      if (params.search) queryParams.search = params.search;
      if (params.connected_only !== undefined) queryParams.connected_only = params.connected_only;
    }
    const response = await apiClient.get<ApiResponse<Device[]>>("/devices", { params: queryParams });
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

  async getADBStatus(): Promise<ApiResponse<ADBStatus>> {
    const response = await apiClient.get<ApiResponse<ADBStatus>>("/devices/adb-status");
    return response.data;
  },

  async refreshDevice(id: number): Promise<ApiResponse<Device>> {
    const response = await apiClient.post<ApiResponse<Device>>(`/devices/${id}/refresh`);
    return response.data;
  },

  async reconnectDevice(id: number): Promise<ApiResponse<DeviceActionResult>> {
    const response = await apiClient.post<ApiResponse<DeviceActionResult>>(`/devices/${id}/reconnect`);
    return response.data;
  },

  async runDiagnostics(id: number): Promise<ApiResponse<DeviceActionResult>> {
    const response = await apiClient.post<ApiResponse<DeviceActionResult>>(`/devices/${id}/diagnostics`);
    return response.data;
  },
};
