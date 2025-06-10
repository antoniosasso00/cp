'use client'

import React, { useState } from 'react'
import { Rect, Text, Group } from '@/shared/components/canvas/CanvasWrapper'
import { cn } from '@/shared/lib/utils'
import type { ToolRectProps } from './types'

/**
 * Tool state colors configuration
 * Colori standard per tutti gli stati dei tool nel canvas
 */
export const TOOL_COLORS = {
  valid: {
    fill: '#22c55e',
    stroke: '#16a34a',
    label: 'Valido'
  },
  rotated: {
    fill: '#eab308',
    stroke: '#ca8a04',
    label: 'Ruotato'
  },
  excluded: {
    fill: '#ef4444',
    stroke: '#dc2626',
    label: 'Escluso'
  },
  outOfBounds: {
    fill: '#f97316',
    stroke: '#ea580c',
    label: 'Fuori Limiti'
  }
} as const

/**
 * Mapper per ottenere il numero ODL formattato
 * Utilizza il campo numero_odl se disponibile, altrimenti genera da ID
 */
export const mapODLIdToNumber = (tool: any): string => {
  // Priorità: numero_odl esistente > generazione da ID
  if (tool.numero_odl && tool.numero_odl !== '') {
    return tool.numero_odl
  }
  
  // Fallback: genera formato ODL da ID
  const odlId = tool.odl_id || tool.id || 0
  return `ODL${String(odlId).padStart(6, '0')}`
}

/**
 * Calcola font-size dinamica basata sull'area del rettangolo
 * Utilizza scala logaritmica per adattarsi meglio alle dimensioni
 */
export const calculateDynamicFontSize = (width: number, height: number): number => {
  const area = width * height
  const minArea = 100 // Area minima per font leggibile
  const maxArea = 10000 // Area massima per font ottimale
  
  // Scala logaritmica: log10(area) mappato su range font-size
  const logArea = Math.log10(Math.max(area, minArea))
  const logMin = Math.log10(minArea)
  const logMax = Math.log10(maxArea)
  
  // Mappa logaritmo su range font-size (6-16px)
  const normalizedLog = (logArea - logMin) / (logMax - logMin)
  const fontSize = 6 + (normalizedLog * 10)
  
  // Clamp tra limiti ragionevoli
  return Math.max(6, Math.min(16, fontSize))
}

/**
 * Determina se il text è visibile basato su dimensioni e font-size
 */
export const isTextVisible = (width: number, height: number, fontSize: number): boolean => {
  // Requisiti minimi per leggibilità
  const minWidth = 40
  const minHeight = 20
  const minFontSize = 8
  
  return width >= minWidth && height >= minHeight && fontSize >= minFontSize
}

/**
 * Normalizza i dati del tool garantendo tipi corretti
 * Gestisce conversioni da string a number e boolean
 */
export const normalizeToolData = (tool: any) => {
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

/**
 * Componente Tooltip per informazioni dettagliate del tool
 */
const ToolTooltip: React.FC<{
  tool: any
  visible: boolean
  x: number
  y: number
}> = ({ tool, visible, x, y }) => {
  if (!visible) return null

  const tooltipData = [
    { label: 'Dimensioni', value: `${tool.width.toFixed(1)} × ${tool.height.toFixed(1)} mm` },
    { label: 'Area', value: `${(tool.width * tool.height / 1000).toFixed(1)} cm²` },
    { label: 'Peso', value: `${tool.peso?.toFixed(1) || 'N/A'} kg` },
    { label: 'Rotazione', value: tool.rotated ? `Sì (${tool.rotation_angle || 90}°)` : 'No' },
    { label: 'Posizione', value: `(${tool.x.toFixed(1)}, ${tool.y.toFixed(1)})` }
  ]

  return (
    <Group name="tooltip">
      {/* Background del tooltip */}
      <Rect
        x={x}
        y={y - 80}
        width={180}
        height={70}
        fill="#1f2937"
        stroke="#374151"
        strokeWidth={1}
        cornerRadius={4}
        opacity={0.95}
      />
      
      {/* Contenuto del tooltip */}
      {tooltipData.map((item, index) => (
        <Group key={index}>
          <Text
            x={x + 8}
            y={y - 65 + (index * 12)}
            text={`${item.label}:`}
            fontSize={10}
            fill="#d1d5db"
            fontStyle="bold"
          />
          <Text
            x={x + 80}
            y={y - 65 + (index * 12)}
            text={item.value}
            fontSize={10}
            fill="#ffffff"
          />
        </Group>
      ))}
    </Group>
  )
}

export const ToolRect: React.FC<ToolRectProps> = ({ 
  tool: rawTool, 
  onClick, 
  isSelected = false, 
  autoclaveWidth, 
  autoclaveHeight, 
  showTooltips = true,
  className 
}) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  
  const tool = normalizeToolData(rawTool)
  
  // Calcola font-size dinamica
  const fontSize = calculateDynamicFontSize(tool.width, tool.height)
  const textVisible = isTextVisible(tool.width, tool.height, fontSize)
  
  // Ottieni numero ODL formattato
  const odlNumber = mapODLIdToNumber(tool)
  
  // Check if tool is out of autoclave bounds
  const isOutOfBoundsX = tool.x + tool.width > autoclaveWidth
  const isOutOfBoundsY = tool.y + tool.height > autoclaveHeight
  const isOutOfBounds = isOutOfBoundsX || isOutOfBoundsY
  
  // Determine color based on tool state
  const colorConfig = tool.excluded 
    ? TOOL_COLORS.excluded
    : isOutOfBounds
    ? TOOL_COLORS.outOfBounds
    : tool.rotated 
    ? TOOL_COLORS.rotated
    : TOOL_COLORS.valid
  
  // Shadow configuration for selected tools
  const shadowConfig = isSelected 
    ? { shadowColor: '#000', shadowOpacity: 0.3, shadowOffsetX: 2, shadowOffsetY: 2, shadowBlur: 4 }
    : {}

  // Opacity for excluded tools
  const opacity = tool.excluded ? 0.7 : 1.0

  // Calculate text position (center of tool)
  const textX = tool.x + tool.width / 2
  const textY = tool.y + tool.height / 2

  // Gestiona eventi mouse per tooltip
  const handleMouseEnter = (e: any) => {
    if (showTooltips) {
      setTooltipPos({ x: tool.x, y: tool.y })
      setShowTooltip(true)
    }
  }

  const handleMouseLeave = () => {
    setShowTooltip(false)
  }

  // Determina quali informazioni mostrare basato su spazio disponibile
  const textLines = []
  let currentY = textY - (fontSize * 1.5) // Inizia più in alto

  // Linea 1: Numero ODL (sempre mostrato se c'è spazio)
  if (textVisible) {
    textLines.push({
      text: odlNumber,
      y: currentY,
      fontSize: fontSize,
      fontStyle: 'bold'
    })
    currentY += fontSize + 2
  }

  // Linea 2: Part Number (se c'è spazio)
  if (textVisible && tool.part_number && fontSize >= 10) {
    textLines.push({
      text: tool.part_number,
      y: currentY,
      fontSize: Math.max(fontSize - 2, 8),
      fontStyle: 'normal'
    })
    currentY += fontSize + 1
  }

  // Linea 3: Descrizione breve (solo se c'è molto spazio)
  if (textVisible && tool.descrizione_breve && fontSize >= 12 && tool.height > 80) {
    const maxDescLength = Math.floor(tool.width / 6) // Stima caratteri che ci stanno
    const truncatedDesc = tool.descrizione_breve.length > maxDescLength
      ? tool.descrizione_breve.substring(0, maxDescLength - 3) + '...'
      : tool.descrizione_breve
    
    textLines.push({
      text: truncatedDesc,
      y: currentY,
      fontSize: Math.max(fontSize - 3, 7),
      fontStyle: 'normal'
    })
  }

  return (
    <Group
      name={`tool-${tool.odl_id}`}
      onClick={onClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Main tool rectangle */}
      <Rect
        x={tool.x}
        y={tool.y}
        width={tool.width}
        height={tool.height}
        fill={colorConfig.fill}
        stroke={colorConfig.stroke}
        strokeWidth={isSelected ? 2 : 1}
        opacity={opacity}
        {...shadowConfig}
      />
      
      {/* Tool text content */}
      {textLines.map((line, index) => (
        <Text
          key={index}
          x={textX}
          y={line.y}
          text={line.text}
          fontSize={line.fontSize}
          fill="#ffffff"
          fontStyle={line.fontStyle}
          align="center"
          verticalAlign="middle"
        />
      ))}
      
      {/* Selection indicator */}
      {isSelected && (
        <Rect
          x={tool.x - 2}
          y={tool.y - 2}
          width={tool.width + 4}
          height={tool.height + 4}
          fill="transparent"
          stroke="#3b82f6"
          strokeWidth={2}
          dash={[5, 5]}
          opacity={0.8}
        />
      )}
      
      {/* Rotation indicator */}
      {tool.rotated && (
        <Group>
          <Rect
            x={tool.x + tool.width - 12}
            y={tool.y + 2}
            width={10}
            height={10}
            fill="#ffffff"
            stroke={colorConfig.stroke}
            strokeWidth={1}
            cornerRadius={2}
          />
          <Text
            x={tool.x + tool.width - 7}
            y={tool.y + 7}
            text="R"
            fontSize={8}
            fill={colorConfig.stroke}
            fontStyle="bold"
            align="center"
            verticalAlign="middle"
          />
        </Group>
      )}
      
      {/* Out of bounds warning */}
      {isOutOfBounds && (
        <Group>
          <Rect
            x={tool.x + 2}
            y={tool.y + tool.height - 12}
            width={10}
            height={10}
            fill="#ffffff"
            stroke="#dc2626"
            strokeWidth={1}
            cornerRadius={2}
          />
          <Text
            x={tool.x + 7}
            y={tool.y + tool.height - 7}
            text="!"
            fontSize={8}
            fill="#dc2626"
            fontStyle="bold"
            align="center"
            verticalAlign="middle"
          />
        </Group>
      )}

      {/* Tooltip */}
      <ToolTooltip
        tool={tool}
        visible={showTooltip}
        x={tooltipPos.x}
        y={tooltipPos.y}
      />
    </Group>
  )
}

/**
 * Versione semplificata per rendering rapido (mantenuta per compatibilità)
 */
export const SimpleToolRect: React.FC<ToolRectProps> = ({ 
  tool: rawTool, 
  onClick, 
  isSelected = false,
  className 
}) => {
  const tool = normalizeToolData(rawTool)
  const fontSize = calculateDynamicFontSize(tool.width, tool.height)
  const textVisible = isTextVisible(tool.width, tool.height, fontSize)
  const odlNumber = mapODLIdToNumber(tool)

  return (
    <Group
      name={`simple-tool-${tool.odl_id}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <Rect
        x={tool.x}
        y={tool.y}
        width={tool.width}
        height={tool.height}
        fill={tool.excluded ? '#ef4444' : '#22c55e'}
        stroke={tool.excluded ? '#dc2626' : '#16a34a'}
        strokeWidth={1}
        opacity={tool.excluded ? 0.7 : 1.0}
      />
      
      {textVisible && (
        <Text
          x={tool.x + tool.width / 2}
          y={tool.y + tool.height / 2}
          text={odlNumber}
          fontSize={fontSize}
          fill="#ffffff"
          fontStyle="bold"
          align="center"
          verticalAlign="middle"
        />
      )}
    </Group>
  )
}

/**
 * Test per rendering su piccole aree (< 50 px)
 * Verifica che il componente gestisca correttamente dimensioni ridotte
 */
export const testSmallAreaRendering = () => {
  const testCases = [
    { width: 30, height: 20, expected: 'No text' },
    { width: 50, height: 30, expected: 'ODL only' },
    { width: 80, height: 40, expected: 'ODL + Part#' },
    { width: 120, height: 80, expected: 'ODL + Part# + Desc' }
  ]

  return testCases.map(testCase => {
    const fontSize = calculateDynamicFontSize(testCase.width, testCase.height)
    const visible = isTextVisible(testCase.width, testCase.height, fontSize)
    
    return {
      ...testCase,
      fontSize: fontSize.toFixed(1),
      textVisible: visible,
      result: visible ? 'Visible' : 'Hidden'
    }
  })
}

export const getToolColor = (tool: any, autoclaveWidth: number, autoclaveHeight: number) => {
  const normalizedTool = normalizeToolData(tool)
  const isOutOfBounds = (normalizedTool.x + normalizedTool.width > autoclaveWidth) || 
                        (normalizedTool.y + normalizedTool.height > autoclaveHeight)
  
  if (normalizedTool.excluded) return TOOL_COLORS.excluded
  if (isOutOfBounds) return TOOL_COLORS.outOfBounds
  if (normalizedTool.rotated) return TOOL_COLORS.rotated
  return TOOL_COLORS.valid
}

export const getToolStatus = (tool: any, autoclaveWidth: number, autoclaveHeight: number) => {
  const normalizedTool = normalizeToolData(tool)
  const isOutOfBounds = (normalizedTool.x + normalizedTool.width > autoclaveWidth) || 
                        (normalizedTool.y + normalizedTool.height > autoclaveHeight)
  
  if (normalizedTool.excluded) return 'excluded'
  if (isOutOfBounds) return 'outOfBounds'
  if (normalizedTool.rotated) return 'rotated'
  return 'valid'
} 