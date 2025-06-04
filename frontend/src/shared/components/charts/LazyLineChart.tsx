'use client'

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineProps,
} from 'recharts'

interface LazyLineChartProps {
  data: any[]
  width?: string | number
  height?: string | number
  margin?: {
    top?: number
    right?: number
    bottom?: number
    left?: number
  }
  lines?: Array<{
    dataKey: string
    stroke: string
    strokeWidth?: number
    name?: string
    type?: 'monotone' | 'linear' | 'step'
    dot?: any
  }>
  showGrid?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  xAxisDataKey?: string
  yAxisLabel?: string
  className?: string
}

/**
 * Componente LineChart ottimizzato con lazy loading
 * 
 * 🎯 CARATTERISTICHE:
 * • Lazy loading per migliorare performance iniziale
 * • Props semplificate per uso comune
 * • Responsive di default
 * • Styling consistente con il tema
 * • Tooltip e Legend configurabili
 * 
 * 💡 USO:
 * import dynamic from 'next/dynamic'
 * const LazyLineChart = dynamic(() => import('./LazyLineChart'), { ssr: false })
 */
export default function LazyLineChart({
  data,
  width = "100%",
  height = 400,
  margin = { top: 5, right: 30, left: 20, bottom: 5 },
  lines = [],
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  xAxisDataKey = "name",
  yAxisLabel,
  className = "",
}: LazyLineChartProps) {
  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width={width} height="100%">
        <LineChart data={data} margin={margin}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
          
          <XAxis 
            dataKey={xAxisDataKey}
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
            interval={0}
          />
          
          <YAxis 
            label={yAxisLabel ? { 
              value: yAxisLabel, 
              angle: -90, 
              position: 'insideLeft',
              className: 'text-muted-foreground'
            } : undefined}
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
          />
          
          {showTooltip && (
            <Tooltip 
              formatter={(value: any, name: any) => [value, name]}
              labelFormatter={(label) => `${xAxisDataKey}: ${label}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                color: 'hsl(var(--foreground))'
              }}
            />
          )}
          
          {showLegend && <Legend />}
          
          {lines.map((lineConfig, index) => (
            <Line 
              key={`line-${index}-${lineConfig.dataKey}`}
              type={lineConfig.type || "monotone"}
              dataKey={lineConfig.dataKey}
              stroke={lineConfig.stroke}
              strokeWidth={lineConfig.strokeWidth || 2}
              dot={lineConfig.dot || { fill: lineConfig.stroke, strokeWidth: 2, r: 4 }}
              name={lineConfig.name || lineConfig.dataKey}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
} 