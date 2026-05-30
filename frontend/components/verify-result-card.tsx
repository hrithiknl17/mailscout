import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckPill } from "@/components/check-pill"
import type { VerificationResult, VerificationStatus } from "@/types/api"
import { cn } from "@/lib/utils"

interface VerifyResultCardProps {
  result: VerificationResult
}

const statusConfig: Record<
  VerificationStatus,
  { label: string; color: string; badgeVariant: "default" | "secondary" | "destructive" | "outline" }
> = {
  deliverable: { label: "Deliverable", color: "text-green-700", badgeVariant: "default" },
  undeliverable: { label: "Undeliverable", color: "text-red-700", badgeVariant: "destructive" },
  risky: { label: "Risky", color: "text-amber-700", badgeVariant: "secondary" },
  invalid_syntax: { label: "Invalid Syntax", color: "text-red-700", badgeVariant: "destructive" },
  dead_domain: { label: "Dead Domain", color: "text-red-700", badgeVariant: "destructive" },
  no_mail_server: { label: "No Mail Server", color: "text-red-700", badgeVariant: "destructive" },
  temporary_failure: { label: "Temp. Failure", color: "text-amber-700", badgeVariant: "secondary" },
  unknown: { label: "Unknown", color: "text-gray-600", badgeVariant: "outline" },
}

const statusBgColor: Record<VerificationStatus, string> = {
  deliverable: "border-l-green-500",
  undeliverable: "border-l-red-500",
  risky: "border-l-amber-500",
  invalid_syntax: "border-l-red-500",
  dead_domain: "border-l-red-500",
  no_mail_server: "border-l-red-500",
  temporary_failure: "border-l-amber-500",
  unknown: "border-l-gray-400",
}

function getChecks(result: VerificationResult) {
  const { status, mx_record } = result

  const syntaxFailed = status === "invalid_syntax"
  const dnsFailed = status === "dead_domain"
  const mxFailed = status === "no_mail_server"
  const smtpSkipped = syntaxFailed || dnsFailed || mxFailed || status === "risky"

  const syntaxState = syntaxFailed ? "fail" : "pass"

  const dnsState = syntaxFailed
    ? "skip"
    : dnsFailed
    ? "fail"
    : "pass"

  const mxState = syntaxFailed || dnsFailed
    ? "skip"
    : mxFailed
    ? "fail"
    : "pass"

  let smtpState: "pass" | "fail" | "skip" | "warn" = "skip"
  if (!smtpSkipped) {
    if (status === "deliverable") smtpState = "pass"
    else if (status === "undeliverable") smtpState = "fail"
    else if (status === "temporary_failure") smtpState = "warn"
    else smtpState = "warn"
  }

  return [
    {
      label: "Syntax",
      state: syntaxState,
      tooltip: "Validates email format, normalizes to lowercase, and detects role addresses like info@ or admin@.",
    },
    {
      label: "DNS",
      state: dnsState,
      tooltip: "Checks that the domain resolves to at least one A record — confirms the domain is live.",
    },
    {
      label: "MX",
      state: mxState,
      tooltip: `Looks up MX records for the domain. ${mx_record ? `Primary mail server: ${mx_record}` : "Verifies there is a mail server configured."}`,
    },
    {
      label: "SMTP",
      state: smtpState,
      tooltip: smtpSkipped
        ? "SMTP check skipped — an earlier layer failed or provider is accept-all/catch-all."
        : "Performs an SMTP handshake (RCPT TO) with the mail server to confirm the mailbox exists.",
    },
  ] as const
}

export function VerifyResultCard({ result }: VerifyResultCardProps) {
  const cfg = statusConfig[result.status]
  const checks = getChecks(result)

  return (
    <Card
      data-testid="verify-result-card"
      className={cn("border-l-4", statusBgColor[result.status])}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Verified email</p>
            <CardTitle className="text-lg font-mono break-all">{result.email}</CardTitle>
          </div>
          <div className="text-right">
            <Badge
              variant={cfg.badgeVariant}
              className={cn("text-sm px-3 py-1", cfg.badgeVariant === "default" && "bg-green-600 hover:bg-green-600")}
            >
              {cfg.label}
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">
              {Math.round(result.confidence * 100)}% confidence
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{result.reason}</p>

        <div className="flex flex-wrap gap-2">
          {checks.map((c) => (
            <CheckPill key={c.label} label={c.label} state={c.state} tooltip={c.tooltip} />
          ))}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1">
          {result.mx_record && (
            <div>
              <p className="text-xs text-muted-foreground">MX Server</p>
              <p className="text-xs font-mono mt-0.5 truncate">{result.mx_record}</p>
            </div>
          )}
          <div>
            <p className="text-xs text-muted-foreground">Catch-all</p>
            <p className="text-xs mt-0.5">{result.is_catch_all ? "Yes" : "No"}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Role address</p>
            <p className="text-xs mt-0.5">{result.is_role ? "Yes" : "No"}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
