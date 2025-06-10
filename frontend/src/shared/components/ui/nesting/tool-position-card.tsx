'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { RotateCw, Package, Weight, Ruler } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { ToolPositionCardProps } from './types'

export const ToolPositionCard: React.FC<ToolPositionCardProps> = ({
  tool,
  onClick,
  selected = false,
  className
}) => {
  // Normalize tool data
  const normalizedTool = {
    ...tool,
    x: Number(tool.x) || 0,
    y: Number(tool.y) || 0,
    width: Number(tool.width) || 50,
    height: Number(tool.height) || 50,
    peso: Number(tool.peso) || 0,
    rotated: Boolean(tool.rotated === true || tool.rotated === 'true'),
    excluded: Boolean(tool.excluded)
  }

  // Calculate area in cm²
  const areaInMm2 = normalizedTool.width * normalizedTool.height
  const areaInCm2 = (areaInMm2 / 100).toFixed(1)

  // Status badge
  const getStatusBadge = () => {
    if (normalizedTool.excluded) {
      return <Badge variant="destructive" className="text-xs">Escluso</Badge>
    }
    if (normalizedTool.rotated) {
      return <Badge variant="secondary" className="text-xs">Ruotato</Badge>
    }
    return <Badge variant="default" className="text-xs">Valido</Badge>
  }

  return (
    <Card 
      className={cn(
        'cursor-pointer transition-all duration-200 hover:shadow-md',
        selected && 'ring-2 ring-blue-500 shadow-md',
        normalizedTool.excluded && 'opacity-75',
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">
            ODL {normalizedTool.odl_id}
          </CardTitle>
          {getStatusBadge()}
        </div>
        {normalizedTool.part_number && (
          <p className="text-xs text-muted-foreground truncate">
            {normalizedTool.part_number}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="pt-0 space-y-3">
        {/* Position */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">X:</span>
            <span className="font-mono">{normalizedTool.x}mm</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Y:</span>
            <span className="font-mono">{normalizedTool.y}mm</span>
          </div>
        </div>

        {/* Dimensions */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs">
            <Ruler className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">Dimensioni:</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <span className="font-mono">{normalizedTool.width} × {normalizedTool.height} mm</span>
            <span className="font-mono text-muted-foreground">{areaInCm2} cm²</span>
          </div>
        </div>

        {/* Weight */}
        {normalizedTool.peso > 0 && (
          <div className="flex items-center gap-1 text-xs">
            <Weight className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">Peso:</span>
            <span className="font-mono">{normalizedTool.peso} kg</span>
          </div>
        )}

        {/* Tool name */}
        {normalizedTool.tool_nome && (
          <div className="flex items-center gap-1 text-xs">
            <Package className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground truncate">{normalizedTool.tool_nome}</span>
          </div>
        )}

        {/* Rotation indicator */}
        {normalizedTool.rotated && (
          <div className="flex items-center gap-1 text-xs text-amber-600">
            <RotateCw className="h-3 w-3" />
            <span>Tool ruotato</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Compact version for lists
export const CompactToolPositionCard: React.FC<ToolPositionCardProps> = ({
  tool,
  onClick,
  selected = false,
  className
}) => {
  const normalizedTool = {
    ...tool,
    x: Number(tool.x) || 0,
    y: Number(tool.y) || 0,
    width: Number(tool.width) || 50,
    height: Number(tool.height) || 50,
    peso: Number(tool.peso) || 0,
    rotated: Boolean(tool.rotated === true || tool.rotated === 'true'),
    excluded: Boolean(tool.excluded)
  }

  const getStatusColor = () => {
    if (normalizedTool.excluded) return 'border-l-red-500 bg-red-50'
    if (normalizedTool.rotated) return 'border-l-amber-500 bg-amber-50'
    return 'border-l-green-500 bg-green-50'
  }

  return (
    <div 
      className={cn(
        'p-3 border-l-4 cursor-pointer transition-all duration-200 hover:shadow-sm',
        getStatusColor(),
        selected && 'ring-2 ring-blue-500',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">ODL {normalizedTool.odl_id}</span>
          {normalizedTool.rotated && <RotateCw className="h-3 w-3 text-amber-600" />}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-mono">
            {normalizedTool.x},{normalizedTool.y}
          </span>
          <span className="font-mono">
            {normalizedTool.width}×{normalizedTool.height}
          </span>
        </div>
      </div>
      
      {normalizedTool.part_number && (
        <p className="text-xs text-muted-foreground mt-1 truncate">
          {normalizedTool.part_number}
        </p>
      )}
    </div>
  )
} 