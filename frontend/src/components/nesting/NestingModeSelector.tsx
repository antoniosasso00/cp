'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  FileText, 
  Zap, 
  Layers, 
  ArrowRight, 
  Settings, 
  Users, 
  Clock 
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NestingMode {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  features: string[]
  complexity: 'Semplice' | 'Intermedio' | 'Avanzato'
  timeEstimate: string
  disabled?: boolean
  disabledReason?: string
}

interface NestingModeSelectorProps {
  onModeSelect: (mode: string) => void
  className?: string
}

const nestingModes: NestingMode[] = [
  {
    id: 'manual',
    title: 'Nesting Manuale',
    description: 'Crea layout personalizzati selezionando manualmente i tool da posizionare',
    icon: FileText,
    features: [
      'Controllo completo del layout',
      'Selezione manuale tool',
      'Preview in tempo reale',
      'Validazione automatica spazi'
    ],
    complexity: 'Semplice',
    timeEstimate: '5-10 min'
  },
  {
    id: 'automatic',
    title: 'Nesting Automatico Singolo',
    description: 'Lascia che l\'algoritmo ottimizzi automaticamente il layout per una singola autoclave',
    icon: Zap,
    features: [
      'Ottimizzazione automatica',
      'Parametri configurabili',
      'Massima efficienza spazio',
      'Algoritmi avanzati'
    ],
    complexity: 'Intermedio',
    timeEstimate: '2-5 min'
  },
  {
    id: 'multi-autoclave',
    title: 'Nesting Multi-Autoclave',
    description: 'Distribuisci automaticamente i tool su multiple autoclavi per ottimizzare la produzione',
    icon: Layers,
    features: [
      'Distribuzione multi-autoclave',
      'Batch processing',
      'Bilanciamento carico',
      'Pianificazione avanzata'
    ],
    complexity: 'Avanzato',
    timeEstimate: '10-15 min'
  }
]

export function NestingModeSelector({ onModeSelect, className }: NestingModeSelectorProps) {
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Semplice': return 'bg-green-100 text-green-800'
      case 'Intermedio': return 'bg-yellow-100 text-yellow-800'
      case 'Avanzato': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div 
      className={cn("space-y-6", className)}
      data-nesting-mode-selector
    >
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold tracking-tight">
          Seleziona Modalità di Nesting
        </h2>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Scegli la modalità più adatta alle tue esigenze. Ogni modalità offre 
          strumenti specifici per ottimizzare il posizionamento dei tool nelle autoclavi.
        </p>
      </div>

      {/* Mode Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {nestingModes.map((mode) => {
          const Icon = mode.icon
          const isDisabled = mode.disabled

          return (
            <Card 
              key={mode.id}
              className={cn(
                "relative transition-all duration-200 cursor-pointer",
                "hover:shadow-lg hover:scale-105",
                isDisabled && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => !isDisabled && onModeSelect(mode.id)}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <Icon className="h-8 w-8 text-primary" />
                  <Badge 
                    variant="secondary" 
                    className={getComplexityColor(mode.complexity)}
                  >
                    {mode.complexity}
                  </Badge>
                </div>
                <CardTitle className="text-lg">{mode.title}</CardTitle>
                <CardDescription className="text-sm">
                  {mode.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features List */}
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-muted-foreground">
                    Caratteristiche:
                  </h4>
                  <ul className="space-y-1">
                    {mode.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full mr-2 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Time Estimate */}
                <div className="flex items-center text-sm text-muted-foreground">
                  <Clock className="h-4 w-4 mr-2" />
                  Tempo stimato: {mode.timeEstimate}
                </div>

                {/* Action Button */}
                <div className="pt-2">
                  {isDisabled ? (
                    <Button 
                      variant="outline" 
                      className="w-full" 
                      disabled
                    >
                      {mode.disabledReason || 'Non disponibile'}
                    </Button>
                  ) : (
                    <Button 
                      className="w-full group"
                      onClick={(e) => {
                        e.stopPropagation()
                        onModeSelect(mode.id)
                      }}
                    >
                      Inizia {mode.title}
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                  )}
                </div>
              </CardContent>

              {/* Disabled Overlay */}
              {isDisabled && (
                <div className="absolute inset-0 bg-gray-50 bg-opacity-50 flex items-center justify-center rounded-lg">
                  <Badge variant="destructive">
                    {mode.disabledReason || 'Non disponibile'}
                  </Badge>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      {/* Help Section */}
      <div className="bg-muted rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Settings className="h-5 w-5 text-primary" />
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold">Hai bisogno di aiuto?</h3>
            <p className="text-sm text-muted-foreground">
              Se non sei sicuro di quale modalità scegliere, inizia con il 
              <strong> Nesting Manuale</strong> per familiarizzare con l'interfaccia, 
              poi passa alle modalità automatiche per ottimizzazioni più avanzate.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 