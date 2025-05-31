'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, RefreshCw, AlertCircle } from 'lucide-react'
import { NestingParametersPanel, NestingParameters } from '@/components/Nesting/NestingParametersPanel'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToast } from '@/hooks/use-toast'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface ParametersTabProps {
  parameters: NestingParameters
  onParametersChange: (parameters: NestingParameters) => void
  isLoading: boolean
  error?: string | null
  onRetry?: () => void
  onPreview: (params: NestingParameters) => void
}

export function ParametersTab({ 
  parameters, 
  onParametersChange, 
  isLoading,
  error,
  onRetry,
  onPreview
}: ParametersTabProps) {
  const { toast } = useToast()

  const handlePreview = async () => {
    // I parametri vengono gestiti dal componente parent
    onPreview(parameters)
  }

  // Gestione errori con possibilità di retry
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametri Nesting
          </CardTitle>
          <CardDescription>
            Configura i parametri dell'algoritmo di ottimizzazione
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Errore nel caricamento dei parametri: {error}
            </AlertDescription>
          </Alert>
          {onRetry && (
            <div className="mt-4">
              <Button 
                onClick={onRetry} 
                variant="outline" 
                className="flex items-center gap-2"
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Riprova
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // Stato di caricamento
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametri Nesting
          </CardTitle>
          <CardDescription>
            Configura i parametri dell'algoritmo di ottimizzazione
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Guida ai parametri */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">💡 Guida ai Parametri</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li><strong>Distanza minima tool:</strong> Spazio minimo tra i tool nell'autoclave</li>
                <li><strong>Padding bordo:</strong> Margine di sicurezza dai bordi dell'autoclave</li>
                <li><strong>Margine sicurezza peso:</strong> Percentuale di sicurezza sul peso massimo</li>
                <li><strong>Priorità minima:</strong> Priorità minima degli ODL da considerare</li>
                <li><strong>Efficienza minima:</strong> Soglia minima di efficienza per accettare un nesting</li>
              </ul>
            </div>
            
            <EmptyState
              message="Caricamento parametri in corso..."
              description="I parametri di configurazione verranno caricati a breve"
              icon="⏳"
              size="sm"
            />
          </div>
        </CardContent>
      </Card>
    )
  }

  // Fallback quando non ci sono parametri disponibili (senza debug)
  if (!parameters) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametri Nesting
          </CardTitle>
          <CardDescription>
            Configura i parametri dell'algoritmo di ottimizzazione
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            message="Parametri non ancora disponibili"
            description="I parametri di configurazione verranno caricati automaticamente. Se il problema persiste, prova a ricaricare la pagina."
            icon="⚙️"
          />
          {onRetry && (
            <div className="mt-4">
              <Button 
                onClick={onRetry} 
                variant="outline" 
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Ricarica Parametri
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Parametri Nesting
        </CardTitle>
        <CardDescription>
          Configura i parametri dell'algoritmo di ottimizzazione. Questi parametri influenzano come vengono posizionati i tool nelle autoclavi e l'efficienza del nesting.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Spiegazione dei parametri */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">💡 Guida ai Parametri</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li><strong>Distanza minima tool:</strong> Spazio minimo tra i tool nell'autoclave</li>
              <li><strong>Padding bordo:</strong> Margine di sicurezza dai bordi dell'autoclave</li>
              <li><strong>Margine sicurezza peso:</strong> Percentuale di sicurezza sul peso massimo</li>
              <li><strong>Priorità minima:</strong> Priorità minima degli ODL da considerare</li>
              <li><strong>Efficienza minima:</strong> Soglia minima di efficienza per accettare un nesting</li>
            </ul>
          </div>

          {/* Panel dei parametri */}
          <NestingParametersPanel
            parameters={parameters}
            onParametersChange={onParametersChange}
            onPreview={handlePreview}
            isLoading={isLoading}
          />

          {/* Informazioni aggiuntive */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <h4 className="font-medium text-amber-900 mb-2">⚠️ Nota Importante</h4>
            <p className="text-sm text-amber-800">
              Le modifiche ai parametri influenzano tutti i futuri nesting automatici. 
              Assicurati di testare i parametri con una preview prima di utilizzarli per l'ottimizzazione finale.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 