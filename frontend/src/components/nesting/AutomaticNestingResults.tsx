'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { CheckCircle, AlertCircle, Package, Layers, Gauge, Weight, Eye, Check } from 'lucide-react'
import { AutomaticNestingResponse, NestingResultSummary, nestingApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface AutomaticNestingResultsProps {
  results: AutomaticNestingResponse
  onViewDetails?: (nestingId: number) => void
  onNestingConfirmed?: () => void
}

export function AutomaticNestingResults({ results, onViewDetails, onNestingConfirmed }: AutomaticNestingResultsProps) {
  const { toast } = useToast()

  // Funzione per confermare un nesting
  const handleConfirmNesting = async (nestingId: number) => {
    try {
      await nestingApi.confirm(nestingId, {
        confermato_da_ruolo: "operatore",
        note_conferma: "Nesting confermato dall'interfaccia utente"
      })
      
      toast({
        title: "✅ Nesting Confermato",
        description: `Il nesting #${nestingId} è stato confermato e passato allo stato "In sospeso"`,
      })
      
      // Callback per aggiornare la UI
      if (onNestingConfirmed) {
        onNestingConfirmed()
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile confermare il nesting",
        variant: "destructive",
      })
    }
  }

  if (!results.success) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            Errore Nesting Automatico
          </CardTitle>
          <CardDescription>
            Si è verificato un errore durante la generazione automatica
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{results.message}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Riepilogo generale */}
      <Card className="border-green-200 bg-green-50/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-700">
            <CheckCircle className="h-5 w-5" />
            Nesting Automatico Completato
          </CardTitle>
          <CardDescription>
            {results.message}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {results.summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {results.summary.total_nesting_created}
                </div>
                <div className="text-sm text-muted-foreground">Nesting Creati</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {results.summary.total_odl_processed}
                </div>
                <div className="text-sm text-muted-foreground">ODL Processati</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {results.summary.total_odl_excluded}
                </div>
                <div className="text-sm text-muted-foreground">ODL Esclusi</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {results.summary.autoclavi_utilizzate}
                </div>
                <div className="text-sm text-muted-foreground">Autoclavi Utilizzate</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lista dei nesting generati */}
      {results.nesting_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Nesting Generati ({results.nesting_results.length})
            </CardTitle>
            <CardDescription>
              Dettagli dei nesting creati automaticamente
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.nesting_results.map((nesting) => (
                <NestingResultCard 
                  key={nesting.id} 
                  nesting={nesting} 
                  onViewDetails={onViewDetails}
                  onConfirm={handleConfirmNesting}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function NestingResultCard({ 
  nesting, 
  onViewDetails,
  onConfirm
}: { 
  nesting: NestingResultSummary
  onViewDetails?: (nestingId: number) => void
  onConfirm?: (nestingId: number) => void
}) {
  const [isConfirming, setIsConfirming] = useState(false)

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato.toLowerCase()) {
      case 'bozza':
        return 'secondary'
      case 'in sospeso':
        return 'default'
      case 'confermato':
        return 'default'
      case 'in_elaborazione':
        return 'default'
      case 'completato':
        return 'default'
      default:
        return 'outline'
    }
  }

  const handleConfirm = async () => {
    if (!onConfirm) return
    
    setIsConfirming(true)
    try {
      await onConfirm(nesting.id)
    } finally {
      setIsConfirming(false)
    }
  }

  // Determina se il nesting può essere confermato
  const canBeConfirmed = nesting.stato.toLowerCase() === 'bozza'

  return (
    <div className="border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-lg">
            Nesting #{nesting.id} - {nesting.autoclave_nome}
          </h3>
          <p className="text-sm text-muted-foreground">
            Ciclo: {nesting.ciclo_cura}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={getStatoBadgeVariant(nesting.stato)}>
            {nesting.stato}
          </Badge>
          
          {/* Pulsante Conferma - visibile solo se il nesting è in bozza */}
          {canBeConfirmed && onConfirm && (
            <Button 
              variant="default" 
              size="sm"
              onClick={handleConfirm}
              disabled={isConfirming}
              className="bg-green-600 hover:bg-green-700"
            >
              <Check className="h-4 w-4 mr-2" />
              {isConfirming ? 'Confermando...' : 'Conferma'}
            </Button>
          )}
          
          {onViewDetails && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => onViewDetails(nesting.id)}
            >
              <Eye className="h-4 w-4 mr-2" />
              Dettagli
            </Button>
          )}
        </div>
      </div>

      {/* Statistiche del nesting */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-blue-500" />
          <div>
            <div className="text-sm text-muted-foreground">ODL Inclusi</div>
            <div className="font-medium">{nesting.odl_inclusi}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-orange-500" />
          <div>
            <div className="text-sm text-muted-foreground">ODL Esclusi</div>
            <div className="font-medium">{nesting.odl_esclusi}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-green-500" />
          <div>
            <div className="text-sm text-muted-foreground">Area Utilizzata</div>
            <div className="font-medium">{nesting.area_utilizzata.toFixed(0)} cm²</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Weight className="h-4 w-4 text-purple-500" />
          <div>
            <div className="text-sm text-muted-foreground">Peso Totale</div>
            <div className="font-medium">{nesting.peso_totale.toFixed(1)} kg</div>
          </div>
        </div>
      </div>

      {/* Barra di efficienza */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Efficienza di Utilizzo</span>
          <span className="text-sm text-muted-foreground">
            {nesting.efficienza.toFixed(1)}%
          </span>
        </div>
        <Progress 
          value={nesting.efficienza} 
          className="h-2"
        />
        <div className="text-xs text-muted-foreground">
          {nesting.efficienza >= 80 ? 'Ottima efficienza' : 
           nesting.efficienza >= 60 ? 'Buona efficienza' : 
           'Efficienza migliorabile'}
        </div>
      </div>
    </div>
  )
} 