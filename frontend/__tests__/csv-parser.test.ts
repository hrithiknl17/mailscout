import Papa from "papaparse"

function extractEmailsFromCsv(csvText: string): string[] {
  const result = Papa.parse<Record<string, string>>(csvText, {
    header: true,
    skipEmptyLines: true,
  })
  const emails: string[] = []
  for (const row of result.data) {
    const email =
      row["email"] ?? row["Email"] ?? row["EMAIL"] ?? ""
    if (email.trim()) emails.push(email.trim())
  }
  return emails
}

describe("CSV email extraction", () => {
  it("extracts emails from lowercase 'email' column", () => {
    const csv = `email,name\njohn@example.com,John\njane@example.com,Jane`
    expect(extractEmailsFromCsv(csv)).toEqual([
      "john@example.com",
      "jane@example.com",
    ])
  })

  it("extracts emails from uppercase 'EMAIL' column", () => {
    const csv = `EMAIL,NAME\nalice@test.com,Alice`
    expect(extractEmailsFromCsv(csv)).toEqual(["alice@test.com"])
  })

  it("extracts emails from title-case 'Email' column", () => {
    const csv = `Email,Name\nbob@domain.com,Bob`
    expect(extractEmailsFromCsv(csv)).toEqual(["bob@domain.com"])
  })

  it("skips empty email rows", () => {
    const csv = `email,name\njohn@example.com,John\n,Empty\njane@example.com,Jane`
    const result = extractEmailsFromCsv(csv)
    expect(result).toHaveLength(2)
    expect(result).not.toContain("")
  })

  it("trims whitespace from email values", () => {
    const csv = `email\n  padded@example.com  \nnormal@example.com`
    expect(extractEmailsFromCsv(csv)).toEqual([
      "padded@example.com",
      "normal@example.com",
    ])
  })

  it("returns empty array when no email column found", () => {
    const csv = `name,company\nJohn,Acme\nJane,Corp`
    expect(extractEmailsFromCsv(csv)).toEqual([])
  })

  it("handles single-row CSV", () => {
    const csv = `email\nonly@example.com`
    expect(extractEmailsFromCsv(csv)).toEqual(["only@example.com"])
  })
})
