import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { PageTransition } from '@/components/motion'
import Sidebar from './Sidebar'
import AIHeader from './AIHeader'

/**
 * AIAdvisorLayout Component
 *
 * Coordinates the AI Workspace layout:
 * - Left Conversation Sidebar (drawer on mobile)
 * - Main Chat / Module Workspace
 */
export function AIAdvisorLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <PageTransition className="flex h-[calc(100vh-4rem)] w-full bg-background overflow-hidden select-none">
      {/* Column 1: Left Conversation Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Column 2: Center Workspace (Header + Nested Route Outlet) */}
      <main className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <AIHeader onOpenSidebar={() => setSidebarOpen(true)} />

        <div className="flex-1 overflow-hidden relative">
          <Outlet />
        </div>
      </main>
    </PageTransition>
  )
}

export default AIAdvisorLayout
