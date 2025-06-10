'use client'

import React from 'react'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Package, 
  Ruler, 
  Weight, 
  RotateCcw,
  Target,
  AlertTriangle
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

interface NestingToolListProps {
  toolPositions: ToolPosition[]
  odlExcluded?: Array<{
    odl_id: number
    motivo: string
    dettagli?: string
  }>
  onToolSelect?: (odlId: number) => void
  className?: string
}

export const NestingToolList: React.FC<NestingToolListProps> = ({
  toolPositions,
  odlExcluded = [],
  onToolSelect,
  className = ''
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Tool Posizionati */}
      {toolPositions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              <Package className="h-4 w-4 text-green-600" />
              Tool Posizionati
            </h4>
            <Badge variant="outline" className="text-xs">
              {toolPositions.length}
            </Badge>
          </div>
          
          <div className="max-h-80 overflow-y-auto space-y-2">
            {toolPositions.map((tool, index) => (
              <div 
                key={tool.odl_id} 
                className="p-3 border rounded-lg bg-white hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => onToolSelect?.(tool.odl_id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">ODL {tool.odl_id}</span>
                    <Badge variant="outline" className="text-xs">
                      #{index + 1}
                    </Badge>
                  </div>
                  
                  {tool.rotated && (
                    <Badge variant="secondary" className="text-xs">
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Ruotato
                    </Badge>
                  )}
                </div>
                
                {(tool.part_number || tool.tool_nome) && (
                  <div className="text-sm text-gray-600 mb-2">
                    {tool.part_number && (
                      <div className="font-mono">{tool.part_number}</div>
                    )}
                    {tool.tool_nome && (
                      <div className="text-xs">{tool.tool_nome}</div>
                    )}
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Target className="h-3 w-3" />
                    <span>Pos: {tool.x.toFixed(0)}, {tool.y.toFixed(0)}</span>
                  </div>
                  
                  <div className="flex items-center gap-1 text-gray-500">
                    <Ruler className="h-3 w-3" />
                    <span>{tool.width.toFixed(0)}×{tool.height.toFixed(0)}</span>
                  </div>
                  
                  <div className="flex items-center gap-1 text-gray-500">
                    <Weight className="h-3 w-3" />
                    <span>{tool.peso.toFixed(1)} kg</span>
                  </div>
                  
                  <div className="text-right text-xs text-gray-400">
                    Area: {((tool.width * tool.height) / 1000000).toFixed(3)} m²
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ODL Esclusi */}
      {odlExcluded.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              ODL Esclusi
            </h4>
            <Badge variant="destructive" className="text-xs">
              {odlExcluded.length}
            </Badge>
          </div>
          
          <div className="max-h-40 overflow-y-auto space-y-2">
            {odlExcluded.map((excluded) => (
              <div 
                key={excluded.odl_id} 
                className="p-3 border border-red-200 rounded-lg bg-red-50"
              >
                <div className="font-medium text-red-800 mb-1">
                  ODL {excluded.odl_id}
                </div>
                <div className="text-red-600 text-sm mb-1">
                  {excluded.motivo}
                </div>
                {excluded.dettagli && (
                  <div className="text-red-500 text-xs">
                    {excluded.dettagli}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messaggio vuoto */}
      {toolPositions.length === 0 && odlExcluded.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Package className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Nessun tool da visualizzare</p>
        </div>
      )}
    </div>
  )
}

export default NestingToolList 