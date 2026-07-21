import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { Play, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useAppStore } from '@/store/appStore'

export default function Simulations() {
  const [simulations, setSimulations] = useState([])
  const [playbooks, setPlaybooks] = useState([])
  const [stands, setStands] = useState([])
  const [loading, setLoading] = useState(true)
  const [showRun, setShowRun] = useState(false)
  const [selectedPlaybook, setSelectedPlaybook] = useState('')
  const [selectedStand, setSelectedStand] = useState('')
  const [mode, setMode] = useState('realtime')
  const [backdateOffset, setBackdateOffset] = useState('')

  const setActiveRunId = useAppStore(state => state.setActiveRunId)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [simRes, pbRes, standsRes] = await Promise.all([
        api.get('/simulations/'),
        api.get('/playbooks/'),
        api.get('/stands/')
      ])
      setSimulations(simRes.data)
      setPlaybooks(pbRes.data)
      setStands(standsRes.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleRun = async () => {
    if (!selectedPlaybook || !selectedStand) {
      alert('Select playbook and stand')
      return
    }
    try {
      const payload: any = {
        playbook_id: parseInt(selectedPlaybook),
        stand_id: parseInt(selectedStand),
        mode: mode
      }
      if (mode === 'historical' && backdateOffset.trim()) {
        payload.backdate_offset = backdateOffset.trim()
      }
      const res = await api.post('/simulations/run', payload)
      const newSim = res.data
      setActiveRunId(newSim.id)
      setShowRun(false)
      fetchData()
    } catch (e) {
      console.error(e)
      alert('Failed to start simulation')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'FAILED': return <XCircle className="h-4 w-4 text-red-500" />
      case 'RUNNING': return <Play className="h-4 w-4 text-blue-500" />
      default: return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await api.post(`/simulations/${id}/cancel`)
      fetchData()
    } catch (e) {
      console.error(e)
      alert("Failed to cancel simulation")
    }
  }

  const handleRestart = async (playbook_id: number, stand_id: number) => {
    try {
      const res = await api.post('/simulations/run', {
        playbook_id,
        stand_id
      })
      setActiveRunId(res.data.id)
      fetchData()
    } catch (e) {
      console.error(e)
      alert("Failed to restart simulation")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Simulations</h1>
        <Button onClick={() => setShowRun(!showRun)}>
          <Play className="mr-2 h-4 w-4" /> Run Playbook
        </Button>
      </div>

      {showRun && (
        <Card>
          <CardHeader>
            <CardTitle>Launch Simulation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Playbook</label>
                <select 
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={selectedPlaybook} 
                  onChange={e => setSelectedPlaybook(e.target.value)}
                >
                  <option value="">-- Choose Playbook --</option>
                  {playbooks.map((pb: any) => (
                    <option key={pb.id} value={pb.id}>{pb.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Target Stand</label>
                <select 
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={selectedStand} 
                  onChange={e => setSelectedStand(e.target.value)}
                >
                  <option value="">-- Choose Stand --</option>
                  {stands.map((st: any) => (
                    <option key={st.id} value={st.id}>{st.name} ({st.elastic_url})</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Simulation Mode</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={mode}
                  onChange={e => setMode(e.target.value)}
                >
                  <option value="realtime">Realtime (Wait for delays)</option>
                  <option value="historical">Historical (Instant, shift timestamps)</option>
                </select>
              </div>
              {mode === 'historical' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Backdate Offset (e.g. '2h', '1d')</label>
                  <input
                    type="text"
                    placeholder="2h"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={backdateOffset}
                    onChange={e => setBackdateOffset(e.target.value)}
                  />
                </div>
              )}
            </div>
            <Button onClick={handleRun} className="mt-4" disabled={!selectedPlaybook || !selectedStand}>Start Run</Button>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="rounded-md border bg-card text-card-foreground">
          <div className="p-6">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">Playbook</th>
                  <th className="pb-3 font-medium">Stand</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Started At</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {simulations.map((sim: any) => (
                  <tr key={sim.id} className="border-b last:border-0">
                    <td className="py-3">{sim.id}</td>
                    <td className="py-3">{sim.playbook_name || `ID: ${sim.playbook_id}`}</td>
                    <td className="py-3">{sim.stand_name || `ID: ${sim.stand_id}`}</td>
                    <td className="py-3 flex items-center gap-2">
                      {getStatusIcon(sim.status)} {sim.status}
                    </td>
                    <td className="py-3">{new Date(sim.created_at).toLocaleString()}</td>
                    <td className="py-3 text-right space-x-2">
                      {(sim.status === 'PENDING' || sim.status === 'RUNNING') && (
                        <Button variant="outline" size="sm" onClick={() => handleCancel(sim.id)}>
                          Stop
                        </Button>
                      )}
                      {sim.playbook_id && sim.stand_id && (
                        <Button variant="secondary" size="sm" onClick={() => handleRestart(sim.playbook_id, sim.stand_id)}>
                          Restart
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {simulations.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground">
                      No simulations run yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
