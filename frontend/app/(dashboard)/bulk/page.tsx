"use client"

import { useState, useCallback } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { verifyBulk, getJob } from "@/lib/api"
import { CsvUploader } from "@/components/csv-uploader"
import { DonutChart } from "@/components/donut-chart"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { toast } from "sonner"
import { Download, RefreshCw } from "lucide-react"
import type { JobStatusResponse, VerificationStatus } from "@/types/api"
import { cn } from "@/lib/utils"

type Filter = "all" | "deliverable" | "risky" | "undeliverable"

const statusBadge: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
}

export default function BulkPage() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>("all")

  const { mutate: startJob, isPending: uploading } = useMutation({
    mutationFn: verifyBulk,
    onSuccess: (data) => {
      setJobId(data.job_id)
      toast.success(`Job started — ${data.total} emails queued`)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const d = query.state.data as JobStatusResponse | undefined
      if (!d) return 2000
      return d.status === "running" || d.status === "queued" ? 2000 : false
    },
  })

  const handleFile = useCallback(
    (file: File) => {
      setJobId(null)
      startJob(file)
    },
    [startJob]
  )

  const pct = job
    ? Math.round((job.processed / Math.max(job.total_emails, 1)) * 100)
    : 0

  const isRunning = job?.status === "running" || job?.status === "queued"

  function downloadClean() {
    if (!job?.result_csv_url) {
      toast.info("CSV URL not available — download from your backend storage.")
      return
    }
    window.open(job.result_csv_url, "_blank")
  }

  const stats = job
    ? [
        { label: "Deliverable", count: job.deliverable_count, color: "text-green-700" },
        { label: "Risky", count: job.risky_count, color: "text-amber-700" },
        { label: "Undeliverable", count: job.undeliverable_count, color: "text-red-700" },
        { label: "Dead Domain", count: job.dead_domain_count, color: "text-red-600" },
        { label: "Unknown", count: job.unknown_count, color: "text-gray-600" },
      ]
    : []

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Bulk Verify</h1>
        <p className="text-muted-foreground mt-1">
          Upload a CSV with an &quot;email&quot; column to verify up to 10,000 addresses.
        </p>
      </div>

      <CsvUploader onFile={handleFile} disabled={uploading || isRunning} />

      {uploading && (
        <p className="text-sm text-center text-muted-foreground">Uploading file…</p>
      )}

      {jobId && (
        <div className="space-y-6">
          {/* Status header */}
          {jobLoading ? (
            <Skeleton className="h-8 w-48" />
          ) : job ? (
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">
                  {job.processed} / {job.total_emails} verified
                </span>
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-medium",
                    statusBadge[job.status]
                  )}
                >
                  {job.status}
                </span>
                {isRunning && (
                  <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
                )}
              </div>
              {job.status === "completed" && (
                <Button size="sm" variant="outline" onClick={downloadClean}>
                  <Download className="h-4 w-4 mr-2" />
                  Download clean CSV
                </Button>
              )}
            </div>
          ) : null}

          {job && (
            <Progress value={pct} className="h-2" />
          )}

          {/* Summary cards */}
          {job && job.processed > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {stats.map((s) => (
                <Card key={s.label} className="text-center py-4">
                  <p className={cn("text-2xl font-bold", s.color)}>{s.count}</p>
                  <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
                </Card>
              ))}
            </div>
          )}

          {/* Donut chart */}
          {job && job.status === "completed" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Result breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <DonutChart job={job} />
              </CardContent>
            </Card>
          )}

          {/* Filter tabs placeholder — results come from download */}
          {job && job.status === "completed" && (
            <Card>
              <CardContent className="pt-6">
                <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
                  <TabsList className="mb-4">
                    <TabsTrigger value="all">All ({job.total_emails})</TabsTrigger>
                    <TabsTrigger value="deliverable">
                      Valid ({job.deliverable_count})
                    </TabsTrigger>
                    <TabsTrigger value="risky">Risky ({job.risky_count})</TabsTrigger>
                    <TabsTrigger value="undeliverable">
                      Invalid ({job.undeliverable_count + job.dead_domain_count})
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
                <p className="text-sm text-muted-foreground">
                  Full results available via{" "}
                  <button
                    onClick={downloadClean}
                    className="text-primary hover:underline"
                  >
                    CSV download
                  </button>
                  . The backend stores per-row results linked to this job.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
