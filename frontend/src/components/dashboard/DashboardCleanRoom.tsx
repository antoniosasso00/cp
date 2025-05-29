'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Wrench, 
  Package, 
  ClipboardCheck, 
  Timer,
  Layers,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Gauge,
  Loader2,
  AlertTriangle,
  RefreshCw
} from 'lucide-react'
import Link from 'next/link'
import { useODLByRole } from '@/hooks/useODLByRole'
import { useDashboardKPI } from '@/hooks/useDashboardKPI'

/**
 * Dashboard dedicata ai Laminatori
 * 
 * Fornisce strumenti specifici per le operazioni di laminazione:
 * - ODL in Preparazione e Laminazione (dati reali)
 * - Cambio stato ODL con pulsanti funzionali
 * - KPI reali di produzione
 * - Azioni rapide per il flusso operativo
 */
export default function DashboardCleanRoom() {
  const { odlList, loading, error, refresh, updateODLStatus } = useODLByRole({ 
    role: 'Clean Room',
    autoRefresh: true,
    refreshInterval: 30000 
  })
  
  const { data: kpiData, loading: kpiLoading } = useDashboardKPI()
  
  const [updatingODL, setUpdatingODL] = useState<number | null>(null)

  // Calcola metriche operative reali
  const getOperativeMetrics = () => {
    const odlInPreparazione = odlList.filter(odl => odl.status === 'Preparazione').length
    const odlInLaminazione = odlList.filter(odl => odl.status === 'Laminazione').length
    const odlTotali = odlList.length
    
    return [
      { 
        label: 'ODL in Preparazione', 
        value: odlInPreparazione.toString(), 
        trend: 'Pronti per laminazione',
        status: odlInPreparazione > 0 ? 'active' : 'success',
        icon: Package
      },
      { 
        label: 'ODL in Laminazione', 
        value: odlInLaminazione.toString(), 
        trend: 'Attualmente in corso',
        status: odlInLaminazione > 0 ? 'active' : 'success',
        icon: Layers
      },
      { 
        label: 'Totale ODL Assegnati', 
        value: odlTotali.toString(), 
        trend: 'Nel tuo flusso',
        status: 'info',
        icon: ClipboardCheck
      },
      { 
        label: 'Efficienza Turno', 
        value: kpiData ? `${kpiData.efficienza_produzione}%` : '--', 
        trend: kpiData && kpiData.efficienza_produzione >= 80 ? 'Ottima performance' : 'Da migliorare',
        status: kpiData && kpiData.efficienza_produzione >= 80 ? 'success' : 'warning',
        icon: Gauge
      }
    ]
  }

  // Gestisce il cambio stato di un ODL
  const handleStatusChange = async (odlId: number, newStatus: string) => {
    try {
      setUpdatingODL(odlId)
      await updateODLStatus(odlId, newStatus)
    } catch (err) {
      console.error('Errore nel cambio stato:', err)
      alert('Errore nel cambio stato. Riprova.')
    } finally {
      setUpdatingODL(null)
    }
  }

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'text-blue-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
      info: 'text-purple-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getODLStatusBadge = (status: string) => {
    const variants = {
      'Preparazione': { variant: 'secondary', label: 'Preparazione', color: 'bg-gray-500' },
      'Laminazione': { variant: 'default', label: 'In Laminazione', color: 'bg-blue-500' }
    }
    return variants[status as keyof typeof variants] || { variant: 'outline', label: status, color: 'bg-gray-500' }
  }

  const getPriorityColor = (priority: number) => {
    if (priority >= 8) return 'text-red-600'
    if (priority >= 5) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getPriorityLabel = (priority: number) => {
    if (priority >= 8) return 'Alta'
    if (priority >= 5) return 'Media'
    return 'Bassa'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Wrench className="h-8 w-8 text-green-500" />
            Dashboard Clean Room
          </h1>
          <p className="text-muted-foreground mt-2">
            Gestione ODL in Preparazione e Laminazione - Controllo flusso operativo
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={refresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Badge variant="default" className="text-sm bg-green-500">
            <Wrench className="h-4 w-4 mr-1" />
            Clean Room
          </Badge>
        </div>
      </div>

      {/* Metriche operative reali */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {getOperativeMetrics().map((metric, index) => {
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
        {/* ODL Attivi - Dati Reali */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Play className="h-5 w-5" />
                    ODL Assegnati
                  </CardTitle>
                  <CardDescription>
                    Ordini di lavoro in Preparazione e Laminazione
                  </CardDescription>
                </div>
                <Badge variant="outline">
                  {odlList.length} ODL
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Caricamento ODL...</span>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-red-600 mb-3">{error}</p>
                  <Button variant="outline" size="sm" onClick={refresh}>
                    Riprova
                  </Button>
                </div>
              ) : odlList.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Nessun ODL assegnato al momento
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {odlList.map((odl) => {
                    const statusInfo = getODLStatusBadge(odl.status)
                    const isUpdating = updatingODL === odl.id
                    
                    return (
                      <div key={odl.id} className="p-4 rounded-lg border space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="font-medium">ODL #{odl.id}</div>
                          <Badge variant={statusInfo.variant as any}>
                            {statusInfo.label}
                          </Badge>
                        </div>
                        
                        <div className="space-y-1 text-sm">
                          <div><strong>Parte:</strong> {odl.parte.part_number}</div>
                          <div className="text-xs text-muted-foreground">
                            {odl.parte.descrizione_breve}
                          </div>
                          <div><strong>Tool:</strong> {odl.tool.part_number_tool}</div>
                          <div className="flex items-center justify-between">
                            <span><strong>Priorità:</strong></span>
                            <span className={`font-medium ${getPriorityColor(odl.priorita)}`}>
                              {getPriorityLabel(odl.priorita)} (P{odl.priorita})
                            </span>
                          </div>
                          <div><strong>Valvole richieste:</strong> {odl.parte.num_valvole_richieste}</div>
                        </div>

                        {/* Pulsanti azione */}
                        <div className="flex gap-2 pt-2">
                          {odl.status === 'Preparazione' && (
                            <Button 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleStatusChange(odl.id, 'Laminazione')}
                              disabled={isUpdating}
                            >
                              {isUpdating ? (
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              ) : (
                                <Play className="h-3 w-3 mr-1" />
                              )}
                              Avvia Laminazione
                            </Button>
                          )}
                          
                          {odl.status === 'Laminazione' && (
                            <Button 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleStatusChange(odl.id, 'Attesa Cura')}
                              disabled={isUpdating}
                            >
                              {isUpdating ? (
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              ) : (
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                              )}
                              Completa Laminazione
                            </Button>
                          )}
                          
                          <Link href={`/dashboard/shared/odl/${odl.id}`}>
                            <Button size="sm" variant="outline">
                              <ClipboardCheck className="h-3 w-3" />
                            </Button>
                          </Link>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar con azioni rapide */}
        <div className="space-y-6">
          {/* Azioni rapide */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RotateCcw className="h-5 w-5" />
                Azioni Rapide
              </CardTitle>
              <CardDescription>
                Operazioni frequenti
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link href="/dashboard/shared/odl">
                <Button className="w-full" variant="outline" size="sm">
                  <ClipboardCheck className="h-4 w-4 mr-2" />
                  Tutti gli ODL
                </Button>
              </Link>
              <Button className="w-full" variant="outline" size="sm" onClick={refresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Aggiorna Dati
              </Button>
            </CardContent>
          </Card>

          {/* Informazioni turno */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Timer className="h-5 w-5" />
                Info Turno
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm">
                <div className="flex justify-between">
                  <span>ODL Completati oggi:</span>
                  <span className="font-medium">{kpiData?.odl_finiti || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Efficienza:</span>
                  <span className={`font-medium ${kpiData && kpiData.efficienza_produzione >= 80 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {kpiData?.efficienza_produzione || 0}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>ODL Totali:</span>
                  <span className="font-medium">{kpiData?.odl_totali || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 