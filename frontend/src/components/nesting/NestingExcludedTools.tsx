'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertTriangle, Package, Info, Eye } from 'lucide-react'
import { nestingApi, NestingDetailResponse, ODLNestingInfo } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingExcludedToolsProps {
  nestingId: number
  onToolClick?: (odl: ODLNestingInfo) => void
  className?: string
}

export function NestingExcludedTools({ 
  nestingId, 
  onToolClick, 
  className = "" 
}: NestingExcludedToolsProps) {
  const [nestingDetails, setNestingDetails] = useState<NestingDetailResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  // Carica i dettagli del nesting per ottenere i tool esclusi
  const loadNestingDetails = async () => {
    try {
      setIsLoading(true)
      const details = await nestingApi.getDetails(nestingId)
      setNestingDetails(details)
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare i dettagli del nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadNestingDetails()
  }, [nestingId])

  // Genera colore per priorità
  const getPriorityColor = (priorita: number) => {
    if (priorita >= 8) return 'bg-red-100 text-red-800'
    if (priorita >= 5) return 'bg-yellow-100 text-yellow-800'
    return 'bg-green-100 text-green-800'
  }

  // Gestisce il click su un tool escluso
  const handleToolClick = (odl: ODLNestingInfo) => {
    if (onToolClick) {
      onToolClick(odl)
    }
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Tool Esclusi
          </CardTitle>
          <CardDescription>
            Caricamento tool esclusi dal nesting...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-32" />
        </CardContent>
      </Card>
    )
  }

  if (!nestingDetails) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Errore Caricamento
          </CardTitle>
          <CardDescription>
            Impossibile caricare i dettagli del nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={loadNestingDetails} variant="outline">
            Riprova
          </Button>
        </CardContent>
      </Card>
    )
  }

  const excludedTools = nestingDetails.odl_esclusi || []

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Tool Esclusi dal Nesting
            </CardTitle>
            <CardDescription>
              {excludedTools.length} tool non inclusi nel layout
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-orange-600">
            {excludedTools.length} esclusi
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {excludedTools.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Tutti i tool sono stati inclusi nel nesting</p>
          </div>
        ) : (
          <>
            {/* Motivi di esclusione */}
            {nestingDetails.motivi_esclusione && nestingDetails.motivi_esclusione.length > 0 && (
              <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <h4 className="font-medium text-orange-800 mb-2 flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Motivi di Esclusione
                </h4>
                <ul className="text-sm text-orange-700 space-y-1">
                  {nestingDetails.motivi_esclusione.map((motivo, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-orange-500 mt-1">•</span>
                      {motivo}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Lista tool esclusi */}
            <div className="space-y-3">
              <h4 className="font-medium text-muted-foreground">Tool Esclusi:</h4>
              <div className="grid gap-3">
                {excludedTools.map((odl) => (
                  <div 
                    key={odl.id} 
                    className="p-4 border rounded-lg bg-red-50 border-red-200 hover:bg-red-100 transition-colors cursor-pointer"
                    onClick={() => handleToolClick(odl)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-red-600">
                          ODL #{odl.id}
                        </Badge>
                        <Badge className={getPriorityColor(odl.priorita)}>
                          Priorità {odl.priorita}
                        </Badge>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-red-700">Parte:</span>
                          <div className="text-red-600">{odl.parte_codice || 'Parte non specificata'}</div>
                        </div>
                        <div>
                          <span className="font-medium text-red-700">Tool:</span>
                          <div className="text-red-600">{odl.tool_nome || 'Tool non specificato'}</div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-red-700">Dimensioni:</span>
                          <div className="text-red-600">
                            {odl.dimensioni.larghezza.toFixed(0)}×{odl.dimensioni.lunghezza.toFixed(0)}mm
                          </div>
                        </div>
                        <div>
                          <span className="font-medium text-red-700">Peso:</span>
                          <div className="text-red-600">{odl.dimensioni.peso.toFixed(1)}kg</div>
                        </div>
                        <div>
                          <span className="font-medium text-red-700">Stato:</span>
                          <div className="text-red-600">{odl.status}</div>
                        </div>
                      </div>
                      
                      {odl.ciclo_cura && (
                        <div className="text-sm">
                          <span className="font-medium text-red-700">Ciclo di cura:</span>
                          <div className="text-red-600">{odl.ciclo_cura}</div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Statistiche tool esclusi */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {excludedTools.length}
                </div>
                <div className="text-sm text-red-700">Tool Esclusi</div>
              </div>
              
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {excludedTools.reduce((sum, odl) => sum + odl.dimensioni.peso, 0).toFixed(1)}kg
                </div>
                <div className="text-sm text-orange-700">Peso Totale</div>
              </div>
              
              <div className="text-center p-3 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {excludedTools.reduce((sum, odl) => sum + (odl.dimensioni.larghezza * odl.dimensioni.lunghezza / 100), 0).toFixed(0)}
                </div>
                <div className="text-sm text-yellow-700">Area cm²</div>
              </div>
              
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.round(excludedTools.reduce((sum, odl) => sum + odl.priorita, 0) / excludedTools.length)}
                </div>
                <div className="text-sm text-purple-700">Priorità Media</div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
} 