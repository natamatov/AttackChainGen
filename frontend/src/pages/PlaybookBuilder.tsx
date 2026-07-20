import { useCallback } from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const initialNodes: Node[] = [
  { id: '1', position: { x: 250, y: 50 }, data: { label: 'Start Playbook' }, type: 'input' },
]

export default function PlaybookBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const addActionNode = () => {
    const newNode: Node = {
      id: `node_${nodes.length + 1}`,
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: { label: `Action Step ${nodes.length}` },
    }
    setNodes((nds) => nds.concat(newNode))
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] w-full gap-4">
      {/* Builder Canvas */}
      <Card className="flex-1 overflow-hidden">
        <CardHeader className="py-4 border-b">
          <CardTitle>Playbook Editor</CardTitle>
        </CardHeader>
        <CardContent className="p-0 h-full w-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background gap={12} size={1} />
          </ReactFlow>
        </CardContent>
      </Card>

      {/* Sidebar Toolbar */}
      <Card className="w-80 overflow-y-auto">
        <CardHeader className="py-4 border-b">
          <CardTitle>Tools</CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div>
            <h4 className="mb-2 text-sm font-medium">Add Node</h4>
            <div className="grid gap-2">
              <Button onClick={addActionNode} variant="secondary" className="w-full justify-start">
                + Action Step
              </Button>
              <Button variant="secondary" className="w-full justify-start">
                + Logic Condition
              </Button>
            </div>
          </div>

          <div className="border-t pt-4 mt-4">
            <h4 className="mb-2 text-sm font-medium">Node Configuration</h4>
            <p className="text-xs text-muted-foreground">Select a node to configure its properties, ECS template, and variables.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
