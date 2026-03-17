// ============================================================
// 대시보드 전역 상태 — Zustand
// ============================================================

import { create } from 'zustand'
import type { AlarmEvent } from '@/types'

interface DashboardStore {
  selectedEquipmentId: string | null
  setSelectedEquipmentId: (id: string | null) => void

  selectedAlarm: AlarmEvent | null
  setSelectedAlarm: (alarm: AlarmEvent | null) => void

  prevAlarmCount: number
  setPrevAlarmCount: (count: number) => void

  chatOpen: boolean
  setChatOpen: (open: boolean) => void
  toggleChat: () => void

  activeOverlay: 'work' | 'inventory' | null
  setActiveOverlay: (key: 'work' | 'inventory' | null) => void
  toggleOverlay: (key: 'work' | 'inventory') => void
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  selectedEquipmentId: null,
  setSelectedEquipmentId: (id) => set({ selectedEquipmentId: id, selectedAlarm: null }),

  selectedAlarm: null,
  setSelectedAlarm: (alarm) => set({ selectedAlarm: alarm, selectedEquipmentId: null }),

  prevAlarmCount: 0,
  setPrevAlarmCount: (count) => set({ prevAlarmCount: count }),

  chatOpen: false,
  setChatOpen: (open) => set({ chatOpen: open }),
  toggleChat: () => set((s) => ({ chatOpen: !s.chatOpen })),

  activeOverlay: null,
  setActiveOverlay: (key) => set({ activeOverlay: key }),
  toggleOverlay: (key) =>
    set((s) => ({ activeOverlay: s.activeOverlay === key ? null : key })),
}))
