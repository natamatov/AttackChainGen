import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import Users from '@/pages/Users'
import Playbooks from '@/pages/Playbooks'
import PlaybookBuilder from '@/pages/PlaybookBuilder'
import Layout from '@/components/Layout'

import Stands from '@/pages/Stands'
import Simulations from '@/pages/Simulations'
import Environments from '@/pages/Environments'
import AIPrompt from '@/pages/AIPrompt'
import MitreMatrix from '@/pages/MitreMatrix'
import ThreatIntel from '@/pages/ThreatIntel'
import MitreMappingPage from '@/pages/MitreMapping'
import Settings from '@/pages/Settings'
import Instructions from '@/pages/Instructions'
import Assignments from '@/pages/Assignments'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected routes wrapped in Layout */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="playbooks" element={<Playbooks />} />
          <Route path="playbooks/builder" element={<PlaybookBuilder />} />
          <Route path="stands" element={<Stands />} />
          <Route path="simulations" element={<Simulations />} />
          <Route path="environments" element={<Environments />} />
          <Route path="ai-prompt" element={<AIPrompt />} />
          <Route path="mitre" element={<MitreMatrix />} />
          <Route path="threat-intel" element={<ThreatIntel />} />
          <Route path="mitre-mapping" element={<MitreMappingPage />} />
          <Route path="users" element={<Users />} />
          <Route path="settings" element={<Settings />} />
          <Route path="instructions" element={<Instructions />} />
          <Route path="assignments" element={<Assignments />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
