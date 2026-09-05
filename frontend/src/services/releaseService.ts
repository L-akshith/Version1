import api from "./api";
import type { 
  ReleaseSchedule, 
  ReleaseScheduleCreate 
} from "../types";

export const releaseService = {
  /**
   * Schedule a release for an approved question paper.
   * Requires papers:release permission.
   */
  scheduleRelease: async (paperId: string, data: ReleaseScheduleCreate): Promise<ReleaseSchedule> => {
    const response = await api.post<ReleaseSchedule>(`/release/${paperId}/schedule`, data);
    return response.data;
  },

  /**
   * Manually execute a scheduled release.
   * Requires papers:release permission.
   */
  executeRelease: async (paperId: string): Promise<{ status: string }> => {
    const response = await api.post<{ status: string }>(`/release/${paperId}/execute`);
    return response.data;
  },

  getUpcomingSchedules: async (): Promise<ReleaseSchedule[]> => {
    const response = await api.get<{ data: ReleaseSchedule[] }>("/release/schedules/upcoming");
    return response.data.data;
  }
};
