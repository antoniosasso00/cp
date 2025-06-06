'use client'

import React from 'react'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  User, 
  Calendar,
  ArrowRight
} from 'lucide-react'

interface BatchNestingResult {
  id: string
  stato: string
  created_at: string
  updated_at?: string
  numero_nesting: number
}

interface HistoryPanelProps {
  batch: BatchNestingResult
}

interface HistoryEvent {
  id: string
  evento: string
  timestamp: string
  utente?: string
  ruolo?: string
  dettagli?: string
  stato_precedente?: string
  stato_nuovo?: string
}

export default function HistoryPanel({ batch }: HistoryPanelProps) {
  // Genera eventi basati sui dati disponibili
  const generateEvents = (): HistoryEvent[] => {
    const events: HistoryEvent[] = []

    // Evento creazione
    events.push({
      id: '1',
      evento: 'Batch Generato',
      timestamp: batch.created_at,
      utente: 'Sistema',
      ruolo: 'AUTOMATICO',
      dettagli: `Nesting #${batch.numero_nesting} generato dall'algoritmo di ottimizzazione`,
      stato_nuovo: 'sospeso'
    })

    // Se c'è updated_at e è diverso da created_at, aggiungi evento aggiornamento
    if (batch.updated_at && batch.updated_at !== batch.created_at) {
      events.push({
        id: '2',
        evento: batch.stato === 'confermato' ? 'Batch Confermato' : 'Batch Aggiornato',
        timestamp: batch.updated_at,
        utente: 'Operatore',
        ruolo: 'OPERATORE',
        dettagli: batch.stato === 'confermato' 
          ? 'Batch confermato e pronto per il caricamento in autoclave'
          : 'Aggiornamento dello stato del batch',
        stato_precedente: 'sospeso',
        stato_nuovo: batch.stato
      })
    }

    // Ordina per timestamp (più recenti prima)
    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }

  const events = generateEvents()

  const getEventIcon = (evento: string) => {
    switch (evento) {
      case 'Batch Generato':
        return <Clock className="h-4 w-4 text-blue-600" />
      case 'Batch Confermato':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'Batch Aggiornato':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getEventColor = (evento: string) => {
    switch (evento) {
      case 'Batch Generato':
        return 'bg-blue-50 border-blue-200'
      case 'Batch Confermato':
        return 'bg-green-50 border-green-200'
      case 'Batch Aggiornato':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getRuoloBadge = (ruolo: string) => {
    switch (ruolo) {
      case 'AUTOMATICO':
        return <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">Sistema</Badge>
      case 'OPERATORE':
        return <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">Operatore</Badge>
      case 'SUPERVISORE':
        return <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700">Supervisore</Badge>
      default:
        return <Badge variant="outline" className="text-xs">{ruolo}</Badge>
    }
  }

  return (
    <div className="space-y-4">
      <h4 className="font-medium text-sm text-gray-700 flex items-center gap-2">
        <Calendar className="h-4 w-4" />
        Cronologia Eventi
      </h4>

      {events.length > 0 ? (
        <div className="space-y-3">
          {events.map((event, index) => (
            <div 
              key={event.id}
              className={`p-3 rounded border ${getEventColor(event.evento)}`}
            >
              {/* Header evento */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getEventIcon(event.evento)}
                  <span className="font-medium text-sm">{event.evento}</span>
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(event.timestamp).toLocaleString('it-IT')}
                </div>
              </div>

              {/* Dettagli evento */}
              {event.dettagli && (
                <p className="text-xs text-gray-600 mb-2">{event.dettagli}</p>
              )}

              {/* Cambio stato */}
              {event.stato_precedente && event.stato_nuovo && (
                <div className="flex items-center gap-2 text-xs">
                  <Badge variant="outline" className="bg-white">
                    {event.stato_precedente}
                  </Badge>
                  <ArrowRight className="h-3 w-3 text-gray-400" />
                  <Badge variant="outline" className="bg-white">
                    {event.stato_nuovo}
                  </Badge>
                </div>
              )}

              {/* Footer con utente */}
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-current border-opacity-20">
                <div className="flex items-center gap-1">
                  <User className="h-3 w-3 text-gray-500" />
                  <span className="text-xs text-gray-600">{event.utente || 'N/A'}</span>
                </div>
                {event.ruolo && getRuoloBadge(event.ruolo)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-gray-500">
          <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Nessun evento registrato</p>
        </div>
      )}

      {/* Info aggiuntive */}
      <div className="mt-4 p-2 bg-gray-50 rounded text-xs text-gray-600">
        <div className="flex items-center gap-1 mb-1">
          <Clock className="h-3 w-3" />
          <span className="font-medium">Informazioni Temporali</span>
        </div>
        <div className="space-y-1 pl-4">
          <div>Creato: {new Date(batch.created_at).toLocaleString('it-IT')}</div>
          {batch.updated_at && batch.updated_at !== batch.created_at && (
            <div>Aggiornato: {new Date(batch.updated_at).toLocaleString('it-IT')}</div>
          )}
          <div>Stato Attuale: <span className="font-medium capitalize">{batch.stato}</span></div>
        </div>
      </div>
    </div>
  )
} 