import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Copy, Sparkles } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

interface Environment {
  id: number
  name: string
  domain: string
}

export default function AIPrompt() {
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [selectedEnvId, setSelectedEnvId] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchEnvironments()
  }, [])

  const fetchEnvironments = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/environments')
      const data = await res.json()
      setEnvironments(data)
    } catch (err) {
      console.error(err)
    }
  }

  const generatePrompt = async () => {
    if (!selectedEnvId) return
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8000/api/ai-prompt/${selectedEnvId}`)
      const data = await res.json()
      if (data.prompt) {
        setPrompt(data.prompt)
      } else {
        toast({ title: 'Error', description: data.detail || 'Failed to generate prompt', variant: 'destructive' })
      }
    } catch (err) {
      toast({ title: 'Error', description: 'Server error', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(prompt)
    toast({
      title: 'Copied!',
      description: 'Prompt copied to clipboard.',
    })
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">AI Playbook Generator</h1>
        <p className="text-muted-foreground">
          Генерация универсального промпта для ИИ (ChatGPT/Claude) на основе топологии вымышленной сети.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Настройки промпта</CardTitle>
          <CardDescription>Выберите вымышленную сеть для генерации промпта</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4 items-end">
          <div className="w-64 space-y-2">
            <label className="text-sm font-medium">Environment</label>
            <Select value={selectedEnvId} onValueChange={setSelectedEnvId}>
              <SelectTrigger>
                <SelectValue placeholder="Select Environment" />
              </SelectTrigger>
              <SelectContent>
                {environments.map(env => (
                  <SelectItem key={env.id} value={env.id.toString()}>
                    {env.name} ({env.domain})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={generatePrompt} disabled={!selectedEnvId || loading} className="gap-2">
            <Sparkles className="w-4 h-4" />
            Сгенерировать промпт
          </Button>
        </CardContent>
      </Card>

      {prompt && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-lg">Готовый промпт для ИИ</CardTitle>
            <Button onClick={copyToClipboard} variant="outline" size="sm" className="gap-2">
              <Copy className="w-4 h-4" />
              Copy
            </Button>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded-md font-mono text-sm whitespace-pre-wrap max-h-[500px] overflow-y-auto">
              {prompt}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
