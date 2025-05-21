'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ODLResponse, odlApi } from '@/lib/api'
import { CalendarClock, Clipboard, Loader2, Settings } from 'lucide-react'

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "primary" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "primary",
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

export default function DashboardPage() {
  const [odls, setODLs] = useState<ODLResponse[]>([])
  const [odlStats, setODLStats] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const odlData = await odlApi.getAll()
        
        // Ordina gli ODL per priorità decrescente
        const sortedODLs = [...odlData].sort((a, b) => b.priorita - a.priorita)
        setODLs(sortedODLs.slice(0, 5)) // Prendi solo i primi 5 ODL
        
        // Calcola le statistiche per stato
        const stats: Record<string, number> = {}
        for (const odl of odlData) {
          if (!stats[odl.status]) {
            stats[odl.status] = 0
          }
          stats[odl.status]++
        }
        setODLStats(stats)
      } catch (error) {
        console.error("Errore nel caricamento degli ODL:", error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Benvenuto nel sistema di gestione CarbonPilot
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Widget ODL */}
        <Card className="col-span-2 md:col-span-1 lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ordini di Lavoro</CardTitle>
            <Clipboard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <>
                <div className="flex space-x-2 mb-4">
                  {Object.entries(odlStats).map(([status, count]) => (
                    <Badge key={status} variant={getStatusBadgeVariant(status)}>
                      {status}: {count}
                    </Badge>
                  ))}
                </div>
                
                <div className="space-y-4">
                  <h3 className="text-sm font-medium">Ultimi ODL per priorità</h3>
                  <div className="border rounded-md">
                    {odls.length > 0 ? (
                      <div className="divide-y">
                        {odls.map(odl => (
                          <div key={odl.id} className="flex items-center justify-between p-3">
                            <div className="flex items-center gap-2">
                              <Badge variant={getStatusBadgeVariant(odl.status)}>
                                {odl.status}
                              </Badge>
                              <div className="font-medium">
                                {odl.parte.part_number} - {odl.tool.codice}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">Priorità: {odl.priorita}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-3 text-center text-sm text-muted-foreground">
                        Nessun ODL trovato
                      </div>
                    )}
                  </div>
                  
                  <div className="flex justify-center mt-2">
                    <Link href="/dashboard/odl">
                      <Button variant="outline" size="sm">
                        Visualizza tutti gli ODL
                      </Button>
                    </Link>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Catalogo</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci il catalogo dei part number
            </p>
            <div className="mt-4">
              <Link href="/dashboard/catalog">
                <Button>Vai al Catalogo</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Parti</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci le parti in produzione
            </p>
            <div className="mt-4">
              <Link href="/dashboard/parts">
                <Button>Vai alle Parti</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Cicli Cura</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci i cicli di cura
            </p>
            <div className="mt-4">
              <Link href="/dashboard/cicli-cura">
                <Button>Vai ai Cicli</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Tools/Stampi</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci gli stampi di produzione
            </p>
            <div className="mt-4">
              <Link href="/dashboard/tools">
                <Button>Vai agli Stampi</Button>
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-col space-y-2">
            <h3 className="text-2xl font-bold tracking-tight">Autoclavi</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci le autoclavi
            </p>
            <div className="mt-4">
              <Link href="/dashboard/autoclavi">
                <Button>Vai alle Autoclavi</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 