'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/shared/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Checkbox } from '@/shared/components/ui/checkbox';
import { Badge } from '@/shared/components/ui/badge';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/table';
import { 
  Loader2, 
  Play, 
  Package, 
  Factory, 
  Plane,
  AlertTriangle,
  CheckCircle2,
  Calculator
} from 'lucide-react';
import { useStandardToast } from '@/shared/hooks/use-standard-toast';
import { batchNestingApi } from '@/shared/lib/api';
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

// Componente ODL ToolboxTable
interface ODLToolboxTableProps {
  odlList: ODLData[];
  selectedOdl: string[];
  onSelectionChange: (odlId: string, checked: boolean) => void;
}

const ODLToolboxTable: React.FC<ODLToolboxTableProps> = ({ 
  odlList, 
  selectedOdl, 
  onSelectionChange 
}) => {
  const handleSelectAll = (checked: boolean) => {
    odlList.forEach(odl => {
      if (checked && !selectedOdl.includes(odl.id.toString())) {
        onSelectionChange(odl.id.toString(), true);
      } else if (!checked && selectedOdl.includes(odl.id.toString())) {
        onSelectionChange(odl.id.toString(), false);
      }
    });
  };

  const allSelected = odlList.length > 0 && selectedOdl.length === odlList.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            ODL Disponibili
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {selectedOdl.length} / {odlList.length}
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleSelectAll(true)}
              disabled={allSelected}
            >
              Seleziona Tutti
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleSelectAll(false)}
              disabled={selectedOdl.length === 0}
            >
              Deseleziona Tutti
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {odlList.length === 0 ? (
          <div className="text-center py-8">
            <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nessun ODL disponibile per il nesting
            </p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead className="w-20">ODL</TableHead>
                  <TableHead>Parte & Tool</TableHead>
                  <TableHead className="text-center w-20">Priorità</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlList.map((odl) => (
                  <TableRow 
                    key={odl.id} 
                    className={`hover:bg-muted/50 cursor-pointer ${
                      selectedOdl.includes(odl.id.toString()) ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => onSelectionChange(
                      odl.id.toString(), 
                      !selectedOdl.includes(odl.id.toString())
                    )}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedOdl.includes(odl.id.toString())}
                        onCheckedChange={(checked) => 
                          onSelectionChange(odl.id.toString(), checked as boolean)
                        }
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      #{odl.id}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm">
                          {odl.parte.part_number}
                        </div>
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {odl.parte.descrizione_breve}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          <span className="bg-slate-100 px-2 py-0.5 rounded">
                            Tool: {odl.tool.part_number_tool}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline" className="text-xs">
                        P{odl.priorita}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Componente Autoclavi ToolboxTable
interface AutoclaveToolboxTableProps {
  autoclaveList: AutoclaveData[];
  selectedAutoclavi: string[];
  onSelectionChange: (autoclaveId: string, checked: boolean) => void;
}

const AutoclaveToolboxTable: React.FC<AutoclaveToolboxTableProps> = ({ 
  autoclaveList, 
  selectedAutoclavi, 
  onSelectionChange 
}) => {
  const handleSelectAll = (checked: boolean) => {
    autoclaveList.forEach(autoclave => {
      if (checked && !selectedAutoclavi.includes(autoclave.id.toString())) {
        onSelectionChange(autoclave.id.toString(), true);
      } else if (!checked && selectedAutoclavi.includes(autoclave.id.toString())) {
        onSelectionChange(autoclave.id.toString(), false);
      }
    });
  };

  const allSelected = autoclaveList.length > 0 && selectedAutoclavi.length === autoclaveList.length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Factory className="h-5 w-5" />
            Autoclavi Disponibili
            <Badge variant="outline" className="bg-green-50 text-green-700">
              {selectedAutoclavi.length} / {autoclaveList.length}
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleSelectAll(true)}
              disabled={allSelected}
            >
              Seleziona Tutte
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleSelectAll(false)}
              disabled={selectedAutoclavi.length === 0}
            >
              Deseleziona Tutte
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {autoclaveList.length === 0 ? (
          <div className="text-center py-8">
            <Factory className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Nessuna autoclave disponibile
            </p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Autoclave</TableHead>
                  <TableHead className="text-center">Dimensioni</TableHead>
                  <TableHead className="text-center">Capacità</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {autoclaveList.map((autoclave) => (
                  <TableRow 
                    key={autoclave.id} 
                    className={`hover:bg-muted/50 cursor-pointer ${
                      selectedAutoclavi.includes(autoclave.id.toString()) ? 'bg-green-50' : ''
                    }`}
                    onClick={() => onSelectionChange(
                      autoclave.id.toString(), 
                      !selectedAutoclavi.includes(autoclave.id.toString())
                    )}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedAutoclavi.includes(autoclave.id.toString())}
                        onCheckedChange={(checked) => 
                          onSelectionChange(autoclave.id.toString(), checked as boolean)
                        }
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm">
                          {autoclave.nome}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Codice: {autoclave.codice}
                        </div>
                        <div className="text-xs">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            autoclave.stato === 'DISPONIBILE' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {autoclave.stato}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      <div className="font-mono">
                        {autoclave.lunghezza}×{autoclave.larghezza_piano}mm
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      <div className="space-y-1">
                        <div>{autoclave.max_load_kg || 1000}kg</div>
                        <div className="text-xs text-muted-foreground">
                          {autoclave.num_linee_vuoto} linee vuoto
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

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

  // Stima tempo medio di calcolo (in secondi) basato su complexità
  const estimateCalculationTime = (): number => {
    const baseTime = 15; // secondi base
    const odlFactor = selectedOdl.length * 2; // 2s per ODL
    const autoclaveFactor = selectedAutoclavi.length * 3; // 3s per autoclave
    return Math.max(baseTime + odlFactor + autoclaveFactor, 10);
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const nestingData = await batchNestingApi.getData();
      
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
    setSelectedAutoclavi(prev => 
      checked 
        ? [...prev, autoclaveId]
        : prev.filter(id => id !== autoclaveId)
    );
  };

  const generateNesting = async () => {
    try {
      setGenerating(true);
      setError(null);
      
      const response = await batchNestingApi.generaMulti({
        odl_ids: selectedOdl,
        parametri: {
          padding_mm: parameters.padding_mm,
          min_distance_mm: parameters.min_distance_mm
        }
      });

      const isSuccess = response?.success === true;
      const successCount = response.success_count || 0;
      const hasValidResults = successCount > 0;
      
      if (isSuccess && hasValidResults) {
        const uniqueAutoclavi = response.unique_autoclavi_count || 0;
        const isMultiAutoclave = uniqueAutoclavi > 1;
        
        success(
          isMultiAutoclave 
            ? `Multi-batch completato: ${successCount} batch generati!`
            : `Nesting completato con successo!`
        );
        
        let redirectBatchId = response.best_batch_id;
        if (!redirectBatchId && response.batch_results && response.batch_results.length > 0) {
          const firstSuccessfulBatch = response.batch_results.find((b: any) => b.success && b.batch_id);
          redirectBatchId = firstSuccessfulBatch?.batch_id;
        }
        
        if (redirectBatchId) {
          const routingParams = isMultiAutoclave ? '?multi=true' : '';
          const redirectUrl = `/nesting/result/${redirectBatchId}${routingParams}`;
          router.push(redirectUrl);
        } else {
          router.push('/nesting/list');
        }
        
        return;
      } else {
        const errorMessage = response?.message || 'Errore nella generazione del nesting';
        throw new Error(errorMessage);
      }
      
    } catch (err: any) {
      console.error('Errore generazione nesting:', err);
      showError(`Errore generazione nesting: ${err.message || 'Errore sconosciuto'}`);
    } finally {
      setGenerating(false);
    }
  };

  // Validazione selezioni
  const isValidSelection = selectedOdl.length >= 1 && selectedAutoclavi.length >= 1;
  const isMultiAutoclave = selectedAutoclavi.length > 1;
  const estimatedTime = estimateCalculationTime();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Caricamento dati nesting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Plane className="h-8 w-8 text-blue-600" />
          Nuovo Nesting Aerospace
        </h1>
        <p className="text-muted-foreground">
          Seleziona ODL e autoclavi per generare batch ottimizzati con algoritmi aerospace-grade
        </p>
      </div>

      {/* Errori */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Status Selezione */}
      {(selectedOdl.length > 0 || selectedAutoclavi.length > 0) && (
        <Alert className={isValidSelection ? 'border-green-200 bg-green-50' : 'border-orange-200 bg-orange-50'}>
          <div className="flex items-center gap-2">
            {isValidSelection ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-orange-600" />
            )}
            <div className="flex-1">
              <div className={`font-medium ${isValidSelection ? 'text-green-800' : 'text-orange-800'}`}>
                {isValidSelection ? (
                  isMultiAutoclave ? 
                    `🚀 Multi-Batch: ${selectedOdl.length} ODL → ${selectedAutoclavi.length} autoclavi` :
                    `✅ Single-Batch: ${selectedOdl.length} ODL → 1 autoclave`
                ) : (
                  '⚠️ Selezione incompleta'
                )}
              </div>
              <div className={`text-sm ${isValidSelection ? 'text-green-700' : 'text-orange-700'}`}>
                {isValidSelection ? (
                  `Tempo stimato: ~${estimatedTime}s • Algoritmo: OR-Tools CP-SAT Aerospace`
                ) : (
                  `Seleziona almeno 1 ODL e 1 autoclave per continuare`
                )}
              </div>
            </div>
          </div>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Colonna sinistra - Selezione ODL */}
        <div className="space-y-6">
          <ODLToolboxTable
            odlList={odlList}
            selectedOdl={selectedOdl}
            onSelectionChange={handleOdlSelection}
          />
        </div>

        {/* Colonna destra - Selezione Autoclavi e Parametri */}
        <div className="space-y-6">
          <AutoclaveToolboxTable
            autoclaveList={autoclaveList}
            selectedAutoclavi={selectedAutoclavi}
            onSelectionChange={handleAutoclaveSelection}
          />

          {/* Form Parametri Aerospace */}
          <AerospaceParametersForm
            initialParameters={parameters}
            onParametersChange={setParameters}
          />

          {/* Pulsante Genera */}
          <Button
            onClick={generateNesting}
            disabled={generating || !isValidSelection}
            className="w-full"
            size="lg"
          >
            {generating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                <Calculator className="mr-2 h-4 w-4" />
                Calcolo in corso... (~{estimatedTime}s)
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Genera {isMultiAutoclave ? 'Multi-Batch' : 'Nesting'} Aerospace
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Riepilogo Finale */}
      {isValidSelection && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Riepilogo Generazione
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{selectedOdl.length}</div>
                <div className="text-sm text-muted-foreground">ODL Selezionati</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{selectedAutoclavi.length}</div>
                <div className="text-sm text-muted-foreground">
                  Autoclave{selectedAutoclavi.length !== 1 ? 'i' : ''}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{selectedAutoclavi.length}</div>
                <div className="text-sm text-muted-foreground">Batch da Generare</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">~{estimatedTime}s</div>
                <div className="text-sm text-muted-foreground">Tempo Stimato</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}