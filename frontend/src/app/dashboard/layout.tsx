'use client'

import React from 'react'
import Link from 'next/link'
import { UserCog } from 'lucide-react'
import { useUserRole } from '@/hooks/useUserRole'
import { UserMenu } from '@/components/ui/user-menu'
import { RoleSidebar } from '@/components/RoleSidebar'

/**
 * 🏗️ **DashboardLayout** - Layout principale della dashboard
 * 
 * **Aggiornato per utilizzare RoleSidebar v1.4.3:**
 * - ✅ Sostituita la sidebar statica con RoleSidebar dinamica
 * - ✅ Menu configurati per ruolo in config/menus.ts
 * - ✅ Header unificato con indicatore ruolo
 * - ✅ Layout responsivo mantenuto
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { role } = useUserRole()

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header unificato */}
      <header className="sticky top-0 z-10 w-full border-b bg-background shadow-sm">
        <div className="flex h-16 items-center px-4 md:px-6 justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold text-xl text-primary">
            Manta Group
          </Link>
          <nav className="flex items-center gap-4">
            {role && (
              <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                <UserCog className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">{role}</span>
              </div>
            )}
            <UserMenu />
          </nav>
        </div>
      </header>

      {/* Layout principale con sidebar dinamica */}
      <div className="flex-1 md:grid md:grid-cols-[240px_1fr]">
        {/* 🎭 Sidebar dinamica basata sui ruoli */}
        <RoleSidebar />

        {/* Contenuto principale */}
        <main className="flex flex-col flex-1 w-full overflow-hidden">
          <div className="p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
