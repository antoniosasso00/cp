// API client per interagire con il backend

import axios from 'axios'
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

console.log('🔗 API Base URL configurata:', API_BASE_URL); // Log per debug

// Configurazione axios con interceptors per logging e gestione errori
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 secondi di timeout
})

// Interceptor per le richieste
api.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data || '');
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
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
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
  console.log(`🌐 API Request: ${method} ${fullUrl}`, data ? { data } : ''); // Log per debug

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
      console.log('✅ API Success (No Content):', method, fullUrl);
      return {} as T;
    }

    const result = await response.json();
    console.log('✅ API Success:', method, fullUrl, result);
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
  getAll: async (params?: { parte_id?: number; tool_id?: number; status?: string }): Promise<ODLResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.parte_id) queryParams.append('parte_id', params.parte_id.toString());
    if (params?.tool_id) queryParams.append('tool_id', params.tool_id.toString());
    if (params?.status) queryParams.append('status', params.status);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await api.get<ODLResponse[]>(`/odl/${query}`);
    return response.data;
  },
  
  getOne: async (id: number): Promise<ODLResponse> => {
    const response = await api.get<ODLResponse>(`/odl/${id}`);
    return response.data;
  },
  
  create: async (data: ODLCreate): Promise<ODLResponse> => {
    const response = await api.post<ODLResponse>('/odl', data);
    return response.data;
  },
  
  update: async (id: number, data: ODLUpdate): Promise<ODLResponse> => {
    const response = await api.put<ODLResponse>(`/odl/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number, confirm: boolean = false): Promise<void> => {
    const queryParam = confirm ? '?confirm=true' : '';
    await api.delete(`/odl/${id}${queryParam}`);
  },

  checkQueue: async (): Promise<{
    message: string;
    updated_odls: Array<{
      odl_id: number;
      old_status: string;
      new_status: string;
      motivo_blocco?: string;
    }>;
  }> => {
    const response = await api.post<{
      message: string;
      updated_odls: Array<{
        odl_id: number;
        old_status: string;
        new_status: string;
        motivo_blocco?: string;
      }>;
    }>('/odl/check-queue');
    return response.data;
  },

  checkSingleStatus: async (id: number): Promise<{
    message: string;
    update_info?: {
      odl_id: number;
      old_status: string;
      new_status: string;
      motivo_blocco?: string;
    };
  }> => {
    const response = await api.post<{
      message: string;
      update_info?: {
        odl_id: number;
        old_status: string;
        new_status: string;
        motivo_blocco?: string;
      };
    }>(`/odl/${id}/check-status`);
    return response.data;
  },

  // Funzioni specifiche per ruoli
  updateStatusCleanRoom: async (id: number, newStatus: "Laminazione" | "Attesa Cura"): Promise<ODLResponse> => {
    const response = await api.patch<ODLResponse>(`/odl/${id}/clean-room-status?new_status=${newStatus}`);
    return response.data;
  },

  updateStatusCuring: async (id: number, newStatus: "Cura" | "Finito"): Promise<ODLResponse> => {
    const response = await api.patch<ODLResponse>(`/odl/${id}/curing-status?new_status=${newStatus}`);
    return response.data;
  },

  // Funzione per admin (qualsiasi transizione)
  updateStatusAdmin: async (id: number, newStatus: "Preparazione" | "Laminazione" | "In Coda" | "Attesa Cura" | "Cura" | "Finito"): Promise<ODLResponse> => {
    const response = await api.patch<ODLResponse>(`/odl/${id}/admin-status?new_status=${newStatus}`);
    return response.data;
  },

  // Funzione generica (accetta JSON nel body) - Supporta conversione automatica formato stato
  updateStatus: async (id: number, status: string): Promise<ODLResponse> => {
    try {
      console.log(`🔄 Aggiornamento stato ODL ${id}: ${status}`);
      const response = await api.patch<ODLResponse>(`/odl/${id}/status`, {
        new_status: status
      });
      console.log(`✅ Stato ODL ${id} aggiornato con successo a: ${response.data.status}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore aggiornamento stato ODL ${id}:`, error);
      throw error;
    }
  },

  // API per il monitoraggio e la timeline
  getProgress: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}/progress`);
    return response.data;
  },

  getTimeline: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}/timeline`);
    return response.data;
  },

  getMonitoringDetail: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}`);
    return response.data;
  },
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
    console.log('🔗 Report Generate Request:', request);
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
    console.log(`🔗 Report Download Request (ID): ${reportId}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      console.error('❌ Report Download Error:', error);
      throw error;
    }
    console.log('✅ Report Download Success');
    return response.blob();
  },
  
  download: async (filename: string): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/reports/download/${filename}`);
    console.log(`🔗 Report Download Request: ${filename}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = {
        status: response.status,
        message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
        data: errorData,
      };
      console.error('❌ Report Download Error:', error);
      throw error;
    }
    console.log('✅ Report Download Success');
    return response.blob();
  },

  // 🆕 Funzione di utilità per aggiornamento stato ODL con gestione errori migliorata
  updateOdlStatus: async (id: number, newStatus: string): Promise<ODLResponse> => {
    try {
      const response = await fetch(`${API_BASE_URL}/odl/${id}/status`, {
        method: "PATCH",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ new_status: newStatus }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `Errore HTTP ${response.status}`;
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      console.log(`✅ Stato ODL ${id} aggiornato: ${data.status}`);
      return data;
    } catch (error) {
      console.error(`❌ Errore aggiornamento stato ODL ${id}:`, error);
      throw error;
    }
  },
};

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