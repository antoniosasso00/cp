import { 
  NestingLayoutResponse, 
  NestingLayoutData
} from '@/lib/api'

interface NestingLayoutRequest {
  padding_mm?: number
  borda_mm?: number
  rotazione_abilitata?: boolean
}

export const nestingApi = {
  /**
   * Ottiene il layout di un nesting specifico
   */
  async getLayout(nestingId: number, params?: NestingLayoutRequest): Promise<NestingLayoutResponse> {
    const queryParams = new URLSearchParams()
    
    if (params?.padding_mm !== undefined) {
      queryParams.append('padding_mm', params.padding_mm.toString())
    }
    if (params?.borda_mm !== undefined) {
      queryParams.append('borda_mm', params.borda_mm.toString())
    }
    if (params?.rotazione_abilitata !== undefined) {
      queryParams.append('rotazione_abilitata', params.rotazione_abilitata.toString())
    }
    
    const url = `/api/v1/nesting/${nestingId}/layout${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`Errore HTTP: ${response.status}`)
    }
    
    return await response.json()
  },

  /**
   * Ottiene il layout di multipli nesting
   */
  async getMultiLayout(nestingIds: number[], params?: NestingLayoutRequest): Promise<any> {
    const queryParams = new URLSearchParams()
    
    nestingIds.forEach(id => queryParams.append('nesting_ids', id.toString()))
    
    if (params?.padding_mm !== undefined) {
      queryParams.append('padding_mm', params.padding_mm.toString())
    }
    if (params?.borda_mm !== undefined) {
      queryParams.append('borda_mm', params.borda_mm.toString())
    }
    if (params?.rotazione_abilitata !== undefined) {
      queryParams.append('rotazione_abilitata', params.rotazione_abilitata.toString())
    }
    
    const url = `/api/v1/nesting/multi-layout?${queryParams.toString()}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`Errore HTTP: ${response.status}`)
    }
    
    return await response.json()
  }
} 