'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Loader2, Plane, AlertTriangle } from 'lucide-react';
import { useStandardToast } from '@/shared/hooks/use-standard-toast';
import { batchNestingApi } from '@/shared/lib/api';
import { NestingParams, defaultNestingParams } from '../schema';
import { StepSidebar, useStepNavigation, StepItem } from '@/shared/components/ui/common/StepSidebar';
import { StepSelectODL } from './components/StepSelectODL';
import { StepSelectAutoclave } from './components/StepSelectAutoclave';
import { StepParams } from './components/StepParams';
import { StepReview } from './components/StepReview';
import { LiveSummary } from './components/LiveSummary';

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
  
  // State data
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [odlList, setOdlList] = useState<ODLData[]>([]);
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([]);
  const [selectedOdl, setSelectedOdl] = useState<string[]>([]);
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<string[]>([]);
  const [parameters, setParameters] = useState<NestingParams>(defaultNestingParams);
  const [error, setError] = useState<string | null>(null);

  // Step navigation setup
  const initialSteps: StepItem[] = [
    {
      id: 'odl',
      title: 'Seleziona ODL',
      description: 'Scegli gli ODL da includere nel nesting',
      status: 'current',
      clickable: true
    },
    {
      id: 'autoclave',
      title: 'Seleziona Autoclavi',
      description: 'Scegli le autoclavi target',
      status: 'pending',
      clickable: true
    },
    {
      id: 'params',
      title: 'Parametri',
      description: 'Configura i parametri aerospace',
      status: 'pending',
      clickable: true
    },
    {
      id: 'review',
      title: 'Riepilogo',
      description: 'Controlla e genera il nesting',
      status: 'pending',
      clickable: true
    }
  ];

  const { steps, currentStepId, updateStepStatus, goToStep } = useStepNavigation(initialSteps);

  // Calcola stato completamento di ogni step
  const isOdlComplete = selectedOdl.length > 0;
  const isAutoclaveComplete = selectedAutoclavi.length > 0;
  const isParamsComplete = parameters.padding_mm > 0 && parameters.min_distance_mm > 0;
  const isReviewComplete = isOdlComplete && isAutoclaveComplete && isParamsComplete;

  // Aggiorna gli stati degli step
  useEffect(() => {
    updateStepStatus('odl', isOdlComplete ? 'completed' : 'pending');
    updateStepStatus('autoclave', isAutoclaveComplete ? 'completed' : 'pending');
    updateStepStatus('params', isParamsComplete ? 'completed' : 'pending');
    updateStepStatus('review', isReviewComplete ? 'completed' : 'pending');
  }, [isOdlComplete, isAutoclaveComplete, isParamsComplete, isReviewComplete, updateStepStatus]);

  // Load data
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

  // Handlers
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

  const handleParametersChange = (newParams: NestingParams) => {
    setParameters(newParams);
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

  // Render step content
  const renderStepContent = () => {
    switch (currentStepId) {
      case 'odl':
        return (
          <StepSelectODL
            odlList={odlList}
            selectedOdl={selectedOdl}
            onSelectionChange={handleOdlSelection}
            isCompleted={isOdlComplete}
          />
        );
      case 'autoclave':
        return (
          <StepSelectAutoclave
            autoclaveList={autoclaveList}
            selectedAutoclavi={selectedAutoclavi}
            onSelectionChange={handleAutoclaveSelection}
            isCompleted={isAutoclaveComplete}
          />
        );
      case 'params':
        return (
          <StepParams
            parameters={parameters}
            onParametersChange={handleParametersChange}
            isCompleted={isParamsComplete}
          />
        );
      case 'review':
        return (
          <StepReview
            selectedOdl={selectedOdl}
            selectedAutoclavi={selectedAutoclavi}
            parameters={parameters}
            odlList={odlList}
            autoclaveList={autoclaveList}
            isCompleted={isReviewComplete}
            generating={generating}
            onGenerate={generateNesting}
          />
        );
      default:
        return null;
    }
  };

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
    <div className="container mx-auto py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Plane className="h-8 w-8 text-blue-600" />
          Nuovo Nesting Aerospace
        </h1>
        <p className="text-muted-foreground">
          Configurazione guidata per generare batch ottimizzati con algoritmi aerospace-grade
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Layout principale con step sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sidebar Steps - sticky */}
        <div className="lg:col-span-3">
          <StepSidebar
            steps={steps}
            currentStepId={currentStepId}
            onStepClick={goToStep}
            title="Configurazione Nesting"
            className="sticky top-6"
          />
        </div>

        {/* Contenuto Step */}
        <div className="lg:col-span-6">
          {renderStepContent()}
        </div>

        {/* Riepilogo Live - sticky */}
        <div className="lg:col-span-3">
          <LiveSummary
            selectedOdl={selectedOdl}
            selectedAutoclavi={selectedAutoclavi}
            parameters={parameters}
            odlList={odlList}
            autoclaveList={autoclaveList}
            currentStepId={currentStepId}
          />
        </div>
      </div>
    </div>
  );
} 