'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/shared/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Checkbox } from '@/shared/components/ui/checkbox';
import { Badge } from '@/shared/components/ui/badge';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { 
  Loader2, 
  Play, 
  Package, 
  Factory, 
  Plane,
  AlertTriangle
} from 'lucide-react';
import { useStandardToast } from '@/shared/hooks/use-standard-toast';
import { batchNestingApi, odlApi, autoclavesApi } from '@/shared/lib/api';
import { NestingParams, defaultNestingParams } from '../schema';
import AerospaceParametersForm from './components/AerospaceParametersForm';

interface ODLData {
  id: number;
  parte: {
    id: number;
    part_number: string;
    descrizione_breve: string;
    num_valvole_richieste: number;
  };
  tool: {
    id: number;
    part_number_tool: string;
    descrizione?: string;
  };
  status: string;
  priorita: number;
  created_at: string;
}

interface AutoclaveData {
  id: number;
  nome: string;
  codice: string;
  lunghezza: number;
  larghezza_piano: number;
  stato: string;
  num_linee_vuoto: number;
  temperatura_max: number;
  pressione_max: number;
  max_load_kg?: number;
}

export default function NewNestingPage() {
  const router = useRouter();
  const { success, error: showError } = useStandardToast();
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [odlList, setOdlList] = useState<ODLData[]>([]);
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([]);
  const [selectedOdl, setSelectedOdl] = useState<string[]>([]);
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<string[]>([]);
  const [parameters, setParameters] = useState<NestingParams>(defaultNestingParams);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 🔧 FIX: Usa endpoint nesting che garantisce dati corretti per il nesting
      const nestingData = await batchNestingApi.getData();
      
      // 🔍 DEBUG: Log dati ricevuti
      console.log('🔍 ODL ricevuti:', nestingData.odl_in_attesa_cura?.length || 0);
      console.log('🔍 Autoclavi ricevute:', nestingData.autoclavi_disponibili?.length || 0, nestingData.autoclavi_disponibili);
      
      setOdlList(nestingData.odl_in_attesa_cura || []);
      setAutoclaveList(nestingData.autoclavi_disponibili || []);
      
    } catch (err: any) {
      console.error('Errore nel caricamento dati:', err);
      showError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const handleOdlSelection = (odlId: string, checked: boolean) => {
    setSelectedOdl(prev => 
      checked 
        ? [...prev, odlId]
        : prev.filter(id => id !== odlId)
    );
  };

  const handleAutoclaveSelection = (autoclaveId: string, checked: boolean) => {
    console.log(`🔍 Autoclave ${autoclaveId} ${checked ? 'SELEZIONATA' : 'DESELEZIONATA'}`);
    setSelectedAutoclavi(prev => {
      const newSelection = checked 
        ? [...prev, autoclaveId]
        : prev.filter(id => id !== autoclaveId);
      console.log('🔍 Nuova selezione autoclavi:', newSelection);
      return newSelection;
    });
  };

  const handleSelectAllAutoclavi = (checked: boolean) => {
    const newSelection = checked ? autoclaveList.map(a => a.id.toString()) : [];
    console.log(`🔍 ${checked ? 'SELEZIONA' : 'DESELEZIONA'} TUTTE le autoclavi:`, newSelection);
    setSelectedAutoclavi(newSelection);
  };

  const generateNesting = async () => {
    if (selectedOdl.length === 0) {
      setError('Seleziona almeno un ODL per generare il nesting');
      return;
    }

    if (selectedAutoclavi.length === 0) {
      setError('Seleziona almeno un\'autoclave per generare il nesting');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      
      // 🔍 DEBUG: Log dettagliato delle selezioni
      console.log('=== DEBUG SELEZIONI ===');
      console.log('ODL selezionati:', selectedOdl.length, selectedOdl);
      console.log('Autoclavi selezionate:', selectedAutoclavi.length, selectedAutoclavi);
      console.log('Lista autoclavi disponibili:', autoclaveList.map(a => `${a.id}-${a.nome}`));
      console.log('Condizione multi-batch:', selectedAutoclavi.length > 1);
      
      let response;
      
      if (selectedAutoclavi.length > 1) {
        // 🚀 MULTI-BATCH: Usa endpoint specifico con distribuzione intelligente ODL
        console.log('🚀 CHIAMANDO ENDPOINT MULTI-BATCH per', selectedAutoclavi.length, 'autoclavi');
        response = await batchNestingApi.generaMulti({
          odl_ids: selectedOdl,
          parametri: {
            padding_mm: parameters.padding_mm,
            min_distance_mm: parameters.min_distance_mm
          }
        });
      } else {
        // Single batch: usa endpoint standard
        console.log('🔄 CHIAMANDO ENDPOINT SINGLE-BATCH per autoclave', selectedAutoclavi[0]);
        response = await batchNestingApi.genera({
          odl_ids: selectedOdl,
          autoclave_ids: selectedAutoclavi,
          parametri: {
            padding_mm: parameters.padding_mm,
            min_distance_mm: parameters.min_distance_mm
          }
        });
      }

      // 🔍 DEBUG: Log completo della risposta
      console.log('=== RISPOSTA ENDPOINT ===');
      console.log('Response object:', response);
      console.log('Success:', response?.success);
      console.log('Success count:', response?.success_count);
      console.log('Total autoclavi:', response?.total_autoclavi);
      console.log('Best batch ID:', response?.best_batch_id);
      console.log('Batch results:', response?.batch_results);

      if (response?.success) {
        // Controllo per multi-batch reale
        const isRealMultiBatch = selectedAutoclavi.length > 1 && 
                                response?.success_count > 1 && 
                                response?.batch_results?.length > 1;
        
        console.log('🔍 Is real multi-batch?', isRealMultiBatch);
        console.log('🔍 Selected autoclavi:', selectedAutoclavi.length);
        console.log('🔍 Success count:', response?.success_count);
        console.log('🔍 Batch results length:', response?.batch_results?.length);
        
        success(`${isRealMultiBatch ? 'Multi-batch' : 'Batch'} generato con successo!`);
        
        // Redirect alla pagina risultati
        if (isRealMultiBatch && response.best_batch_id) {
          // Multi-batch reale: vai al best batch con parametro multi
          console.log('🚀 Redirect to MULTI-BATCH result:', response.best_batch_id);
          router.push(`/nesting/result/${response.best_batch_id}?multi=true`);
        } else if (response.best_batch_id) {
          // Single batch: vai al batch generato
          console.log('🚀 Redirect to SINGLE-BATCH result:', response.best_batch_id);
          router.push(`/nesting/result/${response.best_batch_id}`);
        } else if (response.batch_id) {
          // Fallback per compatibility
          console.log('🚀 Redirect to FALLBACK result:', response.batch_id);
          router.push(`/nesting/result/${response.batch_id}`);
        } else {
          // Fallback alla lista nesting
          console.log('⚠️ No batch ID found, redirect to list');
          router.push('/nesting');
        }
      } else {
        throw new Error(response?.message || 'Errore nella generazione');
      }
      
    } catch (err: any) {
      console.error('Errore nella generazione:', err);
      showError(err.message || 'Errore nella generazione del nesting');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Plane className="h-8 w-8 text-blue-600" />
          Nuovo Nesting Aerospace
        </h1>
        <p className="text-muted-foreground">
          Crea un nuovo batch di nesting con parametri ottimizzati per l'industria aerospaziale
        </p>
      </div>

      {/* Errori */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Colonna sinistra - Selezione ODL */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                ODL Disponibili
                <Badge variant="outline">
                  {selectedOdl.length} / {odlList.length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {odlList.length === 0 ? (
                <div className="text-center py-4">
                  <p className="text-muted-foreground text-sm">
                    Nessun ODL disponibile per il nesting
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {odlList.map((odl) => (
                    <div key={odl.id} className="flex items-center space-x-3 p-2 border rounded-lg">
                      <Checkbox
                        id={`odl-${odl.id}`}
                        checked={selectedOdl.includes(odl.id.toString())}
                        onCheckedChange={(checked) => 
                          handleOdlSelection(odl.id.toString(), checked as boolean)
                        }
                      />
                      <div className="flex-1">
                        <div className="font-medium">{odl.parte.part_number}</div>
                        <div className="text-sm text-muted-foreground">
                          {odl.parte.descrizione_breve}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Tool: {odl.tool.part_number_tool} • Priorità: {odl.priorita}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Colonna destra - Selezione Autoclavi e Parametri */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Factory className="h-5 w-5" />
                  Autoclavi
                  <Badge variant="outline">
                    {selectedAutoclavi.length} / {autoclaveList.length}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleSelectAllAutoclavi(true)}
                    disabled={selectedAutoclavi.length === autoclaveList.length}
                  >
                    Seleziona Tutte
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleSelectAllAutoclavi(false)}
                    disabled={selectedAutoclavi.length === 0}
                  >
                    Deseleziona Tutte
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {autoclaveList.length === 0 ? (
                <div className="text-center py-4">
                  <p className="text-muted-foreground text-sm">
                    Nessuna autoclave disponibile
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {autoclaveList.map((autoclave) => (
                    <div key={autoclave.id} className="flex items-center space-x-3">
                      <Checkbox
                        id={`autoclave-${autoclave.id}`}
                        checked={selectedAutoclavi.includes(autoclave.id.toString())}
                        onCheckedChange={(checked) => 
                          handleAutoclaveSelection(autoclave.id.toString(), checked as boolean)
                        }
                      />
                      <div className="flex-1">
                        <div className="font-medium">{autoclave.nome}</div>
                        <div className="text-sm text-muted-foreground">
                          {autoclave.lunghezza}×{autoclave.larghezza_piano}mm
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {autoclave.num_linee_vuoto} linee • {autoclave.max_load_kg || 1000}kg max
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {selectedAutoclavi.length > 0 && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-800 font-medium mb-2">
                    🚀 {selectedAutoclavi.length > 1 ? 'Multi-Batch' : 'Single-Batch'}: {selectedAutoclavi.length} autoclavi selezionate
                  </p>
                  <p className="text-xs text-green-700 mb-2">
                    {selectedAutoclavi.length > 1 
                      ? 'Verrà generato un batch per ogni autoclave selezionata.'
                      : 'Verrà generato un batch per l\'autoclave selezionata.'
                    }
                  </p>
                  <div className="text-xs text-green-600">
                    🔍 DEBUG: IDs selezionati: [{selectedAutoclavi.join(', ')}]
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedAutoclavi.map((autoclaveId) => {
                      const autoclave = autoclaveList.find(a => a.id.toString() === autoclaveId);
                      return autoclave ? (
                        <Badge key={autoclave.id} variant="secondary" className="text-xs">
                          {autoclave.nome}
                        </Badge>
                      ) : null;
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Form Parametri Aerospace */}
          <AerospaceParametersForm
            initialParameters={parameters}
            onParametersChange={setParameters}
          />

          {/* Pulsante Genera */}
          <Button
            onClick={generateNesting}
            disabled={generating || selectedOdl.length === 0 || selectedAutoclavi.length === 0}
            className="w-full"
            size="lg"
          >
            {generating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generazione in corso...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Genera {selectedAutoclavi.length > 1 ? 'Multi-Batch' : 'Nesting'} Aerospace
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Riepilogo selezione */}
      {(selectedOdl.length > 0 || selectedAutoclavi.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Riepilogo Selezione</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h4 className="font-medium mb-2">ODL Selezionati</h4>
                <p className="text-2xl font-bold text-blue-600">{selectedOdl.length}</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Autoclavi</h4>
                <p className="text-2xl font-bold text-green-600">{selectedAutoclavi.length}</p>
                <p className="text-xs text-muted-foreground">
                  {selectedAutoclavi.length > 0 
                    ? `${selectedAutoclavi.length} batch verranno generati`
                    : 'Nessuna selezionata'
                  }
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Algoritmo</h4>
                <p className="text-sm">OR-Tools CP-SAT Aerospace</p>
                <p className="text-xs text-muted-foreground">
                  {parameters.boeing_787_mode ? 'Boeing 787 Mode' : 
                   parameters.airbus_a350_mode ? 'Airbus A350 Mode' : 
                   'General Aviation Mode'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}