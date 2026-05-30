export type VerificationStatus =
  | "deliverable"
  | "undeliverable"
  | "risky"
  | "invalid_syntax"
  | "dead_domain"
  | "no_mail_server"
  | "temporary_failure"
  | "unknown"

export type JobStatus = "queued" | "running" | "completed" | "failed"

export interface VerificationResult {
  id: string
  email: string
  status: VerificationStatus
  confidence: number
  reason: string
  mx_record: string | null
  is_catch_all: boolean
  is_disposable: boolean
  is_role: boolean
  created_at: string
}

export interface JobResponse {
  job_id: string
  total: number
  status: JobStatus
}

export interface JobStatusResponse {
  id: string
  status: JobStatus
  total_emails: number
  processed: number
  deliverable_count: number
  risky_count: number
  undeliverable_count: number
  dead_domain_count: number
  unknown_count: number
  created_at: string
  completed_at: string | null
  result_csv_url: string | null
}

export interface UsageResponse {
  used_this_month: number
  monthly_limit: number
  renews_at: string
}
