'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Settings, RefreshCw, RotateCcw, Loader2 } from 'lucide-react'

export interface NestingParameters {
  distanza_perimetrale_cm: number
  spaziatura_tra_tool_cm: number
  rotazione_tool_abilitata: boolean
  priorita_ottimizzazione: 'PESO' | 'AREA' | 'EQUILIBRATO'
}

interface NestingParametersPanelProps {
  parameters: NestingParameters
  onParametersChange: (parameters: NestingParameters) => void
  onRegeneratePreview: () => void
  isRegenerating?: boolean
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

const DEFAULT_PARAMETERS: NestingParameters = {
  distanza_perimetrale_cm: 1.0,
  spaziatura_tra_tool_cm: 0.5,
  rotazione_tool_abilitata: true,
  priorita_ottimizzazione: 'EQUILIBRATO'
}

export function NestingParametersPanel({
  parameters,
  onParametersChange,
  onRegeneratePreview,
  isRegenerating = false,
  isCollapsed = false,
  onToggleCollapse
}: NestingParametersPanelProps) {
  const [localParameters, setLocalParameters] = useState<NestingParameters>(parameters)
  const [hasChanges, setHasChanges] = useState(false)

  // Sincronizza i parametri locali quando cambiano quelli esterni
  useEffect(() => {
    setLocalParameters(parameters)
    setHasChanges(false)
  }, [parameters])

  // Controlla se ci sono modifiche rispetto ai parametri originali
  useEffect(() => {
    const changed = JSON.stringify(localParameters) !== JSON.stringify(parameters)
    setHasChanges(changed)
  }, [localParameters, parameters])

  const handleParameterChange = (key: keyof NestingParameters, value: any) => {
    const newParameters = { ...localParameters, [key]: value }
    setLocalParameters(newParameters)
  }

  const handleApplyChanges = () => {
    onParametersChange(localParameters)
    onRegeneratePreview()
  }

  const handleResetToDefaults = () => {
    setLocalParameters(DEFAULT_PARAMETERS)
    onParametersChange(DEFAULT_PARAMETERS)
    onRegeneratePreview()
  }

  const getPriorityDescription = (priority: string) => {
    switch (priority) {
      case 'PESO':
        return 'Ottimizza per il peso dei tool'
      case 'AREA':
        return 'Ottimizza per l\'area occupata'
      case 'EQUILIBRATO':
        return 'Bilanciamento tra peso e area'
      default:
        return ''
    }
  }

  if (isCollapsed) {
    return (
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Settings className="h-4 w-4" />
              Parametri Nesting
              {hasChanges && (
                <Badge variant="outline" className="text-xs">
                  Modifiche non applicate
                </Badge>
              )}
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleCollapse}
            >
              Espandi
            </Button>
          </div>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            ⚙️ Parametri Nesting
            {hasChanges && (
              <Badge variant="outline">
                Modifiche non applicate
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
              >
                Comprimi
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetToDefaults}
              disabled={isRegenerating}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Reset
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Distanza Perimetrale */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="distanza-perimetrale" className="text-sm font-medium">
                Distanza Perimetrale
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="distanza-perimetrale-input"
                  type="number"
                  value={localParameters.distanza_perimetrale_cm}
                  onChange={(e) => handleParameterChange('distanza_perimetrale_cm', parseFloat(e.target.value) || 0)}
                  min={0}
                  max={10}
                  step={0.1}
                  className="w-20 h-8 text-sm"
                />
                <span className="text-sm text-muted-foreground">cm</span>
              </div>
            </div>
            <Slider
              value={localParameters.distanza_perimetrale_cm}
              onValueChange={(value) => handleParameterChange('distanza_perimetrale_cm', value)}
              min={0}
              max={10}
              step={0.1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Distanza minima dal bordo dell'autoclave (0.0 - 10.0 cm)
            </p>
          </div>

          {/* Spaziatura tra Tool */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="spaziatura-tool" className="text-sm font-medium">
                Spaziatura tra Tool
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="spaziatura-tool-input"
                  type="number"
                  value={localParameters.spaziatura_tra_tool_cm}
                  onChange={(e) => handleParameterChange('spaziatura_tra_tool_cm', parseFloat(e.target.value) || 0)}
                  min={0}
                  max={5}
                  step={0.1}
                  className="w-20 h-8 text-sm"
                />
                <span className="text-sm text-muted-foreground">cm</span>
              </div>
            </div>
            <Slider
              value={localParameters.spaziatura_tra_tool_cm}
              onValueChange={(value) => handleParameterChange('spaziatura_tra_tool_cm', value)}
              min={0}
              max={5}
              step={0.1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Spazio minimo tra i tool (0.0 - 5.0 cm)
            </p>
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Rotazione Tool */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="rotazione-tool" className="text-sm font-medium">
                Rotazione Automatica Tool
              </Label>
              <Switch
                id="rotazione-tool"
                checked={localParameters.rotazione_tool_abilitata}
                onCheckedChange={(checked) => handleParameterChange('rotazione_tool_abilitata', checked)}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Permette la rotazione automatica dei tool per ottimizzare lo spazio
            </p>
          </div>

          {/* Priorità Ottimizzazione */}
          <div className="space-y-3">
            <Label htmlFor="priorita-ottimizzazione" className="text-sm font-medium">
              Priorità Ottimizzazione
            </Label>
            <Select
              value={localParameters.priorita_ottimizzazione}
              onValueChange={(value: 'PESO' | 'AREA' | 'EQUILIBRATO') => 
                handleParameterChange('priorita_ottimizzazione', value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona priorità" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PESO">
                  <div className="flex flex-col">
                    <span>Peso</span>
                    <span className="text-xs text-muted-foreground">Ottimizza per il peso</span>
                  </div>
                </SelectItem>
                <SelectItem value="AREA">
                  <div className="flex flex-col">
                    <span>Area</span>
                    <span className="text-xs text-muted-foreground">Ottimizza per l'area</span>
                  </div>
                </SelectItem>
                <SelectItem value="EQUILIBRATO">
                  <div className="flex flex-col">
                    <span>Equilibrato</span>
                    <span className="text-xs text-muted-foreground">Bilanciamento ottimale</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {getPriorityDescription(localParameters.priorita_ottimizzazione)}
            </p>
          </div>
        </div>

        {/* Pulsanti di azione */}
        {hasChanges && (
          <>
            <Separator />
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Hai modifiche non applicate. Clicca "Applica e Rigenera" per vedere l'anteprima aggiornata.
              </p>
              <Button
                onClick={handleApplyChanges}
                disabled={isRegenerating}
                className="ml-4"
              >
                {isRegenerating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Applica e Rigenera
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default NestingParametersPanel 