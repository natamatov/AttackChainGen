import { useState, useEffect } from 'react'
import { Card, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { ShieldAlert, Zap, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface Report {
  id: string
  name: string
  published: string
}

interface ThreatActor {
  id: string
  name: string
  description?: string
  first_seen?: string
  last_seen?: string
  reports?: Report[]
}

export default function ThreatIntel() {
  const [actors, setActors] = useState<ThreatActor[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [selectedReport, setSelectedReport] = useState<Record<string, string>>({})
  const navigate = useNavigate()

  useEffect(() => {
    fetchActors()
  }, [])

  const fetchActors = async () => {
    setLoading(true)
    try {
      const res = await api.get('/opencti/threat-actors')
      const items = res.data.items || []
      
      // Sort reports inside each actor by date descending
      items.forEach((a: ThreatActor) => {
        if (a.reports) {
          a.reports.sort((r1, r2) => new Date(r2.published).getTime() - new Date(r1.published).getTime())
        }
      })

      // Sort actors by last_seen descending
      items.sort((a: ThreatActor, b: ThreatActor) => {
        const timeA = a.last_seen ? new Date(a.last_seen).getTime() : 0
        const timeB = b.last_seen ? new Date(b.last_seen).getTime() : 0
        if (timeA !== timeB) return timeB - timeA
        return a.name.localeCompare(b.name)
      })

      setActors(items)
      
      // Initialize selected reports with the first report available for each actor
      const initialReports: Record<string, string> = {}
      items.forEach((a: ThreatActor) => {
        if (a.reports && a.reports.length > 0) {
          initialReports[a.id] = a.reports[0].id
        }
      })
      setSelectedReport(initialReports)
    } catch (e: any) {
      console.error(e)
      alert("Failed to fetch Threat Actors from OpenCTI. Check integration settings.")
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async (actorId: string, actorName: string) => {
    setGenerating(actorId)
    try {
      let url = `/opencti/generate-playbook/${actorId}?actor_name=${encodeURIComponent(actorName)}`
      if (selectedReport[actorId]) {
        url += `&report_id=${selectedReport[actorId]}`
      }
      const res = await api.post(url)
      if (res.data.playbook) {
        // We will store it in localStorage and navigate to Playbooks page where we can open the import dialog
        localStorage.setItem('opencti_draft_yaml', res.data.playbook)
        localStorage.setItem('opencti_draft_guide', res.data.guide || '')
        localStorage.setItem('opencti_draft_name', `OpenCTI: ${actorName}`)
        navigate('/playbooks')
      }
    } catch (e: any) {
      console.error(e)
      alert("Failed to generate playbook: " + (e.response?.data?.detail || e.message))
    } finally {
      setGenerating(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <ShieldAlert className="h-8 w-8 text-red-500" />
            Threat Intelligence (OpenCTI)
          </h2>
          <p className="text-muted-foreground">Dynamic Playbook Generation based on real-world APT campaigns.</p>
          <div className="mt-2 text-sm font-medium text-muted-foreground flex items-center gap-2">
            Total Threat Actors: {actors.length}
          </div>
        </div>
        <Button onClick={fetchActors} disabled={loading} variant="outline" className="gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Синхронизация...' : 'Синхронизировать фиды'}
        </Button>
      </div>

      <div className="flex flex-col gap-4">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading actors from OpenCTI...</div>
        ) : actors.length === 0 ? (
          <div className="text-sm text-muted-foreground">No threat actors found.</div>
        ) : (
          actors.map((actor) => (
            <Card key={actor.id} className="flex flex-col md:flex-row items-center justify-between p-4 gap-6">
              
              {/* Actor Info (Left) */}
              <div className="flex-1 min-w-0 w-full">
                <CardTitle className="text-lg truncate">{actor.name}</CardTitle>
                <CardDescription className="line-clamp-2 text-xs mt-1">
                  {actor.description || 'No description available in OpenCTI.'}
                </CardDescription>
                <div className="flex items-center gap-4 mt-2">
                  {actor.last_seen && (
                    <div className="text-[10px] text-muted-foreground">
                      Last seen: {new Date(actor.last_seen).toLocaleDateString()}
                    </div>
                  )}
                  <div className="text-[10px] font-medium text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded-full">
                    Инцидентов: {actor.reports?.length || 0}
                  </div>
                </div>
              </div>
              
              {/* Report Selection (Middle) */}
              <div className="flex-1 w-full md:max-w-md">
                {actor.reports && actor.reports.length > 0 ? (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1 block">Выбор инцидента (Campaign Report):</label>
                    <select 
                      className="flex h-9 w-full items-center justify-between whitespace-nowrap rounded-md border border-input bg-transparent px-3 py-2 text-xs shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                      value={selectedReport[actor.id] || ''}
                      onChange={(e) => setSelectedReport({...selectedReport, [actor.id]: e.target.value})}
                    >
                      {actor.reports.map(r => (
                        <option key={r.id} value={r.id} className="bg-background text-foreground">
                          {r.name} ({new Date(r.published).toLocaleDateString()})
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div className="text-xs text-orange-400 bg-orange-400/10 p-2 rounded border border-orange-400/20 text-center">
                    Отчеты не найдены. Будет использован общий профиль TTPs.
                  </div>
                )}
              </div>
              
              {/* Generate Button (Right) */}
              <div className="w-full md:w-auto">
                <Button 
                  className="w-full md:w-auto gap-2" 
                  onClick={() => handleGenerate(actor.id, actor.name)}
                  disabled={generating !== null}
                >
                  <Zap className="h-4 w-4" />
                  {generating === actor.id ? 'Generating...' : 'Generate Playbook'}
                </Button>
              </div>

            </Card>
          ))
        )}
      </div>
    </div>
  )
}
