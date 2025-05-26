'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Clock, AlertTriangle } from 'lucide-react';

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
  
  // Calcola la durata totale effettiva
  const calcolaDurataTotale = (): number => {
    return odl.timestamps.reduce((total, timestamp) => {
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

  // Calcola la percentuale di ogni segmento
  const calcolaPercentuali = () => {
    const durataTotale = calcolaDurataTotale();
    if (durataTotale === 0) return [];

    return odl.timestamps.map(timestamp => ({
      ...timestamp,
      percentuale: ((timestamp.durata_minuti || 0) / durataTotale) * 100
    }));
  };

  // Determina se un ODL è in ritardo (più di 24h nello stato corrente)
  const isInRitardo = (): boolean => {
    const now = new Date();
    const lastUpdate = new Date(odl.updated_at);
    const diffHours = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60);
    return diffHours > 24 && odl.status !== 'Finito';
  };

  // Ottieni il timestamp corrente
  const getCurrentTimestamp = () => {
    return odl.timestamps.find(t => t.stato === odl.status);
  };

  const segmenti = calcolaPercentuali();
  const durataTotale = calcolaDurataTotale();
  const currentTimestamp = getCurrentTimestamp();
  const inRitardo = isInRitardo();

  return (
    <TooltipProvider>
      <div className={`space-y-3 ${className}`}>
        {/* Header con informazioni generali */}
        {showDetails && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                ODL #{odl.id}
              </Badge>
              <Badge 
                variant={odl.status === 'Finito' ? 'default' : 'secondary'}
                className={`text-xs ${STATI_CONFIG[odl.status as keyof typeof STATI_CONFIG]?.textColor || ''}`}
              >
                {STATI_CONFIG[odl.status as keyof typeof STATI_CONFIG]?.icon} {odl.status}
              </Badge>
              {inRitardo && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  In Ritardo
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>Totale: {formatDurata(durataTotale)}</span>
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
                const isCurrentState = segmento.stato === odl.status;
                
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      <div
                        className={`
                          ${config?.color || 'bg-gray-400'} 
                          transition-all duration-300 hover:opacity-80
                          ${isCurrentState ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
                          ${segmento.percentuale < 5 ? 'min-w-[4px]' : ''}
                        `}
                        style={{ width: `${Math.max(segmento.percentuale, 2)}%` }}
                      />
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-center">
                        <div className="font-medium">
                          {config?.icon} {segmento.stato}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Durata: {formatDurata(segmento.durata_minuti || 0)}
                        </div>
                        {segmento.inizio && (
                          <div className="text-xs text-muted-foreground">
                            Inizio: {new Date(segmento.inizio).toLocaleDateString('it-IT', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        )}
                        {segmento.fine && (
                          <div className="text-xs text-muted-foreground">
                            Fine: {new Date(segmento.fine).toLocaleDateString('it-IT', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        )}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })
            ) : (
              // Barra vuota se non ci sono dati
              <div className="w-full bg-gray-300 flex items-center justify-center">
                <span className="text-xs text-gray-600">Dati temporali non disponibili</span>
              </div>
            )}
          </div>

          {/* Indicatore stato corrente */}
          {currentTimestamp && !currentTimestamp.fine && (
            <div className="absolute -top-1 -bottom-1 right-0 w-1 bg-blue-600 rounded-full animate-pulse" />
          )}
        </div>

        {/* Legenda dettagliata (opzionale) */}
        {showDetails && segmenti.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
            {Object.entries(STATI_CONFIG).map(([stato, config]) => {
              const segmento = segmenti.find(s => s.stato === stato);
              const isActive = segmento !== undefined;
              const isCurrent = stato === odl.status;
              
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
                    className={`w-3 h-3 rounded-sm ${config.color}`}
                  />
                  <span className={`text-xs ${isActive ? 'font-medium' : ''}`}>
                    {config.icon} {stato}
                  </span>
                  {segmento && (
                    <span className="text-xs text-muted-foreground ml-auto">
                      {formatDurata(segmento.durata_minuti || 0)}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Informazioni aggiuntive per dati incompleti */}
        {durataTotale === 0 && (
          <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
            <AlertTriangle className="h-4 w-4" />
            <span>Dati temporali incompleti - Alcuni timestamp potrebbero mancare</span>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
} 