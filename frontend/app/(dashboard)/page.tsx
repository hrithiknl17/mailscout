"use client"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { verifySingle } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { VerifyResultCard } from "@/components/verify-result-card"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { UsageBar } from "@/components/usage-bar"
import { toast } from "sonner"
import { Search } from "lucide-react"
import type { VerificationResult } from "@/types/api"

export default function DashboardPage() {
  const [email, setEmail] = useState("")
  const [result, setResult] = useState<VerificationResult | null>(null)

  const { mutate, isPending } = useMutation({
    mutationFn: verifySingle,
    onSuccess: (data) => setResult(data),
    onError: (err: Error) => toast.error(err.message),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = email.trim()
    if (!trimmed) return
    setResult(null)
    mutate(trimmed)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Verify Email</h1>
          <p className="text-muted-foreground mt-1">
            Run a single email through the 4-layer verification pipeline.
          </p>
        </div>
        <UsageBar />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="email"
          placeholder="someone@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1"
          disabled={isPending}
        />
        <Button type="submit" disabled={isPending || !email.trim()}>
          <Search className="h-4 w-4 mr-2" />
          {isPending ? "Verifying…" : "Verify"}
        </Button>
      </form>

      {isPending && <ResultSkeleton />}
      {result && !isPending && <VerifyResultCard result={result} />}
    </div>
  )
}

function ResultSkeleton() {
  return (
    <Card className="border-l-4 border-l-muted">
      <CardContent className="pt-6 space-y-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-full" />
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-6 w-16 rounded-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
