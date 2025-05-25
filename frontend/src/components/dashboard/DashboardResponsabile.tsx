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
import { NestingStatusCard } from './NestingStatusCard'

/**
 * Componente per visualizzare gli ODL in attesa di nesting
 */
function ODLPendingNestingCard() {
  const [odlPending, setOdlPending] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchODLPending = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await odlApi.getPendingNesting()
      setOdlPending(data)
    } catch (err) {
      console.error('Errore nel caricamento ODL in attesa di nesting:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchODLPending()
  }, [])

  const handleRefresh = () => {
    fetchODLPending()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            ODL in Attesa Nesting
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <CardDescription>
          ODL pronti per essere nidificati nelle autoclavi
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Caricamento...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-600 mb-3">{error}</p>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              Riprova
            </Button>
          </div>
        ) : odlPending.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              Nessun ODL in attesa di nesting
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Tutti gli ODL sono stati processati
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium">
                {odlPending.length} ODL in attesa
              </span>
              <Badge variant="secondary" className="text-xs">
                Attesa Cura
              </Badge>
            </div>
            
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {odlPending.map((odl) => (
                <div
                  key={odl.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">ODL #{odl.id}</span>
                      <Badge variant="outline" className="text-xs">
                        P{odl.priorita}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {odl.parte.part_number} - {odl.parte.descrizione_breve}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Tool: {odl.tool.part_number_tool}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">
                      {new Date(odl.created_at).toLocaleDateString('it-IT')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="pt-3 border-t">
              <Link href="/dashboard/nesting">
                <Button className="w-full" variant="outline" size="sm">
                  <Package className="h-4 w-4 mr-2" />
                  Gestisci Nesting
                </Button>
              </Link>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Dashboard dedicata ai Responsabili
 * 
 * Fornisce strumenti per la supervisione della produzione:
 * - Gestione ODL e produzione
 * - Supervisione operazioni
 * - Reports e statistiche
 * - Pianificazione attività
 */
export default function DashboardResponsabile() {
  const [odlPendingCount, setOdlPendingCount] = useState<number>(0)

  // Fetch del conteggio ODL in attesa di nesting per le metriche
  useEffect(() => {
    const fetchOdlPendingCount = async () => {
      try {
        const data = await odlApi.getPendingNesting()
        setOdlPendingCount(data.length)
      } catch (err) {
        console.error('Errore nel caricamento conteggio ODL:', err)
      }
    }
    
    fetchOdlPendingCount()
  }, [])

  // Sezioni principali per il responsabile
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

  // Metriche chiave per il responsabile
  const keyMetrics = [
    { 
      label: 'ODL Attivi', 
      value: '18', 
      trend: '+3 oggi',
      status: 'success',
      icon: ClipboardList
    },
    { 
      label: 'In Attesa Nesting', 
      value: odlPendingCount.toString(), 
      trend: odlPendingCount > 0 ? 'Pronti per nesting' : 'Tutti processati',
      status: odlPendingCount > 5 ? 'warning' : odlPendingCount > 0 ? 'info' : 'success',
      icon: Package
    },
    { 
      label: 'Efficienza Media', 
      value: '87%', 
      trend: '+5% questa settimana',
      status: 'success',
      icon: TrendingUp
    },
    { 
      label: 'Completati Oggi', 
      value: '12', 
      trend: 'Target: 15',
      status: 'info',
      icon: Target
    }
  ]

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
            Dashboard Responsabile
          </h1>
          <p className="text-muted-foreground mt-2">
            Supervisione produzione e gestione operativa - Monitora performance e coordina il team
          </p>
        </div>
        <Badge variant="default" className="text-sm bg-blue-500">
          <Users className="h-4 w-4 mr-1" />
          RESPONSABILE
        </Badge>
      </div>

      {/* Metriche chiave */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {keyMetrics.map((metric, index) => {
          const IconComponent = metric.icon
          return (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
                <IconComponent className={`h-4 w-4 ${getStatusColor(metric.status)}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <p className={`text-xs ${getStatusColor(metric.status)}`}>{metric.trend}</p>
              </CardContent>
            </Card>
          )
        })}
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
          {/* Gestione Nesting */}
          <NestingStatusCard />
          
          {/* ODL in attesa di nesting */}
          <ODLPendingNestingCard />

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
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Azioni Rapide
              </CardTitle>
              <CardDescription>
                Accesso diretto alle funzioni principali
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full" variant="outline" size="sm">
                <ClipboardList className="h-4 w-4 mr-2" />
                Nuovo ODL
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <Calendar className="h-4 w-4 mr-2" />
                Pianifica Attività
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <BarChart3 className="h-4 w-4 mr-2" />
                Report Giornaliero
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <Users className="h-4 w-4 mr-2" />
                Assegna Team
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 