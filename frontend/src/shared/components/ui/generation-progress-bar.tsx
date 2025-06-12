import React, { useState, useEffect, useCallback } from 'react';
import { Progress } from '@/shared/components/ui/progress';
import { CheckCircle2, Clock, Cog, Calculator, Database, Sparkles } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

// Fasi del processo di generazione nesting
export interface GenerationStep {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  estimatedDuration: number; // in ms
  weight: number; // peso relativo per calcolo percentuale
}

// Configurazione delle fasi di generazione
export const GENERATION_STEPS: GenerationStep[] = [
  {
    id: 'validation',
    label: 'Validazione',
    description: 'Controllo ODL e autoclavi selezionate',
    icon: CheckCircle2,
    estimatedDuration: 800,
    weight: 10
  },
  {
    id: 'distribution',
    label: 'Distribuzione',
    description: 'Distribuzione ODL tra autoclavi disponibili',
    icon: Database,
    estimatedDuration: 1200,
    weight: 15
  },
  {
    id: 'calculation',
    label: 'Calcolo Layout',
    description: 'Algoritmi OR-Tools per posizionamento ottimale',
    icon: Calculator,
    estimatedDuration: 4000,
    weight: 60
  },
  {
    id: 'optimization',
    label: 'Ottimizzazione',
    description: 'Post-processing e validazione risultati',
    icon: Cog,
    estimatedDuration: 1500,
    weight: 10
  },
  {
    id: 'finalization',
    label: 'Finalizzazione',
    description: 'Salvataggio batch e preparazione risultati',
    icon: Sparkles,
    estimatedDuration: 500,
    weight: 5
  }
];

interface GenerationProgressBarProps {
  isGenerating: boolean;
  className?: string;
  onComplete?: () => void;
  selectedOdlCount?: number;
  selectedAutoclaveCount?: number;
  variant?: 'compact' | 'detailed';
}

export function GenerationProgressBar({
  isGenerating,
  className,
  onComplete,
  selectedOdlCount = 1,
  selectedAutoclaveCount = 1,
  variant = 'detailed'
}: GenerationProgressBarProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);

  // Calcola durata stimata basata sulla complessità
  const calculateEstimatedDuration = useCallback(() => {
    const baseTime = GENERATION_STEPS.reduce((sum, step) => sum + step.estimatedDuration, 0);
    
    // Fattori di scaling basati sulla complessità
    const odlFactor = Math.max(1, selectedOdlCount / 5); // Scala ogni 5 ODL
    const autoclaveFactor = Math.max(1, selectedAutoclaveCount * 0.8); // +80% per ogni autoclave aggiuntiva
    
    return Math.round(baseTime * odlFactor * autoclaveFactor);
  }, [selectedOdlCount, selectedAutoclaveCount]);

  // Reset quando inizia la generazione
  useEffect(() => {
    if (isGenerating) {
      setCurrentStep(0);
      setProgress(0);
      setStepProgress(0);
    }
  }, [isGenerating]);

  // Simula il progresso realistico
  useEffect(() => {
    if (!isGenerating) return;

    let timeoutId: NodeJS.Timeout | undefined;
    let intervalId: NodeJS.Timeout;
    
    const totalDuration = calculateEstimatedDuration();
    let elapsed = 0;
    let currentStepIndex = 0;
    let stepStartTime = 0;

    const updateProgress = () => {
      elapsed += 50; // Update ogni 50ms
      
      // Calcola il peso cumulativo fino al step corrente
      const cumulativeWeight = GENERATION_STEPS
        .slice(0, currentStepIndex + 1)
        .reduce((sum, step) => sum + step.weight, 0);
      
      const currentStepData = GENERATION_STEPS[currentStepIndex];
      const stepElapsed = elapsed - stepStartTime;
      const stepDuration = (currentStepData.estimatedDuration * totalDuration) / 
        GENERATION_STEPS.reduce((sum, s) => sum + s.estimatedDuration, 0);
      
      // Progresso dello step corrente (0-100)
      const currentStepProgress = Math.min(100, (stepElapsed / stepDuration) * 100);
      setStepProgress(currentStepProgress);
      
      // Progresso totale
      const previousWeight = GENERATION_STEPS
        .slice(0, currentStepIndex)
        .reduce((sum, step) => sum + step.weight, 0);
      
      const totalProgress = previousWeight + 
        (currentStepData.weight * currentStepProgress / 100);
      
      setProgress(Math.min(100, totalProgress));
      
      // Passa al prossimo step quando quello corrente è completato
      if (stepElapsed >= stepDuration && currentStepIndex < GENERATION_STEPS.length - 1) {
        currentStepIndex++;
        setCurrentStep(currentStepIndex);
        stepStartTime = elapsed;
        setStepProgress(0);
      }
      
      // Completa quando tutti gli step sono finiti
      if (elapsed >= totalDuration) {
        setProgress(100);
        setStepProgress(100);
        clearInterval(intervalId);
        onComplete?.();
      }
    };

    intervalId = setInterval(updateProgress, 50);

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      clearInterval(intervalId);
    };
  }, [isGenerating, calculateEstimatedDuration, onComplete]);

  if (!isGenerating) return null;

  const currentStepData = GENERATION_STEPS[currentStep];

  if (variant === 'compact') {
    return (
      <div className={cn("flex items-center gap-3", className)}>
        <div className="flex-1">
          <Progress value={progress} className="h-2" />
        </div>
        <div className="flex items-center gap-2 min-w-0">
          <currentStepData.icon className="h-4 w-4 text-blue-600 animate-pulse" />
          <span className="text-sm text-muted-foreground truncate">
            {currentStepData.label}...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Barra di progresso principale */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <currentStepData.icon className="h-4 w-4 text-blue-600 animate-pulse" />
            <span className="font-medium">{currentStepData.label}</span>
          </div>
          <span className="text-muted-foreground">
            {Math.round(progress)}%
          </span>
        </div>
        
        <Progress value={progress} className="h-3" />
        
        <p className="text-xs text-muted-foreground">
          {currentStepData.description}
        </p>
      </div>

      {/* Indicatori step */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {GENERATION_STEPS.map((step, index) => {
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
            </div>
          );
        })}
      </div>

      {/* Info complessità */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground bg-gray-50 p-3 rounded-lg">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>Durata stimata: ~{Math.round(calculateEstimatedDuration() / 1000)}s</span>
        </div>
        <div className="flex items-center gap-1">
          <Database className="h-3 w-3" />
          <span>{selectedOdlCount} ODL</span>
        </div>
        <div className="flex items-center gap-1">
          <Cog className="h-3 w-3" />
          <span>{selectedAutoclaveCount} Autoclave</span>
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