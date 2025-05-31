// Tipi per il sistema di nesting - CarbonPilot

export interface ToolPosition {
  odl_id: number
  piano: number
  x: number
  y: number
  width: number
  height: number
  rotated?: boolean
}

export interface ODLLayoutInfo {
  id: number
  parte_id: number
  tool_id: number
  priorita: number
  status: string
  note?: string
  parte: {
    id: number
    part_number: string
    descrizione_breve: string
    num_valvole_richieste: number
    ciclo_cura?: {
      id: number
      nome: string
      durata_stasi1: number
      temperatura_stasi1: number
      pressione_stasi1: number
    }
  }
  tool: {
    id: number
    part_number_tool: string
    descrizione?: string
    lunghezza_piano: number
    larghezza_piano: number
    peso?: number
    materiale?: string
  }
}

export interface AutoclaveLayoutInfo {
  id: number
  nome: string
  codice: string
  lunghezza: number
  larghezza_piano: number
  temperatura_max?: number
  pressione_max?: number
  max_load_kg?: number
  stato: string
  use_secondary_plane: boolean
}

// Usa la definizione compatibile con api.ts
export interface NestingLayoutData {
  id: number;
  autoclave: AutoclaveLayoutInfo;
  odl_list: ODLLayoutInfo[];
  posizioni_tool: ToolPosition[];
  area_utilizzata: number;
  area_totale: number;
  valvole_utilizzate: number;
  valvole_totali: number;
  stato: string;
  ciclo_cura_nome?: string;
  created_at: string;
  note?: string;
  padding_mm: number;
  borda_mm: number;
  rotazione_abilitata: boolean;
}

export interface MultiNestingLayoutData {
  nesting_layouts: NestingLayoutData[]
  summary: {
    total_nesting: number
    total_odl: number
    total_area_utilizzata: number
    total_peso_kg: number
    autoclavi_utilizzate: string[]
  }
}

// Re-export dei tipi già esistenti in api.ts per compatibilità
export type { 
  NestingLayoutResponse,
  MultiNestingLayoutResponse 
} from '@/lib/api' 