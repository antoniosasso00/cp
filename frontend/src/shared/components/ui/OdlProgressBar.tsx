'use client';

import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Info, Clock, TrendingUp, TrendingDown } from 'lucide-react';

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

// Configurazione colori e ordine degli stati con palette moderna e intuitiva
const STATI_CONFIG = {
  'Preparazione': { 
    color: 'bg-slate-500', // Più professionale del grigio 
    gradientFrom: 'from-slate-400',
    gradientTo: 'to-slate-600',
    textColor: 'text-slate-700',
    lightBg: 'bg-slate-50',
    borderColor: 'border-slate-200',
    order: 1,
    icon: '📋',
    durata_media: 30,
    description: 'Setup e preparazione materiali'
  },
  'Laminazione': { 
    color: 'bg-blue-500', 
    gradientFrom: 'from-blue-400',
    gradientTo: 'to-blue-600',
    textColor: 'text-blue-700',
    lightBg: 'bg-blue-50',
    borderColor: 'border-blue-200',
    order: 2,
    icon: '🔧',
    durata_media: 120,
    description: 'Processo di laminazione'
  },
  'In Coda': { 
    color: 'bg-amber-500', // Più elegante dell'arancione
    gradientFrom: 'from-amber-400',
    gradientTo: 'to-amber-600',
    textColor: 'text-amber-700',
    lightBg: 'bg-amber-50',
    borderColor: 'border-amber-200',
    order: 2.5,
    icon: '⏳',
    durata_media: 60,
    description: 'In attesa di tool disponibili'
  },
  'Attesa Cura': { 
    color: 'bg-yellow-500', 
    gradientFrom: 'from-yellow-400',
    gradientTo: 'to-yellow-600',
    textColor: 'text-yellow-700',
    lightBg: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    order: 3,
    icon: '⏱️',
    durata_media: 240,
    description: 'In attesa di autoclave'
  },
  'Cura': { 
    color: 'bg-red-500', 
    gradientFrom: 'from-red-400',
    gradientTo: 'to-red-600',
    textColor: 'text-red-700',
    lightBg: 'bg-red-50',
    borderColor: 'border-red-200',
    order: 4,
    icon: '🔥',
    durata_media: 360,
    description: 'Processo di cura in autoclave'
  },
  'Finito': { 
    color: 'bg-emerald-500', // Verde più moderno
    gradientFrom: 'from-emerald-400',
    gradientTo: 'to-emerald-600',
    textColor: 'text-emerald-700',
    lightBg: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    order: 5,
    icon: '✅',
    durata_media: 0,
    description: 'Processo completato'
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

        {/* Barra di progresso compatta per tabelle */}
        <div className="relative">
          {/* Progress Bar Compatta */}
          <div className="flex h-4 bg-gray-100 rounded-md overflow-hidden">
            {segmenti.length > 0 ? (
              segmenti.map((segmento, index) => {
                const config = STATI_CONFIG[segmento.stato as keyof typeof STATI_CONFIG];
                const isCurrentState = segmento.stato === sanitizedOdl.status;
                const isLastSegment = index === segmenti.length - 1;
                
                // Calcola scostamento dalla media standard
                const durataEffettiva = segmento.durata_minuti || 0;
                const durataStandard = config?.durata_media || 0;
                const scostamentoPerc = durataStandard > 0 ? ((durataEffettiva - durataStandard) / durataStandard) * 100 : 0;
                const isRitardo = scostamentoPerc > 20;
                const isVeloce = scostamentoPerc < -20;
                
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div
                        className={`
                          relative transition-all duration-300 hover:brightness-105 cursor-pointer
                          ${isCurrentState 
                            ? `bg-gradient-to-r ${config?.gradientFrom} ${config?.gradientTo}` 
                            : config?.color || 'bg-gray-400'
                          }
                          ${segmento.isEstimated ? 'opacity-60' : ''}
                          ${!isLastSegment ? 'border-r border-white/20' : ''}
                        `}
                        style={{ width: `${segmento.percentuale}%` }}
                      >
                        {/* Indicatore stato attivo minimalista */}
                        {isCurrentState && (
                          <div className="absolute inset-y-0 right-0 w-0.5 bg-white/90" />
                        )}
                        
                        {/* Indicatore performance */}
                        {segmento.fonte_dati === 'tempo_fase' && (isRitardo || isVeloce) && (
                          <div className={`absolute top-0 right-0 w-1 h-1 rounded-full ${isRitardo ? 'bg-red-400' : 'bg-green-400'}`} />
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-sm">
                        <div className="font-medium mb-1">
                          {config?.icon} {segmento.stato}
                          {isCurrentState && <span className="text-blue-400 ml-1">• ATTIVO</span>}
                        </div>
                        
                        <div className="text-xs space-y-1">
                          <div>Durata: <span className="font-medium">{formatDurata(durataEffettiva)}</span></div>
                          
                          {durataStandard > 0 && (
                            <div>
                              Standard: {formatDurata(durataStandard)}
                              {segmento.fonte_dati === 'tempo_fase' && Math.abs(scostamentoPerc) > 20 && (
                                <span className={`ml-1 ${isRitardo ? 'text-red-500' : 'text-green-500'}`}>
                                  ({isRitardo ? '↗' : '↘'}{Math.abs(scostamentoPerc).toFixed(0)}%)
                                </span>
                              )}
                            </div>
                          )}
                          
                          {segmento.fonte_dati === 'tempo_fase' && (
                            <div className="text-green-600">⚡ Preciso</div>
                          )}
                          
                          {segmento.isEstimated && (
                            <div className="text-blue-500">📈 Stimato</div>
                          )}
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })
            ) : (
              <div className="w-full bg-gray-300 flex items-center justify-center">
                <span className="text-xs text-gray-500">Nessun dato</span>
              </div>
            )}
          </div>
        </div>


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