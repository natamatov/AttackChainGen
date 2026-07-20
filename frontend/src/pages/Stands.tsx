import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { Plus, Server, Edit2, Trash2 } from 'lucide-react'

export default function Stands() {
  const [stands, setStands] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [editingStandId, setEditingStandId] = useState<number | null>(null)
  const [newStand, setNewStand] = useState({ name: '', description: '', elastic_url: '', api_key: '', username: '', password: '', tenant_id: '', index_pattern: 'logs-attackchain-default' })

  const fetchStands = async () => {
    try {
      const res = await api.get('/stands/')
      setStands(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStands()
  }, [])

  const handleCreateOrUpdate = async () => {
    try {
      if (editingStandId) {
        await api.patch(`/stands/${editingStandId}`, newStand)
      } else {
        await api.post('/stands/', newStand)
      }
      setShowAdd(false)
      setEditingStandId(null)
      setNewStand({ name: '', description: '', elastic_url: '', api_key: '', username: '', password: '', tenant_id: '', index_pattern: 'logs-attackchain-default' })
      fetchStands()
    } catch (e) {
      console.error(e)
      alert("Failed to save stand")
    }
  }

  const handleEdit = (stand: any) => {
    setNewStand({
      name: stand.name || '',
      description: stand.description || '',
      elastic_url: stand.elastic_url || '',
      api_key: stand.api_key || '',
      username: stand.username || '',
      password: stand.password || '',
      tenant_id: stand.tenant_id || '',
      index_pattern: stand.index_pattern || 'logs-attackchain-default'
    })
    setEditingStandId(stand.id)
    setShowAdd(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this stand?")) return
    try {
      await api.delete(`/stands/${id}`)
      fetchStands()
    } catch (e) {
      console.error(e)
      alert("Failed to delete stand")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Target Stands</h1>
        <Button onClick={() => {
          setEditingStandId(null)
          setNewStand({ name: '', description: '', elastic_url: '', api_key: '', username: '', password: '', tenant_id: '', index_pattern: 'logs-attackchain-default' })
          setShowAdd(!showAdd)
        }}>
          {showAdd ? 'Cancel' : <><Plus className="mr-2 h-4 w-4" /> Add Stand</>}
        </Button>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>{editingStandId ? 'Edit Stand' : 'Add New Stand'}</CardTitle>
            <CardDescription>Configure an ElasticSearch cluster as a target</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <Input value={newStand.name} onChange={e => setNewStand({...newStand, name: e.target.value})} placeholder="e.g. Prod SIEM" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Input value={newStand.description} onChange={e => setNewStand({...newStand, description: e.target.value})} />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">ElasticSearch URL</label>
                <Input value={newStand.elastic_url} onChange={e => setNewStand({...newStand, elastic_url: e.target.value})} placeholder="https://elastic.internal:9200" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">API Key (Optional)</label>
                <Input type="password" value={newStand.api_key} onChange={e => setNewStand({...newStand, api_key: e.target.value})} placeholder="id:key (or base64)" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Username (Optional)</label>
                <Input value={newStand.username} onChange={e => setNewStand({...newStand, username: e.target.value})} placeholder="Basic Auth User" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Password (Optional)</label>
                <Input type="password" value={newStand.password} onChange={e => setNewStand({...newStand, password: e.target.value})} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tenant ID (Optional)</label>
                <Input value={newStand.tenant_id} onChange={e => setNewStand({...newStand, tenant_id: e.target.value})} placeholder="e.g. global_tenant" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Index Pattern</label>
                <Input value={newStand.index_pattern} onChange={e => setNewStand({...newStand, index_pattern: e.target.value})} placeholder="logs-attackchain-default" />
              </div>
            </div>
            <Button onClick={handleCreateOrUpdate} className="mt-4">{editingStandId ? 'Update Stand' : 'Save Stand'}</Button>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {stands.map((stand: any) => (
            <Card key={stand.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center space-x-2">
                  <Server className="h-4 w-4 text-muted-foreground" />
                  <CardTitle className="text-sm font-medium">{stand.name}</CardTitle>
                </div>
                <div className="flex space-x-2">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(stand)}>
                    <Edit2 className="h-4 w-4 text-muted-foreground hover:text-blue-500" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDelete(stand.id)}>
                    <Trash2 className="h-4 w-4 text-muted-foreground hover:text-red-500" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold truncate text-ellipsis">{stand.elastic_url}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stand.description || "No description"}
                </p>
                {stand.tenant_id && (
                  <p className="text-xs text-muted-foreground mt-1">Tenant: {stand.tenant_id}</p>
                )}
              </CardContent>
            </Card>
          ))}
          {stands.length === 0 && !showAdd && (
            <div className="col-span-full text-center p-12 text-muted-foreground">
              No stands found. Add one to get started.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
