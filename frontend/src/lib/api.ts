// API client per interagire con il backend

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Tipi base per Catalogo
export interface CatalogoBase {
  descrizione: string;
  categoria?: string;
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
  codice: string;
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

const api = axios.create({
  baseURL: API_BASE_URL,
})

export interface Tool {
  id: number
  codice: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  disponibile: boolean
  created_at: string
  updated_at: string
}

export interface CreateToolDto {
  codice: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  disponibile: boolean
}

export interface UpdateToolDto extends Partial<CreateToolDto> {}

export const toolApi = {
  getAll: async (): Promise<Tool[]> => {
    const response = await api.get<Tool[]>('/tools')
    return response.data
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
}

// Common fetch wrapper
const apiRequest = async <T>(
  endpoint: string, 
  method: string = 'GET', 
  data?: any
): Promise<T> => {
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

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

  // Gestione errori HTTP
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw {
      status: response.status,
      message: errorData.detail || `Errore API: ${response.status} ${response.statusText}`,
      data: errorData,
    };
  }

  // Per DELETE (204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
};

// API Catalogo
export const catalogoApi = {
  getAll: (params?: { skip?: number; limit?: number; categoria?: string; attivo?: boolean }) => {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.categoria) queryParams.append('categoria', params.categoria);
    if (params?.attivo !== undefined) queryParams.append('attivo', params.attivo.toString());
    
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
  produttore?: string
  anno_produzione?: number
  note?: string
  created_at: string
  updated_at: string
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

  getById: async (id: number): Promise<Autoclave> => {
    const response = await api.get<Autoclave>(`/autoclavi/${id}`)
    return response.data
  },

  create: async (data: CreateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.post<Autoclave>('/autoclavi', data)
    return response.data
  },

  update: async (id: number, data: UpdateAutoclaveDto): Promise<Autoclave> => {
    const response = await api.put<Autoclave>(`/autoclavi/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/autoclavi/${id}`)
  },
}

// Tipi per ODL
export interface ODLBase {
  parte_id: number;
  tool_id: number;
  priorita: number;
  status: "Preparazione" | "Laminazione" | "Attesa Cura" | "Cura" | "Finito";
  note?: string;
}

export interface ODLCreate extends ODLBase {}

export interface ODLUpdate extends Partial<ODLBase> {}

export interface ParteInODLResponse {
  id: number;
  part_number: string;
  descrizione_breve: string;
}

export interface ToolInODLResponse {
  id: number;
  codice: string;
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
  getAll: (params?: { parte_id?: number; tool_id?: number; status?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.parte_id) queryParams.append('parte_id', params.parte_id.toString());
    if (params?.tool_id) queryParams.append('tool_id', params.tool_id.toString());
    if (params?.status) queryParams.append('status', params.status);
    
    const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
    return apiRequest<ODLResponse[]>(`/odl${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<ODLResponse>(`/odl/${id}`),
  
  create: (data: ODLCreate) => 
    apiRequest<ODLResponse>('/odl/', 'POST', data),
  
  update: (id: number, data: ODLUpdate) => 
    apiRequest<ODLResponse>(`/odl/${id}`, 'PUT', data),
  
  delete: (id: number) => 
    apiRequest<void>(`/odl/${id}`, 'DELETE'),
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

// Tipi per Nesting
export interface NestingResponse {
  id: number;
  autoclave: {
    id: number;
    nome: string;
    codice: string;
    num_linee_vuoto: number;
    lunghezza: number;
    larghezza_piano: number;
  };
  odl_list: Array<{
    id: number;
    parte: {
      id: number;
      part_number: string;
      descrizione_breve: string;
      num_valvole_richieste: number;
    };
    tool: {
      id: number;
      codice: string;
      descrizione?: string;
      lunghezza_piano: number;
      larghezza_piano: number;
    };
    priorita: number;
  }>;
  area_utilizzata: number;
  area_totale: number;
  valvole_utilizzate: number;
  valvole_totali: number;
  created_at: string;
}

// API Nesting
export const nestingApi = {
  getAll: () => 
    apiRequest<NestingResponse[]>('/nesting/'),
  
  getOne: (id: number) => 
    apiRequest<NestingResponse>(`/nesting/${id}`),
  
  generateAuto: () => 
    apiRequest<NestingResponse>('/nesting/auto', 'POST'),
}; 