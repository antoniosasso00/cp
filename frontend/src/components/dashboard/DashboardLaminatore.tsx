'use client'

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
  Gauge
} from 'lucide-react'
import Link from 'next/link'

/**
 * Dashboard dedicata ai Laminatori
 * 
 * Fornisce strumenti specifici per le operazioni di laminazione:
 * - Gestione parti e catalogo
 * - Operazioni di laminazione
 * - Controllo qualità
 * - Registrazione attività
 */
export default function DashboardLaminatore() {
  // Sezioni principali per il laminatore
  const laminatoreSections = [
    {
      title: 'Gestione Parti',
      description: 'Catalogo parti e specifiche tecniche',
      icon: Package,
      color: 'bg-green-500',
      href: '/dashboard/parts',
      actions: ['Catalogo parti', 'Specifiche', 'Materiali']
    },
    {
      title: 'Operazioni Laminazione',
      description: 'Processi di laminazione e controllo',
      icon: Layers,
      color: 'bg-blue-500',
      href: '/dashboard/produzione',
      actions: ['Avvia processo', 'Monitora', 'Registra dati']
    },
    {
      title: 'Controllo Qualità',
      description: 'Verifiche qualitative e conformità',
      icon: ClipboardCheck,
      color: 'bg-purple-500',
      href: '/dashboard/quality',
      actions: ['Check QC', 'Non conformità', 'Certificazioni']
    },
    {
      title: 'Strumenti & Attrezzature',
      description: 'Gestione tools e manutenzione',
      icon: Wrench,
      color: 'bg-orange-500',
      href: '/dashboard/tools',
      actions: ['Stato tools', 'Manutenzione', 'Prenotazioni']
    },
    {
      title: 'Tempi & Performance',
      description: 'Registrazione tempi e performance',
      icon: Timer,
      color: 'bg-indigo-500',
      href: '/dashboard/tempi',
      actions: ['Tempi ciclo', 'Efficienza', 'Obiettivi']
    },
    {
      title: 'ODL Assegnati',
      description: 'Ordini di lavoro in lavorazione',
      icon: CheckCircle2,
      color: 'bg-teal-500',
      href: '/dashboard/odl',
      actions: ['ODL attivi', 'Priorità', 'Completamento']
    }
  ]

  // Metriche operative per il laminatore
  const operativeMetrics = [
    { 
      label: 'ODL in Lavorazione', 
      value: '5', 
      trend: '2 completati oggi',
      status: 'active',
      icon: Play
    },
    { 
      label: 'Efficienza Turno', 
      value: '92%', 
      trend: 'Target: 85%',
      status: 'success',
      icon: Gauge
    },
    { 
      label: 'Tempo Medio Ciclo', 
      value: '45min', 
      trend: '-3min vs standard',
      status: 'success',
      icon: Timer
    },
    { 
      label: 'Controlli QC', 
      value: '8/8', 
      trend: '100% conformi',
      status: 'success',
      icon: CheckCircle2
    }
  ]

  // ODL attivi per il laminatore
  const activeODLs = [
    {
      id: 'ODL-1247',
      parte: 'Wing Panel A320',
      tool: 'TOOL-WP-001',
      status: 'in_progress',
      priority: 'Alta',
      timeRemaining: '2h 15min',
      progress: 65
    },
    {
      id: 'ODL-1248',
      parte: 'Fuselage Section',
      tool: 'TOOL-FS-003',
      status: 'waiting',
      priority: 'Media',
      timeRemaining: '4h 30min',
      progress: 0
    },
    {
      id: 'ODL-1249',
      parte: 'Control Surface',
      tool: 'TOOL-CS-002',
      status: 'quality_check',
      priority: 'Alta',
      timeRemaining: '30min',
      progress: 90
    }
  ]

  const getStatusColor = (status: string) => {
    const colors = {
      active: 'text-blue-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600'
    }
    return colors[status as keyof typeof colors] || 'text-gray-600'
  }

  const getODLStatusBadge = (status: string) => {
    const variants = {
      in_progress: { variant: 'default', label: 'In Lavorazione' },
      waiting: { variant: 'secondary', label: 'In Attesa' },
      quality_check: { variant: 'outline', label: 'Controllo QC' },
      completed: { variant: 'default', label: 'Completato' }
    }
    return variants[status as keyof typeof variants] || { variant: 'outline', label: status }
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
            <Wrench className="h-8 w-8 text-green-500" />
            Dashboard Laminatore
          </h1>
          <p className="text-muted-foreground mt-2">
            Operazioni di laminazione e gestione parti - Controllo qualità e registrazione attività
          </p>
        </div>
        <Badge variant="default" className="text-sm bg-green-500">
          <Wrench className="h-4 w-4 mr-1" />
          LAMINATORE
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
          {laminatoreSections.map((section, index) => {
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

        {/* Sidebar con ODL attivi */}
        <div className="space-y-6">
          {/* ODL Attivi */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                ODL Attivi
              </CardTitle>
              <CardDescription>
                Ordini di lavoro assegnati
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeODLs.map((odl, index) => {
                const statusInfo = getODLStatusBadge(odl.status)
                return (
                  <div key={index} className="p-4 rounded-lg border space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{odl.id}</div>
                      <Badge variant={statusInfo.variant as any}>
                        {statusInfo.label}
                      </Badge>
                    </div>
                    
                    <div className="space-y-1 text-sm">
                      <div><strong>Parte:</strong> {odl.parte}</div>
                      <div><strong>Tool:</strong> {odl.tool}</div>
                      <div className="flex items-center justify-between">
                        <span><strong>Priorità:</strong></span>
                        <span className={`font-medium ${getPriorityColor(odl.priority)}`}>
                          {odl.priority}
                        </span>
                      </div>
                      <div><strong>Tempo rimanente:</strong> {odl.timeRemaining}</div>
                    </div>

                    {/* Progress bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Progresso</span>
                        <span>{odl.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${odl.progress}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1">
                        <Play className="h-3 w-3 mr-1" />
                        Continua
                      </Button>
                      <Button size="sm" variant="outline">
                        <Pause className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>

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
              <Button className="w-full" variant="outline" size="sm">
                <Play className="h-4 w-4 mr-2" />
                Avvia Laminazione
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <ClipboardCheck className="h-4 w-4 mr-2" />
                Controllo QC
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <Timer className="h-4 w-4 mr-2" />
                Registra Tempi
              </Button>
              <Button className="w-full" variant="outline" size="sm">
                <AlertCircle className="h-4 w-4 mr-2" />
                Segnala Problema
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 