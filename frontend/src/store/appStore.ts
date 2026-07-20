import { create } from 'zustand'

interface AppState {
  activeRunId: number | null
  setActiveRunId: (id: number | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  activeRunId: null,
  setActiveRunId: (id) => set({ activeRunId: id }),
}))
