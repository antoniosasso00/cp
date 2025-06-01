import React from 'react'
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
  ScrollText,
  MonitorSpeaker,
  Users,
  Database
} from 'lucide-react'

export interface MenuItem {
  title: string
  href: string
  icon?: any
  description?: string
}

export interface MenuSection {
  title: string
  items: MenuItem[]
}

/**
 * 🎯 CONFIGURAZIONE MENU PER RUOLI
 * 
 * ORDINE SPECIFICATO:
 * - Admin: Dashboard • Gestione ODL • Clean-Room • Curing • Planning • Analytics • System
 * - Responsabile: Dashboard • ODL • Planning • Analytics  
 * - Laminatore: ODL (solo Clean-Room) • Laminazione Board
 * - Autoclavista: Batch & Nesting • Autoclavi • Monitoraggio Curing
 */

export const menus = {
  // 👑 ADMIN - Menu completo (7 sezioni)
  admin: [
    {
      title: "Dashboard",
      items: [
        {
          title: "Dashboard",
          href: "/dashboard",
          icon: Home,
          description: "Dashboard principale del sistema"
        }
      ]
    },
    {
      title: "Gestione ODL", 
      items: [
        {
          title: "ODL",
          href: "/dashboard/shared/odl",
          icon: ClipboardList,
          description: "Gestione ordini di lavoro"
        },
        {
          title: "Monitoraggio ODL",
          href: "/dashboard/management/odl-monitoring", 
          icon: Activity,
          description: "Monitoraggio stato ODL"
        }
      ]
    },
    {
      title: "Clean-Room",
      items: [
        {
          title: "Laminazione",
          href: "/dashboard/clean-room/produzione",
          icon: Factory,
          description: "Processo di laminazione"
        },
        {
          title: "Parti",
          href: "/dashboard/clean-room/parts",
          icon: Wrench,
          description: "Gestione parti"
        }
      ]
    },
    {
      title: "Curing",
      items: [
        {
          title: "🎯 Nesting & Batch",
          href: "/dashboard/curing/nesting",
          icon: LayoutGrid,
          description: "Ottimizzazione nesting e gestione batch"
        },
        {
          title: "📦 Gestione Batch", 
          href: "/dashboard/curing/batch-monitoring",
          icon: Package,
          description: "Monitoraggio batch di produzione"
        },
        {
          title: "🔄 Monitoraggio ODL",
          href: "/dashboard/curing/produzione",
          icon: Activity,
          description: "Monitoraggio ODL in curing"
        },
        {
          title: "🔥 Autoclavi",
          href: "/dashboard/curing/autoclavi", 
          icon: Flame,
          description: "Gestione autoclavi"
        },
        {
          title: "⚙️ Cicli di Cura",
          href: "/dashboard/curing/cicli-cura",
          icon: Clock,
          description: "Configurazione cicli di cura"
        }
      ]
    },
    {
      title: "Planning",
      items: [
        {
          title: "Schedule",
          href: "/dashboard/curing/schedule",
          icon: Calendar,
          description: "Pianificazione produzione"
        },
        {
          title: "Catalogo",
          href: "/dashboard/shared/catalog",
          icon: Package,
          description: "Catalogo prodotti"
        },
        {
          title: "Tools",
          href: "/dashboard/management/tools",
          icon: Cog,
          description: "Gestione utensili"
        }
      ]
    },
    {
      title: "Analytics",
      items: [
        {
          title: "📊 Statistiche",
          href: "/dashboard/curing/statistics",
          icon: TrendingUp,
          description: "Statistiche di produzione"
        },
        {
          title: "📋 Reports",
          href: "/dashboard/management/reports",
          icon: FileText,
          description: "Report e documenti"
        },
        {
          title: "Dashboard Monitoraggio",
          href: "/dashboard/monitoraggio",
          icon: BarChart3,
          description: "Dashboard di monitoraggio"
        },
        {
          title: "Tempo Fasi",
          href: "/dashboard/management/tempo-fasi",
          icon: Timer,
          description: "Analisi tempi di produzione"
        }
      ]
    },
    {
      title: "System",
      items: [
        {
          title: "System Logs",
          href: "/dashboard/admin/system-logs",
          icon: ScrollText,
          description: "Log di sistema"
        },
        {
          title: "Configurazioni",
          href: "/dashboard/admin/settings",
          icon: Settings,
          description: "Impostazioni sistema"
        }
      ]
    }
  ] as MenuSection[],

  // 👨‍💼 RESPONSABILE - Menu gestionale (4 sezioni)
  responsabile: [
    {
      title: "Dashboard",
      items: [
        {
          title: "Dashboard",
          href: "/dashboard",
          icon: Home,
          description: "Dashboard principale"
        }
      ]
    },
    {
      title: "ODL",
      items: [
        {
          title: "ODL",
          href: "/dashboard/shared/odl",
          icon: ClipboardList,
          description: "Gestione ordini di lavoro"
        },
        {
          title: "Monitoraggio ODL",
          href: "/dashboard/management/odl-monitoring",
          icon: Activity,
          description: "Monitoraggio stato ODL"
        }
      ]
    },
    {
      title: "Planning",
      items: [
        {
          title: "Schedule",
          href: "/dashboard/curing/schedule",
          icon: Calendar,
          description: "Pianificazione produzione"
        },
        {
          title: "Catalogo",
          href: "/dashboard/shared/catalog",
          icon: Package,
          description: "Catalogo prodotti"
        },
        {
          title: "Tools",
          href: "/dashboard/management/tools",
          icon: Cog,
          description: "Gestione utensili"
        }
      ]
    },
    {
      title: "Analytics",
      items: [
        {
          title: "📊 Statistiche",
          href: "/dashboard/curing/statistics",
          icon: TrendingUp,
          description: "Statistiche di produzione"
        },
        {
          title: "📋 Reports",
          href: "/dashboard/management/reports",
          icon: FileText,
          description: "Report e documenti"
        },
        {
          title: "Dashboard Monitoraggio",
          href: "/dashboard/monitoraggio",
          icon: BarChart3,
          description: "Dashboard di monitoraggio"
        },
        {
          title: "Tempo Fasi",
          href: "/dashboard/management/tempo-fasi",
          icon: Timer,
          description: "Analisi tempi di produzione"
        }
      ]
    }
  ] as MenuSection[],

  // 🏭 LAMINATORE - Menu operativo clean-room (2 sezioni)
  laminatore: [
    {
      title: "ODL",
      items: [
        {
          title: "ODL Clean-Room",
          href: "/dashboard/clean-room/produzione",
          icon: Factory,
          description: "ODL specifici per Clean-Room"
        }
      ]
    },
    {
      title: "Laminazione Board",
      items: [
        {
          title: "Laminazione",
          href: "/dashboard/clean-room/produzione",
          icon: Factory,
          description: "Processo di laminazione"
        },
        {
          title: "Parti",
          href: "/dashboard/clean-room/parts",
          icon: Wrench,
          description: "Gestione parti"
        }
      ]
    }
  ] as MenuSection[],

  // 🔥 AUTOCLAVISTA - Menu operativo curing (3 sezioni)
  autoclavista: [
    {
      title: "Batch & Nesting",
      items: [
        {
          title: "🎯 Nesting & Batch",
          href: "/dashboard/curing/nesting",
          icon: LayoutGrid,
          description: "Ottimizzazione nesting e gestione batch"
        },
        {
          title: "📦 Gestione Batch",
          href: "/dashboard/curing/batch-monitoring",
          icon: Package,
          description: "Monitoraggio batch di produzione"
        }
      ]
    },
    {
      title: "Autoclavi",
      items: [
        {
          title: "🔥 Autoclavi",
          href: "/dashboard/curing/autoclavi",
          icon: Flame,
          description: "Gestione autoclavi"
        },
        {
          title: "⚙️ Cicli di Cura",
          href: "/dashboard/curing/cicli-cura",
          icon: Clock,
          description: "Configurazione cicli di cura"
        }
      ]
    },
    {
      title: "Monitoraggio Curing",
      items: [
        {
          title: "🔄 Monitoraggio ODL",
          href: "/dashboard/curing/produzione",
          icon: Activity,
          description: "Monitoraggio ODL in curing"
        },
        {
          title: "📊 Statistiche",
          href: "/dashboard/curing/statistics",
          icon: TrendingUp,
          description: "Statistiche di curing"
        }
      ]
    }
  ] as MenuSection[]
}

/**
 * 🔧 UTILITY: Ottieni menu per ruolo
 */
export function getMenuForRole(role: string | null): MenuSection[] {
  if (!role) return []
  
  const normalizedRole = role.toLowerCase()
  
  // Mappatura ruoli
  switch (normalizedRole) {
    case 'admin':
    case 'administrator':
      return menus.admin
    case 'responsabile':
    case 'management': 
      return menus.responsabile
    case 'laminatore':
    case 'clean room':
      return menus.laminatore
    case 'autoclavista':
    case 'curing':
      return menus.autoclavista
    default:
      console.warn(`Ruolo non riconosciuto: ${role}`)
      return []
  }
}

/**
 * 🎯 UTILITY: Verifica se utente ha accesso a una sezione
 */
export function hasAccessToSection(role: string | null, sectionTitle: string): boolean {
  const menu = getMenuForRole(role)
  return menu.some(section => section.title === sectionTitle)
}

/**
 * 📊 UTILITY: Statistiche menu per debugging
 */
export function getMenuStats() {
  return {
    admin: {
      sections: menus.admin.length,
      items: menus.admin.reduce((acc, section) => acc + section.items.length, 0)
    },
    responsabile: {
      sections: menus.responsabile.length,
      items: menus.responsabile.reduce((acc, section) => acc + section.items.length, 0)
    },
    laminatore: {
      sections: menus.laminatore.length,
      items: menus.laminatore.reduce((acc, section) => acc + section.items.length, 0)
    },
    autoclavista: {
      sections: menus.autoclavista.length,
      items: menus.autoclavista.reduce((acc, section) => acc + section.items.length, 0)
    }
  }
} 