'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Save, 
  Loader2, 
  Factory, 
  Package, 
  Weight, 
  Gauge, 
  Users, 
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface BatchPreview {
  nome: string;
  descrizione: string;
  gruppi_ciclo_cura: string[];
  assegnazioni: Record<string, any[]>;
  statistiche: {
    numero_autoclavi: number;
    numero_odl_totali: number;
    numero_odl_assegnati: number;
    numero_odl_non_assegnati: number;
    peso_totale_kg: number;
    area_totale_utilizzata: number;
    efficienza_media: number;
  };
  parametri_nesting: any;
  autoclavi_disponibili: number;
  autoclavi_utilizzate: number;
  odl_totali: number;
  odl_assegnati: number;
  odl_non_assegnati: number;
  efficienza_media: number;
}

interface BatchPreviewPanelProps {
  batchPreview: BatchPreview;
  onSave: () => void;
  isLoading: boolean;
}

export function BatchPreviewPanel({
  batchPreview,
  onSave,
  isLoading
}: BatchPreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<string>('overview');

  /**
   * Calcola la percentuale di ODL assegnati
   */
  const getAssignmentPercentage = () => {
    if (batchPreview.statistiche.numero_odl_totali === 0) return 0;
    return Math.round(
      (batchPreview.statistiche.numero_odl_assegnati / batchPreview.statistiche.numero_odl_totali) * 100
    );
  };

  /**
   * Ottiene il colore per l'efficienza
   */
  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 80) return 'text-green-600';
    if (efficiency >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  /**
   * Formatta il peso in kg
   */
  const formatWeight = (weight: number) => {
    return `${weight.toFixed(1)} kg`;
  };

  /**
   * Formatta l'area in cm²
   */
  const formatArea = (area: number) => {
    return `${area.toFixed(0)} cm²`;
  };

  return (
    <div className="space-y-6">
      {/* Header del preview */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{batchPreview.nome}</CardTitle>
              <CardDescription className="mt-2">
                {batchPreview.descrizione}
              </CardDescription>
            </div>
            <Button
              onClick={onSave}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Salva Batch
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Statistiche principali */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Factory className="h-5 w-5 text-blue-600" />
              <div className="text-sm font-medium text-muted-foreground">Autoclavi</div>
            </div>
            <div className="text-2xl font-bold">
              {batchPreview.statistiche.numero_autoclavi}
            </div>
            <div className="text-xs text-muted-foreground">
              su {batchPreview.autoclavi_disponibili} disponibili
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Package className="h-5 w-5 text-green-600" />
              <div className="text-sm font-medium text-muted-foreground">ODL Assegnati</div>
            </div>
            <div className="text-2xl font-bold">
              {batchPreview.statistiche.numero_odl_assegnati}
            </div>
            <div className="text-xs text-muted-foreground">
              su {batchPreview.statistiche.numero_odl_totali} totali ({getAssignmentPercentage()}%)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Weight className="h-5 w-5 text-orange-600" />
              <div className="text-sm font-medium text-muted-foreground">Peso Totale</div>
            </div>
            <div className="text-2xl font-bold">
              {formatWeight(batchPreview.statistiche.peso_totale_kg)}
            </div>
            <div className="text-xs text-muted-foreground">
              Carico complessivo
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Gauge className="h-5 w-5 text-purple-600" />
              <div className="text-sm font-medium text-muted-foreground">Efficienza Media</div>
            </div>
            <div className={`text-2xl font-bold ${getEfficiencyColor(batchPreview.statistiche.efficienza_media)}`}>
              {batchPreview.statistiche.efficienza_media.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">
              Utilizzo spazio
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress bar per assegnazione ODL */}
      <Card>
        <CardContent className="p-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progresso Assegnazione ODL</span>
              <span>{getAssignmentPercentage()}%</span>
            </div>
            <Progress value={getAssignmentPercentage()} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{batchPreview.statistiche.numero_odl_assegnati} assegnati</span>
              <span>{batchPreview.statistiche.numero_odl_non_assegnati} non assegnati</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alert per ODL non assegnati */}
      {batchPreview.statistiche.numero_odl_non_assegnati > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>{batchPreview.statistiche.numero_odl_non_assegnati} ODL non sono stati assegnati</strong> 
            {' '}a causa di limitazioni di spazio o efficienza. 
            Considera di modificare i parametri di nesting o di utilizzare autoclavi aggiuntive.
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs per dettagli */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Panoramica</TabsTrigger>
          <TabsTrigger value="autoclaves">Autoclavi</TabsTrigger>
          <TabsTrigger value="groups">Gruppi ODL</TabsTrigger>
        </TabsList>

        {/* Tab Panoramica */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Riepilogo assegnazioni */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Riepilogo Assegnazioni</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Autoclavi utilizzate:</span>
                  <Badge variant="default">{batchPreview.statistiche.numero_autoclavi}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">ODL totali:</span>
                  <Badge variant="outline">{batchPreview.statistiche.numero_odl_totali}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">ODL assegnati:</span>
                  <Badge variant="default">{batchPreview.statistiche.numero_odl_assegnati}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">ODL non assegnati:</span>
                  <Badge variant="destructive">{batchPreview.statistiche.numero_odl_non_assegnati}</Badge>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Area totale utilizzata:</span>
                  <span className="text-sm font-medium">{formatArea(batchPreview.statistiche.area_totale_utilizzata)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Peso totale:</span>
                  <span className="text-sm font-medium">{formatWeight(batchPreview.statistiche.peso_totale_kg)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Parametri utilizzati */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Parametri Utilizzati</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Distanza tool:</div>
                    <div className="font-medium">{batchPreview.parametri_nesting?.distanza_minima_tool_cm ?? 2.0} cm</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Padding bordo:</div>
                    <div className="font-medium">{batchPreview.parametri_nesting?.padding_bordo_autoclave_cm ?? 1.5} cm</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Margine peso:</div>
                    <div className="font-medium">{batchPreview.parametri_nesting?.margine_sicurezza_peso_percent ?? 10.0}%</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Priorità min:</div>
                    <div className="font-medium">{batchPreview.parametri_nesting?.priorita_minima ?? 1}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Efficienza min:</div>
                    <div className="font-medium">{batchPreview.parametri_nesting?.efficienza_minima_percent ?? 60.0}%</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab Autoclavi */}
        <TabsContent value="autoclaves" className="space-y-4">
          <div className="grid gap-4">
            {Object.entries(batchPreview.assegnazioni).map(([cicloKey, assegnazioni]) => (
              <Card key={cicloKey}>
                <CardHeader>
                  <CardTitle className="text-lg">Ciclo di Cura: {cicloKey}</CardTitle>
                  <CardDescription>
                    {assegnazioni.length} autoclave/i assegnate per questo ciclo
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {assegnazioni.map((assegnazione, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-semibold">{assegnazione.autoclave?.nome ?? 'Autoclave Sconosciuta'}</h4>
                            <p className="text-sm text-muted-foreground">
                              Area: {assegnazione.autoclave?.area_piano ? `${assegnazione.autoclave.area_piano} cm²` : 'Non specificata'} • 
                              Capacità: {assegnazione.autoclave?.capacita_peso ? `${assegnazione.autoclave.capacita_peso} kg` : 'Non specificata'}
                            </p>
                          </div>
                          <Badge 
                            variant={assegnazione.efficienza >= 80 ? 'default' : assegnazione.efficienza >= 60 ? 'secondary' : 'destructive'}
                          >
                            {assegnazione.efficienza ? `${assegnazione.efficienza.toFixed(1)}%` : '0.0%'} efficienza
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-muted-foreground">ODL assegnati:</div>
                            <div className="font-medium">{assegnazione.odl_assegnati?.length || 0}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">ODL esclusi:</div>
                            <div className="font-medium">{assegnazione.odl_esclusi?.length || 0}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Peso totale:</div>
                            <div className="font-medium">{formatWeight(assegnazione.peso_totale || 0)}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Area utilizzata:</div>
                            <div className="font-medium">{formatArea(assegnazione.area_utilizzata || 0)}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Tab Gruppi ODL */}
        <TabsContent value="groups" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Gruppi per Ciclo di Cura</CardTitle>
              <CardDescription>
                ODL raggruppati per compatibilità di ciclo di cura
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {batchPreview.gruppi_ciclo_cura.map((gruppo, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{gruppo}</div>
                        <div className="text-sm text-muted-foreground">
                          Gruppo di ciclo di cura compatibile
                        </div>
                      </div>
                    </div>
                    <Badge variant="outline">
                      {batchPreview.assegnazioni[gruppo]?.length || 0} autoclavi
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Azione finale */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <div className="font-medium">Batch Pronto per il Salvataggio</div>
                <div className="text-sm text-muted-foreground">
                  Verifica i dettagli e salva il batch per procedere con la produzione
                </div>
              </div>
            </div>
            <Button
              onClick={onSave}
              disabled={isLoading}
              size="lg"
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Salva Batch
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 