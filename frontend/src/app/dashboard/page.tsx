'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ODLResponse, odlApi } from '@/lib/api'
import { CalendarClock, Clipboard, Loader2, Settings, Factory, Gauge, Activity, MoreHorizontal } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { useQuery } from '@tanstack/react-query'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

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
  const {
    data: odls = [],
    isLoading,
    isError
  } = useQuery<ODLResponse[], Error>({
    queryKey: ['odl'],
    queryFn: () => odlApi.getAll()
  })

  // Ordina e calcola stats solo quando i dati sono caricati
  const sortedODLs = [...odls].sort((a, b) => b.priorita - a.priorita)
  const lastODLs = sortedODLs.slice(0, 5)
  const odlStats: Record<string, number> = {}
  for (const odl of odls) {
    if (!odlStats[odl.status]) odlStats[odl.status] = 0
    odlStats[odl.status]++
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Benvenuto nel sistema di gestione CarbonPilot
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Widget ODL */}
        <Card className="col-span-2 md:col-span-2 lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ordini di Lavoro</CardTitle>
            <Clipboard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : isError ? (
              <div className="text-center text-destructive py-8">
                Errore nel caricamento degli ODL.
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
                    {lastODLs.length > 0 ? (
                      <div className="divide-y">
                        {lastODLs.map(odl => (
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
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem asChild>
                                    <Link href={`/dashboard/odl/${odl.id}`}>
                                      Dettagli
                                    </Link>
                                  </DropdownMenuItem>
                                  <DropdownMenuItem asChild>
                                    <Link href={`/dashboard/odl/${odl.id}/edit`}>
                                      Modifica
                                    </Link>
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
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
                  
                  <div className="flex justify-end">
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

        {/* Widget Azioni Rapide */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Azioni Rapide</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Link href="/dashboard/odl/new" className="w-full">
                <Button variant="outline" className="w-full justify-start">
                  <Clipboard className="mr-2 h-4 w-4" />
                  Nuovo ODL
                </Button>
              </Link>
              <Link href="/dashboard/parts/new" className="w-full">
                <Button variant="outline" className="w-full justify-start">
                  <Factory className="mr-2 h-4 w-4" />
                  Nuova Parte
                </Button>
              </Link>
              <Link href="/dashboard/tools/new" className="w-full">
                <Button variant="outline" className="w-full justify-start">
                  <Settings className="mr-2 h-4 w-4" />
                  Nuovo Tool
                </Button>
              </Link>
              <Link href="/dashboard/nesting" className="w-full">
                <Button variant="outline" className="w-full justify-start">
                  <Gauge className="mr-2 h-4 w-4" />
                  Nesting
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 