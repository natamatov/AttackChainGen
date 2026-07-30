import { useState } from 'react'
import { Server, ChevronDown, ChevronRight, CheckCircle, AlertCircle, Info, Zap, Shield, Database, Play, Globe, FileText } from 'lucide-react'

const steps = [
  {
    num: 1,
    title: "Настройте Stand (стенд Elasticsearch)",
    icon: Server,
    color: "blue",
    desc: "Stand — это подключение к вашему Elasticsearch / Elastic Security, куда будут отправляться синтетические логи.",
    items: [
      "Перейдите в Settings → Stands",
      "Нажмите «Add Stand»",
      "Укажите URL Elasticsearch (например: http://192.168.1.10:9200)",
      "Введите API Key или логин/пароль",
      "Укажите индекс (например: logs-attackchain-*)",
      "Нажмите «Test Connection» и убедитесь, что соединение установлено",
      "Сохраните стенд"
    ],
    note: "Один стенд = одна группа аналитиков. Создайте отдельный стенд для каждой учебной группы."
  },
  {
    num: 2,
    title: "Настройте CMDB (виртуальная сеть)",
    icon: Database,
    color: "purple",
    desc: "CMDB описывает виртуальную инфраструктуру, чьи хосты и IP будут фигурировать в сгенерированных логах.",
    items: [
      "Перейдите в Settings → CMDB (Environments)",
      "Создайте Environment (например: corp.local)",
      "Добавьте сетевые зоны (Servers 192.168.100.0/24, Workstations 192.168.101.0/24)",
      "В каждой зоне добавьте активы: укажите hostname, IP, ОС, роль устройства",
      "Сохраните изменения"
    ],
    note: "Чем детальнее CMDB — тем реалистичнее будут логи. Аналитики увидят реальные имена хостов из вашей среды."
  },
  {
    num: 3,
    title: "Выберите или создайте Playbook",
    icon: FileText,
    color: "green",
    desc: "Playbook — это сценарий атаки в формате YAML. Он описывает цепочку событий Kill Chain, которые будут отправлены в Elastic.",
    items: [
      "Перейдите в Playbooks",
      "Используйте готовые плейбуки (DCSync, Kerberoasting, Phishing и др.)",
      "Или нажмите «Generate with AI» для создания нового через LLM",
      "Или зайдите в Threat Intel и сгенерируйте плейбук на основе реальной APT-группировки из OpenCTI",
      "Просмотрите YAML и аналитический гайд перед запуском"
    ],
    note: "Поле analyst_guide в YAML — это чеклист для преподавателя. Заполните его, чтобы шпаргалка была доступна после симуляции."
  },
  {
    num: 4,
    title: "Запустите симуляцию",
    icon: Play,
    color: "orange",
    desc: "Симуляция отправляет все события из плейбука в Elasticsearch на выбранный стенд.",
    items: [
      "Перейдите в Simulations",
      "Нажмите «Run Playbook»",
      "Выберите плейбук и стенд",
      "Выберите режим: Realtime (с реальными задержками) или Historical (мгновенно, в прошлом)",
      "Для Historical укажите смещение (например: 2h, 1d — события будут помечены этим временем назад)",
      "Нажмите «Start Run»",
      "Наблюдайте за прогрессом в таблице"
    ],
    note: "Historical-режим рекомендуется для обучения: аналитики сразу видят все события в Elastic и могут начинать расследование."
  },
  {
    num: 5,
    title: "Проверьте результат",
    icon: CheckCircle,
    color: "teal",
    desc: "После завершения симуляции преподаватель получает шпаргалку, а аналитики — задачу найти атаку в Elastic.",
    items: [
      "Дайте аналитикам задание: найти атаку в Elastic Security / Kibana",
      "Нажмите «Шпаргалка» у завершённой симуляции",
      "В попапе вы увидите таблицу сгенерированных IOC (IP атакующего, хэши, PID процессов)",
      "Там же отобразится чеклист расследования с шагами проверки",
      "Сверьте ответы аналитиков с реальными артефактами симуляции"
    ],
    note: "Не показывайте шпаргалку аналитикам до окончания расследования — это ответы!"
  },
  {
    num: 6,
    title: "Threat Intel & OpenCTI (опционально)",
    icon: Globe,
    color: "red",
    desc: "Интеграция с OpenCTI позволяет автоматически генерировать плейбуки на основе реальных APT-кампаний.",
    items: [
      "Перейдите в Settings → OpenCTI Integration",
      "Введите URL вашего OpenCTI (например: http://192.168.111.133:8080)",
      "Введите API Token (из профиля OpenCTI: Profile → API Access)",
      "Нажмите «Сохранить»",
      "Зайдите в Threat Intel",
      "Нажмите «Синхронизировать фиды» — загрузятся APT-группировки с отчётами",
      "Выберите группировку, нажмите «Generate Playbook»",
      "Плейбук будет создан на основе реальных TTPs и IOCs из OpenCTI"
    ],
    note: "Этот шаг опционален. Без OpenCTI платформа полностью работает с встроенными плейбуками."
  }
]

const concepts = [
  { icon: FileText, title: "Playbook", color: "green", desc: "YAML-сценарий атаки. Описывает шаги Kill Chain: какие события генерировать, в какой последовательности и с какими задержками." },
  { icon: Server, title: "Stand", color: "blue", desc: "Подключение к Elasticsearch. Стенд = учебная группа. Один Stand — одна изолированная среда расследования." },
  { icon: Play, title: "Simulation", color: "orange", desc: "Запуск плейбука на стенде. Система генерирует ECS-совместимые логи и отправляет их в Elastic Bulk API." },
  { icon: Database, title: "CMDB", color: "purple", desc: "Виртуальная инфраструктура: сети, зоны, хосты. Делает логи реалистичными — аналитики видят реальные имена хостов." },
  { icon: Shield, title: "MITRE Matrix", color: "indigo", desc: "Карта покрытия тактик и техник ATT&CK. Показывает, какие техники охватывают ваши плейбуки." },
  { icon: Zap, title: "Noise Generator", color: "yellow", desc: "Фоновые легитимные события. Усложняют расследование, имитируя реальную активность пользователей в сети." },
]

const colorMap: Record<string, string> = {
  blue: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  purple: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  green: "bg-green-500/10 text-green-600 border-green-500/20",
  orange: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  teal: "bg-teal-500/10 text-teal-600 border-teal-500/20",
  red: "bg-red-500/10 text-red-600 border-red-500/20",
  indigo: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
  yellow: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
}

const dotMap: Record<string, string> = {
  blue: "bg-blue-500",
  purple: "bg-purple-500",
  green: "bg-green-500",
  orange: "bg-orange-500",
  teal: "bg-teal-500",
  red: "bg-red-500",
  indigo: "bg-indigo-500",
  yellow: "bg-yellow-500",
}

export default function Instructions() {
  const [openStep, setOpenStep] = useState<number | null>(0)

  return (
    <div className="space-y-10 max-w-4xl mx-auto pb-16">
      {/* Hero */}
      <div className="rounded-xl border bg-gradient-to-br from-primary/5 to-primary/10 p-8">
        <div className="flex items-start gap-5">
          <div className="rounded-xl bg-primary/10 p-4 shrink-0">
            <Shield className="h-10 w-10 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2">AttackChainGen</h1>
            <p className="text-muted-foreground text-base leading-relaxed max-w-2xl">
              Платформа для имитации кибератак и обучения аналитиков SOC. Система генерирует реалистичные синтетические
              логи по сценариям атак (Kill Chain) и отправляет их в Elasticsearch — аналитики расследуют инциденты,
              как в реальной жизни, не подвергая риску боевую инфраструктуру.
            </p>
            <div className="flex flex-wrap gap-3 mt-4">
              <span className="text-xs px-3 py-1 rounded-full border bg-background font-medium">ECS 8.x совместимость</span>
              <span className="text-xs px-3 py-1 rounded-full border bg-background font-medium">MITRE ATT&CK</span>
              <span className="text-xs px-3 py-1 rounded-full border bg-background font-medium">Real-time & Historical режимы</span>
              <span className="text-xs px-3 py-1 rounded-full border bg-background font-medium">OpenCTI интеграция</span>
              <span className="text-xs px-3 py-1 rounded-full border bg-background font-medium">LLM генерация</span>
            </div>
          </div>
        </div>
      </div>

      {/* How it works */}
      <div>
        <h2 className="text-xl font-bold mb-1">Как это работает</h2>
        <p className="text-sm text-muted-foreground mb-5">Преподаватель запускает симуляцию → аналитики расследуют в Elastic → преподаватель проверяет по шпаргалке</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4 bg-card">
            <div className="text-2xl font-bold text-primary mb-2">01</div>
            <h3 className="font-semibold mb-1">Инструктор</h3>
            <p className="text-sm text-muted-foreground">Выбирает сценарий атаки и стенд, запускает симуляцию. Система отправляет логи в Elasticsearch.</p>
          </div>
          <div className="border rounded-lg p-4 bg-card">
            <div className="text-2xl font-bold text-blue-500 mb-2">02</div>
            <h3 className="font-semibold mb-1">Аналитик</h3>
            <p className="text-sm text-muted-foreground">Исследует события в Kibana / Elastic Security. Ищет аномалии, строит временную шкалу атаки.</p>
          </div>
          <div className="border rounded-lg p-4 bg-card">
            <div className="text-2xl font-bold text-green-500 mb-2">03</div>
            <h3 className="font-semibold mb-1">Проверка</h3>
            <p className="text-sm text-muted-foreground">Инструктор открывает шпаргалку с реальными IOC симуляции и сверяет с ответами аналитиков.</p>
          </div>
        </div>
      </div>

      {/* Key concepts */}
      <div>
        <h2 className="text-xl font-bold mb-4">Ключевые понятия</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {concepts.map(c => (
            <div key={c.title} className={`flex gap-3 border rounded-lg p-4 ${colorMap[c.color]}`}>
              <c.icon className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-sm">{c.title}</div>
                <div className="text-xs mt-0.5 opacity-80">{c.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Step by step */}
      <div>
        <h2 className="text-xl font-bold mb-1">Пошаговая настройка</h2>
        <p className="text-sm text-muted-foreground mb-5">Выполните шаги по порядку для первого запуска</p>
        <div className="space-y-3">
          {steps.map((step, idx) => {
            const isOpen = openStep === idx
            const Icon = step.icon
            return (
              <div key={step.num} className="border rounded-xl overflow-hidden bg-card">
                <button
                  className="w-full flex items-center gap-4 p-4 text-left hover:bg-muted/40 transition-colors"
                  onClick={() => setOpenStep(isOpen ? null : idx)}
                >
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 border ${colorMap[step.color]}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-muted-foreground">Шаг {step.num}</span>
                    </div>
                    <div className="font-semibold text-sm truncate">{step.title}</div>
                  </div>
                  {isOpen
                    ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                    : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  }
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pt-0 ml-13">
                    <div className="ml-[3.25rem]">
                      <p className="text-sm text-muted-foreground mb-3">{step.desc}</p>
                      <ol className="space-y-2 mb-3">
                        {step.items.map((item, i) => (
                          <li key={i} className="flex gap-3 text-sm">
                            <span className={`w-5 h-5 rounded-full text-xs flex items-center justify-center shrink-0 mt-0.5 text-white ${dotMap[step.color]}`}>
                              {i + 1}
                            </span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ol>
                      <div className={`flex gap-2 p-3 rounded-lg border text-xs ${colorMap[step.color]}`}>
                        <Info className="h-4 w-4 shrink-0 mt-0.5" />
                        <span>{step.note}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Playbook YAML format */}
      <div>
        <h2 className="text-xl font-bold mb-4">Формат YAML плейбука</h2>
        <div className="border rounded-xl overflow-hidden">
          <div className="bg-muted/50 px-4 py-2 border-b text-xs font-mono text-muted-foreground">playbook_example.yaml</div>
          <pre className="p-4 text-xs font-mono leading-relaxed overflow-x-auto bg-background text-foreground">{`name: "Spearphishing → C2 Connection"
description: "Фишинг с последующим C2 подключением"
mitre_tactics: ["Initial Access", "Execution", "Command and Control"]
mitre_techniques: ["T1566", "T1059", "T1071"]

# Аналитический гайд (шпаргалка преподавателя)
analyst_guide: |
  ## Чеклист расследования
  1. [ ] Найти событие запуска WINWORD.EXE с подозрительными аргументами
  2. [ ] Проверить дочерние процессы (powershell.exe, cmd.exe)
  3. [ ] Найти сетевое соединение к C2-серверу
  Ответы: IP C2 = {c2_ip}, Hash = {malware_hash}

# Глобальный контекст (подставляется во все шаги)
global_context:
  host.name: "DESKTOP-HR-01"
  user.name: "j.doe"

steps:
  - id: "step_1_phishing"
    template: "win_sysmon_1_process_creation"
    delay_from_start: "0s"
    fields:
      process.name: "WINWORD.EXE"
      process.command_line: "WINWORD.EXE /q report_Q3.docm"

  - id: "step_2_execution"
    depends_on: "step_1_phishing"   # Наследует PID из шага 1
    template: "win_sysmon_1_process_creation"
    delay_from_prev: "15s"
    fields:
      process.name: "powershell.exe"
      process.command_line: "powershell.exe -nop -w hidden -c IEX..."

  - id: "step_3_c2"
    depends_on: "step_2_execution"
    template: "network_connection"
    delay_from_prev: "30s"
    fields:
      destination.port: 443`}</pre>
        </div>
      </div>

      {/* Templates reference */}
      <div>
        <h2 className="text-xl font-bold mb-4">Доступные шаблоны событий</h2>
        <div className="border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Шаблон</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Тип события</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">ОС</th>
              </tr>
            </thead>
            <tbody>
              {[
                ["sysmon_event_1", "Process Creation (Sysmon Event ID 1)", "Windows"],
                ["sysmon_event_3", "Network Connection (Sysmon Event ID 3)", "Windows"],
                ["sysmon_event_11", "File Create (Sysmon Event ID 11)", "Windows"],
                ["win_security_4624", "Successful Logon (Event ID 4624)", "Windows"],
                ["win_security_4625", "Failed Logon (Event ID 4625)", "Windows"],
                ["win_security_4688", "Process Creation (Event ID 4688)", "Windows"],
                ["win_security_4720", "User Account Created (Event ID 4720)", "Windows"],
                ["win_security_4732", "Member Added to Group (Event ID 4732)", "Windows"],
                ["linux_auditd_execve", "Process Execution (auditd)", "Linux"],
                ["linux_syslog_auth", "Authentication Event (syslog)", "Linux"],
                ["network_connection", "Generic Network Connection", "Any"],
                ["iis_web_log", "IIS Web Server Access Log", "Windows"],
                ["generic_event", "Generic Security Event", "Any"],
              ].map(([tmpl, desc, os]) => (
                <tr key={tmpl} className="border-t hover:bg-muted/30">
                  <td className="px-4 py-2.5 font-mono text-xs text-primary">{tmpl}</td>
                  <td className="px-4 py-2.5 text-xs">{desc}</td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground">{os}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modes */}
      <div>
        <h2 className="text-xl font-bold mb-4">Режимы симуляции</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="border rounded-xl p-5 bg-card">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 border border-blue-500/20 font-medium">REALTIME</span>
              <h3 className="font-semibold">Режим реального времени</h3>
            </div>
            <p className="text-sm text-muted-foreground">События генерируются с реальными задержками из плейбука. Симуляция может длиться часы. Подходит для live-упражнений, когда нужно поймать атаку в процессе.</p>
            <div className="mt-3 text-xs text-muted-foreground border-t pt-3">Параметр <code className="font-mono bg-muted px-1 rounded">delay_from_prev: "5m"</code> создаёт реальную паузу 5 минут.</div>
          </div>
          <div className="border rounded-xl p-5 bg-card">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-600 border border-purple-500/20 font-medium">HISTORICAL</span>
              <h3 className="font-semibold">Исторический режим</h3>
            </div>
            <p className="text-sm text-muted-foreground">Все события генерируются мгновенно, но с временными метками в прошлом. Аналитики сразу получают полную картину и начинают расследование.</p>
            <div className="mt-3 text-xs text-muted-foreground border-t pt-3">Параметр <code className="font-mono bg-muted px-1 rounded">Backdate: 2h</code> сдвигает все метки на 2 часа назад.</div>
          </div>
        </div>
      </div>

      {/* Tips */}
      <div className="border rounded-xl p-6 bg-amber-500/5 border-amber-500/20">
        <div className="flex items-center gap-2 mb-3">
          <AlertCircle className="h-5 w-5 text-amber-600" />
          <h2 className="text-lg font-bold text-amber-700 dark:text-amber-500">Советы для преподавателей</h2>
        </div>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex gap-2"><span className="text-amber-500 font-bold shrink-0">→</span>Начинайте с простых плейбуков (Brute Force, Phishing) прежде чем переходить к сложным цепочкам.</li>
          <li className="flex gap-2"><span className="text-amber-500 font-bold shrink-0">→</span>Используйте Noise Generator (Low/Medium) для имитации реальной среды — аналитики должны уметь отфильтровывать легитимный трафик.</li>
          <li className="flex gap-2"><span className="text-amber-500 font-bold shrink-0">→</span>Не запускайте симуляцию на боевой Elasticsearch — создайте отдельный учебный стенд.</li>
          <li className="flex gap-2"><span className="text-amber-500 font-bold shrink-0">→</span>Заполняйте поле <code className="font-mono bg-muted px-1 rounded text-xs">analyst_guide</code> в плейбуках — это ваша шпаргалка для проверки студентов.</li>
          <li className="flex gap-2"><span className="text-amber-500 font-bold shrink-0">→</span>Historical-режим + детальная CMDB = максимальный реализм без ожидания.</li>
        </ul>
      </div>
    </div>
  )
}
