// ============================================================
// App — TanStack Query 설정 + AppShell 마운트
// ============================================================

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from '@/components/layout/AppShell'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5000,         // 5초 내 동일 쿼리 재요청 방지
      refetchOnWindowFocus: false, // 탭 전환 시 불필요한 refetch 방지
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppShell />
    </QueryClientProvider>
  )
}
