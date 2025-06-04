'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  ArrowLeft, 
  RefreshCw, 
  CheckCircle, 
  Package, 
  Zap, 
  AlertTriangle,
  Clock,
  Settings,
  FileText,
  Loader2
} from 'lucide-react';
import axios from 'axios';

// Interfacce TypeScript
interface BatchDetails {
  id: string;
  nome: string | null;
  stato: 'draft' | 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato';
  autoclave_id: number;
  odl_ids: number[];
  numero_nesting: number;
  peso_totale_kg: number;
  area_totale_utilizzata: number;
  valvole_totali_utilizzate: number;
  efficiency: number;
  area_pct?: number;
  vacuum_util_pct?: number;
  efficiency_score?: number;
  efficiency_level?: string;
  created_at: string;
  updated_at: string;
  data_conferma?: string;
  data_completamento?: string;
  durata_ciclo_minuti?: number;
  creato_da_utente?: string;
  creato_da_ruolo?: string;
  confermato_da_utente?: string;
  confermato_da_ruolo?: string;
  note?: string;
  autoclave?: {
    id: number;
    nome: string;
    codice: string;
    larghezza_piano: number;
    lunghezza: number;
    produttore: string;
  };
}

export default function BatchDetailPage() {
  const router = useRouter();
  const params = useParams();
  const batchId = params.id as string;

  const [batch, setBatch] = useState<BatchDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Stati per i form di transizione
  const [loadedForm, setLoadedForm] = useState({
    caricato_da_utente: 'Operatore',
    caricato_da_ruolo: 'Curing'
  });

  const [curedForm, setCuredForm] = useState({
    curato_da_utente: 'Operatore',
    curato_da_ruolo: 'Curing',
    peso_caricato_kg: '',
    temperatura_max: '',
    pressione_max: '',
    note_operatore: '',
    anomalie: ''
  });

  // Caricamento dettagli batch
  const loadBatchDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(`/api/v1/batch_nesting/${batchId}`);
      console.log('📊 Dettagli batch caricati:', response.data);
      setBatch(response.data);

    } catch (err: any) {
      console.error('❌ Errore nel caricamento batch:', err);
      setError(`Errore nel caricamento: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (batchId) {
      loadBatchDetails();
    }
  }, [batchId]);

  // Funzione per confermare il batch
  const confirmBatch = async () => {
    try {
      setActionLoading('confirm');
      
      const response = await axios.patch(
        `/api/v1/batch_nesting/${batchId}/conferma?confermato_da_utente=Operatore&confermato_da_ruolo=Management`
      );
      
      console.log('✅ Batch confermato:', response.data);
      await loadBatchDetails(); // Ricarica i dettagli
      
    } catch (err: any) {
      console.error('❌ Errore nella conferma:', err);
      alert(`Errore nella conferma: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Funzione per marcare come caricato
  const markAsLoaded = async () => {
    try {
      setActionLoading('loaded');
      
      const response = await axios.patch(
        `/api/v1/batch_nesting/${batchId}/loaded?caricato_da_utente=${loadedForm.caricato_da_utente}&caricato_da_ruolo=${loadedForm.caricato_da_ruolo}`
      );
      
      console.log('📦 Batch marcato come caricato:', response.data);
      await loadBatchDetails(); // Ricarica i dettagli
      
    } catch (err: any) {
      console.error('❌ Errore nel caricamento:', err);
      alert(`Errore nel caricamento: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Funzione per marcare come curato
  const markAsCured = async () => {
    try {
      setActionLoading('cured');
      
      const params = new URLSearchParams({
        curato_da_utente: curedForm.curato_da_utente,
        curato_da_ruolo: curedForm.curato_da_ruolo
      });

      if (curedForm.peso_caricato_kg) params.append('peso_caricato_kg', curedForm.peso_caricato_kg);
      if (curedForm.temperatura_max) params.append('temperatura_max', curedForm.temperatura_max);
      if (curedForm.pressione_max) params.append('pressione_max', curedForm.pressione_max);
      if (curedForm.note_operatore) params.append('note_operatore', curedForm.note_operatore);
      if (curedForm.anomalie) params.append('anomalie', curedForm.anomalie);
      
      const response = await axios.patch(
        `/api/v1/batch_nesting/${batchId}/cured?${params}`
      );
      
      console.log('🎉 Batch marcato come curato:', response.data);
      await loadBatchDetails(); // Ricarica i dettagli
      
    } catch (err: any) {
      console.error('❌ Errore nella marcatura come curato:', err);
      alert(`Errore nella marcatura come curato: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Funzioni di utilità
  const getStatusIcon = (stato: string) => {
    switch (stato) {
      case 'draft': return <Clock className="w-5 h-5" />;
      case 'sospeso': return <AlertTriangle className="w-5 h-5" />;
      case 'confermato': return <CheckCircle className="w-5 h-5" />;
      case 'loaded': return <Package className="w-5 h-5" />;
      case 'cured': return <Zap className="w-5 h-5" />;
      case 'terminato': return <CheckCircle className="w-5 h-5" />;
      default: return <AlertTriangle className="w-5 h-5" />;
    }
  };

  const getStatusColor = (stato: string) => {
    switch (stato) {
      case 'draft': return 'bg-gray-500';
      case 'sospeso': return 'bg-yellow-500';
      case 'confermato': return 'bg-blue-500';
      case 'loaded': return 'bg-purple-500';
      case 'cured': return 'bg-green-500';
      case 'terminato': return 'bg-green-600';
      default: return 'bg-gray-500';
    }
  };

  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 80) return 'bg-green-500';
    if (efficiency >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Caricamento batch...</h2>
            <p className="text-muted-foreground">Recupero dettagli del batch</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !batch) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Batch non trovato'}
          </AlertDescription>
        </Alert>
        <Button 
          onClick={() => router.push('/batch')} 
          className="mt-4"
          variant="outline"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Torna alla Lista
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {batch.nome || `Batch-${batch.id.slice(0, 8)}`}
          </h1>
          <p className="text-muted-foreground">
            Dettagli e gestione del batch nesting
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={loadBatchDetails}
            variant="outline"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          <Button 
            onClick={() => router.push('/batch')} 
            variant="outline"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Torna alla Lista
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Informazioni principali */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Informazioni Batch
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>ID Batch</Label>
                <p className="font-mono text-sm">{batch.id}</p>
              </div>
              <div>
                <Label>Stato</Label>
                <Badge className={`${getStatusColor(batch.stato)} text-white flex items-center gap-1 w-fit mt-1`}>
                  {getStatusIcon(batch.stato)}
                  {batch.stato}
                </Badge>
              </div>
              <div>
                <Label>Efficienza</Label>
                <Badge className={`${getEfficiencyColor(batch.efficiency)} text-white mt-1`}>
                  {batch.efficiency.toFixed(1)}%
                </Badge>
              </div>
              <div>
                <Label>Autoclave</Label>
                <p>#{batch.autoclave_id} - {batch.autoclave?.nome}</p>
              </div>
              <div>
                <Label>ODL Inclusi</Label>
                <p>{batch.odl_ids.length} ODL</p>
              </div>
              <div>
                <Label>Peso Totale</Label>
                <p>{batch.peso_totale_kg.toFixed(1)} kg</p>
              </div>
              <div>
                <Label>Area Utilizzata</Label>
                <p>{batch.area_totale_utilizzata.toFixed(0)} cm²</p>
              </div>
              <div>
                <Label>Valvole Utilizzate</Label>
                <p>{batch.valvole_totali_utilizzate}</p>
              </div>
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Creato il</Label>
                <p className="text-sm">{formatDate(batch.created_at)}</p>
              </div>
              <div>
                <Label>Aggiornato il</Label>
                <p className="text-sm">{formatDate(batch.updated_at)}</p>
              </div>
              {batch.data_conferma && (
                <div>
                  <Label>Confermato il</Label>
                  <p className="text-sm">{formatDate(batch.data_conferma)}</p>
                </div>
              )}
              {batch.data_completamento && (
                <div>
                  <Label>Completato il</Label>
                  <p className="text-sm">{formatDate(batch.data_completamento)}</p>
                </div>
              )}
            </div>

            {batch.note && (
              <>
                <Separator />
                <div>
                  <Label>Note</Label>
                  <p className="text-sm mt-1">{batch.note}</p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Azioni */}
        <div className="space-y-6">
          {/* Azioni di stato */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Azioni
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {batch.stato === 'sospeso' && (
                <Button 
                  onClick={confirmBatch}
                  disabled={actionLoading === 'confirm'}
                  className="w-full"
                >
                  {actionLoading === 'confirm' ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle className="w-4 h-4 mr-2" />
                  )}
                  Conferma Batch
                </Button>
              )}

              {batch.stato === 'confermato' && (
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="caricato-utente">Caricato da</Label>
                    <Input
                      id="caricato-utente"
                      value={loadedForm.caricato_da_utente}
                      onChange={(e) => setLoadedForm(prev => ({
                        ...prev,
                        caricato_da_utente: e.target.value
                      }))}
                    />
                  </div>
                  <Button 
                    onClick={markAsLoaded}
                    disabled={actionLoading === 'loaded'}
                    className="w-full"
                  >
                    {actionLoading === 'loaded' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Package className="w-4 h-4 mr-2" />
                    )}
                    Marca come Caricato
                  </Button>
                </div>
              )}

              {batch.stato === 'loaded' && (
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="curato-utente">Curato da</Label>
                    <Input
                      id="curato-utente"
                      value={curedForm.curato_da_utente}
                      onChange={(e) => setCuredForm(prev => ({
                        ...prev,
                        curato_da_utente: e.target.value
                      }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="peso-reale">Peso caricato (kg)</Label>
                    <Input
                      id="peso-reale"
                      type="number"
                      step="0.1"
                      value={curedForm.peso_caricato_kg}
                      onChange={(e) => setCuredForm(prev => ({
                        ...prev,
                        peso_caricato_kg: e.target.value
                      }))}
                      placeholder="Peso effettivo"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="temp-max">Temp. max (°C)</Label>
                      <Input
                        id="temp-max"
                        type="number"
                        value={curedForm.temperatura_max}
                        onChange={(e) => setCuredForm(prev => ({
                          ...prev,
                          temperatura_max: e.target.value
                        }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="press-max">Press. max (bar)</Label>
                      <Input
                        id="press-max"
                        type="number"
                        step="0.1"
                        value={curedForm.pressione_max}
                        onChange={(e) => setCuredForm(prev => ({
                          ...prev,
                          pressione_max: e.target.value
                        }))}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="note-operatore">Note operatore</Label>
                    <Textarea
                      id="note-operatore"
                      value={curedForm.note_operatore}
                      onChange={(e) => setCuredForm(prev => ({
                        ...prev,
                        note_operatore: e.target.value
                      }))}
                      placeholder="Note sul ciclo di cura..."
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="anomalie">Anomalie</Label>
                    <Textarea
                      id="anomalie"
                      value={curedForm.anomalie}
                      onChange={(e) => setCuredForm(prev => ({
                        ...prev,
                        anomalie: e.target.value
                      }))}
                      placeholder="Eventuali anomalie rilevate..."
                    />
                  </div>
                  <Button 
                    onClick={markAsCured}
                    disabled={actionLoading === 'cured'}
                    className="w-full"
                  >
                    {actionLoading === 'cured' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Zap className="w-4 h-4 mr-2" />
                    )}
                    Marca come Curato
                  </Button>
                </div>
              )}

              {batch.stato === 'cured' && (
                <div className="text-center py-4 text-green-600">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                  <p className="font-medium">Batch Completato</p>
                  <p className="text-sm text-muted-foreground">
                    Il ciclo di cura è stato completato con successo
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Informazioni autoclave */}
          {batch.autoclave && (
            <Card>
              <CardHeader>
                <CardTitle>🏭 Autoclave</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <Label>Nome</Label>
                  <p>{batch.autoclave.nome}</p>
                </div>
                <div>
                  <Label>Codice</Label>
                  <p>{batch.autoclave.codice}</p>
                </div>
                <div>
                  <Label>Dimensioni</Label>
                  <p>{batch.autoclave.lunghezza} × {batch.autoclave.larghezza_piano} mm</p>
                </div>
                <div>
                  <Label>Produttore</Label>
                  <p>{batch.autoclave.produttore}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
} 