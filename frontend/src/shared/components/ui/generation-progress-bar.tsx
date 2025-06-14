import React, { useState, useEffect, useCallback } from 'react';
import { Progress } from '@/shared/components/ui/progress';
import { CheckCircle2, Clock, Cog, Calculator, Database, Sparkles, AlertTriangle, Zap, Target, Layers, RotateCw } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

// 🚀 FASI REALI DEGLI ALGORITMI SOLVER.PY + SOLVER_2L.PY
export interface GenerationStep {
  id: string;
  label: string;
  description: string;
  detailedDescription: string;
  icon: React.ComponentType<{ className?: string }>;
  estimatedDuration: number; // in ms
  weight: number; // peso relativo per calcolo percentuale
  isTimeoutSensitive: boolean; // se questa fase può andare in timeout
  algorithmPhase: 'preprocessing' | 'solving' | 'postprocessing';
}

// 🔧 UTILITY: Formattazione tempo trascorso
const formatTime = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  if (minutes > 0) {
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${remainingSeconds}s`
}

// 🔧 CONFIGURAZIONE FASI REALI BASATE SU SOLVER.PY E SOLVER_2L.PY
export const GENERATION_STEPS: GenerationStep[] = [
  {
    id: 'validation',
    label: 'Validazione & Pre-filtro',
    description: 'Controllo ODL, autoclavi e pre-filtro tool incompatibili',
    detailedDescription: 'Validazione input, controllo dimensioni tool vs autoclavi, esclusione tool oversized, calcolo complessità dataset',
    icon: CheckCircle2,
    estimatedDuration: 800,
    weight: 8,
    isTimeoutSensitive: false,
    algorithmPhase: 'preprocessing'
  },
  {
    id: 'distribution',
    label: 'Distribuzione Multi-Batch',
    description: 'Distribuzione intelligente ODL tra autoclavi disponibili',
    detailedDescription: 'Algoritmo round-robin per distribuzione ODL, bilanciamento peso e compatibilità cicli cura, selezione autoclavi ottimali',
    icon: Database,
    estimatedDuration: 1200,
    weight: 10,
    isTimeoutSensitive: false,
    algorithmPhase: 'preprocessing'
  },
  {
    id: 'level_0_solving',
    label: 'Risoluzione Livello 0',
    description: 'CP-SAT aerospace per piano autoclave (algoritmi OR-Tools)',
    detailedDescription: 'Algoritmo CP-SAT con vincoli geometrici, peso, linee vuoto. Strategie: Bottom-Left FFD, Best-Fit, Corner-Fitting, Gap-Filling',
    icon: Calculator,
    estimatedDuration: 45000, // 45 secondi per livello 0
    weight: 45,
    isTimeoutSensitive: true,
    algorithmPhase: 'solving'
  },
  {
    id: 'level_1_solving',
    label: 'Risoluzione Livello 1 (2L)',
    description: 'Posizionamento cavalletti e tool rimanenti (solo per 2L)',
    detailedDescription: 'Algoritmo greedy per cavalletti, controllo interferenze, calcolo posizioni sicure, ottimizzazione distribuzione peso',
    icon: Layers,
    estimatedDuration: 25000, // 25 secondi per livello 1
    weight: 25,
    isTimeoutSensitive: true,
    algorithmPhase: 'solving'
  },
  {
    id: 'optimization',
    label: 'Post-Processing',
    description: 'GRASP, compattazione, controllo overlap',
    detailedDescription: 'Euristica GRASP per ottimizzazione locale, post-compattazione aerospace, controllo overlap, rotazioni intelligenti',
    icon: Target,
    estimatedDuration: 8000,
    weight: 8,
    isTimeoutSensitive: false,
    algorithmPhase: 'postprocessing'
  },
  {
    id: 'finalization',
    label: 'Finalizzazione',
    description: 'Salvataggio batch e preparazione risultati',
    detailedDescription: 'Conversione layout a formato Pydantic, calcolo metriche finali, salvataggio database, preparazione risposta JSON',
    icon: Sparkles,
    estimatedDuration: 2000,
    weight: 4,
    isTimeoutSensitive: false,
    algorithmPhase: 'postprocessing'
  }
];

export interface GenerationProgressBarProps {
  isGenerating: boolean;
  className?: string;
  onComplete?: () => void;
  selectedOdlCount?: number;
  selectedAutoclaveCount?: number;
  variant?: 'simple' | 'detailed';
  is2LMode?: boolean;
  onTimeout?: (phase: 'warning' | 'critical') => void;
  // isAsyncMode?: boolean; // ❌ RIMOSSO: Modalità asincrona disabilitata
  // asyncJobId?: string;   // ❌ RIMOSSO: ID job per polling
}

export function GenerationProgressBar({
  isGenerating,
  className,
  onComplete,
  selectedOdlCount = 1,
  selectedAutoclaveCount = 1,
  variant = 'detailed',
  is2LMode = false,
  onTimeout
  // isAsyncMode = false, // ❌ RIMOSSO: Modalità asincrona eliminata
  // asyncJobId
}: GenerationProgressBarProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);
  const [timeoutWarning, setTimeoutWarning] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [asyncStatus, setAsyncStatus] = useState<string>(''); // 🚀 NUOVO: Status asincrono

  // 🔧 CALCOLO DURATA REALISTICA BASATA SU COMPLESSITÀ ALGORITMI
  const calculateRealisticDuration = useCallback(() => {
    // Durata base degli step
    let baseDuration = GENERATION_STEPS.reduce((sum, step) => {
      // Salta livello 1 se non è modalità 2L
      if (step.id === 'level_1_solving' && !is2LMode) {
        return sum;
      }
      return sum + step.estimatedDuration;
    }, 0);
    
    // 🚀 FATTORI DI SCALING REALISTICI (basati su solver.py)
    
    // Fattore ODL: Complessità quadratica per CP-SAT
    const odlComplexityFactor = Math.pow(selectedOdlCount / 10, 1.5); // Scaling non lineare
    
    // Fattore autoclavi: +80% per ogni autoclave aggiuntiva
    const autoclaveComplexityFactor = 1 + (selectedAutoclaveCount - 1) * 0.8;
    
    // Fattore 2L: +50% per modalità due livelli
    const levelComplexityFactor = is2LMode ? 1.5 : 1.0;
    
    // Fattore dataset grande: Penalità esponenziale per >20 ODL
    const datasetPenalty = selectedOdlCount > 20 ? Math.pow(selectedOdlCount / 20, 0.8) : 1.0;
    
    const totalComplexity = odlComplexityFactor * autoclaveComplexityFactor * levelComplexityFactor * datasetPenalty;
    
    // ✅ MODALITÀ SEMPRE SINCRONA: Durata ottimizzata
    const maxDuration = is2LMode ? 360000 : 240000; // 6min vs 4min - SEMPRE SINCRONO
    
    const calculatedDuration = Math.min(baseDuration * totalComplexity, maxDuration);
    
    return Math.round(calculatedDuration);
  }, [selectedOdlCount, selectedAutoclaveCount, is2LMode]); // ❌ Rimosso isAsyncMode

  // 🔧 TIMEOUT DINAMICO BASATO SU ALGORITMI REALI
  const calculateTimeoutThresholds = useCallback(() => {
    const totalDuration = calculateRealisticDuration();
    
    return {
      // Timeout per fase di solving (80% del tempo totale)
      solvingTimeout: totalDuration * 0.8,
      // Warning timeout (90% del tempo totale)
      warningTimeout: totalDuration * 0.9,
      // Timeout critico (120% del tempo totale)
      criticalTimeout: totalDuration * 1.2
    };
  }, [calculateRealisticDuration]);

  // Reset quando inizia la generazione
  useEffect(() => {
    if (isGenerating) {
      setCurrentStep(0);
      setProgress(0);
      setStepProgress(0);
      setTimeoutWarning(null);
      setElapsedTime(0);
    }
  }, [isGenerating]);

  // 🚀 SIMULAZIONE PROGRESSO REALISTICA BASATA SU ALGORITMI
  useEffect(() => {
    if (!isGenerating) return;

    let timeoutId: NodeJS.Timeout | undefined;
    let intervalId: NodeJS.Timeout;
    
    const totalDuration = calculateRealisticDuration();
    const timeouts = calculateTimeoutThresholds();
    let elapsed = 0;
    let currentStepIndex = 0;
    let stepStartTime = 0;

    // Filtra step per modalità corrente
    const activeSteps = GENERATION_STEPS.filter(step => {
      if (step.id === 'level_1_solving' && !is2LMode) return false;
      return true;
    });

    const updateProgress = () => {
      elapsed += 100; // Update ogni 100ms per smoothness
      setElapsedTime(elapsed);
      
      // 🚨 GESTIONE TIMEOUT
      if (elapsed > timeouts.criticalTimeout) {
        setTimeoutWarning('TIMEOUT CRITICO: L\'algoritmo potrebbe essere bloccato');
        onTimeout?.('critical');
        clearInterval(intervalId);
        return;
      } else if (elapsed > timeouts.warningTimeout) {
        setTimeoutWarning('Elaborazione più lunga del previsto - algoritmo complesso in corso');
      } else if (elapsed > timeouts.solvingTimeout) {
        setTimeoutWarning('Fase di risoluzione prolungata - dataset complesso');
      }
      
      // Calcola il peso cumulativo fino al step corrente
      const cumulativeWeight = activeSteps
        .slice(0, currentStepIndex + 1)
        .reduce((sum, step) => sum + step.weight, 0);
      
      const currentStepData = activeSteps[currentStepIndex];
      const stepElapsed = elapsed - stepStartTime;
      
      // 🔧 DURATA STEP DINAMICA BASATA SU COMPLESSITÀ
      let stepDuration = currentStepData.estimatedDuration;
      
      // Scaling per step di solving basato su complessità
      if (currentStepData.algorithmPhase === 'solving') {
        const complexityMultiplier = Math.max(1, selectedOdlCount / 10);
        stepDuration *= complexityMultiplier;
      }
      
      // Progresso dello step corrente con curve realistiche
      let currentStepProgress;
      if (currentStepData.algorithmPhase === 'solving') {
        // Curve non lineare per algoritmi CP-SAT (lento all'inizio, accelera)
        const normalizedTime = Math.min(1, stepElapsed / stepDuration);
        currentStepProgress = Math.min(100, Math.pow(normalizedTime, 0.7) * 100);
      } else {
        // Progresso lineare per preprocessing/postprocessing
        currentStepProgress = Math.min(100, (stepElapsed / stepDuration) * 100);
      }
      
      setStepProgress(currentStepProgress);
      
      // Progresso totale
      const previousWeight = activeSteps
        .slice(0, currentStepIndex)
        .reduce((sum, step) => sum + step.weight, 0);
      
      const totalWeight = activeSteps.reduce((sum, step) => sum + step.weight, 0);
      const totalProgress = (previousWeight + (currentStepData.weight * currentStepProgress / 100)) / totalWeight * 100;
      
      setProgress(Math.min(100, totalProgress));
      
      // Passa al prossimo step quando quello corrente è completato
      if (stepElapsed >= stepDuration && currentStepIndex < activeSteps.length - 1) {
        currentStepIndex++;
        setCurrentStep(currentStepIndex);
        stepStartTime = elapsed;
        setStepProgress(0);
      }
      
      // Completa quando tutti gli step sono finiti
      if (elapsed >= totalDuration || currentStepProgress >= 100 && currentStepIndex === activeSteps.length - 1) {
        setProgress(100);
        setStepProgress(100);
        setTimeoutWarning(null);
        clearInterval(intervalId);
        onComplete?.();
      }
    };

    intervalId = setInterval(updateProgress, 100);

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      clearInterval(intervalId);
    };
  }, [isGenerating, calculateRealisticDuration, calculateTimeoutThresholds, onComplete, onTimeout, selectedOdlCount, is2LMode]);

  if (!isGenerating) return null;

  // Filtra step per modalità corrente
  const activeSteps = GENERATION_STEPS.filter(step => {
    if (step.id === 'level_1_solving' && !is2LMode) return false;
    return true;
  });

  const currentStepData = activeSteps[currentStep];
  const totalDuration = calculateRealisticDuration();

  // 🎨 RENDERING CONDIZIONALE: Versione compatta vs dettagliata
  if (variant === 'simple') {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Generazione in corso...
          </span>
          <span className="font-mono text-xs">
            {formatTime(elapsedTime)}
          </span>
        </div>
        <Progress value={progress} className="h-2" />
        {timeoutWarning && (
          <div className="text-xs text-amber-600 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            {timeoutWarning}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Barra di progresso principale */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <currentStepData.icon className="h-4 w-4 text-blue-600 animate-pulse" />
            <span className="font-medium">{currentStepData.label}</span>
            {currentStepData.isTimeoutSensitive && (
              <Clock className="h-3 w-3 text-amber-500" />
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">
              {Math.round(progress)}%
            </span>
            <span className="text-xs text-muted-foreground">
              {Math.round(elapsedTime / 1000)}s
            </span>
          </div>
        </div>
        
        <Progress value={progress} className="h-3" />
        
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">
            {currentStepData.description}
          </p>
          <p className="text-xs text-gray-500 italic">
            {currentStepData.detailedDescription}
          </p>
        </div>
      </div>

      {/* Warning timeout */}
      {timeoutWarning && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <span className="text-sm text-amber-800">{timeoutWarning}</span>
        </div>
      )}

      {/* Indicatori step */}
      <div className="flex flex-wrap gap-2">
        {activeSteps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const IconComponent = step.icon;

          return (
            <div
              key={step.id}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg border min-w-fit transition-all duration-300",
                isActive && "bg-blue-50 border-blue-200 scale-105",
                isCompleted && "bg-green-50 border-green-200",
                !isActive && !isCompleted && "bg-gray-50 border-gray-200"
              )}
            >
              <IconComponent 
                className={cn(
                  "h-3 w-3",
                  isActive && "text-blue-600 animate-pulse",
                  isCompleted && "text-green-600",
                  !isActive && !isCompleted && "text-gray-400"
                )} 
              />
              <span 
                className={cn(
                  "text-xs font-medium",
                  isActive && "text-blue-700",
                  isCompleted && "text-green-700",
                  !isActive && !isCompleted && "text-gray-500"
                )}
              >
                {step.label}
              </span>
              {isCompleted && (
                <CheckCircle2 className="h-3 w-3 text-green-600" />
              )}
              {step.isTimeoutSensitive && isActive && (
                <Clock className="h-3 w-3 text-amber-500 animate-pulse" />
              )}
            </div>
          );
        })}
      </div>

      {/* Info complessità algoritmi */}
      <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
        <div className="space-y-1">
          <div className="flex items-center gap-1">
            <Database className="h-3 w-3" />
            <span>Dataset: {selectedOdlCount} ODL, {selectedAutoclaveCount} autoclavi</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Durata stimata: ~{Math.round(totalDuration / 1000)}s</span>
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-1">
            <Cog className="h-3 w-3" />
            <span>Algoritmo: {is2LMode ? 'CP-SAT + Greedy 2L' : 'CP-SAT Aerospace'}</span>
          </div>
          <div className="flex items-center gap-1">
            {is2LMode ? <Layers className="h-3 w-3" /> : <Target className="h-3 w-3" />}
            <span>Modalità: {is2LMode ? 'Due Livelli (Cavalletti)' : 'Singolo Livello'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Hook per usare il componente in modo più semplice
export function useGenerationProgress() {
  const [isGenerating, setIsGenerating] = useState(false);
  
  const startGeneration = useCallback(() => {
    setIsGenerating(true);
  }, []);
  
  const stopGeneration = useCallback(() => {
    setIsGenerating(false);
  }, []);
  
  return {
    isGenerating,
    startGeneration,
    stopGeneration
  };
}

export default GenerationProgressBar; 