import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ShieldAlert } from 'lucide-react'

interface Playbook {
  id: number
  name: string
  mitre_tactics: string[]
  mitre_techniques: string[]
}

const MITRE_MATRIX = [
  { name: 'Initial Access', techniques: ['T1189', 'T1190', 'T1133', 'T1566', 'T1566.001', 'T1078'] },
  { name: 'Execution', techniques: ['T1059', 'T1059.003', 'T1203', 'T1053', 'T1047', 'T1204', 'T1204.002'] },
  { name: 'Persistence', techniques: ['T1098', 'T1136', 'T1543', 'T1546', 'T1505', 'T1505.003', 'T1053.005'] },
  { name: 'Privilege Escalation', techniques: ['T1548', 'T1134', 'T1078', 'T1053', 'T1068'] },
  { name: 'Defense Evasion', techniques: ['T1140', 'T1070', 'T1218', 'T1218.010', 'T1562', 'T1490', 'T1027'] },
  { name: 'Credential Access', techniques: ['T1110', 'T1003', 'T1003.006', 'T1558', 'T1558.003', 'T1056'] },
  { name: 'Discovery', techniques: ['T1087', 'T1016', 'T1049', 'T1033', 'T1082', 'T1018'] },
  { name: 'Lateral Movement', techniques: ['T1210', 'T1534', 'T1550', 'T1550.002', 'T1021', 'T1078.002', 'T1091'] },
  { name: 'Collection', techniques: ['T1560', 'T1560.001', 'T1123', 'T1114', 'T1056'] },
  { name: 'Command and Control', techniques: ['T1071', 'T1071.001', 'T1090', 'T1105', 'T1573', 'T1104'] },
  { name: 'Exfiltration', techniques: ['T1020', 'T1030', 'T1048', 'T1048.003', 'T1052'] },
  { name: 'Impact', techniques: ['T1485', 'T1486', 'T1490', 'T1491', 'T1529'] }
]

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
    return playbooks.filter(pb => pb.mitre_tactics.some(t => t.toLowerCase() === tacticName.toLowerCase()))
  }

  // Helper to get playbooks covering a specific technique
  const getPlaybooksForTechnique = (techniqueId: string) => {
    return playbooks.filter(pb => pb.mitre_techniques.some(t => t.toLowerCase() === techniqueId.toLowerCase()))
  }

  // Inject any dynamic techniques that we have in playbooks but aren't hardcoded in our UI list
  const matrix = MITRE_MATRIX.map(tactic => {
    const tacticPlaybooks = getPlaybooksForTactic(tactic.name)
    const expandedTechniques = [...tactic.techniques]
    
    tacticPlaybooks.forEach(pb => {
      pb.mitre_techniques.forEach(tech => {
        if (!expandedTechniques.includes(tech)) {
          expandedTechniques.push(tech)
        }
      })
    })

    return {
      ...tactic,
      techniques: Array.from(new Set(expandedTechniques)),
      playbooks: tacticPlaybooks
    }
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">MITRE ATT&CK Matrix</h2>
          <p className="text-muted-foreground">Interactive killchain mapping across all your playbooks.</p>
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
                    <div key={tactic.name} className="flex flex-col w-48 flex-shrink-0 gap-2">
                      {/* Tactic Header */}
                      <div className="group relative">
                        <div className={`p-3 rounded-md text-sm font-bold text-center border cursor-pointer transition-colors ${
                          coveredTactic 
                            ? 'bg-primary text-primary-foreground border-primary shadow-sm hover:bg-primary/90' 
                            : 'bg-muted/30 text-muted-foreground border-border'
                        }`}>
                          {tactic.name}
                        </div>
                        {coveredTactic && (
                          <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 hidden group-hover:block z-50 w-56 bg-popover text-popover-foreground border shadow-lg rounded-md p-3 text-xs pointer-events-none">
                            <strong className="block mb-1 border-b pb-1">Covered by {tactic.playbooks.length} playbooks:</strong>
                            <ul className="list-disc pl-4 space-y-1">
                              {tactic.playbooks.map(pb => (
                                <li key={pb.id} className="truncate">{pb.name}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Techniques List */}
                      <div className="flex flex-col gap-1.5">
                        {tactic.techniques.map(tech => {
                          const techPlaybooks = getPlaybooksForTechnique(tech)
                          const coveredTech = techPlaybooks.length > 0
                          return (
                            <div key={tech} className="group relative">
                              <div className={`px-2 py-1.5 rounded text-xs border text-center cursor-pointer transition-colors ${
                                coveredTech
                                  ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30 hover:bg-blue-500/20 font-medium'
                                  : 'bg-transparent text-muted-foreground border-transparent hover:bg-muted/50'
                              }`}>
                                {tech}
                              </div>
                              {coveredTech && (
                                <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1 hidden group-hover:block z-50 w-56 bg-popover text-popover-foreground border shadow-lg rounded-md p-3 text-xs pointer-events-none">
                                  <strong className="block mb-1 border-b pb-1">Technique {tech} covered by:</strong>
                                  <ul className="list-disc pl-4 space-y-1">
                                    {techPlaybooks.map(pb => (
                                      <li key={pb.id} className="truncate">{pb.name}</li>
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
