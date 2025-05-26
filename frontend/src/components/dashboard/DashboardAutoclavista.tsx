'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Flame, 
  Thermometer, 
  Clock, 
  Grid3X3,
  Activity,
  PlayCircle,
  PauseCircle,
  StopCircle,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Calendar,
  Loader2,
  RefreshCw,
  FileText
} from 'lucide-react'
import Link from 'next/link'
import { useODLByRole } from '@/hooks/useODLByRole'
import { useDashboardKPI } from '@/hooks/useDashboardKPI'
import { nestingApi, type NestingResponse } from '@/lib/api'

/**
 * Dashboard dedicata agli Autoclavisti
 * 
 * Fornisce strumenti specifici per la gestione autoclavi:
 * - ODL in Attesa Cura e Cura (dati reali)
 * - Nesting confermati caricabili
 * - Cambio stato ODL con pulsanti funzionali
 * - KPI reali di produzione
 */
export default function DashboardAutoclavista() {
  const { odlList, loading, error, refresh, updateODLStatus } = useODLByRole({ 
    role: 'AUTOCLAVISTA',
    autoRefresh: true,
    refreshInterval: 30000 
  })
  
  const { data: kpiData, loading: kpiLoading } = useDashboardKPI()
  
  const [updatingODL, setUpdatingODL] = useState<number | null>(null)
  const [nestingList, setNestingList] = useState<NestingResponse[]>([])
  const [nestingLoading, setNestingLoading] = useState(true)
  const [nestingError, setNestingError] = useState<string | null>(null)

  // Carica i nesting confermati
  const fetchNestingConfermati = async () => {
    try {
      setNestingLoading(true)
      setNestingError(null)
      
      // Ottieni tutti i nesting confermati
      const allNesting = await nestingApi.getAll()
      const nestingConfermati = allNesting.filter(nesting => 
        nesting.confermato_da_ruolo && nesting.stato === 'confermato'
      )
      
      setNestingList(nestingConfermati)
    } catch (err) {
      console.error('Errore nel caricamento nesting:', err)
      setNestingError('Errore nel caricamento dei nesting')
    } finally {
      setNestingLoading(false)
    }
  }

  useEffect(() => {
    fetchNestingConfermati()
  }, [])

  // Calcola metriche operative reali
  const getOperativeMetrics = () => {
    const odlInAttesaCura = odlList.filter(odl => odl.status === 'Attesa Cura').length
    const odlInCura = odlList.filter(odl => odl.status === 'Cura').length
    const odlTotali = odlList.length
    
    return [
      { 
        label: 'ODL in Attesa Cura', 
        value: odlInAttesaCura.toString(), 
        trend: 'Pronti per autoclave',
        status: odlInAttesaCura > 0 ? 'active' : 'success',
        icon: Clock
      },
      { 
        label: 'ODL in Cura', 
        value: odlInCura.toString(), 
        trend: 'Attualmente in autoclave',
        status: odlInCura > 0 ? 'active' : 'success',
        icon: Flame
      },
      { 
        label: 'Nesting Confermati', 
        value: nestingList.length.toString(), 
        trend: 'Pronti per caricamento',
        status: nestingList.length > 0 ? 'active' : 'success',
        icon: Grid3X3
      },
      { 
        label: 'Utilizzo Autoclavi', 
        value: kpiData ? `${kpiData.utilizzo_medio_autoclavi}%` : '--', 
        trend: kpiData && kpiData.utilizzo_medio_autoclavi > 80 ? 'Alto utilizzo' : 'Capacità disponibile',
        status: kpiData && kpiData.utilizzo_medio_autoclavi > 90 ? 'warning' : 'success',
        icon: TrendingUp
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
      active: 'text-orange-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
      info: 'text-purple-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getODLStatusBadge = (status: string) => {
    const variants = {
      'Attesa Cura': { variant: 'secondary', label: 'Attesa Cura', color: 'bg-orange-500' },
      'Cura': { variant: 'default', label: 'In Cura', color: 'bg-red-500' }
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

  const refreshAll = () => {
    refresh()
    fetchNestingConfermati()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Flame className="h-8 w-8 text-orange-500" />
            Dashboard Autoclavista
          </h1>
          <p className="text-muted-foreground mt-2">
            Gestione ODL in Attesa Cura e Cura - Controllo autoclavi e nesting
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshAll}
            disabled={loading || nestingLoading}
          >
            <RefreshCw className={`h-4 w-4 ${(loading || nestingLoading) ? 'animate-spin' : ''}`} />
          </Button>
          <Badge variant="default" className="text-sm bg-orange-500">
            <Flame className="h-4 w-4 mr-1" />
            AUTOCLAVISTA
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
        <div className="lg:col-span-2 space-y-6">
          {/* ODL in Attesa Cura e Cura */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Flame className="h-5 w-5" />
                    ODL Assegnati
                  </CardTitle>
                  <CardDescription>
                    Ordini di lavoro in Attesa Cura e Cura
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
                  <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
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
                          {odl.status === 'Attesa Cura' && (
                            <Button 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleStatusChange(odl.id, 'Cura')}
                              disabled={isUpdating}
                            >
                              {isUpdating ? (
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              ) : (
                                <PlayCircle className="h-3 w-3 mr-1" />
                              )}
                              Avvia Cura
                            </Button>
                          )}
                          
                          {odl.status === 'Cura' && (
                            <Button 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleStatusChange(odl.id, 'Finito')}
                              disabled={isUpdating}
                            >
                              {isUpdating ? (
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                              ) : (
                                <CheckCircle className="h-3 w-3 mr-1" />
                              )}
                              Completa Cura
                            </Button>
                          )}
                          
                          <Link href={`/dashboard/shared/odl/${odl.id}`}>
                            <Button size="sm" variant="outline">
                              <FileText className="h-3 w-3" />
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

          {/* Nesting Confermati */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Grid3X3 className="h-5 w-5" />
                    Nesting Confermati
                  </CardTitle>
                  <CardDescription>
                    Nesting pronti per il caricamento in autoclave
                  </CardDescription>
                </div>
                <Badge variant="outline">
                  {nestingList.length} Nesting
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {nestingLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Caricamento nesting...</span>
                </div>
              ) : nestingError ? (
                <div className="text-center py-8">
                  <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                  <p className="text-sm text-red-600 mb-3">{nestingError}</p>
                  <Button variant="outline" size="sm" onClick={fetchNestingConfermati}>
                    Riprova
                  </Button>
                </div>
              ) : nestingList.length === 0 ? (
                <div className="text-center py-8">
                  <Grid3X3 className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Nessun nesting confermato disponibile
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {nestingList.map((nesting) => (
                    <div key={nesting.id} className="p-4 rounded-lg border space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="font-medium">Nesting #{nesting.id}</div>
                        <Badge variant="default" className="bg-green-500">
                          Confermato
                        </Badge>
                      </div>
                      
                      <div className="space-y-1 text-sm">
                        <div><strong>Autoclave:</strong> {nesting.autoclave.nome} ({nesting.autoclave.codice})</div>
                        <div><strong>ODL inclusi:</strong> {nesting.odl_list.length}</div>
                        <div><strong>Utilizzo area:</strong> {Math.round((nesting.area_utilizzata / nesting.area_totale) * 100)}%</div>
                        <div><strong>Valvole:</strong> {nesting.valvole_utilizzate}/{nesting.valvole_totali}</div>
                        {nesting.ciclo_cura_nome && (
                          <div><strong>Ciclo cura:</strong> {nesting.ciclo_cura_nome}</div>
                        )}
                      </div>

                      <div className="flex gap-2 pt-2">
                        <Link href={`/dashboard/shared/nesting/${nesting.id}`}>
                          <Button size="sm" className="flex-1">
                            <PlayCircle className="h-3 w-3 mr-1" />
                            Carica in Autoclave
                          </Button>
                        </Link>
                        <Link href={`/dashboard/shared/nesting/${nesting.id}`}>
                          <Button size="sm" variant="outline">
                            <FileText className="h-3 w-3" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
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
                <Activity className="h-5 w-5" />
                Azioni Rapide
              </CardTitle>
              <CardDescription>
                Operazioni frequenti
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link href="/dashboard/shared/nesting">
                <Button className="w-full" variant="outline" size="sm">
                  <Grid3X3 className="h-4 w-4 mr-2" />
                  Gestione Nesting
                </Button>
              </Link>
              <Link href="/dashboard/shared/autoclavi">
                <Button className="w-full" variant="outline" size="sm">
                  <Flame className="h-4 w-4 mr-2" />
                  Stato Autoclavi
                </Button>
              </Link>
              <Link href="/dashboard/shared/odl">
                <Button className="w-full" variant="outline" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Tutti gli ODL
                </Button>
              </Link>
              <Button className="w-full" variant="outline" size="sm" onClick={refreshAll}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Aggiorna Dati
              </Button>
            </CardContent>
          </Card>

          {/* Informazioni turno */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
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
                  <span>Utilizzo Autoclavi:</span>
                  <span className={`font-medium ${kpiData && kpiData.utilizzo_medio_autoclavi > 80 ? 'text-orange-600' : 'text-green-600'}`}>
                    {kpiData?.utilizzo_medio_autoclavi || 0}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Nesting Attivi:</span>
                  <span className="font-medium">{kpiData?.nesting_attivi || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Stato sistema */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Stato Sistema
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm">
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