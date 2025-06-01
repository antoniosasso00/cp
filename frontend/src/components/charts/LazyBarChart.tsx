'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface LazyBarChartProps {
  data: any[]
  width?: string | number
  height?: string | number
  margin?: {
    top?: number
    right?: number
    bottom?: number
    left?: number
  }
  bars?: Array<{
    dataKey: string
    fill: string
    name?: string
    stackId?: string
  }>
  showGrid?: boolean
  showTooltip?: boolean
  showLegend?: boolean
  xAxisDataKey?: string
  yAxisLabel?: string
  className?: string
  layout?: 'horizontal' | 'vertical'
}

/**
 * Componente BarChart ottimizzato con lazy loading
 * 
 * 🎯 CARATTERISTICHE:
 * • Lazy loading per migliorare performance iniziale
 * • Props semplificate per uso comune
 * • Responsive di default
 * • Styling consistente con il tema
 * • Layout orizzontale/verticale
 * • Support per stacked bars
 * 
 * 💡 USO:
 * import dynamic from 'next/dynamic'
 * const LazyBarChart = dynamic(() => import('./LazyBarChart'), { ssr: false })
 */
export default function LazyBarChart({
  data,
  width = "100%",
  height = 400,
  margin = { top: 5, right: 30, left: 20, bottom: 5 },
  bars = [],
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  xAxisDataKey = "name",
  yAxisLabel,
  className = "",
  layout = 'vertical',
}: LazyBarChartProps) {
  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width={width} height="100%">
        <BarChart 
          data={data} 
          margin={margin}
          layout={layout}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
          
          <XAxis 
            dataKey={layout === 'vertical' ? xAxisDataKey : undefined}
            type={layout === 'vertical' ? 'category' : 'number'}
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
            interval={0}
          />
          
          <YAxis 
            type={layout === 'vertical' ? 'number' : 'category'}
            dataKey={layout === 'horizontal' ? xAxisDataKey : undefined}
            label={yAxisLabel ? { 
              value: yAxisLabel, 
              angle: layout === 'vertical' ? -90 : 0, 
              position: layout === 'vertical' ? 'insideLeft' : 'insideBottom',
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
          
          {bars.map((barConfig, index) => (
            <Bar 
              key={`bar-${index}-${barConfig.dataKey}`}
              dataKey={barConfig.dataKey}
              fill={barConfig.fill}
              name={barConfig.name || barConfig.dataKey}
              stackId={barConfig.stackId}
              radius={[2, 2, 0, 0]} // Angoli arrotondati
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
} 