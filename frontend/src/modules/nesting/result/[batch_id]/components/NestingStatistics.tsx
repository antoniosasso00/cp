'use client'

import React from 'react'
import { Badge } from '@/shared/components/ui/badge'
import { 
  TrendingUp,
  Package,
  Weight,
  Layers,
  Target
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

interface NestingStatisticsProps {
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
}

export const NestingStatistics: React.FC<NestingStatisticsProps> = ({
  toolPositions,
  autoclave,
  canvasWidth,
  canvasHeight,
  efficiency,
  totalWeight,
  totalArea,
  odlExcluded = []
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
    <div className="space-y-6">
      {/* Statistiche Principali in Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="text-2xl font-bold text-green-600 mb-1">
            {(efficiency || calculatedEfficiency).toFixed(1)}%
          </div>
          <div className="text-sm text-green-700 flex items-center justify-center gap-1">
            <TrendingUp className="h-4 w-4" />
            Efficienza
          </div>
        </div>
        
        <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-2xl font-bold text-blue-600 mb-1">
            {stats.totalTools}
          </div>
          <div className="text-sm text-blue-700 flex items-center justify-center gap-1">
            <Package className="h-4 w-4" />
            Tool Posizionati
          </div>
        </div>

        <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div className="text-2xl font-bold text-purple-600 mb-1">
            {(totalWeight || stats.totalWeightUsed).toFixed(1)}
          </div>
          <div className="text-sm text-purple-700 flex items-center justify-center gap-1">
            <Weight className="h-4 w-4" />
            Peso (kg)
          </div>
        </div>

        <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
          <div className="text-2xl font-bold text-orange-600 mb-1">
            {(stats.totalAreaUsed / 1000000).toFixed(2)}
          </div>
          <div className="text-sm text-orange-700 flex items-center justify-center gap-1">
            <Target className="h-4 w-4" />
            Area (m²)
          </div>
        </div>
      </div>

      {/* Dettagli Aggiuntivi */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Statistiche Dettagliate */}
        <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Dettagli Nesting
          </h4>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Tool Ruotati:</span>
              <span className="font-medium">{stats.rotatedTools}/{stats.totalTools}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Area Canvas:</span>
              <span className="font-medium">{(stats.canvasArea / 1000000).toFixed(2)} m²</span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">Spazio Libero:</span>
              <span className="font-medium">
                {((stats.canvasArea - stats.totalAreaUsed) / 1000000).toFixed(2)} m²
              </span>
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
        </div>

        {/* Informazioni Autoclave */}
        {autoclave && (
          <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Autoclave
            </h4>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-700">Nome:</span>
                <span className="font-medium text-blue-900">{autoclave.nome}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-blue-700">Codice:</span>
                <span className="font-medium text-blue-900">{autoclave.codice}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-blue-700">Dimensioni:</span>
                <span className="font-medium text-blue-900">
                  {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
                </span>
              </div>
              
              {autoclave.produttore && (
                <div className="flex justify-between">
                  <span className="text-blue-700">Produttore:</span>
                  <span className="font-medium text-blue-900">{autoclave.produttore}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default NestingStatistics 