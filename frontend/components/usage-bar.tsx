"use client"

import { useQuery } from "@tanstack/react-query"
import { getUsage } from "@/lib/api"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"

export function UsageBar() {
  const { data, isLoading } = useQuery({
    queryKey: ["usage"],
    queryFn: getUsage,
  })

  if (isLoading) return <Skeleton className="h-6 w-48" />
  if (!data) return null

  const pct = Math.round((data.used_this_month / data.monthly_limit) * 100)

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted-foreground whitespace-nowrap">
        {data.used_this_month} / {data.monthly_limit} this month
      </span>
      <Progress value={pct} className="w-28 h-2" />
    </div>
  )
}
