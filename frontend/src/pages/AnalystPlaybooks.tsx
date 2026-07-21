import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  BookOpenCheck, Plus, Trash2, Edit3, ChevronDown, ChevronUp,
  Link2, FileText, ClipboardList, Eye, Code2, AlertCircle
} from 'lucide-react'

interface Playbook { id: number; name: string }
interface AnalystPlaybook {
  id: number
  name: string
  description: string | null
  playbook_id: number | null
  playbook_name: string | null
  analyst_guide: string | null
  investigation_checklist: string | null
  created_at: string
  updated_at: string
}

// ────────────────────────────────────────────────────────────
// Simple Markdown renderer (no external deps)
// ────────────────────────────────────────────────────────────
function renderMarkdown(md: string): string {
  if (!md) return ''
  let html = md
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) =>
      `<pre class="md-code bg-muted p-2 rounded-md my-2 overflow-x-auto font-mono text-sm" data-lang="${lang}"><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`)
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="md-inline-code bg-muted px-1.5 py-0.5 rounded text-sm font-mono">$1</code>')
    // H1-H3
    .replace(/^### (.+)$/gm, '<h3 class="md-h3 text-lg font-semibold mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="md-h2 text-xl font-semibold mt-5 mb-3 border-b pb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="md-h1 text-2xl font-bold mt-6 mb-4">$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Checkboxes
    .replace(/^- \[x\] (.+)$/gm, '<div class="md-check flex items-center gap-2 my-1"><span class="md-checkbox text-primary font-bold">☑</span><span>$1</span></div>')
    .replace(/^- \[ \] (.+)$/gm, '<div class="md-check flex items-center gap-2 my-1"><span class="md-checkbox-empty text-muted-foreground font-bold">☐</span><span>$1</span></div>')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li class="md-li ml-6 list-disc">$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li md-oli ml-6 list-decimal">$1</li>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="md-hr my-4 border-border">')
    // Paragraphs (blank line separation)
    .replace(/\n\n/g, '</p><p class="md-p my-2">')

  return `<div class="md-container space-y-2 leading-relaxed"><p class="md-p my-2">${html}</p></div>`
}

// ────────────────────────────────────────────────────────────
// Markdown Editor with Preview toggle
// ────────────────────────────────────────────────────────────
function MarkdownEditor({
  label, value, onChange, placeholder
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string
}) {
  const [preview, setPreview] = useState(false)

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium flex items-center gap-2">
          <FileText className="h-4 w-4" />
          {label}
        </label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setPreview(!preview)}
          className="h-8"
        >
          {preview ? <><Code2 className="h-4 w-4 mr-2" /> Editor</> : <><Eye className="h-4 w-4 mr-2" /> Preview</>}
        </Button>
      </div>

      {preview ? (
        <div
          className="min-h-[220px] p-4 rounded-md border bg-muted/50 overflow-auto"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(value) }}
        />
      ) : (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          rows={12}
          className="flex min-h-[220px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 font-mono resize-y"
        />
      )}
    </div>
  )
}

// ────────────────────────────────────────────────────────────
// Card for displaying an analyst playbook
// ────────────────────────────────────────────────────────────
function APCard({
  ap, onEdit, onDelete
}: {
  ap: AnalystPlaybook; onEdit: () => void; onDelete: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [tab, setTab] = useState<'guide' | 'checklist'>('guide')

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <BookOpenCheck className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <CardTitle className="text-lg truncate">{ap.name}</CardTitle>
          </div>
          {ap.description && (
            <CardDescription className="ml-8 mt-1.5">{ap.description}</CardDescription>
          )}
          {ap.playbook_name && (
            <div className="flex items-center gap-2 ml-8 mt-3">
              <Link2 className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full border">
                Scenario: {ap.playbook_name}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-1 flex-shrink-0 ml-4">
          <Button variant="ghost" size="icon" onClick={onEdit} title="Edit">
            <Edit3 className="h-4 w-4 text-muted-foreground hover:text-blue-500" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onDelete} title="Delete">
            <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <div className="border-t">
          <div className="flex border-b bg-muted/20">
            <button
              onClick={() => setTab('guide')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                tab === 'guide'
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <FileText className="h-4 w-4" />
              Analyst Guide
            </button>
            <button
              onClick={() => setTab('checklist')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                tab === 'checklist'
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <ClipboardList className="h-4 w-4" />
              Investigation Checklist
            </button>
          </div>

          <div className="p-6">
            {tab === 'guide' ? (
              ap.analyst_guide ? (
                <div
                  className="text-sm text-foreground"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(ap.analyst_guide) }}
                />
              ) : (
                <div className="flex items-center gap-2 text-muted-foreground text-sm py-8 justify-center">
                  <AlertCircle className="h-4 w-4" />
                  No analyst guide provided.
                </div>
              )
            ) : (
              ap.investigation_checklist ? (
                <div
                  className="text-sm text-foreground"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(ap.investigation_checklist) }}
                />
              ) : (
                <div className="flex items-center gap-2 text-muted-foreground text-sm py-8 justify-center">
                  <AlertCircle className="h-4 w-4" />
                  No investigation checklist provided.
                </div>
              )
            )}
          </div>
        </div>
      )}
    </Card>
  )
}

// ────────────────────────────────────────────────────────────
// Main Page
// ────────────────────────────────────────────────────────────
export default function AnalystPlaybooks() {
  const [items, setItems] = useState<AnalystPlaybook[]>([])
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [loading, setLoading] = useState(true)
  const [showImport, setShowImport] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [playbookId, setPlaybookId] = useState<number | ''>('')
  const [guide, setGuide] = useState('')
  const [checklist, setChecklist] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [apRes, pbRes] = await Promise.all([
        api.get('/analyst-playbooks/'),
        api.get('/playbooks/'),
      ])
      setItems(apRes.data)
      setPlaybooks(pbRes.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleEdit = (ap: AnalystPlaybook) => {
    setEditingId(ap.id)
    setName(ap.name)
    setDescription(ap.description || '')
    setPlaybookId(ap.playbook_id ?? '')
    setGuide(ap.analyst_guide || '')
    setChecklist(ap.investigation_checklist || '')
    setShowImport(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCreateNew = () => {
    setEditingId(null)
    setName('')
    setDescription('')
    setPlaybookId('')
    setGuide('')
    setChecklist('')
    setShowImport(!showImport)
  }

  const handleSave = async () => {
    if (!name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    try {
      const data = {
        name: name.trim(),
        description: description || null,
        playbook_id: playbookId !== '' ? Number(playbookId) : null,
        analyst_guide: guide || null,
        investigation_checklist: checklist || null,
      }
      if (editingId) {
        await api.patch(`/analyst-playbooks/${editingId}`, data)
      } else {
        await api.post('/analyst-playbooks/', data)
      }
      setShowImport(false)
      await load()
    } catch (e: any) {
      setError(e.message ?? 'Failed to save analyst playbook')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this analyst playbook?')) return
    await api.delete(`/analyst-playbooks/${id}`)
    await load()
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analyst Playbooks</h2>
          <p className="text-muted-foreground">SOC investigation guides and checklists.</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={handleCreateNew} variant="default">
            {showImport && !editingId ? 'Cancel' : <><Plus className="mr-2 h-4 w-4" /> Create Playbook</>}
          </Button>
        </div>
      </div>

      {showImport && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Analyst Playbook' : 'Create Analyst Playbook'}</CardTitle>
            <CardDescription>Define investigation steps, KQL queries, and requirements.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2 space-y-2">
                <label className="text-sm font-medium">Name *</label>
                <Input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. Investigation Guide: Brute Force"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Short description..."
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Linked Attack Scenario (Optional)</label>
                <select
                  value={playbookId}
                  onChange={e => setPlaybookId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="">— Unlinked —</option>
                  {playbooks.map(pb => (
                    <option key={pb.id} value={pb.id}>{pb.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <MarkdownEditor
              label="Analyst Guide (Markdown)"
              value={guide}
              onChange={setGuide}
              placeholder={`# Analyst Guide: Brute Force\n\n## 1. Detection\n\n**KQL in Kibana:**\n\`\`\`kql\nevent.code: "4625"\n\`\`\``}
            />

            <MarkdownEditor
              label="Investigation Checklist (Markdown)"
              value={checklist}
              onChange={setChecklist}
              placeholder={`# Checklist: Brute Force\n\n## Artifacts\n- [ ] Attacker IP\n- [ ] Compromised User`}
            />

            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm bg-destructive/10 border border-destructive/20 rounded-md px-4 py-3">
                <AlertCircle className="h-4 w-4" /> {error}
              </div>
            )}

            <div className="flex space-x-2 pt-2">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Playbook'}
              </Button>
              {editingId && (
                <Button variant="outline" onClick={() => setShowImport(false)}>Cancel</Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { label: 'Total Playbooks', value: items.length, icon: BookOpenCheck },
          { label: 'With Guides', value: items.filter(i => i.analyst_guide).length, icon: FileText },
          { label: 'With Checklists', value: items.filter(i => i.investigation_checklist).length, icon: ClipboardList },
        ].map(({ label, value, icon: Icon }, idx) => (
          <Card key={idx}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-muted-foreground">No analyst playbooks found. Create one!</div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map(ap => (
            <APCard
              key={ap.id}
              ap={ap}
              onEdit={() => handleEdit(ap)}
              onDelete={() => handleDelete(ap.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
