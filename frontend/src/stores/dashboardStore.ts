// ============================================================
// 대시보드 전역 상태 — Zustand
// 선택된 설비, 알람 확인 여부, 챗봇 열림/닫힘
// ============================================================

import { create } from 'zustand'

interface DashboardStore {
  // 현재 선택된 설비 ID
  selectedEquipmentId: string | null
  setSelectedEquipmentId: (id: string | null) => void

  // 챗봇 FAB 열림 상태
  chatOpen: boolean
  setChatOpen: (open: boolean) => void
  toggleChat: () => void

  // 상단 오버레이 (작업현황 / 재고현황)
  activeOverlay: 'work' | 'inventory' | null
  setActiveOverlay: (key: 'work' | 'inventory' | null) => void
  toggleOverlay: (key: 'work' | 'inventory') => void
}

export const useDashboardStore = create<DashboardStore>((set, _get) => ({
  selectedEquipmentId: null,
  setSelectedEquipmentId: (id) => set({ selectedEquipmentId: id }),

  chatOpen: false,
  setChatOpen: (open) => set({ chatOpen: open }),
  toggleChat: () => set((s) => ({ chatOpen: !s.chatOpen })),

  activeOverlay: null,
  setActiveOverlay: (key) => set({ activeOverlay: key }),
  toggleOverlay: (key) =>
    set((s) => ({ activeOverlay: s.activeOverlay === key ? null : key })),
}))
