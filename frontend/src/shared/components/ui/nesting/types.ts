// Common types for Nesting UI Components

export type BatchStatus = 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato' | 'draft'

export interface ToolPosition {
  odl_id: number
  id?: number // Fallback per ID se odl_id non disponibile
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean | string
  rotation_angle?: number // Angolo di rotazione specifico
  part_number?: string
  tool_nome?: string
  numero_odl?: string // Numero ODL formattato (es. "2024001")
  descrizione_breve?: string // Descrizione breve della parte
  excluded?: boolean
  // Campi aggiuntivi per tooltip
  area?: number
  posizione?: string
  stato?: string
}

export interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}

export interface BatchMetrics {
  efficiency_percentage?: number
  total_tools?: number
  total_weight?: number
  utilized_area?: number
}

export interface NestingCanvasProps {
  batchData: {
    configurazione_json: {
      canvas_width: number
      canvas_height: number
      tool_positions: ToolPosition[]
      autoclave_mm?: [number, number]
      bounding_px?: [number, number]
    } | null
    autoclave: AutoclaveInfo | undefined
    metrics?: BatchMetrics
    id?: string
  }
  className?: string
  showControls?: boolean
  showGrid?: boolean
  showRuler?: boolean
  onToolClick?: (toolId: number) => void
}

export interface NestingControlsProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onZoomReset: () => void
  onToggleGrid: () => void
  onToggleRuler: () => void
  onToggleTooltips: () => void
  onFullscreen?: () => void
  showGrid: boolean
  showRuler: boolean
  showTooltips: boolean
  zoom: number
}

export interface BatchStatusBadgeProps {
  status: BatchStatus
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'outline' | 'solid'
  className?: string
}

export interface ToolPositionCardProps {
  tool: ToolPosition
  onClick?: () => void
  selected?: boolean
  className?: string
}

export interface AutoclaveInfoCardProps {
  autoclave: AutoclaveInfo
  efficiency?: number
  metrics?: BatchMetrics
  className?: string
}

export interface EfficiencyMeterProps {
  percentage: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

export interface GridLayerProps {
  width: number
  height: number
  showRuler?: boolean
  gridSpacing?: number
  className?: string
}

export interface ToolRectProps {
  tool: ToolPosition
  onClick?: () => void
  isSelected?: boolean
  autoclaveWidth: number
  autoclaveHeight: number
  showTooltips?: boolean
  className?: string
}

// Interfaccia per i risultati dei test di rendering
export interface SmallAreaTestResult {
  width: number
  height: number
  expected: string
  fontSize: string
  textVisible: boolean
  result: string
} 