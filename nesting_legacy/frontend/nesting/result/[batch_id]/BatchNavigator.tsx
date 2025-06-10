'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, ChevronRight, Package, RefreshCw } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface BatchInfo {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  created_at: string
  numero_nesting: number
  autoclave?: {
    nome: string
  }
}

interface BatchNavigatorProps {
  currentBatchId: string
  className?: string
}

export default function BatchNavigator({ currentBatchId, className }: BatchNavigatorProps) {
  const router = useRouter()
  const [relatedBatches, setRelatedBatches] = useState<BatchInfo[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(false)

  // Carica batch correlati (creati nello stesso periodo)
  useEffect(() => {
    const loadRelatedBatches = async () => {
      try {
        setLoading(true)
        
        // Carica gli ultimi 10 batch per trovare quelli correlati
        const response = await fetch('/api/batch_nesting?limit=10&order_by=created_at&order=desc')
        if (!response.ok) return
        
        const allBatches: BatchInfo[] = await response.json()
        
        // Trova il batch corrente
        const currentBatch = allBatches.find(b => b.id === currentBatchId)
        if (!currentBatch) return
        
        // Filtra batch creati negli ultimi 5 minuti dal batch corrente
        const currentTime = new Date(currentBatch.created_at)
        const fiveMinutesAgo = new Date(currentTime.getTime() - 5 * 60 * 1000) // 5 minuti prima
        const fiveMinutesAfter = new Date(currentTime.getTime() + 5 * 60 * 1000) // 5 minuti dopo
        
        const related = allBatches.filter(batch => {
          const batchTime = new Date(batch.created_at)
          return batchTime >= fiveMinutesAgo && batchTime <= fiveMinutesAfter
        })
        
        // Ordina per data di creazione
        related.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        
        setRelatedBatches(related)
        
        // Trova l'indice del batch corrente
        const index = related.findIndex(b => b.id === currentBatchId)
        setCurrentIndex(index >= 0 ? index : 0)
        
      } catch (error) {
        console.error('Errore nel caricamento batch correlati:', error)
      } finally {
        setLoading(false)
      }
    }

    loadRelatedBatches()
  }, [currentBatchId])

  const navigateToBatch = (batchId: string) => {
    router.push(`/dashboard/curing/nesting/result/${batchId}`)
  }

  const navigateToPrevious = () => {
    if (currentIndex > 0 && relatedBatches.length > 0) {
      const prevBatch = relatedBatches[currentIndex - 1]
      navigateToBatch(prevBatch.id)
    }
  }

  const navigateToNext = () => {
    if (currentIndex < relatedBatches.length - 1 && relatedBatches.length > 0) {
      const nextBatch = relatedBatches[currentIndex + 1]
      navigateToBatch(nextBatch.id)
    }
  }

  // Non mostrare se c'è solo un batch o meno di 2 batch correlati
  if (relatedBatches.length < 2) {
    return null
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Package className="h-5 w-5" />
          Batch Correlati
          <Badge variant="outline" className="ml-auto">
            {currentIndex + 1} di {relatedBatches.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controlli di navigazione */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={navigateToPrevious}
            disabled={currentIndex === 0 || loading}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Precedente
          </Button>
          
          <div className="text-center">
            <p className="text-sm font-medium">
              Batch {currentIndex + 1} di {relatedBatches.length}
            </p>
            <p className="text-xs text-muted-foreground">
              {relatedBatches.length > 1 ? 'Generati contemporaneamente' : ''}
            </p>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={navigateToNext}
            disabled={currentIndex === relatedBatches.length - 1 || loading}
          >
            Successivo
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>

        {/* Lista batch con preview */}
        <div className="space-y-2">
          {relatedBatches.map((batch, index) => {
            const isCurrent = batch.id === currentBatchId
            
            return (
              <div
                key={batch.id}
                className={`p-2 rounded-lg border transition-colors cursor-pointer ${
                  isCurrent 
                    ? 'bg-primary/10 border-primary' 
                    : 'bg-muted/50 border-muted hover:bg-muted'
                }`}
                onClick={() => !isCurrent && navigateToBatch(batch.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${isCurrent ? 'text-primary' : ''}`}>
                      {batch.nome}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`} • 
                      {new Date(batch.created_at).toLocaleTimeString('it-IT', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={batch.stato === 'confermato' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {batch.stato}
                    </Badge>
                    {isCurrent && (
                      <Badge variant="outline" className="text-xs">
                        Corrente
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Barra di progresso visiva per indicare la posizione */}
                {relatedBatches.length > 1 && (
                  <div className="mt-1 h-1 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all ${
                        isCurrent ? 'bg-primary' : 'bg-muted-foreground/30'
                      }`}
                      style={{ 
                        width: `${((index + 1) / relatedBatches.length) * 100}%` 
                      }}
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Azione rapida per rigenerare */}
        <div className="pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => router.push('/dashboard/curing/nesting')}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Genera Nuovo Nesting
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 