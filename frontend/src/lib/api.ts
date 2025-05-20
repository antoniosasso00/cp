// API client per interagire con il backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

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
    return apiRequest<ParteResponse[]>(`/parte${query}`);
  },
  
  getOne: (id: number) => 
    apiRequest<ParteResponse>(`/parte/${id}`),
  
  create: (data: ParteCreate) => 
    apiRequest<ParteResponse>('/parte/', 'POST', data),
  
  update: (id: number, data: ParteUpdate) => 
    apiRequest<ParteResponse>(`/parte/${id}`, 'PUT', data),
  
  delete: (id: number) => 
    apiRequest<void>(`/parte/${id}`, 'DELETE'),
};

// API CicloCura (per selezionare nei dropdown)
export const cicloCuraApi = {
  getAll: () => apiRequest<{ id: number; nome: string }[]>('/ciclo_cura'),
};

// API Tool (per selezionare nei dropdown)
export const toolApi = {
  getAll: () => apiRequest<{ id: number; codice: string; descrizione?: string }[]>('/tool'),
}; 