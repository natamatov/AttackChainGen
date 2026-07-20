import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { Plus, Server } from 'lucide-react'

export default function Stands() {
  const [stands, setStands] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [newStand, setNewStand] = useState({ name: '', description: '', elastic_url: '', api_key: '', index_pattern: 'logs-attackchain-default' })

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

  const handleCreate = async () => {
    try {
      await api.post('/stands/', newStand)
      setShowAdd(false)
      setNewStand({ name: '', description: '', elastic_url: '', api_key: '', index_pattern: 'logs-attackchain-default' })
      fetchStands()
    } catch (e) {
      console.error(e)
      alert("Failed to create stand")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Target Stands</h1>
        <Button onClick={() => setShowAdd(!showAdd)}>
          <Plus className="mr-2 h-4 w-4" /> Add Stand
        </Button>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>Add New Stand</CardTitle>
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
                <label className="text-sm font-medium">API Key / Auth Token</label>
                <Input type="password" value={newStand.api_key} onChange={e => setNewStand({...newStand, api_key: e.target.value})} placeholder="id:key (or any string)" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Index Pattern</label>
                <Input value={newStand.index_pattern} onChange={e => setNewStand({...newStand, index_pattern: e.target.value})} placeholder="logs-attackchain-default" />
              </div>
            </div>
            <Button onClick={handleCreate} className="mt-4">Save Stand</Button>
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
                <CardTitle className="text-sm font-medium">{stand.name}</CardTitle>
                <Server className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold truncate text-ellipsis">{stand.elastic_url}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stand.description || "No description"}
                </p>
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
