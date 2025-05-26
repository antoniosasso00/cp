'use client'

import React from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
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
  Timer
} from 'lucide-react'
import { usePathname } from 'next/navigation'
import { useUserRole, type UserRole } from '@/hooks/useUserRole'
import { Button } from '@/components/ui/button'
import { UserMenu } from '@/components/ui/user-menu'

interface SidebarNavItem {
  title: string;
  href: string;
  icon?: React.ReactNode;
  roles?: UserRole[]; // Ruoli che possono vedere questo item
}

interface SidebarSection {
  title: string;
  items: SidebarNavItem[];
  roles?: UserRole[]; // Ruoli che possono vedere questa sezione
}

/**
 * Configurazione della sidebar con controllo dei ruoli
 * Configurazione specifica per ogni ruolo:
 * - ADMIN: vede tutto
 * - RESPONSABILE: vede solo ODL, monitoraggio, schedule
 * - LAMINATORE: vede solo produzione, tool
 * - AUTOCLAVISTA: vede nesting, autoclavi, reports
 */
const sidebarSections: SidebarSection[] = [
  {
    title: "Dashboard",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: <Home className="h-4 w-4" />
        // Visibile a tutti i ruoli
      }
    ]
  },
  {
    title: "Gestione ODL",
    items: [
      {
        title: "ODL",
        href: "/dashboard/shared/odl",
        icon: <ClipboardList className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      },
      {
        title: "Monitoraggio ODL",
        href: "/dashboard/responsabile/odl-monitoring",
        icon: <Activity className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      }
    ],
    roles: ['ADMIN', 'RESPONSABILE']
  },
  {
    title: "Produzione",
    items: [
      {
        title: "Produzione",
        href: "/dashboard/laminatore/produzione",
        icon: <Factory className="h-4 w-4" />,
        roles: ['ADMIN', 'LAMINATORE']
      },
      {
        title: "Tools/Stampi",
        href: "/dashboard/laminatore/tools",
        icon: <Cog className="h-4 w-4" />,
        roles: ['ADMIN', 'LAMINATORE']
      }
    ],
    roles: ['ADMIN', 'LAMINATORE']
  },
  {
    title: "Autoclave",
    items: [
      {
        title: "Produzione",
        href: "/dashboard/autoclavista/produzione",
        icon: <Activity className="h-4 w-4" />,
        roles: ['ADMIN', 'AUTOCLAVISTA']
      },
      {
        title: "Nesting",
        href: "/dashboard/autoclavista/nesting",
        icon: <LayoutGrid className="h-4 w-4" />,
        roles: ['ADMIN', 'AUTOCLAVISTA']
      },
      {
        title: "Autoclavi",
        href: "/dashboard/autoclavista/autoclavi",
        icon: <Flame className="h-4 w-4" />,
        roles: ['ADMIN', 'AUTOCLAVISTA']
      },
      {
        title: "Reports",
        href: "/dashboard/responsabile/reports",
        icon: <FileText className="h-4 w-4" />,
        roles: ['ADMIN', 'AUTOCLAVISTA']
      }
    ],
    roles: ['ADMIN', 'AUTOCLAVISTA']
  },
  {
    title: "Pianificazione",
    items: [
      {
        title: "Schedule",
        href: "/dashboard/autoclavista/schedule",
        icon: <Calendar className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      }
    ],
    roles: ['ADMIN', 'RESPONSABILE']
  },
  {
    title: "Amministrazione",
    items: [
      {
        title: "Catalogo",
        href: "/dashboard/shared/catalog",
        icon: <Package className="h-4 w-4" />,
        roles: ['ADMIN']
      },
      {
        title: "Parti",
        href: "/dashboard/laminatore/parts",
        icon: <Wrench className="h-4 w-4" />,
        roles: ['ADMIN']
      },
      {
        title: "Cicli Cura",
        href: "/dashboard/autoclavista/cicli-cura",
        icon: <Clock className="h-4 w-4" />,
        roles: ['ADMIN']
      },
      {
        title: "Statistiche",
        href: "/dashboard/responsabile/statistiche",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: ['ADMIN']
      },
      {
        title: "Tempi & Performance",
        href: "/dashboard/laminatore/tempi",
        icon: <Timer className="h-4 w-4" />,
        roles: ['ADMIN']
      },

    ],
    roles: ['ADMIN']
  }
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const activeClass = "text-foreground bg-muted";
  const { role, clearRole } = useUserRole();

  /**
   * Filtra gli item della sidebar in base al ruolo dell'utente
   */
  const filterItemsByRole = (items: SidebarNavItem[]): SidebarNavItem[] => {
    return items.filter(item => {
      // Se l'item non ha ruoli specificati, è visibile a tutti
      if (!item.roles) return true;
      // Se l'utente non ha ruolo, non mostrare nulla
      if (!role) return false;
      // Mostra l'item se il ruolo dell'utente è incluso
      return item.roles.includes(role);
    });
  };

  /**
   * Filtra le sezioni della sidebar in base al ruolo dell'utente
   */
  const filterSectionsByRole = (sections: SidebarSection[]): SidebarSection[] => {
    return sections
      .map(section => ({
        ...section,
        items: filterItemsByRole(section.items)
      }))
      .filter(section => {
        // Se la sezione non ha ruoli specificati, è visibile a tutti
        if (!section.roles) return section.items.length > 0;
        // Se l'utente non ha ruolo, non mostrare nulla
        if (!role) return false;
        // Mostra la sezione se il ruolo dell'utente è incluso E ha almeno un item
        return section.roles.includes(role) && section.items.length > 0;
      });
  };



  const filteredSections = filterSectionsByRole(sidebarSections);

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 w-full border-b bg-background">
        <div className="flex h-16 items-center px-4 md:px-6">
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <span className="text-primary text-xl">Manta Group</span>
          </Link>
          <nav className="ml-auto flex items-center gap-4">
            {/* Indicatore ruolo corrente */}
            {role && (
              <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                <UserCog className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium text-primary">
                  {role}
                </span>
              </div>
            )}
            
            {/* Menu utente con dropdown */}
            <UserMenu />
          </nav>
        </div>
        <div className="flex h-10 items-center px-4 text-sm text-muted-foreground md:px-6">
          <nav className="flex items-center gap-2">
            <Link href="/dashboard" className="transition-colors hover:text-foreground">
              Dashboard
            </Link>
          </nav>
        </div>
      </header>
      
      <div className="flex-1 items-start md:grid md:grid-cols-[220px_1fr] lg:grid-cols-[240px_1fr]">
        {/* Sidebar */}
        <aside className="fixed top-[104px] z-30 hidden h-[calc(100vh-104px)] w-full shrink-0 border-r md:sticky md:block">
          <div className="h-full py-6 pl-8 pr-6 lg:pl-10 overflow-y-auto">
            <nav className="space-y-6">
              {filteredSections.map((section, sectionIndex) => (
                <div key={sectionIndex} className="space-y-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {section.title}
                  </h3>
                  <div className="space-y-1">
                    {section.items.map((item, itemIndex) => (
                      <Link
                        key={itemIndex}
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:text-foreground",
                          "text-muted-foreground hover:bg-muted",
                          pathname?.startsWith(item.href) ? activeClass : ""
                        )}
                      >
                        {item.icon}
                        {item.title}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
              
              {/* Messaggio se nessuna sezione è visibile */}
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
        
        {/* Main content */}
        <main className="flex flex-col flex-1 w-full overflow-hidden">
          <div className="p-6">{children}</div>
        </main>
      </div>
    </div>
  )
} 