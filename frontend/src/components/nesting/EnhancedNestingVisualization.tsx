/**
 * Componente di visualizzazione migliorato per il nesting con algoritmo enhanced.
 * 
 * Caratteristiche:
 * - Utilizza l'algoritmo enhanced con vincoli completi
 * - Mostra proporzioni reali e dimensioni accurate
 * - Sistema di riferimento con griglia millimetrica
 * - Informazioni complete su ODL inclusi ed esclusi
 * - Gestione dettagliata dei motivi di esclusione
 * - Visualizzazione delle valvole e cicli di cura
 */

import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { 
  Eye, 
  Download, 
  RotateCw, 
  AlertTriangle, 
  Info, 
  Settings,
  Ruler,
  Zap,
  Weight,
  Target
} from "lucide-react"
import { apiCall } from '@/lib/api'

// Tipi per il componente
interface EnhancedNestingVisualizationProps {
  odlIds: number[]
  autoclaveId: number
  onToolClick?: (odl: any) => void
  showControls?: boolean
  className?: string
  constraints?: {
    distanza_minima_tool_mm?: number
    padding_bordo_mm?: number
    margine_sicurezza_peso_percent?: number
    efficienza_minima_percent?: number
    separa_cicli_cura?: boolean
    abilita_rotazioni?: boolean
  }
}

interface ToolPosition {
  odl_id: number
  x: number
  y: number
  width: number
  height: number
  rotated: boolean
  piano: number
}

interface ODLInfo {
  id: number
  parte_nome: string
  tool_nome: string
  priorita: number
  peso_kg: number
  area_cm2: number
  valvole_richieste: number
  ciclo_cura: string
  motivo_esclusione?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  area_piano: number
  capacita_peso: number
  num_linee_vuoto: number
  stato: string
}

interface NestingPreviewData {
  success: boolean
  message: string
  autoclave: AutoclaveInfo
  odl_inclusi: ODLInfo[]
  odl_esclusi: ODLInfo[]
  statistiche: {
    odl_totali: number
    odl_inclusi: number
    odl_esclusi: number
    efficienza_percent: number
    efficienza_geometrica_percent?: number
    peso_totale_kg: number
    peso_massimo_kg: number
    valvole_utilizzate: number
    valvole_totali: number
    area_utilizzata_cm2: number
    area_totale_cm2: number
    cycles_found?: string[]
  }
  tool_positions: ToolPosition[]
  effective_dimensions: {
    width: number
    height: number
    border_padding_mm: number
    tool_padding_mm: number
  }
  constraints_used: any
}

export function EnhancedNestingVisualization({
  odlIds,
  autoclaveId,
  onToolClick,
  showControls = true,
  className = "",
  constraints: initialConstraints = {}
}: EnhancedNestingVisualizationProps) {
  const [previewData, setPreviewData] = useState<NestingPreviewData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [zoom, setZoom] = useState(1)
  const [showGrid, setShowGrid] = useState(true)
  const [showDimensions, setShowDimensions] = useState(true)
  const [showToolNames, setShowToolNames] = useState(true)
  const [showExcluded, setShowExcluded] = useState(true)
  const [showConstraints, setShowConstraints] = useState(false)
  
  // Vincoli configurabili
  const [constraints, setConstraints] = useState({
    distanza_minima_tool_mm: 20,
    padding_bordo_mm: 15,
    margine_sicurezza_peso_percent: 10,
    efficienza_minima_percent: 60,
    separa_cicli_cura: true,
    abilita_rotazioni: true,
    ...initialConstraints
  })
  
  const { toast } = useToast()

  // Carica i dati del nesting migliorato
  const loadEnhancedPreview = async () => {
    try {
      setIsLoading(true)
      
      const response = await apiCall('/nesting/enhanced-preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          odl_ids: odlIds,
          autoclave_id: autoclaveId,
          constraints: constraints
        })
      })
      
      if (response.success) {
        setPreviewData(response)
      } else {
        // Anche se il nesting fallisce, mostriamo i dati disponibili
        setPreviewData(response)
        toast({
          title: "Nesting non ottimale",
          description: response.message,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare la preview del nesting migliorato",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (odlIds.length > 0 && autoclaveId) {
      loadEnhancedPreview()
    }
  }, [odlIds, autoclaveId, constraints])

  // Calcola le dimensioni del viewport SVG con proporzioni reali
  const svgDimensions = useMemo(() => {
    if (!previewData) return { 
      width: 800, 
      height: 600, 
      viewBox: "0 0 800 600",
      autoclaveX: 50,
      autoclaveY: 50,
      autoclaveWidth: 700,
      autoclaveHeight: 500,
      scale: 1
    }
    
    const autoclave = previewData.autoclave
    const margin = 100 // Margine per etichette e riferimenti
    
    // Calcola scala per adattare l'autoclave al viewport mantenendo proporzioni
    const maxViewportWidth = 1200
    const maxViewportHeight = 800
    
    const scaleX = (maxViewportWidth - 2 * margin) / autoclave.area_piano
    const scaleY = (maxViewportHeight - 2 * margin) / autoclave.area_piano
    const scale = Math.min(scaleX, scaleY, 1) // Non ingrandire oltre 1:1
    
    const autoclaveWidth = autoclave.area_piano * scale
    const autoclaveHeight = autoclave.area_piano * scale
    
    const totalWidth = autoclaveWidth + 2 * margin
    const totalHeight = autoclaveHeight + 2 * margin
    
    return {
      width: totalWidth,
      height: totalHeight,
      viewBox: `0 0 ${totalWidth} ${totalHeight}`,
      autoclaveX: margin,
      autoclaveY: margin,
      autoclaveWidth,
      autoclaveHeight,
      scale,
      realAutoclaveWidth: autoclave.area_piano,
      realAutoclaveHeight: autoclave.area_piano
    }
  }, [previewData])

  // Genera colori per i tool basati sulla priorità e stato
  const getToolColor = (priorita: number, isExcluded: boolean = false) => {
    if (isExcluded) return '#ef4444' // Rosso per esclusi
    
    // Gradiente dal verde (priorità bassa) al rosso (priorità alta)
    const hue = Math.max(0, 120 - (priorita * 12)) // 120 = verde, 0 = rosso
    return `hsl(${hue}, 70%, 60%)`
  }

  // Gestisce il click su un tool
  const handleToolClick = (position: ToolPosition) => {
    const odl = previewData?.odl_inclusi.find(o => o.id === position.odl_id)
    if (odl && onToolClick) {
      onToolClick(odl)
    }
  }

  // Esporta SVG
  const exportSVG = () => {
    const svgElement = document.getElementById(`enhanced-nesting-svg`)
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
      link.download = `enhanced-nesting-preview.png`
      link.href = canvas.toDataURL()
      link.click()
    }
    
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData)
  }

  // Aggiorna vincoli
  const updateConstraint = (key: string, value: any) => {
    setConstraints(prev => ({
      ...prev,
      [key]: value
    }))
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Caricamento Nesting Migliorato...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-96 bg-gray-200 rounded"></div>
            <div className="grid grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!previewData) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Errore nel Caricamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>Impossibile caricare la preview del nesting migliorato.</p>
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
              Nesting Migliorato - {previewData.autoclave.nome}
            </CardTitle>
            <CardDescription>
              {previewData.statistiche.odl_inclusi} ODL inclusi, {previewData.statistiche.odl_esclusi} esclusi
              {previewData.statistiche.cycles_found && previewData.statistiche.cycles_found.length > 0 && (
                <span> • Cicli: {previewData.statistiche.cycles_found.join(', ')}</span>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={previewData.success ? "default" : "destructive"}>
              {previewData.success ? "Ottimizzato" : "Non Ottimale"}
            </Badge>
            <Badge variant="outline">
              Efficienza: {previewData.statistiche.efficienza_percent.toFixed(1)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Alert per nesting non riuscito */}
        {!previewData.success && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Nesting non ottimale:</strong> {previewData.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Controlli */}
        {showControls && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Controlli Visualizzazione</h4>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={exportSVG}>
                  <Download className="h-4 w-4 mr-2" />
                  Esporta
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setShowConstraints(!showConstraints)}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Vincoli
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                <Label htmlFor="show-dimensions" className="text-sm">Dimensioni</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-tool-names"
                  checked={showToolNames}
                  onCheckedChange={setShowToolNames}
                />
                <Label htmlFor="show-tool-names" className="text-sm">Nomi Tool</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-excluded"
                  checked={showExcluded}
                  onCheckedChange={setShowExcluded}
                />
                <Label htmlFor="show-excluded" className="text-sm">ODL Esclusi</Label>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Label className="text-sm">Zoom:</Label>
              <Slider
                value={zoom}
                onValueChange={(value) => setZoom(value)}
                max={3}
                min={0.5}
                step={0.1}
                className="flex-1 max-w-xs"
              />
              <span className="text-sm text-muted-foreground">{(zoom * 100).toFixed(0)}%</span>
            </div>

            {/* Pannello vincoli */}
            {showConstraints && (
              <div className="border rounded-lg p-4 space-y-4">
                <h5 className="font-medium">Vincoli Algoritmo</h5>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Distanza Tool (mm)</Label>
                    <Slider
                      value={constraints.distanza_minima_tool_mm}
                      onValueChange={(value) => updateConstraint('distanza_minima_tool_mm', value)}
                      max={50}
                      min={5}
                      step={5}
                      className="mt-2"
                    />
                    <span className="text-xs text-muted-foreground">{constraints.distanza_minima_tool_mm}mm</span>
                  </div>
                  
                  <div>
                    <Label className="text-sm">Padding Bordo (mm)</Label>
                    <Slider
                      value={constraints.padding_bordo_mm}
                      onValueChange={(value) => updateConstraint('padding_bordo_mm', value)}
                      max={30}
                      min={5}
                      step={5}
                      className="mt-2"
                    />
                    <span className="text-xs text-muted-foreground">{constraints.padding_bordo_mm}mm</span>
                  </div>
                  
                  <div>
                    <Label className="text-sm">Margine Peso (%)</Label>
                    <Slider
                      value={constraints.margine_sicurezza_peso_percent}
                      onValueChange={(value) => updateConstraint('margine_sicurezza_peso_percent', value)}
                      max={30}
                      min={0}
                      step={5}
                      className="mt-2"
                    />
                    <span className="text-xs text-muted-foreground">{constraints.margine_sicurezza_peso_percent}%</span>
                  </div>
                  
                  <div>
                    <Label className="text-sm">Efficienza Min (%)</Label>
                    <Slider
                      value={constraints.efficienza_minima_percent}
                      onValueChange={(value) => updateConstraint('efficienza_minima_percent', value)}
                      max={90}
                      min={30}
                      step={5}
                      className="mt-2"
                    />
                    <span className="text-xs text-muted-foreground">{constraints.efficienza_minima_percent}%</span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="separa-cicli"
                      checked={constraints.separa_cicli_cura}
                      onCheckedChange={(value) => updateConstraint('separa_cicli_cura', value)}
                    />
                    <Label htmlFor="separa-cicli" className="text-sm">Separa Cicli Cura</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="abilita-rotazioni"
                      checked={constraints.abilita_rotazioni}
                      onCheckedChange={(value) => updateConstraint('abilita_rotazioni', value)}
                    />
                    <Label htmlFor="abilita-rotazioni" className="text-sm">Rotazioni Auto</Label>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <Separator />

        {/* Visualizzazione SVG migliorata */}
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
              id="enhanced-nesting-svg"
              width={svgDimensions.width}
              height={svgDimensions.height}
              viewBox={svgDimensions.viewBox}
              className="border"
            >
              {/* Definizioni */}
              <defs>
                {/* Griglia millimetrica */}
                <pattern id="grid-mm" width={svgDimensions.scale * 10} height={svgDimensions.scale * 10} patternUnits="userSpaceOnUse">
                  <path 
                    d={`M ${svgDimensions.scale * 10} 0 L 0 0 0 ${svgDimensions.scale * 10}`} 
                    fill="none" 
                    stroke="#e5e7eb" 
                    strokeWidth="0.5"
                  />
                </pattern>
                
                {/* Griglia centimetrica */}
                <pattern id="grid-cm" width={svgDimensions.scale * 100} height={svgDimensions.scale * 100} patternUnits="userSpaceOnUse">
                  <path 
                    d={`M ${svgDimensions.scale * 100} 0 L 0 0 0 ${svgDimensions.scale * 100}`} 
                    fill="none" 
                    stroke="#94a3b8" 
                    strokeWidth="1"
                  />
                </pattern>
                
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.3"/>
                </filter>
              </defs>

              {/* Griglia di sfondo */}
              {showGrid && (
                <>
                  <rect 
                    width={svgDimensions.width} 
                    height={svgDimensions.height} 
                    fill="url(#grid-mm)" 
                  />
                  <rect 
                    width={svgDimensions.width} 
                    height={svgDimensions.height} 
                    fill="url(#grid-cm)" 
                  />
                </>
              )}

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

              {/* Etichetta autoclave con dimensioni reali */}
              <text
                x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth / 2}
                y={svgDimensions.autoclaveY - 30}
                textAnchor="middle"
                className="fill-slate-700 text-sm font-semibold"
              >
                {previewData.autoclave.nome}
              </text>
              <text
                x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth / 2}
                y={svgDimensions.autoclaveY - 15}
                textAnchor="middle"
                className="fill-slate-500 text-xs"
              >
                {Math.sqrt(previewData.autoclave.area_piano).toFixed(0)}×{Math.sqrt(previewData.autoclave.area_piano).toFixed(0)}mm
                • Scala 1:{(1/svgDimensions.scale).toFixed(1)}
              </text>

              {/* Bordi di sicurezza */}
              {previewData.effective_dimensions && (
                <rect
                  x={svgDimensions.autoclaveX + (previewData.effective_dimensions.border_padding_mm * svgDimensions.scale)}
                  y={svgDimensions.autoclaveY + (previewData.effective_dimensions.border_padding_mm * svgDimensions.scale)}
                  width={svgDimensions.autoclaveWidth - (2 * previewData.effective_dimensions.border_padding_mm * svgDimensions.scale)}
                  height={svgDimensions.autoclaveHeight - (2 * previewData.effective_dimensions.border_padding_mm * svgDimensions.scale)}
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="1"
                  strokeDasharray="5,5"
                />
              )}

              {/* Tool posizionati */}
              {previewData.tool_positions.map((position, index) => {
                const odl = previewData.odl_inclusi.find(o => o.id === position.odl_id)
                if (!odl) return null

                const toolColor = getToolColor(odl.priorita)
                const x = svgDimensions.autoclaveX + (position.x * svgDimensions.scale)
                const y = svgDimensions.autoclaveY + (position.y * svgDimensions.scale)
                const width = position.width * svgDimensions.scale
                const height = position.height * svgDimensions.scale

                return (
                  <g key={position.odl_id}>
                    {/* Rettangolo del tool */}
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
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
                        <circle
                          cx={x + width - 15}
                          cy={y + 15}
                          r="8"
                          fill="white"
                          stroke="#1e293b"
                          strokeWidth="1"
                        />
                        <RotateCw 
                          x={x + width - 19} 
                          y={y + 11} 
                          width="8" 
                          height="8" 
                          className="fill-slate-700"
                        />
                      </g>
                    )}

                    {/* Nome del tool */}
                    {showToolNames && width > 40 && height > 20 && (
                      <text
                        x={x + width / 2}
                        y={y + height / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        className="fill-white text-xs font-medium"
                        style={{ fontSize: Math.min(10, width / 12) }}
                      >
                        {odl.tool_nome}
                      </text>
                    )}

                    {/* Dimensioni reali */}
                    {showDimensions && (
                      <g>
                        <text
                          x={x + width / 2}
                          y={y - 5}
                          textAnchor="middle"
                          className="fill-slate-600 text-xs"
                        >
                          {position.width.toFixed(0)}×{position.height.toFixed(0)}mm
                        </text>
                        <text
                          x={x + width / 2}
                          y={y + height + 15}
                          textAnchor="middle"
                          className="fill-slate-600 text-xs"
                        >
                          P{odl.priorita} | {odl.valvole_richieste}V | {odl.peso_kg.toFixed(1)}kg
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}

              {/* Sistema di riferimento */}
              <g transform={`translate(20, ${svgDimensions.height - 80})`}>
                <rect x="0" y="0" width="200" height="60" fill="white" stroke="#e5e7eb" rx="4" fillOpacity="0.9"/>
                <text x="10" y="15" className="fill-slate-700 text-xs font-semibold">Sistema di Riferimento</text>
                
                {/* Scala lineare */}
                <line x1="10" y1="25" x2={10 + (100 * svgDimensions.scale)} y2="25" stroke="#334155" strokeWidth="2"/>
                <line x1="10" y1="20" x2="10" y2="30" stroke="#334155" strokeWidth="2"/>
                <line x1={10 + (100 * svgDimensions.scale)} y1="20" x2={10 + (100 * svgDimensions.scale)} y2="30" stroke="#334155" strokeWidth="2"/>
                <text x={10 + (50 * svgDimensions.scale)} y="40" textAnchor="middle" className="fill-slate-600 text-xs">
                  100mm
                </text>
                
                {/* Indicatori */}
                <text x="10" y="55" className="fill-slate-500 text-xs">
                  Scala 1:{(1/svgDimensions.scale).toFixed(1)} • Grid: 10mm/100mm
                </text>
              </g>

              {/* Legenda priorità e stati */}
              <g transform={`translate(${svgDimensions.width - 180}, 20)`}>
                <rect x="0" y="0" width="170" height="120" fill="white" stroke="#e5e7eb" rx="4" fillOpacity="0.9"/>
                <text x="10" y="15" className="fill-slate-700 text-xs font-semibold">Legenda</text>
                
                {/* Priorità */}
                <text x="10" y="30" className="fill-slate-600 text-xs">Priorità:</text>
                {[1, 5, 10].map((priorita, i) => (
                  <g key={priorita} transform={`translate(10, ${35 + i * 15})`}>
                    <rect width="12" height="12" fill={getToolColor(priorita)} rx="2"/>
                    <text x="18" y="9" className="fill-slate-600 text-xs">
                      {priorita === 1 ? 'Bassa (1-3)' : priorita === 5 ? 'Media (4-7)' : 'Alta (8-10)'}
                    </text>
                  </g>
                ))}
                
                {/* Simboli */}
                <text x="10" y="90" className="fill-slate-600 text-xs">Simboli:</text>
                <g transform="translate(10, 95)">
                  <circle cx="6" cy="6" r="6" fill="white" stroke="#1e293b"/>
                  <RotateCw x="2" y="2" width="8" height="8" className="fill-slate-700"/>
                  <text x="18" y="9" className="fill-slate-600 text-xs">Ruotato</text>
                </g>
              </g>
            </svg>
          </div>
        </div>

        {/* Statistiche dettagliate */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {previewData.statistiche.odl_inclusi}
            </div>
            <div className="text-sm text-blue-700">ODL Inclusi</div>
          </div>
          
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {previewData.statistiche.efficienza_percent.toFixed(1)}%
            </div>
            <div className="text-sm text-green-700">Efficienza Totale</div>
            {previewData.statistiche.efficienza_geometrica_percent && (
              <div className="text-xs text-green-600">
                Geom: {previewData.statistiche.efficienza_geometrica_percent.toFixed(1)}%
              </div>
            )}
          </div>
          
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {previewData.statistiche.valvole_utilizzate}/{previewData.statistiche.valvole_totali}
            </div>
            <div className="text-sm text-purple-700">Valvole</div>
          </div>
          
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {previewData.statistiche.peso_totale_kg.toFixed(1)}kg
            </div>
            <div className="text-sm text-orange-700">Peso Totale</div>
            <div className="text-xs text-orange-600">
              Max: {previewData.statistiche.peso_massimo_kg.toFixed(1)}kg
            </div>
          </div>
          
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {previewData.tool_positions.filter(p => p.rotated).length}
            </div>
            <div className="text-sm text-red-700">Tool Ruotati</div>
          </div>
        </div>

        {/* Lista ODL esclusi */}
        {showExcluded && previewData.odl_esclusi.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-destructive">
              ODL Esclusi ({previewData.odl_esclusi.length})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {previewData.odl_esclusi.map((odl) => (
                <div key={odl.id} className="flex items-center justify-between p-2 bg-red-50 rounded text-sm">
                  <div>
                    <span className="font-medium">ODL #{odl.id}</span>
                    <span className="text-muted-foreground ml-2">{odl.parte_nome}</span>
                  </div>
                  <div className="text-xs text-destructive">
                    {odl.motivo_esclusione}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 