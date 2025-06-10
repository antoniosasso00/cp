'use client'

import React, { useState, useCallback } from 'react'
import CanvasWrapper, { 
  Layer, 
  Rect, 
  Group,
  CanvasLoadingPlaceholder,
  useClientMount 
} from '@/shared/components/canvas/CanvasWrapper'
import { GridLayer } from './grid-layer'
import { ToolRect } from './tool-rect'
import { NestingControls, useNestingControls } from './nesting-controls'
import { AutoclaveHeader } from './autoclave-info-card'
import { cn } from '@/shared/lib/utils'
import type { NestingCanvasProps, ToolPosition } from './types'

// Normalize tool data utility
const normalizeToolData = (tool: ToolPosition): ToolPosition => {
  return {
    ...tool,
    x: Number(tool.x) || 0,
    y: Number(tool.y) || 0,
    width: Number(tool.width) || 50,
    height: Number(tool.height) || 50,
    peso: Number(tool.peso) || 0,
    rotated: Boolean(tool.rotated === true || tool.rotated === 'true'),
    excluded: Boolean(tool.excluded)
  }
}

export const NestingCanvas: React.FC<NestingCanvasProps> = ({
  batchData,
  className,
  showControls = true,
  showGrid = true,
  showRuler = true,
  onToolClick
}) => {
  const isClientMounted = useClientMount()
  const [selectedToolId, setSelectedToolId] = useState<number | null>(null)
  
  // Controls state
  const {
    showGrid: gridVisible,
    showRuler: rulerVisible,
    showTooltips,
    zoom,
    handleZoomIn,
    handleZoomOut,
    handleZoomReset,
    handleToggleGrid,
    handleToggleRuler,
    handleToggleTooltips,
    setZoom
  } = useNestingControls({
    showGrid,
    showRuler,
    showTooltips: true,
    zoom: 1
  })

  // Validation
  if (!batchData?.configurazione_json || !batchData.autoclave) {
    return (
      <div className={cn('flex items-center justify-center h-64 border rounded-lg', className)}>
        <p className="text-muted-foreground">Dati batch non disponibili</p>
      </div>
    )
  }

  const { configurazione_json, autoclave, metrics } = batchData
  const { canvas_width, canvas_height, tool_positions } = configurazione_json

  // Normalize and validate data
  if (!canvas_width || !canvas_height || !tool_positions) {
    return (
      <div className={cn('flex items-center justify-center h-64 border rounded-lg', className)}>
        <p className="text-muted-foreground">Configurazione canvas non valida</p>
      </div>
    )
  }

  const normalizedTools = tool_positions.map(normalizeToolData)
  const efficiency = metrics?.efficiency_percentage || 0

  // Tool click handler
  const handleToolClick = useCallback((toolId: number) => {
    setSelectedToolId(toolId === selectedToolId ? null : toolId)
    onToolClick?.(toolId)
  }, [selectedToolId, onToolClick])

  // Loading state
  if (!isClientMounted) {
    return (
      <div className={cn('h-96', className)}>
        <CanvasLoadingPlaceholder />
      </div>
    )
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with autoclave info */}
      <AutoclaveHeader 
        autoclave={autoclave}
        efficiency={efficiency}
      />

      {/* Controls */}
      {showControls && (
        <div className="flex justify-between items-center">
          <NestingControls
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomReset={handleZoomReset}
            onToggleGrid={handleToggleGrid}
            onToggleRuler={handleToggleRuler}
            onToggleTooltips={handleToggleTooltips}
            showGrid={gridVisible}
            showRuler={rulerVisible}
            showTooltips={showTooltips}
            zoom={zoom}
          />
          
          {/* Tool info */}
          <div className="text-sm text-muted-foreground">
            {normalizedTools.length} tool • {efficiency.toFixed(1)}% efficienza
          </div>
        </div>
      )}

      {/* Canvas */}
      <div className="border rounded-lg overflow-hidden bg-white">
        <CanvasWrapper
          width={canvas_width}
          height={canvas_height}
          scaleX={zoom}
          scaleY={zoom}
          className="max-h-[600px]"
        >
          <Layer>
            {/* Autoclave bounds */}
            <Rect
              x={0}
              y={0}
              width={autoclave.lunghezza}
              height={autoclave.larghezza_piano}
              fill="#f8fafc"
              stroke="#e2e8f0"
              strokeWidth={2}
            />

            {/* Grid layer */}
            {gridVisible && (
              <GridLayer
                width={autoclave.lunghezza}
                height={autoclave.larghezza_piano}
                showRuler={rulerVisible}
                gridSpacing={100}
              />
            )}

            {/* Tools */}
            <Group name="tools">
              {normalizedTools.map((tool) => (
                <ToolRect
                  key={tool.odl_id}
                  tool={tool}
                  onClick={() => handleToolClick(tool.odl_id)}
                  isSelected={selectedToolId === tool.odl_id}
                  autoclaveWidth={autoclave.lunghezza}
                  autoclaveHeight={autoclave.larghezza_piano}
                  showTooltips={showTooltips}
                />
              ))}
            </Group>
          </Layer>
        </CanvasWrapper>
      </div>

      {/* Legend/Status */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Valido</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>Ruotato</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <span>Fuori Limiti</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>Escluso</span>
          </div>
        </div>
        
        {selectedToolId && (
          <span>
            Tool selezionato: ODL {selectedToolId}
          </span>
        )}
      </div>
    </div>
  )
}

// Simplified version without controls
export const SimpleNestingCanvas: React.FC<NestingCanvasProps> = ({
  batchData,
  className,
  onToolClick
}) => {
  return (
    <NestingCanvas
      batchData={batchData}
      className={className}
      showControls={false}
      showGrid={false}
      showRuler={false}
      onToolClick={onToolClick}
    />
  )
}

// Overview version for thumbnails
export const NestingCanvasOverview: React.FC<NestingCanvasProps & {
  maxWidth?: number
  maxHeight?: number
}> = ({
  batchData,
  className,
  maxWidth = 200,
  maxHeight = 150,
  onToolClick
}) => {
  const isClientMounted = useClientMount()

  if (!isClientMounted || !batchData?.configurazione_json || !batchData.autoclave) {
    return (
      <div className={cn('flex items-center justify-center bg-gray-100 rounded', className)}>
        <span className="text-xs text-muted-foreground">N/A</span>
      </div>
    )
  }

  const { configurazione_json, autoclave } = batchData
  const { canvas_width, canvas_height, tool_positions } = configurazione_json

  if (!canvas_width || !canvas_height || !tool_positions) {
    return null
  }

  const normalizedTools = tool_positions.map(normalizeToolData)
  
  // Calculate scale to fit within maxWidth/maxHeight
  const scaleX = maxWidth / autoclave.lunghezza
  const scaleY = maxHeight / autoclave.larghezza_piano
  const scale = Math.min(scaleX, scaleY, 1)

  const scaledWidth = autoclave.lunghezza * scale
  const scaledHeight = autoclave.larghezza_piano * scale

  return (
    <div className={cn('inline-block border rounded bg-white', className)}>
             <CanvasWrapper
         width={scaledWidth}
         height={scaledHeight}
         scaleX={1}
         scaleY={1}
         className="block"
       >
        <Layer>
          {/* Autoclave bounds */}
          <Rect
            x={0}
            y={0}
            width={scaledWidth}
            height={scaledHeight}
            fill="#f8fafc"
            stroke="#e2e8f0"
            strokeWidth={1}
          />

          {/* Tools (simplified) */}
          {normalizedTools.map((tool) => (
            <Rect
              key={tool.odl_id}
              x={tool.x * scale}
              y={tool.y * scale}
              width={tool.width * scale}
              height={tool.height * scale}
              fill={tool.excluded ? '#ef4444' : tool.rotated ? '#eab308' : '#22c55e'}
              stroke="#ffffff"
              strokeWidth={0.5}
              onClick={() => onToolClick?.(tool.odl_id)}
            />
          ))}
        </Layer>
      </CanvasWrapper>
    </div>
  )
} 