'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Grid3X3, 
  Ruler, 
  MessageSquare, 
  Maximize2,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { NestingControlsProps } from './types'

export const NestingControls: React.FC<NestingControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onToggleGrid,
  onToggleRuler,
  onToggleTooltips,
  onFullscreen,
  showGrid,
  showRuler,
  showTooltips,
  zoom
}) => {
  const formatZoom = (zoomLevel: number) => {
    return `${Math.round(zoomLevel * 100)}%`
  }

  return (
    <div className="flex items-center gap-2 p-2 bg-white border rounded-lg shadow-sm">
      {/* Zoom Controls */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomOut}
          disabled={zoom <= 0.1}
          className="h-8 w-8 p-0"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomReset}
          className="h-8 px-2 min-w-[60px] font-mono text-xs"
          title="Reset Zoom"
        >
          {formatZoom(zoom)}
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomIn}
          disabled={zoom >= 3}
          className="h-8 w-8 p-0"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
      </div>

      {/* View Controls */}
      <div className="flex items-center gap-1 pr-2 border-r">
        <Button
          variant={showGrid ? "default" : "outline"}
          size="sm"
          onClick={onToggleGrid}
          className="h-8 w-8 p-0"
          title={showGrid ? "Nascondi Griglia" : "Mostra Griglia"}
        >
          <Grid3X3 className="h-4 w-4" />
        </Button>
        
        <Button
          variant={showRuler ? "default" : "outline"}
          size="sm"
          onClick={onToggleRuler}
          className="h-8 w-8 p-0"
          title={showRuler ? "Nascondi Righello" : "Mostra Righello"}
        >
          <Ruler className="h-4 w-4" />
        </Button>
        
        <Button
          variant={showTooltips ? "default" : "outline"}
          size="sm"
          onClick={onToggleTooltips}
          className="h-8 w-8 p-0"
          title={showTooltips ? "Nascondi Tooltip" : "Mostra Tooltip"}
        >
          {showTooltips ? (
            <Eye className="h-4 w-4" />
          ) : (
            <EyeOff className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Fullscreen Control */}
      {onFullscreen && (
        <Button
          variant="outline"
          size="sm"
          onClick={onFullscreen}
          className="h-8 w-8 p-0"
          title="Modalità Fullscreen"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  )
}

// Simplified version with just zoom controls
export const SimpleNestingControls: React.FC<{
  onZoomIn: () => void
  onZoomOut: () => void
  onZoomReset: () => void
  zoom: number
  className?: string
}> = ({ onZoomIn, onZoomOut, onZoomReset, zoom, className }) => {
  const formatZoom = (zoomLevel: number) => {
    return `${Math.round(zoomLevel * 100)}%`
  }

  return (
    <div className={cn("flex items-center gap-1 p-1 bg-white border rounded-md shadow-sm", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={onZoomOut}
        disabled={zoom <= 0.1}
        className="h-7 w-7 p-0"
      >
        <ZoomOut className="h-3 w-3" />
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={onZoomReset}
        className="h-7 px-2 min-w-[50px] font-mono text-xs"
      >
        {formatZoom(zoom)}
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={onZoomIn}
        disabled={zoom >= 3}
        className="h-7 w-7 p-0"
      >
        <ZoomIn className="h-3 w-3" />
      </Button>
    </div>
  )
}

// Controls state hook for managing control state
export const useNestingControls = (initialState?: {
  showGrid?: boolean
  showRuler?: boolean
  showTooltips?: boolean
  zoom?: number
}) => {
  const [showGrid, setShowGrid] = React.useState(initialState?.showGrid ?? true)
  const [showRuler, setShowRuler] = React.useState(initialState?.showRuler ?? true)
  const [showTooltips, setShowTooltips] = React.useState(initialState?.showTooltips ?? true)
  const [zoom, setZoom] = React.useState(initialState?.zoom ?? 1)

  const handleZoomIn = React.useCallback(() => {
    setZoom(prev => Math.min(prev * 1.2, 3))
  }, [])

  const handleZoomOut = React.useCallback(() => {
    setZoom(prev => Math.max(prev / 1.2, 0.1))
  }, [])

  const handleZoomReset = React.useCallback(() => {
    setZoom(1)
  }, [])

  const handleToggleGrid = React.useCallback(() => {
    setShowGrid(prev => !prev)
  }, [])

  const handleToggleRuler = React.useCallback(() => {
    setShowRuler(prev => !prev)
  }, [])

  const handleToggleTooltips = React.useCallback(() => {
    setShowTooltips(prev => !prev)
  }, [])

  return {
    showGrid,
    showRuler,
    showTooltips,
    zoom,
    handleZoomIn,
    handleZoomOut,
    handleZoomReset,
    handleToggleGrid,
    handleToggleRuler,
    handleToggleTooltips,
    setZoom
  }
} 