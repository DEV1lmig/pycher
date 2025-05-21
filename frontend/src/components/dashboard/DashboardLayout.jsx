import { DashboardHeader } from "@/components/dashboard/DashboardHeader"

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#160f30] text-white flex">
      <div className="flex-1 flex flex-col">
        <DashboardHeader />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
