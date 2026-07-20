import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Activity } from 'lucide-react'

interface SimulationProgress {
  run_id: number
  progress_current: number
  progress_total: number
  status: string
  logs?: string[]
}

export function SimulationTracker({ runId }: { runId: number | null }) {
  const [progress, setProgress] = useState<SimulationProgress | null>(null)

  useEffect(() => {
    if (!runId) return

    const ws = new WebSocket(`ws://${window.location.host}/ws/simulations/${runId}/progress`)
    
    ws.onmessage = (event) => {
      if (event.data === 'pong') return
      try {
        const data = JSON.parse(event.data)
        setProgress(data)
      } catch (err) {
        console.error('Failed to parse WS message', err)
      }
    }

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [runId])

  if (!runId || !progress) return null

  const percent = progress.progress_total > 0 
    ? Math.round((progress.progress_current / progress.progress_total) * 100) 
    : 0

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80">
      <Card className="shadow-lg border-primary/20">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary animate-pulse" />
              <span className="text-sm font-semibold">Simulation #{runId}</span>
            </div>
            <span className="text-xs font-medium uppercase text-muted-foreground">{progress.status}</span>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Progress</span>
              <span>{percent}%</span>
            </div>
            <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  progress.status === 'completed' ? 'bg-green-500' : 
                  progress.status === 'failed' ? 'bg-red-500' : 'bg-primary'
                }`}
                style={{ width: `${percent}%` }}
              />
            </div>
            <div className="text-[10px] text-muted-foreground mt-1 text-right">
              {progress.progress_current} / {progress.progress_total} steps
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
