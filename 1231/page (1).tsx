"use client"

import { useState } from "react"
import { AppSidebar } from "@/components/layout/app-sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, AlertCircle, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

const mockQueue = [
  {
    id: "1",
    code: "005930",
    name: "Samsung Electronics",
    price: 68500,
    priceChange: 3.2,
    aiScore: 92,
    addedDate: "2025-01-15",
    status: "pending",
  },
  {
    id: "2",
    code: "035420",
    name: "NAVER",
    price: 185000,
    priceChange: 2.8,
    aiScore: 89,
    addedDate: "2025-01-15",
    status: "pending",
  },
  {
    id: "3",
    code: "035720",
    name: "Kakao",
    price: 45200,
    priceChange: 4.1,
    aiScore: 86,
    addedDate: "2025-01-14",
    status: "pending",
  },
]

export default function ApprovalQueuePage() {
  const [selectedStock, setSelectedStock] = useState(mockQueue[0])

  return (
    <div className="flex min-h-screen">
      <AppSidebar />

      <main className="ml-64 flex-1 p-8">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Approval Queue</h1>
            <p className="mt-1 text-sm text-muted-foreground">Review and approve stocks for trading</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left - Queue Table */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Pending Approvals ({mockQueue.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {mockQueue.map((stock) => (
                      <button
                        key={stock.id}
                        onClick={() => setSelectedStock(stock)}
                        className={cn(
                          "w-full rounded-lg border p-4 text-left transition-colors",
                          selectedStock.id === stock.id
                            ? "border-primary bg-primary/10"
                            : "border-border hover:border-primary/50",
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm font-semibold text-foreground">{stock.code}</span>
                                <Badge variant="secondary" className="text-xs">
                                  Score: {stock.aiScore}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-0.5">{stock.name}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <div className="font-mono text-sm font-semibold text-foreground">
                                ₩{stock.price.toLocaleString()}
                              </div>
                              <div
                                className={cn(
                                  "text-xs font-medium flex items-center gap-1",
                                  stock.priceChange >= 0 ? "text-success" : "text-destructive",
                                )}
                              >
                                {stock.priceChange >= 0 ? (
                                  <TrendingUp className="h-3 w-3" />
                                ) : (
                                  <TrendingDown className="h-3 w-3" />
                                )}
                                {stock.priceChange >= 0 ? "+" : ""}
                                {stock.priceChange}%
                              </div>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {stock.addedDate}
                            </Badge>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right - Detail Panel */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Quick Analysis</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-mono text-xl font-bold text-foreground">{selectedStock.code}</h3>
                    <p className="text-sm text-muted-foreground">{selectedStock.name}</p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Current Price</span>
                      <span className="font-mono text-lg font-semibold text-foreground">
                        ₩{selectedStock.price.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">AI Score</span>
                      <Badge className="bg-success text-success-foreground">{selectedStock.aiScore}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Price Change</span>
                      <span
                        className={cn(
                          "font-mono text-sm font-semibold",
                          selectedStock.priceChange >= 0 ? "text-success" : "text-destructive",
                        )}
                      >
                        {selectedStock.priceChange >= 0 ? "+" : ""}
                        {selectedStock.priceChange}%
                      </span>
                    </div>
                  </div>

                  <div className="rounded-lg bg-muted p-4">
                    <div className="flex items-start gap-2">
                      <BarChart3 className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <div className="flex-1">
                        <p className="text-xs text-muted-foreground mb-2">Technical Indicators</p>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">RSI:</span>
                            <span className="font-mono text-foreground">68.5</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">MACD:</span>
                            <span className="font-mono text-success">Bullish</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Volume:</span>
                            <span className="font-mono text-success">High</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg bg-warning/10 border border-warning/30 p-3">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 text-warning mt-0.5" />
                      <div>
                        <p className="text-xs font-semibold text-foreground">Risk Assessment</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Moderate volatility. Suggested position: 2-3% of portfolio
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Actions */}
              <div className="space-y-2">
                <Button size="lg" className="w-full bg-success text-success-foreground hover:bg-success/90">
                  Start Trading
                </Button>
                <Button size="lg" variant="outline" className="w-full bg-transparent">
                  Re-evaluate
                </Button>
                <Button size="lg" variant="destructive" className="w-full">
                  Remove from Queue
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
