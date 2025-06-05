/**
 * 🔧 Configurazione dell'applicazione
 */

// URL base dell'API  
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// Endpoint API
export const API_ENDPOINTS = {
  // Dashboard endpoints
  dashboard: {
    odlCount: `${API_BASE_URL}/api/dashboard/odl-count`,
    autoclaveLoad: `${API_BASE_URL}/api/dashboard/autoclave-load`,
    nestingActive: `${API_BASE_URL}/api/dashboard/nesting-active`,
    kpiSummary: `${API_BASE_URL}/api/dashboard/kpi-summary`,
  },
  
  // Health check
  health: `${API_BASE_URL}/health`,
  
  // ODL endpoints
  odl: `${API_BASE_URL}/api/odl`,
  
  // Autoclave endpoints
  autoclavi: `${API_BASE_URL}/api/autoclavi`,
  
  // Tools endpoints
  tools: `${API_BASE_URL}/api/tools`,
} as const

// Configurazione refresh intervals (in millisecondi)
export const REFRESH_INTERVALS = {
  dashboard: 30000,  // 30 secondi
  nesting: 45000,    // 45 secondi
  kpi: 60000,        // 1 minuto
} as const

// Configurazione timeout per le richieste
export const REQUEST_TIMEOUT = 10000 // 10 secondi 