import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'

interface Assignment {
  id: number
  simulation_id: number
  assigned_to: number
  legend: string
  status: 'pending' | 'completed' | 'failed'
  score: number
  created_at: string
}

export default function Assignments() {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitError, setSubmitError] = useState('')

  const fetchAssignments = async () => {
    try {
      const res = await api.get('/assignments/')
      setAssignments(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAssignments()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError('')
    if (!selectedAssignment) return
    
    try {
      await api.post(`/assignments/${selectedAssignment.id}/submit`, { answers })
      setSelectedAssignment(null)
      fetchAssignments()
    } catch (err: any) {
      setSubmitError(err.response?.data?.detail || 'Ошибка при отправке ответов. Возможно, артефакты не совпали.')
      // Fetch again to see if status changed to failed
      fetchAssignments()
    }
  }

  // Helper to extract input fields needed. For MVP, we might just ask them to submit JSON or specific keys.
  // Ideally, the backend would tell the frontend which fields are expected, but since `artifacts` is dynamically generated,
  // we can let the student add Key-Value pairs dynamically.
  
  const handleAddAnswerField = () => {
    const key = prompt('Введите название артефакта (например: C2 IP, Malicious Process)')
    if (key && !answers[key]) {
      setAnswers(prev => ({ ...prev, [key]: '' }))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight text-white">Мои Задания (CTF)</h1>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {assignments.map((assignment) => (
            <div
              key={assignment.id}
              className="bg-slate-800 border border-slate-700 rounded-lg p-6 flex flex-col cursor-pointer hover:border-indigo-500 transition-colors"
              onClick={() => {
                setSelectedAssignment(assignment)
                setAnswers({})
                setSubmitError('')
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white line-clamp-1">
                  Задание #{assignment.id}
                </h3>
                {assignment.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                {assignment.status === 'failed' && <XCircle className="h-5 w-5 text-red-500" />}
                {assignment.status === 'pending' && <Clock className="h-5 w-5 text-yellow-500" />}
              </div>
              
              <div className="text-sm text-slate-400 mb-4 line-clamp-3">
                {assignment.legend || 'Нет вводных данных.'}
              </div>

              <div className="mt-auto flex items-center justify-between">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                  ${assignment.status === 'completed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                    assignment.status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                    'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'}`}
                >
                  {assignment.status}
                </span>
                <span className="text-sm text-slate-300 font-mono">
                  Баллы: {assignment.score}
                </span>
              </div>
            </div>
          ))}
          
          {assignments.length === 0 && (
            <div className="col-span-full text-center py-12 text-slate-400">
              У вас пока нет активных заданий.
            </div>
          )}
        </div>
      )}

      {/* Modal for Submission */}
      {selectedAssignment && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-2xl w-full">
            <h2 className="text-xl font-bold text-white mb-4">
              Задание #{selectedAssignment.id}
            </h2>
            
            <div className="bg-slate-800 p-4 rounded-lg mb-6 border border-slate-700">
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Легенда (Контекст):</h4>
              <p className="text-sm text-slate-400 whitespace-pre-wrap">{selectedAssignment.legend}</p>
            </div>

            {selectedAssignment.status === 'pending' ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-slate-300 mb-2">Найденные артефакты (Флаги):</h4>
                  <p className="text-xs text-slate-500 mb-4">
                    Добавьте поля и введите найденные значения. Названия полей должны соответствовать ключам артефактов (например, "Attacker IP").
                  </p>
                  
                  {Object.keys(answers).length === 0 ? (
                    <div className="text-center py-4 text-sm text-slate-500 italic">
                      Нет добавленных полей.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {Object.keys(answers).map(key => (
                        <div key={key} className="flex gap-4 items-center">
                          <label className="text-sm text-slate-300 w-1/3 truncate" title={key}>{key}</label>
                          <input
                            type="text"
                            value={answers[key]}
                            onChange={(e) => setAnswers(prev => ({ ...prev, [key]: e.target.value }))}
                            className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                            placeholder="Введите значение..."
                            required
                          />
                          <button
                            type="button"
                            onClick={() => {
                              const newAnswers = { ...answers }
                              delete newAnswers[key]
                              setAnswers(newAnswers)
                            }}
                            className="text-red-400 hover:text-red-300 text-sm"
                          >
                            Удалить
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={handleAddAnswerField}
                    className="mt-4 text-sm text-indigo-400 hover:text-indigo-300"
                  >
                    + Добавить поле
                  </button>
                </div>

                {submitError && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-400 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    {submitError}
                  </div>
                )}

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAssignment(null)}
                    className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg"
                  >
                    Сдать ответ
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg border ${selectedAssignment.status === 'completed' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                  Задание {selectedAssignment.status === 'completed' ? 'успешно выполнено' : 'провалено'}. Вы набрали {selectedAssignment.score} баллов.
                </div>
                <div className="flex justify-end mt-4">
                  <button
                    onClick={() => setSelectedAssignment(null)}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg"
                  >
                    Закрыть
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
