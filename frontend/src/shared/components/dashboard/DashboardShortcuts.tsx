'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Plus, 
  ClipboardList, 
  Wrench, 
  Thermometer, 
  Package, 
  BarChart3,
  FileText,
  Calendar,
  Settings,
  Users
} from 'lucide-react'
import Link from 'next/link'

interface ShortcutItem {
  title: string
  description: string
  icon: React.ComponentType<any>
  href: string
  color: string
  available: boolean
}

interface DashboardShortcutsProps {
  userRole: 'admin' | 'management'
  className?: string
}

export function DashboardShortcuts({ userRole, className = "" }: DashboardShortcutsProps) {
  // Scorciatoie per il management
  const managementShortcuts: ShortcutItem[] = [
    {
      title: 'Nuovo ODL',
      description: 'Crea un nuovo ordine di lavorazione',
      icon: Plus,
      href: '/dashboard/shared/odl/create',
      color: 'bg-blue-500 hover:bg-blue-600',
      available: true
    },
    {
      title: 'Gestisci ODL',
      description: 'Visualizza e gestisci tutti gli ODL',
      icon: ClipboardList,
      href: '/dashboard/shared/odl',
      color: 'bg-green-500 hover:bg-green-600',
      available: true
    },
    {
      title: 'Nesting Attivi',
      description: 'Visualizza i nesting in corso',
      icon: Package,
      href: '/nesting',
      color: 'bg-purple-500 hover:bg-purple-600',
      available: true
    },
    {
      title: 'Reports',
      description: 'Genera report di produzione',
      icon: BarChart3,
      href: '/dashboard/management/reports',
      color: 'bg-orange-500 hover:bg-orange-600',
      available: true
    },
    {
      title: 'Dashboard Monitoraggio',
      description: 'Analisi complete e statistiche',
      icon: FileText,
      href: '/dashboard/monitoraggio',
      color: 'bg-indigo-500 hover:bg-indigo-600',
      available: true
    },
    {
      title: 'Catalogo Parti',
      description: 'Gestisci il catalogo delle parti',
      icon: Wrench,
      href: '/dashboard/shared/catalog',
      color: 'bg-teal-500 hover:bg-teal-600',
      available: true
    }
  ]

  // Scorciatoie per l'admin
  const adminShortcuts: ShortcutItem[] = [
    {
      title: 'Nuovo ODL',
      description: 'Crea un nuovo ordine di lavorazione',
      icon: Plus,
      href: '/dashboard/shared/odl/create',
      color: 'bg-blue-500 hover:bg-blue-600',
      available: true
    },
    {
      title: 'Gestisci Utenti',
      description: 'Amministra utenti e permessi',
      icon: Users,
      href: '/dashboard/admin/users',
      color: 'bg-red-500 hover:bg-red-600',
      available: false // Non ancora implementato
    },
    {
      title: 'Impostazioni',
      description: 'Configurazioni di sistema',
      icon: Settings,
      href: '/dashboard/admin/impostazioni',
      color: 'bg-gray-500 hover:bg-gray-600',
      available: true
    },
    {
      title: 'Catalogo Parti',
      description: 'Gestisci il catalogo delle parti',
      icon: Wrench,
      href: '/dashboard/shared/catalog',
      color: 'bg-teal-500 hover:bg-teal-600',
      available: true
    },
    {
      title: 'Nesting Attivi',
      description: 'Visualizza i nesting in corso',
      icon: Package,
      href: '/nesting',
      color: 'bg-purple-500 hover:bg-purple-600',
      available: true
    },
    {
      title: 'Log Sistema',
      description: 'Visualizza log di sistema',
      icon: FileText,
      href: '/dashboard/admin/logs',
      color: 'bg-yellow-500 hover:bg-yellow-600',
      available: true
    }
  ]

  const shortcuts = userRole === 'admin' ? adminShortcuts : managementShortcuts

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Azioni Rapide
        </CardTitle>
        <CardDescription>
          Accesso diretto alle funzioni principali
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-2">
          {shortcuts.map((shortcut, index) => {
            const IconComponent = shortcut.icon
            
            if (!shortcut.available) {
              return (
                <div
                  key={index}
                  className="p-3 rounded-lg border border-dashed border-gray-300 bg-gray-50 opacity-60"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-gray-400 flex items-center justify-center">
                      <IconComponent className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-500">
                        {shortcut.title}
                      </div>
                      <div className="text-xs text-gray-400">
                        In sviluppo
                      </div>
                    </div>
                  </div>
                </div>
              )
            }
            
            return (
              <Link key={index} href={shortcut.href}>
                <div className="p-3 rounded-lg border hover:shadow-md transition-all duration-200 hover:border-primary/50 cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded ${shortcut.color} flex items-center justify-center transition-colors`}>
                      <IconComponent className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium group-hover:text-primary transition-colors">
                        {shortcut.title}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {shortcut.description}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
        
        {/* Pulsante per visualizzare tutte le funzioni */}
        <div className="mt-4 pt-4 border-t">
          <Link href="/dashboard">
            <Button variant="outline" className="w-full" size="sm">
              <ClipboardList className="h-4 w-4 mr-2" />
              Visualizza tutte le funzioni
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
} 