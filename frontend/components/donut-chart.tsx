"use client"

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts"
import type { JobStatusResponse } from "@/types/api"

interface DonutChartProps {
  job: JobStatusResponse
}

const SLICES = [
  { key: "deliverable_count", label: "Deliverable", color: "#16a34a" },
  { key: "risky_count", label: "Risky", color: "#d97706" },
  { key: "undeliverable_count", label: "Undeliverable", color: "#dc2626" },
  { key: "dead_domain_count", label: "Dead Domain", color: "#ef4444" },
  { key: "unknown_count", label: "Unknown", color: "#6b7280" },
] as const

export function DonutChart({ job }: DonutChartProps) {
  const data = SLICES.filter((s) => job[s.key] > 0).map((s) => ({
    name: s.label,
    value: job[s.key],
    color: s.color,
  }))

  if (data.length === 0) return null

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, idx) => (
            <Cell key={idx} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => [value, ""]} />
        <Legend iconType="circle" iconSize={8} />
      </PieChart>
    </ResponsiveContainer>
  )
}
