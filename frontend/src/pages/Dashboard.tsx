import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity } from 'lucide-react'

interface SimulationRunSummary {
  id: number
  playbook_name: string
  stand_name: string
  status: string
  mode: string
  noise_level: string
  progress_current: number
  progress_total: number
  events_sent: number
  created_at: string
}

export default function Dashboard() {
  const [runs, setRuns] = useState<SimulationRunSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRuns()
  }, [])

  const fetchRuns = async () => {
    try {
      const res = await api.get('/simulations/')
      setRuns(res.data)
    } catch (err) {
      console.error('Failed to fetch runs', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Monitor your attack simulation runs and their status.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runs.length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Simulations</CardTitle>
          <CardDescription>A list of recent simulation runs.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : (
            <div className="relative w-full overflow-auto">
              <table className="w-full caption-bottom text-sm">
                <thead className="[&_tr]:border-b">
                  <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">ID</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Playbook</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Stand</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Progress</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody className="[&_tr:last-child]:border-0">
                  {runs.map((run) => (
                    <tr key={run.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                      <td className="p-4 align-middle font-medium">{run.id}</td>
                      <td className="p-4 align-middle">{run.playbook_name || 'N/A'}</td>
                      <td className="p-4 align-middle">{run.stand_name || 'N/A'}</td>
                      <td className="p-4 align-middle">
                        <div className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
                          run.status === 'completed' ? 'border-transparent bg-green-500 text-white' :
                          run.status === 'failed' ? 'border-transparent bg-red-500 text-white' :
                          run.status === 'running' ? 'border-transparent bg-blue-500 text-white' :
                          'border-transparent bg-secondary text-secondary-foreground'
                        }`}>
                          {run.status}
                        </div>
                      </td>
                      <td className="p-4 align-middle">
                        {run.progress_current} / {run.progress_total}
                      </td>
                      <td className="p-4 align-middle">
                        {new Date(run.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-muted-foreground">No runs found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
