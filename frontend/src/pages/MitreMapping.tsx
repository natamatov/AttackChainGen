import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'

interface Mapping {
  id: number
  mitre_id: string
  template_name: string
  description?: string
}

export default function MitreMappingPage() {
  const [mappings, setMappings] = useState<Mapping[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  
  const [form, setForm] = useState({ id: 0, mitre_id: '', template_name: '', description: '' })

  const fetchMappings = () => {
    setLoading(true)
    api.get('/opencti/mappings')
      .then(res => setMappings(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchMappings()
  }, [])

  const handleSave = () => {
    const payload = {
      mitre_id: form.mitre_id,
      template_name: form.template_name,
      description: form.description
    }
    
    const request = form.id === 0 
      ? api.post('/opencti/mappings', payload)
      : api.put(`/opencti/mappings/${form.id}`, payload)
      
    request.then(() => {
      setShowModal(false)
      fetchMappings()
    }).catch(err => {
      alert("Error saving mapping. Check console.")
      console.error(err)
    })
  }

  const handleDelete = (id: number) => {
    if (confirm("Are you sure you want to delete this mapping?")) {
      api.delete(`/opencti/mappings/${id}`)
        .then(() => fetchMappings())
        .catch(err => console.error(err))
    }
  }

  const openNew = () => {
    setForm({ id: 0, mitre_id: '', template_name: '', description: '' })
    setShowModal(true)
  }

  const openEdit = (m: Mapping) => {
    setForm({ id: m.id, mitre_id: m.mitre_id, template_name: m.template_name, description: m.description || '' })
    setShowModal(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">MITRE Mappings</h2>
          <p className="text-muted-foreground">Map OpenCTI MITRE Techniques to local Playbook Templates</p>
        </div>
        <Button onClick={openNew}>
          <Plus className="mr-2 h-4 w-4" /> Add Mapping
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
                <tr>
                  <th className="px-6 py-3">MITRE ID</th>
                  <th className="px-6 py-3">Template Name</th>
                  <th className="px-6 py-3">Description</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} className="p-6 text-center">Loading...</td></tr>
                ) : mappings.length === 0 ? (
                  <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No mappings found. Default mappings will be created on first OpenCTI run.</td></tr>
                ) : (
                  mappings.map(m => (
                    <tr key={m.id} className="border-b last:border-0 hover:bg-muted/30">
                      <td className="px-6 py-4 font-medium">{m.mitre_id}</td>
                      <td className="px-6 py-4 font-mono text-blue-600 dark:text-blue-400">{m.template_name}</td>
                      <td className="px-6 py-4 text-muted-foreground">{m.description || '-'}</td>
                      <td className="px-6 py-4 text-right">
                        <Button variant="ghost" size="sm" onClick={() => openEdit(m)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(m.id)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Basic Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background w-[400px] rounded-lg shadow-xl border p-6">
            <h3 className="text-lg font-bold mb-4">{form.id === 0 ? 'New Mapping' : 'Edit Mapping'}</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">MITRE ID (e.g. T1078)</label>
                <input 
                  type="text" 
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                  value={form.mitre_id}
                  onChange={e => setForm({...form, mitre_id: e.target.value})}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Template Name (e.g. win_security_4624)</label>
                <input 
                  type="text" 
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                  value={form.template_name}
                  onChange={e => setForm({...form, template_name: e.target.value})}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description (optional)</label>
                <input 
                  type="text" 
                  className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                  value={form.description}
                  onChange={e => setForm({...form, description: e.target.value})}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
              <Button onClick={handleSave}>Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
