'use client'

import React from 'react'
import { Rect, Text, Group } from '@/shared/components/canvas/CanvasWrapper'
import { cn } from '@/shared/lib/utils'
import type { ToolRectProps } from './types'

// Tool state colors
const TOOL_COLORS = {
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
}

// Normalize tool data
const normalizeToolData = (tool: any) => {
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

export const ToolRect: React.FC<ToolRectProps> = ({ 
  tool: rawTool, 
  onClick, 
  isSelected = false, 
  autoclaveWidth, 
  autoclaveHeight, 
  showTooltips = true,
  className 
}) => {
  const tool = normalizeToolData(rawTool)
  
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

  // Determine font size based on tool size
  const fontSize = Math.min(tool.width / 8, tool.height / 4, 14)
  const isTextVisible = fontSize >= 8 // Only show text if font size is readable

  return (
    <Group
      name={`tool-${tool.odl_id}`}
      onClick={onClick}
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
      
      {/* Tool text (ODL ID and part number) */}
      {isTextVisible && (
        <Group>
          {/* ODL ID */}
          <Text
            x={textX}
            y={textY - (tool.part_number ? 6 : 0)}
            text={`ODL ${tool.odl_id}`}
            fontSize={fontSize}
            fill="#ffffff"
            fontStyle="bold"
            align="center"
            verticalAlign="middle"
          />
          
          {/* Part number (if available and space permits) */}
          {tool.part_number && fontSize >= 10 && (
            <Text
              x={textX}
              y={textY + 6}
              text={tool.part_number}
              fontSize={Math.max(fontSize - 2, 8)}
              fill="#ffffff"
              align="center"
              verticalAlign="middle"
              opacity={0.9}
            />
          )}
        </Group>
      )}
      
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
    </Group>
  )
}

// Simplified version for overview/minimap
export const SimpleToolRect: React.FC<ToolRectProps> = ({ 
  tool: rawTool, 
  onClick, 
  isSelected = false,
  className 
}) => {
  const tool = normalizeToolData(rawTool)
  
  const colorConfig = tool.excluded 
    ? TOOL_COLORS.excluded
    : tool.rotated 
    ? TOOL_COLORS.rotated
    : TOOL_COLORS.valid

  return (
    <Rect
      x={tool.x}
      y={tool.y}
      width={tool.width}
      height={tool.height}
      fill={colorConfig.fill}
      stroke={isSelected ? '#3b82f6' : colorConfig.stroke}
      strokeWidth={isSelected ? 2 : 1}
      opacity={tool.excluded ? 0.7 : 1.0}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    />
  )
}

// Utility functions
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