import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { CheckCircle2, XCircle, MinusCircle, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

type CheckState = "pass" | "fail" | "skip" | "warn"

interface CheckPillProps {
  label: string
  state: CheckState
  tooltip: string
}

const stateConfig: Record<CheckState, { icon: React.ComponentType<{ className?: string }>, className: string }> = {
  pass: { icon: CheckCircle2, className: "bg-green-100 text-green-700 border-green-200" },
  fail: { icon: XCircle, className: "bg-red-100 text-red-700 border-red-200" },
  skip: { icon: MinusCircle, className: "bg-gray-100 text-gray-500 border-gray-200" },
  warn: { icon: AlertCircle, className: "bg-amber-100 text-amber-700 border-amber-200" },
}

export function CheckPill({ label, state, tooltip }: CheckPillProps) {
  const { icon: Icon, className } = stateConfig[state]
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-medium cursor-default select-none",
              className
            )}
          >
            <Icon className="h-3 w-3" />
            {label}
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[220px] text-xs">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
