'use client'

import React from 'react'
import { Line, Text, Group } from '@/shared/components/canvas/CanvasWrapper'
import type { GridLayerProps } from './types'

export const GridLayer: React.FC<GridLayerProps> = ({ 
  width, 
  height, 
  showRuler = true,
  gridSpacing = 100,
  className 
}) => {
  const lines: number[] = []
  
  // Generate vertical lines
  for (let x = 0; x <= width; x += gridSpacing) {
    lines.push(x, 0, x, height)
  }
  
  // Generate horizontal lines
  for (let y = 0; y <= height; y += gridSpacing) {
    lines.push(0, y, width, y)
  }
  
  return (
    <Group name="grid-layer">
      {/* Main grid */}
      <Line
        points={lines}
        stroke="#e5e7eb"
        strokeWidth={0.5}
        opacity={0.5}
      />
      
      {/* Ruler (if enabled) */}
      {showRuler && (
        <Group name="ruler">
          {/* Horizontal scale every gridSpacing mm (limited for performance) */}
          {Array.from({ length: Math.min(Math.floor(width / gridSpacing) + 1, 25) }, (_, i) => {
            const x = i * gridSpacing
            return (
              <Group key={`h-${i}`}>
                {/* Measurement line */}
                <Line
                  points={[x, 0, x, 20]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {/* Measurement text - show labels only every 2 lines to reduce clutter */}
                {i % 2 === 0 && (
                  <Text
                    x={x + 5}
                    y={5}
                    text={`${(x / 10).toFixed(0)}cm`}
                    fontSize={10}
                    fill="#374151"
                    opacity={0.8}
                  />
                )}
              </Group>
            )
          })}
          
          {/* Vertical scale every gridSpacing mm (limited for performance) */}
          {Array.from({ length: Math.min(Math.floor(height / gridSpacing) + 1, 30) }, (_, i) => {
            const y = i * gridSpacing
            return (
              <Group key={`v-${i}`}>
                {/* Measurement line */}
                <Line
                  points={[0, y, 20, y]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {/* Measurement text - show labels only every 2 lines to reduce clutter */}
                {i % 2 === 0 && (
                  <Text
                    x={5}
                    y={y + 5}
                    text={`${(y / 10).toFixed(0)}cm`}
                    fontSize={10}
                    fill="#374151"
                    opacity={0.8}
                    rotation={-90}
                  />
                )}
              </Group>
            )
          })}
        </Group>
      )}
    </Group>
  )
}

// Alternative grid with different spacing options
export const AdaptiveGridLayer: React.FC<GridLayerProps & {
  majorSpacing?: number
  minorSpacing?: number
  showMajor?: boolean
  showMinor?: boolean
}> = ({ 
  width, 
  height, 
  showRuler = true,
  gridSpacing = 100,
  majorSpacing = 100,
  minorSpacing = 20,
  showMajor = true,
  showMinor = true,
  className 
}) => {
  const majorLines: number[] = []
  const minorLines: number[] = []
  
  // Generate major grid lines
  if (showMajor) {
    for (let x = 0; x <= width; x += majorSpacing) {
      majorLines.push(x, 0, x, height)
    }
    for (let y = 0; y <= height; y += majorSpacing) {
      majorLines.push(0, y, width, y)
    }
  }
  
  // Generate minor grid lines
  if (showMinor) {
    for (let x = 0; x <= width; x += minorSpacing) {
      if (x % majorSpacing !== 0) { // Skip major lines
        minorLines.push(x, 0, x, height)
      }
    }
    for (let y = 0; y <= height; y += minorSpacing) {
      if (y % majorSpacing !== 0) { // Skip major lines
        minorLines.push(0, y, width, y)
      }
    }
  }
  
  return (
    <Group name="adaptive-grid-layer">
      {/* Minor grid lines */}
      {showMinor && minorLines.length > 0 && (
        <Line
          points={minorLines}
          stroke="#f3f4f6"
          strokeWidth={0.25}
          opacity={0.3}
        />
      )}
      
      {/* Major grid lines */}
      {showMajor && majorLines.length > 0 && (
        <Line
          points={majorLines}
          stroke="#e5e7eb"
          strokeWidth={0.5}
          opacity={0.6}
        />
      )}
      
      {/* Ruler (if enabled) */}
      {showRuler && (
        <Group name="adaptive-ruler">
          {Array.from({ length: Math.min(Math.floor(width / majorSpacing) + 1, 25) }, (_, i) => {
            const x = i * majorSpacing
            return (
              <Group key={`h-${i}`}>
                <Line
                  points={[x, 0, x, 25]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {i % 2 === 0 && (
                  <Text
                    x={x + 5}
                    y={8}
                    text={`${(x / 10).toFixed(0)}cm`}
                    fontSize={12}
                    fill="#374151"
                    opacity={0.9}
                    fontFamily="monospace"
                  />
                )}
              </Group>
            )
          })}
          
          {Array.from({ length: Math.min(Math.floor(height / majorSpacing) + 1, 30) }, (_, i) => {
            const y = i * majorSpacing
            return (
              <Group key={`v-${i}`}>
                <Line
                  points={[0, y, 25, y]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {i % 2 === 0 && (
                  <Text
                    x={8}
                    y={y + 5}
                    text={`${(y / 10).toFixed(0)}cm`}
                    fontSize={12}
                    fill="#374151"
                    opacity={0.9}
                    rotation={-90}
                    fontFamily="monospace"
                  />
                )}
              </Group>
            )
          })}
        </Group>
      )}
    </Group>
  )
} 