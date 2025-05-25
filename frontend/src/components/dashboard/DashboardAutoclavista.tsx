'use client'

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
  Calendar
} from 'lucide-react'
import Link from 'next/link'
import { NestingStatusCard } from './NestingStatusCard'

/**
 * Dashboard dedicata agli Autoclavisti
 * 
 * Fornisce strumenti specifici per la gestione autoclavi:
 * - Gestione autoclavi e cicli di cura
 * - Nesting e scheduling
 * - Monitoraggio processi
 * - Controllo temperatura e pressione
 */
export default function DashboardAutoclavista() {
  // Sezioni principali per l'autoclavista
  const autoclavistaSections = [
    {
      title: 'Gestione Autoclavi',
      description: 'Controllo e monitoraggio autoclavi',
      icon: Flame,
      color: 'bg-orange-500',
      href: '/dashboard/autoclavi',
      actions: ['Stato autoclavi', 'Parametri', 'Manutenzione']
    },
    {
      title: 'Cicli di Cura',
      description: 'Gestione e monitoraggio cicli termici',
      icon: Thermometer,
      color: 'bg-red-500',
      href: '/dashboard/cicli-cura',
      actions: ['Avvia ciclo', 'Monitora', 'Storico']
    },
    {
      title: 'Nesting & Scheduling',
      description: 'Ottimizzazione carico e pianificazione',
      icon: Grid3X3,
      color: 'bg-blue-500',
      href: '/dashboard/nesting',
      actions: ['Ottimizza carico', 'Pianifica', 'Simulazioni']
    },
    {
      title: 'Monitoraggio Processi',
      description: 'Controllo in tempo reale dei processi',
      icon: Activity,
      color: 'bg-green-500',
      href: '/dashboard/monitoring',
      actions: ['Dashboard live', 'Allarmi', 'Trend']
    },
    {
      title: 'Scheduling Produzione',
      description: 'Pianificazione temporale delle attività',
      icon: Calendar,
      color: 'bg-purple-500',
      href: '/dashboard/schedule',
      actions: ['Timeline', 'Risorse', 'Ottimizzazione']
    },
    {
      title: 'Reports & Analytics',
      description: 'Analisi performance e efficienza',
      icon: TrendingUp,
      color: 'bg-indigo-500',
      href: '/dashboard/reports',
      actions: ['Efficienza', 'Consumi', 'KPI']
    }
  ]

  // Stato autoclavi
  const autoclaviStatus = [
    { 
      id: 'AC-001',
      name: 'Autoclave Alpha',
      status: 'running',
      temperature: '180°C',
      pressure: '6.5 bar',
      timeRemaining: '2h 45min',
      progress: 35
    },
    { 
      id: 'AC-002',
      name: 'Autoclave Beta',
      status: 'idle',
      temperature: '25°C',
      pressure: '0 bar',
      timeRemaining: 'Pronta',
      progress: 0
    },
    { 
      id: 'AC-003',
      name: 'Autoclave Gamma',
      status: 'maintenance',
      temperature: '25°C',
      pressure: '0 bar',
      timeRemaining: 'Manutenzione',
      progress: 0
    }
  ]

  // Metriche operative
  const operativeMetrics = [
    { 
      label: 'Autoclavi Attive', 
      value: '1/3', 
      trend: 'AC-001 in ciclo',
      status: 'active',
      icon: Flame
    },
    { 
      label: 'Efficienza Media', 
      value: '94%', 
      trend: '+2% questa settimana',
      status: 'success',
      icon: TrendingUp
    },
    { 
      label: 'Cicli Completati', 
      value: '8', 
      trend: 'Oggi',
      status: 'success',
      icon: CheckCircle
    },
    { 
      label: 'Tempo Medio Ciclo', 
      value: '6.2h', 
      trend: 'Standard: 6.5h',
      status: 'success',
      icon: Clock
    }
  ]

  // Cicli programmati
  const scheduledCycles = [
    {
      id: 'CICLO-001',
      autoclave: 'AC-002',
      startTime: '14:30',
      duration: '6h 30min',
      parts: ['Wing Panel x4', 'Fuselage Section x2'],
      priority: 'Alta',
      status: 'scheduled'
    },
    {
      id: 'CICLO-002',
      autoclave: 'AC-001',
      startTime: '22:15',
      duration: '7h 15min',
      parts: ['Control Surface x6'],
      priority: 'Media',
      status: 'queued'
    }
  ]

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'text-orange-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getAutoclaveStatusBadge = (status: string) => {
    const variants = {
      running: { variant: 'default', label: 'In Funzione', color: 'bg-orange-500' },
      idle: { variant: 'secondary', label: 'Pronta', color: 'bg-green-500' },
      maintenance: { variant: 'destructive', label: 'Manutenzione', color: 'bg-red-500' },
      error: { variant: 'destructive', label: 'Errore', color: 'bg-red-600' }
    }
    return variants[status as keyof typeof variants] || { variant: 'outline', label: status, color: 'bg-gray-500' }
  }

  const getPriorityColor = (priority: string) => {
    const colors = {
      'Alta': 'text-red-600',
      'Media': 'text-yellow-600',
      'Bassa': 'text-green-600'
    }
    return colors[priority as keyof typeof colors] || 'text-gray-600'
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
            Gestione autoclavi e cicli di cura - Nesting, scheduling e monitoraggio processi
          </p>
        </div>
        <Badge variant="default" className="text-sm bg-orange-500">
          <Flame className="h-4 w-4 mr-1" />
          AUTOCLAVISTA
        </Badge>
      </div>

      {/* Metriche operative */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {operativeMetrics.map((metric, index) => {
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
          {autoclavistaSections.map((section, index) => {
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

        {/* Sidebar con stato autoclavi e cicli */}
        <div className="space-y-6">
          {/* Nesting Status Card */}
          <NestingStatusCard />
          
          {/* Stato Autoclavi */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5" />
                Stato Autoclavi
              </CardTitle>
              <CardDescription>
                Monitoraggio in tempo reale
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {autoclaviStatus.map((autoclave, index) => {
                const statusInfo = getAutoclaveStatusBadge(autoclave.status)
                return (
                  <div key={index} className="p-4 rounded-lg border space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{autoclave.name}</div>
                      <Badge variant={statusInfo.variant as any} className={statusInfo.color}>
                        {statusInfo.label}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Thermometer className="h-3 w-3" />
                        {autoclave.temperature}
                      </div>
                      <div className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {autoclave.pressure}
                      </div>
                    </div>

                    <div className="text-sm">
                      <strong>Tempo rimanente:</strong> {autoclave.timeRemaining}
                    </div>

                    {autoclave.status === 'running' && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>Progresso</span>
                          <span>{autoclave.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-orange-500 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${autoclave.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2">
                      {autoclave.status === 'running' ? (
                        <>
                          <Button size="sm" variant="outline" className="flex-1">
                            <PauseCircle className="h-3 w-3 mr-1" />
                            Pausa
                          </Button>
                          <Button size="sm" variant="outline">
                            <StopCircle className="h-3 w-3" />
                          </Button>
                        </>
                      ) : autoclave.status === 'idle' ? (
                        <Button size="sm" variant="outline" className="w-full">
                          <PlayCircle className="h-3 w-3 mr-1" />
                          Avvia Ciclo
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline" className="w-full" disabled>
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Non Disponibile
                        </Button>
                      )}
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>

          {/* Cicli Programmati */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Cicli Programmati
              </CardTitle>
              <CardDescription>
                Prossimi cicli in coda
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {scheduledCycles.map((cycle, index) => (
                <div key={index} className="p-3 rounded-lg border space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-sm">{cycle.id}</div>
                    <Badge variant="outline">{cycle.autoclave}</Badge>
                  </div>
                  
                  <div className="text-xs space-y-1">
                    <div><strong>Inizio:</strong> {cycle.startTime}</div>
                    <div><strong>Durata:</strong> {cycle.duration}</div>
                    <div className="flex items-center justify-between">
                      <span><strong>Priorità:</strong></span>
                      <span className={`font-medium ${getPriorityColor(cycle.priority)}`}>
                        {cycle.priority}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs">
                    <strong>Parti:</strong>
                    <div className="mt-1 space-y-1">
                      {cycle.parts.map((part, partIndex) => (
                        <div key={partIndex} className="text-muted-foreground">
                          • {part}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Azioni rapide */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Grid3X3 className="h-5 w-5" />
                Azioni Rapide
              </CardTitle>
              <CardDescription>
                Operazioni frequenti
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full" variant="outline" size="sm">
                <PlayCircle className="h-4 w-4 mr-2" />
                Avvia Ciclo
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <Grid3X3 className="h-4 w-4 mr-2" />
                Ottimizza Nesting
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <Calendar className="h-4 w-4 mr-2" />
                Pianifica Cicli
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Controllo Allarmi
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 