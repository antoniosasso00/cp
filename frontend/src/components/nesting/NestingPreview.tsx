'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw, Package, Gauge, Weight, Layers } from 'lucide-react'
import { nestingApi, NestingPreviewResponse, ODLGroupPreview } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingPreviewProps {
  onRefresh?: () => void
}

export function NestingPreview({ onRefresh }: NestingPreviewProps) {
  const [previewData, setPreviewData] = useState<NestingPreviewResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  const loadPreview = async () => {
    try {
      setIsLoading(true)
      const data = await nestingApi.getPreview({
        include_excluded: true,
        group_by_cycle: true
      })
      setPreviewData(data)
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare la preview del nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadPreview()
  }, [])

  const handleRefresh = () => {
    loadPreview()
    onRefresh?.()
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Preview Nesting
          </CardTitle>
          <CardDescription>
            Caricamento preview degli ODL disponibili...
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-20 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  if (!previewData || !previewData.success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Preview Nesting
          </CardTitle>
          <CardDescription>
            Errore nel caricamento della preview
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">
              {previewData?.message || 'Impossibile caricare la preview'}
            </p>
            <Button onClick={handleRefresh} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Riprova
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Preview Nesting
            </CardTitle>
            <CardDescription>
              {previewData.total_odl_pending} ODL in attesa di nesting, raggruppati per ciclo di cura
            </CardDescription>
          </div>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {previewData.odl_groups.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Nessun ODL in attesa di nesting</p>
          </div>
        ) : (
          previewData.odl_groups.map((group, index) => (
            <ODLGroupCard key={index} group={group} />
          ))
        )}

        {/* Riepilogo autoclavi disponibili */}
        {previewData.available_autoclaves.length > 0 && (
          <div className="border-t pt-6">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Autoclavi Disponibili ({previewData.available_autoclaves.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {previewData.available_autoclaves.map((autoclave) => (
                <div key={autoclave.id} className="p-3 border rounded-lg">
                  <div className="font-medium">{autoclave.nome}</div>
                  <div className="text-sm text-muted-foreground">
                    Area: {autoclave.area_piano.toFixed(0)} cm²
                  </div>
                  {autoclave.max_load_kg && (
                    <div className="text-sm text-muted-foreground">
                      Max: {autoclave.max_load_kg} kg
                    </div>
                  )}
                  <Badge variant="secondary" className="mt-1">
                    {autoclave.stato}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ODLGroupCard({ group }: { group: ODLGroupPreview }) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">{group.ciclo_cura}</h3>
        <Badge variant="outline">
          {group.odl_list.length} ODL
        </Badge>
      </div>

      {/* Statistiche del gruppo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-blue-500" />
          <div>
            <div className="text-sm text-muted-foreground">ODL</div>
            <div className="font-medium">{group.odl_list.length}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-green-500" />
          <div>
            <div className="text-sm text-muted-foreground">Area</div>
            <div className="font-medium">{group.total_area.toFixed(0)} cm²</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Weight className="h-4 w-4 text-orange-500" />
          <div>
            <div className="text-sm text-muted-foreground">Peso</div>
            <div className="font-medium">{group.total_weight.toFixed(1)} kg</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-purple-500" />
          <div>
            <div className="text-sm text-muted-foreground">Autoclavi</div>
            <div className="font-medium">{group.compatible_autoclaves.length}</div>
          </div>
        </div>
      </div>

      {/* Lista ODL nel gruppo */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-muted-foreground">ODL nel gruppo:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {group.odl_list.slice(0, 6).map((odl) => (
            <div key={odl.id} className="text-sm p-2 bg-muted/50 rounded">
              <div className="font-medium">
                ODL #{odl.id} - {odl.parte_codice || 'Parte non specificata'}
              </div>
              <div className="text-sm text-muted-foreground">
                Tool: {odl.tool_nome || 'Tool non specificato'} | Priorità: {odl.priorita}
              </div>
              <div className="text-xs text-muted-foreground">
                {odl.dimensioni.larghezza}×{odl.dimensioni.lunghezza}mm, {odl.dimensioni.peso.toFixed(1)}kg
              </div>
            </div>
          ))}
          {group.odl_list.length > 6 && (
            <div className="text-sm p-2 bg-muted/30 rounded text-center text-muted-foreground">
              +{group.odl_list.length - 6} altri ODL...
            </div>
          )}
        </div>
      </div>

      {/* Autoclavi compatibili */}
      {group.compatible_autoclaves.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Autoclavi compatibili:</h4>
          <div className="flex flex-wrap gap-2">
            {group.compatible_autoclaves.map((autoclave) => (
              <Badge key={autoclave.id} variant="secondary">
                {autoclave.nome}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 