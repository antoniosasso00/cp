'use client'

import React, { useRef, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// 🎯 Interfacce per nesting 2L
interface ToolPosition2L {
  odl_id: number
  tool_id: number
  x: number
  y: number
  width: number
  height: number
  rotated: boolean
  weight_kg: number
  level: number // 0 = piano base, 1 = su cavalletti
  z_position: number
  lines_used: number
  part_number?: string
  descrizione_breve?: string
  numero_odl?: string
}

interface Cavalletto {
  x: number
  y: number
  width: number
  height: number
  tool_odl_id: number
  tool_id?: number
  sequence_number: number
  center_x: number
  center_y: number
  support_area_mm2: number
  height_mm: number
  load_capacity_kg: number
}

interface NestingCanvas2LProps {
  positioned_tools: ToolPosition2L[]
  cavalletti: Cavalletto[]
  canvas_width: number
  canvas_height: number
  className?: string
  showLevelFilter?: boolean
  onToolClick?: (tool: ToolPosition2L) => void
  onStandClick?: (stand: Cavalletto) => void
}

export const NestingCanvas2L: React.FC<NestingCanvas2LProps> = ({
  positioned_tools,
  cavalletti,
  canvas_width,
  canvas_height,
  className = '',
  showLevelFilter = true,
  onToolClick,
  onStandClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedLevel, setSelectedLevel] = useState<'all' | 0 | 1>('all')
  const [zoom, setZoom] = useState(1)
  const [showGrid, setShowGrid] = useState(true)
  const [showStands, setShowStands] = useState(true)
  const [selectedTool, setSelectedTool] = useState<ToolPosition2L | null>(null)

  // 🎨 Filtro tool per livello
  const getFilteredTools = () => {
    if (selectedLevel === 'all') return positioned_tools
    return positioned_tools.filter(tool => tool.level === selectedLevel)
  }

  // 🎨 Filtro cavalletti per livello
  const getFilteredStands = () => {
    if (!showStands) return []
    if (selectedLevel === 'all') return cavalletti
    if (selectedLevel === 0) return [] // Livello 0 non ha cavalletti
    
    const level1ToolIds = positioned_tools
      .filter(tool => tool.level === 1)
      .map(tool => tool.odl_id)
    
    return cavalletti.filter(stand => level1ToolIds.includes(stand.tool_odl_id))
  }

  // 🎨 Separazione tool per ordine di rendering (PROMPT 12)
  const separateToolsByLevel = () => {
    const level0Tools = positioned_tools.filter(tool => tool.level === 0)
    const level1Tools = positioned_tools.filter(tool => tool.level === 1)
    return { level0Tools, level1Tools }
  }

  // 🎨 Generazione griglia
  const generateGrid = () => {
    if (!showGrid) return null
    
    const gridLines = []
    const gridSpacing = 100
    
    // Linee verticali
    for (let x = 0; x <= canvas_width; x += gridSpacing) {
      gridLines.push(
        <line
          key={`v-${x}`}
          x1={x}
          y1={0}
          x2={x}
          y2={canvas_height}
          stroke="#f3f4f6"
          strokeWidth="1"
        />
      )
    }
    
    // Linee orizzontali
    for (let y = 0; y <= canvas_height; y += gridSpacing) {
      gridLines.push(
        <line
          key={`h-${y}`}
          x1={0}
          y1={y}
          x2={canvas_width}
          y2={y}
          stroke="#f3f4f6"
          strokeWidth="1"
        />
      )
    }
    
    return <g className="grid">{gridLines}</g>
  }

  // 🎨 Colori per livelli (PROMPT 12 - Distinzione visiva)
  const getLevelColor = (level: number, isSelected: boolean = false) => {
    if (isSelected) {
      return {
        fill: '#ef4444',
        stroke: '#dc2626',
        strokeWidth: 4,
        strokeDasharray: undefined
      }
    }

    if (level === 0) {
      // Livello 0 (Piano base) - Blu solido
      return {
        fill: '#dbeafe',
        stroke: '#3b82f6',
        strokeWidth: 2,
        strokeDasharray: undefined
      }
    } else {
      // Livello 1 (Su cavalletti) - Arancione con bordo tratteggiato (PROMPT 12)
      return {
        fill: '#fef3c7',
        stroke: '#f59e0b',
        strokeWidth: 3,
        strokeDasharray: '10,5' // Bordo tratteggiato per enfatizzare livello sopraelevato
      }
    }
  }

  // 🏗️ Rendering cavalletti come piccoli elementi grafici (PROMPT 12)
  const renderCavalletto = (stand: Cavalletto, index: number) => (
    <g 
      key={`stand-${index}`} 
      className="cursor-pointer hover:opacity-80 transition-opacity"
      onClick={() => onStandClick?.(stand)}
    >
      {/* Rettangolo cavalletto con design treppiede */}
      <rect
        x={stand.x}
        y={stand.y}
        width={stand.width}
        height={stand.height}
        fill="#9ca3af"
        stroke="#6b7280"
        strokeWidth="2"
        strokeDasharray="8,4"
        rx="6"
        ry="6"
      />
      
      {/* Pattern interno per indicare la superficie di supporto */}
      <rect
        x={stand.x + 8}
        y={stand.y + 8}
        width={stand.width - 16}
        height={stand.height - 16}
        fill="none"
        stroke="#6b7280"
        strokeWidth="1"
        strokeDasharray="3,3"
        rx="3"
      />
      
      {/* Icona treppiede centrale */}
      <text
        x={stand.x + stand.width/2}
        y={stand.y + stand.height/2}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="14"
        fill="#6b7280"
        fontWeight="bold"
      >
        🏗️
      </text>
      
      {/* Numero sequenza cavalletto */}
      <text
        x={stand.x + stand.width/2}
        y={stand.y + stand.height + 18}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="10"
        fill="#6b7280"
        fontWeight="bold"
      >
        C{stand.sequence_number + 1}
      </text>
      
      {/* Capacità di carico */}
      <text
        x={stand.x + stand.width/2}
        y={stand.y - 8}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="9"
        fill="#6b7280"
      >
        {stand.load_capacity_kg}kg
      </text>
    </g>
  )

  // 🔧 Rendering tool con informazioni migliorate
  const renderTool = (tool: ToolPosition2L, index: number, renderOrder: 'level0' | 'level1') => {
    const isSelected = selectedTool?.odl_id === tool.odl_id
    const colors = getLevelColor(tool.level, isSelected)
    
    // Skip se il tool non appartiene al livello corrente di rendering
    if (renderOrder === 'level0' && tool.level !== 0) return null
    if (renderOrder === 'level1' && tool.level !== 1) return null
    
    return (
      <g 
        key={`tool-${renderOrder}-${index}`}
        className="cursor-pointer hover:opacity-90 transition-opacity"
        onClick={() => {
          setSelectedTool(tool)
          onToolClick?.(tool)
        }}
      >
        {/* Rettangolo tool con stili differenziati per livello */}
        <rect
          x={tool.x}
          y={tool.y}
          width={tool.width}
          height={tool.height}
          fill={colors.fill}
          stroke={colors.stroke}
          strokeWidth={colors.strokeWidth}
          strokeDasharray={colors.strokeDasharray}
          rx="6"
          transform={tool.rotated ? `rotate(90 ${tool.x + tool.width/2} ${tool.y + tool.height/2})` : ''}
        />
        
        {/* Shadow effect per livello 1 (per enfatizzare altezza) */}
        {tool.level === 1 && (
          <rect
            x={tool.x + 3}
            y={tool.y + 3}
            width={tool.width}
            height={tool.height}
            fill="rgba(0,0,0,0.15)"
            rx="6"
            transform={tool.rotated ? `rotate(90 ${tool.x + tool.width/2} ${tool.y + tool.height/2})` : ''}
            style={{ zIndex: -1 }}
          />
        )}
        
        {/* Labels nel tool */}
        <text
          x={tool.x + tool.width/2}
          y={tool.y + tool.height/2 - 15}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="14"
          fontWeight="bold"
          fill="#1f2937"
        >
          {tool.numero_odl}
        </text>
        
        <text
          x={tool.x + tool.width/2}
          y={tool.y + tool.height/2}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="11"
          fill="#6b7280"
        >
          L{tool.level} • {tool.weight_kg}kg
        </text>
        
        <text
          x={tool.x + tool.width/2}
          y={tool.y + tool.height/2 + 15}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="10"
          fill="#6b7280"
        >
          {tool.part_number}
        </text>
        
        {/* Indicatore Z per livello 1 con icona elevazione */}
        {tool.level === 1 && (
          <g>
            <text
              x={tool.x + 8}
              y={tool.y + 18}
              fontSize="11"
              fill="#f59e0b"
              fontWeight="bold"
            >
              ⬆️ Z:{tool.z_position}mm
            </text>
          </g>
        )}
        
        {/* Indicatore rotazione */}
        {tool.rotated && (
          <text
            x={tool.x + tool.width - 15}
            y={tool.y + 18}
            fontSize="12"
            fill="#dc2626"
            fontWeight="bold"
          >
            ↻
          </text>
        )}
      </g>
    )
  }

  // 📊 Statistiche
  const { level0Tools, level1Tools } = separateToolsByLevel()
  const filteredTools = getFilteredTools()
  const filteredStands = getFilteredStands()

  return (
    <div className={`nesting-canvas-2l ${className}`}>
      {/* 🔧 Controlli */}
      {showLevelFilter && (
        <div className="flex flex-wrap items-center gap-3 mb-4 p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Livello:</span>
            <select 
              value={selectedLevel} 
              onChange={(e) => setSelectedLevel(e.target.value === 'all' ? 'all' : parseInt(e.target.value) as 0 | 1)}
              className="px-3 py-1 border rounded-md text-sm bg-white"
            >
              <option value="all">Tutti i livelli</option>
              <option value={0}>Solo Livello 0 (Piano)</option>
              <option value={1}>Solo Livello 1 (Cavalletti)</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant={showGrid ? "default" : "outline"}
              size="sm"
              onClick={() => setShowGrid(!showGrid)}
            >
              📏 Griglia
            </Button>
            
            <Button
              variant={showStands ? "default" : "outline"}
              size="sm"
              onClick={() => setShowStands(!showStands)}
            >
              🏗️ Cavalletti
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
            >
              🔍-
            </Button>
            <span className="text-sm min-w-[60px] text-center font-mono">{Math.round(zoom * 100)}%</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setZoom(Math.min(3, zoom + 0.1))}
            >
              🔍+
            </Button>
          </div>
        </div>
      )}

      {/* 📊 Statistiche Rapide */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-lg font-bold text-blue-600">{level0Tools.length}</div>
          <div className="text-xs text-blue-600">Livello 0 (Piano)</div>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg border border-orange-200">
          <div className="text-lg font-bold text-orange-600">{level1Tools.length}</div>
          <div className="text-xs text-orange-600">Livello 1 (Elevato)</div>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-lg font-bold text-gray-600">{cavalletti.length}</div>
          <div className="text-xs text-gray-600">Cavalletti</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
          <div className="text-lg font-bold text-green-600">
            {positioned_tools.reduce((sum, t) => sum + t.weight_kg, 0).toFixed(1)}kg
          </div>
          <div className="text-xs text-green-600">Peso Totale</div>
        </div>
      </div>

      {/* 🎨 Canvas SVG con ordine di rendering corretto (PROMPT 12) */}
      <div className="border-2 rounded-lg bg-white overflow-auto shadow-sm" style={{ maxHeight: '700px' }}>
        <svg
          ref={svgRef}
          width={canvas_width * zoom}
          height={canvas_height * zoom}
          viewBox={`0 0 ${canvas_width} ${canvas_height}`}
          className="bg-white"
          style={{ minWidth: '500px', minHeight: '400px' }}
        >
          {/* 📏 Griglia (sotto tutto) */}
          {generateGrid()}
          
          {/* ORDINE DI RENDERING CORRETTO (PROMPT 12) */}
          
          {/* 1. PRIMA: Cavalletti (sul pavimento, sotto tutti i tool) */}
          {filteredStands.map((stand, index) => renderCavalletto(stand, index))}
          
          {/* 2. SECONDO: Tool Livello 0 (piano base, sopra i cavalletti) */}
          {selectedLevel === 'all' || selectedLevel === 0 ? (
            <>
              {level0Tools.map((tool, index) => renderTool(tool, index, 'level0'))}
            </>
          ) : null}
          
          {/* 3. TERZO: Tool Livello 1 (su cavalletti, sopra tutto) */}
          {selectedLevel === 'all' || selectedLevel === 1 ? (
            <>
              {level1Tools.map((tool, index) => renderTool(tool, index, 'level1'))}
            </>
          ) : null}
        </svg>
      </div>

      {/* 📄 Tool Info Panel */}
      {selectedTool && (
        <Card className="mt-4 border-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              🔧 {selectedTool.numero_odl} - {selectedTool.part_number}
              <Badge variant={selectedTool.level === 0 ? "default" : "secondary"}>
                Livello {selectedTool.level} {selectedTool.level === 0 ? '(Piano)' : '(Elevato)'}
              </Badge>
              {selectedTool.rotated && <Badge variant="destructive">↻ Ruotato</Badge>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-600">Posizione:</span>
                <div className="font-mono">X: {selectedTool.x}mm</div>
                <div className="font-mono">Y: {selectedTool.y}mm</div>
                <div className="font-mono">Z: {selectedTool.z_position}mm</div>
              </div>
              <div>
                <span className="font-medium text-gray-600">Dimensioni:</span>
                <div className="font-mono">{selectedTool.width} × {selectedTool.height}mm</div>
                <div className="text-xs text-gray-500">Area: {(selectedTool.width * selectedTool.height / 1000000).toFixed(2)}m²</div>
              </div>
              <div>
                <span className="font-medium text-gray-600">Proprietà:</span>
                <div>Peso: {selectedTool.weight_kg}kg</div>
                <div>Linee: {selectedTool.lines_used}</div>
                <div>Livello: {selectedTool.level === 0 ? 'Piano base' : 'Su cavalletti'}</div>
              </div>
              <div>
                <span className="font-medium text-gray-600">Descrizione:</span>
                <div className="text-xs">{selectedTool.descrizione_breve}</div>
                {selectedTool.level === 1 && (
                  <div className="text-xs text-orange-600 mt-1">
                    🏗️ Richiede {cavalletti.filter(c => c.tool_odl_id === selectedTool.odl_id).length} cavalletti
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 📈 Legenda livelli */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg border">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Legenda:</h4>
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded"></div>
            <span>Livello 0 (Piano base)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-100 border-2 border-yellow-500 rounded" style={{borderStyle: 'dashed'}}></div>
            <span>Livello 1 (Su cavalletti)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 border-2 border-gray-500 rounded" style={{borderStyle: 'dashed'}}></div>
            <span>🏗️ Cavalletti di supporto</span>
          </div>
        </div>
      </div>
    </div>
  )
} 