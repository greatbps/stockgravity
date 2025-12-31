"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Database,
  FileText,
  TrendingUp,
  CheckSquare,
  Activity,
  History,
  Zap,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Stock Pool", href: "/stock-pool", icon: Database },
  { name: "AI Reports", href: "/ai-reports", icon: FileText },
  { name: "Trading", href: "/trading", icon: TrendingUp },
  { name: "Approval Queue", href: "/approval-queue", icon: CheckSquare },
  { name: "Active Trades", href: "/active-trades", icon: Activity },
  { name: "Trade History", href: "/trade-history", icon: History },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-sidebar-border bg-sidebar">
      <div className="flex h-full flex-col">
        {/* Logo & Title */}
        <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Zap className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-sidebar-foreground">StockGravity</h1>
            <p className="text-xs text-muted-foreground">AI Trading System</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="border-b border-sidebar-border p-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Pool Size</span>
              <Badge variant="secondary" className="text-xs">
                500
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">AI Reports</span>
              <Badge variant="secondary" className="text-xs">
                20
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Active Trades</span>
              <Badge className="bg-success text-success-foreground text-xs">8</Badge>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Updated 2 min ago</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* AI Engine Info */}
        <div className="border-t border-sidebar-border p-4">
          <div className="rounded-lg bg-sidebar-accent p-3">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs font-medium text-sidebar-foreground">AI Engine Active</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">GPT-5 Analysis v2.1</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
