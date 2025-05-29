'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { Info, Eye, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface NestingParameters {
  distanza_minima_tool_cm: number;
  padding_bordo_autoclave_cm: number;
  margine_sicurezza_peso_percent: number;
  priorita_minima: number;
  efficienza_minima_percent: number;
}

interface BatchParametersFormProps {
  parameters: NestingParameters;
  onParametersChange: (parameters: NestingParameters) => void;
  onCreatePreview: () => void;
  isLoading: boolean;
}

export function BatchParametersForm({
  parameters,
  onParametersChange,
  onCreatePreview,
  isLoading
}: BatchParametersFormProps) {

  /**
   * Aggiorna un singolo parametro
   */
  const updateParameter = (key: keyof NestingParameters, value: number) => {
    onParametersChange({
      ...parameters,
      [key]: value
    });
  };

  /**
   * Reset ai valori di default
   */
  const resetToDefaults = () => {
    onParametersChange({
      distanza_minima_tool_cm: 2.0,
      padding_bordo_autoclave_cm: 1.5,
      margine_sicurezza_peso_percent: 10.0,
      priorita_minima: 1,
      efficienza_minima_percent: 60.0
    });
  };

  return (
    <div className="space-y-6">
      {/* Informazioni sui parametri */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Questi parametri influenzano l'algoritmo di ottimizzazione del nesting multiplo. 
          Valori più conservativi garantiscono maggiore sicurezza ma potrebbero ridurre l'efficienza.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Parametri Spaziali */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Parametri Spaziali</CardTitle>
            <CardDescription>
              Configurazione delle distanze e margini di sicurezza
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Distanza minima tra tool */}
            <div className="space-y-2">
              <Label htmlFor="distanza-tool">
                Distanza minima tra tool (cm)
              </Label>
              <div className="flex items-center space-x-4">
                <Slider
                  id="distanza-tool"
                  min={0.5}
                  max={10.0}
                  step={0.1}
                  value={parameters.distanza_minima_tool_cm}
                  onValueChange={(value: number) => updateParameter('distanza_minima_tool_cm', value)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={0.5}
                  max={10.0}
                  step={0.1}
                  value={parameters.distanza_minima_tool_cm}
                  onChange={(e) => updateParameter('distanza_minima_tool_cm', parseFloat(e.target.value) || 0.5)}
                  className="w-20"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Spazio minimo tra i tool per evitare interferenze durante la cura
              </p>
            </div>

            <Separator />

            {/* Padding bordo autoclave */}
            <div className="space-y-2">
              <Label htmlFor="padding-bordo">
                Padding bordo autoclave (cm)
              </Label>
              <div className="flex items-center space-x-4">
                <Slider
                  id="padding-bordo"
                  min={0.5}
                  max={5.0}
                  step={0.1}
                  value={parameters.padding_bordo_autoclave_cm}
                  onValueChange={(value: number) => updateParameter('padding_bordo_autoclave_cm', value)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={0.5}
                  max={5.0}
                  step={0.1}
                  value={parameters.padding_bordo_autoclave_cm}
                  onChange={(e) => updateParameter('padding_bordo_autoclave_cm', parseFloat(e.target.value) || 0.5)}
                  className="w-20"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Margine di sicurezza dai bordi dell'autoclave
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Parametri di Ottimizzazione */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Parametri di Ottimizzazione</CardTitle>
            <CardDescription>
              Configurazione dei criteri di selezione e efficienza
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Margine sicurezza peso */}
            <div className="space-y-2">
              <Label htmlFor="margine-peso">
                Margine sicurezza peso (%)
              </Label>
              <div className="flex items-center space-x-4">
                <Slider
                  id="margine-peso"
                  min={0}
                  max={50}
                  step={1}
                  value={parameters.margine_sicurezza_peso_percent}
                  onValueChange={(value: number) => updateParameter('margine_sicurezza_peso_percent', value)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={0}
                  max={50}
                  step={1}
                  value={parameters.margine_sicurezza_peso_percent}
                  onChange={(e) => updateParameter('margine_sicurezza_peso_percent', parseInt(e.target.value) || 0)}
                  className="w-20"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Percentuale di margine sulla capacità massima di peso dell'autoclave
              </p>
            </div>

            <Separator />

            {/* Priorità minima */}
            <div className="space-y-2">
              <Label htmlFor="priorita-minima">
                Priorità minima ODL
              </Label>
              <div className="flex items-center space-x-4">
                <Slider
                  id="priorita-minima"
                  min={1}
                  max={10}
                  step={1}
                  value={parameters.priorita_minima}
                  onValueChange={(value: number) => updateParameter('priorita_minima', value)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={1}
                  max={10}
                  step={1}
                  value={parameters.priorita_minima}
                  onChange={(e) => updateParameter('priorita_minima', parseInt(e.target.value) || 1)}
                  className="w-20"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Solo gli ODL con priorità maggiore o uguale verranno considerati
              </p>
            </div>

            <Separator />

            {/* Efficienza minima */}
            <div className="space-y-2">
              <Label htmlFor="efficienza-minima">
                Efficienza minima richiesta (%)
              </Label>
              <div className="flex items-center space-x-4">
                <Slider
                  id="efficienza-minima"
                  min={30}
                  max={95}
                  step={1}
                  value={parameters.efficienza_minima_percent}
                  onValueChange={(value: number) => updateParameter('efficienza_minima_percent', value)}
                  className="flex-1"
                />
                <Input
                  type="number"
                  min={30}
                  max={95}
                  step={1}
                  value={parameters.efficienza_minima_percent}
                  onChange={(e) => updateParameter('efficienza_minima_percent', parseInt(e.target.value) || 30)}
                  className="w-20"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Efficienza minima di utilizzo dell'autoclave per accettare l'assegnazione
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Riepilogo parametri */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Riepilogo Configurazione</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div className="text-center">
              <div className="font-semibold text-lg text-blue-600">
                {parameters.distanza_minima_tool_cm} cm
              </div>
              <div className="text-muted-foreground">Distanza tool</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-lg text-green-600">
                {parameters.padding_bordo_autoclave_cm} cm
              </div>
              <div className="text-muted-foreground">Padding bordo</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-lg text-orange-600">
                {parameters.margine_sicurezza_peso_percent}%
              </div>
              <div className="text-muted-foreground">Margine peso</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-lg text-purple-600">
                {parameters.priorita_minima}
              </div>
              <div className="text-muted-foreground">Priorità min</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-lg text-red-600">
                {parameters.efficienza_minima_percent}%
              </div>
              <div className="text-muted-foreground">Efficienza min</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Azioni */}
      <div className="flex justify-between items-center">
        <Button
          onClick={resetToDefaults}
          variant="outline"
          disabled={isLoading}
        >
          Reset Default
        </Button>
        
        <Button
          onClick={onCreatePreview}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
          Crea Preview Batch
        </Button>
      </div>
    </div>
  );
} 