import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Users, CheckSquare } from 'lucide-react'

interface SimulationRunSummary {
  id: number
  playbook_name: string
  stand_name: string
  status: string
  progress_current: number
  progress_total: number
  created_at: string
}

interface LeaderboardEntry {
  student_id: number
  student_name: string
  email: string
  total_score: number
  tasks_completed: number
  tasks_failed: number
  tasks_pending: number
}

export default function InstructorDashboard() {
  const [runs, setRuns] = useState<SimulationRunSummary[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [runsRes, boardRes] = await Promise.all([
        api.get('/simulations/'),
        api.get('/progress/leaderboard')
      ])
      setRuns(runsRes.data)
      setLeaderboard(boardRes.data)
    } catch (err) {
      console.error('Failed to fetch instructor data', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Панель Инструктора</h2>
        <p className="text-muted-foreground">Управление симуляциями и учет успеваемости студентов.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Всего Симуляций</CardTitle>
            <Activity className="h-4 w-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{runs.length}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Всего Студентов</CardTitle>
            <Users className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{leaderboard.length}</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Решенных Заданий</CardTitle>
            <CheckSquare className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {leaderboard.reduce((acc, curr) => acc + curr.tasks_completed, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Успеваемость Студентов</CardTitle>
            <CardDescription>Общий рейтинг и прогресс.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-slate-400">Загрузка...</div>
            ) : (
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm text-left">
                  <thead className="[&_tr]:border-b border-slate-700 text-slate-400">
                    <tr className="border-b transition-colors">
                      <th className="h-12 px-4 font-medium">Студент</th>
                      <th className="h-12 px-4 font-medium">Баллы</th>
                      <th className="h-12 px-4 font-medium">Выполнено</th>
                      <th className="h-12 px-4 font-medium">В процессе</th>
                    </tr>
                  </thead>
                  <tbody className="[&_tr:last-child]:border-0 text-slate-300">
                    {leaderboard.map((entry, idx) => (
                      <tr key={entry.student_id} className="border-b border-slate-700 transition-colors">
                        <td className="p-4 font-medium">
                          {idx + 1}. {entry.student_name}
                          <div className="text-xs text-slate-500 font-normal">{entry.email}</div>
                        </td>
                        <td className="p-4 font-bold text-indigo-400">{entry.total_score}</td>
                        <td className="p-4 text-green-400">{entry.tasks_completed}</td>
                        <td className="p-4 text-yellow-400">{entry.tasks_pending}</td>
                      </tr>
                    ))}
                    {leaderboard.length === 0 && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-slate-500">Нет студентов.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Последние Симуляции</CardTitle>
            <CardDescription>Статус запущенных стендов.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-slate-400">Загрузка...</div>
            ) : (
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm text-left">
                  <thead className="[&_tr]:border-b border-slate-700 text-slate-400">
                    <tr className="border-b transition-colors">
                      <th className="h-12 px-4 font-medium">ID</th>
                      <th className="h-12 px-4 font-medium">Сценарий</th>
                      <th className="h-12 px-4 font-medium">Статус</th>
                      <th className="h-12 px-4 font-medium">Дата</th>
                    </tr>
                  </thead>
                  <tbody className="[&_tr:last-child]:border-0 text-slate-300">
                    {runs.slice(0, 5).map((run) => (
                      <tr key={run.id} className="border-b border-slate-700 transition-colors">
                        <td className="p-4 font-medium">{run.id}</td>
                        <td className="p-4">{run.playbook_name || 'N/A'}</td>
                        <td className="p-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold
                            ${run.status === 'completed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                              run.status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                              run.status === 'running' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 
                              'bg-slate-500/10 text-slate-400 border border-slate-500/20'}`}>
                            {run.status}
                          </span>
                        </td>
                        <td className="p-4">
                          {new Date(run.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                    {runs.length === 0 && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center text-slate-500">Симуляций пока нет.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
