'use client'

import React from 'react'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Settings, 
  Ruler, 
  Target, 
  RotateCw,
  CheckCircle,
  XCircle
} from 'lucide-react'

interface BatchNestingResult {
  parametri?: {
    padding_mm: number
    min_distance_mm: number
    // priorita_area rimosso (non utilizzato dall'algoritmo)
  }
  configurazione_json: {
    tool_positions: any[]
  } | null
}

interface BatchParametersProps {
  batch: BatchNestingResult
}

export default function BatchParameters({ batch }: BatchParametersProps) {
  const { parametri } = batch
  const toolsRotated = batch.configurazione_json?.tool_positions?.filter(tool => tool.rotated)?.length || 0
  const totalTools = batch.configurazione_json?.tool_positions?.length || 0

  if (!parametri) {
    return (
      <div className="text-center py-6 text-gray-500">
        <Settings className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Parametri non disponibili per questo batch</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h4 className="font-medium text-sm text-gray-700 flex items-center gap-2">
        <Settings className="h-4 w-4" />
        Configurazione Algoritmo
      </h4>

      {/* Parametri principali */}
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded border">
          <div className="flex items-center gap-2">
            <Ruler className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium">Padding</span>
          </div>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {parametri.padding_mm} mm
          </Badge>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded border">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium">Distanza Minima</span>
          </div>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            {parametri.min_distance_mm} mm
          </Badge>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded border">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium">Algoritmo</span>
          </div>
          <Badge 
            variant="outline" 
            className="bg-purple-50 text-purple-700 border-purple-200"
          >
            <div className="flex items-center gap-1">
              <Target className="h-3 w-3" />
              OR-Tools CP-SAT Aerospace
            </div>
          </Badge>
        </div>
      </div>

      {/* Statistiche rotazioni */}
      {totalTools > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-sm text-gray-700 flex items-center gap-2">
            <RotateCw className="h-4 w-4" />
            Rotazioni Applicate
          </h4>
          
          <div className="p-3 bg-gray-50 rounded border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm">Tool Ruotati</span>
              <span className="font-semibold">{toolsRotated} / {totalTools}</span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all" 
                style={{ width: `${(toolsRotated / totalTools) * 100}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between mt-2 text-xs text-gray-600">
              <span>0%</span>
              <span className="font-medium">
                {((toolsRotated / totalTools) * 100).toFixed(0)}% ruotati
              </span>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}

      {/* Spiegazioni parametri */}
      <div className="space-y-2">
        <h4 className="font-medium text-sm text-gray-700">Dettagli Configurazione</h4>
        
        <div className="text-xs text-gray-600 space-y-1">
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-blue-400 rounded-full mt-1 flex-shrink-0" />
            <span><strong>Padding:</strong> Spazio minimo dai bordi dell'autoclave</span>
          </div>
          
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full mt-1 flex-shrink-0" />
            <span><strong>Distanza Minima:</strong> Spazio tra strumenti adiacenti</span>
          </div>
          
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full mt-1 flex-shrink-0" />
            <span>
              <strong>Algoritmo:</strong> OR-Tools CP-SAT con ottimizzazioni aerospace per massima efficienza
            </span>
          </div>
        </div>
      </div>
    </div>
  )
} 