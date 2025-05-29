'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Settings, RotateCcw, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

/**
 * Interfaccia per i parametri di nesting
 */
export interface NestingParameters {
  distanza_minima_tool_cm: number;
  padding_bordo_autoclave_cm: number;
  margine_sicurezza_peso_percent: number;
  priorita_minima: number;
  efficienza_minima_percent: number;
}

/**
 * Props per il componente NestingParametersPanel
 */
interface NestingParametersPanelProps {
  /** Parametri attuali */
  parameters: NestingParameters;
  /** Callback chiamata quando i parametri cambiano */
  onParametersChange: (parameters: NestingParameters) => void;
  /** Callback chiamata quando si applica una preview */
  onPreview?: (parameters: NestingParameters) => void;
  /** Indica se il pannello è in modalità loading */
  isLoading?: boolean;
  /** Indica se il pannello è collassato inizialmente */
  defaultCollapsed?: boolean;
}

/**
 * Parametri di default per il nesting
 */
const DEFAULT_PARAMETERS: NestingParameters = {
  distanza_minima_tool_cm: 2.0,
  padding_bordo_autoclave_cm: 1.5,
  margine_sicurezza_peso_percent: 10.0,
  priorita_minima: 1,
  efficienza_minima_percent: 60.0,
};

/**
 * Componente per gestire i parametri regolabili dell'algoritmo di nesting.
 * 
 * Questo componente fornisce un'interfaccia utente per modificare:
 * - Distanza minima tra tool
 * - Padding dal bordo dell'autoclave
 * - Margine di sicurezza per il peso
 * - Priorità minima degli ODL
 * - Efficienza minima richiesta
 */
export const NestingParametersPanel: React.FC<NestingParametersPanelProps> = ({
  parameters,
  onParametersChange,
  onPreview,
  isLoading = false,
  defaultCollapsed = false,
}) => {
  const [localParameters, setLocalParameters] = useState<NestingParameters>(parameters);
  const [hasChanges, setHasChanges] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Aggiorna i parametri locali quando cambiano quelli esterni
  useEffect(() => {
    setLocalParameters(parameters);
    setHasChanges(false);
  }, [parameters]);

  /**
   * Valida un singolo parametro
   */
  const validateParameter = (key: keyof NestingParameters, value: number): string | null => {
    switch (key) {
      case 'distanza_minima_tool_cm':
        if (value < 0.1 || value > 10.0) {
          return 'La distanza deve essere tra 0.1 e 10.0 cm';
        }
        break;
      case 'padding_bordo_autoclave_cm':
        if (value < 0.1 || value > 5.0) {
          return 'Il padding deve essere tra 0.1 e 5.0 cm';
        }
        break;
      case 'margine_sicurezza_peso_percent':
        if (value < 0.0 || value > 50.0) {
          return 'Il margine deve essere tra 0% e 50%';
        }
        break;
      case 'priorita_minima':
        if (value < 1 || value > 10) {
          return 'La priorità deve essere tra 1 e 10';
        }
        break;
      case 'efficienza_minima_percent':
        if (value < 30.0 || value > 95.0) {
          return 'L\'efficienza deve essere tra 30% e 95%';
        }
        break;
    }
    return null;
  };

  /**
   * Gestisce il cambiamento di un parametro
   */
  const handleParameterChange = (key: keyof NestingParameters, value: string) => {
    const numValue = parseFloat(value);
    
    if (isNaN(numValue)) {
      return;
    }

    // Valida il parametro
    const error = validateParameter(key, numValue);
    setValidationErrors(prev => ({
      ...prev,
      [key]: error || ''
    }));

    // Aggiorna i parametri locali
    const newParameters = {
      ...localParameters,
      [key]: numValue,
    };
    
    setLocalParameters(newParameters);
    setHasChanges(true);
  };

  /**
   * Applica i parametri modificati
   */
  const handleApplyParameters = () => {
    // Verifica che non ci siano errori di validazione
    const hasErrors = Object.values(validationErrors).some(error => error !== '');
    if (hasErrors) {
      toast({
        title: "Errore di validazione",
        description: "Correggi gli errori di validazione prima di applicare i parametri",
        variant: "destructive"
      });
      return;
    }

    onParametersChange(localParameters);
    setHasChanges(false);
    toast({
      title: "Parametri applicati",
      description: "I parametri sono stati applicati con successo"
    });
  };

  /**
   * Ripristina i parametri di default
   */
  const handleResetToDefaults = () => {
    setLocalParameters(DEFAULT_PARAMETERS);
    setValidationErrors({});
    setHasChanges(true);
    toast({
      title: "Parametri ripristinati",
      description: "I parametri sono stati ripristinati ai valori di default"
    });
  };

  /**
   * Genera una preview con i parametri attuali
   */
  const handlePreview = () => {
    if (onPreview) {
      onPreview(localParameters);
    }
  };

  return (
    <Card className="w-full">
      <Accordion type="single" collapsible>
        <AccordionItem value="item-1">
          <AccordionTrigger className="cursor-pointer hover:bg-muted/50 transition-colors px-6 py-0">
            <div className="flex flex-col space-y-2 w-full">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center space-x-2">
                  <Settings className="h-5 w-5 text-primary" />
                  <span className="text-lg font-semibold">Parametri Nesting</span>
                  {hasChanges && (
                    <Badge variant="secondary" className="text-xs">
                      Modifiche non salvate
                    </Badge>
                  )}
                </div>
              </div>
              <p className="text-sm text-muted-foreground text-left">
                Configura i parametri dell'algoritmo di ottimizzazione
              </p>
            </div>
          </AccordionTrigger>

          <AccordionContent>
            <CardContent className="space-y-6">
              {/* Distanza minima tra tool */}
              <div className="space-y-2">
                <Label htmlFor="distanza-tool" className="text-sm font-medium">
                  Distanza minima tra tool (cm)
                </Label>
                <Input
                  id="distanza-tool"
                  type="number"
                  min="0.1"
                  max="10.0"
                  step="0.1"
                  value={localParameters.distanza_minima_tool_cm}
                  onChange={(e) => handleParameterChange('distanza_minima_tool_cm', e.target.value)}
                  className={validationErrors.distanza_minima_tool_cm ? 'border-destructive' : ''}
                  disabled={isLoading}
                />
                {validationErrors.distanza_minima_tool_cm && (
                  <div className="flex items-center space-x-1 text-destructive text-xs">
                    <AlertCircle className="h-3 w-3" />
                    <span>{validationErrors.distanza_minima_tool_cm}</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Spazio minimo da mantenere tra i tool durante il posizionamento
                </p>
              </div>

              <Separator />

              {/* Padding bordo autoclave */}
              <div className="space-y-2">
                <Label htmlFor="padding-bordo" className="text-sm font-medium">
                  Padding bordo autoclave (cm)
                </Label>
                <Input
                  id="padding-bordo"
                  type="number"
                  min="0.1"
                  max="5.0"
                  step="0.1"
                  value={localParameters.padding_bordo_autoclave_cm}
                  onChange={(e) => handleParameterChange('padding_bordo_autoclave_cm', e.target.value)}
                  className={validationErrors.padding_bordo_autoclave_cm ? 'border-destructive' : ''}
                  disabled={isLoading}
                />
                {validationErrors.padding_bordo_autoclave_cm && (
                  <div className="flex items-center space-x-1 text-destructive text-xs">
                    <AlertCircle className="h-3 w-3" />
                    <span>{validationErrors.padding_bordo_autoclave_cm}</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Margine di sicurezza dal bordo dell'autoclave
                </p>
              </div>

              <Separator />

              {/* Margine sicurezza peso */}
              <div className="space-y-2">
                <Label htmlFor="margine-peso" className="text-sm font-medium">
                  Margine sicurezza peso (%)
                </Label>
                <Input
                  id="margine-peso"
                  type="number"
                  min="0"
                  max="50"
                  step="1"
                  value={localParameters.margine_sicurezza_peso_percent}
                  onChange={(e) => handleParameterChange('margine_sicurezza_peso_percent', e.target.value)}
                  className={validationErrors.margine_sicurezza_peso_percent ? 'border-destructive' : ''}
                  disabled={isLoading}
                />
                {validationErrors.margine_sicurezza_peso_percent && (
                  <div className="flex items-center space-x-1 text-destructive text-xs">
                    <AlertCircle className="h-3 w-3" />
                    <span>{validationErrors.margine_sicurezza_peso_percent}</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Percentuale di margine di sicurezza sul peso massimo dell'autoclave
                </p>
              </div>

              <Separator />

              {/* Priorità minima */}
              <div className="space-y-2">
                <Label htmlFor="priorita-minima" className="text-sm font-medium">
                  Priorità minima ODL
                </Label>
                <Input
                  id="priorita-minima"
                  type="number"
                  min="1"
                  max="10"
                  step="1"
                  value={localParameters.priorita_minima}
                  onChange={(e) => handleParameterChange('priorita_minima', e.target.value)}
                  className={validationErrors.priorita_minima ? 'border-destructive' : ''}
                  disabled={isLoading}
                />
                {validationErrors.priorita_minima && (
                  <div className="flex items-center space-x-1 text-destructive text-xs">
                    <AlertCircle className="h-3 w-3" />
                    <span>{validationErrors.priorita_minima}</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Solo gli ODL con priorità maggiore o uguale verranno considerati
                </p>
              </div>

              <Separator />

              {/* Efficienza minima */}
              <div className="space-y-2">
                <Label htmlFor="efficienza-minima" className="text-sm font-medium">
                  Efficienza minima richiesta (%)
                </Label>
                <Input
                  id="efficienza-minima"
                  type="number"
                  min="30"
                  max="95"
                  step="1"
                  value={localParameters.efficienza_minima_percent}
                  onChange={(e) => handleParameterChange('efficienza_minima_percent', e.target.value)}
                  className={validationErrors.efficienza_minima_percent ? 'border-destructive' : ''}
                  disabled={isLoading}
                />
                {validationErrors.efficienza_minima_percent && (
                  <div className="flex items-center space-x-1 text-destructive text-xs">
                    <AlertCircle className="h-3 w-3" />
                    <span>{validationErrors.efficienza_minima_percent}</span>
                  </div>
                )}
                <p className="text-xs text-muted-foreground">
                  Efficienza minima di utilizzo dell'autoclave per accettare il nesting
                </p>
              </div>

              <Separator />

              {/* Pulsanti di azione */}
              <div className="flex flex-col space-y-2">
                <div className="flex space-x-2">
                  <Button
                    onClick={handleApplyParameters}
                    disabled={!hasChanges || isLoading}
                    className="flex-1"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Applica Parametri
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={handleResetToDefaults}
                    disabled={isLoading}
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset
                  </Button>
                </div>

                {onPreview && (
                  <Button
                    variant="secondary"
                    onClick={handlePreview}
                    disabled={isLoading}
                    className="w-full"
                  >
                    Genera Preview
                  </Button>
                )}
              </div>

              {/* Indicatore stato */}
              {hasChanges && (
                <div className="flex items-center space-x-2 text-amber-600 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>Hai modifiche non salvate. Clicca "Applica Parametri" per salvarle.</span>
                </div>
              )}
            </CardContent>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );
}; 