import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Playbooks from '@/pages/Playbooks'
import PlaybookBuilder from '@/pages/PlaybookBuilder'
import Layout from '@/components/Layout'

import Stands from '@/pages/Stands'
import Simulations from '@/pages/Simulations'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes wrapped in Layout */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="playbooks" element={<Playbooks />} />
          <Route path="playbooks/builder" element={<PlaybookBuilder />} />
          <Route path="stands" element={<Stands />} />
          <Route path="simulations" element={<Simulations />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
