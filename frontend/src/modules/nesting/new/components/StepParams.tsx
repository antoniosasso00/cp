'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Label } from '@/shared/components/ui/label';
import { Input } from '@/shared/components/ui/input';
import { Badge } from '@/shared/components/ui/badge';
import { CheckCircle2, Settings, Plane } from 'lucide-react';
import { NestingParams } from '../../schema';

interface StepParamsProps {
  parameters: NestingParams;
  onParametersChange: (params: NestingParams) => void;
  isCompleted: boolean;
}

export const StepParams: React.FC<StepParamsProps> = ({ 
  parameters, 
  onParametersChange, 
  isCompleted 
}) => {
  const updateParameter = (key: keyof NestingParams, value: number) => {
    onParametersChange({ ...parameters, [key]: value });
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametri Nesting
            {isCompleted && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
          </div>
          <Badge variant="outline" className="bg-orange-50 text-orange-700">
            <Plane className="h-3 w-3 mr-1" />
            Aerospace
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Parametri Base */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="padding_mm" className="text-sm font-medium">
              Padding (mm)
            </Label>
            <Input
              id="padding_mm"
              type="number"
              min="0.1"
              max="5.0"
              step="0.1"
              value={parameters.padding_mm}
              onChange={(e) => updateParameter('padding_mm', parseFloat(e.target.value) || 0.5)}
              className="text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Distanza minima dai bordi
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="min_distance_mm" className="text-sm font-medium">
              Distanza Minima (mm)
            </Label>
            <Input
              id="min_distance_mm"
              type="number"
              min="0.1"
              max="5.0"
              step="0.1"
              value={parameters.min_distance_mm}
              onChange={(e) => updateParameter('min_distance_mm', parseFloat(e.target.value) || 0.5)}
              className="text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Distanza tra tool
            </p>
          </div>
        </div>

        {/* Riepilogo Configurazione */}
        <div className="mt-6 p-3 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Plane className="h-4 w-4" />
            Configurazione Aerospace
          </h4>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <div className="text-muted-foreground">Algoritmo</div>
              <div className="font-medium">OR-Tools CP-SAT</div>
            </div>
            <div>
              <div className="text-muted-foreground">Multithread</div>
              <div className="font-medium">8 workers</div>
            </div>
            <div>
              <div className="text-muted-foreground">Target Efficienza</div>
              <div className="font-medium">85-90%</div>
            </div>
            <div>
              <div className="text-muted-foreground">Timeout</div>
              <div className="font-medium">Dinamico</div>
            </div>
          </div>
        </div>

        {/* Note */}
        <div className="text-xs text-muted-foreground bg-blue-50 p-3 rounded-lg">
          <strong>Nota:</strong> I parametri aerospace sono ottimizzati per massimizzare l'efficienza 
          di posizionamento usando algoritmi di livello industriale aerospaziale.
        </div>
      </CardContent>
    </Card>
  );
}; 