'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Users, 
  Wrench, 
  Flame,
  Package,
  ClipboardList,
  ExternalLink
} from 'lucide-react'

/**
 * Pagina di test per verificare tutti i link della nuova struttura organizzata per ruoli
 * Questa pagina può essere rimossa dopo i test
 */
export default function TestLinksPage() {
  const testLinks = [
    {
      category: "ADMIN",
      icon: Shield,
      color: "bg-red-500",
      links: [
        { title: "Impostazioni", href: "/dashboard/admin/impostazioni", description: "Configurazioni di sistema" }
      ]
    },
    {
      category: "MANAGEMENT", 
      icon: Users,
      color: "bg-blue-500",
      links: [
        { title: "Reports", href: "/dashboard/management/reports", description: "Reports e analytics" },
        { title: "ODL Monitoring", href: "/dashboard/management/odl-monitoring", description: "Monitoraggio ODL tempo reale" },
        { title: "Dashboard Monitoraggio", href: "/dashboard/monitoraggio", description: "Dashboard unificata con statistiche e tempi" }
      ]
    },
    {
      category: "CLEAN ROOM",
      icon: Wrench, 
      color: "bg-green-500",
      links: [
        { title: "Parts", href: "/dashboard/clean-room/parts", description: "Gestione parti" },
        { title: "Tools", href: "/dashboard/clean-room/tools", description: "Tools e stampi" },
        { title: "Produzione", href: "/dashboard/clean-room/produzione", description: "Operazioni produzione" },
        { title: "Tempi", href: "/dashboard/clean-room/tempi", description: "Tempi e performance" }
      ]
    },
    {
      category: "CURING",
      icon: Flame,
      color: "bg-orange-500", 
      links: [
        { title: "Nesting", href: "/dashboard/curing/nesting", description: "Gestione nesting" },
        { title: "Autoclavi", href: "/dashboard/curing/autoclavi", description: "Controllo autoclavi" },
        { title: "Cicli Cura", href: "/dashboard/curing/cicli-cura", description: "Cicli di cura" },
        { title: "Schedule", href: "/dashboard/curing/schedule", description: "Scheduling produzione" }
      ]
    },
    {
      category: "SHARED",
      icon: Package,
      color: "bg-purple-500",
      links: [
        { title: "Catalog", href: "/dashboard/shared/catalog", description: "Catalogo parti condivisi" },
        { title: "ODL", href: "/dashboard/shared/odl", description: "Gestione ODL condivisa" }
      ]
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <ClipboardList className="h-8 w-8 text-primary" />
            Test Links - Nuova Struttura
          </h1>
          <p className="text-muted-foreground mt-2">
            Verifica tutti i link della struttura riorganizzata per ruoli
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Test Page
        </Badge>
      </div>

      {/* Grid delle categorie */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {testLinks.map((category, categoryIndex) => {
          const IconComponent = category.icon
          
          return (
            <Card key={categoryIndex} className="hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg ${category.color} flex items-center justify-center`}>
                    <IconComponent className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{category.category}</CardTitle>
                    <CardDescription>{category.links.length} pagine</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {category.links.map((link, linkIndex) => (
                  <div key={linkIndex} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{link.title}</h4>
                        <p className="text-sm text-muted-foreground">{link.description}</p>
                      </div>
                    </div>
                    <Link href={link.href}>
                      <Button variant="outline" size="sm" className="w-full">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Testa Link
                      </Button>
                    </Link>
                  </div>
                ))}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Istruzioni */}
      <Card>
        <CardHeader>
          <CardTitle>Istruzioni Test</CardTitle>
          <CardDescription>
            Come utilizzare questa pagina per verificare la nuova struttura
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">1. Test dei Link</h4>
            <p className="text-sm text-muted-foreground">
              Clicca su ogni "Testa Link" per verificare che le pagine si caricano correttamente
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">2. Verifica Sidebar</h4>
            <p className="text-sm text-muted-foreground">
              Controlla che la sidebar mostri le voci corrette per ogni ruolo selezionato
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">3. Test Ruoli</h4>
            <p className="text-sm text-muted-foreground">
              Vai su /select-role, cambia ruolo e verifica che le pagine siano accessibili
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">4. Rimozione</h4>
            <p className="text-sm text-muted-foreground">
              Questa pagina può essere rimossa dopo aver completato i test
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 