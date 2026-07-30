import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { Play, CheckCircle2, XCircle, Clock, ChevronDown, ChevronRight, Activity, BookOpen, X, Copy, Check } from 'lucide-react'
import { useAppStore } from '@/store/appStore'

export default function Simulations() {
  const [simulations, setSimulations] = useState<any[]>([])
  const [totalSims, setTotalSims] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const pageSize = 20

  const [playbooks, setPlaybooks] = useState([])
  const [stands, setStands] = useState([])
  const [loading, setLoading] = useState(true)
  const [showRun, setShowRun] = useState(false)
  const [selectedPlaybook, setSelectedPlaybook] = useState('')
  const [selectedStand, setSelectedStand] = useState('')
  const [mode, setMode] = useState('realtime')
  const [backdateOffset, setBackdateOffset] = useState('')
  const [assignAsTask, setAssignAsTask] = useState(false)
  const [assignTo, setAssignTo] = useState('')
  const [legend, setLegend] = useState('')
  const [students, setStudents] = useState<any[]>([])
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null)

  const setActiveRunId = useAppStore(state => state.setActiveRunId)

  // Cheatsheet modal
  const [cheatsheetSim, setCheatsheetSim] = useState<any | null>(null)
  const [cheatsheetPlaybook, setCheatsheetPlaybook] = useState<any | null>(null)
  const [loadingCheatsheet, setLoadingCheatsheet] = useState(false)
  const [copied, setCopied] = useState(false)

  const openCheatsheet = async (sim: any) => {
    setCheatsheetSim(sim)
    setCheatsheetPlaybook(null)
    setLoadingCheatsheet(true)
    try {
      if (sim.playbook_id) {
        const res = await api.get(`/playbooks/${sim.playbook_id}`)
        setCheatsheetPlaybook(res.data)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingCheatsheet(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const fetchData = async (page = 1, showLoading = true) => {
    try {
      if (showLoading) setLoading(true)
      const skip = (page - 1) * pageSize
      const [simRes, pbRes, standsRes] = await Promise.all([
        api.get(`/simulations/?skip=${skip}&limit=${pageSize}`),
        api.get('/playbooks/'),
        api.get('/stands/')
      ])
      
      if (simRes.data.items) {
        setSimulations(simRes.data.items)
        setTotalSims(simRes.data.total)
        setTotalPages(simRes.data.pages)
        setCurrentPage(simRes.data.page)
      } else {
        // Fallback if backend pagination is not yet returning the new format
        setSimulations(simRes.data)
      }
      
      setPlaybooks(pbRes.data)
      setStands(standsRes.data)

      try {
        const studRes = await api.get('/users/students')
        setStudents(studRes.data)
      } catch (e) {
        console.warn("Could not fetch students")
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(currentPage)
    
    // Poll every 3 seconds to update progress
    const interval = setInterval(() => {
      fetchData(currentPage, false)
    }, 3000)
    
    return () => clearInterval(interval)
  }, [currentPage])

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
      setActiveRunId(newSim.run_id)

      if (assignAsTask && assignTo) {
        try {
          await api.post('/assignments/', {
            simulation_id: newSim.run_id,
            assigned_to: parseInt(assignTo),
            legend: legend
          })
        } catch (e) {
          console.error("Failed to assign task", e)
          alert("Simulation started, but failed to assign task.")
        }
      }

      setShowRun(false)
      fetchData(1)
    } catch (e) {
      console.error(e)
      alert('Failed to start simulation')
    }
  }

  const getStatusIcon = (status: string) => {
    const s = status.toUpperCase()
    switch (s) {
      case 'COMPLETED': return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'FAILED': return <XCircle className="h-4 w-4 text-red-500" />
      case 'RUNNING': return <Play className="h-4 w-4 text-blue-500" />
      default: return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await api.post(`/simulations/${id}/cancel`)
      fetchData(currentPage)
    } catch (e) {
      console.error(e)
      alert("Failed to cancel simulation")
    }
  }

  const handleRestart = async (playbook_id: number, stand_id: number, mode: string, backdate_offset: string | null) => {
    try {
      const payload: any = {
        playbook_id,
        stand_id,
        mode
      }
      if (mode === 'historical' && backdate_offset) {
        payload.backdate_offset = backdate_offset
      }
      const res = await api.post('/simulations/run', payload)
      setActiveRunId(res.data.run_id)
      fetchData(1)
    } catch (e) {
      console.error(e)
      alert("Failed to restart simulation")
    }
  }

  const toggleRow = (id: number) => {
    setExpandedRowId(expandedRowId === id ? null : id)
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

            <div className="border-t pt-4 mt-4">
              <div className="flex items-center gap-2 mb-4">
                <input 
                  type="checkbox" 
                  id="assignTask"
                  checked={assignAsTask}
                  onChange={e => setAssignAsTask(e.target.checked)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="assignTask" className="text-sm font-medium">Assign to Student (CTF Mode)</label>
              </div>

              {assignAsTask && (
                <div className="grid gap-4 md:grid-cols-2 bg-muted/30 p-4 rounded-lg border">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Select Student</label>
                    <select 
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={assignTo}
                      onChange={e => setAssignTo(e.target.value)}
                    >
                      <option value="">-- Choose Student --</option>
                      {students.map((st: any) => (
                        <option key={st.id} value={st.id}>{st.email} {st.full_name ? `(${st.full_name})` : ''}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Legend (Context for Student)</label>
                    <textarea 
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      placeholder="e.g. Suspicious login detected at 10:00 AM..."
                      value={legend}
                      onChange={e => setLegend(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>

            <Button onClick={handleRun} className="mt-4" disabled={!selectedPlaybook || !selectedStand || (assignAsTask && !assignTo)}>Start Run</Button>
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
                  <th className="pb-3 w-8"></th>
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">Playbook</th>
                  <th className="pb-3 font-medium">Stand</th>
                  <th className="pb-3 font-medium">Mode</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Started At</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {simulations.map((sim: any) => (
                  <React.Fragment key={sim.id}>
                    <tr className="border-b last:border-0 hover:bg-muted/50 transition-colors cursor-pointer" onClick={() => toggleRow(sim.id)}>
                      <td className="py-3">
                        {expandedRowId === sim.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </td>
                      <td className="py-3">{sim.id}</td>
                      <td className="py-3 font-medium">{sim.playbook_name || `ID: ${sim.playbook_id}`}</td>
                      <td className="py-3 text-muted-foreground">{sim.stand_name || `ID: ${sim.stand_id}`}</td>
                      <td className="py-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${sim.mode === 'historical' ? 'bg-purple-500/10 text-purple-500 border border-purple-500/20' : 'bg-blue-500/10 text-blue-500 border border-blue-500/20'}`}>
                          {sim.mode === 'historical' ? 'HISTORICAL' : 'REALTIME'}
                        </span>
                      </td>
                      <td className="py-3 flex items-center gap-2">
                        {getStatusIcon(sim.status)} 
                        <span className={sim.status?.toUpperCase() === 'FAILED' ? 'text-red-500 font-medium flex items-center gap-1' : ''}>
                          {sim.status}
                          {sim.status?.toUpperCase() === 'FAILED' && <span className="text-[10px] text-red-400 bg-red-500/10 px-1 rounded ml-1">Click to view error</span>}
                        </span>
                      </td>
                      <td className="py-3">{sim.created_at ? new Date(sim.created_at).toLocaleString() : ''}</td>
                      <td className="py-3 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                        {(sim.status?.toUpperCase() === 'PENDING' || sim.status?.toUpperCase() === 'RUNNING') && (
                          <Button variant="outline" size="sm" onClick={() => handleCancel(sim.id)}>
                            Stop
                          </Button>
                        )}
                        {sim.status?.toUpperCase() === 'COMPLETED' && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="gap-1 border-amber-500/40 text-amber-600 hover:bg-amber-500/10 hover:text-amber-700"
                            onClick={() => openCheatsheet(sim)}
                          >
                            <BookOpen className="h-3.5 w-3.5" />
                            Шпаргалка
                          </Button>
                        )}
                        {sim.playbook_id && sim.stand_id && (
                          <Button variant="secondary" size="sm" onClick={() => handleRestart(sim.playbook_id, sim.stand_id, sim.mode, sim.backdate_offset)}>
                            Restart
                          </Button>
                        )}
                      </td>
                    </tr>
                    
                    {/* Collapsible Details Row */}
                    {expandedRowId === sim.id && (
                      <tr className="border-b bg-muted/20">
                        <td colSpan={7} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-8">
                            <div className="space-y-4">
                              <div>
                                <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                                  <Activity className="h-4 w-4 text-blue-500"/>
                                  Execution Progress
                                </h4>
                                <div className="text-sm text-muted-foreground mb-1">
                                  Step {sim.progress_current || 0} of {sim.progress_total || 0}
                                </div>
                                <div className="w-full bg-secondary rounded-full h-2.5">
                                  <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${Math.min(100, (sim.progress_current / (sim.progress_total || 1)) * 100)}%` }}></div>
                                </div>
                                <div className="mt-2 text-sm text-muted-foreground">
                                  {sim.progress_message || "Waiting..."}
                                </div>
                              </div>
                              
                              <div>
                                <h4 className="text-sm font-semibold mb-1">Metrics</h4>
                                <div className="text-sm text-muted-foreground">
                                  Events sent to Elastic: <strong className="text-foreground">{sim.events_sent || 0}</strong>
                                </div>
                              </div>
                            </div>

                            <div className="space-y-4">
                              {sim.status?.toUpperCase() === 'FAILED' && sim.error_message && (
                                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md">
                                  <h4 className="text-sm font-semibold text-red-500 mb-1">Failure Reason</h4>
                                  <pre className="text-xs text-red-400 whitespace-pre-wrap font-mono">
                                    {sim.error_message}
                                  </pre>
                                </div>
                              )}

                              {sim.artifacts && Object.keys(sim.artifacts).length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                    <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
                                    Generated IOCs
                                  </h4>
                                  <div className="bg-background border rounded-md p-3 max-h-48 overflow-y-auto font-mono text-xs">
                                    {Object.entries(sim.artifacts).map(([stepId, arts]: [string, any]) => (
                                      <div key={stepId} className="mb-3 last:mb-0">
                                        <div className="text-[10px] font-semibold text-muted-foreground mb-1 uppercase tracking-wide">{stepId}</div>
                                        {Object.entries(arts).map(([k, v]) => (
                                          <div key={k} className="flex gap-2 py-0.5 border-b border-border/30 last:border-0">
                                            <span className="text-muted-foreground min-w-[120px]">{k}:</span>
                                            <span className="text-foreground font-medium">{String(v)}</span>
                                          </div>
                                        ))}
                                      </div>
                                    ))}
                                  </div>
                                  {sim.status?.toUpperCase() === 'COMPLETED' && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      className="mt-2 w-full gap-2 border-amber-500/40 text-amber-600 hover:bg-amber-500/10"
                                      onClick={() => openCheatsheet(sim)}
                                    >
                                      <BookOpen className="h-3.5 w-3.5" />
                                      Открыть шпаргалку преподавателя
                                    </Button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
                {simulations.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground">
                      No simulations run yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            
            {/* Pagination Controls */}
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                Showing {totalSims === 0 ? 0 : (currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalSims)} of {totalSims} entries
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <div className="flex items-center px-2 text-sm font-medium">
                  Page {currentPage} of {totalPages}
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages || totalPages === 0}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* ── Cheatsheet Modal ─────────────────────────────────────── */}
      {cheatsheetSim && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm overflow-y-auto p-4 pt-10">
          <div className="relative w-full max-w-3xl bg-background border rounded-xl shadow-2xl">
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <BookOpen className="h-5 w-5 text-amber-500" />
                  <h2 className="text-xl font-bold">Шпаргалка преподавателя</h2>
                </div>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">{cheatsheetSim.playbook_name}</span>
                  {' · '}{new Date(cheatsheetSim.created_at).toLocaleString()}
                  {' · '}<span className="text-blue-500">{cheatsheetSim.events_sent} событий отправлено</span>
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setCheatsheetSim(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-6 space-y-6">
              {/* IOC Summary Table */}
              {cheatsheetSim.artifacts && Object.keys(cheatsheetSim.artifacts).length > 0 && (
                <div>
                  <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
                    Индикаторы компрометации (IOCs)
                    <span className="text-xs font-normal text-muted-foreground ml-1">— для проверки студентов</span>
                  </h3>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-muted-foreground">Шаг</th>
                          <th className="px-4 py-2 text-left font-medium text-muted-foreground">Артефакт</th>
                          <th className="px-4 py-2 text-left font-medium text-muted-foreground">Значение</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(cheatsheetSim.artifacts).flatMap(([stepId, arts]: [string, any]) =>
                          Object.entries(arts).map(([k, v], i) => (
                            <tr key={`${stepId}-${k}`} className="border-t hover:bg-muted/30">
                              {i === 0 && (
                                <td className="px-4 py-2 font-mono text-xs text-muted-foreground align-top" rowSpan={Object.keys(arts).length}>
                                  {stepId.replace(/_/g, ' ')}
                                </td>
                              )}
                              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{k}</td>
                              <td className="px-4 py-2 font-mono text-xs font-medium text-blue-600 dark:text-blue-400">{String(v)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Analyst Guide */}
              {loadingCheatsheet ? (
                <div className="text-sm text-muted-foreground">Загрузка чеклиста расследования...</div>
              ) : cheatsheetPlaybook?.analyst_guide ? (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-semibold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>
                      Чеклист расследования
                    </h3>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-2 text-xs"
                      onClick={() => copyToClipboard(cheatsheetPlaybook.analyst_guide)}
                    >
                      {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                      {copied ? 'Скопировано!' : 'Копировать'}
                    </Button>
                  </div>
                  <div className="bg-muted/30 border rounded-lg p-4 max-h-[50vh] overflow-y-auto">
                    <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-foreground">
                      {cheatsheetPlaybook.analyst_guide}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground p-4 bg-muted/30 rounded-lg border border-dashed">
                  Чеклист расследования не прикреплен к этому плейбуку.
                  Добавьте поле <code className="font-mono bg-muted px-1 rounded">analyst_guide</code> в YAML плейбука.
                </div>
              )}
            </div>

            <div className="flex justify-end p-4 border-t">
              <Button onClick={() => setCheatsheetSim(null)}>Закрыть</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
