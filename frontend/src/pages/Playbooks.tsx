import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

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
  const [showImport, setShowImport] = useState(false)
  const [newYamlName, setNewYamlName] = useState('')
  const [yamlContent, setYamlContent] = useState('')

  useEffect(() => {
    fetchPlaybooks()
  }, [])

  const handleImportYaml = async () => {
    if (!newYamlName || !yamlContent) {
      alert("Name and YAML content are required")
      return
    }
    try {
      await api.post('/playbooks/', {
        name: newYamlName,
        yaml_content: yamlContent,
        mitre_tactics: [],
        mitre_techniques: []
      })
      setShowImport(false)
      setNewYamlName('')
      setYamlContent('')
      fetchPlaybooks()
    } catch (e) {
      console.error(e)
      alert("Failed to import YAML playbook")
    }
  }

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
        <div className="flex space-x-2">
          <Button onClick={() => setShowImport(!showImport)} variant="outline">
            Import YAML
          </Button>
          <Link to="/playbooks/builder" className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            Open Builder
          </Link>
        </div>
      </div>

      {showImport && (
        <Card>
          <CardHeader>
            <CardTitle>Import Playbook YAML</CardTitle>
            <CardDescription>Paste the YAML definition of your playbook here.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input value={newYamlName} onChange={e => setNewYamlName(e.target.value)} placeholder="e.g. My Custom Playbook" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">YAML Content</label>
              <textarea 
                className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                value={yamlContent}
                onChange={e => setYamlContent(e.target.value)}
                placeholder="name: My Custom Playbook&#10;steps:&#10;  ..."
              />
            </div>
            <Button onClick={handleImportYaml}>Save Playbook</Button>
          </CardContent>
        </Card>
      )}

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
