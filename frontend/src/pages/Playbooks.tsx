import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Edit2, Trash2, Plus } from 'lucide-react'

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
  const [editingId, setEditingId] = useState<number | null>(null)
  const [newYamlName, setNewYamlName] = useState('')
  const [yamlContent, setYamlContent] = useState('')
  const [defaultTemplate, setDefaultTemplate] = useState('')

  useEffect(() => {
    fetchPlaybooks()
  }, [])

  const handleImportYaml = async () => {
    if (!newYamlName || !yamlContent) {
      alert("Name and YAML content are required")
      return
    }
    try {
      if (editingId) {
        await api.put(`/playbooks/${editingId}`, {
          name: newYamlName,
          yaml_content: yamlContent
        })
      } else {
        await api.post('/playbooks/', {
          name: newYamlName,
          yaml_content: yamlContent,
          mitre_tactics: [],
          mitre_techniques: []
        })
      }
      setShowImport(false)
      setEditingId(null)
      setNewYamlName('')
      setYamlContent('')
      fetchPlaybooks()
    } catch (e: any) {
      console.error(e)
      const detail = e.response?.data?.detail || "Failed to save YAML playbook"
      alert(detail)
    }
  }

  const handleEdit = async (id: number) => {
    try {
      const res = await api.get(`/playbooks/${id}`)
      const pb = res.data
      setNewYamlName(pb.name)
      setYamlContent(pb.yaml_content || '')
      setEditingId(pb.id)
      setShowImport(true)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) {
      console.error(e)
      alert("Failed to fetch playbook details")
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this playbook?")) return
    try {
      await api.delete(`/playbooks/${id}`)
      fetchPlaybooks()
    } catch (e) {
      console.error(e)
      alert("Failed to delete playbook")
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
          <Button onClick={() => {
            setEditingId(null)
            setNewYamlName('')
            setYamlContent('')
            setShowImport(!showImport)
          }} variant="default">
            {showImport && !editingId ? 'Cancel' : <><Plus className="mr-2 h-4 w-4" /> Create / Import YAML</>}
          </Button>
          <Link to="/playbooks/builder" className="inline-flex h-10 items-center justify-center rounded-md border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-accent">
            Visual Builder
          </Link>
        </div>
      </div>

      {showImport && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Playbook YAML' : 'Create Playbook from YAML'}</CardTitle>
            <CardDescription>Edit the YAML definition of your playbook here.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input value={newYamlName} onChange={e => setNewYamlName(e.target.value)} placeholder="e.g. My Custom Playbook" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Template Override (Optional)</label>
              <div className="flex gap-2">
                <Input 
                  value={defaultTemplate} 
                  onChange={e => setDefaultTemplate(e.target.value)} 
                  placeholder="e.g. win_security_4688" 
                />
                <Button variant="secondary" onClick={() => {
                  if (!defaultTemplate) return;
                  const updatedYaml = yamlContent.replace(/template:\s*.*/g, `template: "${defaultTemplate}"`);
                  setYamlContent(updatedYaml);
                }}>
                  Apply to YAML
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">Type a template name and click Apply to replace all templates in the YAML.</p>
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
            <div className="flex space-x-2">
              <Button onClick={handleImportYaml}>{editingId ? 'Save Changes' : 'Create Playbook'}</Button>
              {editingId && (
                <Button variant="outline" onClick={() => { setShowImport(false); setEditingId(null) }}>Cancel</Button>
              )}
            </div>
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
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex-1">
                  <CardTitle>{pb.name}</CardTitle>
                  <CardDescription className="line-clamp-2 mt-1">{pb.description || 'No description provided.'}</CardDescription>
                </div>
                <div className="flex space-x-2 ml-4">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(pb.id)}>
                    <Edit2 className="h-4 w-4 text-muted-foreground hover:text-blue-500" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDelete(pb.id)}>
                    <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
                  </Button>
                </div>
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
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
