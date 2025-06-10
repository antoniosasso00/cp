'use client'

import { useEffect, useRef } from 'react'

interface ToolPosition {
  x: number
  y: number
  width: number
  height: number
  rotated?: boolean
  part_number_tool?: string
  part_number?: string
}

interface AutoclaveInfo {
  nome: string
  codice?: string
  lunghezza: number
  larghezza_piano: number
}

interface BatchCanvasData {
  id: string
  configurazione_json?: {
    tool_positions?: ToolPosition[]
    canvas_width?: number
    canvas_height?: number
  }
  autoclave?: AutoclaveInfo
  metrics?: {
    efficiency_percentage: number
    total_weight_kg: number
    positioned_tools: number
    excluded_tools: number
  }
}

interface NestingCanvasProps {
  batchData: BatchCanvasData
}

export default function NestingCanvas({ batchData }: NestingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current || !batchData.autoclave) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Canvas dimensions
    const canvasWidth = 800
    const canvasHeight = 600
    canvas.width = canvasWidth
    canvas.height = canvasHeight

    // Autoclave dimensions
    const autoclaveWidth = batchData.autoclave.lunghezza || 1000
    const autoclaveHeight = batchData.autoclave.larghezza_piano || 800

    // Calculate scale to fit autoclave in canvas with padding
    const padding = 40
    const scaleX = (canvasWidth - 2 * padding) / autoclaveWidth
    const scaleY = (canvasHeight - 2 * padding) / autoclaveHeight
    const scale = Math.min(scaleX, scaleY)

    // Calculate offset to center autoclave
    const offsetX = (canvasWidth - autoclaveWidth * scale) / 2
    const offsetY = (canvasHeight - autoclaveHeight * scale) / 2

    // Clear canvas
    ctx.clearRect(0, 0, canvasWidth, canvasHeight)

    // Draw autoclave background
    ctx.fillStyle = '#f8f9fa'
    ctx.strokeStyle = '#dee2e6'
    ctx.lineWidth = 2
    ctx.fillRect(offsetX, offsetY, autoclaveWidth * scale, autoclaveHeight * scale)
    ctx.strokeRect(offsetX, offsetY, autoclaveWidth * scale, autoclaveHeight * scale)

    // Draw grid
    ctx.strokeStyle = '#e9ecef'
    ctx.lineWidth = 1
    const gridSize = 100 * scale // 100mm grid
    
    // Vertical lines
    for (let x = gridSize; x < autoclaveWidth * scale; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(offsetX + x, offsetY)
      ctx.lineTo(offsetX + x, offsetY + autoclaveHeight * scale)
      ctx.stroke()
    }
    
    // Horizontal lines
    for (let y = gridSize; y < autoclaveHeight * scale; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(offsetX, offsetY + y)
      ctx.lineTo(offsetX + autoclaveWidth * scale, offsetY + y)
      ctx.stroke()
    }

    // Draw tools
    const toolPositions = batchData.configurazione_json?.tool_positions || []
    
    toolPositions.forEach((tool, index) => {
      if (tool.x == null || tool.y == null || tool.width == null || tool.height == null) return

      const toolX = offsetX + tool.x * scale
      const toolY = offsetY + tool.y * scale
      const toolWidth = tool.width * scale
      const toolHeight = tool.height * scale

      // Draw tool rectangle
      ctx.fillStyle = tool.rotated ? '#d4edda' : '#cce5ff'
      ctx.strokeStyle = '#495057'
      ctx.lineWidth = 1.5
      
      ctx.fillRect(toolX, toolY, toolWidth, toolHeight)
      ctx.strokeRect(toolX, toolY, toolWidth, toolHeight)

      // Draw tool label
      ctx.fillStyle = '#212529'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      
      const centerX = toolX + toolWidth / 2
      const centerY = toolY + toolHeight / 2
      
      const label = tool.part_number_tool || tool.part_number || `T${index + 1}`
      
      // Add background for text readability
      const textMetrics = ctx.measureText(label)
      const textPadding = 4
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
      ctx.fillRect(
        centerX - textMetrics.width / 2 - textPadding,
        centerY - 8,
        textMetrics.width + 2 * textPadding,
        16
      )
      
      ctx.fillStyle = '#212529'
      ctx.fillText(label, centerX, centerY)
    })

    // Draw title and info
    ctx.fillStyle = '#495057'
    ctx.font = 'bold 16px Arial'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(
      `${batchData.autoclave.nome} (${autoclaveWidth}×${autoclaveHeight}mm)`,
      10,
      10
    )

    // Draw metrics
    if (batchData.metrics) {
      ctx.font = '14px Arial'
      ctx.fillStyle = '#6c757d'
      const metricsY = 35
      ctx.fillText(
        `Efficienza: ${batchData.metrics.efficiency_percentage.toFixed(1)}% | ` +
        `Tool: ${batchData.metrics.positioned_tools} | ` +
        `Peso: ${batchData.metrics.total_weight_kg.toFixed(1)}kg`,
        10,
        metricsY
      )
    }

    // Draw scale reference
    ctx.strokeStyle = '#495057'
    ctx.lineWidth = 2
    const scaleRefX = canvasWidth - 150
    const scaleRefY = canvasHeight - 30
    const scaleRefLength = 100 * scale // 100mm reference
    
    ctx.beginPath()
    ctx.moveTo(scaleRefX, scaleRefY)
    ctx.lineTo(scaleRefX + scaleRefLength, scaleRefY)
    ctx.stroke()
    
    // Scale labels
    ctx.font = '12px Arial'
    ctx.textAlign = 'center'
    ctx.fillStyle = '#495057'
    ctx.fillText('100mm', scaleRefX + scaleRefLength / 2, scaleRefY + 15)

  }, [batchData])

  if (!batchData.autoclave) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 border rounded-lg">
        <p className="text-gray-500">Nessun dato autoclave disponibile</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <canvas
        ref={canvasRef}
        className="w-full h-auto border rounded-lg shadow-sm"
        style={{ maxHeight: '600px' }}
      />
      
      {/* Info panel */}
      <div className="mt-4 p-3 bg-muted rounded-lg text-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="font-medium">Dimensioni:</span>
            <br />
            {batchData.autoclave.lunghezza}×{batchData.autoclave.larghezza_piano}mm
          </div>
          {batchData.metrics && (
            <>
              <div>
                <span className="font-medium">Efficienza:</span>
                <br />
                {batchData.metrics.efficiency_percentage.toFixed(1)}%
              </div>
              <div>
                <span className="font-medium">Tool:</span>
                <br />
                {batchData.metrics.positioned_tools} posizionati
              </div>
              <div>
                <span className="font-medium">Peso:</span>
                <br />
                {batchData.metrics.total_weight_kg.toFixed(1)}kg
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
} 