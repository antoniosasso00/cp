'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { 
  Layers,
  TrendingUp,
  Award,
  ExternalLink
} from 'lucide-react'
import { scrollToTopAndFocus } from '@/shared/lib/canvas-utils'

interface BatchResult {
  id: string
  autoclave?: {
    id: number
    nome: string
    codice: string
  }
  autoclave_id: number
  metrics?: {
    efficiency_percentage?: number
  }
  efficiency?: number
  stato?: string
  nome?: string
}

interface MultiBatchData {
  batch_results: BatchResult[]
  total_batches: number
  is_partial_multi_batch?: boolean
  batch_type?: string
}

interface NestingBatchSwitcherProps {
  multiBatchData: MultiBatchData
  currentBatchId: string
  selectedBatchIndex: number
  onBatchSelect: (index: number) => void
  className?: string
}

export const NestingBatchSwitcher: React.FC<NestingBatchSwitcherProps> = ({
  multiBatchData,
  currentBatchId,
  selectedBatchIndex,
  onBatchSelect,
  className = ''
}) => {
  const router = useRouter()

  // Trova il batch con efficienza maggiore
  const bestBatchIndex = multiBatchData.batch_results.reduce((bestIdx, batch, index) => {
    const currentBest = multiBatchData.batch_results[bestIdx]
    const currentEfficiency = batch.metrics?.efficiency_percentage || batch.efficiency || 0
    const bestEfficiency = currentBest.metrics?.efficiency_percentage || currentBest.efficiency || 0
    return currentEfficiency > bestEfficiency ? index : bestIdx
  }, 0)

  const handleBatchSelect = (index: number, batchId: string) => {
    if (index === selectedBatchIndex) return

    // Update local state immediatamente
    onBatchSelect(index)

    // Navigate con scroll to top e focus
    router.push(`/nesting/result/${batchId}?multi=true`)
    
    // Scroll to top e focus canvas
    scrollToTopAndFocus('nesting-canvas-container')
  }

  const getBatchDisplayName = (batch: BatchResult) => {
    return batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}` || batch.nome || `Batch ${batch.id.slice(0, 8)}`
  }

  const getBatchEfficiency = (batch: BatchResult) => {
    return batch.metrics?.efficiency_percentage || batch.efficiency || 0
  }

  const getStateBadge = (stato?: string) => {
    switch (stato?.toLowerCase()) {
      case 'confermato':
        return <Badge variant="default" className="text-xs">Confermato</Badge>
      case 'sospeso':
        return <Badge variant="secondary" className="text-xs">Sospeso</Badge>
      case 'draft':
        return <Badge variant="outline" className="text-xs">Draft</Badge>
      default:
        return null
    }
  }

  if (multiBatchData.total_batches <= 1) {
    return (
      <div className={`text-center py-6 text-gray-500 ${className}`}>
        <Layers className="h-8 w-8 mx-auto mb-2 text-gray-300" />
        <p className="text-sm">Batch singolo</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900 flex items-center gap-2">
          <Layers className="h-4 w-4 text-blue-600" />
          Batch Multipli
        </h4>
        <Badge variant="outline" className="text-xs">
          {multiBatchData.total_batches} disponibili
        </Badge>
      </div>

      <div className="space-y-2">
        {multiBatchData.batch_results.map((batch, index) => {
          const isSelected = index === selectedBatchIndex
          const isBest = index === bestBatchIndex
          const efficiency = getBatchEfficiency(batch)
          const displayName = getBatchDisplayName(batch)

          return (
            <div
              key={batch.id}
              className={`
                p-3 rounded-lg border transition-all cursor-pointer
                ${isSelected 
                  ? 'bg-blue-50 border-blue-200 ring-2 ring-blue-100' 
                  : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                }
              `}
              onClick={() => handleBatchSelect(index, batch.id)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                    {displayName}
                  </span>
                                     {isBest && (
                     <div title="Migliore efficienza">
                       <Award className="h-4 w-4 text-yellow-500" />
                     </div>
                   )}
                </div>
                
                <div className="flex items-center gap-2">
                  {getStateBadge(batch.stato)}
                  {!isSelected && (
                    <ExternalLink className="h-3 w-3 text-gray-400" />
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1 text-gray-600">
                  <TrendingUp className="h-3 w-3" />
                  <span>Efficienza</span>
                </div>
                
                <div className={`font-medium ${
                  efficiency > 70 ? 'text-green-600' :
                  efficiency > 50 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {efficiency.toFixed(1)}%
                </div>
              </div>

              {/* Progress bar efficienza */}
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div 
                    className={`h-1.5 rounded-full transition-all ${
                      efficiency > 70 ? 'bg-green-500' :
                      efficiency > 50 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(efficiency, 100)}%` }}
                  />
                </div>
              </div>

              {batch.autoclave?.codice && (
                <div className="mt-2 text-xs text-gray-500">
                  Codice: {batch.autoclave.codice}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Statistiche Riassuntive */}
      <div className="pt-3 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-gray-500">Efficienza Media:</span>
            <div className="font-medium text-gray-900">
              {(multiBatchData.batch_results.reduce((sum, batch) => 
                sum + getBatchEfficiency(batch), 0) / multiBatchData.batch_results.length
              ).toFixed(1)}%
            </div>
          </div>
          
          <div>
            <span className="text-gray-500">Efficienza Max:</span>
            <div className="font-medium text-green-600">
              {Math.max(...multiBatchData.batch_results.map(getBatchEfficiency)).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NestingBatchSwitcher 