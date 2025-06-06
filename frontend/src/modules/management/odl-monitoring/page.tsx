'use client'

import { useState } from 'react'

// Force dynamic rendering for this page
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Package, RefreshCw } from 'lucide-react'

export default function ODLMonitoringPage() {
  const [loading, setLoading] = useState(false)

  const handleRefresh = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 1000)
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio ODL</h1>
          <p className="text-muted-foreground">
            Controllo e gestione degli Ordini di Lavoro
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>ODL in Monitoraggio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Nessun ODL in monitoraggio al momento</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 