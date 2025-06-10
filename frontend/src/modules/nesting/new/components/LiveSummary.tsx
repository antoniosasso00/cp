'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Badge } from '@/shared/components/ui/badge';
import { Separator } from '@/shared/components/ui/separator';
import { Progress } from '@/shared/components/ui/progress';
import { 
  Package, 
  Factory, 
  Settings, 
  Clock, 
  Target,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
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

interface LiveSummaryProps {
  selectedOdl: string[];
  selectedAutoclavi: string[];
  parameters: NestingParams;
  odlList: ODLData[];
  autoclaveList: AutoclaveData[];
  currentStepId: string;
}

export const LiveSummary: React.FC<LiveSummaryProps> = ({
  selectedOdl,
  selectedAutoclavi,
  parameters,
  odlList,
  autoclaveList,
  currentStepId
}) => {
  // Calcoli
  const isOdlComplete = selectedOdl.length > 0;
  const isAutoclaveComplete = selectedAutoclavi.length > 0;
  const isParamsComplete = parameters.padding_mm > 0 && parameters.min_distance_mm > 0;
  const isAllComplete = isOdlComplete && isAutoclaveComplete && isParamsComplete;
  const isMultiAutoclave = selectedAutoclavi.length > 1;

  // Tempo stimato
  const estimateTime = () => {
    const baseTime = 15;
    const odlFactor = selectedOdl.length * 2;
    const autoclaveFactor = selectedAutoclavi.length * 3;
    return Math.max(baseTime + odlFactor + autoclaveFactor, 10);
  };

  // Progress globale
  const completedSteps = [isOdlComplete, isAutoclaveComplete, isParamsComplete].filter(Boolean).length;
  const progressPercent = (completedSteps / 3) * 100;

  // Get selected data
  const selectedOdlData = odlList.filter(odl => selectedOdl.includes(odl.id.toString()));
  const selectedAutoclaveData = autoclaveList.filter(autoclave => 
    selectedAutoclavi.includes(autoclave.id.toString())
  );

  return (
    <Card className="sticky top-6">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Target className="h-5 w-5" />
          Riepilogo Live
        </CardTitle>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Completamento</span>
            <span className="font-medium">{completedSteps}/3</span>
          </div>
          <Progress value={progressPercent} className="h-2" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        
        {/* ODL Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Package className="h-4 w-4" />
              ODL Selezionati
            </div>
            {isOdlComplete ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-orange-500" />
            )}
          </div>
          
          <div className="text-center p-2 bg-blue-50 rounded">
            <div className="text-xl font-bold text-blue-600">{selectedOdl.length}</div>
            <div className="text-xs text-muted-foreground">ODL</div>
          </div>

          {selectedOdlData.length > 0 && (
            <div className="max-h-24 overflow-y-auto text-xs space-y-1">
              {selectedOdlData.slice(0, 3).map((odl) => (
                <div key={odl.id} className="flex justify-between items-center bg-slate-50 px-2 py-1 rounded">
                  <span className="font-mono">#{odl.id}</span>
                  <span className="truncate ml-2 text-muted-foreground">
                    {odl.parte.part_number}
                  </span>
                </div>
              ))}
              {selectedOdlData.length > 3 && (
                <div className="text-center text-muted-foreground">
                  +{selectedOdlData.length - 3} altri...
                </div>
              )}
            </div>
          )}
        </div>

        <Separator />

        {/* Autoclavi Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Factory className="h-4 w-4" />
              Autoclavi
            </div>
            {isAutoclaveComplete ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-orange-500" />
            )}
          </div>
          
          <div className="text-center p-2 bg-green-50 rounded">
            <div className="text-xl font-bold text-green-600">{selectedAutoclavi.length}</div>
            <div className="text-xs text-muted-foreground">
              Autoclave{selectedAutoclavi.length !== 1 ? 'i' : ''}
            </div>
          </div>

          {selectedAutoclaveData.length > 0 && (
            <div className="text-xs space-y-1">
              {selectedAutoclaveData.map((autoclave) => (
                <div key={autoclave.id} className="flex justify-between items-center bg-slate-50 px-2 py-1 rounded">
                  <span className="font-medium">{autoclave.nome}</span>
                  <span className="text-muted-foreground">{autoclave.codice}</span>
                </div>
              ))}
            </div>
          )}

          {isMultiAutoclave && (
            <Badge variant="default" className="w-full justify-center text-xs">
              Modalità Multi-Batch
            </Badge>
          )}
        </div>

        <Separator />

        {/* Parametri Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Settings className="h-4 w-4" />
              Parametri
            </div>
            {isParamsComplete ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-orange-500" />
            )}
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <div className="text-center p-2 bg-orange-50 rounded">
              <div className="text-lg font-bold text-orange-600">{parameters.padding_mm}</div>
              <div className="text-xs text-muted-foreground">Padding (mm)</div>
            </div>
            <div className="text-center p-2 bg-purple-50 rounded">
              <div className="text-lg font-bold text-purple-600">{parameters.min_distance_mm}</div>
              <div className="text-xs text-muted-foreground">Distanza (mm)</div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Tempo Stimato */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Clock className="h-4 w-4" />
            Tempo Stimato
          </div>
          
          <div className="text-center p-2 bg-slate-50 rounded">
            <div className="text-lg font-bold text-slate-600">~{estimateTime()}s</div>
            <div className="text-xs text-muted-foreground">Calcolo previsto</div>
          </div>
        </div>

        {/* Status */}
        {isAllComplete ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center gap-2 text-green-800 text-sm font-medium">
              <CheckCircle2 className="h-4 w-4" />
              Pronto per la generazione
            </div>
            <div className="text-xs text-green-700 mt-1">
              Tutti gli step sono completati
            </div>
          </div>
        ) : (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
            <div className="flex items-center gap-2 text-orange-800 text-sm font-medium">
              <AlertCircle className="h-4 w-4" />
              Configurazione incompleta
            </div>
            <div className="text-xs text-orange-700 mt-1">
              Completa tutti gli step per procedere
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}; 