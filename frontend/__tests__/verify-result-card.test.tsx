import "@testing-library/jest-dom"
import { render, screen } from "@testing-library/react"
import { VerifyResultCard } from "@/components/verify-result-card"
import type { VerificationResult } from "@/types/api"

const base: VerificationResult = {
  id: "abc-123",
  email: "test@example.com",
  status: "deliverable",
  confidence: 0.95,
  reason: "SMTP 250 OK",
  mx_record: "aspmx.l.google.com",
  is_catch_all: false,
  is_disposable: false,
  is_role: false,
  created_at: "2026-05-23T10:00:00Z",
}

describe("VerifyResultCard", () => {
  it("renders email address", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("test@example.com")).toBeInTheDocument()
  })

  it("shows Deliverable badge for deliverable status", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("Deliverable")).toBeInTheDocument()
  })

  it("shows confidence percentage", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("95% confidence")).toBeInTheDocument()
  })

  it("renders all 4 check pills", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("Syntax")).toBeInTheDocument()
    expect(screen.getByText("DNS")).toBeInTheDocument()
    expect(screen.getByText("MX")).toBeInTheDocument()
    expect(screen.getByText("SMTP")).toBeInTheDocument()
  })

  it("shows Undeliverable badge for undeliverable status", () => {
    render(
      <VerifyResultCard result={{ ...base, status: "undeliverable", reason: "SMTP rejected" }} />
    )
    expect(screen.getByText("Undeliverable")).toBeInTheDocument()
  })

  it("shows Invalid Syntax badge for invalid_syntax status", () => {
    render(
      <VerifyResultCard
        result={{
          ...base,
          status: "invalid_syntax",
          confidence: 1.0,
          reason: "Missing @ symbol",
          mx_record: null,
        }}
      />
    )
    expect(screen.getByText("Invalid Syntax")).toBeInTheDocument()
  })

  it("shows reason text", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("SMTP 250 OK")).toBeInTheDocument()
  })

  it("shows MX record when present", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByText("aspmx.l.google.com")).toBeInTheDocument()
  })

  it("shows catch-all as Yes when true", () => {
    render(<VerifyResultCard result={{ ...base, is_catch_all: true }} />)
    const catchAllValues = screen.getAllByText("Yes")
    expect(catchAllValues.length).toBeGreaterThan(0)
  })

  it("has data-testid attribute", () => {
    render(<VerifyResultCard result={base} />)
    expect(screen.getByTestId("verify-result-card")).toBeInTheDocument()
  })
})
