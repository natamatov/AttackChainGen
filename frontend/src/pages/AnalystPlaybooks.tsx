import { useState, useEffect, useRef } from 'react'
import api from '@/lib/api'
import {
  BookOpenCheck, Plus, Trash2, Edit3, Save, X, ChevronDown, ChevronUp,
  Link2, FileText, ClipboardList, Eye, Code2, AlertCircle, CheckSquare
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
      `<pre class="md-code" data-lang="${lang}"><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`)
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
    // H1-H3
    .replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Checkboxes
    .replace(/^- \[x\] (.+)$/gm, '<div class="md-check md-checked"><span class="md-checkbox">✓</span>$1</div>')
    .replace(/^- \[ \] (.+)$/gm, '<div class="md-check"><span class="md-checkbox-empty">○</span>$1</div>')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li class="md-li">$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li md-oli">$1</li>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="md-hr">')
    // Paragraphs (blank line separation)
    .replace(/\n\n/g, '</p><p class="md-p">')

  return `<p class="md-p">${html}</p>`
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
        <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-400" />
          {label}
        </label>
        <button
          type="button"
          onClick={() => setPreview(!preview)}
          className="flex items-center gap-1 text-xs px-3 py-1 rounded-full border border-white/10 text-gray-400 hover:text-white hover:border-blue-500/50 transition-all"
        >
          {preview ? <><Code2 className="h-3 w-3" /> Редактор</> : <><Eye className="h-3 w-3" /> Превью</>}
        </button>
      </div>

      {preview ? (
        <div
          className="markdown-body min-h-[220px] p-4 rounded-xl border border-white/10 bg-black/20 overflow-auto"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(value) }}
        />
      ) : (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          rows={12}
          className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-gray-200 font-mono placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y"
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
    <div className="rounded-2xl border border-white/10 bg-[#0f1117] shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between px-6 py-5 gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <BookOpenCheck className="h-5 w-5 text-blue-400 flex-shrink-0" />
            <h3 className="text-base font-semibold text-white truncate">{ap.name}</h3>
          </div>
          {ap.description && (
            <p className="text-sm text-gray-400 ml-8">{ap.description}</p>
          )}
          {ap.playbook_name && (
            <div className="flex items-center gap-2 ml-8 mt-2">
              <Link2 className="h-3 w-3 text-purple-400" />
              <span className="text-xs text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded-full border border-purple-500/20">
                Сценарий: {ap.playbook_name}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onEdit}
            className="p-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 transition-all"
            title="Редактировать"
          >
            <Edit3 className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
            title="Удалить"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-white/10">
          {/* Tabs */}
          <div className="flex border-b border-white/10">
            <button
              onClick={() => setTab('guide')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all border-b-2 ${
                tab === 'guide'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              <FileText className="h-4 w-4" />
              Руководство аналитика
            </button>
            <button
              onClick={() => setTab('checklist')}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all border-b-2 ${
                tab === 'checklist'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              <ClipboardList className="h-4 w-4" />
              Чеклист расследования
            </button>
          </div>

          <div className="p-6">
            {tab === 'guide' ? (
              ap.analyst_guide ? (
                <div
                  className="markdown-body"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(ap.analyst_guide) }}
                />
              ) : (
                <div className="flex items-center gap-2 text-gray-500 text-sm py-8 justify-center">
                  <AlertCircle className="h-4 w-4" />
                  Руководство аналитика не заполнено
                </div>
              )
            ) : (
              ap.investigation_checklist ? (
                <div
                  className="markdown-body"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(ap.investigation_checklist) }}
                />
              ) : (
                <div className="flex items-center gap-2 text-gray-500 text-sm py-8 justify-center">
                  <AlertCircle className="h-4 w-4" />
                  Чеклист расследования не заполнен
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ────────────────────────────────────────────────────────────
// Modal for Create / Edit
// ────────────────────────────────────────────────────────────
function APModal({
  initial, playbooks, onSave, onClose
}: {
  initial?: AnalystPlaybook | null
  playbooks: Playbook[]
  onSave: (data: Partial<AnalystPlaybook>) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [playbookId, setPlaybookId] = useState<number | ''>(initial?.playbook_id ?? '')
  const [guide, setGuide] = useState(initial?.analyst_guide ?? '')
  const [checklist, setChecklist] = useState(initial?.investigation_checklist ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSave = async () => {
    if (!name.trim()) { setError('Название обязательно'); return }
    setSaving(true)
    try {
      await onSave({
        name: name.trim(),
        description: description || null,
        playbook_id: playbookId !== '' ? Number(playbookId) : null,
        analyst_guide: guide || null,
        investigation_checklist: checklist || null,
      })
      onClose()
    } catch (e: any) {
      setError(e.message ?? 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#0d1117] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BookOpenCheck className="h-6 w-6 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">
              {initial ? 'Редактировать аналитический плейбук' : 'Создать аналитический плейбук'}
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-8 flex flex-col gap-6">
          {/* Basic info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-semibold text-gray-300 mb-2">Название *</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                placeholder="Руководство по расследованию: Brute Force on AD"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">Описание</label>
              <input
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                placeholder="Краткое описание..."
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                <Link2 className="inline h-4 w-4 text-purple-400 mr-1" />
                Сценарий атаки (необязательно)
              </label>
              <select
                value={playbookId}
                onChange={e => setPlaybookId(e.target.value === '' ? '' : Number(e.target.value))}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">— Не привязан —</option>
                {playbooks.map(pb => (
                  <option key={pb.id} value={pb.id}>{pb.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Analyst guide */}
          <MarkdownEditor
            label="Руководство аналитика (Markdown)"
            value={guide}
            onChange={setGuide}
            placeholder={`# Руководство аналитика: Brute Force\n\n## 1. Обнаружение\n\n**KQL в Kibana:**\n\`\`\`kql\nevent.code: "4625" AND source.ip: "192.168.100.20"\n\`\`\`\n\n## 2. Подтверждение\n...`}
          />

          {/* Checklist */}
          <MarkdownEditor
            label="Чеклист расследования (Markdown)"
            value={checklist}
            onChange={setChecklist}
            placeholder={`# Чеклист: Brute Force\n\n## Артефакты к сбору\n- [ ] IP-адрес атакующего\n- [ ] Скомпрометированный пользователь\n- [ ] Время начала атаки\n- [ ] Число попыток\n\n## Выполненные проверки\n- [ ] Поиск событий 4625\n- [ ] Поиск событий 4624 от того же IP`}
          />

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertCircle className="h-4 w-4" /> {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl border border-white/10 text-sm text-gray-400 hover:text-white hover:border-white/20 transition-all"
            >
              Отмена
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium text-white transition-all"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ────────────────────────────────────────────────────────────
// Main Page
// ────────────────────────────────────────────────────────────
export default function AnalystPlaybooks() {
  const [items, setItems] = useState<AnalystPlaybook[]>([])
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<AnalystPlaybook | null>(null)

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

  const handleCreate = async (data: Partial<AnalystPlaybook>) => {
    await api.post('/analyst-playbooks/', data)
    await load()
  }

  const handleUpdate = async (id: number, data: Partial<AnalystPlaybook>) => {
    await api.patch(`/analyst-playbooks/${id}`, data)
    await load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить аналитический плейбук?')) return
    await api.delete(`/analyst-playbooks/${id}`)
    await load()
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BookOpenCheck className="h-7 w-7 text-blue-400" />
            Аналитические плейбуки
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Руководства для SOC-аналитиков и чеклисты расследований
          </p>
        </div>
        <button
          onClick={() => { setEditing(null); setModalOpen(true) }}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white transition-all shadow-lg shadow-blue-500/20"
        >
          <Plus className="h-4 w-4" />
          Создать плейбук
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Всего плейбуков', value: items.length, icon: BookOpenCheck, color: 'blue' },
          { label: 'С руководством', value: items.filter(i => i.analyst_guide).length, icon: FileText, color: 'purple' },
          { label: 'С чеклистом', value: items.filter(i => i.investigation_checklist).length, icon: ClipboardList, color: 'emerald' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="rounded-2xl border border-white/10 bg-[#0f1117] p-5 flex items-center gap-4">
            <div className={`rounded-xl p-3 bg-${color}-500/10`}>
              <Icon className={`h-5 w-5 text-${color}-400`} />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{value}</div>
              <div className="text-xs text-gray-500">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3" />
          Загрузка...
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <div className="rounded-2xl bg-blue-500/10 border border-blue-500/20 p-6">
            <BookOpenCheck className="h-12 w-12 text-blue-400 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-white">Нет аналитических плейбуков</h3>
          <p className="text-sm text-gray-500 max-w-sm">
            Создайте первое руководство для аналитика SOC с шагами расследования и KQL-запросами
          </p>
          <button
            onClick={() => { setEditing(null); setModalOpen(true) }}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white transition-all"
          >
            <Plus className="h-4 w-4" /> Создать первый плейбук
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map(ap => (
            <APCard
              key={ap.id}
              ap={ap}
              onEdit={() => { setEditing(ap); setModalOpen(true) }}
              onDelete={() => handleDelete(ap.id)}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <APModal
          initial={editing}
          playbooks={playbooks}
          onSave={data => editing ? handleUpdate(editing.id, data) : handleCreate(data)}
          onClose={() => { setModalOpen(false); setEditing(null) }}
        />
      )}
    </div>
  )
}
