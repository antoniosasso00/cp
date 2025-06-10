'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { Separator } from '@/shared/components/ui/separator'

import { 
  Package, 
  Ruler, 
  Weight, 
  RotateCcw,
  Layers,
  Target,
  TrendingUp
} from 'lucide-react'

interface ToolPosition {
  odl_id: number
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean
  part_number?: string
  tool_nome?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore?: string
}

interface NestingToolboxProps {
  toolPositions: ToolPosition[]
  autoclave?: AutoclaveInfo
  canvasWidth: number
  canvasHeight: number
  efficiency?: number
  totalWeight?: number
  totalArea?: number
  odlExcluded?: Array<{
    odl_id: number
    motivo: string
    dettagli?: string
  }>
  className?: string
}

const NestingToolbox: React.FC<NestingToolboxProps> = ({
  toolPositions,
  autoclave,
  canvasWidth,
  canvasHeight,
  efficiency,
  totalWeight,
  totalArea,
  odlExcluded = [],
  className = ''
}) => {
  // Calcola statistiche
  const stats = {
    totalTools: toolPositions.length,
    rotatedTools: toolPositions.filter(t => t.rotated).length,
    totalAreaUsed: toolPositions.reduce((sum, t) => sum + (t.width * t.height), 0),
    totalWeightUsed: toolPositions.reduce((sum, t) => sum + t.peso, 0),
    canvasArea: canvasWidth * canvasHeight,
    excludedCount: odlExcluded.length
  }

  const calculatedEfficiency = stats.canvasArea > 0 ? (stats.totalAreaUsed / stats.canvasArea) * 100 : 0

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Statistiche Principali */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <TrendingUp className="h-4 w-4" />
            Statistiche Nesting
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-green-600">
                {(efficiency || calculatedEfficiency).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600">Efficienza</div>
            </div>
            
            <div className="text-center p-2 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-blue-600">
                {stats.totalTools}
              </div>
              <div className="text-xs text-gray-600">Tool Posizionati</div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Peso Totale:</span>
              <span className="font-medium">{(totalWeight || stats.totalWeightUsed).toFixed(1)} kg</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Area Utilizzata:</span>
              <span className="font-medium">{(stats.totalAreaUsed / 1000000).toFixed(2)} m²</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Tool Ruotati:</span>
              <span className="font-medium">{stats.rotatedTools}/{stats.totalTools}</span>
            </div>
            
            {stats.excludedCount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-600">ODL Esclusi:</span>
                <Badge variant="destructive" className="text-xs">
                  {stats.excludedCount}
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Informazioni Autoclave */}
      {autoclave && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Layers className="h-4 w-4" />
              Autoclave
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Nome:</span>
              <span className="font-medium">{autoclave.nome}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Codice:</span>
              <span className="font-medium">{autoclave.codice}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Dimensioni:</span>
              <span className="font-medium">
                {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
              </span>
            </div>
            
            {autoclave.produttore && (
              <div className="flex justify-between">
                <span className="text-gray-600">Produttore:</span>
                <span className="font-medium">{autoclave.produttore}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Lista Tool Posizionati */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Package className="h-4 w-4" />
            Tool Posizionati ({stats.totalTools})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-64 overflow-y-auto">
            <div className="p-3 space-y-2">
              {toolPositions.map((tool, index) => (
                <div key={tool.odl_id} className="p-2 border rounded-lg text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">ODL {tool.odl_id}</span>
                    {tool.rotated && (
                      <Badge variant="outline" className="text-xs">
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Ruotato
                      </Badge>
                    )}
                  </div>
                  
                  {tool.part_number && (
                    <div className="text-gray-600 text-xs mb-1">
                      {tool.part_number}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Target className="h-3 w-3" />
                      {tool.x.toFixed(0)}, {tool.y.toFixed(0)}
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Ruler className="h-3 w-3" />
                      {tool.width.toFixed(0)}×{tool.height.toFixed(0)}
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Weight className="h-3 w-3" />
                      {tool.peso.toFixed(1)} kg
                    </div>
                    
                    <div className="text-right">
                      #{index + 1}
                    </div>
                  </div>
                </div>
              ))}
                          </div>
            </div>
        </CardContent>
      </Card>

      {/* ODL Esclusi */}
      {odlExcluded.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm text-red-600">
              <Package className="h-4 w-4" />
              ODL Esclusi ({odlExcluded.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-40 overflow-y-auto">
              <div className="p-3 space-y-2">
                {odlExcluded.map((excluded) => (
                  <div key={excluded.odl_id} className="p-2 border border-red-200 rounded-lg text-sm bg-red-50">
                    <div className="font-medium text-red-800">
                      ODL {excluded.odl_id}
                    </div>
                    <div className="text-red-600 text-xs mt-1">
                      {excluded.motivo}
                    </div>
                    {excluded.dettagli && (
                      <div className="text-red-500 text-xs mt-1">
                        {excluded.dettagli}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default NestingToolbox 