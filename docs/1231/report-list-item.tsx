"use client"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { TrendingUp, TrendingDown } from "lucide-react"

interface ReportListItemProps {
  report: {
    id: string
    rank: number
    code: string
    name: string
    recommendation: "buy" | "hold" | "monitor"
    score: number
    confidence: number
    priceChange: number
    summary: string
  }
  isSelected: boolean
  onClick: () => void
}

export function ReportListItem({ report, isSelected, onClick }: ReportListItemProps) {
  const recommendationColors = {
    buy: "bg-success text-success-foreground",
    hold: "bg-warning text-warning-foreground",
    monitor: "bg-info text-info-foreground",
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-lg border transition-colors",
        isSelected ? "border-primary bg-primary/10" : "border-border hover:border-primary/50 hover:bg-accent/50",
      )}
    >
      <div className="flex items-start gap-3">
        {/* Rank Badge */}
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-sm font-bold text-foreground">
          {report.rank}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold text-foreground">{report.code}</span>
                <Badge className={cn("text-xs", recommendationColors[report.recommendation])}>
                  {report.recommendation.toUpperCase()}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">{report.name}</p>
            </div>
            <div className="flex items-center gap-1 text-sm">
              {report.priceChange >= 0 ? (
                <TrendingUp className="h-4 w-4 text-success" />
              ) : (
                <TrendingDown className="h-4 w-4 text-destructive" />
              )}
              <span
                className={cn("font-mono font-medium", report.priceChange >= 0 ? "text-success" : "text-destructive")}
              >
                {report.priceChange >= 0 ? "+" : ""}
                {report.priceChange}%
              </span>
            </div>
          </div>

          {/* Metrics */}
          <div className="flex items-center gap-4 mb-2 text-xs">
            <div>
              <span className="text-muted-foreground">Score: </span>
              <span className="font-mono font-semibold text-foreground">{report.score}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Confidence: </span>
              <span className="font-mono font-semibold text-foreground">{report.confidence}%</span>
            </div>
          </div>

          {/* Summary */}
          <p className="text-xs text-muted-foreground line-clamp-2">{report.summary}</p>
        </div>
      </div>
    </button>
  )
}
