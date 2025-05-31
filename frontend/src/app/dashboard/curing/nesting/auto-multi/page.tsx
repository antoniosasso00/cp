"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  AlertCircle, 
  CheckCircle2, 
  Loader2, 
  Settings, 
  Play,
  Filter,
  Package,
  Weight,
  Clock
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

// ✅ NUOVO: Import delle funzioni API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

// Helper function per le chiamate API
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  console.log(`🌐 API Call: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorData = await response.text();
      console.error(`❌ API Error ${response.status}:`, errorData);
      throw new Error(`Errore API ${response.status}: ${errorData}`);
    }
    
    const data = await response.json();
    console.log(`✅ API Success:`, data);
    return data;
  } catch (error) {
    console.error(`❌ Fetch Error:`, error);
    throw error;
  }
};

interface ODLDisponibile {
  id: number;
  numero_odl: string;
  parte_nome: string;
  tool_nome: string;
  tool_dimensioni: {
    lunghezza: number;
    larghezza: number;
  };
  peso_kg: number;
  area_stimata: number;
  ciclo_cura: {
    id: number;
    nome: string;
  };
  priorita: string;
  data_creazione: string;
}

interface AutoclaveDisponibile {
  id: number;
  nome: string;
  dimensioni: {
    lunghezza: number;
    larghezza: number;
  };
  capacita_peso_kg: number;
  superficie_piano_1: number;
  superficie_piano_2: number;
  stato: string;
}

interface ParametriNesting {
  efficienza_minima_percent: number;
  peso_massimo_percent: number;
  margine_sicurezza_mm: number;
  priorita_efficienza: boolean;
  separa_cicli_cura: boolean;
}

export default function NestingAutoMultiPage() {
  const router = useRouter();
  
  // Stati per i dati
  const [odlDisponibili, setOdlDisponibili] = useState<ODLDisponibile[]>([]);
  const [autoclavi, setAutoclavi] = useState<AutoclaveDisponibile[]>([]);
  const [odlSelezionati, setOdlSelezionati] = useState<Set<number>>(new Set());
  const [autoclaveSelezionate, setAutoclaveSelezionate] = useState<Set<number>>(new Set());
  
  // Stati per i filtri
  const [filtroCiclo, setFiltroCiclo] = useState<string>("all");
  const [filtroPriorita, setFiltroPriorita] = useState<string>("all");
  const [filtroRicerca, setFiltroRicerca] = useState<string>("");
  
  // Stati per i parametri
  const [parametri, setParametri] = useState<ParametriNesting>({
    efficienza_minima_percent: 10,
    peso_massimo_percent: 90,
    margine_sicurezza_mm: 10,
    priorita_efficienza: true,
    separa_cicli_cura: true
  });
  
  // Stati per l'interfaccia
  const [loading, setLoading] = useState(true);
  const [generando, setGenerando] = useState(false);
  const [errore, setErrore] = useState<string>("");
  const [mostraParametri, setMostraParametri] = useState(false);

  // Caricamento dati iniziali
  useEffect(() => {
    caricaDatiIniziali();
  }, []);

  const caricaDatiIniziali = async () => {
    try {
      setLoading(true);
      setErrore("");

      // Carica ODL disponibili
      const responseODL = await apiCall('/nesting/auto-multi/odl-disponibili');
      if (!responseODL.success) throw new Error(responseODL.error || 'Errore nel caricamento degli ODL');
      const dataODL = responseODL.data || [];

      // Carica autoclavi disponibili
      const responseAutoclavi = await apiCall('/nesting/auto-multi/autoclavi-disponibili');
      if (!responseAutoclavi.success) throw new Error(responseAutoclavi.error || 'Errore nel caricamento delle autoclavi');
      const dataAutoclavi = responseAutoclavi.data || [];

      setOdlDisponibili(dataODL);
      setAutoclavi(dataAutoclavi);

      // Seleziona tutte le autoclavi di default
      if (dataAutoclavi.length > 0) {
        const autoclaveIds = dataAutoclavi.map((a: AutoclaveDisponibile) => a.id);
        setAutoclaveSelezionate(new Set(autoclaveIds));
      }

    } catch (error) {
      console.error('Errore nel caricamento:', error);
      setErrore(error instanceof Error ? error.message : 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  // Gestione selezione ODL
  const toggleODLSelezione = (odlId: number) => {
    const nuovaSezione = new Set(odlSelezionati);
    if (nuovaSezione.has(odlId)) {
      nuovaSezione.delete(odlId);
    } else {
      nuovaSezione.add(odlId);
    }
    setOdlSelezionati(nuovaSezione);
  };

  const selezionaTuttiODL = () => {
    const tuttiIds = odlFiltrati.map(odl => odl.id);
    setOdlSelezionati(new Set(tuttiIds));
  };

  const deselezionaTuttiODL = () => {
    setOdlSelezionati(new Set());
  };

  // Gestione selezione autoclavi
  const toggleAutoclaveSelezione = (autoclaveId: number) => {
    const nuovaSelezione = new Set(autoclaveSelezionate);
    if (nuovaSelezione.has(autoclaveId)) {
      nuovaSelezione.delete(autoclaveId);
    } else {
      nuovaSelezione.add(autoclaveId);
    }
    setAutoclaveSelezionate(nuovaSelezione);
  };

  // Filtri
  const odlFiltrati = odlDisponibili.filter(odl => {
    const matchCiclo = filtroCiclo === "all" || !filtroCiclo || odl.ciclo_cura.nome === filtroCiclo;
    const matchPriorita = filtroPriorita === "all" || !filtroPriorita || odl.priorita === filtroPriorita;
    const matchRicerca = !filtroRicerca || 
      odl.numero_odl.toLowerCase().includes(filtroRicerca.toLowerCase()) ||
      odl.parte_nome.toLowerCase().includes(filtroRicerca.toLowerCase()) ||
      odl.tool_nome.toLowerCase().includes(filtroRicerca.toLowerCase());
    
    return matchCiclo && matchPriorita && matchRicerca;
  });

  // Cicli di cura unici per il filtro
  const cicliCuraUnici = Array.from(new Set(odlDisponibili.map(odl => odl.ciclo_cura.nome)));

  // Generazione nesting
  const generaNesting = async () => {
    if (odlSelezionati.size === 0) {
      setErrore("Seleziona almeno un ODL per procedere");
      return;
    }

    if (autoclaveSelezionate.size === 0) {
      setErrore("Seleziona almeno un'autoclave per procedere");
      return;
    }

    try {
      setGenerando(true);
      setErrore("");

      const payload = {
        odl_ids: Array.from(odlSelezionati),
        autoclave_ids: Array.from(autoclaveSelezionate),
        parametri: parametri
      };

      const response = await apiCall('/nesting/auto-multi/genera', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (!response.success) {
        throw new Error(response.error || 'Errore nella generazione del nesting');
      }

      // Reindirizza alla pagina di preview
      router.push(`/dashboard/curing/nesting/auto-multi/preview?batch_id=${response.batch_id}`);

    } catch (error) {
      console.error('Errore nella generazione:', error);
      setErrore(error instanceof Error ? error.message : 'Errore sconosciuto');
    } finally {
      setGenerando(false);
    }
  };

  // Statistiche di selezione
  const pesoTotaleSelezionato = Array.from(odlSelezionati)
    .map(id => odlDisponibili.find(odl => odl.id === id)?.peso_kg || 0)
    .reduce((sum, peso) => sum + peso, 0);

  const areaTotaleSelezionata = Array.from(odlSelezionati)
    .map(id => odlDisponibili.find(odl => odl.id === id)?.area_stimata || 0)
    .reduce((sum, area) => sum + area, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Caricamento dati...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Nesting Multi-Autoclave Automatico</h1>
          <p className="text-muted-foreground mt-2">
            Seleziona gli ODL e le autoclavi per generare automaticamente il nesting ottimale
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setMostraParametri(!mostraParametri)}
        >
          <Settings className="h-4 w-4 mr-2" />
          Parametri
        </Button>
      </div>

      {/* Errori */}
      {errore && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{errore}</AlertDescription>
        </Alert>
      )}

      {/* Parametri di nesting (collassabile) */}
      {mostraParametri && (
        <Card>
          <CardHeader>
            <CardTitle>Parametri di Ottimizzazione</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="efficienza">Efficienza Minima (%)</Label>
              <Input
                id="efficienza"
                type="number"
                min="0"
                max="100"
                value={parametri.efficienza_minima_percent}
                onChange={(e) => setParametri(prev => ({
                  ...prev,
                  efficienza_minima_percent: Number(e.target.value)
                }))}
              />
            </div>
            <div>
              <Label htmlFor="peso">Peso Massimo (%)</Label>
              <Input
                id="peso"
                type="number"
                min="0"
                max="100"
                value={parametri.peso_massimo_percent}
                onChange={(e) => setParametri(prev => ({
                  ...prev,
                  peso_massimo_percent: Number(e.target.value)
                }))}
              />
            </div>
            <div>
              <Label htmlFor="margine">Margine Sicurezza (mm)</Label>
              <Input
                id="margine"
                type="number"
                min="0"
                value={parametri.margine_sicurezza_mm}
                onChange={(e) => setParametri(prev => ({
                  ...prev,
                  margine_sicurezza_mm: Number(e.target.value)
                }))}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="priorita-efficienza"
                checked={parametri.priorita_efficienza}
                onCheckedChange={(checked) => setParametri(prev => ({
                  ...prev,
                  priorita_efficienza: checked as boolean
                }))}
              />
              <Label htmlFor="priorita-efficienza">Priorità Efficienza</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="separa-cicli"
                checked={parametri.separa_cicli_cura}
                onCheckedChange={(checked) => setParametri(prev => ({
                  ...prev,
                  separa_cicli_cura: checked as boolean
                }))}
              />
              <Label htmlFor="separa-cicli">Separa Cicli di Cura</Label>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Selezione ODL */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  ODL Disponibili ({odlFiltrati.length})
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={selezionaTuttiODL}
                    disabled={odlFiltrati.length === 0}
                  >
                    Seleziona Tutti
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={deselezionaTuttiODL}
                    disabled={odlSelezionati.size === 0}
                  >
                    Deseleziona Tutti
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filtri */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <Label htmlFor="ricerca">Ricerca</Label>
                  <Input
                    id="ricerca"
                    placeholder="ODL, parte, tool..."
                    value={filtroRicerca}
                    onChange={(e) => setFiltroRicerca(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="ciclo">Ciclo di Cura</Label>
                  <Select value={filtroCiclo} onValueChange={setFiltroCiclo}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tutti i cicli" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tutti i cicli</SelectItem>
                      {cicliCuraUnici.map(ciclo => (
                        <SelectItem key={ciclo} value={ciclo}>{ciclo}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="priorita">Priorità</Label>
                  <Select value={filtroPriorita} onValueChange={setFiltroPriorita}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tutte le priorità" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tutte le priorità</SelectItem>
                      <SelectItem value="Alta">Alta</SelectItem>
                      <SelectItem value="Media">Media</SelectItem>
                      <SelectItem value="Bassa">Bassa</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Lista ODL */}
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {odlFiltrati.map(odl => (
                  <div
                    key={odl.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      odlSelezionati.has(odl.id) 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => toggleODLSelezione(odl.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={odlSelezionati.has(odl.id)}
                          onChange={() => {}} // Gestito dal click del container
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">{odl.numero_odl}</span>
                            <Badge variant={
                              odl.priorita === 'Alta' ? 'destructive' :
                              odl.priorita === 'Media' ? 'default' : 'secondary'
                            }>
                              {odl.priorita}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {odl.parte_nome} • {odl.tool_nome}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>
                              {odl.tool_dimensioni.lunghezza}×{odl.tool_dimensioni.larghezza} mm
                            </span>
                            <span className="flex items-center gap-1">
                              <Weight className="h-3 w-3" />
                              {odl.peso_kg} kg
                            </span>
                            <span>{odl.ciclo_cura.nome}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {odlFiltrati.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Nessun ODL trovato con i filtri selezionati</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar con autoclavi e riepilogo */}
        <div className="space-y-6">
          {/* Selezione Autoclavi */}
          <Card>
            <CardHeader>
              <CardTitle>Autoclavi Disponibili ({autoclavi.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {autoclavi.map(autoclave => (
                  <div
                    key={autoclave.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      autoclaveSelezionate.has(autoclave.id)
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => toggleAutoclaveSelezione(autoclave.id)}
                  >
                    <div className="flex items-start gap-2">
                      <Checkbox
                        checked={autoclaveSelezionate.has(autoclave.id)}
                        onChange={() => {}} // Gestito dal click del container
                      />
                      <div className="flex-1">
                        <p className="font-medium text-sm">{autoclave.nome}</p>
                        <p className="text-xs text-muted-foreground">
                          {autoclave.dimensioni.lunghezza}×{autoclave.dimensioni.larghezza} mm
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Max: {autoclave.capacita_peso_kg} kg
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Riepilogo Selezione */}
          <Card>
            <CardHeader>
              <CardTitle>Riepilogo Selezione</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">ODL selezionati:</span>
                <Badge variant="outline">{odlSelezionati.size}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Autoclavi selezionate:</span>
                <Badge variant="outline">{autoclaveSelezionate.size}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Peso totale:</span>
                <span className="text-sm font-medium">{pesoTotaleSelezionato.toFixed(1)} kg</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Area stimata:</span>
                <span className="text-sm font-medium">{areaTotaleSelezionata.toFixed(0)} cm²</span>
              </div>
              
              <Button
                className="w-full"
                onClick={generaNesting}
                disabled={generando || odlSelezionati.size === 0 || autoclaveSelezionate.size === 0}
              >
                {generando ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generazione in corso...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Genera Nesting
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 