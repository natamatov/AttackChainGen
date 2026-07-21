import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ShieldAlert } from 'lucide-react'
import mitreData from '@/lib/mitre_data.json'

interface Playbook {
  id: number
  name: string
  mitre_tactics: string[]
  mitre_techniques: string[]
}

interface MitreTechnique {
  id: string
  name: string
}

interface MitreTactic {
  name: string
  techniques: MitreTechnique[]
}

export default function MitreMatrix() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/playbooks/')
      .then(res => setPlaybooks(res.data))
      .catch(err => console.error("Failed to load playbooks for matrix", err))
      .finally(() => setLoading(false))
  }, [])

  // Helper to get playbooks covering a specific tactic
  const getPlaybooksForTactic = (tacticName: string) => {
    return playbooks.filter(pb => 
      pb.mitre_tactics.some(t => t.toLowerCase().replace(/[^a-z0-9]/g, '') === tacticName.toLowerCase().replace(/[^a-z0-9]/g, ''))
    )
  }

  // Helper to get playbooks covering a specific technique
  const getPlaybooksForTechnique = (techniqueId: string) => {
    return playbooks.filter(pb => {
      // Split sub-techniques to match main technique as well, e.g. T1566.001 should match T1566
      return pb.mitre_techniques.some(t => {
        const pbTech = t.toUpperCase().trim()
        const targetTech = techniqueId.toUpperCase().trim()
        return pbTech === targetTech || pbTech.startsWith(`${targetTech}.`)
      })
    })
  }

  const matrix = (mitreData as MitreTactic[]).map(tactic => {
    const tacticPlaybooks = getPlaybooksForTactic(tactic.name)
    
    // Create a deep copy of techniques
    const techniques = tactic.techniques.map(t => ({ ...t }))

    return {
      ...tactic,
      techniques,
      playbooks: tacticPlaybooks
    }
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">MITRE ATT&CK Matrix</h2>
          <p className="text-muted-foreground">Full Enterprise Killchain mapping across all your playbooks.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-primary" />
            Coverage Map
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading matrix...</div>
          ) : (
            <div className="overflow-x-auto pb-6">
              <div className="flex gap-2 min-w-max">
                {matrix.map((tactic) => {
                  const coveredTactic = tactic.playbooks.length > 0
                  return (
                    <div key={tactic.name} className="flex flex-col w-72 flex-shrink-0 gap-3">
                      {/* Tactic Header */}
                      <div className="group relative z-10">
                        <div className={`p-4 rounded-md text-lg font-bold text-center border cursor-pointer transition-colors h-24 flex items-center justify-center ${
                          coveredTactic 
                            ? 'bg-primary text-primary-foreground border-primary shadow-sm hover:bg-primary/90' 
                            : 'bg-muted/30 text-muted-foreground border-border hover:bg-muted/50'
                        }`}>
                          {tactic.name}
                        </div>
                        {coveredTactic && (
                          <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 hidden group-hover:block z-50 w-64 bg-popover text-popover-foreground border shadow-xl rounded-md p-3 text-xs pointer-events-none">
                            <strong className="block mb-1 border-b pb-1">Covered by {tactic.playbooks.length} playbooks:</strong>
                            <ul className="list-disc pl-4 space-y-1 mt-2">
                              {tactic.playbooks.map(pb => (
                                <li key={pb.id} className="truncate font-medium">{pb.name}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Techniques List */}
                      <div className="flex flex-col gap-2 mt-3">
                        {tactic.techniques.map(tech => {
                          const techPlaybooks = getPlaybooksForTechnique(tech.id)
                          const coveredTech = techPlaybooks.length > 0
                          return (
                            <div key={tech.id} className="group relative">
                              <div className={`px-3 py-3 rounded text-sm border leading-snug cursor-pointer transition-colors h-16 flex flex-col justify-center ${
                                coveredTech
                                  ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/30 hover:bg-blue-500/20 font-semibold shadow-sm'
                                  : 'bg-transparent text-muted-foreground border-transparent hover:bg-muted/50'
                              }`}>
                                <span>{tech.id}</span>
                                <span className={coveredTech ? '' : 'opacity-70'}>{tech.name}</span>
                              </div>
                              {coveredTech && (
                                <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1 hidden group-hover:block z-50 w-64 bg-popover text-popover-foreground border shadow-xl rounded-md p-3 text-xs pointer-events-none">
                                  <strong className="block mb-1 border-b pb-1">Technique {tech.id}: {tech.name}</strong>
                                  <div className="mt-2 font-medium">Covered by:</div>
                                  <ul className="list-disc pl-4 space-y-1 mt-1">
                                    {techPlaybooks.map(pb => (
                                      <li key={pb.id} className="truncate text-blue-600 dark:text-blue-400">{pb.name}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
