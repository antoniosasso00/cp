'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useUserRole } from '@/hooks/useUserRole'
import { getMenuForRole, getMenuStats, type MenuItem, type MenuSection } from '@/config/menus'
import { UserCog } from 'lucide-react'

interface RoleSidebarProps {
  /**
   * Se true, mostra la sidebar in modalità collassata
   */
  collapsed?: boolean
  /**
   * Callback quando la sidebar viene collassata/espansa
   */
  onToggleCollapse?: () => void
  /**
   * Classi CSS aggiuntive per il contenitore della sidebar
   */
  className?: string
}

/**
 * 🎭 **RoleSidebar** - Componente sidebar dinamica basata sui ruoli
 * 
 * **Funzionalità:**
 * - Legge automaticamente il ruolo da `localStorage.role`
 * - Mostra solo i menu items autorizzati per il ruolo corrente
 * - Supporta sidebar collassabile 
 * - Evidenzia la voce attiva basandosi sul pathname
 * - Gestisce stati di loading e ruoli non riconosciuti
 * 
 * **Utilizzo:**
 * ```tsx
 * <RoleSidebar collapsed={false} onToggleCollapse={() => setCollapsed(!collapsed)} />
 * ```
 */
export function RoleSidebar({ 
  collapsed = false, 
  onToggleCollapse,
  className 
}: RoleSidebarProps) {
  const pathname = usePathname()
  const { role, isLoading } = useUserRole()

  // Stato di loading
  if (isLoading) {
    return <SidebarSkeleton collapsed={collapsed} />
  }

  // Ottieni menu per ruolo corrente
  const menuSections = getMenuForRole(role)
  const stats = getMenuStats()

  return (
    <aside className={cn(
      "fixed top-[64px] z-30 h-[calc(100vh-64px)] shrink-0 border-r bg-background transition-all duration-300",
      "hidden md:sticky md:block",
      collapsed ? "w-16" : "w-64",
      className
    )}>
      <div className="h-full py-6 overflow-y-auto">
        {/* Header con informazioni ruolo */}
        {!collapsed && (
          <div className="px-6 mb-6">
            <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 rounded-lg">
              <UserCog className="h-4 w-4 text-primary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-primary truncate">
                  {role || 'Nessun ruolo'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {menuSections.length} sezioni, {stats[role?.toLowerCase() as keyof typeof stats]?.items || 0} voci
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigazione menu */}
        <nav className={cn("space-y-6", collapsed ? "px-2" : "px-6")}>
          {menuSections.length > 0 ? (
            menuSections.map((section, sectionIndex) => (
              <MenuSection
                key={sectionIndex}
                section={section}
                collapsed={collapsed}
                currentPath={pathname}
              />
            ))
          ) : (
            <EmptyMenu collapsed={collapsed} role={role} />
          )}
        </nav>

        {/* Debug info - solo in development */}
        {process.env.NODE_ENV === 'development' && !collapsed && (
          <div className="px-6 mt-6 pt-6 border-t border-border">
            <details className="text-xs text-muted-foreground">
              <summary className="cursor-pointer hover:text-foreground">
                🐛 Debug Info
              </summary>
              <div className="mt-2 space-y-1 text-[10px] font-mono">
                <div>Ruolo: {role || 'null'}</div>
                <div>Pathname: {pathname}</div>
                <div>Sezioni: {menuSections.length}</div>
              </div>
            </details>
          </div>
        )}
      </div>
    </aside>
  )
}

/**
 * 📂 Componente per renderizzare una singola sezione del menu
 */
function MenuSection({ 
  section, 
  collapsed, 
  currentPath 
}: { 
  section: MenuSection
  collapsed: boolean
  currentPath: string
}) {
  return (
    <div className="space-y-2">
      {/* Titolo sezione */}
      {!collapsed && (
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide px-3">
          {section.title}
        </h3>
      )}

      {/* Menu items */}
      <div className="space-y-1">
        {section.items.map((item, itemIndex) => (
          <MenuItem
            key={itemIndex}
            item={item}
            collapsed={collapsed}
            isActive={currentPath?.startsWith(item.href) || false}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * 🔗 Componente per renderizzare un singolo menu item
 */
function MenuItem({ 
  item, 
  collapsed, 
  isActive 
}: { 
  item: MenuItem
  collapsed: boolean
  isActive: boolean
}) {
  const IconComponent = item.icon

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all relative group",
        "text-muted-foreground hover:text-foreground hover:bg-muted duration-200",
        isActive && "text-foreground bg-muted font-semibold",
        collapsed && "justify-center"
      )}
      title={collapsed ? `${item.title}${item.description ? ` - ${item.description}` : ''}` : undefined}
    >
      {/* Indicatore attivo */}
      {isActive && !collapsed && (
        <span className="absolute left-0 top-0 h-full w-1 bg-primary rounded-r-md" />
      )}

      {/* Icona */}
      {IconComponent && (
        <IconComponent className={cn(
          "h-4 w-4 flex-shrink-0",
          isActive && "text-primary"
        )} />
      )}

      {/* Testo (nascosto quando collassata) */}
      {!collapsed && (
        <span className="flex-1 truncate">
          {item.title}
        </span>
      )}

      {/* Dot indicator per sidebar collassata */}
      {collapsed && isActive && (
        <span className="absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-primary rounded-full" />
      )}
    </Link>
  )
}

/**
 * 💀 Componente skeleton per loading
 */
function SidebarSkeleton({ collapsed }: { collapsed: boolean }) {
  return (
    <aside className={cn(
      "fixed top-[64px] z-30 h-[calc(100vh-64px)] shrink-0 border-r bg-background",
      "hidden md:sticky md:block",
      collapsed ? "w-16" : "w-64"
    )}>
      <div className="h-full py-6 px-6">
        <div className="animate-pulse space-y-6">
          {/* Header skeleton */}
          {!collapsed && (
            <div className="h-16 bg-muted rounded-lg" />
          )}
          
          {/* Menu sections skeleton */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              {!collapsed && <div className="h-4 bg-muted rounded w-20" />}
              <div className="space-y-1">
                {Array.from({ length: 2 }).map((_, j) => (
                  <div key={j} className={cn(
                    "h-8 bg-muted rounded",
                    collapsed ? "mx-2" : ""
                  )} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}

/**
 * 🚫 Componente quando non ci sono menu disponibili
 */
function EmptyMenu({ collapsed, role }: { collapsed: boolean, role: string | null }) {
  if (collapsed) {
    return (
      <div className="flex justify-center">
        <UserCog className="h-6 w-6 text-muted-foreground opacity-50" />
      </div>
    )
  }

  return (
    <div className="text-center text-muted-foreground text-sm py-8">
      <UserCog className="h-8 w-8 mx-auto mb-2 opacity-50" />
      <p className="font-medium">Nessuna funzionalità disponibile</p>
      <p>per il ruolo: <span className="font-mono text-xs">{role || 'non definito'}</span></p>
      <p className="text-xs mt-2 text-destructive">
        Contatta l'amministratore per configurare i permessi
      </p>
    </div>
  )
} 