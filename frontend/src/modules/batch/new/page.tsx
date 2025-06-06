'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Loader2, Settings, Play, AlertTriangle, CheckCircle, ArrowLeft } from 'lucide-react';
import axios from 'axios';

// Interfacce TypeScript
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

interface NestingParametri {
  padding_mm: number;
  min_distance_mm: number;
  priorita_area: boolean;
}

export default function NewBatchPage() {
  const router = useRouter();

  // States
  const [odlList, setOdlList] = useState<ODLData[]>([]);
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([]);
  const [selectedOdl, setSelectedOdl] = useState<string[]>([]);
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('');
  const [batchName, setBatchName] = useState<string>('');
  const [nestingParams, setNestingParams] = useState<NestingParametri>({
    padding_mm: 1,
    min_distance_mm: 1,
    priorita_area: true
  });
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Caricamento dati iniziali
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Carica dati per il nesting
        const response = await axios.get('http://localhost:8000/batch_nesting/data');
        console.log('📋 Dati nesting caricati:', response.data);
        
        setOdlList(response.data.odl_in_attesa_cura || []);
        setAutoclaveList(response.data.autoclavi_disponibili || []);

        if (response.data.autoclavi_disponibili?.length === 0) {
          setError('⚠️ Nessuna autoclave disponibile. Verifica che almeno un\'autoclave sia in stato "DISPONIBILE".');
        }

      } catch (err: any) {
        console.error('❌ Errore nel caricamento dati:', err);
        setError(`Errore nel caricamento: ${err.message || 'Errore sconosciuto'}`);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Gestione selezione ODL
  const handleOdlSelection = (odlId: string, checked: boolean) => {
    if (checked) {
      setSelectedOdl(prev => [...prev, odlId]);
    } else {
      setSelectedOdl(prev => prev.filter(id => id !== odlId));
    }
  };

  // Gestione selezione autoclave
  const handleAutoclaveSelection = (autoclaveId: string) => {
    setSelectedAutoclave(autoclaveId);
  };

  // Generazione batch
  const generateBatch = async () => {
    if (selectedOdl.length === 0) {
      setError('Seleziona almeno un ODL per generare il batch');
      return;
    }

    if (!selectedAutoclave) {
      setError('Seleziona un\'autoclave per generare il batch');
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      console.log('🚀 Avvio generazione batch:', {
        odl_ids: selectedOdl,
        autoclave_ids: [selectedAutoclave],
        parametri: nestingParams
      });

      // Chiamata API per generare il nesting robusto
      const response = await axios.post('http://localhost:8000/batch_nesting/genera', {
        odl_ids: selectedOdl,
        autoclave_ids: [selectedAutoclave],
        parametri: nestingParams
      });

      console.log('✅ Batch generato:', response.data);

      // Reindirizza alla pagina di visualizzazione del batch
      if (response.data.batch_id) {
        router.push(`/batch/${response.data.batch_id}`);
      } else {
        setError('Errore: ID batch non ricevuto dal server');
      }

    } catch (err: any) {
      console.error('❌ Errore nella generazione batch:', err);
      setError(`Errore nella generazione: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Caricamento dati...</h2>
            <p className="text-muted-foreground">Recupero ODL e autoclavi disponibili</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Nuovo Batch Nesting</h1>
          <p className="text-muted-foreground">
            Seleziona ODL e autoclave per generare un nuovo batch ottimizzato
          </p>
        </div>
        <Button 
          onClick={() => router.push('/batch')} 
          variant="outline"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Torna alla Lista
        </Button>
      </div>

      {/* Errori */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Selezione ODL */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📋 Selezione ODL ({selectedOdl.length} selezionati)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {odlList.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Nessun ODL in attesa di cura</p>
                <p className="text-sm">Verifica che ci siano ODL nello stato "Attesa Cura"</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {odlList.map((odl) => (
                  <div key={odl.id} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                    <Checkbox
                      id={`odl-${odl.id}`}
                      checked={selectedOdl.includes(odl.id.toString())}
                      onCheckedChange={(checked) => 
                        handleOdlSelection(odl.id.toString(), checked as boolean)
                      }
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">ODL #{odl.id}</span>
                        <Badge variant="outline">Priorità {odl.priorita}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <p><strong>Parte:</strong> {odl.parte.part_number} - {odl.parte.descrizione_breve}</p>
                        <p><strong>Tool:</strong> {odl.tool.part_number_tool}</p>
                        <p><strong>Valvole:</strong> {odl.parte.num_valvole_richieste}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Configurazione */}
        <div className="space-y-6">
          {/* Selezione Autoclave */}
          <Card>
            <CardHeader>
              <CardTitle>🏭 Autoclave</CardTitle>
            </CardHeader>
            <CardContent>
              {autoclaveList.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Nessuna autoclave disponibile</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {autoclaveList.map((autoclave) => (
                    <div key={autoclave.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={`autoclave-${autoclave.id}`}
                        checked={selectedAutoclave === autoclave.id.toString()}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            handleAutoclaveSelection(autoclave.id.toString());
                          } else {
                            setSelectedAutoclave('');
                          }
                        }}
                      />
                      <div className="flex-1">
                        <div className="font-medium">{autoclave.nome}</div>
                        <div className="text-sm text-muted-foreground">
                          {autoclave.lunghezza}×{autoclave.larghezza_piano}mm
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Parametri */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Parametri
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="batch-name">Nome Batch (opzionale)</Label>
                <Input
                  id="batch-name"
                  value={batchName}
                  onChange={(e) => setBatchName(e.target.value)}
                  placeholder="Es. Batch_Produzione_01"
                />
              </div>

              <Separator />

              <div>
                <Label htmlFor="padding">Padding (mm)</Label>
                <Input
                  id="padding"
                  type="number"
                  value={nestingParams.padding_mm}
                  onChange={(e) => setNestingParams(prev => ({
                    ...prev,
                    padding_mm: parseInt(e.target.value) || 1
                  }))}
                  min="1"
                  max="50"
                />
              </div>

              <div>
                <Label htmlFor="distance">Distanza minima (mm)</Label>
                <Input
                  id="distance"
                  type="number"
                  value={nestingParams.min_distance_mm}
                  onChange={(e) => setNestingParams(prev => ({
                    ...prev,
                    min_distance_mm: parseInt(e.target.value) || 1
                  }))}
                  min="1"
                  max="30"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="priorita-area"
                  checked={nestingParams.priorita_area}
                  onCheckedChange={(checked) => setNestingParams(prev => ({
                    ...prev,
                    priorita_area: checked
                  }))}
                />
                <Label htmlFor="priorita-area">Priorità area</Label>
              </div>
            </CardContent>
          </Card>

          {/* Pulsante Genera */}
          <Button 
            onClick={generateBatch}
            disabled={generating || selectedOdl.length === 0 || !selectedAutoclave}
            className="w-full"
            size="lg"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generazione in corso...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Genera Batch ({selectedOdl.length} ODL)
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
} 