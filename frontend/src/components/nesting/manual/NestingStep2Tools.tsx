'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Wrench, CheckCircle, Package, Info, ArrowRight } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { nestingApi, NestingToolsResponse, NestingToolInfo } from '@/lib/api'

interface NestingStep2ToolsProps {
  nestingId: number
  onStepComplete?: (data?: any) => void
  onStepError?: (error: string) => void
  disabled?: boolean
}

export function NestingStep2Tools({ 
  nestingId, 
  onStepComplete, 
  onStepError,
  disabled = false 
}: NestingStep2ToolsProps) {
  const [toolsData, setToolsData] = useState<NestingToolsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Carica i tool del nesting
  useEffect(() => {
    const loadNestingTools = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        const response = await nestingApi.getTools(nestingId)
        setToolsData(response)
        
        // Se non ci sono tool, notifica l'errore
        if (!response.tools || response.tools.length === 0) {
          const errorMsg = "Nessun tool trovato per questo nesting. Assicurati che ci siano ODL associati."
          setError(errorMsg)
          if (onStepError) {
            onStepError(errorMsg)
          }
        }
        
      } catch (error) {
        console.error('❌ Errore nel caricamento dei tool:', error)
        const errorMessage = error instanceof Error ? error.message : 'Errore nel caricamento dei tool'
        setError(errorMessage)
        
        if (onStepError) {
          onStepError(errorMessage)
        }
        
        toast({
          title: "Errore",
          description: errorMessage,
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    if (nestingId) {
      loadNestingTools()
    }
  }, [nestingId, onStepError, toast])

  // Procede al prossimo step
  const handleNextStep = () => {
    if (onStepComplete) {
      onStepComplete({
        step: 'select-tools',
        completed: true,
        tools_count: toolsData?.tools.length || 0,
        tools_data: toolsData?.tools || []
      })
    }
  }

  // Componente per mostrare un singolo tool
  const ToolCard = ({ tool }: { tool: NestingToolInfo }) => (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h4 className="font-medium text-sm">{tool.part_number_tool}</h4>
          {tool.descrizione && (
            <p className="text-xs text-gray-600">{tool.descrizione}</p>
          )}
        </div>
        <Badge variant={tool.disponibile ? "default" : "destructive"} className="text-xs">
          {tool.disponibile ? "Disponibile" : "Non Disponibile"}
        </Badge>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-gray-500">Dimensioni:</span>
          <p className="font-medium">
            {tool.dimensioni.larghezza}×{tool.dimensioni.lunghezza} mm
          </p>
        </div>
        <div>
          <span className="text-gray-500">Area:</span>
          <p className="font-medium">{tool.area_cm2} cm²</p>
        </div>
        <div>
          <span className="text-gray-500">Peso:</span>
          <p className="font-medium">{tool.peso ? `${tool.peso} kg` : 'N/D'}</p>
        </div>
        <div>
          <span className="text-gray-500">Materiale:</span>
          <p className="font-medium">{tool.materiale || 'N/D'}</p>
        </div>
      </div>
      
      <div className="border-t pt-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">ODL #{tool.odl_id}</span>
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Parte:</span>
            <span className="font-medium">{tool.parte_codice}</span>
            <Badge variant="outline" className="text-xs">
              Priorità {tool.priorita}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5" />
            Step 2: Tool Inclusi
          </CardTitle>
          <CardDescription>
            Caricamento dei tool determinati dagli ODL associati...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="grid gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="border rounded-lg p-4">
                  <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-full"></div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !toolsData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5" />
            Step 2: Tool Inclusi
          </CardTitle>
          <CardDescription>
            Tool determinati automaticamente dagli ODL associati
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <Package className="h-4 w-4" />
            <AlertTitle>Problema con i Tool</AlertTitle>
            <AlertDescription>
              {error || "Impossibile caricare i tool per questo nesting."}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="h-5 w-5" />
          Step 2: Tool Inclusi
        </CardTitle>
        <CardDescription>
          🧰 Tool determinati automaticamente dagli ODL associati. Nessuna azione richiesta.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Alert informativo */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Step Informativo</AlertTitle>
          <AlertDescription>
            I tool mostrati qui sotto sono determinati automaticamente in base agli ODL associati 
            all'autoclave selezionata. Non è necessario selezionare manualmente i tool.
          </AlertDescription>
        </Alert>

        {/* Statistiche tool */}
        {toolsData.statistiche_tools && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {toolsData.statistiche_tools.totale_tools}
              </p>
              <p className="text-sm text-gray-600">Tool Totali</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {toolsData.statistiche_tools.tools_disponibili}
              </p>
              <p className="text-sm text-gray-600">Disponibili</p>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">
                {toolsData.statistiche_tools.area_totale.toFixed(1)} cm²
              </p>
              <p className="text-sm text-gray-600">Area Totale</p>
            </div>
          </div>
        )}

        {/* Lista tool */}
        {toolsData.tools.length > 0 ? (
          <div className="space-y-4">
            <h3 className="font-medium text-lg">Tool Inclusi nel Nesting</h3>
            <div className="grid gap-4">
              {toolsData.tools.map((tool) => (
                <ToolCard key={tool.id} tool={tool} />
              ))}
            </div>
          </div>
        ) : (
          <Alert>
            <Package className="h-4 w-4" />
            <AlertTitle>Nessun Tool Trovato</AlertTitle>
            <AlertDescription>
              Non ci sono tool associati a questo nesting. 
              Verifica che l'autoclave abbia ODL associati.
            </AlertDescription>
          </Alert>
        )}

        {/* Informazioni autoclave */}
        {toolsData.autoclave_nome && (
          <div className="border-t pt-4">
            <p className="text-sm text-gray-600">
              <strong>Autoclave:</strong> {toolsData.autoclave_nome}
            </p>
            {toolsData.statistiche_tools.efficienza_area > 0 && (
              <p className="text-sm text-gray-600">
                <strong>Efficienza Area:</strong> {toolsData.statistiche_tools.efficienza_area.toFixed(1)}%
              </p>
            )}
          </div>
        )}

        {/* Pulsante per procedere */}
        <div className="flex justify-end pt-4 border-t">
          <Button
            onClick={handleNextStep}
            disabled={disabled || toolsData.tools.length === 0}
            className="flex items-center gap-2"
            data-nesting-action="confirm"
          >
            Procedi al Layout
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 