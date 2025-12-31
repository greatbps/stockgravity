import type { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface KPICardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: string
    positive: boolean
  }
  variant?: "default" | "success" | "warning" | "info"
}

export function KPICard({ title, value, icon: Icon, trend, variant = "default" }: KPICardProps) {
  const variantStyles = {
    default: "border-border",
    success: "border-success/30 bg-success/5",
    warning: "border-warning/30 bg-warning/5",
    info: "border-info/30 bg-info/5",
  }

  return (
    <Card className={cn("border-2", variantStyles[variant])}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="mt-2 text-3xl font-bold text-foreground">{value}</p>
            {trend && (
              <p className={cn("mt-1 text-xs", trend.positive ? "text-success" : "text-destructive")}>{trend.value}</p>
            )}
          </div>
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded-lg",
              variant === "success" && "bg-success/20",
              variant === "warning" && "bg-warning/20",
              variant === "info" && "bg-info/20",
              variant === "default" && "bg-muted",
            )}
          >
            <Icon
              className={cn(
                "h-6 w-6",
                variant === "success" && "text-success",
                variant === "warning" && "text-warning",
                variant === "info" && "text-info",
                variant === "default" && "text-foreground",
              )}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
