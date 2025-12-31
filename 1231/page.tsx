import { Database, FileText, CheckSquare, TrendingUp } from "lucide-react"
import { AppSidebar } from "@/components/layout/app-sidebar"
import { KPICard } from "@/components/dashboard/kpi-card"
import { WorkflowProgress } from "@/components/dashboard/workflow-progress"
import { ActionItems } from "@/components/dashboard/action-items"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function Dashboard() {
  return (
    <div className="flex min-h-screen">
      <AppSidebar />

      <main className="ml-64 flex-1 p-8">
        <div className="mx-auto max-w-7xl space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
            <p className="mt-1 text-sm text-muted-foreground">System overview and next actions</p>
          </div>

          {/* KPI Cards */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <KPICard title="Stock Pool" value={500} icon={Database} variant="info" />
            <KPICard title="AI Reports Today" value={20} icon={FileText} variant="default" />
            <KPICard
              title="Approval Queue"
              value={5}
              icon={CheckSquare}
              variant="warning"
              trend={{ value: "+2 from yesterday", positive: false }}
            />
            <KPICard
              title="Active Trades"
              value={8}
              icon={TrendingUp}
              variant="success"
              trend={{ value: "+12.5% P/L", positive: true }}
            />
          </div>

          {/* Workflow Progress */}
          <Card>
            <CardContent className="p-6">
              <WorkflowProgress />
            </CardContent>
          </Card>

          {/* Action Items & Status Distribution */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ActionItems />
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Status Distribution</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Approved</span>
                      <span className="font-medium text-foreground">40%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div className="h-2 rounded-full bg-success w-[40%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Monitoring</span>
                      <span className="font-medium text-foreground">35%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div className="h-2 rounded-full bg-info w-[35%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Pending</span>
                      <span className="font-medium text-foreground">25%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted">
                      <div className="h-2 rounded-full bg-warning w-[25%]" />
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <h4 className="text-sm font-semibold text-foreground mb-3">AI Score Range</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">High (80-100)</span>
                      <span className="font-mono text-foreground">8 stocks</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Medium (60-79)</span>
                      <span className="font-mono text-foreground">7 stocks</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Low (40-59)</span>
                      <span className="font-mono text-foreground">5 stocks</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
