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
      
      // 🚀 AEROSPACE PATTERN: Unified endpoint per tutti i casi
      // Single-batch è semplicemente un sottocaso del multi-batch
      console.log('');
      console.log('🚀🚀🚀 === AEROSPACE UNIFIED NESTING === 🚀🚀🚀');
      console.log(`📋 ODL selezionati: ${selectedOdl.length}`);
      console.log(`🏭 Autoclavi target: ${selectedAutoclavi.length}`);
      console.log(`📊 Modalità: ${selectedAutoclavi.length === 1 ? 'Single-Batch (subset of Multi)' : 'Multi-Batch'}`);
      console.log('🎯 Endpoint: /api/batch_nesting/genera-multi (UNIFIED)');
      console.log('');

      // 🚀 SEMPRE genera-multi - elegante e robusto
      console.log('🔍 PAYLOAD GENERA-MULTI:', {
        odl_ids: selectedOdl,
        parametri: {
          padding_mm: parameters.padding_mm,
          min_distance_mm: parameters.min_distance_mm
        }
      });
      
      let response;
      try {
        response = await batchNestingApi.generaMulti({
          odl_ids: selectedOdl,
          parametri: {
            padding_mm: parameters.padding_mm,
            min_distance_mm: parameters.min_distance_mm
          }
        });
        console.log('✅ API CALL COMPLETATA');
      } catch (apiError: any) {
        console.error('❌ ERRORE CHIAMATA API:', apiError);
        console.error('❌ API ERROR TYPE:', typeof apiError);
        console.error('❌ API ERROR MESSAGE:', apiError?.message);
        console.error('❌ API ERROR RESPONSE:', apiError?.response);
        throw new Error(`Errore chiamata API aerospace: ${apiError?.message || 'Errore sconosciuto'}`);
      }

      console.log('📊 === ANALISI RISPOSTA BACKEND DETTAGLIATA === 📊');
      console.log('🔍 RAW RESPONSE:', response);
      console.log('🔍 RESPONSE TYPE:', typeof response);
      console.log('🔍 RESPONSE KEYS:', response ? Object.keys(response) : 'null');
      console.log('🔍 RESPONSE JSON:', JSON.stringify(response, null, 2));
      
      // ⚠️ IMMEDIATE CHECK: Se response è null/undefined, esci subito
      if (!response) {
        console.error('❌ RESPONSE È NULL/UNDEFINED!');
        throw new Error('Nessuna risposta dal server');
      }

      // 🎯 DEBUGGING APPROFONDITO: Controllo ogni campo
      const isSuccess = response?.success === true;
      const bestBatchId = response?.best_batch_id;
      
      console.log(`🔍 DEBUGGING DETTAGLIATO SUCCESS CHECK:`);
      console.log(`   response.success = ${response?.success} (type: ${typeof response?.success})`);
      console.log(`   response.success === true = ${response?.success === true}`);
      console.log(`   response.best_batch_id = ${response?.best_batch_id} (type: ${typeof response?.best_batch_id})`);
      console.log(`   !!response.best_batch_id = ${!!response?.best_batch_id}`);
      console.log(`   isSuccess = ${isSuccess}`);
      console.log(`   bestBatchId = ${bestBatchId}`);
      console.log(`   Success count: ${response?.success_count}`);
      console.log(`   Message: ${response?.message}`);
      console.log(`   is_real_multi_batch: ${response?.is_real_multi_batch}`);
      console.log(`   unique_autoclavi_count: ${response?.unique_autoclavi_count}`);

      // 🔧 FIX LOGICA SUCCESSO: Considera successo quando success=true E success_count > 0
      // best_batch_id può essere null anche in caso di successo multi-batch
      const successCount = response.success_count || 0;
      const hasValidResults = successCount > 0;
      
      if (isSuccess && hasValidResults) {
        // ✅ SUCCESSO: Il backend ha generato almeno un batch
        const uniqueAutoclavi = response.unique_autoclavi_count || 0;
        const isMultiAutoclave = uniqueAutoclavi > 1;
        
        console.log('✅ NESTING RIUSCITO!');
        console.log(`   Batch generati: ${successCount}`);
        console.log(`   Autoclavi uniche: ${uniqueAutoclavi}`);
        console.log(`   Multi-autoclave: ${isMultiAutoclave}`);
        
        // 🚀 SUCCESS TOAST
        success(
          isMultiAutoclave 
            ? `Multi-batch completato: ${successCount} batch generati!`
            : `Nesting completato con successo!`
        );
        
        // 🚀 REDIRECT ai risultati - Usa best_batch_id se disponibile, altrimenti primo batch
        let redirectBatchId = bestBatchId;
        if (!redirectBatchId && response.batch_results && response.batch_results.length > 0) {
          // Fallback: usa il primo batch disponibile con successo
          const firstSuccessfulBatch = response.batch_results.find((b: any) => b.success && b.batch_id);
          redirectBatchId = firstSuccessfulBatch?.batch_id;
        }
        
        if (redirectBatchId) {
          const routingParams = isMultiAutoclave ? '?multi=true' : '';
          const redirectUrl = `/nesting/result/${redirectBatchId}${routingParams}`;
          
          console.log(`🚀 REDIRECT: ${redirectUrl}`);
          router.push(redirectUrl);
        } else {
          // Fallback estremo: vai alla lista batch
          console.log('⚠️ Nessun batch_id disponibile, redirect alla lista');
          router.push('/nesting/list');
        }
        
        console.log('✅ NESTING GENERATION COMPLETED');
        return; // Esci con successo
      } else {
        // ❌ FALLIMENTO: Il backend non ha generato batch utilizzabili
        console.log('❌❌❌ NESTING CONSIDERATO FALLITO - ANALISI DETTAGLIATA:');
        console.log(`   Condizione 1 - isSuccess: ${isSuccess} (response.success === true: ${response?.success === true})`);
        console.log(`   Condizione 2 - hasValidResults: ${hasValidResults} (success_count > 0: ${successCount > 0})`);
        console.log(`   Condizione combinata (isSuccess && hasValidResults): ${isSuccess && hasValidResults}`);
        console.log('');
        console.log('   VALORI RAW:');
        console.log(`   - response.success: ${response?.success}`);
        console.log(`   - response.best_batch_id: ${response?.best_batch_id}`);
        console.log(`   - response.success_count: ${response?.success_count}`);
        console.log(`   - response.message: ${response?.message}`);
        console.log('');
        console.log('   MOTIVO FALLIMENTO:');
        if (!isSuccess) {
          console.log('   ❌ response.success non è true');
        }
        if (!hasValidResults) {
          console.log('   ❌ success_count è 0 (nessun batch generato)');
        }
        
        // Mostra il messaggio di errore dal backend
        const errorMessage = response?.message || 'Errore nella generazione del nesting';
        throw new Error(errorMessage);
      }
      
    } catch (err: any) {
      console.error('❌❌❌ AEROSPACE ERROR:', err);
      showError(`Errore generazione aerospace: ${err.message || 'Errore sconosciuto'}`);
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
                <div className={`mt-4 p-3 rounded-lg border ${
                  selectedAutoclavi.length > 1 
                    ? 'bg-blue-50 border-blue-200' 
                    : 'bg-green-50 border-green-200'
                }`}>
                  <p className={`text-sm font-medium mb-2 ${
                    selectedAutoclavi.length > 1 
                      ? 'text-blue-800' 
                      : 'text-green-800'
                  }`}>
                    {selectedAutoclavi.length > 1 ? '🚀 MODALITÀ MULTI-BATCH ATTIVA' : '🔄 Single-Batch'}: {selectedAutoclavi.length} autoclavi selezionate
                  </p>
                  <p className={`text-xs mb-2 ${
                    selectedAutoclavi.length > 1 
                      ? 'text-blue-700' 
                      : 'text-green-700'
                  }`}>
                    {selectedAutoclavi.length > 1 
                      ? `Verrà generato un batch separato per ogni autoclave. Gli ODL verranno distribuiti automaticamente tra le ${selectedAutoclavi.length} autoclavi.`
                      : 'Verrà generato un batch per l\'autoclave selezionata.'
                    }
                  </p>
                  {selectedAutoclavi.length > 1 && (
                    <div className="text-xs text-blue-600 mb-2 font-medium">
                      ⚡ Algoritmo: Distribuzione ciclica ODL + Aerospace nesting per ogni autoclave
                    </div>
                  )}
                  <div className="text-xs text-gray-600 mb-2">
                    🔍 DEBUG: IDs selezionati: [{selectedAutoclavi.join(', ')}]
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedAutoclavi.map((autoclaveId) => {
                      const autoclave = autoclaveList.find(a => a.id.toString() === autoclaveId);
                      return autoclave ? (
                        <Badge 
                          key={autoclave.id} 
                          variant="secondary" 
                          className={`text-xs ${
                            selectedAutoclavi.length > 1 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
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