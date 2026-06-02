import apiClient from "./api";
import type { ApiResponse, Conversation } from "@/types";

export const conversationsService = {
  async getCurrent(): Promise<ApiResponse<Conversation | null>> {
    const response = await apiClient.get<ApiResponse<Conversation | null>>(
      "/conversations/current",
    );
    return response.data;
  },

  async selectLanguage(
    callSessionId: number,
    language: "english" | "hindi" | "gujarati",
  ): Promise<ApiResponse<Conversation>> {
    const response = await apiClient.post<ApiResponse<Conversation>>(
      `/conversations/call/${callSessionId}/language`,
      { language },
    );
    return response.data;
  },

  async recordAnswer(
    callSessionId: number,
    answer: string,
  ): Promise<ApiResponse<Conversation>> {
    const response = await apiClient.post<ApiResponse<Conversation>>(
      `/conversations/call/${callSessionId}/answers`,
      { answer },
    );
    return response.data;
  },
};
