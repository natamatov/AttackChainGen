import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Trash2, Server, Globe, Network, Edit2, Check, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'

interface Asset {
  id: number
  zone_id: number
  hostname: string
  ip_address: string
  role?: string
  device_type?: string
  os_name?: string
}

interface NetworkZone {
  id: number
  environment_id: number
  name: string
  ip_range: string
  description?: string
  zone_type?: string
  assets: Asset[]
}

interface Environment {
  id: number
  name: string
  domain: string
  description?: string
  zones: NetworkZone[]
}

export default function Environments() {
  const [environments, setEnvironments] = useState<Environment[]>([])

  const [newEnv, setNewEnv] = useState({ name: '', domain: '', description: '' })
  const [newZone, setNewZone] = useState({ envId: 0, name: '', ip_range: '', zone_type: 'Workstation' })
  const [newAsset, setNewAsset] = useState({ zoneId: 0, hostname: '', ip_address: '', role: '', os_name: 'Windows' })
  
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null)
  const [editAssetData, setEditAssetData] = useState<any>({})

  useEffect(() => {
    fetchEnvironments()
  }, [])

  const fetchEnvironments = async () => {
    try {
      const res = await api.get('/environments/')
      setEnvironments(res.data)
    } catch (err) {
      window.alert('Failed to fetch environments')
    }
  }

  const createEnvironment = async () => {
    if (!newEnv.name || !newEnv.domain) return
    try {
      const res = await api.post('/environments/', newEnv)
      if (res.status === 201 || res.status === 200) {
        setNewEnv({ name: '', domain: '', description: '' })
        fetchEnvironments()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const createZone = async (envId: number) => {
    if (!newZone.name || !newZone.ip_range) {
      window.alert("Please fill in both Name and IP Range for the zone.")
      return
    }
    try {
      const res = await api.post(`/environments/${envId}/zones`, { name: newZone.name, ip_range: newZone.ip_range, zone_type: newZone.zone_type })
      if (res.status === 201 || res.status === 200) {
        setNewZone({ envId: 0, name: '', ip_range: '', zone_type: 'Workstation' })
        fetchEnvironments()
      }
    } catch (err: any) {
      window.alert(err.response?.data?.detail || 'Failed to create zone')
    }
  }

  const createAsset = async (zoneId: number) => {
    if (!newAsset.hostname) {
      window.alert("Please fill in Hostname for the asset.")
      return
    }
    try {
      const payload: any = { 
        hostname: newAsset.hostname, 
        role: newAsset.role,
        os_name: newAsset.os_name
      }
      if (newAsset.ip_address) {
        payload.ip_address = newAsset.ip_address
      }
      const res = await api.post(`/environments/zones/${zoneId}/assets`, payload)
      if (res.status === 201 || res.status === 200) {
        setNewAsset({ zoneId: 0, hostname: '', ip_address: '', role: '', os_name: 'Windows' })
        fetchEnvironments()
      }
    } catch (err: any) {
      window.alert(err.response?.data?.detail || 'Failed to create asset')
    }
  }

  const deleteEnvironment = async (id: number) => {
    await api.delete(`/environments/${id}`)
    fetchEnvironments()
  }

  const deleteZone = async (id: number) => {
    await api.delete(`/environments/zones/${id}`)
    fetchEnvironments()
  }

  const deleteAsset = async (id: number) => {
    await api.delete(`/environments/assets/${id}`)
    fetchEnvironments()
  }

  const startEditAsset = (asset: Asset) => {
    setEditingAssetId(asset.id)
    setEditAssetData({ ...asset })
  }

  const cancelEditAsset = () => {
    setEditingAssetId(null)
    setEditAssetData({})
  }

  const saveEditAsset = async () => {
    if (!editingAssetId) return
    try {
      await api.put(`/environments/assets/${editingAssetId}`, {
        hostname: editAssetData.hostname,
        ip_address: editAssetData.ip_address,
        os_name: editAssetData.os_name
      })
      setEditingAssetId(null)
      fetchEnvironments()
    } catch (err: any) {
      window.alert(err.response?.data?.detail || 'Failed to update asset')
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Fictional Networks</h1>
        <p className="text-muted-foreground">
          Управление вымышленными сетями, подсетями и инвентаризацией активов (CMDB).
        </p>
      </div>

      <Card className="bg-muted/30">
        <CardContent className="pt-6 flex gap-4 items-end">
          <div className="space-y-1"><label className="text-xs">Имя сети (Env)</label><Input placeholder="CorpNet" value={newEnv.name} onChange={e => setNewEnv({...newEnv, name: e.target.value})} /></div>
          <div className="space-y-1"><label className="text-xs">Домен</label><Input placeholder="corp.local" value={newEnv.domain} onChange={e => setNewEnv({...newEnv, domain: e.target.value})} /></div>
          <Button onClick={createEnvironment}><Plus className="w-4 h-4 mr-2"/> Создать сеть</Button>
        </CardContent>
      </Card>

      {environments.map(env => (
        <Card key={env.id} className="overflow-hidden border-primary/20">
          <CardHeader className="bg-primary/5 pb-4 flex flex-row items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2"><Globe className="w-5 h-5 text-primary"/> {env.name} ({env.domain})</CardTitle>
              <CardDescription>ID: {env.id} | Зон: {env.zones.length}</CardDescription>
            </div>
            <Button variant="ghost" size="icon" className="text-destructive" onClick={() => deleteEnvironment(env.id)}>
              <Trash2 className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            
            <div className="flex gap-4 items-end bg-muted/20 p-4 rounded-md border border-dashed">
              <div className="space-y-1"><label className="text-xs">Имя подсети (Zone)</label><Input placeholder="Servers" value={newZone.envId === env.id ? newZone.name : ''} onChange={e => setNewZone({...newZone, envId: env.id, name: e.target.value})} /></div>
              <div className="space-y-1"><label className="text-xs">Диапазон IP (Range)</label><Input placeholder="192.168.100.10-192.168.100.20" value={newZone.envId === env.id ? newZone.ip_range : ''} onChange={e => setNewZone({...newZone, envId: env.id, ip_range: e.target.value})} /></div>
              <div className="space-y-1">
                <label className="text-xs">Тип зоны</label>
                <select className="h-9 w-32 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors" value={newZone.envId === env.id ? newZone.zone_type : 'Workstation'} onChange={e => setNewZone({...newZone, envId: env.id, zone_type: e.target.value})}>
                  <option value="Workstation">ПК</option>
                  <option value="Server">Сервер</option>
                  <option value="Switch">Коммутатор</option>
                  <option value="Printer">Принтер</option>
                  <option value="Router">Роутер</option>
                  <option value="Firewall">Файрвол</option>
                </select>
              </div>
              <Button size="sm" variant="secondary" onClick={() => createZone(env.id)}><Plus className="w-4 h-4 mr-2"/> Добавить зону</Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {env.zones.map(zone => (
                <Card key={zone.id} className="shadow-sm">
                  <CardHeader className="py-3 bg-muted/30 flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-sm font-medium flex items-center gap-2"><Network className="w-4 h-4 text-blue-500"/> {zone.name} {zone.zone_type && <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{zone.zone_type}</span>}</CardTitle>
                      <CardDescription className="text-xs">{zone.ip_range}</CardDescription>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => deleteZone(zone.id)}>
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="p-3 bg-muted/10 border-b flex flex-col gap-2">
                      <div className="flex gap-2">
                        <Input className="h-7 text-xs flex-1" placeholder="SRV-01" value={newAsset.zoneId === zone.id ? newAsset.hostname : ''} onChange={e => setNewAsset({...newAsset, zoneId: zone.id, hostname: e.target.value})} />
                        <Input className="h-7 text-xs flex-1" placeholder="Авто (опционально)" value={newAsset.zoneId === zone.id ? newAsset.ip_address : ''} onChange={e => setNewAsset({...newAsset, zoneId: zone.id, ip_address: e.target.value})} />
                      </div>
                      <div className="flex gap-2">
                        <select className="h-7 text-xs flex-1 rounded border-input border px-2 bg-background" value={newAsset.zoneId === zone.id ? newAsset.os_name : ''} onChange={e => setNewAsset({...newAsset, zoneId: zone.id, os_name: e.target.value})}>
                          <option value="">Без ОС (Empty)</option>
                          <option value="Windows">Windows</option>
                          <option value="Linux">Linux</option>
                          <option value="macOS">macOS</option>
                        </select>
                        <Button size="sm" className="h-7 px-2" onClick={() => createAsset(zone.id)}><Plus className="w-3 h-3"/></Button>
                      </div>
                    </div>
                    <ul className="divide-y divide-border">
                      {zone.assets.map(asset => (
                        <li key={asset.id} className="flex justify-between items-center p-3 text-sm hover:bg-muted/50 transition-colors">
                          {editingAssetId === asset.id ? (
                            <div className="flex flex-col gap-2 w-full">
                              <div className="flex gap-2">
                                <Input className="h-7 text-xs flex-1" value={editAssetData.hostname} onChange={e => setEditAssetData({...editAssetData, hostname: e.target.value})} />
                                <Input className="h-7 text-xs flex-1" value={editAssetData.ip_address} onChange={e => setEditAssetData({...editAssetData, ip_address: e.target.value})} />
                              </div>
                              <div className="flex gap-2">
                                <select className="h-7 text-xs flex-1 rounded border-input border px-2 bg-background" value={editAssetData.os_name || ''} onChange={e => setEditAssetData({...editAssetData, os_name: e.target.value})}>
                                  <option value="">Без ОС (Empty)</option>
                                  <option value="Windows">Windows</option>
                                  <option value="Linux">Linux</option>
                                  <option value="macOS">macOS</option>
                                </select>
                                <Button size="sm" variant="ghost" className="h-7 px-2 text-green-500 hover:text-green-600" onClick={saveEditAsset}><Check className="w-4 h-4"/></Button>
                                <Button size="sm" variant="ghost" className="h-7 px-2 text-destructive" onClick={cancelEditAsset}><X className="w-4 h-4"/></Button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-center gap-3">
                                <Server className="w-4 h-4 text-muted-foreground" />
                                <div className="flex flex-col">
                                  <span className="font-semibold text-xs">{asset.hostname}</span>
                                  <span className="text-[10px] text-muted-foreground font-mono">{asset.ip_address}</span>
                                </div>
                                <div className="flex flex-col ml-2 border-l pl-2">
                                  <span className="text-[10px] text-muted-foreground">{asset.os_name || 'Без ОС'}</span>
                                </div>
                              </div>
                              <div className="flex gap-1">
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-primary" onClick={() => startEditAsset(asset)}>
                                  <Edit2 className="w-3 h-3" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => deleteAsset(asset.id)}>
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              </div>
                            </>
                          )}
                        </li>
                      ))}
                      {zone.assets.length === 0 && <li className="p-4 text-xs text-muted-foreground text-center">Нет хостов</li>}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

    </div>
  )
}
