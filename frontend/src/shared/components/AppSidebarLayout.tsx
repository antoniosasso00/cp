'use client'

import React from 'react'
import Link from 'next/link'
import { cn } from '@/shared/lib/utils'
import {
  Clock,
  BarChart3,
  LayoutGrid,
  Calendar,
  FileText,
  Settings,
  Home,
  Package,
  Wrench,
  ClipboardList,
  Factory,
  Flame,
  TrendingUp,
  Cog,
  UserCog,
  Activity,
  Timer,
  ScrollText
} from 'lucide-react'
import { usePathname } from 'next/navigation'
import { useUserRole } from '@/shared/hooks/useUserRole'
import type { UserRole } from '@/shared/types'
import { UserMenu } from '@/shared/components/ui/user-menu'
import { ThemeToggle } from '@/shared/components/ui/theme-toggle'

interface SidebarNavItem {
  title: string;
  href: string;
  icon?: React.ReactNode;
  roles?: UserRole[];
}

interface SidebarSection {
  title: string;
  items: SidebarNavItem[];
  roles?: UserRole[];
}

const sidebarSections: SidebarSection[] = [
  {
    title: "Dashboard",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: <Home className="h-4 w-4" />
      }
    ]
  },
  {
    title: "Gestione ODL",
    items: [
      {
        title: "ODL",
        href: "/odl",
        icon: <ClipboardList className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      },

    ],
    roles: ['ADMIN', 'Management']
  },
  {
    title: "CLEAN ROOM",
    items: [
      {
        title: "Laminazione",
        href: "/dashboard/clean-room/produzione",
        icon: <Factory className="h-4 w-4" />,
        roles: ['ADMIN', 'Clean Room']
      }
    ],
    roles: ['ADMIN', 'Clean Room']
  },
  {
    title: "CURING",
    items: [
      {
        title: "Nesting & Batch",
        href: "/nesting",
        icon: <LayoutGrid className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing']
      },
      {
        title: "Gestione Batch",
        href: "/dashboard/curing/batch-monitoring",
        icon: <Package className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing']
      },

      {
        title: "Autoclavi",
        href: "/autoclavi",
        icon: <Flame className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing']
      },
      {
        title: "Cicli di Cura",
        href: "/dashboard/curing/cicli-cura",
        icon: <Clock className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing']
      },
      {
        title: "Statistiche",
        href: "/dashboard/curing/statistics",
        icon: <TrendingUp className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing', 'Management']
      },
      {
        title: "Reports",
        href: "/report",
        icon: <FileText className="h-4 w-4" />,
        roles: ['ADMIN', 'Curing']
      }
    ],
    roles: ['ADMIN', 'Curing']
  },
  {
    title: "Pianificazione",
    items: [
      {
        title: "Schedule",
        href: "/schedule",
        icon: <Calendar className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      }
    ],
    roles: ['ADMIN', 'Management']
  },
  {
    title: "Flusso Produttivo",
    items: [
      {
        title: "Catalogo",
        href: "/catalogo",
        icon: <Package className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      },
      {
        title: "Tools",
        href: "/tools",
        icon: <Cog className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      },
      {
        title: "Parti",
        href: "/parti",
        icon: <Wrench className="h-4 w-4" />,
        roles: ['ADMIN']
      }
    ],
    roles: ['ADMIN', 'Management']
  },
  {
    title: "Amministrazione",
    items: [
      {
        title: "Dashboard Monitoraggio",
        href: "/dashboard/monitoraggio",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      },
      {
        title: "Tempo Fasi",
        href: "/tempi",
        icon: <Timer className="h-4 w-4" />,
        roles: ['ADMIN', 'Management']
      },
      {
        title: "System Logs",
        href: "/modules/admin/system-logs",
        icon: <ScrollText className="h-4 w-4" />,
        roles: ['ADMIN']
      }
    ],
    roles: ['ADMIN', 'Management']
  }
]

interface AppSidebarLayoutProps {
  children: React.ReactNode
}

export function AppSidebarLayout({ children }: AppSidebarLayoutProps) {
  const pathname = usePathname()
  const { role } = useUserRole()

  // Pagine dove NON mostrare la sidebar
  const shouldHideSidebar = 
    pathname === '/' || 
    pathname === '/modules/role' || 
    pathname.startsWith('/modules/role') ||
    !role  // Nascondi se non c'è un ruolo selezionato
  
  if (shouldHideSidebar) {
    return <>{children}</>
  }

  const activeClass = "text-foreground bg-muted font-semibold";

  const filterItemsByRole = (items: SidebarNavItem[]) => {
    return items.filter(item => !item.roles || (role && item.roles.includes(role)));
  };

  const filterSectionsByRole = (sections: SidebarSection[]) => {
    return sections
      .map(section => ({
        ...section,
        items: filterItemsByRole(section.items)
      }))
      .filter(section => (!section.roles || (role && section.roles.includes(role))) && section.items.length > 0);
  };

  const filteredSections = filterSectionsByRole(sidebarSections);

  return (
    <div className="flex min-h-screen flex-col">
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
            <ThemeToggle />
            <UserMenu />
          </nav>
        </div>
      </header>

      <div className="flex-1 md:grid md:grid-cols-[240px_1fr]">
        <aside className="fixed top-[64px] z-30 hidden h-[calc(100vh-64px)] w-[240px] shrink-0 border-r bg-background md:sticky md:block transition-all duration-300">
          <div className="h-full py-6 pl-8 pr-4 overflow-y-auto">
            <nav className="space-y-6">
              {filteredSections.map((section, i) => (
                <div key={i} className="space-y-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    {section.title}
                  </h3>
                  <div className="space-y-1">
                    {section.items.map((item, j) => {
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link
                          key={j}
                          href={item.href}
                          className={cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all relative group",
                            "text-muted-foreground hover:text-foreground hover:pl-4 hover:bg-muted duration-200",
                            isActive && activeClass
                          )}
                        >
                          {isActive && <span className="absolute left-0 top-0 h-full w-1 bg-primary rounded-r-md" />}
                          {item.icon}
                          {item.title}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}

              {filteredSections.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-8">
                  <UserCog className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Nessuna funzionalità disponibile</p>
                  <p>per il ruolo corrente</p>
                </div>
              )}
            </nav>
          </div>
        </aside>

        <main className="flex flex-col flex-1 w-full min-w-0 overflow-hidden">
          <div className="flex-1 p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
} 