/**
 * Componente per visualizzare lo stato del nesting con indicatori di sincronizzazione.
 * 
 * Mostra:
 * - Stato attuale del nesting
 * - Stato degli ODL correlati
 * - Stato dell'autoclave associata
 * - Indicatori di coerenza
 */

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { 
  CheckCircle, 
  Clock, 
  Play, 
  Zap, 
  CheckSquare,
  AlertTriangle,
  Factory,
  FileText
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NestingStateIndicatorProps {
  nestingState: string
  odlStates?: Array<{
    id: string
    status: string
    parte_codice?: string
  }>
  autoclaveState?: {
    nome: string
    stato: string
  }
  className?: string
  showDetails?: boolean
}

// Configurazione degli stati con icone e colori
const STATE_CONFIG = {
  // Stati Nesting
  'bozza': {
    icon: FileText,
    color: 'bg-gray-100 text-gray-800 border-gray-300',
    label: 'Bozza',
    description: 'Nesting in fase di definizione'
  },
  'confermato': {
    icon: CheckCircle,
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    label: 'Confermato',
    description: 'Nesting confermato, pronto per caricamento'
  },
  'in sospeso': {
    icon: Clock,
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    label: 'In Sospeso',
    description: 'Nesting in attesa di caricamento'
  },
  'caricato': {
    icon: Play,
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    label: 'Caricato',
    description: 'Nesting caricato in autoclave'
  },
  'cura': {
    icon: Zap,
    color: 'bg-purple-100 text-purple-800 border-purple-300',
    label: 'In Cura',
    description: 'Processo di cura in corso'
  },
  'finito': {
    icon: CheckSquare,
    color: 'bg-green-100 text-green-800 border-green-300',
    label: 'Finito',
    description: 'Processo completato'
  },
  
  // Stati ODL
  'preparazione': {
    icon: FileText,
    color: 'bg-gray-100 text-gray-600',
    label: 'Preparazione'
  },
  'laminazione': {
    icon: Factory,
    color: 'bg-blue-100 text-blue-600',
    label: 'Laminazione'
  },
  'in coda': {
    icon: Clock,
    color: 'bg-yellow-100 text-yellow-600',
    label: 'In Coda'
  },
  'attesa cura': {
    icon: Clock,
    color: 'bg-orange-100 text-orange-600',
    label: 'Attesa Cura'
  },
  
  // Stati Autoclave
  'disponibile': {
    icon: CheckCircle,
    color: 'bg-green-100 text-green-600',
    label: 'Disponibile'
  },
  'in_uso': {
    icon: Zap,
    color: 'bg-purple-100 text-purple-600',
    label: 'In Uso'
  },
  'manutenzione': {
    icon: AlertTriangle,
    color: 'bg-red-100 text-red-600',
    label: 'Manutenzione'
  }
}

// Verifica coerenza stati
const checkStateConsistency = (
  nestingState: string,
  odlStates: Array<{status: string}>,
  autoclaveState?: {stato: string}
) => {
  const issues: string[] = []
  
  // Regole di coerenza
  if (nestingState === 'confermato') {
    const odlNonPronti = odlStates.filter(odl => odl.status.toLowerCase() !== 'attesa cura')
    if (odlNonPronti.length > 0) {
      issues.push(`${odlNonPronti.length} ODL non in "Attesa Cura"`)
    }
  }
  
  if (nestingState === 'caricato' || nestingState === 'cura') {
    const odlNonInCura = odlStates.filter(odl => odl.status.toLowerCase() !== 'cura')
    if (odlNonInCura.length > 0) {
      issues.push(`${odlNonInCura.length} ODL non in "Cura"`)
    }
    
    if (autoclaveState && autoclaveState.stato.toLowerCase() !== 'in_uso') {
      issues.push('Autoclave non in uso')
    }
  }
  
  if (nestingState === 'finito') {
    const odlNonFiniti = odlStates.filter(odl => odl.status.toLowerCase() !== 'finito')
    if (odlNonFiniti.length > 0) {
      issues.push(`${odlNonFiniti.length} ODL non completati`)
    }
    
    if (autoclaveState && autoclaveState.stato.toLowerCase() === 'in_uso') {
      issues.push('Autoclave ancora in uso')
    }
  }
  
  return issues
}

export function NestingStateIndicator({
  nestingState,
  odlStates = [],
  autoclaveState,
  className,
  showDetails = true
}: NestingStateIndicatorProps) {
  const normalizedState = nestingState.toLowerCase()
  const stateConfig = STATE_CONFIG[normalizedState as keyof typeof STATE_CONFIG]
  const StateIcon = stateConfig?.icon || FileText
  
  // Verifica coerenza
  const consistencyIssues = checkStateConsistency(normalizedState, odlStates, autoclaveState)
  const isConsistent = consistencyIssues.length === 0
  
  // Raggruppa ODL per stato
  const odlByState = odlStates.reduce((acc, odl) => {
    const state = odl.status.toLowerCase()
    if (!acc[state]) acc[state] = []
    acc[state].push(odl)
    return acc
  }, {} as Record<string, typeof odlStates>)

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <StateIcon className="h-4 w-4" />
          Stato Nesting
          {!isConsistent && (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Stato principale del nesting */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Nesting:</span>
          <Badge 
            variant="outline" 
            className={cn("border", stateConfig?.color)}
          >
            <StateIcon className="h-3 w-3 mr-1" />
            {stateConfig?.label || nestingState}
          </Badge>
        </div>
        
        {showDetails && (
          <>
            <Separator />
            
            {/* Stati ODL */}
            {odlStates.length > 0 && (
              <div className="space-y-2">
                <span className="text-sm font-medium">ODL ({odlStates.length}):</span>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(odlByState).map(([state, odls]) => {
                    const odlConfig = STATE_CONFIG[state as keyof typeof STATE_CONFIG]
                    const OdlIcon = odlConfig?.icon || FileText
                    
                    return (
                      <div key={state} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1">
                          <OdlIcon className="h-3 w-3" />
                          <span>{odlConfig?.label || state}</span>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {odls.length}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
            
            {/* Stato Autoclave */}
            {autoclaveState && (
              <>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Autoclave:</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {autoclaveState.nome}
                    </span>
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "text-xs",
                        STATE_CONFIG[autoclaveState.stato.toLowerCase() as keyof typeof STATE_CONFIG]?.color
                      )}
                    >
                      {STATE_CONFIG[autoclaveState.stato.toLowerCase() as keyof typeof STATE_CONFIG]?.label || autoclaveState.stato}
                    </Badge>
                  </div>
                </div>
              </>
            )}
            
            {/* Indicatori di inconsistenza */}
            {!isConsistent && (
              <>
                <Separator />
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-amber-600">
                    <AlertTriangle className="h-3 w-3" />
                    <span className="text-xs font-medium">Inconsistenze rilevate:</span>
                  </div>
                  {consistencyIssues.map((issue, index) => (
                    <div key={index} className="text-xs text-amber-600 ml-4">
                      • {issue}
                    </div>
                  ))}
                </div>
              </>
            )}
            
            {/* Indicatore di coerenza */}
            {isConsistent && (
              <>
                <Separator />
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  <span className="text-xs">Stati sincronizzati</span>
                </div>
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
} 