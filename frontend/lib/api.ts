import { createClient } from "@/lib/supabase/client"
import type {
  JobResponse,
  JobStatusResponse,
  UsageResponse,
  VerificationResult,
} from "@/types/api"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function getToken(): Promise<string> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (!session?.access_token) throw new Error("Not authenticated")
  return session.access_token
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const token = await getToken()
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `API error ${res.status}`)
  }
  return res.json()
}

export async function verifySingle(email: string): Promise<VerificationResult> {
  return apiFetch("/api/verify/single", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
}

export async function verifyBulk(file: File): Promise<JobResponse> {
  const form = new FormData()
  form.append("file", file)
  const token = await getToken()
  const res = await fetch(`${BASE}/api/verify/bulk`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `API error ${res.status}`)
  }
  return res.json()
}

export async function getJob(jobId: string): Promise<JobStatusResponse> {
  return apiFetch(`/api/jobs/${jobId}`)
}

export async function getHistory(
  limit = 20,
  offset = 0
): Promise<VerificationResult[]> {
  return apiFetch(`/api/history?limit=${limit}&offset=${offset}`)
}

export async function getUsage(): Promise<UsageResponse> {
  return apiFetch("/api/usage")
}
