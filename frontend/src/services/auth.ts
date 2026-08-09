import api from "./api";
import type { APIResponse, User } from "../types";

export interface LoginResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  async login(payload: Record<string, string>): Promise<APIResponse<LoginResponseData>> {
    const response = await api.post<APIResponse<LoginResponseData>>("/auth/login", payload);
    return response.data;
  },

  async register(payload: Record<string, string>): Promise<APIResponse<User>> {
    const response = await api.post<APIResponse<User>>("/auth/register", payload);
    return response.data;
  },

  async getMe(): Promise<APIResponse<User>> {
    const response = await api.get<APIResponse<User>>("/auth/me");
    return response.data;
  },
};
