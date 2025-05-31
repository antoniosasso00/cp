'use client'

import React, { useEffect, useState } from 'react'
import { Stage, Layer, Rect, Text, Group } from 'react-konva'
import { Package } from 'lucide-react'

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

const NestingCanvas: React.FC<NestingCanvasProps> = ({ odlData, autoclave, className }) => {
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 })
  const [scale, setScale] = useState(1)

  useEffect(() => {
    // Calcola la scala per far stare l'autoclave nel canvas
    const maxWidth = 800
    const maxHeight = 600
    const margin = 50 // Margine per il bordo

    const scaleX = (maxWidth - margin * 2) / autoclave.lunghezza
    const scaleY = (maxHeight - margin * 2) / autoclave.larghezza_piano
    const optimalScale = Math.min(scaleX, scaleY, 1) // Non ingrandire oltre la dimensione reale

    setScale(optimalScale)
    setCanvasSize({
      width: autoclave.lunghezza * optimalScale + margin * 2,
      height: autoclave.larghezza_piano * optimalScale + margin * 2
    })
  }, [autoclave])

  // Colori diversi per ogni tool (ciclo attraverso una palette)
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
  ]

  const getToolColor = (index: number) => colors[index % colors.length]

  if (!odlData || odlData.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-muted/30 rounded-lg ${className}`} style={{ height: '400px' }}>
        <div className="text-center space-y-2">
          <Package className="h-12 w-12 text-muted-foreground mx-auto" />
          <p className="text-muted-foreground">Nessun ODL configurato</p>
          <p className="text-sm text-muted-foreground">
            Verifica che il nesting contenga la configurazione_json con i dati degli ODL
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={`border rounded-lg ${className}`}>
      <div className="p-4 border-b">
        <h3 className="font-semibold">Layout Nesting - {autoclave.nome}</h3>
        <p className="text-sm text-muted-foreground">
          Dimensioni autoclave: {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
        </p>
      </div>
      
      <div className="p-4">
        <Stage width={canvasSize.width} height={canvasSize.height}>
          <Layer>
            {/* Bordo autoclave */}
            <Rect
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
            <Text
              x={25}
              y={5}
              text={`${autoclave.nome} (${autoclave.lunghezza} × ${autoclave.larghezza_piano} mm)`}
              fontSize={12}
              fill="#374151"
              fontStyle="bold"
            />

            {/* ODL posizionati */}
            {odlData.map((odl, index) => (
              <Group key={`${odl.odl_id}_${odl.tool_id}`}>
                {/* Rettangolo del tool */}
                <Rect
                  x={25 + odl.x_mm * scale}
                  y={25 + odl.y_mm * scale}
                  width={odl.larghezza_mm * scale}
                  height={odl.lunghezza_mm * scale}
                  fill={getToolColor(index)}
                  stroke="#000"
                  strokeWidth={1}
                  opacity={0.7}
                />
                
                {/* Etichetta del tool */}
                <Text
                  x={25 + odl.x_mm * scale + 5}
                  y={25 + odl.y_mm * scale + 5}
                  text={`${odl.part_number}`}
                  fontSize={Math.max(8, 10 * scale)}
                  fill="#fff"
                  fontStyle="bold"
                />
                
                <Text
                  x={25 + odl.x_mm * scale + 5}
                  y={25 + odl.y_mm * scale + 5 + Math.max(8, 10 * scale) + 2}
                  text={`${odl.tool_nome}`}
                  fontSize={Math.max(6, 8 * scale)}
                  fill="#fff"
                />
              </Group>
            ))}
          </Layer>
        </Stage>
      </div>

      {/* Legenda */}
      <div className="p-4 border-t bg-muted/30">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
          {odlData.slice(0, 10).map((odl, index) => (
            <div key={`legend_${odl.odl_id}_${odl.tool_id}`} className="flex items-center space-x-2">
              <div 
                className="w-4 h-4 rounded border border-black"
                style={{ backgroundColor: getToolColor(index) }}
              />
              <span className="text-xs truncate">{odl.part_number}</span>
            </div>
          ))}
          {odlData.length > 10 && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-muted-foreground">
                +{odlData.length - 10} altri...
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default NestingCanvas 