'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { NestingParametersPanel, NestingParameters } from './NestingParametersPanel';
import { useNestingParameters } from '@/hooks/useNestingParameters';
import { toast } from '@/components/ui/use-toast';
import { 
  Play, 
  Eye, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  Settings2,
  BarChart3
} from 'lucide-react';

/**
 * Componente principale che integra i parametri di nesting con la funzionalità di generazione automatica.
 * 
 * Questo componente fornisce:
 * - Pannello per configurare i parametri dell'algoritmo
 * - Preview del nesting con i parametri attuali
 * - Generazione automatica del nesting
 * - Visualizzazione dei risultati
 */
export const NestingWithParameters: React.FC = () => {
  const {
    parameters,
    isLoading,
    error,
    loadDefaultParameters,
    generatePreviewWithParameters,
    generateAutomaticNesting,
    updateParameters,
  } = useNestingParameters();

  const [previewData, setPreviewData] = useState<any>(null);
  const [nestingResults, setNestingResults] = useState<any>(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [isGeneratingNesting, setIsGeneratingNesting] = useState(false);

  // Carica i parametri di default all'avvio
  useEffect(() => {
    loadDefaultParameters();
  }, [loadDefaultParameters]);

  /**
   * Gestisce il cambiamento dei parametri
   */
  const handleParametersChange = (newParameters: NestingParameters) => {
    updateParameters(newParameters);
    // Reset della preview quando cambiano i parametri
    setPreviewData(null);
  };

  /**
   * Genera una preview con i parametri attuali
   */
  const handleGeneratePreview = async (params: NestingParameters) => {
    setIsGeneratingPreview(true);
    
    try {
      const result = await generatePreviewWithParameters(params);
      
      if (result) {
        setPreviewData(result);
        toast({
          title: "Preview generata",
          description: `Trovati ${result.total_odl_pending} ODL in ${result.odl_groups.length} gruppi`
        });
      }
    } catch (err) {
      toast({
        title: "Errore Preview",
        description: "Impossibile generare la preview con i parametri selezionati",
        variant: "destructive",
      })
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  /**
   * Genera il nesting automatico
   */
  const handleGenerateNesting = async (forceRegenerate: boolean = false) => {
    setIsGeneratingNesting(true);
    
    try {
      const result = await generateAutomaticNesting(parameters, forceRegenerate);
      
      if (result) {
        setNestingResults(result);
        toast({
          title: "Nesting generato",
          description: `Creati ${result.nesting_results.length} nesting automatici`
        });
      }
    } catch (err) {
      toast({
        title: "Errore Generazione",
        description: "Impossibile generare il nesting automatico",
        variant: "destructive",
      })
    } finally {
      setIsGeneratingNesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nesting Automatico</h1>
          <p className="text-muted-foreground">
            Configura i parametri e genera il nesting ottimale per gli ODL in attesa
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          <Settings2 className="h-4 w-4 mr-1" />
          Parametri Regolabili
        </Badge>
      </div>

      {/* Errore globale */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pannello parametri */}
        <div className="lg:col-span-1">
          <NestingParametersPanel
            parameters={parameters}
            onParametersChange={handleParametersChange}
            onPreview={handleGeneratePreview}
            isLoading={isLoading || isGeneratingPreview}
            defaultCollapsed={false}
          />
        </div>

        {/* Area principale */}
        <div className="lg:col-span-2 space-y-6">
          {/* Azioni principali */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Play className="h-5 w-5" />
                <span>Azioni Nesting</span>
              </CardTitle>
              <CardDescription>
                Genera una preview o avvia il nesting automatico con i parametri configurati
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  onClick={() => handleGeneratePreview(parameters)}
                  disabled={isGeneratingPreview || isLoading}
                  className="flex-1"
                >
                  {isGeneratingPreview ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Eye className="h-4 w-4 mr-2" />
                  )}
                  Genera Preview
                </Button>
                
                <Button
                  onClick={() => handleGenerateNesting(false)}
                  disabled={isGeneratingNesting || isLoading}
                  className="flex-1"
                >
                  {isGeneratingNesting ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Genera Nesting
                </Button>
              </div>

              <Button
                variant="destructive"
                onClick={() => handleGenerateNesting(true)}
                disabled={isGeneratingNesting || isLoading}
                className="w-full"
                size="sm"
              >
                Forza Rigenerazione (Sovrascrive Bozze)
              </Button>
            </CardContent>
          </Card>

          {/* Preview risultati */}
          {previewData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Preview Nesting</span>
                </CardTitle>
                <CardDescription>
                  Anteprima degli ODL disponibili con i parametri attuali
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {previewData.total_odl_pending}
                    </div>
                    <div className="text-sm text-muted-foreground">ODL Totali</div>
                  </div>
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {previewData.odl_groups.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Gruppi Cicli</div>
                  </div>
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {previewData.available_autoclaves.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Autoclavi Disponibili</div>
                  </div>
                </div>

                <Separator className="my-4" />

                <div className="space-y-3">
                  <h4 className="font-medium">Gruppi per Ciclo di Cura:</h4>
                  {previewData.odl_groups.map((group: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{group.ciclo_cura}</div>
                        <div className="text-sm text-muted-foreground">
                          {group.odl_list.length} ODL • {group.total_area.toFixed(1)} cm² • {group.total_weight.toFixed(1)} kg
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {group.compatible_autoclaves.length} autoclavi compatibili
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risultati nesting */}
          {nestingResults && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Risultati Nesting</span>
                </CardTitle>
                <CardDescription>
                  Nesting automatici generati con successo
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {nestingResults.nesting_results.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Nesting Creati</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {nestingResults.summary?.total_odl_processed || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">ODL Processati</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {nestingResults.summary?.total_odl_excluded || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">ODL Esclusi</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {nestingResults.summary?.autoclavi_utilizzate || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">Autoclavi Utilizzate</div>
                  </div>
                </div>

                <Separator className="my-4" />

                <div className="space-y-3">
                  <h4 className="font-medium">Nesting Generati:</h4>
                  {nestingResults.nesting_results.map((result: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">
                          {result.autoclave_nome} - {result.ciclo_cura}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {result.odl_inclusi} ODL inclusi • {result.efficienza}% efficienza • {result.area_utilizzata} cm²
                        </div>
                      </div>
                      <Badge variant="outline">
                        {result.stato}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}; 