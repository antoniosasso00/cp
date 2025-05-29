// API client per interagire con il backend

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Configurazione axios con interceptors per logging e gestione errori
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 secondi di timeout
})

// Interceptor per le richieste
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('❌ Errore nella richiesta API:', error);
    return Promise.reject(error);
  }
);

// Interceptor per le risposte
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('❌ Errore nella risposta API:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    
    // Gestione errori specifici con messaggi più dettagliati
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      const errorMessage = 'Errore di connessione – verifica che il backend sia attivo e l\'endpoint esista';
      console.error('🔌 Errore di connessione:', errorMessage);
      throw new Error(errorMessage);
    }
    
    if (error.response?.status === 404) {
      const errorMessage = `Endpoint non trovato: ${error.config?.url}`;
      console.error('🔍 Endpoint non trovato:', errorMessage);
      throw new Error(errorMessage);
    }
    
    if (error.response?.status >= 500) {
      const errorMessage = 'Errore interno del server. Riprova più tardi.';
      console.error('🔥 Errore server:', errorMessage);
      throw new Error(errorMessage);
    }
    
    if (error.response?.status === 422) {
      const errorMessage = error.response.data?.detail || 'Dati non validi';
      console.error('📝 Errore validazione:', errorMessage);
      throw new Error(errorMessage);
    }
    
    if (error.response?.status === 400) {
      const errorMessage = error.response.data?.detail || 'Richiesta non valida';
      console.error('❌ Richiesta non valida:', errorMessage);
      throw new Error(errorMessage);
    }
    
    throw error;
  }
);

// Tipi base per Catalogo
export interface CatalogoBase {
  descrizione: string;
  categoria?: string;
  sotto_categoria?: string;
  attivo: boolean;
  note?: string;
}

export interface CatalogoCreate extends CatalogoBase {
  part_number: string;
}

export interface CatalogoUpdate extends Partial<CatalogoBase> {}

export interface CatalogoResponse extends CatalogoBase {
  part_number: string;
  created_at: string;
  updated_at: string;
}

// Tipi base per Parte
export interface ParteBase {
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
  note_produzione?: string;
}

export interface ParteCreate extends ParteBase {
  ciclo_cura_id?: number;
  tool_ids: number[];
}

export interface ParteUpdate extends Partial<ParteBase> {
  ciclo_cura_id?: number;
  tool_ids?: number[];
}

export interface ToolInParteResponse {
  id: number;
  part_number_tool: string;
  descrizione?: string;
}

export interface CicloCuraInParteResponse {
  id: number;
  nome: string;
}

export interface CatalogoInParteResponse {
  part_number: string;
  descrizione: string;
  categoria?: string;
}

export interface ParteResponse extends ParteBase {
  id: number;
  ciclo_cura?: CicloCuraInParteResponse;
  tools: ToolInParteResponse[];
  catalogo: CatalogoInParteResponse;
  created_at: string;
  updated_at: string;
}

export interface Tool {
  id: number
  part_number_tool: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  // ✅ NUOVO: Campi per nesting su due piani
  peso?: number
  materiale?: string
  disponibile: boolean
  created_at: string
  updated_at: string
  // ✅ NUOVO: Campo calcolato per l'area
  area?: number
}

export interface ToolWithStatus extends Tool {
  status_display: string
  current_odl?: {
    id: number
    status: string
    parte_id: number
    updated_at: string | null
  } | null
}

export interface CreateToolDto {
  part_number_tool: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  // ✅ NUOVO: Campi per nesting su due piani
  peso?: number
  materiale?: string
  disponibile: boolean
}

export interface UpdateToolDto extends Partial<CreateToolDto> {}

export const toolApi = {
  getAll: async (): Promise<Tool[]> => {
    const response = await api.get<Tool[]>('/tools')
    return response.data
  },

  getAllWithStatus: async (params?: { 
    skip?: number; 
    limit?: number; 
    part_number_tool?: string; 
    disponibile?: boolean 
  }): Promise<ToolWithStatus[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.part_number_tool) queryParams.append('part_number_tool', params.part_number_tool);
    if (params?.disponibile !== undefined) queryParams.append('disponibile', params.disponibile.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ToolWithStatus[]>(`/tools/with-status${query}`);
  },

  getById: async (id: number): Promise<Tool> => {
    const response = await api.get<Tool>(`/tools/${id}`)
    return response.data
  },

  create: async (data: CreateToolDto): Promise<Tool> => {
    const response = await api.post<Tool>('/tools', data)
    return response.data
  },

  update: async (id: number, data: UpdateToolDto): Promise<Tool> => {
    const response = await api.put<Tool>(`/tools/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tools/${id}`)
  },

  updateStatusFromODL: async (): Promise<{
    message: string;
    updated_tools: Array<{
      id: number;
      part_number_tool: string;
      old_status: string;
      new_status: string;
      odl_info?: any;
    }>;
    total_tools: number;
    tools_in_use: number;
    tools_available: number;
    tools_by_status: Record<string, number>;
  }> => {
    const response = await api.put('/tools/update-status-from-odl')
    return response.data
  },
}

// Common fetch wrapper
const apiRequest = async <T>(
  endpoint: string, 
  method: string = 'GET', 
  data?: any
): Promise<T> => {
  const fullUrl = `${API_BASE_URL}${endpoint}`;

  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    cache: 'no-store', // Disabilita la cache per ottenere sempre dati aggiornati
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(fullUrl, options);

    // Gestione errori HTTP
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
        url: fullUrl,
        method
      };
      
      console.error('❌ API Error:', error); // Log dettagliato dell'errore
      
      // Mostra toast se disponibile (in modo sicuro)
      if (typeof window !== 'undefined' && window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('api-error', { 
          detail: { 
            message: error.message, 
            status: error.status,
            url: fullUrl 
          } 
        }));
      }
      
      throw error;
    }

    // Per DELETE (204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('💥 API Network Error:', method, fullUrl, error);
    
    // Mostra toast per errori di rete
    if (typeof window !== 'undefined' && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent('api-error', { 
        detail: { 
          message: error instanceof Error ? error.message : 'Errore di connessione', 
          status: 0,
          url: fullUrl 
        } 
      }));
    }
    
    throw error;
  }
};

// API Catalogo
export const catalogoApi = {
  getAll: (params?: { skip?: number; limit?: number; categoria?: string; sotto_categoria?: string; attivo?: boolean; search?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.categoria) queryParams.append('categoria', params.categoria);
    if (params?.sotto_categoria) queryParams.append('sotto_categoria', params.sotto_categoria);
    if (params?.attivo !== undefined) queryParams.append('attivo', params.attivo.toString());
    if (params?.search) queryParams.append('search', params.search);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<CatalogoResponse[]>(`/catalogo${query}`);
  },
  
  getOne: (partNumber: string) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}`),
  
  create: (data: CatalogoCreate) => 
    apiRequest<CatalogoResponse>('/catalogo/', 'POST', data),
  
  update: (partNumber: string, data: CatalogoUpdate) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}`, 'PUT', data),
  
  delete: (partNumber: string) => 
    apiRequest<void>(`/catalogo/${partNumber}`, 'DELETE'),
  
  // ✅ FIX 3: Aggiorna part_number con propagazione globale
  updatePartNumberWithPropagation: (partNumber: string, newPartNumber: string) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}/update-with-propagation`, 'PUT', { new_part_number: newPartNumber }),
};

// API Parti
export const partiApi = {
  getAll: (params?: { skip?: number; limit?: number; part_number?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.part_number) queryParams.append('part_number', params.part_number);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ParteResponse[]>(`/parti${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<ParteResponse>(`/parti/${id}`),
  
  create: (data: ParteCreate) => 
    apiRequest<ParteResponse>('/parti/', 'POST', data),
  
  update: (id: number, data: ParteUpdate) => 
    apiRequest<ParteResponse>(`/parti/${id}`, 'PUT', data),
  
  delete: (id: number) => 
    apiRequest<void>(`/parti/${id}`, 'DELETE'),
};

// API CicloCura (per selezionare nei dropdown)
export const cicloCuraApi = {
  getAll: async (): Promise<CicloCura[]> => {
    const response = await api.get<CicloCura[]>('/cicli-cura')
    return response.data
  },

  getById: async (id: number): Promise<CicloCura> => {
    const response = await api.get<CicloCura>(`/cicli-cura/${id}`)
    return response.data
  },

  create: async (data: CreateCicloCuraDto): Promise<CicloCura> => {
    const response = await api.post<CicloCura>('/cicli-cura', data)
    return response.data
  },

  update: async (id: number, data: UpdateCicloCuraDto): Promise<CicloCura> => {
    const response = await api.put<CicloCura>(`/cicli-cura/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/cicli-cura/${id}`)
  },
}

export interface CicloCura {
  id: number
  nome: string
  temperatura_stasi1: number
  pressione_stasi1: number
  durata_stasi1: number
  attiva_stasi2: boolean
  temperatura_stasi2?: number
  pressione_stasi2?: number
  durata_stasi2?: number
  created_at: string
  updated_at: string
}

export interface CreateCicloCuraDto {
  nome: string
  temperatura_stasi1: number
  pressione_stasi1: number
  durata_stasi1: number
  attiva_stasi2: boolean
  temperatura_stasi2?: number
  pressione_stasi2?: number
  durata_stasi2?: number
}

export interface UpdateCicloCuraDto extends Partial<CreateCicloCuraDto> {}

export interface Autoclave {
  id: number
  nome: string
  codice: string
  lunghezza: number
  larghezza_piano: number
  num_linee_vuoto: number
  stato: 'DISPONIBILE' | 'IN_USO' | 'GUASTO' | 'MANUTENZIONE' | 'SPENTA'
  temperatura_max: number
  pressione_max: number
  // ✅ NUOVO: Carico massimo per nesting su due piani
  max_load_kg?: number
  produttore?: string
  anno_produzione?: number
  note?: string
  created_at: string
  updated_at: string
  // ✅ NUOVO: Campo calcolato per l'area del piano
  area_piano?: number
}

export interface CreateAutoclaveDto {
  nome: string
  codice: string
  lunghezza: number
  larghezza_piano: number
  num_linee_vuoto: number
  stato: 'DISPONIBILE' | 'IN_USO' | 'GUASTO' | 'MANUTENZIONE' | 'SPENTA'
  temperatura_max: number
  pressione_max: number
  // ✅ NUOVO: Carico massimo per nesting su due piani
  max_load_kg?: number
  produttore?: string
  anno_produzione?: number
  note?: string
}

export interface UpdateAutoclaveDto extends Partial<CreateAutoclaveDto> {}

export const autoclaveApi = {
  getAll: async (): Promise<Autoclave[]> => {
    const response = await api.get<Autoclave[]>('/autoclavi')
    return response.data
  },

  getAvailable: async (): Promise<Autoclave[]> => {
    const response = await api.get<Autoclave[]>('/autoclavi?stato=DISPONIBILE')
    return response.data
  },

  getById: async (id: number): Promise<Autoclave> => {
    const response = await api.get<Autoclave>(`/autoclavi/${id}/`)
    return response.data
  },

  create: async (data: CreateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.post<Autoclave>('/autoclavi', data)
    return response.data
  },

  update: async (id: number, data: UpdateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.put<Autoclave>(`/autoclavi/${id}/`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/autoclavi/${id}/`)
  },
}

// Tipi per ODL
export interface ODLBase {
  parte_id: number;
  tool_id: number;
  priorita: number;
  status: "Preparazione" | "Laminazione" | "In Coda" | "Attesa Cura" | "Cura" | "Finito";
  note?: string;
  motivo_blocco?: string;
}

export interface ODLCreate extends ODLBase {}

export interface ODLUpdate extends Partial<ODLBase> {}

export interface ParteInODLResponse {
  id: number;
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
}

export interface ToolInODLResponse {
  id: number;
  part_number_tool: string;
  descrizione?: string;
}

export interface ODLResponse extends ODLBase {
  id: number;
  parte: ParteInODLResponse;
  tool: ToolInODLResponse;
  created_at: string;
  updated_at: string;
}

// API ODL
export const odlApi = {
  getAll: (params?: { 
    status?: string; 
    parte_id?: number; 
    tool_id?: number; 
    priorita?: number;
    limit?: number;
    offset?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.parte_id) queryParams.append('parte_id', params.parte_id.toString());
    if (params?.tool_id) queryParams.append('tool_id', params.tool_id.toString());
    if (params?.priorita) queryParams.append('priorita', params.priorita.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ODLResponse[]>(`/odl${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<ODLResponse>(`/odl/${id}`),
  
  create: (data: ODLCreate) => 
    apiRequest<ODLResponse>('/odl/', 'POST', data),
  
  update: (id: number, data: ODLUpdate) => 
    apiRequest<ODLResponse>(`/odl/${id}`, 'PUT', data),
  
  delete: (id: number, confirm?: boolean) => {
    const queryParams = new URLSearchParams();
    if (confirm) queryParams.append('confirm', 'true');
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<void>(`/odl/${id}${query}`, 'DELETE');
  },

  updateStatus: (id: number, newStatus: string) => 
    apiRequest<ODLResponse>(`/odl/${id}/status`, 'PATCH', { new_status: newStatus }),

  // Funzioni specifiche per stati
  getByStatus: (status: string) => 
    apiRequest<ODLResponse[]>(`/odl/status/${status}`),

  // Funzioni per il monitoraggio
  getInProgress: () => 
    apiRequest<ODLResponse[]>('/odl/in-progress'),

  getCompleted: (params?: { start_date?: string; end_date?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ODLResponse[]>(`/odl/completed${query}`);
  },

  // Funzioni per statistiche
  getStats: () => 
    apiRequest<{
      totali: number;
      per_stato: Record<string, number>;
      completati_oggi: number;
      in_ritardo: number;
    }>('/odl/stats'),

  // Funzioni per la ricerca
  search: (query: string) => 
    apiRequest<ODLResponse[]>(`/odl/search?q=${encodeURIComponent(query)}`),

  // Funzioni per priorità
  updatePriority: (id: number, priorita: number) => 
    apiRequest<ODLResponse>(`/odl/${id}/priority`, 'PATCH', { priorita }),

  // Funzioni per note e blocchi
  addNote: (id: number, note: string) => 
    apiRequest<ODLResponse>(`/odl/${id}/note`, 'PATCH', { note }),

  block: (id: number, motivo: string) => 
    apiRequest<ODLResponse>(`/odl/${id}/block`, 'PATCH', { motivo_blocco: motivo }),

  unblock: (id: number) => 
    apiRequest<ODLResponse>(`/odl/${id}/unblock`, 'PATCH'),

  // Funzioni per il batch processing
  batchUpdateStatus: (ids: number[], newStatus: string) => 
    apiRequest<ODLResponse[]>('/odl/batch/status', 'PATCH', { 
      odl_ids: ids, 
      new_status: newStatus 
    }),

  batchDelete: (ids: number[]) => 
    apiRequest<void>('/odl/batch/delete', 'DELETE', { odl_ids: ids }),

  // Funzioni per le previsioni
  getPrevisioni: (partNumber: string) => {
    const previsioni = {
      laminazione: { media_minuti: 120, numero_osservazioni: 15 },
      attesa_cura: { media_minuti: 30, numero_osservazioni: 12 },
      cura: { media_minuti: 480, numero_osservazioni: 20 }
    };
    
    return {
      part_number: partNumber,
      previsioni,
      totale_odl: previsioni.cura.numero_osservazioni || 0
    };
  },

  // ✅ CORREZIONE: Funzione per recuperare dati di progresso temporali reali
  getProgress: (id: number) => 
    apiRequest<{
      id: number;
      status: string;
      created_at: string;
      updated_at: string;
      timestamps: Array<{
        stato: string;
        inizio: string;
        fine?: string | null;
        durata_minuti?: number;
      }>;
      tempo_totale_stimato?: number;
      has_timeline_data: boolean;
    }>(`/odl-monitoring/monitoring/${id}/progress`),
};

// Tipi base per TempoFase
export interface TempoFaseBase {
  odl_id: number;
  fase: "laminazione" | "attesa_cura" | "cura";
  inizio_fase: string;
  fine_fase?: string | null;
  durata_minuti?: number | null;
  note?: string | null;
}

export interface TempoFaseCreate extends TempoFaseBase {}

export interface TempoFaseUpdate extends Partial<TempoFaseBase> {}

export interface TempoFaseResponse extends TempoFaseBase {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface PrevisioneTempo {
  fase: "laminazione" | "attesa_cura" | "cura";
  media_minuti: number;
  numero_osservazioni: number;
}

// API Tempo Fasi
export const tempoFasiApi = {
  getAll: (params?: { odl_id?: number; fase?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.odl_id) queryParams.append('odl_id', params.odl_id.toString());
    if (params?.fase) queryParams.append('fase', params.fase);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<TempoFaseResponse[]>(`/tempo-fasi${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<TempoFaseResponse>(`/tempo-fasi/${id}`),
  
  create: (data: TempoFaseCreate) => 
    apiRequest<TempoFaseResponse>('/tempo-fasi/', 'POST', data),
  
  update: (id: number, data: TempoFaseUpdate) => 
    apiRequest<TempoFaseResponse>(`/tempo-fasi/${id}`, 'PUT', data),
  
  delete: (id: number) => 
    apiRequest<void>(`/tempo-fasi/${id}`, 'DELETE'),
    
  getPrevisione: (fase: string, partNumber?: string) => {
    const queryParams = new URLSearchParams();
    if (partNumber) queryParams.append('part_number', partNumber);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<PrevisioneTempo>(`/tempo-fasi/previsioni/${fase}${query}`);
  },

  // Nuova funzione per recuperare statistiche per part number
  getStatisticheByPartNumber: async (partNumber: string, giorni?: number) => {
    const queryParams = new URLSearchParams();
    if (giorni) queryParams.append('giorni', giorni.toString());
    
    // Dati fittizi per ogni fase
    const previsioni: Record<string, PrevisioneTempo> = {};
    
    // Recupera statistiche per ogni fase
    for (const fase of ['laminazione', 'attesa_cura', 'cura']) {
      try {
        const result = await apiRequest<PrevisioneTempo>(
          `/tempo-fasi/previsioni/${fase}?part_number=${partNumber}${queryParams.toString() ? `&${queryParams.toString()}` : ''}`
        );
        previsioni[fase] = result;
      } catch (error) {
        console.error(`Errore nel recupero delle statistiche per ${fase}:`, error);
        // Inserisci un dato vuoto in caso di errore
        previsioni[fase] = {
          fase: fase as any,
          media_minuti: 0,
          numero_osservazioni: 0
        };
      }
    }
    
    return {
      part_number: partNumber,
      previsioni,
      totale_odl: previsioni.cura.numero_osservazioni || 0
    };
  }
};

import {
  ScheduleEntry,
  ScheduleEntryCreateData,
  ScheduleEntryUpdateData,
  AutoScheduleResponseData,
  RecurringScheduleCreateData,
  ScheduleOperatorActionData,
  TempoProduzione,
  TempoProduzioneData,
  ProductionTimeEstimate
} from './types/schedule';

// API Schedule
export const scheduleApi = {
  getAll: (params?: { 
    include_done?: boolean; 
    start_date?: string; 
    end_date?: string; 
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.include_done !== undefined) queryParams.append('include_done', params.include_done.toString());
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ScheduleEntry[]>(`/schedules${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}`),
  
  create: (data: ScheduleEntryCreateData) => 
    apiRequest<ScheduleEntry>('/schedules/', 'POST', data),
  
  createRecurring: (data: RecurringScheduleCreateData) => 
    apiRequest<ScheduleEntry[]>('/schedules/recurring', 'POST', data),
  
  update: (id: number, data: ScheduleEntryUpdateData) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}`, 'PUT', data),
  
  executeAction: (id: number, action: ScheduleOperatorActionData) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}/action`, 'POST', action),
  
  delete: (id: number) => 
    apiRequest<void>(`/schedules/${id}`, 'DELETE'),
    
  autoGenerate: (date: string) => 
    apiRequest<AutoScheduleResponseData>(`/schedules/auto-generate?date=${date}`),
  
  // API per i tempi di produzione
  createProductionTime: (data: TempoProduzioneData) => 
    apiRequest<TempoProduzione>('/schedules/production-times', 'POST', data),
  
  getProductionTimes: () => 
    apiRequest<TempoProduzione[]>('/schedules/production-times'),
  
  estimateProductionTime: (params: {
    part_number?: string;
    categoria?: string;
    sotto_categoria?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params.part_number) queryParams.append('part_number', params.part_number);
    if (params.categoria) queryParams.append('categoria', params.categoria);
    if (params.sotto_categoria) queryParams.append('sotto_categoria', params.sotto_categoria);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ProductionTimeEstimate>(`/schedules/production-times/estimate${query}`);
  },
};

// Tipi per Reports
export interface ReportFileInfo {
  id: number;
  filename: string;
  file_path: string;
  report_type: ReportTypeEnum;
  generated_for_user_id?: number;
  period_start?: string;
  period_end?: string;
  include_sections?: string;
  file_size_bytes?: number;
  created_at: string;
  updated_at: string;
}

export interface ReportListResponse {
  reports: ReportFileInfo[];
}

export interface ReportGenerateResponse {
  message: string;
  file_path: string;
  file_name: string;
  report_id: number;
}

export interface ReportGenerateRequest {
  report_type: ReportTypeEnum;
  range_type?: ReportRangeType;
  start_date?: string;
  end_date?: string;
  include_sections?: ReportIncludeSection[];
  odl_filter?: string;
  user_id?: number;
  download?: boolean;
}

export type ReportRangeType = 'giorno' | 'settimana' | 'mese';
export type ReportTypeEnum = 'produzione' | 'qualita' | 'tempi' | 'completo';
export type ReportIncludeSection = 'odl' | 'tempi' | 'header';

// API Reports
export const reportsApi = {
  generate: async (request: ReportGenerateRequest): Promise<ReportGenerateResponse> => {
    return apiRequest<ReportGenerateResponse>('/reports/generate', 'POST', request);
  },
  
  list: (params?: {
    report_type?: ReportTypeEnum;
    start_date?: string;
    end_date?: string;
    odl_filter?: string;
    user_id?: number;
    limit?: number;
    offset?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.report_type) queryParams.append('report_type', params.report_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.odl_filter) queryParams.append('odl_filter', params.odl_filter);
    if (params?.user_id) queryParams.append('user_id', params.user_id.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ReportListResponse>(`/reports/${query}`);
  },
  
  downloadById: async (reportId: number): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },
  
  download: async (filename: string): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/reports/download/${filename}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },

  // ✅ NUOVO: API per export di report in diversi formati
  exportCSV: async (params?: {
    start_date?: string;
    end_date?: string;
    nesting_ids?: number[];
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.nesting_ids) {
      params.nesting_ids.forEach(id => queryParams.append('nesting_ids', id.toString()));
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/nesting/reports/export.csv${query}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },

  exportExcel: async (params?: {
    start_date?: string;
    end_date?: string;
    nesting_ids?: number[];
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.nesting_ids) {
      params.nesting_ids.forEach(id => queryParams.append('nesting_ids', id.toString()));
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/nesting/reports/export.xlsx${query}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },

  exportPDF: async (params?: {
    start_date?: string;
    end_date?: string;
    nesting_ids?: number[];
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.nesting_ids) {
      params.nesting_ids.forEach(id => queryParams.append('nesting_ids', id.toString()));
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/nesting/reports/export.pdf${query}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },
};

// 🆕 Funzione di utilità per aggiornamento stato ODL con gestione errori migliorata
export async function updateOdlStatus(id: number, newStatus: string): Promise<ODLResponse> {
  try {
    // Usa apiRequest invece di fetch diretto per gestione errori coerente
    const data = await apiRequest<ODLResponse>(`/odl/${id}/status`, 'PATCH', { new_status: newStatus });
    
    return data;
  } catch (error) {
    console.error(`❌ Errore aggiornamento stato ODL ${id}:`, error);
    throw error;
  }
}

// 🆕 Tipi per Nesting
export interface NestingBase {
  note?: string;
}

export interface NestingCreate extends NestingBase {}

export interface NestingResponse extends NestingBase {
  id: string;
  created_at: string;
  stato: string;
  // ✅ NUOVI CAMPI: Aggiungo tutti i campi disponibili dal backend
  autoclave_id?: number;
  autoclave_nome?: string;
  ciclo_cura?: string;
  odl_inclusi?: number;
  odl_esclusi?: number;
  efficienza?: number;
  area_utilizzata?: number;
  area_totale?: number;
  peso_totale?: number;
  valvole_utilizzate?: number;
  valvole_totali?: number;
  motivi_esclusione?: string[];
  statistiche?: {
    area_utilizzata: number;
    area_totale: number;
    efficienza: number;
    peso_totale: number;
    valvole_utilizzate: number;
    valvole_totali: number;
  };
}

// 🆕 Tipi per Nesting Automatico
export interface AutomaticNestingRequest {
  force_regenerate?: boolean;
  max_autoclaves?: number;
  priority_threshold?: number;
}

export interface ODLNestingInfo {
  id: number;
  parte_codice?: string;
  tool_nome?: string;
  priorita: number;
  dimensioni: {
    larghezza: number;
    lunghezza: number;
    peso: number;
  };
  ciclo_cura?: string;
  status: string;
}

export interface AutoclaveNestingInfo {
  id: number;
  nome: string;
  area_piano: number;
  max_load_kg?: number;
  stato: string;
}

export interface NestingResultSummary {
  id: number;
  autoclave_id: number;
  autoclave_nome: string;
  ciclo_cura: string;
  odl_inclusi: number;
  odl_esclusi: number;
  efficienza: number;
  area_utilizzata: number;
  peso_totale: number;
  stato: string;
}

export interface AutomaticNestingResponse {
  success: boolean;
  message: string;
  nesting_results: NestingResultSummary[];
  summary?: {
    total_nesting_created: number;
    total_odl_processed: number;
    total_odl_excluded: number;
    autoclavi_utilizzate: number;
  };
}

export interface NestingPreviewRequest {
  include_excluded?: boolean;
  group_by_cycle?: boolean;
}

export interface ODLGroupPreview {
  ciclo_cura: string;
  odl_list: ODLNestingInfo[];
  total_area: number;
  total_weight: number;
  compatible_autoclaves: AutoclaveNestingInfo[];
}

export interface NestingPreviewResponse {
  success: boolean;
  message: string;
  odl_groups: ODLGroupPreview[];
  available_autoclaves: AutoclaveNestingInfo[];
  total_odl_pending: number;
}

export interface NestingDetailResponse {
  id: number;
  autoclave: AutoclaveNestingInfo;
  odl_inclusi: ODLNestingInfo[];
  odl_esclusi: ODLNestingInfo[];
  motivi_esclusione: string[];
  statistiche: {
    area_utilizzata: number;
    area_totale: number;
    efficienza: number;
    peso_totale: number;
    valvole_utilizzate: number;
    valvole_totali: number;
  };
  stato: string;
  note?: string;
  created_at: string;
}

export interface NestingStatusUpdate {
  stato: string;
  note?: string;
  confermato_da_ruolo?: string;
}

// 🆕 Interfaccia per la conferma del nesting
export interface NestingConfirmRequest {
  confermato_da_ruolo?: string;
  note_conferma?: string;
}

// 🆕 Interfaccia per il caricamento del nesting
export interface NestingLoadRequest {
  caricato_da_ruolo?: string;
  note_caricamento?: string;
}

// ✅ Interfaccia per il risultato singolo di nesting nella lista
export interface NestingResult {
  id: number;
  stato: string;
  autoclave?: {
    id: number;
    nome: string;
    codice: string;
  };
  ciclo_cura?: string;
  odl_count?: number;
  area_utilizzata?: number;
  area_totale?: number;
  valvole_utilizzate?: number;
  valvole_totali?: number;
  efficienza?: number;
  peso_totale?: number;
  note?: string;
  created_at: string;
  updated_at?: string;
}

// 🆕 Interfaccia per la risposta della lista paginata di nesting
export interface NestingListResponse {
  success: boolean;
  message: string;
  nesting_list: NestingResult[];
  pagination?: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

// 🆕 Interfaccia per i parametri di ricerca della lista nesting
export interface NestingListParams {
  page?: number;
  per_page?: number;
  stato?: string;
  autoclave_id?: number;
  search?: string;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
}

// 🆕 API Nesting
export const nestingApi = {
  getAll: () => 
    apiRequest<NestingResponse[]>('/nesting/'),
  
  // 🆕 NUOVO: Ottiene lista paginata di nesting con filtri
  getList: (params?: NestingListParams) => {
    const queryParams = new URLSearchParams();
    
    if (params?.page !== undefined) {
      queryParams.append('page', params.page.toString());
    }
    if (params?.per_page !== undefined) {
      queryParams.append('per_page', params.per_page.toString());
    }
    if (params?.stato) {
      queryParams.append('stato', params.stato);
    }
    if (params?.autoclave_id !== undefined) {
      queryParams.append('autoclave_id', params.autoclave_id.toString());
    }
    if (params?.search) {
      queryParams.append('search', params.search);
    }
    if (params?.order_by) {
      queryParams.append('order_by', params.order_by);
    }
    if (params?.order_direction) {
      queryParams.append('order_direction', params.order_direction);
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<NestingListResponse>(`/nesting/list${query}`);
  },

  create: (data: NestingCreate) => 
    apiRequest<NestingResponse>('/nesting/', 'POST', data),
  
  generateAutomatic: (request?: AutomaticNestingRequest) => 
    apiRequest<AutomaticNestingResponse>('/nesting/automatic', 'POST', request || {}),
  
  getPreview: (request?: NestingPreviewRequest) => {
    const queryParams = new URLSearchParams();
    if (request?.include_excluded !== undefined) {
      queryParams.append('include_excluded', request.include_excluded.toString());
    }
    if (request?.group_by_cycle !== undefined) {
      queryParams.append('group_by_cycle', request.group_by_cycle.toString());
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<NestingPreviewResponse>(`/nesting/preview${query}`);
  },
  
  getDetails: (nestingId: number) => 
    apiRequest<NestingDetailResponse>(`/nesting/${nestingId}`),
  
  updateStatus: (nestingId: number, statusUpdate: NestingStatusUpdate) => 
    apiRequest<{success: boolean; message: string}>(`/nesting/${nestingId}/status`, 'PUT', statusUpdate),

  // 🆕 Conferma nesting - cambia stato a "in sospeso"
  confirm: (nestingId: number, confirmData?: NestingConfirmRequest) => 
    apiRequest<NestingDetailResponse>(`/nesting/${nestingId}/confirm`, 'POST', confirmData || {}),

  // 🆕 Carica nesting - cambia stato ODL a "Cura" e autoclave a "IN_USO"
  load: (nestingId: number, loadData?: NestingLoadRequest) => 
    apiRequest<NestingDetailResponse>(`/nesting/${nestingId}/load`, 'POST', loadData || {}),

  // 🆕 Ottiene nesting attivi (caricati)
  getActive: () => 
    apiRequest<NestingDetailResponse[]>('/nesting/active'),

  // ✅ NUOVO: Endpoint per la visualizzazione grafica
  getLayout: (
    nestingId: number, 
    options?: {
      padding_mm?: number;
      borda_mm?: number;
      rotazione_abilitata?: boolean;
    }
  ) => {
    const queryParams = new URLSearchParams();
    if (options?.padding_mm !== undefined) {
      queryParams.append('padding_mm', options.padding_mm.toString());
    }
    if (options?.borda_mm !== undefined) {
      queryParams.append('borda_mm', options.borda_mm.toString());
    }
    if (options?.rotazione_abilitata !== undefined) {
      queryParams.append('rotazione_abilitata', options.rotazione_abilitata.toString());
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<NestingLayoutResponse>(`/nesting/${nestingId}/layout${query}`);
  },

  getAllLayouts: (options?: {
    limit?: number;
    stato_filtro?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (options?.limit !== undefined) {
      queryParams.append('limit', options.limit.toString());
    }
    if (options?.stato_filtro !== undefined) {
      queryParams.append('stato_filtro', options.stato_filtro);
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<MultiNestingLayoutResponse>(`/nesting/layouts/all${query}`);
  },

  calculateOrientation: (request: OrientationCalculationRequest) => 
    apiRequest<OrientationCalculationResponse>('/nesting/calculate-orientation', 'POST', request),

  // ✅ NUOVO: Genera report PDF per un nesting specifico
  generateReport: (nestingId: number, forceRegenerate?: boolean) => {
    const queryParams = new URLSearchParams();
    if (forceRegenerate !== undefined) {
      queryParams.append('force_regenerate', forceRegenerate.toString());
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<{
      success: boolean;
      message: string;
      report_id: number;
      filename: string;
      file_path: string;
      file_size_bytes?: number;
      created_at: string;
      download_url: string;
    }>(`/nesting/${nestingId}/generate-report${query}`, 'POST');
  },

  // ✅ NUOVO: Scarica report PDF di un nesting specifico
  downloadReport: async (nestingId: number): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/reports/nesting/${nestingId}/download`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      throw error;
    }
    return response.blob();
  },

  // ✅ NUOVO: Ottiene informazioni su un report esistente di un nesting
  getReport: (nestingId: number) => {
    return apiRequest<{
      exists: boolean;
      report_id?: number;
      filename?: string;
      file_path?: string;
      file_size_bytes?: number;
      created_at?: string;
      download_url?: string;
    }>(`/nesting/${nestingId}/report`);
  },

  // 🆕 NUOVO: Rigenera un nesting esistente
  regenerate: (nestingId: number, forceRegenerate?: boolean) => {
    const queryParams = new URLSearchParams();
    if (forceRegenerate !== undefined) {
      queryParams.append('force_regenerate', forceRegenerate.toString());
    }
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<{
      success: boolean;
      message: string;
      nesting_id: number;
      stato: string;
    }>(`/nesting/${nestingId}/regenerate${query}`, 'POST');
  },

  // 🆕 NUOVO: Elimina un nesting
  delete: (nestingId: number) => 
    apiRequest<{
      success: boolean;
      message: string;
    }>(`/nesting/${nestingId}`, 'DELETE'),
};

// ✅ NUOVO: Interfacce per la visualizzazione grafica del nesting
export interface ToolPosition {
  odl_id: number;
  x: number;
  y: number;
  width: number;
  height: number;
  rotated: boolean;
  piano: number;
}

export interface ToolDetailInfo {
  id: number;
  part_number_tool: string;
  descrizione?: string;
  lunghezza_piano: number;
  larghezza_piano: number;
  peso?: number;
  materiale?: string;
  orientamento_preferito?: string;
}

export interface ParteDetailInfo {
  id: number;
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
  area_cm2?: number;
}

export interface ODLLayoutInfo {
  id: number;
  priorita: number;
  parte: ParteDetailInfo;
  tool: ToolDetailInfo;
}

export interface AutoclaveLayoutInfo {
  id: number;
  nome: string;
  codice: string;
  lunghezza: number;
  larghezza_piano: number;
  temperatura_max: number;
  num_linee_vuoto: number;
}

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
  nesting_list: NestingLayoutData[];
  statistiche_globali: Record<string, any>;
}

export interface OrientationCalculationRequest {
  tool_length: number;
  tool_width: number;
  autoclave_length: number;
  autoclave_width: number;
}

export interface OrientationCalculationResponse {
  should_rotate: boolean;
  normal_efficiency: number;
  rotated_efficiency: number;
  improvement_percentage: number;
  recommended_orientation: string;
}

export interface NestingLayoutResponse {
  success: boolean;
  message: string;
  layout_data?: NestingLayoutData;
}

export interface MultiNestingLayoutResponse {
  success: boolean;
  message: string;
  layout_data?: MultiNestingLayoutData;
}

// ✅ NUOVE API PER MONITORAGGIO ODL
export interface ODLMonitoringStats {
  totale_odl: number;
  per_stato: Record<string, number>;
  in_ritardo: number;
  completati_oggi: number;
  media_tempo_completamento?: number;
}

export interface ODLMonitoringSummary {
  id: number;
  parte_nome: string;
  tool_nome: string;
  status: string;
  priorita: number;
  created_at: string;
  updated_at: string;
  nesting_stato?: string;
  autoclave_nome?: string;
  ultimo_evento?: string;
  ultimo_evento_timestamp?: string;
  tempo_in_stato_corrente?: number;
}

export interface ODLMonitoringDetail {
  id: number;
  status: string;
  priorita: number;
  parte_nome: string;
  tool_nome: string;
  created_at: string;
  updated_at: string;
  nesting_id?: number;
  autoclave_nome?: string;
  ciclo_cura_nome?: string;
  tempo_in_stato_corrente?: number;
  tempo_totale_produzione?: number;
  logs: Array<{
    id: number;
    evento: string;
    stato_precedente?: string;
    stato_nuovo: string;
    descrizione?: string;
    timestamp: string;
    nesting_stato?: string;
    autoclave_nome?: string;
  }>;
}

export interface ODLProgressData {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
  timestamps: Array<{
    stato: string;
    inizio: string;
    fine?: string;
    durata_minuti: number;
  }>;
  tempo_totale_stimato: number;
  has_timeline_data: boolean;
  data_source: string;
}

// API per il monitoraggio ODL
export const odlMonitoringApi = {
  // Ottieni statistiche generali del monitoraggio
  getStats: async (): Promise<ODLMonitoringStats> => {
    return apiRequest<ODLMonitoringStats>('/odl-monitoring/monitoring/stats');
  },

  // Ottieni lista riassuntiva del monitoraggio ODL
  getList: async (params?: {
    skip?: number;
    limit?: number;
    status_filter?: string;
    priorita_min?: number;
    solo_attivi?: boolean;
  }): Promise<ODLMonitoringSummary[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params?.priorita_min) queryParams.append('priorita_min', params.priorita_min.toString());
    if (params?.solo_attivi !== undefined) queryParams.append('solo_attivi', params.solo_attivi.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ODLMonitoringSummary[]>(`/odl-monitoring/monitoring${query}`);
  },

  // Ottieni monitoraggio completo di un ODL specifico
  getDetail: async (odlId: number): Promise<ODLMonitoringDetail> => {
    return apiRequest<ODLMonitoringDetail>(`/odl-monitoring/monitoring/${odlId}`);
  },

  // Ottieni timeline di un ODL specifico
  getTimeline: async (odlId: number): Promise<Array<{
    id: number;
    evento: string;
    stato_precedente?: string;
    stato_nuovo: string;
    descrizione?: string;
    timestamp: string;
    nesting_stato?: string;
    autoclave_nome?: string;
  }>> => {
    return apiRequest<Array<{
      id: number;
      evento: string;
      stato_precedente?: string;
      stato_nuovo: string;
      descrizione?: string;
      timestamp: string;
      nesting_stato?: string;
      autoclave_nome?: string;
    }>>(`/odl-monitoring/monitoring/${odlId}/timeline`);
  },

  // Ottieni dati di progresso per la barra temporale
  getProgress: async (odlId: number): Promise<ODLProgressData> => {
    return apiRequest<ODLProgressData>(`/odl-monitoring/monitoring/${odlId}/progress`);
  },

  // Genera log mancanti per ODL esistenti
  generateMissingLogs: async (): Promise<{ message: string; logs_creati: number }> => {
    return apiRequest<{ message: string; logs_creati: number }>('/odl-monitoring/monitoring/generate-missing-logs', 'POST');
  },

  // Inizializza il tracking degli stati per ODL esistenti
  initializeStateTracking: async (): Promise<{ message: string; logs_creati: number; odl_processati: number[] }> => {
    return apiRequest<{ message: string; logs_creati: number; odl_processati: number[] }>('/odl-monitoring/monitoring/initialize-state-tracking', 'POST');
  }
};

// Funzioni di compatibilità per l'obiettivo
export const getDashboardKPI = async (): Promise<ODLMonitoringStats> => {
  return odlMonitoringApi.getStats();
};

export const getStatisticheByPartNumber = async (partNumber: string, giorni: number): Promise<{
  part_number: string;
  previsioni: Record<string, {
    fase: string;
    media_minuti: number;
    numero_osservazioni: number;
  }>;
  totale_odl: number;
}> => {
  // Questa funzione usa l'API esistente dei tempi fasi
  return tempoFasiApi.getStatisticheByPartNumber(partNumber, giorni);
}; 