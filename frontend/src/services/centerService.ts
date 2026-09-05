import api from "./api";
import type { 
  ExaminationCenter, 
  ExaminationCenterCreate, 
  KeyProvisionRequest
} from "../types";

export const centerService = {
  /**
   * Register a new examination center.
   * Requires system:manage permission.
   */
  registerCenter: async (data: ExaminationCenterCreate): Promise<ExaminationCenter> => {
    const response = await api.post<ExaminationCenter>("/centers", data);
    return response.data;
  },

  /**
   * Provision a public key for a center.
   * Requires system:manage permission.
   */
  provisionKey: async (centerId: string, data: KeyProvisionRequest): Promise<ExaminationCenter> => {
    const response = await api.post<ExaminationCenter>(`/centers/${centerId}/keys`, data);
    return response.data;
  },

  getCenters: async (): Promise<ExaminationCenter[]> => {
    const response = await api.get<{ data: ExaminationCenter[] }>("/centers");
    return response.data.data;
  },

  deactivateCenter: async (centerId: string): Promise<ExaminationCenter> => {
    const response = await api.post<ExaminationCenter>(`/centers/${centerId}/deactivate`);
    return response.data;
  }
};
