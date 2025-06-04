'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Clock, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { ODLResponse, TempoFaseResponse } from '@/lib/api';

interface ODLTimingDisplayProps {
  odl: ODLResponse;
  tempoFasi: TempoFaseResponse[];
  showDetails?: boolean;
  className?: string;
}

// Configurazione colori per gli stati
const STATI_CONFIG = {
  'Preparazione': { color: 'bg-gray-400', icon: '📋', order: 1 },
  'Laminazione': { color: 'bg-blue-500', icon: '🔧', order: 2 },
  'In Coda': { color: 'bg-orange-400', icon: '⏳', order: 2.5 },
  'Attesa Cura': { color: 'bg-yellow-500', icon: '⏱️', order: 3 },
  'Cura': { color: 'bg-red-500', icon: '🔥', order: 4 },
  'Finito': { color: 'bg-green-500', icon: '✅', order: 5 }
};

// Tempi standard di riferimento (in minuti)
const TEMPI_STANDARD = {
  'laminazione': 120,    // 2 ore
  'attesa_cura': 60,     // 1 ora
  'cura': 300            // 5 ore
};

export function ODLTimingDisplay({ 
  odl, 
  tempoFasi, 
  showDetails = true, 
  className = '' 
}: ODLTimingDisplayProps) {

  // Formatta la durata in formato leggibile
  const formatDurata = (minuti: number): string => {
    if (minuti < 60) {
      return `${minuti}m`;
    }
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return min > 0 ? `${ore}h ${min}m` : `${ore}h`;
  };

  // Calcola la durata corrente per una fase in corso
  const calcolaDurataCorrente = (inizio: string): number => {
    const inizioDate = new Date(inizio);
    const now = new Date();
    return Math.floor((now.getTime() - inizioDate.getTime()) / (1000 * 60));
  };

  // Determina se una fase è in ritardo
  const isFaseInRitardo = (fase: TempoFaseResponse): boolean => {
    const durataCorrente = fase.durata_minuti || calcolaDurataCorrente(fase.inizio_fase);
    const tempoStandard = TEMPI_STANDARD[fase.fase as keyof typeof TEMPI_STANDARD] || 0;
    return tempoStandard > 0 && durataCorrente > tempoStandard * 1.5; // 50% oltre il tempo standard
  };

  // Calcola lo scostamento percentuale
  const calcolaScostamento = (durataReale: number, fase: string): number => {
    const tempoStandard = TEMPI_STANDARD[fase as keyof typeof TEMPI_STANDARD] || 0;
    if (tempoStandard === 0) return 0;
    return ((durataReale - tempoStandard) / tempoStandard) * 100;
  };

  // Calcola il progresso totale dell'ODL
  const calcolaProgressoTotale = (): number => {
    const statiOrdinati = Object.keys(STATI_CONFIG).sort((a, b) => 
      STATI_CONFIG[a as keyof typeof STATI_CONFIG].order - STATI_CONFIG[b as keyof typeof STATI_CONFIG].order
    );
    
    const statoCorrente = odl.status;
    const indiceCorrente = statiOrdinati.indexOf(statoCorrente);
    
    if (indiceCorrente === -1) return 0;
    return ((indiceCorrente + 1) / statiOrdinati.length) * 100;
  };

  // Calcola durata totale
  const calcolaDurataTotale = (): number => {
    return tempoFasi.reduce((total, fase) => {
      const durata = fase.durata_minuti || (fase.fine_fase ? 0 : calcolaDurataCorrente(fase.inizio_fase));
      return total + durata;
    }, 0);
  };

  const durataTotale = calcolaDurataTotale();
  const progressoTotale = calcolaProgressoTotale();
  const faseCorrente = tempoFasi.find(f => !f.fine_fase);

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Badge variant="outline">ODL #{odl.id}</Badge>
            <Badge variant={odl.status === 'Finito' ? 'default' : 'secondary'}>
              {STATI_CONFIG[odl.status as keyof typeof STATI_CONFIG]?.icon} {odl.status}
            </Badge>
          </CardTitle>
          
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Totale: {formatDurata(durataTotale)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Barra di progresso generale */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progresso ODL</span>
            <span>{progressoTotale.toFixed(0)}%</span>
          </div>
          <Progress value={progressoTotale} className="h-2" />
        </div>

        {/* Dettagli delle fasi */}
        {showDetails && tempoFasi.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Dettaglio Fasi</h4>
            
            {tempoFasi.map((fase, index) => {
              const durataReale = fase.durata_minuti || (fase.fine_fase ? 0 : calcolaDurataCorrente(fase.inizio_fase));
              const scostamento = calcolaScostamento(durataReale, fase.fase);
              const inRitardo = isFaseInRitardo(fase);
              const isCorrente = !fase.fine_fase;
              const tempoStandard = TEMPI_STANDARD[fase.fase as keyof typeof TEMPI_STANDARD] || 0;

              return (
                <div 
                  key={index} 
                  className={`p-3 rounded-lg border ${isCorrente ? 'border-blue-300 bg-blue-50' : 'border-gray-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">{fase.fase.replace('_', ' ')}</span>
                      {isCorrente && (
                        <Badge variant="outline" className="text-xs">
                          In corso
                        </Badge>
                      )}
                      {inRitardo && (
                        <Badge variant="destructive" className="text-xs">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          Ritardo
                        </Badge>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className="font-bold">{formatDurata(durataReale)}</div>
                      {tempoStandard > 0 && (
                        <div className={`text-xs flex items-center gap-1 ${
                          Math.abs(scostamento) > 20 ? 'text-red-600' : 
                          Math.abs(scostamento) > 10 ? 'text-orange-600' : 'text-green-600'
                        }`}>
                          {scostamento > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                          {scostamento > 0 ? '+' : ''}{scostamento.toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>
                      Inizio: {new Date(fase.inizio_fase).toLocaleDateString('it-IT', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                    {tempoStandard > 0 && (
                      <span>Standard: {formatDurata(tempoStandard)}</span>
                    )}
                  </div>
                  
                  {fase.fine_fase && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Fine: {new Date(fase.fine_fase).toLocaleDateString('it-IT', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Riepilogo se non ci sono fasi */}
        {tempoFasi.length === 0 && (
          <div className="text-center text-muted-foreground py-4">
            <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Nessun dato temporale disponibile</p>
            <p className="text-xs">I tempi verranno registrati durante l'avanzamento</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 