'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Loader2, 
  Info, 
  TrendingUp, 
  Users, 
  Package, 
  Weight, 
  Gauge,
  AlertCircle,
  Factory,
  Settings,
  BarChart3
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'sonner';

interface BatchDetails {
  id: number;
  nome: string;
  descrizione: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  numero_odl_assegnati: number;
  numero_odl_non_assegnati: number;
  peso_totale_kg: number;
  efficienza_media: number;
  created_at: string;
  updated_at: string;
  creato_da_ruolo: string;
  parametri_nesting: {
    distanza_minima_tool_cm: number;
    padding_bordo_autoclave_cm: number;
    margine_sicurezza_peso_percent: number;
    priorita_minima: number;
    efficienza_minima_percent: number;
  };
  assegnazioni: Record<string, any[]>;
  gruppi_ciclo_cura: string[];
  statistiche_dettagliate: {
    autoclavi_utilizzate: number;
    autoclavi_disponibili: number;
    area_totale_utilizzata: number;
    peso_medio_per_autoclave: number;
    efficienza_per_autoclave: Record<string, number>;
  };
}

interface BatchDetailsModalProps {
  batchId: number;
  isOpen: boolean;
  onClose: () => void;
}

export function BatchDetailsModal({
  batchId,
  isOpen,
  onClose
}: BatchDetailsModalProps) {
  const [batchDetails, setBatchDetails] = useState<BatchDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Carica i dettagli del batch dal backend
   */
  const loadBatchDetails = async () => {
    if (!batchId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/multi-nesting/batch/${batchId}`);
      const data = await response.json();

      if (data.success) {
        setBatchDetails(data.dettagli.batch);
      } else {
        throw new Error(data.message || 'Errore nel caricamento dei dettagli');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Errore sconosciuto');
      toast.error('Errore nel caricamento dei dettagli del batch');
    } finally {
      setIsLoading(false);
    }
  };

  // Carica i dettagli quando il modal si apre
  useEffect(() => {
    if (isOpen && batchId) {
      loadBatchDetails();
    }
  }, [isOpen, batchId]);

  /**
   * Reset dello stato quando il modal si chiude
   */
  useEffect(() => {
    if (!isOpen) {
      setBatchDetails(null);
      setError(null);
    }
  }, [isOpen]);

  /**
   * Formatta la data in formato relativo
   */
  const formatRelativeDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { 
        addSuffix: true, 
        locale: it 
      });
    } catch (error) {
      return 'Data non valida';
    }
  };

  /**
   * Ottiene il colore del badge per lo stato
   */
  const getStatusBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'Pianificazione':
        return 'secondary';
      case 'Pronto':
        return 'default';
      case 'In Esecuzione':
        return 'destructive';
      case 'Completato':
        return 'default';
      case 'Annullato':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  /**
   * Calcola la percentuale di assegnazione ODL
   */
  const getAssignmentPercentage = () => {
    if (!batchDetails || batchDetails.numero_odl_totali === 0) return 0;
    return Math.round((batchDetails.numero_odl_assegnati / batchDetails.numero_odl_totali) * 100);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl">
                {batchDetails ? batchDetails.nome : `Batch #${batchId}`}
              </DialogTitle>
              <DialogDescription>
                Dettagli completi del batch di nesting multiplo
              </DialogDescription>
            </div>
            {batchDetails && (
              <Badge variant={getStatusBadgeVariant(batchDetails.stato)}>
                {batchDetails.stato}
              </Badge>
            )}
          </div>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Caricamento dettagli...</span>
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {batchDetails && !isLoading && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Panoramica</TabsTrigger>
              <TabsTrigger value="autoclaves">Autoclavi</TabsTrigger>
              <TabsTrigger value="parameters">Parametri</TabsTrigger>
              <TabsTrigger value="statistics">Statistiche</TabsTrigger>
            </TabsList>

            {/* Tab Panoramica */}
            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Informazioni generali */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Info className="h-5 w-5" />
                      Informazioni Generali
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Nome</label>
                      <p className="font-medium">{batchDetails.nome}</p>
                    </div>
                    
                    {batchDetails.descrizione && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Descrizione</label>
                        <p className="text-sm">{batchDetails.descrizione}</p>
                      </div>
                    )}
                    
                    <Separator />
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Creato</label>
                        <p className="text-sm">{formatRelativeDate(batchDetails.created_at)}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Creato da</label>
                        <Badge variant="outline" className="text-xs">
                          {batchDetails.creato_da_ruolo}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Statistiche principali */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Statistiche Principali
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <Users className="h-6 w-6 mx-auto mb-1 text-blue-600" />
                        <p className="text-2xl font-bold">{batchDetails.numero_autoclavi}</p>
                        <p className="text-xs text-muted-foreground">Autoclavi</p>
                      </div>
                      
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <Package className="h-6 w-6 mx-auto mb-1 text-green-600" />
                        <p className="text-2xl font-bold">{batchDetails.numero_odl_totali}</p>
                        <p className="text-xs text-muted-foreground">ODL Totali</p>
                      </div>
                      
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <Weight className="h-6 w-6 mx-auto mb-1 text-orange-600" />
                        <p className="text-2xl font-bold">{batchDetails.peso_totale_kg.toFixed(1)}</p>
                        <p className="text-xs text-muted-foreground">kg Totali</p>
                      </div>
                      
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <Gauge className="h-6 w-6 mx-auto mb-1 text-purple-600" />
                        <p className="text-2xl font-bold">{batchDetails.efficienza_media.toFixed(1)}%</p>
                        <p className="text-xs text-muted-foreground">Efficienza</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Progress bar assegnazione ODL */}
              <Card>
                <CardHeader>
                  <CardTitle>Progresso Assegnazione ODL</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>ODL Assegnati</span>
                      <span>{getAssignmentPercentage()}%</span>
                    </div>
                    <Progress value={getAssignmentPercentage()} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{batchDetails.numero_odl_assegnati} assegnati</span>
                      <span>{batchDetails.numero_odl_non_assegnati} non assegnati</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab Autoclavi */}
            <TabsContent value="autoclaves" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Factory className="h-5 w-5" />
                    Autoclavi Utilizzate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <Factory className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">
                      Dettagli autoclavi non disponibili nel formato corrente
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab Parametri */}
            <TabsContent value="parameters" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Parametri di Nesting Utilizzati
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {batchDetails.parametri_nesting ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Distanza minima tool</label>
                          <p className="text-lg font-semibold">{batchDetails.parametri_nesting.distanza_minima_tool_cm} cm</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Padding bordo autoclave</label>
                          <p className="text-lg font-semibold">{batchDetails.parametri_nesting.padding_bordo_autoclave_cm} cm</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Margine sicurezza peso</label>
                          <p className="text-lg font-semibold">{batchDetails.parametri_nesting.margine_sicurezza_peso_percent}%</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Priorità minima ODL</label>
                          <p className="text-lg font-semibold">{batchDetails.parametri_nesting.priorita_minima}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-muted-foreground">Efficienza minima richiesta</label>
                          <p className="text-lg font-semibold">{batchDetails.parametri_nesting.efficienza_minima_percent}%</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        Parametri di nesting non disponibili
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Tab Statistiche */}
            <TabsContent value="statistics" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Statistiche Dettagliate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">Utilizzo Autoclavi</h4>
                      <p className="text-2xl font-bold text-blue-600">{batchDetails.numero_autoclavi}</p>
                      <p className="text-sm text-muted-foreground">autoclavi utilizzate</p>
                    </div>
                    
                    <div className="text-center p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">Efficienza Media</h4>
                      <p className="text-2xl font-bold text-green-600">{batchDetails.efficienza_media.toFixed(1)}%</p>
                      <p className="text-sm text-muted-foreground">utilizzo spazio</p>
                    </div>
                    
                    <div className="text-center p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">Peso Medio</h4>
                      <p className="text-2xl font-bold text-orange-600">
                        {batchDetails.numero_autoclavi > 0 
                          ? (batchDetails.peso_totale_kg / batchDetails.numero_autoclavi).toFixed(1)
                          : '0.0'
                        }
                      </p>
                      <p className="text-sm text-muted-foreground">kg per autoclave</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
} 