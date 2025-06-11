'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { batchNestingApi, autoclavesApi, odlApi, BatchNestingResponse, Autoclave, ODLResponse } from '@/lib/api';
import { Clock, Package, Weight, Gauge, User, Calendar, CheckCircle, AlertCircle } from 'lucide-react';

interface BatchConAutoclave extends BatchNestingResponse {
  autoclave: Autoclave;
  odl_list: ODLResponse[];
}

export default function ConfermaFineCuraPage() {
  const [batches, setBatches] = useState<BatchConAutoclave[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingBatch, setProcessingBatch] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Carica i batch confermati all'avvio
  useEffect(() => {
    caricaBatchConfermati();
  }, []);

  const caricaBatchConfermati = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Recupera solo i batch in stato "sospeso" pronti per caricamento
              const batchList = await batchNestingApi.getAll({ 
          stato: 'sospeso',
        limit: 50 
      });
      
      console.log(`📦 Trovati ${batchList.length} batch confermati`);
      
      // Arricchisci ogni batch con i dati dell'autoclave e degli ODL
      const batchesArricchiti: BatchConAutoclave[] = [];
      
      for (const batch of batchList) {
        try {
          // Recupera i dettagli completi del batch
          const batchCompleto = await batchNestingApi.getOne(batch.id);
          
          // Recupera l'autoclave
          const autoclave = await autoclavesApi.fetchAutoclave(batch.autoclave_id);
          
          // Recupera gli ODL inclusi nel batch (usa batchCompleto che ha odl_ids)
          const odlPromises = batchCompleto.odl_ids.map(id => odlApi.fetchODL(id));
          const odlList: ODLResponse[] = await Promise.all(odlPromises);
          
          batchesArricchiti.push({
            ...batchCompleto,
            autoclave,
            odl_list: odlList
          });
          
        } catch (err) {
          console.error(`❌ Errore nel caricamento del batch ${batch.id}:`, err);
        }
      }
      
      setBatches(batchesArricchiti);
      console.log(`✅ Caricati ${batchesArricchiti.length} batch con dettagli completi`);
      
    } catch (err: any) {
      console.error('❌ Errore nel caricamento dei batch confermati:', err);
      setError(err.message || 'Errore nel caricamento dei batch confermati');
    } finally {
      setLoading(false);
    }
  };

  const handleConfermaFineCura = async (batch: BatchConAutoclave) => {
    if (!batch.id) return;
    
    try {
      setProcessingBatch(batch.id);
      
      console.log(`🏁 Avvio chiusura batch ${batch.id}...`);
      
      // Chiama l'API per chiudere il batch
      await batchNestingApi.chiudi(
        batch.id,
        'operatore_autoclave', // utente simulato
        'Curing' // ruolo
      );
      
      // Mostra messaggio di successo
      alert(`✅ Cura completata! Il batch "${batch.nome || batch.id}" è stato chiuso con successo. L'autoclave è ora disponibile.`);
      
      // Ricarica la lista dei batch
      await caricaBatchConfermati();
      
    } catch (err: any) {
      console.error(`❌ Errore nella chiusura del batch ${batch.id}:`, err);
      
      alert(`❌ Errore nella chiusura: ${err.message || 'Si è verificato un errore durante la chiusura del batch'}`);
    } finally {
      setProcessingBatch(null);
    }
  };

  const calcolaDurataCura = (dataConferma?: string): string => {
    if (!dataConferma) return 'Non disponibile';
    
    const inizioCura = new Date(dataConferma);
    const ora = new Date();
    const durataMs = ora.getTime() - inizioCura.getTime();
    const durataMinuti = Math.floor(durataMs / (1000 * 60));
    
    if (durataMinuti < 60) {
      return `${durataMinuti} minuti`;
    } else {
      const ore = Math.floor(durataMinuti / 60);
      const minutiRestanti = durataMinuti % 60;
      return `${ore}h ${minutiRestanti}m`;
    }
  };

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'confermato': return 'default';
      case 'terminato': return 'secondary';
      default: return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-4">
          <h1 className="text-2xl font-bold">🏁 Conferma Fine Cura</h1>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-600">Caricamento batch in cura...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CheckCircle className="h-6 w-6 text-green-600" />
            Conferma Fine Cura
          </h1>
          <p className="text-gray-600">
            Gestisci la chiusura dei batch nesting al termine del ciclo di cura
          </p>
        </div>

        {/* Errore globale */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Pulsante ricarica */}
        <div className="flex justify-end">
          <Button
            onClick={caricaBatchConfermati}
            disabled={loading}
            variant="outline"
          >
            {loading ? 'Caricamento...' : '🔄 Ricarica'}
          </Button>
        </div>

        {/* Lista batch confermati */}
        {batches.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">
                Nessun batch in cura
              </h3>
              <p className="text-gray-500">
                Al momento non ci sono batch confermati in fase di cura da chiudere.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {batches.map((batch) => (
              <Card key={batch.id} className="shadow-lg">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Package className="h-5 w-5" />
                        {batch.nome || `Batch ${batch.id.slice(0, 8)}`}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-4 mt-2">
                        <span>🏭 {batch.autoclave.nome}</span>
                        <span>📅 {new Date(batch.created_at).toLocaleDateString('it-IT')}</span>
                      </CardDescription>
                    </div>
                    <Badge variant={getStatoBadgeVariant(batch.stato) as any}>
                      {batch.stato.toUpperCase()}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Statistiche del batch */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-blue-600" />
                      <span className="text-sm">
                        <strong>{batch.odl_list.length}</strong> ODL
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Weight className="h-4 w-4 text-green-600" />
                      <span className="text-sm">
                        <strong>{batch.peso_totale_kg}</strong> kg
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Gauge className="h-4 w-4 text-orange-600" />
                      <span className="text-sm">
                        <strong>{batch.valvole_totali_utilizzate}</strong> valvole
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-purple-600" />
                      <span className="text-sm">
                        <strong>{calcolaDurataCura(batch.data_conferma)}</strong>
                      </span>
                    </div>
                  </div>

                  <Separator />

                  {/* Dettagli autoclave */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">🏭 Autoclave: {batch.autoclave.nome}</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-gray-600">
                      <span>📏 {batch.autoclave.lunghezza} × {batch.autoclave.larghezza_piano} mm</span>
                      <span>🌡️ Max {batch.autoclave.temperatura_max}°C</span>
                      <span>🔧 {batch.autoclave.pressione_max} bar</span>
                    </div>
                  </div>

                  {/* Lista ODL */}
                  {batch.odl_list.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">📋 ODL inclusi ({batch.odl_list.length})</h4>
                      <div className="grid gap-2">
                        {batch.odl_list.slice(0, 5).map((odl) => (
                          <div key={odl.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span className="text-sm">
                              <strong>ODL #{odl.id}</strong> - {odl.parte.part_number}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {odl.status}
                            </Badge>
                          </div>
                        ))}
                        {batch.odl_list.length > 5 && (
                          <div className="text-sm text-gray-500 p-2">
                            ... e altri {batch.odl_list.length - 5} ODL
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Informazioni conferma */}
                  {batch.data_conferma && (
                    <div className="bg-blue-50 p-3 rounded-lg text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <User className="h-4 w-4 text-blue-600" />
                        <span className="font-semibold">Confermato da:</span>
                      </div>
                      <div className="ml-6 space-y-1">
                        <div>👤 {batch.confermato_da_utente || 'N/A'} ({batch.confermato_da_ruolo})</div>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-3 w-3" />
                          {new Date(batch.data_conferma).toLocaleString('it-IT')}
                        </div>
                      </div>
                    </div>
                  )}

                  <Separator />

                  {/* Pulsante conferma fine cura */}
                  <div className="flex justify-end">
                    <Button
                      onClick={() => handleConfermaFineCura(batch)}
                      disabled={processingBatch === batch.id}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {processingBatch === batch.id ? (
                        <>
                          <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                          Chiusura in corso...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Conferma Fine Cura
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 