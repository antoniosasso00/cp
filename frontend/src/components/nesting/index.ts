// Esportazioni per i componenti di nesting
export { NestingTable } from './NestingTable'
export { NestingPreview } from './NestingPreview'
export { NestingWithParameters } from './NestingWithParameters'
export { NestingParametersPanel } from './NestingParametersPanel'
export { AutomaticNestingResults } from './AutomaticNestingResults'
export { NestingExcludedTools } from './NestingExcludedTools'
export { NestingVisualization } from './NestingVisualization'
export { NestingVisualizationPage } from './NestingVisualizationPage'
export { ActiveNestingTable } from './ActiveNestingTable'
export { NestingCanvas } from './NestingCanvas'
export { NestingSelector } from './NestingSelector'
export { NestingTabWrapper } from './NestingTabsWrapper'

// Nuovi componenti per il redesign workflow-based
export { NestingModeSelector } from './NestingModeSelector'
export { NestingStepIndicator } from './NestingStepIndicator'
export { NestingStateIndicator } from './NestingStateIndicator'

// Componenti per il multi-batch nesting
export { MultiBatchNesting } from './MultiBatchNesting'
export { BatchParametersForm } from './BatchParametersForm'
export { BatchPreviewPanel } from './BatchPreviewPanel'
export { BatchListTable } from './BatchListTable'
export { BatchDetailsModal } from './BatchDetailsModal'

// Tipi TypeScript condivisi
export interface NestingParameters {
  distanza_minima_tool_cm: number;
  padding_bordo_autoclave_cm: number;
  margine_sicurezza_peso_percent: number;
  priorita_minima: number;
  efficienza_minima_percent: number;
}

export interface BatchPreview {
  nome: string;
  descrizione: string;
  gruppi_ciclo_cura: string[];
  assegnazioni: Record<string, any[]>;
  statistiche: {
    numero_autoclavi: number;
    numero_odl_totali: number;
    numero_odl_assegnati: number;
    numero_odl_non_assegnati: number;
    peso_totale_kg: number;
    area_totale_utilizzata: number;
    efficienza_media: number;
  };
  parametri_nesting: NestingParameters;
  autoclavi_disponibili: number;
  autoclavi_utilizzate: number;
  odl_totali: number;
  odl_assegnati: number;
  odl_non_assegnati: number;
  efficienza_media: number;
}

export interface Batch {
  id: number;
  nome: string;
  descrizione: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  peso_totale_kg: number;
  efficienza_media: number;
  created_at: string;
  creato_da_ruolo: string;
} 