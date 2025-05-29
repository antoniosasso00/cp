'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Layers } from 'lucide-react'
import { MultiBatchNesting } from '@/components/nesting/MultiBatchNesting'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function MultiAutoclaveTab() {
  const [error, setError] = useState<string | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Multi-Autoclave
        </CardTitle>
        <CardDescription>
          Gestisci nesting complessi che utilizzano multiple autoclavi simultaneamente. 
          Ottimizza la distribuzione dei tool su più autoclavi per massimizzare l'efficienza produttiva.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Informazioni sul Multi-Batch */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-medium text-green-900 mb-2">🚀 Vantaggi Multi-Autoclave</h4>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• <strong>Maggiore throughput:</strong> Utilizza più autoclavi contemporaneamente</li>
              <li>• <strong>Ottimizzazione globale:</strong> Distribuzione intelligente dei carichi</li>
              <li>• <strong>Riduzione tempi:</strong> Parallelizzazione dei processi di curing</li>
              <li>• <strong>Flessibilità:</strong> Adattamento automatico alle autoclavi disponibili</li>
            </ul>
          </div>

          {/* Componente Multi-Batch */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                Errore nel caricamento del sistema multi-autoclave: {error}
              </AlertDescription>
            </Alert>
          )}
          
          <MultiBatchNesting />

          {/* Note operative */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">📋 Note Operative</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Verifica che tutte le autoclavi selezionate siano disponibili</li>
              <li>• Controlla i parametri di temperatura e pressione per ogni autoclave</li>
              <li>• Assicurati che i tool siano compatibili con le autoclavi assegnate</li>
              <li>• Monitora i tempi di ciclo per sincronizzare le operazioni</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 