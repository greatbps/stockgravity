import { CheckCircle2, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

const steps = [
  { name: "Filter", count: 2790, status: "complete" },
  { name: "Pool", count: 500, status: "complete" },
  { name: "AI Analysis", count: 20, status: "active" },
  { name: "Approval", count: 5, status: "pending" },
  { name: "Trading", count: 8, status: "pending" },
]

export function WorkflowProgress() {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Workflow Progress</h3>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.name} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2",
                  step.status === "complete" && "border-success bg-success/20",
                  step.status === "active" && "border-warning bg-warning/20",
                  step.status === "pending" && "border-muted bg-muted",
                )}
              >
                {step.status === "complete" ? (
                  <CheckCircle2 className="h-5 w-5 text-success" />
                ) : (
                  <Circle
                    className={cn("h-5 w-5", step.status === "active" ? "text-warning" : "text-muted-foreground")}
                  />
                )}
              </div>
              <div className="mt-2 text-center">
                <p className="text-xs font-medium text-foreground">{step.name}</p>
                <p className="text-xs text-muted-foreground">{step.count}</p>
              </div>
            </div>
            {index < steps.length - 1 && (
              <div className={cn("h-0.5 flex-1 mx-2", index < 2 ? "bg-success" : "bg-muted")} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
