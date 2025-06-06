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
import { FormField } from '@/shared/components/form';
import { Loader2, Settings, Play, AlertTriangle, CheckCircle } from 'lucide-react';
import { odlApi, autoclavesApi } from '@/lib/api';
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
  accorpamento_odl: boolean;
}

export default function NewNestingPage() {
  const router = useRouter();

  // States
  const [odlList, setOdlList] = useState<ODLData[]>([]);
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([]);
  const [selectedOdl, setSelectedOdl] = useState<string[]>([]);
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('');
  const [parametri, setParametri] = useState<NestingParametri>({
    padding_mm: 1,
    min_distance_mm: 1,
    priorita_area: true,
    accorpamento_odl: false
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

        // Carica ODL in attesa di cura
        const odlData = await odlApi.fetchODLs({ status: 'Attesa Cura' });
        console.log('📋 ODL caricati:', odlData);
        setOdlList(odlData);

        // Carica autoclavi disponibili
        const autoclaveResponse = await autoclavesApi.fetchAvailableAutoclaves();
        console.log('🏭 Autoclavi caricate:', autoclaveResponse);
        setAutoclaveList(autoclaveResponse);

        if (autoclaveResponse.length === 0) {
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

  // Generazione nesting
  const generateNesting = async () => {
    if (selectedOdl.length === 0) {
      setError('Seleziona almeno un ODL per generare il nesting');
      return;
    }

    if (!selectedAutoclave) {
      setError('Seleziona un\'autoclave per generare il nesting');
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      console.log('🚀 Avvio generazione nesting:', {
        odl_ids: selectedOdl,
        autoclave_ids: [selectedAutoclave],
        parametri
      });

      // Chiamata API per generare il nesting
      const response = await axios.post('/api/batch_nesting/genera', {
        odl_ids: selectedOdl,
        autoclave_ids: [selectedAutoclave],
        parametri
      });

      console.log('✅ Nesting generato:', response.data);

      // Reindirizza alla pagina di visualizzazione del risultato
      if (response.data.batch_id) {
        router.push(`/nesting/result/${response.data.batch_id}`);
      } else {
        setError('Errore: ID batch non ricevuto dal server');
      }

    } catch (err: any) {
      console.error('❌ Errore nella generazione nesting:', err);
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
          <h1 className="text-3xl font-bold">Nuovo Nesting Automatico</h1>
          <p className="text-muted-foreground">
            Seleziona ODL e autoclave per generare un layout ottimizzato con OR-Tools
          </p>
        </div>
        <Button 
          onClick={() => router.back()} 
          variant="outline"
        >
          Indietro
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
              <CheckCircle className="h-5 w-5" />
              Selezione ODL ({selectedOdl.length} selezionati)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {odlList.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  Nessun ODL in stato "Attesa Cura" disponibile
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {odlList.map((odl) => (
                  <div key={odl.id} className="flex items-center space-x-3 p-3 border rounded-lg">
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
                        <Badge variant="secondary">{odl.parte.part_number}</Badge>
                        <Badge variant="outline">Priorità {odl.priorita}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {odl.parte.descrizione_breve}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Tool: {odl.tool.part_number_tool} • Valvole: {odl.parte.num_valvole_richieste}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Selezione Autoclave e Parametri */}
        <div className="space-y-6">
          {/* Selezione Autoclave */}
          <Card>
            <CardHeader>
              <CardTitle>Autoclave</CardTitle>
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
                        <div className="text-xs text-muted-foreground">
                          {autoclave.num_linee_vuoto} linee • {autoclave.max_load_kg || 1000}kg max
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Parametri Nesting */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Parametri Nesting
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                label="Padding (mm)"
                name="padding_mm"
                type="number"
                value={parametri.padding_mm}
                onChange={(value) => setParametri(prev => ({
                  ...prev,
                  padding_mm: Number(value) || 1
                }))}
                min={5}
                max={100}
                description="Spazio aggiuntivo attorno ai pezzi"
              />

              <FormField
                label="Distanza minima (mm)"
                name="min_distance_mm"
                type="number"
                value={parametri.min_distance_mm}
                onChange={(value) => setParametri(prev => ({
                  ...prev,
                  min_distance_mm: Number(value) || 15
                }))}
                min={5}
                max={50}
                description="Distanza minima tra i pezzi"
              />

              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <Label className="text-sm font-medium">Priorità area</Label>
                  <p className="text-xs text-muted-foreground">
                    Ottimizza per ridurre l'area utilizzata
                  </p>
                </div>
                <Switch
                  checked={parametri.priorita_area}
                  onCheckedChange={(checked) => setParametri(prev => ({
                    ...prev,
                    priorita_area: checked
                  }))}
                />
              </div>

              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <Label className="text-sm font-medium">Accorpamento ODL</Label>
                  <p className="text-xs text-muted-foreground">
                    Raggruppa ODL simili per ottimizzare lo spazio
                  </p>
                </div>
                <Switch
                  checked={parametri.accorpamento_odl}
                  onCheckedChange={(checked) => setParametri(prev => ({
                    ...prev,
                    accorpamento_odl: checked
                  }))}
                />
              </div>
            </CardContent>
          </Card>

          {/* Pulsante Genera */}
          <Button
            onClick={generateNesting}
            disabled={generating || selectedOdl.length === 0 || !selectedAutoclave}
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
                Genera Nesting
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Riepilogo selezione */}
      {(selectedOdl.length > 0 || selectedAutoclave) && (
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
                <h4 className="font-medium mb-2">Autoclave</h4>
                <p className="text-sm">
                  {selectedAutoclave ? 
                    autoclaveList.find(a => a.id.toString() === selectedAutoclave)?.nome || 'Sconosciuta'
                    : 'Nessuna selezionata'
                  }
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-2">Algoritmo</h4>
                <p className="text-sm">OR-Tools CP-SAT</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 