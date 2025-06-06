'use client'

import React from 'react'
import { Card, CardContent, CardHeader } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '@/shared/components/ui/tabs'
import { 
  Package, 
  CheckCircle, 
  Clock, 
  CheckCircle2,
  AlertTriangle 
} from 'lucide-react'

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}

interface BatchNestingResult {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: AutoclaveInfo
  created_at: string
  numero_nesting: number
  metrics?: {
    efficiency_percentage?: number
  }
}

interface BatchTabsProps {
  batches: BatchNestingResult[]
  selectedIndex: number
  onSelectionChange: (index: number) => void
}

export default function BatchTabs({ batches, selectedIndex, onSelectionChange }: BatchTabsProps) {
  // ✨ MIGLIORAMENTO: Mostra sempre il componente se ci sono batch, con informazioni utili
  if (batches.length <= 1) {
    return (
      <Card>
        <CardContent className="py-3">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4" />
              <span>Batch singolo</span>
            </div>
            <Badge variant="outline" className="text-xs">
              1 risultato
            </Badge>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getStatoIcon = (stato: string) => {
    switch (stato?.toLowerCase()) {
      case 'sospeso':
        return <Clock className="h-3 w-3 text-yellow-600" />
      case 'confermato':
        return <CheckCircle className="h-3 w-3 text-green-600" />
      case 'terminato':
        return <CheckCircle2 className="h-3 w-3 text-gray-600" />
      default:
        return <AlertTriangle className="h-3 w-3 text-red-600" />
    }
  }

  const getStatoColor = (stato: string) => {
    switch (stato?.toLowerCase()) {
      case 'sospeso':
        return 'border-yellow-200 bg-yellow-50 hover:bg-yellow-100'
      case 'confermato':
        return 'border-green-200 bg-green-50 hover:bg-green-100'
      case 'terminato':
        return 'border-gray-200 bg-gray-50 hover:bg-gray-100'
      default:
        return 'border-red-200 bg-red-50 hover:bg-red-100'
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            <h3 className="text-lg font-semibold">Batch Multi-Autoclave</h3>
          </div>
          <Badge variant="outline" className="text-sm">
            {batches.length} batch generati
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Desktop: Tab orizzontali */}
        <div className="hidden md:block">
          <Tabs value={selectedIndex.toString()} onValueChange={(value) => onSelectionChange(parseInt(value))}>
            <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${batches.length}, 1fr)` }}>
              {batches.map((batch, index) => (
                <TabsTrigger 
                  key={batch.id} 
                  value={index.toString()}
                  className="flex items-center gap-2 px-4 py-2"
                >
                  {getStatoIcon(batch.stato)}
                  <span className="font-medium">
                    {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}
                  </span>
                  {batch.metrics?.efficiency_percentage && (
                    <Badge variant="secondary" className="text-xs ml-1">
                      {batch.metrics.efficiency_percentage.toFixed(0)}%
                    </Badge>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* Mobile: Lista verticale */}
        <div className="md:hidden space-y-2">
          {batches.map((batch, index) => (
            <Button
              key={batch.id}
              variant={index === selectedIndex ? "default" : "outline"}
              className={`w-full justify-start p-4 h-auto ${index === selectedIndex ? '' : getStatoColor(batch.stato)}`}
              onClick={() => onSelectionChange(index)}
            >
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-3">
                  {getStatoIcon(batch.stato)}
                  <div className="text-left">
                    <div className="font-medium">
                      {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {batch.nome} • {new Date(batch.created_at).toLocaleTimeString('it-IT', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {batch.metrics?.efficiency_percentage && (
                    <Badge variant="secondary" className="text-xs">
                      {batch.metrics.efficiency_percentage.toFixed(0)}%
                    </Badge>
                  )}
                  <Badge 
                    variant={batch.stato === 'confermato' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {batch.stato}
                  </Badge>
                </div>
              </div>
            </Button>
          ))}
        </div>

        {/* Informazioni batch corrente */}
        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Batch selezionato: <span className="font-medium">{selectedIndex + 1} di {batches.length}</span>
            </span>
            <span className="text-muted-foreground">
              Creato: {new Date(batches[selectedIndex].created_at).toLocaleString('it-IT')}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 