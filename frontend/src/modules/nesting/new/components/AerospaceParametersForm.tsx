'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Label } from '@/shared/components/ui/label'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { Switch } from '@/shared/components/ui/switch'
import { Separator } from '@/shared/components/ui/separator'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Info, 
  Settings, 
  Plane,
  Gauge,
  Zap,
  Target,
  RotateCcw,
  Wind,
  Thermometer
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/components/ui/tooltip'

interface AerospaceParameters {
  // Parametri base
  padding_mm: number
  min_distance_mm: number
  vacuum_lines_capacity: number
  use_fallback: boolean
  allow_heuristic: boolean
  timeout_override?: number
  
  // Algoritmi avanzati
  use_multithread: boolean
  num_search_workers: number
  use_grasp_heuristic: boolean
  compactness_weight: number
  balance_weight: number
  area_weight: number
  max_iterations_grasp: number
  
  // Parametri aerospace avanzati
  enable_rotation_optimization: boolean
  heat_transfer_spacing: number
  airflow_margin: number
  composite_cure_pressure: number
  autoclave_efficiency_target: number
  enable_aerospace_constraints: boolean
  
  // Standard industriali
  boeing_787_mode: boolean
  airbus_a350_mode: boolean
  general_aviation_mode: boolean
}

interface AerospaceParametersFormProps {
  initialParameters?: Partial<AerospaceParameters>
  onParametersChange: (parameters: AerospaceParameters) => void
  className?: string
}

const AerospaceParametersForm: React.FC<AerospaceParametersFormProps> = ({
  initialParameters = {},
  onParametersChange,
  className = ""
}) => {
  
  const [parameters, setParameters] = useState<AerospaceParameters>({
    // Valori default aerospace ottimizzati
    padding_mm: 0.5,
    min_distance_mm: 0.5,
    vacuum_lines_capacity: 25,
    use_fallback: true,
    allow_heuristic: true,
    
    use_multithread: true,
    num_search_workers: 8,
    use_grasp_heuristic: true,
    compactness_weight: 0.10,
    balance_weight: 0.05,
    area_weight: 0.85,
    max_iterations_grasp: 5,
    
    enable_rotation_optimization: true,
    heat_transfer_spacing: 0.3,
    airflow_margin: 0.2,
    composite_cure_pressure: 0.7,
    autoclave_efficiency_target: 85.0,
    enable_aerospace_constraints: true,
    
    boeing_787_mode: false,
    airbus_a350_mode: false,
    general_aviation_mode: true,
    
    ...initialParameters
  })

  const updateParameter = (key: keyof AerospaceParameters, value: any) => {
    const newParameters = { ...parameters, [key]: value }
    setParameters(newParameters)
    onParametersChange(newParameters)
  }

  const applyPreset = (preset: 'boeing' | 'airbus' | 'general') => {
    let presetParams: Partial<AerospaceParameters> = {}
    
    switch (preset) {
      case 'boeing':
        presetParams = {
          padding_mm: 0.3,
          min_distance_mm: 0.3,
          heat_transfer_spacing: 0.5,
          composite_cure_pressure: 0.8,
          autoclave_efficiency_target: 90.0,
          boeing_787_mode: true,
          airbus_a350_mode: false,
          general_aviation_mode: false,
          num_search_workers: 12,
          max_iterations_grasp: 8
        }
        break
      case 'airbus':
        presetParams = {
          padding_mm: 0.4,
          min_distance_mm: 0.4,
          heat_transfer_spacing: 0.4,
          composite_cure_pressure: 0.7,
          autoclave_efficiency_target: 87.0,
          boeing_787_mode: false,
          airbus_a350_mode: true,
          general_aviation_mode: false,
          num_search_workers: 10,
          max_iterations_grasp: 7
        }
        break
      case 'general':
        presetParams = {
          padding_mm: 0.5,
          min_distance_mm: 0.5,
          heat_transfer_spacing: 0.3,
          composite_cure_pressure: 0.7,
          autoclave_efficiency_target: 85.0,
          boeing_787_mode: false,
          airbus_a350_mode: false,
          general_aviation_mode: true,
          num_search_workers: 8,
          max_iterations_grasp: 5
        }
        break
    }
    
    const newParameters = { ...parameters, ...presetParams }
    setParameters(newParameters)
    onParametersChange(newParameters)
  }

  const resetToDefaults = () => {
    applyPreset('general')
  }

  return (
    <TooltipProvider>
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plane className="h-5 w-5 text-blue-600" />
            Parametri Nesting Aerospace
            <Badge variant="outline" className="text-xs">
              Advanced
            </Badge>
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          
          {/* PRESET INDUSTRIALI */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold text-gray-700">Preset Standard Industriali</Label>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
              <Button
                variant={parameters.boeing_787_mode ? "default" : "outline"}
                size="sm"
                onClick={() => applyPreset('boeing')}
                className="text-xs"
              >
                <Plane className="h-3 w-3 mr-1" />
                Boeing 787
              </Button>
              <Button
                variant={parameters.airbus_a350_mode ? "default" : "outline"}
                size="sm"
                onClick={() => applyPreset('airbus')}
                className="text-xs"
              >
                <Plane className="h-3 w-3 mr-1" />
                Airbus A350
              </Button>
              <Button
                variant={parameters.general_aviation_mode ? "default" : "outline"}
                size="sm"
                onClick={() => applyPreset('general')}
                className="text-xs"
              >
                <Plane className="h-3 w-3 mr-1" />
                General Aviation
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={resetToDefaults}
                className="text-xs"
              >
                Reset
              </Button>
            </div>
          </div>

          <Separator />

          {/* PARAMETRI BASE */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Parametri Base
            </Label>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="padding" className="text-xs flex items-center gap-1">
                  Padding (mm)
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        <strong>Standard Aerospace:</strong><br/>
                        • Boeing 787: 0.3-0.5mm<br/>
                        • Airbus A350: 0.4-0.6mm<br/>
                        • General Aviation: 0.5-0.8mm<br/>
                        Ridurre per massimizzare efficienza
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Input
                  id="padding"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="2.0"
                  value={parameters.padding_mm}
                  onChange={(e) => updateParameter('padding_mm', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="min_distance" className="text-xs flex items-center gap-1">
                  Distanza Min (mm)
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        <strong>Heat Isolation Spacing (FAA AC 21-26A):</strong><br/>
                        Distanza minima per prevenire trasferimento calore tra tool durante la cura
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Input
                  id="min_distance"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="2.0"
                  value={parameters.min_distance_mm}
                  onChange={(e) => updateParameter('min_distance_mm', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="vacuum_lines" className="text-xs flex items-center gap-1">
                  Linee Vuoto
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        Capacità massima linee vuoto dell'autoclave. Aumentare per maggiore flessibilità di layout
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Input
                  id="vacuum_lines"
                  type="number"
                  min="10"
                  max="50"
                  value={parameters.vacuum_lines_capacity}
                  onChange={(e) => updateParameter('vacuum_lines_capacity', parseInt(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="efficiency_target" className="text-xs flex items-center gap-1">
                  Target Efficienza (%)
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        <strong>Benchmark Industriali:</strong><br/>
                        • Boeing 787: 85-90%<br/>
                        • Airbus A350: 87-92%<br/>
                        • General Aviation: 80-85%
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Input
                  id="efficiency_target"
                  type="number"
                  step="1"
                  min="50"
                  max="95"
                  value={parameters.autoclave_efficiency_target}
                  onChange={(e) => updateParameter('autoclave_efficiency_target', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* ALGORITMI AVANZATI */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Algoritmi Avanzati
            </Label>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="multithread" className="text-xs flex items-center gap-1">
                  Multi-Threading
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        Abilita parallelismo CP-SAT con múltipli workers per convergenza rapida (Airbus A350 standard)
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Switch
                  id="multithread"
                  checked={parameters.use_multithread}
                  onCheckedChange={(checked) => updateParameter('use_multithread', checked)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="workers" className="text-xs">Workers CP-SAT</Label>
                <Input
                  id="workers"
                  type="number"
                  min="1"
                  max="16"
                  value={parameters.num_search_workers}
                  onChange={(e) => updateParameter('num_search_workers', parseInt(e.target.value))}
                  className="text-xs"
                  disabled={!parameters.use_multithread}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="grasp" className="text-xs flex items-center gap-1">
                  GRASP Heuristic
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        Greedy Randomized Adaptive Search Procedure per ottimizzazione globale (Boeing 787 optimization)
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Switch
                  id="grasp"
                  checked={parameters.use_grasp_heuristic}
                  onCheckedChange={(checked) => updateParameter('use_grasp_heuristic', checked)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="grasp_iterations" className="text-xs">Iterazioni GRASP</Label>
                <Input
                  id="grasp_iterations"
                  type="number"
                  min="1"
                  max="20"
                  value={parameters.max_iterations_grasp}
                  onChange={(e) => updateParameter('max_iterations_grasp', parseInt(e.target.value))}
                  className="text-xs"
                  disabled={!parameters.use_grasp_heuristic}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* FUNZIONE OBIETTIVO */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Funzione Obiettivo Aerospace
            </Label>
            
            <div className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="area_weight" className="text-xs flex justify-between">
                  <span>Peso Area: {(parameters.area_weight * 100).toFixed(0)}%</span>
                  <Badge variant="outline" className="text-xs">Primario</Badge>
                </Label>
                <Input
                  id="area_weight"
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={parameters.area_weight}
                  onChange={(e) => updateParameter('area_weight', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="compactness_weight" className="text-xs flex justify-between">
                  <span>Peso Compattezza: {(parameters.compactness_weight * 100).toFixed(0)}%</span>
                </Label>
                <Input
                  id="compactness_weight"
                  type="range"
                  min="0.0"
                  max="0.3"
                  step="0.01"
                  value={parameters.compactness_weight}
                  onChange={(e) => updateParameter('compactness_weight', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="balance_weight" className="text-xs flex justify-between">
                  <span>Peso Bilanciamento: {(parameters.balance_weight * 100).toFixed(0)}%</span>
                </Label>
                <Input
                  id="balance_weight"
                  type="range"
                  min="0.0"
                  max="0.2"
                  step="0.01"
                  value={parameters.balance_weight}
                  onChange={(e) => updateParameter('balance_weight', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                Totale: {((parameters.area_weight + parameters.compactness_weight + parameters.balance_weight) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <Separator />

          {/* PARAMETRI AEROSPACE AVANZATI */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Thermometer className="h-4 w-4" />
              Parametri Aerospace Avanzati
            </Label>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="rotation" className="text-xs flex items-center gap-1">
                  <RotateCcw className="h-3 w-3" />
                  Rotazione Tool
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-3 w-3 text-gray-400" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs max-w-xs">
                        Abilita rotazione 90° dei tool per ottimizzare layout (standard aerospace)
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Switch
                  id="rotation"
                  checked={parameters.enable_rotation_optimization}
                  onCheckedChange={(checked) => updateParameter('enable_rotation_optimization', checked)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="heat_spacing" className="text-xs flex items-center gap-1">
                  <Thermometer className="h-3 w-3" />
                  Heat Transfer (mm)
                </Label>
                <Input
                  id="heat_spacing"
                  type="number"
                  step="0.1"
                  min="0.0"
                  max="1.0"
                  value={parameters.heat_transfer_spacing}
                  onChange={(e) => updateParameter('heat_transfer_spacing', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="airflow" className="text-xs flex items-center gap-1">
                  <Wind className="h-3 w-3" />
                  Airflow Margin (mm)
                </Label>
                <Input
                  id="airflow"
                  type="number"
                  step="0.1"
                  min="0.0"
                  max="1.0"
                  value={parameters.airflow_margin}
                  onChange={(e) => updateParameter('airflow_margin', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="pressure" className="text-xs flex items-center gap-1">
                  <Gauge className="h-3 w-3" />
                  Pressione Cura (bar)
                </Label>
                <Input
                  id="pressure"
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="2.0"
                  value={parameters.composite_cure_pressure}
                  onChange={(e) => updateParameter('composite_cure_pressure', parseFloat(e.target.value))}
                  className="text-xs"
                />
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="aerospace_constraints" className="text-xs flex items-center gap-1">
                Vincoli Aerospace
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-3 w-3 text-gray-400" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs max-w-xs">
                      Abilita vincoli specifici per manufacturing aerospace (FAA AC 21-26A compliance)
                    </p>
                  </TooltipContent>
                </Tooltip>
              </Label>
              <Switch
                id="aerospace_constraints"
                checked={parameters.enable_aerospace_constraints}
                onCheckedChange={(checked) => updateParameter('enable_aerospace_constraints', checked)}
              />
            </div>
          </div>

          {/* SUMMARY */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-xs text-blue-800">
              <div className="font-semibold mb-1">Configurazione Attuale:</div>
              <div className="space-y-1">
                {parameters.boeing_787_mode && <Badge className="mr-1 text-xs">Boeing 787 Mode</Badge>}
                {parameters.airbus_a350_mode && <Badge className="mr-1 text-xs">Airbus A350 Mode</Badge>}
                {parameters.general_aviation_mode && <Badge className="mr-1 text-xs">General Aviation Mode</Badge>}
                <div>Padding: {parameters.padding_mm}mm • Min Distance: {parameters.min_distance_mm}mm</div>
                <div>Workers: {parameters.num_search_workers} • Target: {parameters.autoclave_efficiency_target}%</div>
              </div>
            </div>
          </div>

        </CardContent>
      </Card>
    </TooltipProvider>
  )
}

export default AerospaceParametersForm 