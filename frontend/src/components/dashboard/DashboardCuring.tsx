'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
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
  FileText,
  Gauge,
  AlertCircle,
  Timer
} from 'lucide-react'
import Link from 'next/link'
import { odlApi, autoclaveApi, type ODLResponse, type Autoclave } from '@/lib/api'

/**
 * 🔥 Dashboard Curing - Pannello di controllo per il reparto di cura
 * 
 * Funzionalità principali:
 * - ODL in cura e completati
 * - Stato autoclavi
 * - Statistiche di produzione
 */

export default function DashboardCuring() {
  const [odlInCura, setOdlInCura] = useState<ODLResponse[]>([])
  const [odlCompletati, setOdlCompletati] = useState<ODLResponse[]>([])
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Carica i dati del dashboard
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Carica ODL in cura
      const odlCura = await odlApi.getByStatus('Cura')
      setOdlInCura(odlCura)

      // Carica ODL completati oggi
      const oggi = new Date()
      oggi.setHours(0, 0, 0, 0)
      const domani = new Date(oggi)
      domani.setDate(domani.getDate() + 1)
      
      const odlFiniti = await odlApi.getCompleted({
        start_date: oggi.toISOString().split('T')[0],
        end_date: domani.toISOString().split('T')[0]
      })
      setOdlCompletati(odlFiniti)

      // Carica stato autoclavi
      const autoclaveList = await autoclaveApi.getAll()
      setAutoclavi(autoclaveList)

    } catch (err) {
      console.error('Errore nel caricamento dashboard curing:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Calcola statistiche
  const autoclavi_in_uso = autoclavi.filter(a => a.stato === 'IN_USO').length
  const autoclavi_disponibili = autoclavi.filter(a => a.stato === 'DISPONIBILE').length
  const autoclavi_guaste = autoclavi.filter(a => a.stato === 'GUASTO').length

  const kpiCards = [
    {
      title: 'ODL in Cura',
      value: odlInCura.length.toString(),
      description: 'Attualmente in processo',
      icon: <Thermometer className="h-4 w-4" />,
      status: odlInCura.length > 0 ? 'active' : 'success',
    },
    {
      title: 'Completati Oggi',
      value: odlCompletati.length.toString(),
      description: 'ODL finiti oggi',
      icon: <CheckCircle className="h-4 w-4" />,
      status: 'success',
    },
    {
      title: 'Autoclavi in Uso',
      value: autoclavi_in_uso.toString(),
      description: `${autoclavi_disponibili} disponibili`,
      icon: <Gauge className="h-4 w-4" />,
      status: autoclavi_in_uso > 0 ? 'active' : 'warning',
    },
    {
      title: 'Autoclavi Guaste',
      value: autoclavi_guaste.toString(),
      description: 'Richiedono manutenzione',
      icon: <AlertCircle className="h-4 w-4" />,
      status: autoclavi_guaste > 0 ? 'error' : 'success',
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-blue-600 bg-blue-50'
      case 'success': return 'text-green-600 bg-green-50'
      case 'warning': return 'text-yellow-600 bg-yellow-50'
      case 'error': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Curing</h1>
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-4 w-4 bg-gray-200 rounded"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-32"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Curing</h1>
          <Button onClick={fetchDashboardData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Riprova
          </Button>
        </div>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Curing</h1>
          <p className="text-muted-foreground">
            Monitoraggio processi di cura e stato autoclavi
          </p>
        </div>
        <Button onClick={fetchDashboardData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Aggiorna
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((kpi, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {kpi.title}
              </CardTitle>
              <div className={`p-2 rounded-md ${getStatusColor(kpi.status)}`}>
                {kpi.icon}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpi.value}</div>
              <p className="text-xs text-muted-foreground">
                {kpi.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Dettagli ODL e Autoclavi */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* ODL in Cura */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Thermometer className="h-5 w-5" />
              <span>ODL in Cura</span>
            </CardTitle>
            <CardDescription>
              Ordini attualmente in processo di cura
            </CardDescription>
          </CardHeader>
          <CardContent>
            {odlInCura.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">
                Nessun ODL in cura al momento
              </p>
            ) : (
              <div className="space-y-3">
                {odlInCura.slice(0, 5).map((odl) => (
                  <div key={odl.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">ODL #{odl.id}</p>
                      <p className="text-sm text-muted-foreground">
                        {odl.parte.part_number} - {odl.parte.descrizione_breve}
                      </p>
                    </div>
                    <Badge variant="secondary">
                      <Activity className="h-3 w-3 mr-1" />
                      In Cura
                    </Badge>
                  </div>
                ))}
                {odlInCura.length > 5 && (
                  <p className="text-sm text-muted-foreground text-center">
                    ... e altri {odlInCura.length - 5} ODL
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stato Autoclavi */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Gauge className="h-5 w-5" />
              <span>Stato Autoclavi</span>
            </CardTitle>
            <CardDescription>
              Panoramica dello stato delle autoclavi
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {autoclavi.map((autoclave) => (
                <div key={autoclave.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{autoclave.nome}</p>
                    <p className="text-sm text-muted-foreground">
                      {autoclave.codice}
                    </p>
                  </div>
                  <Badge 
                    variant={
                      autoclave.stato === 'DISPONIBILE' ? 'default' :
                      autoclave.stato === 'IN_USO' ? 'secondary' :
                      autoclave.stato === 'GUASTO' ? 'destructive' : 'outline'
                    }
                  >
                    {autoclave.stato}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 