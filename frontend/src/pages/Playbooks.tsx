import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

interface PlaybookSummary {
  id: number
  name: string
  description: string
  mitre_tactics: string[]
  mitre_techniques: string[]
  created_at: string
}

export default function Playbooks() {
  const [playbooks, setPlaybooks] = useState<PlaybookSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlaybooks()
  }, [])

  const fetchPlaybooks = async () => {
    try {
      const res = await api.get('/playbooks/')
      setPlaybooks(res.data)
    } catch (err) {
      console.error('Failed to fetch playbooks', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Playbooks</h2>
          <p className="text-muted-foreground">Manage your attack simulation playbooks.</p>
        </div>
        <Link to="/playbooks/builder" className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          Create Playbook
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : playbooks.length === 0 ? (
          <div className="text-sm text-muted-foreground">No playbooks found. Create one!</div>
        ) : (
          playbooks.map((pb) => (
            <Card key={pb.id}>
              <CardHeader>
                <CardTitle>{pb.name}</CardTitle>
                <CardDescription className="line-clamp-2">{pb.description || 'No description provided.'}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase text-muted-foreground">Tactics</h4>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {pb.mitre_tactics.map(t => (
                      <span key={t} className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold">{t}</span>
                    ))}
                    {pb.mitre_tactics.length === 0 && <span className="text-xs text-muted-foreground">None</span>}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase text-muted-foreground">Techniques</h4>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {pb.mitre_techniques.map(t => (
                      <span key={t} className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold">{t}</span>
                    ))}
                    {pb.mitre_techniques.length === 0 && <span className="text-xs text-muted-foreground">None</span>}
                  </div>
                </div>
                <div className="pt-2 flex justify-end">
                  <Link to={`/playbooks/builder?id=${pb.id}`} className="inline-flex h-9 items-center justify-center rounded-md border border-input bg-background px-3 text-sm font-medium hover:bg-accent hover:text-accent-foreground">
                    Edit
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
