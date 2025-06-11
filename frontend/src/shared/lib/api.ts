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

// ✅ PULITO: Rimosso /v1/ dal base URL, aggiunto /api per il fallback locale
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

console.log('🔗 API Base URL configurata:', API_BASE_URL); // Log per debug

// ✅ Funzioni helper per gestione errori
const isRetryableError = (error: any): boolean => {
  if (!error) return false;
  
  // Errori di rete
  if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') return true;
  if (error.name === 'AbortError') return true; // Timeout
  
  // Errori HTTP temporanei
  const status = error.response?.status;
  if (status === 408 || status === 429 || (status >= 500 && status <= 599)) return true;
  
  // Errori specifici
  if (error.message?.includes('timeout')) return true;
  if (error.message?.includes('connessione')) return true;
  if (error.message?.includes('network')) return true;
  
  return false;
};

const getErrorMessage = (error: any): string => {
  if (!error) return 'Errore sconosciuto';
  
  // Errori di rete
  if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
    return 'Errore di connessione al server. Verifica che il backend sia attivo.';
  }
  
  if (error.name === 'AbortError') {
    return 'Richiesta interrotta per timeout. Il server potrebbe essere sovraccarico.';
  }
  
  // Errori HTTP con messaggi specifici
  if (error.response?.data?.detail) {
    return `Errore server: ${error.response.data.detail}`;
  }
  
  if (error.response?.status) {
    const status = error.response.status;
    switch (status) {
      case 404:
        return 'Risorsa non trovata. Verifica che l\'endpoint esista.';
      case 422:
        return 'Dati non validi inviati al server.';
      case 500:
        return 'Errore interno del server. Riprova più tardi.';
      case 503:
        return 'Servizio temporaneamente non disponibile.';
      default:
        return `Errore HTTP ${status}: ${error.response.statusText || 'Errore del server'}`;
    }
  }
  
  // Errori generici
  if (error.message) {
    return error.message;
  }
  
  return 'Errore sconosciuto durante la comunicazione con il server';
};

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

// ✅ RINOMINATO: API Tools con nomi più descrittivi
export const toolsApi = {
  // ✅ getAll → fetchTools
  fetchTools: async (): Promise<Tool[]> => {
    const response = await api.get<Tool[]>('/tools')
    return response.data
  },

  // ✅ getAllWithStatus → fetchToolsWithStatus  
  fetchToolsWithStatus: async (): Promise<ToolWithStatus[]> => {
    const response = await api.get<ToolWithStatus[]>('/tools/with-status')
    return response.data
  },

  // ✅ getById → fetchToolById
  fetchToolById: async (id: number): Promise<Tool> => {
    const response = await api.get<Tool>(`/tools/${id}`)
    return response.data
  },

  // ✅ create → createTool (già corretto)
  createTool: async (data: CreateToolDto): Promise<Tool> => {
    const response = await api.post<Tool>('/tools', data)
    return response.data
  },

  // ✅ update → updateTool
  updateTool: async (id: number, data: UpdateToolDto): Promise<Tool> => {
    const response = await api.put<Tool>(`/tools/${id}`, data)
    return response.data
  },

  // ✅ delete → deleteTool
  deleteTool: async (id: number): Promise<void> => {
    await api.delete(`/tools/${id}`)
  },

  // ✅ updateStatusFromOdl → updateToolStatusFromODL
  updateToolStatusFromODL: async (): Promise<{
    message: string;
    updated_tools: Array<{
      tool_id: number;
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

// ✅ RINOMINATO: API Catalogo con nomi più descrittivi
export const catalogApi = {
  // ✅ getAll → fetchCatalogItems
  fetchCatalogItems: (params?: { skip?: number; limit?: number; categoria?: string; sotto_categoria?: string; attivo?: boolean; search?: string }) => {
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
  
  // ✅ getOne → fetchCatalogItem
  fetchCatalogItem: (partNumber: string) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}`),
  
  // ✅ create → createCatalogItem
  createCatalogItem: (data: CatalogoCreate) => 
    apiRequest<CatalogoResponse>('/catalogo/', 'POST', data),
  
  // ✅ update → updateCatalogItem
  updateCatalogItem: (partNumber: string, data: CatalogoUpdate) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}`, 'PUT', data),
  
  // ✅ delete → deleteCatalogItem
  deleteCatalogItem: (partNumber: string) => 
    apiRequest<void>(`/catalogo/${partNumber}`, 'DELETE'),
  
  // ✅ updatePartNumberWithPropagation → updatePartNumberWithPropagation (già descrittivo)
  updatePartNumberWithPropagation: (partNumber: string, newPartNumber: string) => 
    apiRequest<CatalogoResponse>(`/catalogo/${partNumber}/update-with-propagation`, 'PUT', { new_part_number: newPartNumber }),
};

// ✅ RINOMINATO: API Parti con nomi più descrittivi
export const partsApi = {
  // ✅ getAll → fetchParts
  fetchParts: (params?: { skip?: number; limit?: number; part_number?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.part_number) queryParams.append('part_number', params.part_number);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ParteResponse[]>(`/parti${query}`);
  },
  
  // ✅ getOne → fetchPart
  fetchPart: (id: number) => 
    apiRequest<ParteResponse>(`/parti/${id}`),
  
  // ✅ create → createPart
  createPart: (data: ParteCreate) => 
    apiRequest<ParteResponse>('/parti/', 'POST', data),
  
  // ✅ update → updatePart
  updatePart: (id: number, data: ParteUpdate) => 
    apiRequest<ParteResponse>(`/parti/${id}`, 'PUT', data),
  
  // ✅ delete → deletePart
  deletePart: (id: number) => 
    apiRequest<void>(`/parti/${id}`, 'DELETE'),
};

// ✅ RINOMINATO: API CicloCura con nomi più descrittivi
export const curingCyclesApi = {
  // ✅ getAll → fetchCuringCycles
  fetchCuringCycles: async (): Promise<CicloCura[]> => {
    const response = await api.get<CicloCura[]>('/cicli-cura')
    return response.data
  },

  // ✅ getById → fetchCuringCycle
  fetchCuringCycle: async (id: number): Promise<CicloCura> => {
    const response = await api.get<CicloCura>(`/cicli-cura/${id}`)
    return response.data
  },

  // ✅ create → createCuringCycle
  createCuringCycle: async (data: CreateCicloCuraDto): Promise<CicloCura> => {
    const response = await api.post<CicloCura>('/cicli-cura', data)
    return response.data
  },

  // ✅ update → updateCuringCycle
  updateCuringCycle: async (id: number, data: UpdateCicloCuraDto): Promise<CicloCura> => {
    const response = await api.put<CicloCura>(`/cicli-cura/${id}`, data)
    return response.data
  },

  // ✅ delete → deleteCuringCycle
  deleteCuringCycle: async (id: number): Promise<void> => {
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

// ✅ RINOMINATO: API Autoclavi con nomi più descrittivi
export const autoclavesApi = {
  // ✅ getAll → fetchAutoclaves
  fetchAutoclaves: async (): Promise<Autoclave[]> => {
    const response = await api.get<Autoclave[]>('/autoclavi')
    return response.data
  },

  // ✅ getAvailable → fetchAvailableAutoclaves
  fetchAvailableAutoclaves: async (): Promise<Autoclave[]> => {
    const response = await api.get<Autoclave[]>('/autoclavi?stato=DISPONIBILE')
    return response.data
  },

  // ✅ getById → fetchAutoclave
  fetchAutoclave: async (id: number): Promise<Autoclave> => {
    const response = await api.get<Autoclave>(`/autoclavi/${id}`)
    return response.data
  },

  // ✅ create → createAutoclave
  createAutoclave: async (data: CreateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.post<Autoclave>('/autoclavi', data)
    return response.data
  },

  // ✅ update → updateAutoclave
  updateAutoclave: async (id: number, data: UpdateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.put<Autoclave>(`/autoclavi/${id}`, data)
    return response.data
  },

  // ✅ delete → deleteAutoclave
  deleteAutoclave: async (id: number): Promise<void> => {
    await api.delete(`/autoclavi/${id}`)
  },
}

// Tipi per ODL
export interface ODLBase {
  numero_odl: string;
  parte_id: number;
  tool_id: number;
  priorita: number;
  status: "Preparazione" | "Laminazione" | "In Coda" | "Attesa Cura" | "Cura" | "Finito";
  include_in_std: boolean;
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

// ✅ RINOMINATO: API ODL con nomi più descrittivi e gestione errori migliorata
export const odlApi = {
  // ✅ getAll → fetchODLs
  fetchODLs: async (params?: { parte_id?: number; tool_id?: number; status?: string; include_in_std?: boolean }, options?: { retries?: number; timeout?: number }): Promise<ODLResponse[]> => {
    const { retries = 3, timeout = 10000 } = options || {};
    
    const queryParams = new URLSearchParams();
    if (params?.parte_id) queryParams.append('parte_id', params.parte_id.toString());
    if (params?.tool_id) queryParams.append('tool_id', params.tool_id.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.include_in_std !== undefined) queryParams.append('include_in_std', params.include_in_std.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const endpoint = `/odl${query}`;
    
    console.log(`🔄 Richiesta ODL: ${endpoint}`);
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await api.get<ODLResponse[]>(endpoint, {
          timeout: timeout
        });
        
        console.log(`✅ ODL caricati con successo: ${response.data.length} elementi (tentativo ${attempt}/${retries})`);
        return response.data;
        
      } catch (error) {
        console.error(`❌ Errore tentativo ${attempt}/${retries}:`, {
          endpoint,
          error: error instanceof Error ? error.message : 'Errore sconosciuto',
          code: (error as any)?.code,
          status: (error as any)?.response?.status
        });

        // Se non è l'ultimo tentativo e l'errore è recuperabile, riprova
        if (attempt < retries && isRetryableError(error)) {
          const delayMs = Math.min(1000 * Math.pow(2, attempt - 1), 5000); // Exponential backoff, max 5s
          console.log(`🔄 Nuovo tentativo in ${delayMs}ms...`);
          await new Promise(resolve => setTimeout(resolve, delayMs));
          continue;
        }
        
        // Ultimo tentativo o errore non recuperabile
        const errorMessage = getErrorMessage(error);
        console.error(`🚫 Richiesta ODL fallita definitivamente: ${errorMessage}`);
        throw new Error(errorMessage);
      }
    }
    
    throw new Error('Impossibile caricare gli ODL dopo tutti i tentativi');
  },
  
  // ✅ getOne → fetchODL
  fetchODL: async (id: number): Promise<ODLResponse> => {
    try {
      console.log(`🔍 Richiesta ODL singolo: ${id}`);
      const response = await api.get<ODLResponse>(`/odl/${id}`);
      console.log(`✅ ODL ${id} caricato con successo`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore caricamento ODL ${id}:`, error);
      throw error;
    }
  },
  
  // ✅ create → createODL
  createODL: async (data: ODLCreate): Promise<ODLResponse> => {
    try {
      console.log('🆕 Creazione nuovo ODL:', data);
      const response = await api.post<ODLResponse>('/odl', data);
      console.log(`✅ ODL creato con successo: ID ${response.data.id}`);
      return response.data;
    } catch (error) {
      console.error('❌ Errore creazione ODL:', error);
      throw error;
    }
  },
  
  // ✅ update → updateODL
  updateODL: async (id: number, data: ODLUpdate): Promise<ODLResponse> => {
    try {
      console.log(`📝 Aggiornamento ODL ${id}:`, data);
      const response = await api.put<ODLResponse>(`/odl/${id}`, data);
      console.log(`✅ ODL ${id} aggiornato con successo`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore aggiornamento ODL ${id}:`, error);
      throw error;
    }
  },
  
  // ✅ delete → deleteODL
  deleteODL: async (id: number, confirm: boolean = false): Promise<void> => {
    try {
      console.log(`🗑️ Eliminazione ODL ${id} (confirm: ${confirm})`);
      const queryParam = confirm ? '?confirm=true' : '';
      await api.delete(`/odl/${id}${queryParam}`);
      console.log(`✅ ODL ${id} eliminato con successo`);
    } catch (error) {
      console.error(`❌ Errore eliminazione ODL ${id}:`, error);
      throw error;
    }
  },

  // ✅ deleteMultiple → deleteMultipleODL
  deleteMultipleODL: async (ids: number[], confirm: boolean = false): Promise<{
    message: string;
    deleted_count: number;
    deleted_ids: number[];
    total_requested: number;
    errors: string[];
  }> => {
    try {
      console.log(`🗑️ Eliminazione multipla ODL ${ids.join(', ')} (confirm: ${confirm})`);
      const queryParam = confirm ? '?confirm=true' : '';
      
      // Usa axios con il body come array diretto per la richiesta DELETE
      const response = await api.request({
        method: 'DELETE',
        url: `/odl/bulk${queryParam}`,
        data: ids,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log(`✅ Eliminazione multipla completata: ${response.data.deleted_count}/${response.data.total_requested}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore eliminazione multipla ODL:`, error);
      throw error;
    }
  },

  // ✅ checkQueue → checkODLQueue
  checkODLQueue: async (): Promise<{
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

  // ✅ checkSingleStatus → checkODLStatus
  checkODLStatus: async (id: number): Promise<{
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

  // ✅ updateStatus → updateODLStatus
  updateODLStatus: async (id: number, status: string): Promise<ODLResponse> => {
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
  // ✅ getProgress → fetchODLProgress
  fetchODLProgress: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}/progress`);
    return response.data;
  },

  // ✅ getTimeline → fetchODLTimeline
  fetchODLTimeline: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}/timeline`);
    return response.data;
  },

  // ✅ getMonitoringDetail → fetchODLMonitoringDetail
  fetchODLMonitoringDetail: async (id: number) => {
    const response = await api.get(`/odl-monitoring/monitoring/${id}`);
    return response.data;
  },

  // ✅ getMonitoringStats → fetchODLMonitoringStats
  fetchODLMonitoringStats: async () => {
    const response = await api.get('/odl-monitoring/monitoring/stats');
    return response.data;
  },

  // ✅ getMonitoringList → fetchODLMonitoringList
  fetchODLMonitoringList: async (params?: {
    skip?: number;
    limit?: number;
    status_filter?: string;
    priorita_min?: number;
    solo_attivi?: boolean;
  }) => {
    const queryParams = new URLSearchParams();
    
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params?.priorita_min !== undefined) queryParams.append('priorita_min', params.priorita_min.toString());
    if (params?.solo_attivi !== undefined) queryParams.append('solo_attivi', params.solo_attivi.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await api.get(`/odl-monitoring/monitoring${query}`);
    return response.data;
  },

  // ✅ getLogs → fetchODLLogs
  fetchODLLogs: async (id: number, limit?: number) => {
    const query = limit ? `?limit=${limit}` : '';
    const response = await api.get(`/odl-monitoring/monitoring/${id}/logs${query}`);
    return response.data;
  }
};

// Tipi base per TempoFase
export interface TempoFaseBase {
  odl_id: number;
  fase: "preparazione" | "laminazione" | "attesa_cura" | "cura";
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
  fase: "preparazione" | "laminazione" | "attesa_cura" | "cura";
  media_minuti: number;
  numero_osservazioni: number;
}

// ✅ RINOMINATO: API Tempo Fasi con nomi più descrittivi
export const phaseTimesApi = {
  // ✅ getAll → fetchPhaseTimes
  fetchPhaseTimes: (params?: { odl_id?: number; fase?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.odl_id) queryParams.append('odl_id', params.odl_id.toString());
    if (params?.fase) queryParams.append('fase', params.fase);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<TempoFaseResponse[]>(`/tempo-fasi/${query}`);
  },
  
  // ✅ getOne → fetchPhaseTime
  fetchPhaseTime: (id: number) => 
    apiRequest<TempoFaseResponse>(`/tempo-fasi/${id}`),
  
  // ✅ create → createPhaseTime
  createPhaseTime: (data: TempoFaseCreate) => 
    apiRequest<TempoFaseResponse>('/tempo-fasi/', 'POST', data),
  
  // ✅ update → updatePhaseTime
  updatePhaseTime: (id: number, data: TempoFaseUpdate) => 
    apiRequest<TempoFaseResponse>(`/tempo-fasi/${id}`, 'PUT', data),
  
  // ✅ delete → deletePhaseTime
  deletePhaseTime: (id: number) => 
    apiRequest<void>(`/tempo-fasi/${id}`, 'DELETE'),
    
  // ✅ getPrevisione → fetchPhaseTimeEstimate
  fetchPhaseTimeEstimate: (fase: string, partNumber?: string) => {
    const queryParams = new URLSearchParams();
    if (partNumber) queryParams.append('part_number', partNumber);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<PrevisioneTempo>(`/tempo-fasi/previsioni/${fase}${query}`);
  },

  // ✅ getStatisticheByPartNumber → fetchPhaseTimeStatsByPartNumber
  fetchPhaseTimeStatsByPartNumber: async (partNumber: string, giorni?: number) => {
    const queryParams = new URLSearchParams();
    if (giorni) queryParams.append('giorni', giorni.toString());
    
    // Dati fittizi per ogni fase
    const previsioni: Record<string, PrevisioneTempo> = {};
    
    // Recupera statistiche per ogni fase, inclusa preparazione
    for (const fase of ['preparazione', 'laminazione', 'attesa_cura', 'cura']) {
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

// ✅ RINOMINATO: API Reports con nomi più descrittivi
export const reportsApi = {
  // ✅ generate → generateReport
  generateReport: async (request: ReportGenerateRequest): Promise<ReportGenerateResponse> => {
    console.log('🔗 Report Generate Request:', request);
    return apiRequest<ReportGenerateResponse>('/reports/generate', 'POST', request);
  },
  
  // ✅ list → fetchReports
  fetchReports: (params?: {
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
  
  // ✅ downloadById → downloadReportById
  downloadReportById: async (reportId: number): Promise<Blob> => {
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
  
  // ✅ download → downloadReport
  downloadReport: async (filename: string): Promise<Blob> => {
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
  fetchSchedules: (params?: { 
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

  // Mantiene il vecchio metodo per compatibilità backward
  getAll: (params?: { 
    include_done?: boolean; 
    start_date?: string; 
    end_date?: string; 
  }) => {
    return scheduleApi.fetchSchedules(params);
  },
  
  fetchSchedule: (id: number) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}`),

  // Mantiene il vecchio metodo per compatibilità backward
  getOne: (id: number) => 
    scheduleApi.fetchSchedule(id),
  
  createSchedule: (data: ScheduleEntryCreateData) => 
    apiRequest<ScheduleEntry>('/schedules/', 'POST', data),

  // Mantiene il vecchio metodo per compatibilità backward
  create: (data: ScheduleEntryCreateData) => 
    scheduleApi.createSchedule(data),
  
  createRecurring: (data: RecurringScheduleCreateData) => 
    apiRequest<ScheduleEntry[]>('/schedules/recurring', 'POST', data),
  
  updateSchedule: (id: number, data: ScheduleEntryUpdateData) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}`, 'PUT', data),

  // Mantiene il vecchio metodo per compatibilità backward
  update: (id: number, data: ScheduleEntryUpdateData) => 
    scheduleApi.updateSchedule(id, data),
  
  executeAction: (id: number, action: ScheduleOperatorActionData) => 
    apiRequest<ScheduleEntry>(`/schedules/${id}/action`, 'POST', action),
  
  deleteSchedule: (id: number) => 
    apiRequest<void>(`/schedules/${id}`, 'DELETE'),

  // Mantiene il vecchio metodo per compatibilità backward
  delete: (id: number) => 
    scheduleApi.deleteSchedule(id),
    
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

// Tipi per Batch Nesting
export interface BatchNestingBase {
  nome?: string;
  stato: 'sospeso' | 'confermato' | 'terminato';
  autoclave_id: number;
  odl_ids: number[];
  parametri?: any;
  configurazione_json?: any;
  note?: string;
}

export interface BatchNestingCreate extends BatchNestingBase {
  creato_da_utente?: string;
  creato_da_ruolo?: string;
}

export interface BatchNestingUpdate extends Partial<BatchNestingBase> {
  confermato_da_utente?: string;
  confermato_da_ruolo?: string;
}

export interface BatchNestingResponse extends BatchNestingBase {
  id: string;
  numero_nesting: number;
  peso_totale_kg: number;
  area_totale_utilizzata: number;
  valvole_totali_utilizzate: number;
  creato_da_utente?: string;
  creato_da_ruolo?: string;
  confermato_da_utente?: string;
  confermato_da_ruolo?: string;
  data_conferma?: string;
  created_at: string;
  updated_at: string;
  stato_descrizione?: string;
}

export interface BatchNestingList {
  id: string;
  nome?: string;
  stato: 'sospeso' | 'confermato' | 'terminato';
  autoclave_id: number;
  numero_nesting: number;
  peso_totale_kg: number;
  created_at: string;
  updated_at: string;
}

// API Batch Nesting
export const batchNestingApi = {
  getData: async () => {
    return apiRequest<any>('/batch_nesting/data');
  },

  // 🚨 ENDPOINT LEGACY RIMOSSO - USA SEMPRE generaMulti
  // L'endpoint /genera è stato sostituito dall'architettura unificata aerospace
  genera: async (request: {
    odl_ids: string[];
    autoclave_ids: string[];
    parametri: {
      padding_mm: number;
      min_distance_mm: number;
    };
  }) => {
    // 🚀 AEROSPACE UNIFIED: Redirect automatico a generaMulti
    console.warn('⚠️ DEPRECATED: Uso di endpoint legacy /genera - redirecting to /genera-multi');
    return batchNestingApi.generaMulti({
      odl_ids: request.odl_ids,
      parametri: request.parametri
      // Note: autoclave_ids ignorati (auto-discovery nel sistema aerospace)
    });
  },

  // 🚀 AEROSPACE: Endpoint multi-batch con bypass degli interceptor problematici
  generaMulti: async (request: {
    odl_ids: string[];
    parametri: {
      padding_mm: number;
      min_distance_mm: number;
    };
  }) => {
    console.log('🚀 AEROSPACE GENERA-MULTI: Bypass interceptor per evitare false interpretazioni di errore');
    
    const fullUrl = `${API_BASE_URL}/batch_nesting/genera-multi`;
    console.log(`🌐 DIRECT FETCH: POST ${fullUrl}`, request);

    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        cache: 'no-store',
      });

      console.log(`📡 FETCH RESPONSE STATUS: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ FETCH ERROR DATA:', errorData);
        
        // 🔧 FIX CRITICO: Se il backend restituisce dati di successo nonostante l'errore HTTP
        // Questo può succedere quando c'è un'eccezione dopo aver generato i batch con successo
        if (errorData && typeof errorData === 'object' && errorData.success === true && errorData.best_batch_id) {
          console.warn('🚨 BACKEND WORKAROUND: Error HTTP ma dati di successo presenti!');
          console.warn('   success:', errorData.success);
          console.warn('   best_batch_id:', errorData.best_batch_id);
          console.warn('   Usando i dati di successo nonostante HTTP error');
          
          // Restituisci i dati come se fosse un successo
          return errorData;
        }
        
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ FETCH SUCCESS - RAW RESULT:', result);
      
      // ✅ AEROSPACE: Verifica che la risposta abbia i campi necessari
      if (typeof result === 'object' && result !== null) {
        console.log('🎯 AEROSPACE SUCCESS: Response object valid');
        return result as {
          success: boolean;
          message: string;
          total_autoclavi: number;
          success_count: number;
          error_count: number;
          best_batch_id: string | null;
          avg_efficiency: number;
          batch_results: Array<{
            batch_id: string | null;
            autoclave_id: number;
            autoclave_nome: string;
            efficiency: number;
            total_weight: number;
            positioned_tools: number;
            excluded_odls: number;
            success: boolean;
            message: string;
          }>;
          is_real_multi_batch: boolean;
          unique_autoclavi_count: number;
        };
      } else {
        console.error('❌ FETCH INVALID RESPONSE TYPE:', typeof result);
        throw new Error('Response invalida dal server aerospace');
      }
    } catch (error) {
      console.error('💥 FETCH NETWORK ERROR:', error);
      throw error;
    }
  },

  fetchBatchNestings: (params?: {
    skip?: number;
    limit?: number;
    autoclave_id?: number;
    stato?: 'sospeso' | 'confermato' | 'terminato';
    nome?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.autoclave_id) queryParams.append('autoclave_id', params.autoclave_id.toString());
    if (params?.stato) queryParams.append('stato', params.stato);
    if (params?.nome) queryParams.append('nome', params.nome);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<BatchNestingList[]>(`/batch_nesting${query}`);
  },

  // Mantiene il vecchio metodo per compatibilità backward
  getAll: (params?: {
    skip?: number;
    limit?: number;
    autoclave_id?: number;
    stato?: 'sospeso' | 'confermato' | 'terminato';
    nome?: string;
  }) => {
    return batchNestingApi.fetchBatchNestings(params);
  },

  fetchBatchNesting: (id: string) => 
    apiRequest<BatchNestingResponse>(`/batch_nesting/${id}`),

  // Mantiene il vecchio metodo per compatibilità backward
  getOne: (id: string) => 
    batchNestingApi.fetchBatchNesting(id),

  getFull: (id: string) => 
    apiRequest<any>(`/batch_nesting/${id}/full`),

  createBatchNesting: (data: BatchNestingCreate) => 
    apiRequest<BatchNestingResponse>('/batch_nesting/', 'POST', data),

  // Mantiene il vecchio metodo per compatibilità backward
  create: (data: BatchNestingCreate) => 
    batchNestingApi.createBatchNesting(data),

  updateBatchNesting: (id: string, data: BatchNestingUpdate) => 
    apiRequest<BatchNestingResponse>(`/batch_nesting/${id}`, 'PUT', data),

  // Mantiene il vecchio metodo per compatibilità backward
  update: (id: string, data: BatchNestingUpdate) => 
    batchNestingApi.updateBatchNesting(id, data),

  deleteBatchNesting: (id: string) => 
    apiRequest<void>(`/batch_nesting/${id}`, 'DELETE'),

  // 🗑️ NUOVO: Eliminazione multipla batch
  deleteMultipleBatch: async (ids: string[], confirm: boolean = false): Promise<{
    message: string;
    deleted_count: number;
    deleted_ids: string[];
    total_requested: number;
    errors: string[];
    cleanup_stats: {
      batch_sospesi_vecchi: number;
      batch_confermati: number;
      autoclavi_coinvolte: string[];
    };
    batch_analysis: Record<string, {
      nome: string;
      stato: string;
      autoclave: string;
      created_at: string;
    }>;
  }> => {
    try {
      console.log(`🗑️ Eliminazione multipla batch ${ids.join(', ')} (confirm: ${confirm})`);
      const queryParam = confirm ? '?confirm=true' : '';
      
      const response = await api.request({
        method: 'DELETE',
        url: `/batch_nesting/bulk${queryParam}`,
        data: ids,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log(`✅ Eliminazione multipla batch completata: ${response.data.deleted_count}/${response.data.total_requested}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore eliminazione multipla batch:`, error);
      throw error;
    }
  },

  // 🧹 NUOVO: Cleanup automatico batch vecchi (RISOLVE PROBLEMA ISMAR)
  cleanupOldBatches: async (options: {
    days_threshold?: number;
    stato_filter?: string;
    autoclave_filter?: string;
    dry_run?: boolean;
  } = {}): Promise<{
    message: string;
    threshold_date: string;
    filters: {
      days_threshold: number;
      stato_filter: string | null;
      autoclave_filter: string | null;
    };
    cleanup_stats: {
      total_candidates: number;
      deleted_count?: number;
      would_delete?: number;
      space_freed: string;
      autoclavi_affected: string[];
      errors?: string[];
    };
    autoclavi_stats: Record<string, {
      batch_count: number;
      oldest_days: number;
      states: string[];
    }>;
    batch_analysis: Record<string, {
      nome: string;
      stato: string;
      autoclave: string;
      days_old: number;
      created_at: string;
      odl_count: number;
    }>;
    deleted_ids?: string[];
    dry_run: boolean;
  }> => {
    try {
      const {
        days_threshold = 7,
        stato_filter = 'SOSPESO',
        autoclave_filter,
        dry_run = false
      } = options;
      
      console.log(`🧹 Cleanup batch vecchi - soglia: ${days_threshold} giorni, dry_run: ${dry_run}`);
      
      const params = new URLSearchParams();
      params.append('days_threshold', days_threshold.toString());
      if (stato_filter) params.append('stato_filter', stato_filter);
      if (autoclave_filter) params.append('autoclave_filter', autoclave_filter);
      params.append('dry_run', dry_run.toString());
      
      const response = await api.request({
        method: 'DELETE',
        url: `/batch_nesting/cleanup?${params.toString()}`,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log(`✅ Cleanup completato: ${response.data.message}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Errore cleanup batch:`, error);
      throw error;
    }
  },

  // Mantiene il vecchio metodo per compatibilità backward
  delete: (id: string) => 
    batchNestingApi.deleteBatchNesting(id),

  getStatistics: (id: string) => 
    apiRequest<any>(`/batch_nesting/${id}/statistics`),

  // 🆕 Nuova funzione per confermare il batch e avviare il ciclo di cura
  conferma: async (
    id: string, 
    confermato_da_utente: string, 
    confermato_da_ruolo: string
  ): Promise<BatchNestingResponse> => {
    try {
      console.log(`🚀 Avvio conferma batch ${id}...`);
      
      const queryParams = new URLSearchParams();
      queryParams.append('confermato_da_utente', confermato_da_utente);
      queryParams.append('confermato_da_ruolo', confermato_da_ruolo);
      
      const response = await apiRequest<BatchNestingResponse>(
        `/batch_nesting/${id}/confirm?${queryParams.toString()}`, 
        'PATCH'
      );
      
      console.log(`✅ Batch ${id} confermato con successo!`);
      return response;
    } catch (error: any) {
      console.error(`❌ Errore nella conferma del batch ${id}:`, error);
      
      // Estrai il messaggio di errore più specifico
      const errorMessage = error?.message || error?.detail || 'Errore sconosciuto nella conferma del batch';
      throw new Error(errorMessage);
    }
  },

  // 🆕 Funzione per caricare il batch (CONFERMATO → LOADED)
  carica: async (
    id: string, 
    caricato_da_utente: string, 
    caricato_da_ruolo: string
  ): Promise<BatchNestingResponse> => {
    try {
      console.log(`📦 Avvio caricamento batch ${id}...`);
      
      const queryParams = new URLSearchParams();
      queryParams.append('caricato_da_utente', caricato_da_utente);
      queryParams.append('caricato_da_ruolo', caricato_da_ruolo);
      
      const response = await apiRequest<BatchNestingResponse>(
        `/batch_nesting/${id}/load?${queryParams.toString()}`, 
        'PATCH'
      );
      
      console.log(`✅ Batch ${id} caricato con successo!`);
      return response;
    } catch (error: any) {
      console.error(`❌ Errore nel caricamento del batch ${id}:`, error);
      
      const errorMessage = error?.message || error?.detail || 'Errore sconosciuto nel caricamento del batch';
      throw new Error(errorMessage);
    }
  },

  // 🆕 Funzione per avviare la cura (SOSPESO → IN_CURA)
  avviaCura: async (
    id: string, 
    caricato_da_utente: string, 
    caricato_da_ruolo: string
  ): Promise<BatchNestingResponse> => {
    try {
      console.log(`🔥 Avvio cura batch ${id}...`);
      
      const queryParams = new URLSearchParams();
      queryParams.append('caricato_da_utente', caricato_da_utente);
      queryParams.append('caricato_da_ruolo', caricato_da_ruolo);
      
      const response = await apiRequest<BatchNestingResponse>(
        `/batch_nesting/${id}/start-cure?${queryParams.toString()}`, 
        'PATCH'
      );
      
      console.log(`✅ Cura batch ${id} avviata con successo!`);
      return response;
    } catch (error: any) {
      console.error(`❌ Errore nell'avvio cura del batch ${id}:`, error);
      
      const errorMessage = error?.message || error?.detail || 'Errore sconosciuto nell\'avvio della cura';
      throw new Error(errorMessage);
    }
  },

  // 🆕 Funzione per terminare il batch (CURED → TERMINATO)
  termina: async (
    id: string, 
    terminato_da_utente: string, 
    terminato_da_ruolo: string
  ): Promise<BatchNestingResponse> => {
    try {
      console.log(`🏁 Avvio terminazione batch ${id}...`);
      
      const queryParams = new URLSearchParams();
      queryParams.append('terminato_da_utente', terminato_da_utente);
      queryParams.append('terminato_da_ruolo', terminato_da_ruolo);
      
      const response = await apiRequest<BatchNestingResponse>(
        `/batch_nesting/${id}/terminate?${queryParams.toString()}`, 
        'PATCH'
      );
      
      console.log(`✅ Batch ${id} terminato con successo!`);
      return response;
    } catch (error: any) {
      console.error(`❌ Errore nella terminazione del batch ${id}:`, error);
      
      const errorMessage = error?.message || error?.detail || 'Errore sconosciuto nella terminazione del batch';
      throw new Error(errorMessage);
    }
  },

  // 🆕 Metodo legacy per compatibilità backward - ora mappatosull'endpoint corretto
  chiudi: async (
    id: string, 
    chiuso_da_utente: string, 
    chiuso_da_ruolo: string
  ): Promise<BatchNestingResponse> => {
    // Compatibilità: chiudi ora mappa su termina
    return batchNestingApi.termina(id, chiuso_da_utente, chiuso_da_ruolo);
  },

  // 🚀 BEST PRACTICE: Caricamento intelligente risultati batch senza parametri confusi
  getResult: async (batchId: string) => {
    try {
      console.log(`📊 CARICAMENTO AUTOMATICO: Rilevamento multi-batch per ${batchId}...`);
      
      // 🎯 STRATEGIA 1: Prova sempre multi-batch per rilevare automaticamente batch correlati
      try {
        const multiResponse = await apiRequest<any>(`/batch_nesting/result/${batchId}?multi=true`);
        
        if (multiResponse.batch_results && Array.isArray(multiResponse.batch_results) && multiResponse.batch_results.length > 1) {
          console.log(`✅ MULTI-BATCH AUTO-RILEVATO: ${multiResponse.batch_results.length} batch correlati`);
          return multiResponse;
        }
      } catch (multiError) {
        console.log(`🔄 Multi-batch non disponibile, usando single-batch:`, multiError);
      }
      
      // 🎯 STRATEGIA 2: Fallback intelligente a single-batch
      const singleResponse = await apiRequest<any>(`/batch_nesting/result/${batchId}`);
      console.log(`✅ SINGLE-BATCH CARICATO: ${batchId}`);
      return singleResponse;
      
    } catch (error: any) {
      console.error(`❌ Errore nel caricamento risultati batch ${batchId}:`, error);
      throw new Error(error?.message || 'Errore nel caricamento dei risultati');
    }
  },

  // 🆕 Metodo per confermare un batch (alias di conferma per compatibilità)
  confirm: async (
    id: string, 
    data: {
      confermato_da_utente: string;
      confermato_da_ruolo: string;
    }
  ): Promise<BatchNestingResponse> => {
    return batchNestingApi.conferma(id, data.confermato_da_utente, data.confermato_da_ruolo);
  }
};

// ✅ NUOVO: API per la produzione




// API Nesting
export const nestingApi = {
  getData: async () => {
    return apiRequest<any>('/nesting/data');
  },

  genera: async (request: {
    odl_ids: string[];
    autoclave_ids: string[];
    parametri?: {
      padding_mm?: number;
      min_distance_mm?: number;
      priorita_area?: boolean;
    };
  }) => {
    return apiRequest<any>('/nesting/genera', 'POST', request);
  }
};

// ✅ NUOVO: Interfacce per System Logs
export interface SystemLogResponse {
  id: number;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  event_type: string;
  user_role: string;
  user_id?: string;
  action: string;
  entity_type?: string;
  entity_id?: number;
  details?: string;
  old_value?: string;
  new_value?: string;
  ip_address?: string;
}

export interface SystemLogFilter {
  event_type?: string;
  user_role?: string;
  level?: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  entity_type?: string;
  entity_id?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface SystemLogStats {
  total_logs: number;
  logs_by_type: Record<string, number>;
  logs_by_role: Record<string, number>;
  logs_by_level: Record<string, number>;
  recent_errors: SystemLogResponse[];
}

// ✅ NUOVO: API System Logs con nomi più descrittivi
export const systemLogsApi = {
  /**
   * ✅ getAll → fetchSystemLogs
   */
  fetchSystemLogs: (filters?: SystemLogFilter): Promise<SystemLogResponse[]> => {
    const queryParams = new URLSearchParams();
    
    if (filters?.event_type) queryParams.append('event_type', filters.event_type);
    if (filters?.user_role) queryParams.append('user_role', filters.user_role);
    if (filters?.level) queryParams.append('level', filters.level);
    if (filters?.entity_type) queryParams.append('entity_type', filters.entity_type);
    if (filters?.entity_id) queryParams.append('entity_id', filters.entity_id.toString());
    if (filters?.start_date) queryParams.append('start_date', filters.start_date);
    if (filters?.end_date) queryParams.append('end_date', filters.end_date);
    if (filters?.limit) queryParams.append('limit', filters.limit.toString());
    if (filters?.offset) queryParams.append('offset', filters.offset.toString());
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<SystemLogResponse[]>(`/system-logs${query}`);
  },

  /**
   * ✅ getStats → fetchSystemLogStats
   */
  fetchSystemLogStats: (days: number = 30): Promise<SystemLogStats> => {
    return apiRequest<SystemLogStats>(`/system-logs/stats?days=${days}`);
  },

  /**
   * ✅ getRecentErrors → fetchRecentErrors
   */
  fetchRecentErrors: (limit: number = 20): Promise<SystemLogResponse[]> => {
    return apiRequest<SystemLogResponse[]>(`/system-logs/recent-errors?limit=${limit}`);
  },

  /**
   * ✅ getByEntity → fetchLogsByEntity
   */
  fetchLogsByEntity: (entityType: string, entityId: number, limit: number = 50): Promise<SystemLogResponse[]> => {
    return apiRequest<SystemLogResponse[]>(`/system-logs/by-entity/${entityType}/${entityId}?limit=${limit}`);
  },

  /**
   * ✅ exportCsv → exportSystemLogsCsv
   */
  exportSystemLogsCsv: async (filters?: SystemLogFilter): Promise<void> => {
    const queryParams = new URLSearchParams();
    
    if (filters?.event_type) queryParams.append('event_type', filters.event_type);
    if (filters?.user_role) queryParams.append('user_role', filters.user_role);
    if (filters?.start_date) queryParams.append('start_date', filters.start_date);
    if (filters?.end_date) queryParams.append('end_date', filters.end_date);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    
    try {
      const response = await fetch(`${API_BASE_URL}/system-logs/export${query}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Errore nell'esportazione: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `system_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Errore nell\'esportazione CSV:', error);
      throw error;
    }
  }
};

// ✅ NUOVO: API per i tempi standard v1.4.5-DEMO
export interface StandardTime {
  id: number;
  part_number: string;
  phase: string;
  minutes: number;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface FaseConfronto {
  fase: string;
  tempo_osservato_minuti: number;
  tempo_standard_minuti: number;
  numero_osservazioni: number;
  delta_percentuale: number;
  dati_limitati: boolean;
  colore_delta: "verde" | "giallo" | "rosso";
  note_standard?: string;
}

export interface TimesComparisonResponse {
  part_number: string;
  periodo_giorni: number;
  fasi: Record<string, FaseConfronto>;
  scostamento_medio_percentuale: number;
  odl_totali_periodo: number;
  dati_limitati_globale: boolean;
  ultima_analisi: string;
}

// ✅ RINOMINATO: API Standard Times con nomi più descrittivi
export const standardTimesApi = {
  /**
   * ✅ getAll → fetchStandardTimes
   */
  fetchStandardTimes: (params?: {
    skip?: number;
    limit?: number;
    part_number?: string;
    part_id?: number;
    phase?: string;
  }): Promise<StandardTime[]> => {
    const queryParams = new URLSearchParams();
    
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.part_number) queryParams.append('part_number', params.part_number);
    if (params?.part_id) queryParams.append('part_id', params.part_id.toString());
    if (params?.phase) queryParams.append('phase', params.phase);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<StandardTime[]>(`/standard-times${query}`);
  },

  /**
   * ✅ getById → fetchStandardTime
   */
  fetchStandardTime: (id: number): Promise<StandardTime> => {
    return apiRequest<StandardTime>(`/standard-times/${id}`);
  },

  /**
   * ✅ getByPartNumber → fetchStandardTimesByPartNumber
   */
  fetchStandardTimesByPartNumber: (partNumber: string): Promise<StandardTime[]> => {
    return apiRequest<StandardTime[]>(`/standard-times/by-part-number/${partNumber}`);
  },

  /**
   * ✅ getComparison → fetchTimesComparison
   * 🎯 FUNZIONE PRINCIPALE per v1.4.5-DEMO
   */
  fetchTimesComparison: (partNumber: string, giorni: number = 30): Promise<TimesComparisonResponse> => {
    return apiRequest<TimesComparisonResponse>(`/standard-times/comparison/${partNumber}?giorni=${giorni}`);
  },

  /**
   * ✅ getTopDelta → fetchTopDeltaVariances
   * 🎯 FUNZIONE PRINCIPALE per v1.4.6-DEMO
   */
  fetchTopDeltaVariances: (limit: number = 5, days: number = 30): Promise<TopDeltaResponse> => {
    return apiRequest<TopDeltaResponse>(`/standard-times/top-delta?limit=${limit}&days=${days}`);
  },

  /**
   * ✅ recalculate → recalculateStandardTimes
   */
  recalculateStandardTimes: (userId: string = "admin", userRole: string = "ADMIN"): Promise<any> => {
    return apiRequest<any>(`/standard-times/recalc?user_id=${userId}&user_role=${userRole}`, 'POST');
  },

  /**
   * ✅ getStatistics → fetchStandardTimesStatistics
   */
  fetchStandardTimesStatistics: (): Promise<any> => {
    return apiRequest<any>('/standard-times/statistics');
  }
};

// ✅ NUOVO: Tipi per Top Delta Variances (v1.4.6-DEMO)
export interface TopDeltaVariance {
  part_number: string;
  fase: string;
  delta_percent: number;
  abs_delta_percent: number;
  tempo_osservato: number;
  tempo_standard: number;
  numero_osservazioni: number;
  colore_delta: "verde" | "giallo" | "rosso";
}

export interface TopDeltaResponse {
  success: boolean;
  data: TopDeltaVariance[];
  parameters: {
    limit: number;
    days: number;
    data_analisi: string;
  };
} 