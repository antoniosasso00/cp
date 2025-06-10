'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { CheckCircle2, Play, Loader2, Calculator, Package, Factory, Settings, Timer } from 'lucide-react';
import { NestingParams } from '../../schema';

interface AutoclaveData {
  id: number;
  nome: string;
  codice: string;
}

interface ODLData {
  id: number;
  parte: {
    part_number: string;
  };
}

interface StepReviewProps {
  selectedOdl: string[];
  selectedAutoclavi: string[];
  parameters: NestingParams;
  odlList: ODLData[];
  autoclaveList: AutoclaveData[];
  isCompleted: boolean;
  generating: boolean;
  onGenerate: () => void;
}

export const StepReview: React.FC<StepReviewProps> = ({ 
  selectedOdl,
  selectedAutoclavi,
  parameters,
  odlList,
  autoclaveList,
  isCompleted,
  generating,
  onGenerate
}) => {
  // Calcola tempo stimato
  const estimateCalculationTime = (): number => {
    const baseTime = 15;
    const odlFactor = selectedOdl.length * 2;
    const autoclaveFactor = selectedAutoclavi.length * 3;
    return Math.max(baseTime + odlFactor + autoclaveFactor, 10);
  };

  const estimatedTime = estimateCalculationTime();
  const isMultiAutoclave = selectedAutoclavi.length > 1;

  // Recupera dati dettagliati
  const selectedOdlData = odlList.filter(odl => selectedOdl.includes(odl.id.toString()));
  const selectedAutoclaveData = autoclaveList.filter(autoclave => 
    selectedAutoclavi.includes(autoclave.id.toString())
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            Riepilogo & Generazione
            {isCompleted && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
          </div>
          <Badge variant={isMultiAutoclave ? "default" : "secondary"} className="text-xs">
            {isMultiAutoclave ? 'Multi-Batch' : 'Single-Batch'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Statistiche Principali */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{selectedOdl.length}</div>
            <div className="text-xs text-muted-foreground">ODL Selezionati</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{selectedAutoclavi.length}</div>
            <div className="text-xs text-muted-foreground">
              Autoclave{selectedAutoclavi.length !== 1 ? 'i' : ''}
            </div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{parameters.padding_mm}</div>
            <div className="text-xs text-muted-foreground">Padding (mm)</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">~{estimatedTime}s</div>
            <div className="text-xs text-muted-foreground">Tempo Stimato</div>
          </div>
        </div>

        {/* Dettagli Selezione */}
        <div className="space-y-4">
          {/* ODL Selezionati */}
          <div>
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Package className="h-4 w-4" />
              ODL Selezionati ({selectedOdl.length})
            </h4>
            <div className="max-h-32 overflow-y-auto bg-slate-50 rounded-lg p-3">
              <div className="space-y-1">
                {selectedOdlData.map((odl) => (
                  <div key={odl.id} className="text-xs flex justify-between items-center">
                    <span className="font-mono">#{odl.id}</span>
                    <span className="text-muted-foreground truncate ml-2">
                      {odl.parte.part_number}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Autoclavi Selezionate */}
          <div>
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Factory className="h-4 w-4" />
              Autoclavi Selezionate ({selectedAutoclavi.length})
            </h4>
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="space-y-1">
                {selectedAutoclaveData.map((autoclave) => (
                  <div key={autoclave.id} className="text-xs flex justify-between items-center">
                    <span className="font-medium">{autoclave.nome}</span>
                    <span className="text-muted-foreground">{autoclave.codice}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Parametri */}
          <div>
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Parametri Nesting
            </h4>
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <div className="text-muted-foreground">Padding</div>
                  <div className="font-medium">{parameters.padding_mm}mm</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Distanza Minima</div>
                  <div className="font-medium">{parameters.min_distance_mm}mm</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Info Algoritmo */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="text-sm font-medium text-blue-800 mb-2">
            Algoritmo Aerospace Attivo
          </div>
          <div className="text-xs text-blue-700 space-y-1">
            <div>• OR-Tools CP-SAT con ottimizzazione multi-thread</div>
            <div>• Target efficienza: 85-90%</div>
            <div>• Timeout dinamico basato su complessità</div>
            <div>• {isMultiAutoclave ? 'Distribuzione multi-autoclave intelligente' : 'Ottimizzazione single-batch'}</div>
          </div>
        </div>

        {/* Pulsante Genera */}
        <Button
          onClick={onGenerate}
          disabled={generating || !isCompleted}
          className="w-full"
          size="lg"
        >
          {generating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              <Calculator className="mr-2 h-4 w-4" />
              Calcolo in corso...
              <Timer className="ml-2 h-4 w-4" />
              ~{estimatedTime}s
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Genera {isMultiAutoclave ? 'Multi-Batch' : 'Nesting'} Aerospace
            </>
          )}
        </Button>

        {!isCompleted && (
          <div className="text-center text-sm text-muted-foreground">
            Completa tutti gli step precedenti per abilitare la generazione
          </div>
        )}
      </CardContent>
    </Card>
  );
}; 