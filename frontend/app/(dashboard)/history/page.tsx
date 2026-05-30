"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { getHistory } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { VerifyResultCard } from "@/components/verify-result-card"
import type { VerificationResult, VerificationStatus } from "@/types/api"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 20

const statusBadge: Record<VerificationStatus, { label: string; className: string }> = {
  deliverable: { label: "Deliverable", className: "bg-green-100 text-green-700 border-green-200" },
  undeliverable: { label: "Undeliverable", className: "bg-red-100 text-red-700 border-red-200" },
  risky: { label: "Risky", className: "bg-amber-100 text-amber-700 border-amber-200" },
  invalid_syntax: { label: "Invalid Syntax", className: "bg-red-100 text-red-700 border-red-200" },
  dead_domain: { label: "Dead Domain", className: "bg-red-100 text-red-700 border-red-200" },
  no_mail_server: { label: "No MX", className: "bg-red-100 text-red-700 border-red-200" },
  temporary_failure: { label: "Temp. Failure", className: "bg-amber-100 text-amber-700 border-amber-200" },
  unknown: { label: "Unknown", className: "bg-gray-100 text-gray-600 border-gray-200" },
}

export default function HistoryPage() {
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<VerificationResult | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["history", offset],
    queryFn: () => getHistory(PAGE_SIZE, offset),
  })

  const hasPrev = offset > 0
  const hasNext = (data?.length ?? 0) === PAGE_SIZE

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">History</h1>
        <p className="text-muted-foreground mt-1">
          Your past single-email verifications, newest first.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Verification log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !data?.length ? (
            <p className="p-6 text-sm text-muted-foreground text-center">
              No verifications yet. Try verifying an email on the Dashboard.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden sm:table-cell">Confidence</TableHead>
                  <TableHead className="hidden md:table-cell">Date</TableHead>
                  <TableHead className="w-16" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((row) => {
                  const badge = statusBadge[row.status]
                  return (
                    <TableRow
                      key={row.id}
                      className="cursor-pointer"
                      onClick={() => setSelected(row)}
                    >
                      <TableCell className="font-mono text-sm max-w-[200px] truncate">
                        {row.email}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "text-xs px-2 py-0.5 rounded-full border font-medium",
                            badge.className
                          )}
                        >
                          {badge.label}
                        </span>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                        {Math.round(row.confidence * 100)}%
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                        {new Date(row.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" className="text-xs">
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          size="sm"
          disabled={!hasPrev}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
        >
          <ChevronLeft className="h-4 w-4 mr-1" /> Previous
        </Button>
        <span className="text-sm text-muted-foreground">
          Showing {offset + 1}–{offset + (data?.length ?? 0)}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={!hasNext}
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
        >
          Next <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* Detail dialog */}
      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Verification detail</DialogTitle>
          </DialogHeader>
          {selected && <VerifyResultCard result={selected} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}
