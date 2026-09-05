export interface ExaminationCenter {
  id: string;
  center_code: string;
  name: string;
  status: string;
  public_key_pem: string | null;
  key_identifier: string | null;
  created_at: string;
}

export interface ExaminationCenterCreate {
  center_code: string;
  name: string;
}

export interface KeyProvisionRequest {
  public_key_pem: string;
  key_identifier: string;
}

export interface ReleaseSchedule {
  id: string;
  question_paper_id: string;
  release_at: string;
  status: string;
  scheduled_by: string;
  created_at: string;
}

export interface ReleaseScheduleCreate {
  release_at: string; // ISO 8601 UTC timestamp
}

// Represents the status of a release for a specific center
export interface CenterReleaseStatus {
  id: string;
  schedule_id: string;
  center_id: string;
  status: string;
  error_message: string | null;
  delivered_at: string | null;
}
