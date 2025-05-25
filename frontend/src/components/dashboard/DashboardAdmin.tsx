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
  Server
} from 'lucide-react'
import Link from 'next/link'

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

  // Statistiche rapide per l'admin
  const quickStats = [
    { label: 'Utenti Attivi', value: '24', trend: '+2 questa settimana' },
    { label: 'Sistema Uptime', value: '99.9%', trend: '30 giorni' },
    { label: 'ODL Totali', value: '1,247', trend: '+15% questo mese' },
    { label: 'Performance', value: 'Ottima', trend: 'Tutti i servizi operativi' }
  ]

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

      {/* Statistiche rapide */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.trend}</p>
            </CardContent>
          </Card>
        ))}
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cog className="h-5 w-5" />
            Azioni Rapide Amministratore
          </CardTitle>
          <CardDescription>
            Accesso diretto alle funzioni più utilizzate
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" size="sm">
              <Users className="h-4 w-4 mr-2" />
              Nuovo Utente
            </Button>
            <Button variant="outline" size="sm">
              <Database className="h-4 w-4 mr-2" />
              Backup Sistema
            </Button>
            <Button variant="outline" size="sm">
              <Activity className="h-4 w-4 mr-2" />
              Monitor Sistema
            </Button>
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Export Logs
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Configurazioni
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 