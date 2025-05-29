'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { 
  Eye, 
  ZoomIn, 
  ZoomOut, 
  RotateCw, 
  Maximize2, 
  Download,
  Settings,
  Package,
  Layers,
  AlertTriangle
} from 'lucide-react'
import { 
  nestingApi, 
  NestingLayoutData, 
  ToolPosition, 
  ODLLayoutInfo,
  AutoclaveLayoutInfo,
  NestingDetailResponse 
} from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingVisualizationProps {
  nestingId: number
  onToolClick?: (odl: ODLLayoutInfo) => void
  showControls?: boolean
  className?: string
}

export function NestingVisualization({ 
  nestingId, 
  onToolClick, 
  showControls = true,
  className = "" 
}: NestingVisualizationProps) {
  const [layoutData, setLayoutData] = useState<NestingLayoutData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [zoom, setZoom] = useState(1)
  const [showExcluded, setShowExcluded] = useState(false)
  const [showDimensions, setShowDimensions] = useState(true)
  const [showToolNames, setShowToolNames] = useState(true)
  const [paddingMm, setPaddingMm] = useState(10)
  const [bordaMm, setBordaMm] = useState(20)
  const [rotazioneAbilitata, setRotazioneAbilitata] = useState(true)
  const { toast } = useToast()

  // Carica i dati del layout
  const loadLayoutData = async () => {
    try {
      setIsLoading(true)
      const response = await nestingApi.getLayout(nestingId, {
        padding_mm: paddingMm,
        borda_mm: bordaMm,
        rotazione_abilitata: rotazioneAbilitata
      })
      
      if (response.success && response.layout_data) {
        setLayoutData(response.layout_data)
      } else {
        throw new Error(response.message || 'Errore nel caricamento del layout')
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare il layout del nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadLayoutData()
  }, [nestingId, paddingMm, bordaMm, rotazioneAbilitata])

  // Calcola le dimensioni del viewport SVG
  const svgDimensions = useMemo(() => {
    if (!layoutData) return { 
      width: 800, 
      height: 600, 
      viewBox: "0 0 800 600",
      autoclaveX: 50,
      autoclaveY: 50,
      autoclaveWidth: 700,
      autoclaveHeight: 500
    }
    
    const autoclave = layoutData.autoclave
    const margin = 50 // Margine per le etichette
    
    // Converti da mm a pixel (1mm = 1px per semplicità)
    const width = autoclave.lunghezza + (margin * 2)
    const height = autoclave.larghezza_piano + (margin * 2)
    
    return {
      width: Math.max(width, 400),
      height: Math.max(height, 300),
      viewBox: `0 0 ${width} ${height}`,
      autoclaveX: margin,
      autoclaveY: margin,
      autoclaveWidth: autoclave.lunghezza,
      autoclaveHeight: autoclave.larghezza_piano
    }
  }, [layoutData])

  // Genera colori per i tool basati sulla priorità
  const getToolColor = (priorita: number, isExcluded: boolean = false) => {
    if (isExcluded) return '#ef4444' // Rosso per esclusi
    
    // Gradiente dal verde (priorità bassa) al rosso (priorità alta)
    const hue = Math.max(0, 120 - (priorita * 12)) // 120 = verde, 0 = rosso
    return `hsl(${hue}, 70%, 60%)`
  }

  // Gestisce il click su un tool
  const handleToolClick = (position: ToolPosition) => {
    const odl = layoutData?.odl_list.find(o => o.id === position.odl_id)
    if (odl && onToolClick) {
      onToolClick(odl)
    }
  }

  // Esporta l'SVG come immagine
  const exportSVG = () => {
    const svgElement = document.getElementById(`nesting-svg-${nestingId}`)
    if (!svgElement) return

    const svgData = new XMLSerializer().serializeToString(svgElement)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      ctx?.drawImage(img, 0, 0)
      
      const link = document.createElement('a')
      link.download = `nesting-${nestingId}-layout.png`
      link.href = canvas.toDataURL()
      link.click()
    }
    
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData)
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Visualizzazione Nesting
          </CardTitle>
          <CardDescription>
            Caricamento layout del nesting...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-96" />
        </CardContent>
      </Card>
    )
  }

  if (!layoutData) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Errore Visualizzazione
          </CardTitle>
          <CardDescription>
            Impossibile caricare i dati del layout
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={loadLayoutData} variant="outline">
            Riprova
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Visualizzazione Nesting #{layoutData.id}
            </CardTitle>
            <CardDescription>
              {layoutData.autoclave.nome} - {layoutData.odl_list.length} tool posizionati
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              Efficienza: {((layoutData.area_utilizzata / layoutData.area_totale) * 100).toFixed(1)}%
            </Badge>
            <Badge variant="secondary">
              {layoutData.stato}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Controlli di visualizzazione */}
        {showControls && (
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between">
              <h4 className="font-medium flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Controlli Visualizzazione
              </h4>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-sm font-mono min-w-[60px] text-center">
                  {(zoom * 100).toFixed(0)}%
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setZoom(Math.min(3, zoom + 0.1))}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setZoom(1)}
                >
                  <Maximize2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportSVG}
                >
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-dimensions"
                  checked={showDimensions}
                  onCheckedChange={setShowDimensions}
                />
                <Label htmlFor="show-dimensions" className="text-sm">
                  Mostra dimensioni
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-tool-names"
                  checked={showToolNames}
                  onCheckedChange={setShowToolNames}
                />
                <Label htmlFor="show-tool-names" className="text-sm">
                  Nomi tool
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-excluded"
                  checked={showExcluded}
                  onCheckedChange={setShowExcluded}
                />
                <Label htmlFor="show-excluded" className="text-sm">
                  Tool esclusi
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="rotazione-abilitata"
                  checked={rotazioneAbilitata}
                  onCheckedChange={setRotazioneAbilitata}
                />
                <Label htmlFor="rotazione-abilitata" className="text-sm">
                  Rotazione auto
                </Label>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-sm">Padding tool: {paddingMm}mm</Label>
                <Slider
                  value={paddingMm}
                  onValueChange={(value: number) => setPaddingMm(value)}
                  max={50}
                  min={5}
                  step={5}
                  className="w-full"
                />
              </div>
              
              <div className="space-y-2">
                <Label className="text-sm">Bordo autoclave: {bordaMm}mm</Label>
                <Slider
                  value={bordaMm}
                  onValueChange={(value: number) => setBordaMm(value)}
                  max={100}
                  min={10}
                  step={10}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Visualizzazione SVG */}
        <div className="border rounded-lg overflow-hidden bg-white">
          <div 
            className="overflow-auto"
            style={{ 
              transform: `scale(${zoom})`,
              transformOrigin: 'top left',
              width: `${100 / zoom}%`,
              height: `${100 / zoom}%`
            }}
          >
            <svg
              id={`nesting-svg-${nestingId}`}
              width={svgDimensions.width}
              height={svgDimensions.height}
              viewBox={svgDimensions.viewBox}
              className="border"
            >
              {/* Definizioni per pattern e gradienti */}
              <defs>
                <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                  <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
                </pattern>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.3"/>
                </filter>
              </defs>

              {/* Griglia di sfondo */}
              <rect 
                width={svgDimensions.width} 
                height={svgDimensions.height} 
                fill="url(#grid)" 
              />

              {/* Piano dell'autoclave */}
              <rect
                x={svgDimensions.autoclaveX}
                y={svgDimensions.autoclaveY}
                width={svgDimensions.autoclaveWidth}
                height={svgDimensions.autoclaveHeight}
                fill="#f8fafc"
                stroke="#334155"
                strokeWidth="3"
                rx="8"
              />

              {/* Etichetta autoclave */}
              <text
                x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth / 2}
                y={svgDimensions.autoclaveY - 10}
                textAnchor="middle"
                className="fill-slate-700 text-sm font-semibold"
              >
                {layoutData.autoclave.nome} ({layoutData.autoclave.lunghezza}×{layoutData.autoclave.larghezza_piano}mm)
              </text>

              {/* Bordi di sicurezza */}
              <rect
                x={svgDimensions.autoclaveX + bordaMm}
                y={svgDimensions.autoclaveY + bordaMm}
                width={svgDimensions.autoclaveWidth - (bordaMm * 2)}
                height={svgDimensions.autoclaveHeight - (bordaMm * 2)}
                fill="none"
                stroke="#94a3b8"
                strokeWidth="1"
                strokeDasharray="5,5"
              />

              {/* Tool posizionati */}
              {layoutData.posizioni_tool.map((position, index) => {
                const odl = layoutData.odl_list.find(o => o.id === position.odl_id)
                if (!odl) return null

                const toolColor = getToolColor(odl.priorita)
                const x = svgDimensions.autoclaveX + position.x
                const y = svgDimensions.autoclaveY + position.y

                return (
                  <g key={position.odl_id}>
                    {/* Rettangolo del tool */}
                    <rect
                      x={x}
                      y={y}
                      width={position.width}
                      height={position.height}
                      fill={toolColor}
                      stroke="#1e293b"
                      strokeWidth="2"
                      rx="4"
                      filter="url(#shadow)"
                      className="cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => handleToolClick(position)}
                    />

                    {/* Indicatore di rotazione */}
                    {position.rotated && (
                      <g>
                        <RotateCw 
                          x={x + position.width - 20} 
                          y={y + 5} 
                          width="15" 
                          height="15" 
                          className="fill-white"
                        />
                      </g>
                    )}

                    {/* Nome del tool */}
                    {showToolNames && (
                      <text
                        x={x + position.width / 2}
                        y={y + position.height / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        className="fill-white text-xs font-medium"
                        style={{ fontSize: Math.min(12, position.width / 8) }}
                      >
                        {odl.tool.part_number_tool}
                      </text>
                    )}

                    {/* Dimensioni */}
                    {showDimensions && (
                      <g>
                        <text
                          x={x + position.width / 2}
                          y={y - 5}
                          textAnchor="middle"
                          className="fill-slate-600 text-xs"
                        >
                          {position.width.toFixed(0)}×{position.height.toFixed(0)}mm
                        </text>
                        <text
                          x={x + position.width / 2}
                          y={y + position.height + 15}
                          textAnchor="middle"
                          className="fill-slate-600 text-xs"
                        >
                          P{odl.priorita} | ODL#{odl.id}
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}

              {/* Legenda priorità */}
              <g transform={`translate(${svgDimensions.width - 150}, 20)`}>
                <rect x="0" y="0" width="140" height="80" fill="white" stroke="#e5e7eb" rx="4"/>
                <text x="10" y="15" className="fill-slate-700 text-xs font-semibold">Priorità</text>
                {[1, 5, 10].map((priorita, i) => (
                  <g key={priorita} transform={`translate(10, ${25 + i * 15})`}>
                    <rect width="12" height="12" fill={getToolColor(priorita)} rx="2"/>
                    <text x="18" y="9" className="fill-slate-600 text-xs">
                      {priorita === 1 ? 'Bassa (1-3)' : priorita === 5 ? 'Media (4-7)' : 'Alta (8-10)'}
                    </text>
                  </g>
                ))}
              </g>
            </svg>
          </div>
        </div>

        {/* Statistiche del layout */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {layoutData.odl_list.length}
            </div>
            <div className="text-sm text-blue-700">Tool Inclusi</div>
          </div>
          
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {((layoutData.area_utilizzata / layoutData.area_totale) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-green-700">Efficienza Area</div>
          </div>
          
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {layoutData.valvole_utilizzate}
            </div>
            <div className="text-sm text-purple-700">Valvole Totali</div>
          </div>
          
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {layoutData.posizioni_tool.filter(p => p.rotated).length}
            </div>
            <div className="text-sm text-orange-700">Tool Ruotati</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 