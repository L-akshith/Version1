export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role_id: string | null;
  role_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  created_at: string;
  updated_at: string;
}

export interface APIResponse<T = any> {
  success: boolean;
  message: string;
  data: T | null;
  errors: Array<{
    field?: string;
    message: string;
    type?: string;
  }>;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  total: number;
  skip: number;
  limit: number;
  errors: any[];
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource: string;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  status_code: number | null;
  endpoint: string | null;
  execution_time_ms: number | null;
  created_at: string;
}

export interface Exam {
  id: string;
  exam_code: string;
  exam_name: string;
  conducting_authority: string;
  year: number;
  exam_date: string;
  description: string | null;
  status: string;
  created_by: string;
  creator_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExamStatistics {
  total: number;
  draft: number;
  scheduled: number;
  active: number;
  completed: number;
  archived: number;
}

export interface Subject {
  id: string;
  exam_id: string;
  subject_code: string;
  subject_name: string;
  language: string;
  description: string | null;
  status: string;
  created_by: string;
  exam_name: string | null;
  creator_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubjectStatistics {
  total: number;
  draft: number;
  active: number;
  archived: number;
}

export interface QuestionPaper {
  id: string;
  subject_id: string;
  paper_code: string;
  title: string;
  version: number;
  description: string | null;
  status: string;
  file_name: string;
  original_file_name: string;
  storage_path: string;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  uploaded_by: string;
  approved_by: string | null;
  upload_time: string;
  subject_name: string | null;
  exam_name: string | null;
  uploader_name: string | null;
  approver_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface QuestionPaperVersion {
  id: string;
  version: number;
  status: string;
  file_name: string;
  original_file_name: string;
  file_size: number;
  sha256_hash: string;
  uploaded_by: string;
  uploader_name: string | null;
  upload_time: string;
  created_at: string;
}

export interface QuestionPaperStatistics {
  total: number;
  draft: number;
  uploaded: number;
  under_review: number;
  approved: number;
  rejected: number;
  archived: number;
}
