'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Eye, 
  Package,
  Loader2,
  AlertCircle,
  Grid3X3,
  Ruler,
  RotateCw
} from 'lucide-react'

interface ODLInfo {
  id: number
  numero_odl: string
  parte_nome: string
  tool_nome: string
  peso_kg: number
  valvole_richieste: number
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  max_load_kg: number
}

interface ToolPosition {
  odl_id: number
  x: number
  y: number
  width: number
  height: number
  rotated?: boolean
  piano: number
}

interface SimpleNestingData {
  autoclave: AutoclaveInfo
  odl_list: ODLInfo[]
  posizioni_tool: ToolPosition[]
  statistiche: {
    efficienza_piano_1: number
    efficienza_piano_2: number
    peso_totale_kg: number
    area_utilizzata_cm2: number
    area_totale_cm2: number
  }
}

interface SimpleNestingCanvasProps {
  data: SimpleNestingData
  selectedPlane?: number
  showControls?: boolean
  height?: number
  className?: string
}

export function SimpleNestingCanvas({ 
  data, 
  selectedPlane = 1,
  showControls = true,
  height = 650,
  className = ""
}: SimpleNestingCanvasProps) {
  const [currentPlane, setCurrentPlane] = useState(selectedPlane)
  const [showGrid, setShowGrid] = useState(true)
  const [showDimensions, setShowDimensions] = useState(true)
  const [showLabels, setShowLabels] = useState(true)
  const [selectedTool, setSelectedTool] = useState<number | null>(null)

  // Filtra le posizioni per il piano corrente
  const currentPositions = data.posizioni_tool.filter(pos => pos.piano === currentPlane)
  
  // ✅ MIGLIORIA: Calcolo dimensioni canvas ottimizzate
  const margin = 40  // Ridotto da 60 a 40
  const maxWidth = 900  // Aumentato da 700 a 900
  const maxHeight = height - 80  // Ridotto margine da 100 a 80
  
  // ✅ MIGLIORIA: Scala migliorata per sfruttare meglio lo spazio
  const scaleX = maxWidth / data.autoclave.lunghezza
  const scaleY = maxHeight / data.autoclave.larghezza_piano
  const scale = Math.min(scaleX, scaleY, 1.0) // Aumentato da 0.6 a 1.0 per canvas più grandi
  
  // ✅ MIGLIORIA: Dimensioni canvas dinamiche
  const autoclaveWidth = data.autoclave.lunghezza * scale
  const autoclaveHeight = data.autoclave.larghezza_piano * scale
  const canvasWidth = Math.max(autoclaveWidth + margin * 2, 600)  // Minimo 600px
  const canvasHeight = Math.max(autoclaveHeight + margin * 2, 400) // Minimo 400px
  const autoclaveX = (canvasWidth - autoclaveWidth) / 2  // Centra l'autoclave
  const autoclaveY = (canvasHeight - autoclaveHeight) / 2
  
  // Colore per il piano
  const planeColor = currentPlane === 1 ? "#3b82f6" : "#10b981" // blu o verde
  
  // Statistiche per il piano corrente
  const planeEfficiency = currentPlane === 1 ? 
    data.statistiche.efficienza_piano_1 : 
    data.statistiche.efficienza_piano_2
  
  // Conta ODL per piano
  const odlCountPiano1 = data.posizioni_tool.filter(p => p.piano === 1).length
  const odlCountPiano2 = data.posizioni_tool.filter(p => p.piano === 2).length

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Canvas Semplificato - {data.autoclave.nome}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {data.autoclave.lunghezza}×{data.autoclave.larghezza_piano}mm • {data.odl_list.length} ODL • {data.statistiche.peso_totale_kg.toFixed(1)}kg
            </p>
          </div>
          
          {/* Selezione piano con contatori */}
          <div className="flex items-center gap-4">
            <Tabs value={currentPlane.toString()} onValueChange={(value) => setCurrentPlane(parseInt(value))}>
              <TabsList>
                <TabsTrigger value="1" className="flex items-center gap-2">
                  Piano 1
                  <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                    {odlCountPiano1}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="2" className="flex items-center gap-2">
                  Piano 2
                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                    {odlCountPiano2}
                  </Badge>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Controlli di visualizzazione */}
        {showControls && (
          <div className="flex items-center gap-6 p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Switch
                id="show-grid"
                checked={showGrid}
                onCheckedChange={setShowGrid}
              />
              <Label htmlFor="show-grid" className="text-sm">Griglia</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="show-dimensions"
                checked={showDimensions}
                onCheckedChange={setShowDimensions}
              />
              <Label htmlFor="show-dimensions" className="text-sm">Quote</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="show-labels"
                checked={showLabels}
                onCheckedChange={setShowLabels}
              />
              <Label htmlFor="show-labels" className="text-sm">Etichette</Label>
            </div>
            
            <div className="ml-auto text-sm text-muted-foreground">
              Piano {currentPlane}: {planeEfficiency.toFixed(1)}% • {currentPositions.length} ODL
            </div>
          </div>
        )}

        {/* Canvas SVG */}
        <div className="relative border rounded-lg overflow-hidden bg-gray-50">
          <svg
            width="100%"
            height={canvasHeight}
            viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
            className="bg-white mx-auto"
            style={{ minHeight: '400px', maxHeight: '800px' }}
          >
            {/* Definizioni */}
            <defs>
              {/* Griglia */}
              <pattern id="grid-pattern" width={50 * scale} height={50 * scale} patternUnits="userSpaceOnUse">
                <path d={`M ${50 * scale} 0 L 0 0 0 ${50 * scale}`} fill="none" stroke="#e5e7eb" strokeWidth="1"/>
              </pattern>
              
              {/* Ombra */}
              <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="2" dy="2" stdDeviation="2" floodOpacity="0.2"/>
              </filter>
              
              {/* Pattern per rotazione */}
              <pattern id="rotated-pattern" patternUnits="userSpaceOnUse" width="8" height="8">
                <rect width="8" height="8" fill="white" opacity="0.1"/>
                <path d="M 0,8 l 8,-8 M -2,2 l 4,-4 M 6,10 l 4,-4" stroke="white" strokeWidth="1" opacity="0.5"/>
              </pattern>
            </defs>

            {/* Griglia di sfondo */}
            {showGrid && (
              <rect
                x={autoclaveX}
                y={autoclaveY}
                width={autoclaveWidth}
                height={autoclaveHeight}
                fill="url(#grid-pattern)"
              />
            )}

            {/* Contorno autoclave */}
            <rect
              x={autoclaveX}
              y={autoclaveY}
              width={autoclaveWidth}
              height={autoclaveHeight}
              fill="none"
              stroke="#374151"
              strokeWidth="3"
              rx="8"
            />

            {/* Etichetta autoclave */}
            <text
              x={autoclaveX + autoclaveWidth / 2}
              y={autoclaveY - 30}
              textAnchor="middle"
              className="fill-gray-700 text-sm font-semibold"
            >
              {data.autoclave.nome} - Piano {currentPlane}
            </text>
            
            <text
              x={autoclaveX + autoclaveWidth / 2}
              y={autoclaveY - 15}
              textAnchor="middle"
              className="fill-gray-500 text-xs"
            >
              {data.autoclave.lunghezza}×{data.autoclave.larghezza_piano}mm • Scala 1:{Math.round(1/scale)}
            </text>

            {/* Quote autoclave */}
            {showDimensions && (
              <>
                {/* Quota lunghezza */}
                <g>
                  <line
                    x1={autoclaveX}
                    y1={autoclaveY + autoclaveHeight + 15}
                    x2={autoclaveX + autoclaveWidth}
                    y2={autoclaveY + autoclaveHeight + 15}
                    stroke="#666"
                    strokeWidth="1"
                  />
                  <text
                    x={autoclaveX + autoclaveWidth / 2}
                    y={autoclaveY + autoclaveHeight + 30}
                    textAnchor="middle"
                    className="fill-gray-600 text-xs"
                  >
                    {data.autoclave.lunghezza}mm
                  </text>
                </g>
                
                {/* Quota larghezza */}
                <g>
                  <line
                    x1={autoclaveX + autoclaveWidth + 15}
                    y1={autoclaveY}
                    x2={autoclaveX + autoclaveWidth + 15}
                    y2={autoclaveY + autoclaveHeight}
                    stroke="#666"
                    strokeWidth="1"
                  />
                  <text
                    x={autoclaveX + autoclaveWidth + 30}
                    y={autoclaveY + autoclaveHeight / 2}
                    textAnchor="middle"
                    className="fill-gray-600 text-xs"
                    transform={`rotate(90, ${autoclaveX + autoclaveWidth + 30}, ${autoclaveY + autoclaveHeight / 2})`}
                  >
                    {data.autoclave.larghezza_piano}mm
                  </text>
                </g>
              </>
            )}

            {/* Tool posizionati per il piano corrente */}
            {currentPositions.map((position) => {
              const odl = data.odl_list.find(o => o.id === position.odl_id)
              if (!odl) return null

              // Coordinate convertite per visualizzazione
              const x = autoclaveX + (position.x * scale)
              const y = autoclaveY + (position.y * scale)
              const width = position.width * scale
              const height = position.height * scale
              
              const isSelected = selectedTool === odl.id
              const toolColor = isSelected ? "#1f2937" : planeColor

              return (
                <g
                  key={position.odl_id}
                  className="cursor-pointer transition-all duration-200"
                  onClick={() => setSelectedTool(isSelected ? null : odl.id)}
                >
                  {/* Rettangolo tool */}
                  <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    fill={toolColor}
                    fillOpacity={isSelected ? 0.9 : 0.7}
                    stroke={isSelected ? "#fbbf24" : "white"}
                    strokeWidth={isSelected ? "3" : "2"}
                    rx="4"
                    filter={isSelected ? "url(#shadow)" : undefined}
                  />
                  
                  {/* Pattern per tool ruotati */}
                  {position.rotated && (
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill="url(#rotated-pattern)"
                      rx="4"
                    />
                  )}
                  
                  {/* Icona rotazione */}
                  {position.rotated && (
                    <g transform={`translate(${x + width - 12}, ${y + 6})`}>
                      <circle r="6" fill="white" fillOpacity="0.9"/>
                      <RotateCw className="h-3 w-3" x="-6" y="-6" />
                    </g>
                  )}
                  
                  {/* Etichetta ODL */}
                  {showLabels && (
                    <>
                      {/* ✅ MIGLIORIA: Etichette sempre visibili se sopra soglia minima */}
                      {width > 30 && height > 20 && (
                        <>
                          <text
                            x={x + width / 2}
                            y={y + height / 2 - 4}
                            textAnchor="middle"
                            className="fill-white font-bold"
                            fontSize={Math.max(10, Math.min(14, width / 8))}
                            style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}
                          >
                            {odl.numero_odl}
                          </text>
                          {height > 35 && (
                            <text
                              x={x + width / 2}
                              y={y + height / 2 + 8}
                              textAnchor="middle"
                              className="fill-white"
                              fontSize={Math.max(8, Math.min(12, width / 10))}
                              style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}
                            >
                              {odl.valvole_richieste}V • {odl.peso_kg}kg
                            </text>
                          )}
                        </>
                      )}
                      
                      {/* ✅ MIGLIORIA: Fallback per tool molto piccoli - solo punto con tooltip */}
                      {(width <= 30 || height <= 20) && (
                        <>
                          <circle
                            cx={x + width / 2}
                            cy={y + height / 2}
                            r="3"
                            fill="white"
                            stroke={toolColor}
                            strokeWidth="2"
                          />
                          <title>{odl.numero_odl} - {odl.valvole_richieste}V - {odl.peso_kg}kg</title>
                        </>
                      )}
                    </>
                  )}
                  
                  {/* Quote se selezionato */}
                  {showDimensions && isSelected && (
                    <>
                      {/* Dimensioni sopra */}
                      <text
                        x={x + width / 2}
                        y={y - 8}
                        textAnchor="middle"
                        className="fill-amber-600 text-xs font-medium"
                        style={{ textShadow: '1px 1px 1px white' }}
                      >
                        {position.width}×{position.height}mm
                      </text>
                      
                      {/* Coordinate sotto */}
                      <text
                        x={x + width / 2}
                        y={y + height + 15}
                        textAnchor="middle"
                        className="fill-amber-600 text-xs font-medium"
                        style={{ textShadow: '1px 1px 1px white' }}
                      >
                        ({position.x}, {position.y})
                      </text>
                    </>
                  )}
                </g>
              )
            })}

            {/* Righello di riferimento */}
            <g>
              <line
                x1={autoclaveX + 10}
                y1={canvasHeight - 25}
                x2={autoclaveX + 10 + (100 * scale)}
                y2={canvasHeight - 25}
                stroke="#374151"
                strokeWidth="2"
              />
              <text
                x={autoclaveX + 10 + (50 * scale)}
                y={canvasHeight - 10}
                textAnchor="middle"
                className="fill-gray-700 text-xs font-medium"
              >
                100mm
              </text>
            </g>
          </svg>
        </div>

        {/* Informazioni piano corrente */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-lg font-bold text-blue-600">
              {planeEfficiency.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Efficienza Piano {currentPlane}</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-600">
              {currentPositions.length}
            </div>
            <div className="text-xs text-muted-foreground">ODL Posizionati</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-lg font-bold text-orange-600">
              {currentPositions.reduce((sum, pos) => {
                const odl = data.odl_list.find(o => o.id === pos.odl_id)
                return sum + (odl?.peso_kg || 0)
              }, 0).toFixed(1)}kg
            </div>
            <div className="text-xs text-muted-foreground">Peso Piano {currentPlane}</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-lg font-bold text-purple-600">
              {currentPositions.reduce((sum, pos) => {
                const odl = data.odl_list.find(o => o.id === pos.odl_id)
                return sum + (odl?.valvole_richieste || 0)
              }, 0)}
            </div>
            <div className="text-xs text-muted-foreground">Valvole Piano {currentPlane}</div>
          </div>
        </div>

        {/* Lista ODL del piano corrente */}
        {currentPositions.length > 0 && (
          <div>
            <h4 className="font-medium mb-3">ODL Piano {currentPlane}:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {currentPositions.map((position) => {
                const odl = data.odl_list.find(o => o.id === position.odl_id)
                if (!odl) return null
                
                const isSelected = selectedTool === odl.id
                
                return (
                  <div
                    key={odl.id}
                    className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                      isSelected ? 'bg-amber-50 border border-amber-200' : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                    onClick={() => setSelectedTool(isSelected ? null : odl.id)}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: planeColor }}
                      />
                      <div>
                        <div className="text-sm font-medium">{odl.numero_odl}</div>
                        <div className="text-xs text-muted-foreground">
                          {position.width}×{position.height}mm{position.rotated ? ' (ruotato)' : ''}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{odl.valvole_richieste}V</Badge>
                      <span className="text-xs text-muted-foreground">{odl.peso_kg}kg</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Messaggio se piano vuoto */}
        {currentPositions.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Nessun ODL posizionato sul Piano {currentPlane}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 