import { useState } from 'react'
import { Navigate, Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useAppStore } from '@/store/appStore'
import { Activity, BookOpen, Server, LogOut, Play, ShieldAlert, Users, Settings as SettingsIcon, ChevronDown, ChevronRight, Layers, HelpCircle, CheckSquare } from 'lucide-react'
import { SimulationTracker } from '@/components/SimulationTracker'

type NavItem = {
  name: string
  href?: string
  icon: any
  children?: { name: string, href: string, icon: any }[]
}

export default function Layout() {
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const activeRunId = useAppStore((state) => state.activeRunId)
  const location = useLocation()
  
  const [settingsOpen, setSettingsOpen] = useState(
    location.pathname.startsWith('/stands') || 
    location.pathname.startsWith('/environments') || 
    location.pathname.startsWith('/settings')
  )

  if (!token) {
    return <Navigate to="/login" replace />
  }

  let navItems: NavItem[] = []

  if (user?.role === 'student') {
    navItems = [
      { name: 'Мои Задания', href: '/assignments', icon: CheckSquare },
      { name: 'Инструкция', href: '/instructions', icon: HelpCircle },
    ]
  } else {
    navItems = [
      { name: 'Dashboard', href: '/', icon: Activity },
      { name: 'Playbooks', href: '/playbooks', icon: BookOpen },
      { name: 'Simulations', href: '/simulations', icon: Play },
      { name: 'Threat Intel', href: '/threat-intel', icon: ShieldAlert },
      { name: 'MITRE Matrix', href: '/mitre', icon: ShieldAlert },
      { name: 'Инструкция', href: '/instructions', icon: HelpCircle },
      { name: 'Задания (CTF)', href: '/assignments', icon: CheckSquare },
    ]
  }

  if (user?.role === 'admin') {
    navItems.push({ name: 'Users', href: '/users', icon: Users })
    navItems.push({
      name: 'Settings',
      icon: SettingsIcon,
      children: [
        { name: 'Stands', href: '/stands', icon: Layers },
        { name: 'CMDB (Environments)', href: '/environments', icon: Server },
        { name: 'OpenCTI Integration', href: '/settings', icon: ShieldAlert }
      ]
    })
  }

  return (
    <div className="flex min-h-screen w-full bg-muted/40">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-10 hidden w-64 flex-col border-r bg-background sm:flex">
        <div className="flex h-14 items-center border-b px-6">
          <span className="font-semibold text-lg tracking-tight">AttackChainGen</span>
        </div>
        <nav className="flex flex-col gap-2 p-4 text-sm font-medium">
          {navItems.map((item) => {
            if (item.children) {
              return (
                <div key={item.name} className="flex flex-col gap-1">
                  <button
                    onClick={() => setSettingsOpen(!settingsOpen)}
                    className="flex items-center justify-between w-full rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      {item.name}
                    </div>
                    {settingsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </button>
                  {settingsOpen && (
                    <div className="ml-6 flex flex-col gap-1 border-l pl-2 mt-1">
                      {item.children.map(child => (
                        <Link
                          key={child.name}
                          to={child.href}
                          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary ${
                            location.pathname === child.href ? 'bg-muted text-primary' : ''
                          }`}
                        >
                          <child.icon className="h-4 w-4" />
                          {child.name}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )
            }

            return (
              <Link
                key={item.name}
                to={item.href!}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary ${
                  location.pathname === item.href ? 'bg-muted text-primary' : ''
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col sm:pl-64 w-full">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-6 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6 py-4">
          <div className="flex items-center gap-4 w-full justify-end">
            <span className="text-sm font-medium text-muted-foreground">
              {user?.email} ({user?.role})
            </span>
            <button 
              onClick={logout}
              className="text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>

      <SimulationTracker runId={activeRunId} />
    </div>
  )
}
