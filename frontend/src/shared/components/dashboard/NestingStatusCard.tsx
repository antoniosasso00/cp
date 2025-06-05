'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Package,
  RefreshCw,
  Loader2,
  Clock,
  AlertTriangle
} from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useUserRole } from '@/shared/hooks/useUserRole'
import { formatDateIT } from '@/lib/utils'

/**
 * Componente per visualizzare una panoramica dei nesting nella dashboard
 * Mostra i nesting raggruppati per stato con azioni specifiche per ruolo
 * 
 * NOTA: Temporaneamente disabilitato per problemi di compatibilità API
 */
export function NestingStatusCard() {
  const { role } = useUserRole()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Stato Nesting
            </CardTitle>
            <CardDescription>
              Panoramica dei nesting di produzione (in aggiornamento)
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="icon"
            disabled={true}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground mb-3">
            Componente in aggiornamento per compatibilità API
          </p>
          <Link href="/dashboard/curing/nesting">
            <Button variant="outline" size="sm">
              Vai al Nesting
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
} 