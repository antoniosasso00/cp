'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Clock, AlertTriangle, Info } from 'lucide-react';

// Tipi per i dati temporali degli stati
export interface ODLStateTimestamp {
  stato: string;
  inizio: string;
  fine?: string;
  durata_minuti?: number;
}

export interface ODLProgressData {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
  timestamps: ODLStateTimestamp[];
  tempo_totale_stimato?: number;
}

interface OdlProgressBarProps {
  odl: ODLProgressData;
  showDetails?: boolean;
  className?: string;
  onTimelineClick?: () => void;
}

// Configurazione colori e ordine degli stati
const STATI_CONFIG = {
  'Preparazione': { 
    color: 'bg-gray-400', 
    textColor: 'text-gray-700',
    order: 1,
    icon: '📋'
  },
  'Laminazione': { 
    color: 'bg-blue-500', 
    textColor: 'text-blue-700',
    order: 2,
    icon: '🔧'
  },
  'In Coda': { 
    color: 'bg-orange-400', 
    textColor: 'text-orange-700',
    order: 2.5,
    icon: '⏳'
  },
  'Attesa Cura': { 
    color: 'bg-yellow-500', 
    textColor: 'text-yellow-700',
    order: 3,
    icon: '⏱️'
  },
  'Cura': { 
    color: 'bg-red-500', 
    textColor: 'text-red-700',
    order: 4,
    icon: '🔥'
  },
  'Finito': { 
    color: 'bg-green-500', 
    textColor: 'text-green-700',
    order: 5,
    icon: '✅'
  }
};

export function OdlProgressBar({ 
  odl, 
  showDetails = true, 
  className = '',
  onTimelineClick 
}: OdlProgressBarProps) {
  
  // Validazione e sanitizzazione dei dati in ingresso
  const sanitizeOdlData = (data: ODLProgressData): ODLProgressData => {
    return {
      ...data,
      timestamps: Array.isArray(data.timestamps) ? data.timestamps : [],
      status: data.status || 'Preparazione',
      created_at: data.created_at || new Date().toISOString(),
      updated_at: data.updated_at || new Date().toISOString()
    };
  };

  const sanitizedOdl = sanitizeOdlData(odl);

  // Calcola la durata totale effettiva
  const calcolaDurataTotale = (): number => {
    if (!sanitizedOdl.timestamps || sanitizedOdl.timestamps.length === 0) {
      // Fallback: calcola durata dall'inizio dell'ODL
      const now = new Date();
      const created = new Date(sanitizedOdl.created_at);
      return Math.floor((now.getTime() - created.getTime()) / (1000 * 60));
    }
    
    return sanitizedOdl.timestamps.reduce((total, timestamp) => {
      return total + (timestamp.durata_minuti || 0);
    }, 0);
  };

  // Formatta la durata in formato leggibile
  const formatDurata = (minuti: number): string => {
    if (minuti < 60) {
      return `${minuti}m`;
    }
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return min > 0 ? `${ore}h ${min}m` : `${ore}h`;
  };

  // Genera segmenti di fallback basati sullo stato corrente
  const generaSegmentiFallback = () => {
    const statiOrdinati = Object.keys(STATI_CONFIG).sort((a, b) => 
      STATI_CONFIG[a as keyof typeof STATI_CONFIG].order - STATI_CONFIG[b as keyof typeof STATI_CONFIG].order
    );
    
    const indiceCorrente = statiOrdinati.indexOf(sanitizedOdl.status);
    const durataTotale = calcolaDurataTotale();
    
    if (indiceCorrente === -1) {
      // Stato non riconosciuto, mostra solo lo stato corrente
      return [{
        stato: sanitizedOdl.status,
        inizio: sanitizedOdl.created_at,
        fine: undefined,
        durata_minuti: durataTotale,
        percentuale: 100,
        isEstimated: true
      }];
    }
    
    // Crea segmenti per tutti gli stati fino a quello corrente
    const segmenti = [];
    const durataPerStato = Math.floor(durataTotale / (indiceCorrente + 1));
    
    for (let i = 0; i <= indiceCorrente; i++) {
      const stato = statiOrdinati[i];
      const isCorrente = i === indiceCorrente;
      const durata = isCorrente ? durataTotale - (durataPerStato * i) : durataPerStato;
      
      segmenti.push({
        stato,
        inizio: sanitizedOdl.created_at,
        fine: isCorrente ? undefined : sanitizedOdl.updated_at,
        durata_minuti: durata,
        percentuale: (durata / durataTotale) * 100,
        isEstimated: true
      });
    }
    
    return segmenti;
  };

  // Calcola la percentuale di ogni segmento
  const calcolaPercentuali = () => {
    // Se non ci sono timestamps, usa i segmenti di fallback
    if (!sanitizedOdl.timestamps || sanitizedOdl.timestamps.length === 0) {
      return generaSegmentiFallback();
    }
    
    const durataTotale = calcolaDurataTotale();
    if (durataTotale === 0) return generaSegmentiFallback();

    return sanitizedOdl.timestamps.map(timestamp => ({
      ...timestamp,
      percentuale: ((timestamp.durata_minuti || 0) / durataTotale) * 100,
      isEstimated: false
    }));
  };

  // Determina se un ODL è in ritardo (più di 24h nello stato corrente)
  const isInRitardo = (): boolean => {
    const now = new Date();
    const lastUpdate = new Date(sanitizedOdl.updated_at);
    const diffHours = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60);
    return diffHours > 24 && sanitizedOdl.status !== 'Finito';
  };

  // Calcola il tempo stimato vs reale per evidenziare ritardi
  const calcolaScostamentoTempo = (): { scostamento: number; percentuale: number } => {
    const durataTotale = calcolaDurataTotale();
    const tempoStimato = sanitizedOdl.tempo_totale_stimato || 480; // Default 8 ore
    const scostamento = durataTotale - tempoStimato;
    const percentuale = tempoStimato > 0 ? (scostamento / tempoStimato) * 100 : 0;
    return { scostamento, percentuale };
  };

  // Ottieni il timestamp corrente
  const getCurrentTimestamp = () => {
    if (!sanitizedOdl.timestamps || sanitizedOdl.timestamps.length === 0) return null;
    return sanitizedOdl.timestamps.find(t => t.stato === sanitizedOdl.status);
  };

  // Determina se stiamo usando dati stimati
  const isUsingEstimatedData = (): boolean => {
    return !sanitizedOdl.timestamps || sanitizedOdl.timestamps.length === 0;
  };

  const segmenti = calcolaPercentuali();
  const durataTotale = calcolaDurataTotale();
  const currentTimestamp = getCurrentTimestamp();
  const inRitardo = isInRitardo();
  const scostamento = calcolaScostamentoTempo();
  const usingEstimatedData = isUsingEstimatedData();

  return (
    <TooltipProvider>
      <div className={`space-y-3 ${className}`}>
        {/* Header con informazioni generali */}
        {showDetails && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                ODL #{sanitizedOdl.id}
              </Badge>
              <Badge 
                variant={sanitizedOdl.status === 'Finito' ? 'default' : 'secondary'}
                className={`text-xs ${STATI_CONFIG[sanitizedOdl.status as keyof typeof STATI_CONFIG]?.textColor || ''}`}
              >
                {STATI_CONFIG[sanitizedOdl.status as keyof typeof STATI_CONFIG]?.icon} {sanitizedOdl.status}
              </Badge>
              {inRitardo && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  In Ritardo
                </Badge>
              )}
              {usingEstimatedData && (
                <Badge variant="outline" className="text-xs text-blue-600">
                  <Info className="h-3 w-3 mr-1" />
                  Stimato
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>Totale: {formatDurata(durataTotale)}</span>
              {sanitizedOdl.tempo_totale_stimato && (
                <span className={`text-xs ${scostamento.percentuale > 20 ? 'text-red-600' : scostamento.percentuale > 10 ? 'text-orange-600' : 'text-green-600'}`}>
                  (Stima: {formatDurata(sanitizedOdl.tempo_totale_stimato)})
                </span>
              )}
              {onTimelineClick && (
                <button
                  onClick={onTimelineClick}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  Storico
                </button>
              )}
            </div>
          </div>
        )}

        {/* Barra di progresso segmentata */}
        <div className="relative">
          <div className="flex h-6 bg-gray-200 rounded-lg overflow-hidden">
            {segmenti.length > 0 ? (
              segmenti.map((segmento, index) => {
                const config = STATI_CONFIG[segmento.stato as keyof typeof STATI_CONFIG];
                const isCurrentState = segmento.stato === sanitizedOdl.status;
                
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div
                        className={`
                          ${config?.color || 'bg-gray-400'} 
                          transition-all duration-300 hover:opacity-80
                          ${isCurrentState ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
                          ${segmento.percentuale < 5 ? 'min-w-[4px]' : ''}
                          ${segmento.isEstimated ? 'opacity-75 border-2 border-dashed border-white' : ''}
                        `}
                        style={{ width: `${Math.max(segmento.percentuale, 2)}%` }}
                      />
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-center">
                        <div className="font-medium">
                          {config?.icon} {segmento.stato}
                          {segmento.isEstimated && <span className="text-blue-400 ml-1">(stimato)</span>}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Durata: {formatDurata(segmento.durata_minuti || 0)}
                        </div>
                        {segmento.inizio && !segmento.isEstimated && (
                          <div className="text-xs text-muted-foreground">
                            Inizio: {new Date(segmento.inizio).toLocaleDateString('it-IT', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        )}
                        {segmento.fine && !segmento.isEstimated && (
                          <div className="text-xs text-muted-foreground">
                            Fine: {new Date(segmento.fine).toLocaleDateString('it-IT', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        )}
                        {segmento.isEstimated && (
                          <div className="text-xs text-blue-400">
                            Dati stimati - Timeline non disponibile
                          </div>
                        )}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })
            ) : (
              // Barra vuota se non ci sono dati (caso estremo)
              <div className="w-full bg-gray-300 flex items-center justify-center">
                <span className="text-xs text-gray-600">Stato sconosciuto</span>
              </div>
            )}
          </div>

          {/* Indicatore stato corrente */}
          {(currentTimestamp && !currentTimestamp.fine) || usingEstimatedData && (
            <div className="absolute -top-1 -bottom-1 right-0 w-1 bg-blue-600 rounded-full animate-pulse" />
          )}
        </div>

        {/* Legenda dettagliata (opzionale) */}
        {showDetails && segmenti.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
            {Object.entries(STATI_CONFIG).map(([stato, config]) => {
              const segmento = segmenti.find(s => s.stato === stato);
              const isActive = segmento !== undefined;
              const isCurrent = stato === sanitizedOdl.status;
              
              return (
                <div 
                  key={stato}
                  className={`
                    flex items-center gap-1 p-1 rounded
                    ${isActive ? 'bg-gray-50' : 'opacity-50'}
                    ${isCurrent ? 'ring-1 ring-blue-300' : ''}
                  `}
                >
                  <div 
                    className={`w-3 h-3 rounded-sm ${config.color} ${segmento?.isEstimated ? 'opacity-75 border border-dashed border-gray-400' : ''}`}
                  />
                  <span className={`text-xs ${isActive ? 'font-medium' : ''}`}>
                    {config.icon} {stato}
                  </span>
                  {segmento && (
                    <span className="text-xs text-muted-foreground ml-auto">
                      {formatDurata(segmento.durata_minuti || 0)}
                      {segmento.isEstimated && <span className="text-blue-400">*</span>}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Informazioni aggiuntive per dati incompleti */}
        {usingEstimatedData && (
          <div className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 p-2 rounded">
            <Info className="h-4 w-4" />
            <span>
              Dati temporali stimati - La timeline dettagliata sarà disponibile dopo il primo cambio di stato
              {durataTotale > 0 && ` (tempo dall'inizio: ${formatDurata(durataTotale)})`}
            </span>
          </div>
        )}

        {durataTotale === 0 && !usingEstimatedData && (
          <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
            <AlertTriangle className="h-4 w-4" />
            <span>Dati temporali incompleti - Alcuni timestamp potrebbero mancare</span>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}

// Funzione di utilità per creare dati di test
export const createTestODLData = (overrides: Partial<ODLProgressData> = {}): ODLProgressData => {
  const now = new Date();
  const created = new Date(now.getTime() - 2 * 60 * 60 * 1000); // 2 ore fa
  
  return {
    id: 1,
    status: 'Laminazione',
    created_at: created.toISOString(),
    updated_at: now.toISOString(),
    timestamps: [],
    tempo_totale_stimato: 480,
    ...overrides
  };
}; 