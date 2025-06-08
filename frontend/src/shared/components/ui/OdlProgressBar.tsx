'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Clock, AlertTriangle, Info, TrendingUp, TrendingDown } from 'lucide-react';

// Tipi per i dati temporali degli stati
export interface ODLStateTimestamp {
  stato: string;
  inizio: string;
  fine?: string;
  durata_minuti?: number;
  fonte_dati?: 'tempo_fase' | 'state_log';
}

// ✅ NOVITÀ: Informazioni sui tempi di preparazione
export interface TempoPreparazioneInfo {
  minuti?: number;
  fonte?: 'preciso' | 'stimato';
  disponibile: boolean;
}

// ✅ NOVITÀ: Informazioni sulle fonti dati utilizzate
export interface FontiDatiInfo {
  tempo_fasi_count: number;
  state_logs_count: number;
  integrazione_attiva: boolean;
}

export interface ODLProgressData {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
  timestamps: ODLStateTimestamp[];
  tempo_totale_stimato?: number;
  has_timeline_data?: boolean;
  // ✅ NOVITÀ: Dati specifici per preparazione
  tempo_preparazione?: TempoPreparazioneInfo;
  fonti_dati?: FontiDatiInfo;
}

interface OdlProgressBarProps {
  odl: ODLProgressData;
  showDetails?: boolean;
  className?: string;
  onTimelineClick?: () => void;
}

// Configurazione colori e ordine degli stati con durata media stimata
const STATI_CONFIG = {
  'Preparazione': { 
    color: 'bg-gray-400', 
    textColor: 'text-gray-700',
    order: 1,
    icon: '📋',
    durata_media: 30 // minuti
  },
  'Laminazione': { 
    color: 'bg-blue-500', 
    textColor: 'text-blue-700',
    order: 2,
    icon: '🔧',
    durata_media: 120
  },
  'In Coda': { 
    color: 'bg-orange-400', 
    textColor: 'text-orange-700',
    order: 2.5,
    icon: '⏳',
    durata_media: 60
  },
  'Attesa Cura': { 
    color: 'bg-yellow-500', 
    textColor: 'text-yellow-700',
    order: 3,
    icon: '⏱️',
    durata_media: 240
  },
  'Cura': { 
    color: 'bg-red-500', 
    textColor: 'text-red-700',
    order: 4,
    icon: '🔥',
    durata_media: 360
  },
  'Finito': { 
    color: 'bg-green-500', 
    textColor: 'text-green-700',
    order: 5,
    icon: '✅',
    durata_media: 0
  }
};

// Costanti per il bilanciamento della visualizzazione
const MIN_SEGMENT_WIDTH = 8; // Percentuale minima per ogni segmento
const MAX_SEGMENT_WIDTH = 60; // Percentuale massima per evitare dominanza

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

  // Rimuove i rollback mantenendo solo l'ultima occorrenza di ogni stato
  const rimuoviRollback = (timestamps: ODLStateTimestamp[]): ODLStateTimestamp[] => {
    const statiVisti = new Map<string, ODLStateTimestamp>();
    
    // Ordina per data di inizio
    const timestampsOrdinati = [...timestamps].sort((a, b) => 
      new Date(a.inizio).getTime() - new Date(b.inizio).getTime()
    );
    
    // Mantieni solo l'ultima occorrenza di ogni stato
    timestampsOrdinati.forEach(timestamp => {
      statiVisti.set(timestamp.stato, timestamp);
    });
    
    // Ordina il risultato per ordine sequenziale degli stati
    return Array.from(statiVisti.values()).sort((a, b) => {
      const orderA = STATI_CONFIG[a.stato as keyof typeof STATI_CONFIG]?.order || 999;
      const orderB = STATI_CONFIG[b.stato as keyof typeof STATI_CONFIG]?.order || 999;
      return orderA - orderB;
    });
  };

  // Calcola durata totale senza rollback
  const calcolaDurataTotale = (): number => {
    const timestampsPuliti = rimuoviRollback(sanitizedOdl.timestamps);
    
    if (timestampsPuliti.length === 0) {
      const now = new Date();
      const created = new Date(sanitizedOdl.created_at);
      return Math.floor((now.getTime() - created.getTime()) / (1000 * 60));
    }
    
    return timestampsPuliti.reduce((total, timestamp) => {
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

  // Calcola proporzioni bilanciate per evitare segmenti troppo piccoli o grandi
  const calcolaProporzioniEque = (segmenti: ODLStateTimestamp[]): Array<ODLStateTimestamp & { percentuale: number; percentualeOriginale: number }> => {
    if (segmenti.length === 0) return [];
    
    const durataTotale = segmenti.reduce((sum, s) => sum + (s.durata_minuti || 0), 0);
    if (durataTotale === 0) {
      // Distribuzione equa se non ci sono durate
      const percentualeEguale = 100 / segmenti.length;
      return segmenti.map(s => ({
        ...s,
        percentuale: percentualeEguale,
        percentualeOriginale: percentualeEguale
      }));
    }
    
    // Calcola percentuali originali
    const segmentiConPercentuali = segmenti.map(s => ({
      ...s,
      percentualeOriginale: ((s.durata_minuti || 0) / durataTotale) * 100,
      percentuale: 0 // Sarà calcolata dopo
    }));
    
    // Bilancia le proporzioni
    let percentualiTotali = 0;
    const segmentiBilanciati = segmentiConPercentuali.map(s => {
      let percentualeBilanciata = s.percentualeOriginale;
      
      // Applica limiti minimi e massimi
      if (percentualeBilanciata < MIN_SEGMENT_WIDTH && segmenti.length > 1) {
        percentualeBilanciata = MIN_SEGMENT_WIDTH;
      } else if (percentualeBilanciata > MAX_SEGMENT_WIDTH && segmenti.length > 1) {
        percentualeBilanciata = MAX_SEGMENT_WIDTH;
      }
      
      percentualiTotali += percentualeBilanciata;
      return { ...s, percentuale: percentualeBilanciata };
    });
    
    // Riscala per mantenere il 100% totale
    if (percentualiTotali !== 100) {
      const fattoreScala = 100 / percentualiTotali;
      segmentiBilanciati.forEach(s => {
        s.percentuale *= fattoreScala;
      });
    }
    
    return segmentiBilanciati;
  };

  // Genera segmenti di fallback basati sullo stato corrente
  const generaSegmentiFallback = () => {
    const statiOrdinati = Object.keys(STATI_CONFIG).sort((a, b) => 
      STATI_CONFIG[a as keyof typeof STATI_CONFIG].order - STATI_CONFIG[b as keyof typeof STATI_CONFIG].order
    );
    
    const indiceCorrente = statiOrdinati.indexOf(sanitizedOdl.status);
    const durataTotale = calcolaDurataTotale();
    
    if (indiceCorrente === -1) {
      return [{
        stato: sanitizedOdl.status,
        inizio: sanitizedOdl.created_at,
        fine: undefined,
        durata_minuti: durataTotale,
        percentuale: 100,
        percentualeOriginale: 100,
        isEstimated: true
      }];
    }
    
    // Usa durate medie stimate per stati passati e corrente
    const segmenti = [];
    for (let i = 0; i <= indiceCorrente; i++) {
      const stato = statiOrdinati[i];
      const config = STATI_CONFIG[stato as keyof typeof STATI_CONFIG];
      const isCorrente = i === indiceCorrente;
      const durata = isCorrente ? Math.max(durataTotale * 0.3, config.durata_media) : config.durata_media;
      
      segmenti.push({
        stato,
        inizio: sanitizedOdl.created_at,
        fine: isCorrente ? undefined : sanitizedOdl.updated_at,
        durata_minuti: durata,
        isEstimated: true
      });
    }
    
    return calcolaProporzioniEque(segmenti).map(s => ({ ...s, isEstimated: true }));
  };

  // Calcola le percentuali equilibrate
  const calcolaPercentuali = () => {
    // Se non ci sono timestamps, usa i segmenti di fallback
    if (!sanitizedOdl.timestamps || sanitizedOdl.timestamps.length === 0) {
      return generaSegmentiFallback();
    }
    
    const timestampsPuliti = rimuoviRollback(sanitizedOdl.timestamps);
    if (timestampsPuliti.length === 0) return generaSegmentiFallback();

    return calcolaProporzioniEque(timestampsPuliti).map(s => ({ ...s, isEstimated: false }));
  };

  // Determina se un ODL è in ritardo
  const isInRitardo = (): boolean => {
    const now = new Date();
    const lastUpdate = new Date(sanitizedOdl.updated_at);
    const diffHours = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60);
    return diffHours > 24 && sanitizedOdl.status !== 'Finito';
  };

  // Calcola scostamento da tempo stimato
  const calcolaScostamentoTempo = (): { scostamento: number; percentuale: number; trend: 'up' | 'down' | 'stable' } => {
    const durataTotale = calcolaDurataTotale();
    const tempoStimato = sanitizedOdl.tempo_totale_stimato || 
      Object.values(STATI_CONFIG).reduce((sum, config) => sum + config.durata_media, 0);
    
    const scostamento = durataTotale - tempoStimato;
    const percentuale = tempoStimato > 0 ? (scostamento / tempoStimato) * 100 : 0;
    
    let trend: 'up' | 'down' | 'stable' = 'stable';
    if (Math.abs(percentuale) > 10) {
      trend = percentuale > 0 ? 'up' : 'down';
    }
    
    return { scostamento, percentuale, trend };
  };

  // Ottieni il timestamp corrente
  const getCurrentTimestamp = () => {
    const timestampsPuliti = rimuoviRollback(sanitizedOdl.timestamps);
    return timestampsPuliti.find(t => t.stato === sanitizedOdl.status);
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
              {sanitizedOdl.tempo_preparazione?.disponibile && (
                <Badge 
                  variant="outline" 
                  className={`text-xs ${
                    sanitizedOdl.tempo_preparazione.fonte === 'preciso' 
                      ? 'text-green-600 border-green-300' 
                      : 'text-orange-600 border-orange-300'
                  }`}
                >
                  <Clock className="h-3 w-3 mr-1" />
                  Prep: {sanitizedOdl.tempo_preparazione.fonte === 'preciso' ? 'Preciso' : 'Stimato'}
                </Badge>
              )}
              {sanitizedOdl.fonti_dati?.integrazione_attiva && (
                <Badge variant="outline" className="text-xs text-blue-600 border-blue-300">
                  <Info className="h-3 w-3 mr-1" />
                  Integrato
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>Totale: {formatDurata(durataTotale)}</span>
              </div>
              
              {sanitizedOdl.tempo_preparazione?.disponibile && sanitizedOdl.tempo_preparazione.minuti && (
                <div className={`flex items-center gap-1 ${
                  sanitizedOdl.tempo_preparazione.fonte === 'preciso' 
                    ? 'text-green-600' 
                    : 'text-orange-600'
                }`}>
                  <Clock className="h-3 w-3" />
                  <span>
                    Prep: {formatDurata(sanitizedOdl.tempo_preparazione.minuti)}
                  </span>
                </div>
              )}
              
              {sanitizedOdl.tempo_totale_stimato && (
                <div className={`flex items-center gap-1 ${
                  Math.abs(scostamento.percentuale) > 20 ? 'text-red-600' : 
                  Math.abs(scostamento.percentuale) > 10 ? 'text-orange-600' : 'text-green-600'
                }`}>
                  {scostamento.trend === 'up' ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : scostamento.trend === 'down' ? (
                    <TrendingDown className="h-3 w-3" />
                  ) : (
                    <Clock className="h-3 w-3" />
                  )}
                  <span>
                    Stima: {formatDurata(sanitizedOdl.tempo_totale_stimato)}
                    {Math.abs(scostamento.percentuale) > 5 && (
                      <span className="ml-1">
                        ({scostamento.percentuale > 0 ? '+' : ''}{scostamento.percentuale.toFixed(0)}%)
                      </span>
                    )}
                  </span>
                </div>
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

        {/* Barra di progresso segmentata bilanciata */}
        <div className="relative">
          <div className="flex h-6 bg-gray-200 rounded-lg overflow-hidden">
            {segmenti.length > 0 ? (
              segmenti.map((segmento, index) => {
                const config = STATI_CONFIG[segmento.stato as keyof typeof STATI_CONFIG];
                const isCurrentState = segmento.stato === sanitizedOdl.status;
                const hasSignificantDifference = Math.abs(segmento.percentuale - segmento.percentualeOriginale) > 5;
                
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div
                        className={`
                          ${config?.color || 'bg-gray-400'} 
                          transition-all duration-300 hover:opacity-80
                          ${isCurrentState ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
                          ${segmento.isEstimated ? 'opacity-75 border-2 border-dashed border-white' : ''}
                          ${hasSignificantDifference ? 'border-l-2 border-r-2 border-yellow-400' : ''}
                        `}
                        style={{ width: `${segmento.percentuale}%` }}
                      />
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-center">
                        <div className="font-medium">
                          {config?.icon} {segmento.stato}
                          {segmento.isEstimated && <span className="text-blue-400 ml-1">(stimato)</span>}
                          {isCurrentState && <span className="text-green-400 ml-1">• ATTIVO</span>}
                          {segmento.fonte_dati === 'tempo_fase' && (
                            <span className="text-green-500 ml-1">⚡ Preciso</span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <div>Durata: {formatDurata(segmento.durata_minuti || 0)}</div>
                          <div>Visualizzazione: {segmento.percentuale.toFixed(1)}%</div>
                          {segmento.fonte_dati && (
                            <div className={`mt-1 ${
                              segmento.fonte_dati === 'tempo_fase' 
                                ? 'text-green-600' 
                                : 'text-gray-600'
                            }`}>
                              Fonte: {segmento.fonte_dati === 'tempo_fase' ? 'Tracciamento Preciso' : 'Log Stati'}
                            </div>
                          )}
                          {hasSignificantDifference && (
                            <div className="text-yellow-600">
                              Reale: {segmento.percentualeOriginale.toFixed(1)}% 
                              <br />
                              <span className="text-xs">(bilanciato per leggibilità)</span>
                            </div>
                          )}
                        </div>
                        {segmento.inizio && !segmento.isEstimated && (
                          <div className="text-xs text-muted-foreground mt-1">
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
                        {config && (
                          <div className="text-xs text-gray-500 mt-1">
                            Media tipica: {formatDurata(config.durata_media)}
                            {segmento.fonte_dati === 'tempo_fase' && segmento.durata_minuti && (
                              <div className={`mt-1 ${
                                Math.abs((segmento.durata_minuti - config.durata_media) / config.durata_media) > 0.2
                                  ? (segmento.durata_minuti > config.durata_media ? 'text-red-500' : 'text-green-500')
                                  : 'text-gray-500'
                              }`}>
                                {segmento.durata_minuti > config.durata_media ? '↗' : '↘'} 
                                {Math.abs(((segmento.durata_minuti - config.durata_media) / config.durata_media) * 100).toFixed(0)}% vs media
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })
            ) : (
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

        {/* Legenda dettagliata con statistiche */}
        {showDetails && segmenti.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
            {Object.entries(STATI_CONFIG).map(([stato, config]) => {
              const segmento = segmenti.find(s => s.stato === stato);
              const isActive = segmento !== undefined;
              const isCurrent = stato === sanitizedOdl.status;
              const durataEffettiva = segmento?.durata_minuti || 0;
              const durataMedia = config.durata_media;
              const scostamentoStato = durataEffettiva - durataMedia;
              const hasScostamento = Math.abs(scostamentoStato) > durataMedia * 0.2; // >20% scostamento
              
              return (
                <div 
                  key={stato}
                  className={`
                    flex flex-col p-2 rounded border
                    ${isActive ? 'bg-gray-50 border-gray-200' : 'opacity-50 border-gray-100'}
                    ${isCurrent ? 'ring-2 ring-blue-300 bg-blue-50' : ''}
                  `}
                >
                  <div className="flex items-center gap-1 mb-1">
                    <div 
                      className={`w-3 h-3 rounded-sm ${config.color} ${segmento?.isEstimated ? 'opacity-75 border border-dashed border-gray-400' : ''}`}
                    />
                    <span className={`text-xs ${isActive ? 'font-medium' : ''}`}>
                      {config.icon} {stato}
                    </span>
                  </div>
                  
                  {segmento && (
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-xs text-muted-foreground">Durata:</span>
                        <span className="text-xs font-medium">
                          {formatDurata(durataEffettiva)}
                          {segmento.isEstimated && <span className="text-blue-400">*</span>}
                        </span>
                      </div>
                      
                      {!segmento.isEstimated && hasScostamento && (
                        <div className={`text-xs ${scostamentoStato > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {scostamentoStato > 0 ? '+' : ''}{formatDurata(Math.abs(scostamentoStato))} vs media
                        </div>
                      )}
                      
                      <div className="text-xs text-gray-400">
                        Media: {formatDurata(durataMedia)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Note informative */}
        {usingEstimatedData && (
          <div className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 p-2 rounded">
            <Info className="h-4 w-4" />
            <span>
              Dati temporali stimati - La timeline dettagliata sarà disponibile dopo il primo cambio di stato
              {durataTotale > 0 && ` (tempo dall'inizio: ${formatDurata(durataTotale)})`}
            </span>
          </div>
        )}

        {segmenti.some(s => Math.abs(s.percentuale - s.percentualeOriginale) > 5) && (
          <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
            <Info className="h-4 w-4" />
            <span>
              Le proporzioni sono state bilanciate per migliorare la leggibilità. 
              I valori reali sono mostrati nei tooltip dei segmenti.
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