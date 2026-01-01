import { AlertCircle, FileText, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const actions = [
  {
    id: 1,
    type: "review",
    title: "5 AI Reports need review",
    description: "Top 20 stocks analyzed, awaiting approval decision",
    priority: "high",
    icon: FileText,
  },
  {
    id: 2,
    type: "reevaluate",
    title: "3 Stocks need re-evaluation",
    description: "Price movement triggers requiring attention",
    priority: "medium",
    icon: RefreshCw,
  },
  {
    id: 3,
    type: "warning",
    title: "2 Active trades approaching stop-loss",
    description: "Monitor positions: Samsung Electronics, NAVER",
    priority: "high",
    icon: AlertCircle,
  },
]

export function ActionItems() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Action Needed</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {actions.map((action) => (
          <div key={action.id} className="flex items-start justify-between gap-4 rounded-lg border border-border p-4">
            <div className="flex gap-3">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                  action.priority === "high" ? "bg-warning/20" : "bg-info/20"
                }`}
              >
                <action.icon className={`h-5 w-5 ${action.priority === "high" ? "text-warning" : "text-info"}`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-foreground">{action.title}</h4>
                  {action.priority === "high" && (
                    <Badge variant="destructive" className="text-xs">
                      High Priority
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{action.description}</p>
              </div>
            </div>
            <Button size="sm" variant="outline">
              View
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
