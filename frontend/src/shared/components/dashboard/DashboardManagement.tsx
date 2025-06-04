'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  ClipboardList, 
  BarChart3, 
  Calendar,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Factory,
  Target,
  Package,
  Loader2,
  RefreshCw
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { odlApi, type ODLResponse } from '@/lib/api'
import { OdlProgressWrapper } from '@/components/ui/OdlProgressWrapper'
import { KPIBox } from './KPIBox'
import { ODLHistoryTable } from './ODLHistoryTable'
import { DashboardShortcuts } from './DashboardShortcuts'
import { useDashboardKPI } from '@/hooks/useDashboardKPI'

/**
 * Dashboard dedicata ai Responsabili
 * 
 * Fornisce strumenti per la supervisione della produzione:
 * - Gestione ODL e produzione
 * - Supervisione operazioni
 * - Reports e statistiche
 * - Pianificazione attività
 */
export default function DashboardManagement() {
  const { data: kpiData, loading: kpiLoading, error: kpiError, refresh: refreshKPI } = useDashboardKPI()

  // Sezioni principali per il management
  const responsabileSections = [
    {
      title: 'Gestione ODL',
      description: 'Supervisiona e gestisci gli ordini di lavoro',
      icon: ClipboardList,
      color: 'bg-blue-500',
      href: '/dashboard/odl',
      actions: ['Crea ODL', 'Assegna priorità', 'Monitora stato']
    },
    {
      title: 'Pianificazione Produzione',
      description: 'Organizza e pianifica le attività produttive',
      icon: Calendar,
      color: 'bg-green-500',
      href: '/dashboard/schedule',
      actions: ['Scheduling', 'Risorse', 'Timeline']
    },
    {
      title: 'Reports & Analytics',
      description: 'Analisi performance e statistiche produzione',
      icon: BarChart3,
      color: 'bg-purple-500',
      href: '/dashboard/reports',
      actions: ['KPI produzione', 'Efficienza', 'Trend analysis']
    },
    {
      title: 'Supervisione Team',
      description: 'Monitora attività del team e assegnazioni',
      icon: Users,
      color: 'bg-orange-500',
      href: '/dashboard/team',
      actions: ['Assegnazioni', 'Performance', 'Workload']
    },
    {
      title: 'Controllo Qualità',
      description: 'Supervisiona standard qualitativi e controlli',
      icon: CheckCircle,
      color: 'bg-indigo-500',
      href: '/dashboard/quality',
      actions: ['Standard QC', 'Non conformità', 'Audit']
    },
    {
      title: 'Gestione Risorse',
      description: 'Ottimizza utilizzo di strumenti e materiali',
      icon: Factory,
      color: 'bg-teal-500',
      href: '/dashboard/tools',
      actions: ['Disponibilità', 'Manutenzione', 'Allocazione']
    }
  ]

  // Metriche chiave reali per il management
  const getKPIMetrics = (): Array<{
    label: string;
    value: string;
    trend: string;
    status: 'success' | 'warning' | 'info' | 'error';
    icon: any;
  }> => {
    if (!kpiData) return []
    
    // Funzione helper per determinare lo status dell'attesa cura
    const getAttesaCuraStatus = (count: number): 'success' | 'warning' | 'info' | 'error' => {
      if (count === 0) return 'success'
      if (count <= 5) return 'info'
      if (count <= 10) return 'warning'
      return 'error'
    }
    
    // Funzione helper per determinare lo status dell'efficienza
    const getEfficienzaStatus = (efficienza: number): 'success' | 'warning' | 'info' | 'error' => {
      if (efficienza >= 90) return 'success'
      if (efficienza >= 80) return 'info'
      if (efficienza >= 70) return 'warning'
      return 'error'
    }
    
    return [
      { 
        label: 'ODL Totali', 
        value: kpiData.odl_totali.toString(), 
        trend: `${kpiData.odl_finiti} completati`,
        status: 'info',
        icon: ClipboardList
      },
      { 
        label: 'In Attesa Cura', 
        value: kpiData.odl_attesa_cura.toString(), 
        trend: kpiData.odl_attesa_cura > 0 ? 'Pronti per cura' : 'Tutti processati',
        status: getAttesaCuraStatus(kpiData.odl_attesa_cura),
        icon: Package
      },
      { 
        label: 'Efficienza Produzione', 
        value: `${kpiData.efficienza_produzione}%`, 
        trend: kpiData.efficienza_produzione >= 80 ? 'Ottima performance' : 'Da migliorare',
        status: getEfficienzaStatus(kpiData.efficienza_produzione),
        icon: TrendingUp
      },
      { 
        label: 'Completati Oggi', 
        value: kpiData.completati_oggi.toString(), 
        trend: 'Aggiornato in tempo reale',
        status: 'success',
        icon: Target
      }
    ]
  }

  // Priorità e alert
  const alerts = [
    {
      type: 'urgent',
      message: 'ODL #1247 in ritardo - Richiede attenzione',
      time: '10 min fa'
    },
    {
      type: 'info',
      message: 'Nuova richiesta di materiali per ODL #1250',
      time: '25 min fa'
    },
    {
      type: 'success',
      message: 'ODL #1245 completato con successo',
      time: '1 ora fa'
    }
  ]

  const getStatusColor = (status: string) => {
    const colors = {
      success: 'text-green-600',
      warning: 'text-yellow-600',
      info: 'text-blue-600',
      urgent: 'text-red-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getAlertVariant = (type: string) => {
    const variants = {
      urgent: 'destructive',
      warning: 'secondary',
      info: 'outline',
      success: 'default'
    }
    return variants[type as keyof typeof variants] || 'outline'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Users className="h-8 w-8 text-blue-500" />
            Dashboard Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Supervisione produzione e gestione operativa - Monitora performance e coordina il team
          </p>
        </div>
        <Badge variant="default" className="text-sm bg-blue-500">
          <Users className="h-4 w-4 mr-1" />
          Management
        </Badge>
      </div>

      {/* Metriche chiave */}
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
          getKPIMetrics().map((metric, index) => (
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

      {/* Layout principale */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Sezioni principali */}
        <div className="lg:col-span-2 grid gap-6 md:grid-cols-2">
          {responsabileSections.map((section, index) => {
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

        {/* Sidebar con ODL in attesa e alert */}
        <div className="space-y-6">
          {/* Alert e notifiche */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Alert & Notifiche
              </CardTitle>
              <CardDescription>
                Aggiornamenti in tempo reale
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map((alert, index) => (
                <div key={index} className="flex items-start gap-3 p-3 rounded-lg border">
                  <Badge variant={getAlertVariant(alert.type) as any} className="mt-0.5">
                    {alert.type}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                      <Clock className="h-3 w-3" />
                      {alert.time}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Azioni rapide */}
          <DashboardShortcuts userRole="management" />
        </div>
      </div>

      {/* Storico ODL */}
      <ODLHistoryTable 
        maxItems={15} 
        showFilters={true} 
        className="mt-6"
      />
    </div>
  )
} 