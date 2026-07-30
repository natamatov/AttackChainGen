import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { Save, AlertCircle, CheckCircle } from 'lucide-react'

interface Setting {
    key: string;
    value: string;
    description: string;
}

export default function Settings() {
    const [settings, setSettings] = useState<Setting[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)

    useEffect(() => {
        fetchSettings()
    }, [])

    const fetchSettings = async () => {
        try {
            const res = await api.get('/settings/')
            setSettings(res.data)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Ошибка загрузки настроек')
        } finally {
            setLoading(false)
        }
    }

    const getSettingValue = (key: string) => {
        const s = settings.find(s => s.key === key)
        return s ? s.value : ''
    }

    const handleSettingChange = (key: string, value: string, description: string = '') => {
        setSettings(prev => {
            const existing = prev.find(s => s.key === key)
            if (existing) {
                return prev.map(s => s.key === key ? { ...s, value } : s)
            }
            return [...prev, { key, value, description }]
        })
    }

    const handleSave = async () => {
        setSaving(true)
        setError(null)
        setSuccess(false)
        try {
            await api.put('/settings/', { settings })
            setSuccess(true)
            setTimeout(() => setSuccess(false), 3000)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Ошибка сохранения настроек')
        } finally {
            setSaving(false)
        }
    }

    if (loading) {
        return <div className="p-8">Загрузка...</div>
    }

    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h3 className="text-lg font-medium">Глобальные настройки</h3>
                <p className="text-sm text-muted-foreground">
                    Управление интеграциями и глобальными параметрами системы.
                </p>
            </div>

            {error && (
                <div className="bg-destructive/15 text-destructive border-destructive/50 flex items-center p-4 rounded-md border">
                    <AlertCircle className="h-4 w-4 mr-2" />
                    <div>
                        <h4 className="font-semibold text-sm">Ошибка</h4>
                        <div className="text-sm">{error}</div>
                    </div>
                </div>
            )}

            {success && (
                <div className="bg-green-500/15 text-green-600 border-green-500/50 flex items-center p-4 rounded-md border">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    <div>
                        <h4 className="font-semibold text-sm">Успех</h4>
                        <div className="text-sm">Настройки успешно сохранены!</div>
                    </div>
                </div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle>Интеграция с OpenCTI</CardTitle>
                    <CardDescription>
                        Настройки подключения к серверу OpenCTI для загрузки Threat Intelligence
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium">OpenCTI URL</label>
                        <Input
                            placeholder="http://192.168.111.133:8080"
                            value={getSettingValue('OPENCTI_URL')}
                            onChange={(e) => handleSettingChange('OPENCTI_URL', e.target.value, 'URL сервера OpenCTI')}
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium">OpenCTI Token</label>
                        <Input
                            type="password"
                            placeholder="API Token"
                            value={getSettingValue('OPENCTI_TOKEN')}
                            onChange={(e) => handleSettingChange('OPENCTI_TOKEN', e.target.value, 'API токен OpenCTI')}
                        />
                    </div>
                    <Button onClick={handleSave} disabled={saving} className="mt-4">
                        <Save className="mr-2 h-4 w-4" />
                        {saving ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}
