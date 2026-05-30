import { redirect } from "next/navigation"
import { createClient } from "@/lib/supabase/server"
import { Nav } from "@/components/nav"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) redirect("/login")

  return (
    <div className="min-h-screen flex flex-col">
      <Nav userEmail={user.email ?? ""} />
      <main className="flex-1 container py-8">{children}</main>
    </div>
  )
}
