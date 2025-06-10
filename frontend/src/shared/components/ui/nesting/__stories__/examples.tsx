/**
 * Nesting UI Components Examples
 * 
 * This file contains example usage of all nesting components.
 * Can be used for development, testing, and documentation purposes.
 */

import React from 'react'
import {
  BatchStatusBadge,
  EfficiencyMeter,
  NestingControls,
  ToolPositionCard,
  AutoclaveInfoCard,
  GridLayer,
  ToolRect,
  NestingCanvas
} from '../index'
import type { ToolPosition, AutoclaveInfo } from '../types'

// Mock data for examples
const mockTool: ToolPosition = {
  odl_id: 1,
  x: 100,
  y: 150,
  width: 200,
  height: 100,
  peso: 2.5,
  rotated: false,
  part_number: 'P001',
  tool_nome: 'Tool Example',
  excluded: false
}

const mockAutoclave: AutoclaveInfo = {
  id: 1,
  nome: 'PANINI',
  lunghezza: 1000,
  larghezza_piano: 800,
  codice: 'PAN001'
}

const mockBatchData = {
  configurazione_json: {
    canvas_width: 1000,
    canvas_height: 800,
    tool_positions: [mockTool]
  },
  autoclave: mockAutoclave,
  metrics: {
    efficiency_percentage: 75,
    total_tools: 1,
    total_weight: 2.5,
    utilized_area: 20000
  },
  id: 'batch-example-1'
}

// Example components
export const BatchStatusBadgeExamples = () => (
  <div className="space-y-4 p-4">
    <h3 className="text-lg font-semibold">BatchStatusBadge Examples</h3>
    
    <div className="space-y-2">
      <h4 className="font-medium">All Statuses:</h4>
      <div className="flex flex-wrap gap-2">
        <BatchStatusBadge status="draft" />
        <BatchStatusBadge status="sospeso" />
        <BatchStatusBadge status="confermato" />
        <BatchStatusBadge status="loaded" />
        <BatchStatusBadge status="cured" />
        <BatchStatusBadge status="terminato" />
      </div>
    </div>

    <div className="space-y-2">
      <h4 className="font-medium">Sizes:</h4>
      <div className="flex items-center gap-2">
        <BatchStatusBadge status="confermato" size="sm" />
        <BatchStatusBadge status="confermato" size="md" />
        <BatchStatusBadge status="confermato" size="lg" />
      </div>
    </div>

    <div className="space-y-2">
      <h4 className="font-medium">Variants:</h4>
      <div className="flex items-center gap-2">
        <BatchStatusBadge status="confermato" variant="default" />
        <BatchStatusBadge status="confermato" variant="outline" />
        <BatchStatusBadge status="confermato" variant="solid" />
      </div>
    </div>
  </div>
)

export const EfficiencyMeterExamples = () => (
  <div className="space-y-4 p-4">
    <h3 className="text-lg font-semibold">EfficiencyMeter Examples</h3>
    
    <div className="space-y-4 max-w-md">
      <div>
        <h4 className="font-medium mb-2">Different Efficiency Levels:</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-4">
            <span className="w-20 text-sm">Poor (25%):</span>
            <EfficiencyMeter percentage={25} showLabel />
          </div>
          <div className="flex items-center gap-4">
            <span className="w-20 text-sm">Average (50%):</span>
            <EfficiencyMeter percentage={50} showLabel />
          </div>
          <div className="flex items-center gap-4">
            <span className="w-20 text-sm">Good (75%):</span>
            <EfficiencyMeter percentage={75} showLabel />
          </div>
          <div className="flex items-center gap-4">
            <span className="w-20 text-sm">Excellent (90%):</span>
            <EfficiencyMeter percentage={90} showLabel />
          </div>
        </div>
      </div>

      <div>
        <h4 className="font-medium mb-2">Sizes:</h4>
        <div className="space-y-2">
          <EfficiencyMeter percentage={65} size="sm" showLabel />
          <EfficiencyMeter percentage={75} size="md" showLabel />
          <EfficiencyMeter percentage={85} size="lg" showLabel />
        </div>
      </div>
    </div>
  </div>
)

export const ToolPositionCardExamples = () => (
  <div className="space-y-4 p-4">
    <h3 className="text-lg font-semibold">ToolPositionCard Examples</h3>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
      <ToolPositionCard tool={mockTool} />
      <ToolPositionCard 
        tool={{...mockTool, rotated: true, odl_id: 2}} 
        selected 
      />
      <ToolPositionCard 
        tool={{...mockTool, excluded: true, odl_id: 3}} 
      />
    </div>
  </div>
)

export const AutoclaveInfoCardExamples = () => (
  <div className="space-y-4 p-4">
    <h3 className="text-lg font-semibold">AutoclaveInfoCard Examples</h3>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
      <AutoclaveInfoCard 
        autoclave={mockAutoclave} 
        efficiency={75}
        metrics={mockBatchData.metrics}
      />
      <AutoclaveInfoCard 
        autoclave={{...mockAutoclave, nome: 'ISMAR', codice: 'ISM001'}} 
        efficiency={45}
      />
    </div>
  </div>
)

export const NestingCanvasExample = () => (
  <div className="space-y-4 p-4">
    <h3 className="text-lg font-semibold">NestingCanvas Example</h3>
    
    <div className="max-w-4xl">
      <NestingCanvas 
        batchData={mockBatchData}
        showControls={true}
        showGrid={true}
        showRuler={true}
      />
    </div>
  </div>
)

// Main examples component
export const NestingComponentsExamples = () => (
  <div className="space-y-8">
    <h1 className="text-2xl font-bold">Nesting UI Components Library</h1>
    <p className="text-muted-foreground">
      A comprehensive collection of React components for nesting visualization in CarbonPilot.
    </p>
    
    <BatchStatusBadgeExamples />
    <EfficiencyMeterExamples />
    <ToolPositionCardExamples />
    <AutoclaveInfoCardExamples />
    <NestingCanvasExample />
  </div>
) 