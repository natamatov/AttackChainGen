import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'

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

  useEffect(() => {
    fetchEnvironments()
  }, [])

  const fetchEnvironments = async () => {
    try {
      const res = await api.get('/environments/')
      setEnvironments(res.data)
    } catch (err) {
      console.error(err)
    }
  }

  const generatePrompt = async () => {
    if (!selectedEnvId) return
    setLoading(true)
    try {
      const res = await api.get(`/ai-prompt/${selectedEnvId}`)
      if (res.data.prompt) {
        setPrompt(res.data.prompt)
      } else {
        window.alert(res.data.detail || 'Failed to generate prompt')
      }
    } catch (err: any) {
      window.alert(err.response?.data?.detail || 'Server error')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(prompt)
    window.alert('Prompt copied to clipboard.')
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
          <div className="w-64 space-y-2 flex flex-col">
            <label className="text-sm font-medium">Environment</label>
            <select 
              value={selectedEnvId} 
              onChange={e => setSelectedEnvId(e.target.value)}
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select Environment</option>
              {environments.map(env => (
                <option key={env.id} value={env.id.toString()}>
                  {env.name} ({env.domain})
                </option>
              ))}
            </select>
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
