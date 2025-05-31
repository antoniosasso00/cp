'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { Package, AlertCircle, Loader2 } from 'lucide-react'
import dynamic from 'next/dynamic'

// Import dinamico con opzioni avanzate per react-konva
const KonvaStage = dynamic(
  () => import('react-konva').then(mod => ({ default: mod.Stage })),
  { 
    ssr: false,
    loading: () => <CanvasLoader />,
  }
)

const KonvaLayer = dynamic(
  () => import('react-konva').then(mod => ({ default: mod.Layer })),
  { ssr: false }
)

const KonvaRect = dynamic(
  () => import('react-konva').then(mod => ({ default: mod.Rect })),
  { ssr: false }
)

const KonvaText = dynamic(
  () => import('react-konva').then(mod => ({ default: mod.Text })),
  { ssr: false }
)

const KonvaGroup = dynamic(
  () => import('react-konva').then(mod => ({ default: mod.Group })),
  { ssr: false }
)

interface ODLDettaglio {
  odl_id: string | number
  tool_id: string | number
  x_mm: number
  y_mm: number
  larghezza_mm: number
  lunghezza_mm: number
  part_number: string
  descrizione: string
  ciclo_cura: string
  tool_nome: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}

interface NestingCanvasProps {
  odlData: ODLDettaglio[]
  autoclave: AutoclaveInfo
  className?: string
}

// Componente di caricamento
const CanvasLoader: React.FC = () => (
  <div className="flex items-center justify-center bg-muted/30 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-2">
      <Loader2 className="h-12 w-12 text-blue-500 mx-auto animate-spin" />
      <p className="text-muted-foreground">Caricamento canvas...</p>
      <p className="text-xs text-muted-foreground">Inizializzazione react-konva</p>
    </div>
  </div>
)

// Componente di errore
const CanvasError: React.FC<{ onRetry: () => void }> = ({ onRetry }) => (
  <div className="flex items-center justify-center bg-red-50 border border-red-200 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-3">
      <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
      <div>
        <p className="text-red-800 font-medium">Errore nel caricamento canvas</p>
        <p className="text-sm text-red-600">Problema nell'inizializzazione di react-konva</p>
      </div>
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors"
      >
        Riprova
      </button>
    </div>
  </div>
)

// Componente dati mancanti
const NoDataCanvas: React.FC = () => (
  <div className="flex items-center justify-center bg-muted/30 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-2">
      <Package className="h-12 w-12 text-muted-foreground mx-auto" />
      <p className="text-muted-foreground">Nessun ODL configurato</p>
      <p className="text-sm text-muted-foreground">
        Verifica che il nesting contenga la configurazione_json con i dati degli ODL
      </p>
    </div>
  </div>
)

// Componente canvas principale
const KonvaCanvas: React.FC<{
  odlData: ODLDettaglio[]
  autoclave: AutoclaveInfo
  canvasSize: { width: number; height: number }
  scale: number
}> = ({ odlData, autoclave, canvasSize, scale }) => {
  // Colori per i tool
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
  ]

  const getToolColor = (index: number) => colors[index % colors.length]

  return (
    <KonvaStage width={canvasSize.width} height={canvasSize.height}>
      <KonvaLayer>
        {/* Bordo autoclave */}
        <KonvaRect
          x={25}
          y={25}
          width={autoclave.lunghezza * scale}
          height={autoclave.larghezza_piano * scale}
          stroke="#374151"
          strokeWidth={2}
          fill="transparent"
          dash={[5, 5]}
        />
        
        {/* Etichetta autoclave */}
        <KonvaText
          x={25}
          y={5}
          text={`${autoclave.nome} (${autoclave.lunghezza} × ${autoclave.larghezza_piano} mm)`}
          fontSize={12}
          fill="#374151"
          fontStyle="bold"
        />

        {/* ODL posizionati */}
        {odlData.map((odl, index) => (
          <KonvaGroup key={`${odl.odl_id}_${odl.tool_id}_${index}`}>
            {/* Rettangolo del tool */}
            <KonvaRect
              x={25 + (odl.x_mm || 0) * scale}
              y={25 + (odl.y_mm || 0) * scale}
              width={(odl.larghezza_mm || 50) * scale}
              height={(odl.lunghezza_mm || 50) * scale}
              fill={getToolColor(index)}
              stroke="#000"
              strokeWidth={1}
              opacity={0.7}
            />
            
            {/* Etichetta del tool */}
            <KonvaText
              x={25 + (odl.x_mm || 0) * scale + 5}
              y={25 + (odl.y_mm || 0) * scale + 5}
              text={odl.part_number || 'N/A'}
              fontSize={Math.max(8, 10 * scale)}
              fill="#fff"
              fontStyle="bold"
            />
            
            <KonvaText
              x={25 + (odl.x_mm || 0) * scale + 5}
              y={25 + (odl.y_mm || 0) * scale + 5 + Math.max(8, 10 * scale) + 2}
              text={odl.tool_nome || 'Tool sconosciuto'}
              fontSize={Math.max(6, 8 * scale)}
              fill="#fff"
            />
          </KonvaGroup>
        ))}
      </KonvaLayer>
    </KonvaStage>
  )
}

const NestingCanvas: React.FC<NestingCanvasProps> = ({ odlData, autoclave, className }) => {
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 })
  const [scale, setScale] = useState(1)
  const [isClient, setIsClient] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)

  // Inizializzazione client-side
  useEffect(() => {
    setIsClient(true)
    
    // Simula un piccolo delay per assicurarsi che tutti i moduli siano caricati
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [retryCount])

  // Calcolo scala e dimensioni canvas
  useEffect(() => {
    if (isClient && autoclave && !isLoading) {
      try {
        const maxWidth = 800
        const maxHeight = 600
        const margin = 50

        const scaleX = (maxWidth - margin * 2) / (autoclave.lunghezza || 1000)
        const scaleY = (maxHeight - margin * 2) / (autoclave.larghezza_piano || 500)
        const optimalScale = Math.min(scaleX, scaleY, 1)

        setScale(optimalScale)
        setCanvasSize({
          width: (autoclave.lunghezza || 1000) * optimalScale + margin * 2,
          height: (autoclave.larghezza_piano || 500) * optimalScale + margin * 2
        })
        setHasError(false)
      } catch (error) {
        console.error('Errore nel calcolo delle dimensioni canvas:', error)
        setHasError(true)
      }
    }
  }, [autoclave, isClient, isLoading])

  // Funzione retry
  const handleRetry = useCallback(() => {
    setHasError(false)
    setIsLoading(true)
    setRetryCount(prev => prev + 1)
  }, [])

  // Rendering condizionale
  if (!isClient || isLoading) {
    return <CanvasLoader />
  }

  if (hasError) {
    return <CanvasError onRetry={handleRetry} />
  }

  if (!odlData || odlData.length === 0) {
    return <NoDataCanvas />
  }

  if (!autoclave) {
    return (
      <div className={`flex items-center justify-center bg-yellow-50 border border-yellow-200 rounded-lg ${className}`} style={{ height: '400px' }}>
        <div className="text-center space-y-2">
          <AlertCircle className="h-12 w-12 text-yellow-600 mx-auto" />
          <p className="text-yellow-800">Dati autoclave mancanti</p>
          <p className="text-sm text-yellow-600">Impossibile calcolare le dimensioni del canvas</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`border rounded-lg bg-white ${className}`}>
      <div className="p-4 border-b bg-gray-50">
        <h3 className="font-semibold text-gray-900">Layout Nesting - {autoclave.nome}</h3>
        <p className="text-sm text-gray-600">
          Dimensioni autoclave: {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
        </p>
        <p className="text-xs text-gray-500">
          Scala: {(scale * 100).toFixed(1)}% | Tool visualizzati: {odlData.length}
        </p>
      </div>
      
      <div className="p-4 bg-gray-50">
        <div className="bg-white border rounded p-2 overflow-auto">
          <React.Suspense fallback={<CanvasLoader />}>
            <KonvaCanvas 
              odlData={odlData}
              autoclave={autoclave}
              canvasSize={canvasSize}
              scale={scale}
            />
          </React.Suspense>
        </div>
      </div>

      {/* Legenda migliorata */}
      <div className="p-4 border-t bg-gray-50">
        <h4 className="font-medium text-gray-900 mb-3">Legenda Tool</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {odlData.slice(0, 12).map((odl, index) => (
            <div key={`legend_${odl.odl_id}_${odl.tool_id}`} className="flex items-center space-x-2 p-2 bg-white rounded border">
              <div 
                className="w-4 h-4 rounded border border-gray-300 flex-shrink-0"
                style={{ backgroundColor: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'][index % 10] }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-900 truncate">{odl.part_number}</p>
                <p className="text-xs text-gray-500 truncate">{odl.tool_nome}</p>
              </div>
            </div>
          ))}
          {odlData.length > 12 && (
            <div className="flex items-center justify-center p-2 bg-gray-100 rounded border border-dashed">
              <span className="text-xs text-gray-600 font-medium">
                +{odlData.length - 12} altri tool
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default NestingCanvas 