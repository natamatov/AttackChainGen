import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Trophy, CheckSquare, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'

interface LeaderboardEntry {
  student_id: number
  student_name: string
  email: string
  total_score: number
  tasks_completed: number
  tasks_failed: number
  tasks_pending: number
}


export default function StudentDashboard() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [myStats, setMyStats] = useState<LeaderboardEntry | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [boardRes, meRes] = await Promise.all([
        api.get('/progress/leaderboard'),
        api.get('/users/me')
      ])
      const board = boardRes.data
      setLeaderboard(board)
      
      const myId = meRes.data.id
      const myEntry = board.find((e: LeaderboardEntry) => e.student_id === myId)
      if (myEntry) {
        setMyStats(myEntry)
      } else {
        // Fallback for new students
        setMyStats({
          student_id: myId,
          student_name: meRes.data.full_name,
          email: meRes.data.email,
          total_score: 0,
          tasks_completed: 0,
          tasks_failed: 0,
          tasks_pending: 0
        })
      }
    } catch (err) {
      console.error('Failed to fetch student data', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Мой Дашборд</h2>
        <p className="text-muted-foreground">Добро пожаловать. Следите за своими баллами и заданиями.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Мои Баллы</CardTitle>
            <Trophy className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{myStats?.total_score || 0}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Выполнено Заданий</CardTitle>
            <CheckSquare className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{myStats?.tasks_completed || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-white">Заданий в Ожидании</CardTitle>
            <Clock className="h-4 w-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{myStats?.tasks_pending || 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center justify-between">
              Быстрый доступ
            </CardTitle>
            <CardDescription>Перейдите к решению заданий.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col space-y-4">
              <div className="bg-slate-900 border border-slate-700 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">Мои Задания</h4>
                  <p className="text-sm text-slate-400">Просмотр и сдача CTF заданий</p>
                </div>
                <Link to="/assignments" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-medium text-sm transition-colors">
                  Перейти
                </Link>
              </div>
              
              <div className="bg-slate-900 border border-slate-700 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">Инструкция</h4>
                  <p className="text-sm text-slate-400">Гайд по выполнению симуляций</p>
                </div>
                <Link to="/instructions" className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded font-medium text-sm transition-colors">
                  Читать
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Лидерборд</CardTitle>
            <CardDescription>Топ студентов (По баллам).</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-slate-400">Загрузка...</div>
            ) : (
              <div className="relative w-full overflow-auto">
                <table className="w-full caption-bottom text-sm text-left">
                  <thead className="[&_tr]:border-b border-slate-700 text-slate-400">
                    <tr className="border-b transition-colors">
                      <th className="h-12 px-4 font-medium">#</th>
                      <th className="h-12 px-4 font-medium">Студент</th>
                      <th className="h-12 px-4 font-medium text-right">Баллы</th>
                    </tr>
                  </thead>
                  <tbody className="[&_tr:last-child]:border-0 text-slate-300">
                    {leaderboard.slice(0, 10).map((entry, idx) => (
                      <tr key={entry.student_id} className={`border-b border-slate-700 transition-colors ${entry.student_id === myStats?.student_id ? 'bg-indigo-900/20 font-semibold' : ''}`}>
                        <td className="p-4">{idx + 1}</td>
                        <td className="p-4">{entry.student_name || entry.email.split('@')[0]}</td>
                        <td className="p-4 text-right text-yellow-400">{entry.total_score}</td>
                      </tr>
                    ))}
                    {leaderboard.length === 0 && (
                      <tr>
                        <td colSpan={3} className="p-4 text-center text-slate-500">Пока нет участников.</td>
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
