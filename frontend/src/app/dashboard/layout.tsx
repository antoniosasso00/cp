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
  Activity
} from 'lucide-react'
import { usePathname } from 'next/navigation'
import { useUserRole, type UserRole } from '@/hooks/useUserRole'
import { Button } from '@/components/ui/button'

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
 * Se roles non è specificato, l'item/sezione è visibile a tutti
 */
const sidebarSections: SidebarSection[] = [
  {
    title: "Produzione",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: <Home className="h-4 w-4" />
        // Visibile a tutti i ruoli
      },
      {
        title: "Catalogo",
        href: "/dashboard/catalog",
        icon: <Package className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'LAMINATORE']
      },
      {
        title: "Parti",
        href: "/dashboard/parts",
        icon: <Wrench className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'LAMINATORE']
      },
      {
        title: "ODL",
        href: "/dashboard/odl",
        icon: <ClipboardList className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'LAMINATORE']
      },
      {
        title: "Tools/Stampi",
        href: "/dashboard/tools",
        icon: <Cog className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'LAMINATORE']
      },
      {
        title: "Produzione",
        href: "/dashboard/produzione",
        icon: <Factory className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'LAMINATORE']
      }
    ]
  },
  {
    title: "Autoclave",
    items: [
      {
        title: "Nesting",
        href: "/dashboard/nesting",
        icon: <LayoutGrid className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'AUTOCLAVISTA']
      },
      {
        title: "Autoclavi",
        href: "/dashboard/autoclavi",
        icon: <Flame className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'AUTOCLAVISTA']
      },
      {
        title: "Cicli Cura",
        href: "/dashboard/cicli-cura",
        icon: <Clock className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'AUTOCLAVISTA']
      },
      {
        title: "Scheduling",
        href: "/dashboard/schedule",
        icon: <Calendar className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE', 'AUTOCLAVISTA']
      }
    ]
  },
  {
    title: "Controllo",
    items: [
      {
        title: "Monitoraggio ODL",
        href: "/dashboard/odl/monitoring",
        icon: <Activity className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      },
      {
        title: "Reports",
        href: "/dashboard/reports",
        icon: <FileText className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      },
      {
        title: "Statistiche",
        href: "/dashboard/catalog/statistiche",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: ['ADMIN', 'RESPONSABILE']
      },
      {
        title: "Impostazioni",
        href: "/dashboard/impostazioni",
        icon: <Settings className="h-4 w-4" />,
        roles: ['ADMIN']
      }
    ]
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

  /**
   * Gestisce il cambio ruolo (solo in sviluppo)
   */
  const handleRoleChange = () => {
    clearRole();
    window.location.href = '/select-role';
  };

  const filteredSections = filterSectionsByRole(sidebarSections);

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 w-full border-b bg-background">
        <div className="flex h-16 items-center px-4 md:px-6">
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <span className="text-primary text-xl">CarbonPilot</span>
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
            
            {/* Pulsante cambio ruolo (solo in sviluppo) */}
            {process.env.NODE_ENV !== 'production' && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRoleChange}
                className="text-xs"
              >
                Cambia Ruolo
              </Button>
            )}
            
            <div className="relative inline-block text-left">
              <div>
                <button
                  type="button"
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 w-10"
                >
                  <span className="sr-only">Opzioni utente</span>
                  <span className="h-4 w-4">👤</span>
                </button>
              </div>
            </div>
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