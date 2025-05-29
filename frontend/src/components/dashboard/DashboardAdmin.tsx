'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Users, 
  Settings, 
  Database, 
  Activity, 
  BarChart3,
  FileText,
  Cog,
  UserCheck,
  Server,
  AlertTriangle,
  Clock
} from 'lucide-react'
import Link from 'next/link'
import { KPIBox } from './KPIBox'
import { ODLHistoryTable } from './ODLHistoryTable'
import { DashboardShortcuts } from './DashboardShortcuts'
import { useDashboardKPI } from '@/hooks/useDashboardKPI'

/**
 * Dashboard dedicata agli Amministratori
 * 
 * Fornisce accesso completo a tutte le funzionalità del sistema:
 * - Gestione utenti e ruoli
 * - Configurazioni di sistema
 * - Monitoraggio e statistiche
 * - Gestione database
 */
export default function DashboardAdmin() {
  const { data: kpiData, loading: kpiLoading, error: kpiError, refresh: refreshKPI } = useDashboardKPI()

  // Sezioni principali per l'admin
  const adminSections = [
    {
      title: 'Gestione Utenti',
      description: 'Amministra utenti, ruoli e permessi',
      icon: Users,
      color: 'bg-blue-500',
      href: '/dashboard/users',
      actions: ['Crea utente', 'Gestisci ruoli', 'Permessi']
    },
    {
      title: 'Configurazioni Sistema',
      description: 'Impostazioni globali e configurazioni avanzate',
      icon: Settings,
      color: 'bg-purple-500',
      href: '/dashboard/impostazioni',
      actions: ['Parametri globali', 'Configurazioni', 'Backup']
    },
    {
      title: 'Monitoraggio Sistema',
      description: 'Stato del sistema e performance',
      icon: Activity,
      color: 'bg-green-500',
      href: '/dashboard/monitoring',
      actions: ['Stato server', 'Performance', 'Log sistema']
    },
    {
      title: 'Database Management',
      description: 'Gestione database e manutenzione',
      icon: Database,
      color: 'bg-orange-500',
      href: '/dashboard/database',
      actions: ['Backup DB', 'Manutenzione', 'Query']
    },
    {
      title: 'Reports Avanzati',
      description: 'Statistiche complete e analytics',
      icon: BarChart3,
      color: 'bg-indigo-500',
      href: '/dashboard/reports',
      actions: ['Analytics', 'Export dati', 'Dashboard custom']
    },
    {
      title: 'Audit & Logs',
      description: 'Tracciamento attività e sicurezza',
      icon: FileText,
      color: 'bg-red-500',
      href: '/dashboard/audit',
      actions: ['Log accessi', 'Audit trail', 'Sicurezza']
    }
  ]

  // KPI reali per l'admin
  const getAdminKPIMetrics = (): Array<{
    label: string;
    value: string;
    trend: string;
    status: 'success' | 'warning' | 'info' | 'error';
    icon: any;
  }> => {
    if (!kpiData) return []
    
    return [
      { 
        label: 'ODL Totali', 
        value: kpiData.odl_totali.toString(), 
        trend: `${kpiData.odl_finiti} completati`,
        status: 'info',
        icon: FileText
      },
      { 
        label: 'Utilizzo Autoclavi', 
        value: `${kpiData.utilizzo_medio_autoclavi}%`, 
        trend: kpiData.utilizzo_medio_autoclavi > 80 ? 'Alto utilizzo' : 'Capacità disponibile',
        status: kpiData.utilizzo_medio_autoclavi > 90 ? 'warning' : 'success',
        icon: Activity
      },
      { 
        label: 'Efficienza Sistema', 
        value: `${kpiData.efficienza_produzione}%`, 
        trend: kpiData.efficienza_produzione >= 80 ? 'Ottima performance' : 'Da ottimizzare',
        status: kpiData.efficienza_produzione >= 80 ? 'success' : kpiData.efficienza_produzione >= 60 ? 'warning' : 'error',
        icon: BarChart3
      },
      { 
        label: 'ODL in Attesa Cura',
        value: kpiData.odl_attesa_cura.toString(),
        trend: 'Pronti per autoclave',
        status: 'info',
        icon: Clock
      }
    ]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Shield className="h-8 w-8 text-red-500" />
            Dashboard Amministratore
          </h1>
          <p className="text-muted-foreground mt-2">
            Controllo completo del sistema Manta Group - Gestisci utenti, configurazioni e monitoraggio
          </p>
        </div>
        <Badge variant="destructive" className="text-sm">
          <UserCheck className="h-4 w-4 mr-1" />
          ADMIN
        </Badge>
      </div>

      {/* KPI Sistema */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiLoading ? (
          // Skeleton loading per i KPI
          Array.from({ length: 4 }).map((_, index) => (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="animate-pulse bg-gray-200 h-4 w-20 rounded"></div>
                <div className="animate-pulse bg-gray-200 h-4 w-4 rounded"></div>
              </CardHeader>
              <CardContent>
                <div className="animate-pulse bg-gray-200 h-8 w-16 rounded mb-2"></div>
                <div className="animate-pulse bg-gray-200 h-3 w-24 rounded"></div>
              </CardContent>
            </Card>
          ))
        ) : kpiError ? (
          <Card className="col-span-full">
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                <p className="text-sm text-red-600 mb-3">{kpiError}</p>
                <Button variant="outline" size="sm" onClick={refreshKPI}>
                  Riprova
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          getAdminKPIMetrics().map((metric, index) => (
            <KPIBox
              key={index}
              title={metric.label}
              value={metric.value}
              trend={metric.trend}
              status={metric.status}
              icon={metric.icon}
              loading={kpiLoading}
            />
          ))
        )}
      </div>

      {/* Sezioni principali */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {adminSections.map((section, index) => {
          const IconComponent = section.icon
          
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg ${section.color} flex items-center justify-center`}>
                    <IconComponent className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{section.title}</CardTitle>
                    <CardDescription>{section.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  {section.actions.map((action, actionIndex) => (
                    <div key={actionIndex} className="flex items-center text-sm text-muted-foreground">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full mr-2" />
                      {action}
                    </div>
                  ))}
                </div>
                <Link href={section.href}>
                  <Button className="w-full" variant="outline">
                    Accedi
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Azioni rapide */}
      <DashboardShortcuts userRole="admin" />

      {/* Storico ODL */}
      <ODLHistoryTable 
        maxItems={15} 
        showFilters={true} 
        className="mt-6"
      />
    </div>
  )
} 