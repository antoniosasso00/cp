'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Play, Pause, CheckCircle, XCircle, Settings, Eye, Save } from 'lucide-react';
import { toast } from 'sonner';

// Componenti specifici per il multi-nesting
import { BatchPreviewPanel } from './BatchPreviewPanel';
import { BatchParametersForm } from './BatchParametersForm';
import { BatchListTable } from './BatchListTable';
import { BatchDetailsModal } from './BatchDetailsModal';

// Tipi TypeScript
interface NestingParameters {
  distanza_minima_tool_cm: number;
  padding_bordo_autoclave_cm: number;
  margine_sicurezza_peso_percent: number;
  priorita_minima: number;
  efficienza_minima_percent: number;
}

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
  parametri_nesting: NestingParameters;
  autoclavi_disponibili: number;
  autoclavi_utilizzate: number;
  odl_totali: number;
  odl_assegnati: number;
  odl_non_assegnati: number;
  efficienza_media: number;
}

interface Batch {
  id: number;
  nome: string;
  descrizione: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  peso_totale_kg: number;
  efficienza_media: number;
  created_at: string;
  creato_da_ruolo: string;
}

export function MultiBatchNesting() {
  // Stati per la gestione del componente
  const [activeTab, setActiveTab] = useState<string>('preview');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Stati per i parametri e preview
  const [parameters, setParameters] = useState<NestingParameters>({
    distanza_minima_tool_cm: 2.0,
    padding_bordo_autoclave_cm: 1.5,
    margine_sicurezza_peso_percent: 10.0,
    priorita_minima: 1,
    efficienza_minima_percent: 60.0
  });
  
  const [batchPreview, setBatchPreview] = useState<BatchPreview | null>(null);
  const [batchList, setBatchList] = useState<Batch[]>([]);
  
  // Stati per i modali
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [showBatchDetails, setShowBatchDetails] = useState(false);

  // Carica la lista dei batch all'avvio
  useEffect(() => {
    loadBatchList();
  }, []);

  /**
   * Carica la lista dei batch dal backend
   */
  const loadBatchList = async () => {
    try {
      const response = await fetch('/api/multi-nesting/batch');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setBatchList(data.batch_list || []);
      } else {
        throw new Error(data.message || 'Errore nel caricamento dei batch');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
      setError(`Errore nel caricamento batch: ${errorMessage}`);
      setBatchList([]);
      toast.error('Errore nel caricamento dei batch salvati');
    }
  };

  /**
   * Crea un preview del batch con i parametri correnti
   */
  const createBatchPreview = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/multi-nesting/preview-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parametri_nesting: parameters,
          priorita_minima: parameters.priorita_minima,
          nome_batch: null // Verrà generato automaticamente
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setBatchPreview(data.batch_preview);
        toast.success(data.message);
        setActiveTab('preview');
      } else {
        throw new Error(data.message || 'Errore nella creazione del preview');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
      setError(`Errore nella creazione preview: ${errorMessage}`);
      setBatchPreview(null);
      toast.error('Impossibile creare il preview del batch');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Salva il batch corrente nel database
   */
  const saveBatch = async () => {
    if (!batchPreview) {
      toast.error('Nessun preview del batch disponibile');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/multi-nesting/salva-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch_preview: batchPreview,
          creato_da_ruolo: localStorage.getItem('user_role') || 'Operatore' // Ottiene dal localStorage o default
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        setBatchPreview(null); // Reset del preview
        await loadBatchList(); // Ricarica la lista
        setActiveTab('batches'); // Passa alla tab dei batch
      } else {
        throw new Error(data.message || 'Errore nel salvataggio del batch');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
      setError(`Errore nel salvataggio: ${errorMessage}`);
      toast.error('Impossibile salvare il batch');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Aggiorna lo stato di un batch
   */
  const updateBatchStatus = async (batchId: number, newStatus: string) => {
    try {
      const response = await fetch(`/api/multi-nesting/batch/${batchId}/stato?nuovo_stato=${newStatus}`, {
        method: 'PUT',
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        await loadBatchList(); // Ricarica la lista
      } else {
        throw new Error(data.message || 'Errore nell\'aggiornamento dello stato');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
      setError(`Errore aggiornamento stato: ${errorMessage}`);
      toast.error('Errore nell\'aggiornamento dello stato del batch');
    }
  };

  /**
   * Elimina un batch
   */
  const deleteBatch = async (batchId: number) => {
    if (!confirm('Sei sicuro di voler eliminare questo batch? Questa operazione è irreversibile.')) {
      return;
    }

    try {
      const response = await fetch(`/api/multi-nesting/batch/${batchId}`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        await loadBatchList(); // Ricarica la lista
      } else {
        throw new Error(data.message || 'Errore nell\'eliminazione del batch');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto';
      setError(`Errore eliminazione batch: ${errorMessage}`);
      toast.error('Errore nell\'eliminazione del batch');
    }
  };

  /**
   * Mostra i dettagli di un batch
   */
  const showBatchDetailsModal = (batchId: number) => {
    setSelectedBatchId(batchId);
    setShowBatchDetails(true);
  };

  /**
   * Ottiene il colore del badge per lo stato del batch
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

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nesting Multiplo</h1>
          <p className="text-muted-foreground">
            Gestione batch di nesting con assegnazione automatica di autoclavi multiple
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={createBatchPreview}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
            Crea Preview
          </Button>
          
          {batchPreview && (
            <Button
              onClick={saveBatch}
              disabled={isLoading}
              variant="default"
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Salva Batch
            </Button>
          )}
        </div>
      </div>

      {/* Alert per errori */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Tabs principali */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="parameters" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Parametri
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Preview Batch
          </TabsTrigger>
          <TabsTrigger value="batches" className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Batch Salvati
          </TabsTrigger>
        </TabsList>

        {/* Tab Parametri */}
        <TabsContent value="parameters" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parametri di Nesting</CardTitle>
              <CardDescription>
                Configura i parametri per l'ottimizzazione del nesting multiplo
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BatchParametersForm
                parameters={parameters}
                onParametersChange={setParameters}
                onCreatePreview={createBatchPreview}
                isLoading={isLoading}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab Preview */}
        <TabsContent value="preview" className="space-y-4">
          {batchPreview ? (
            <BatchPreviewPanel
              batchPreview={batchPreview}
              onSave={saveBatch}
              isLoading={isLoading}
            />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Eye className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Nessun Preview Disponibile</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Configura i parametri e clicca su "Crea Preview" per visualizzare 
                  l'anteprima del batch di nesting multiplo.
                </p>
                <Button onClick={() => setActiveTab('parameters')} variant="outline">
                  Vai ai Parametri
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab Batch Salvati */}
        <TabsContent value="batches" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Batch di Nesting Salvati</CardTitle>
              <CardDescription>
                Gestisci i batch di nesting creati e monitora il loro stato
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BatchListTable
                batches={batchList}
                onViewDetails={showBatchDetailsModal}
                onUpdateStatus={updateBatchStatus}
                onDelete={deleteBatch}
                getStatusBadgeVariant={getStatusBadgeVariant}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal per i dettagli del batch */}
      {showBatchDetails && selectedBatchId && (
        <BatchDetailsModal
          batchId={selectedBatchId}
          isOpen={showBatchDetails}
          onClose={() => {
            setShowBatchDetails(false);
            setSelectedBatchId(null);
          }}
        />
      )}
    </div>
  );
} 