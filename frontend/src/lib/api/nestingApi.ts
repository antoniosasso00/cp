import { 
    NestingParameters, 
    NestingRequest, 
    NestingResponse, 
    NestingConfirmRequest,
    NestingResultSummary,
    ODLAttesaCura
} from '../types/nesting';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * API per il sistema di nesting
 */
export const nestingApi = {
    /**
     * Esegue l'algoritmo di nesting automatico
     * @param request Parametri per la richiesta di nesting
     * @returns Risposta con i layout ottimizzati
     */
    runAutoNesting: async (request: NestingRequest): Promise<NestingResponse> => {
        const response = await fetch(`${API_URL}/nesting/auto`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nell\'esecuzione del nesting automatico');
        }

        return response.json();
    },

    /**
     * Esegue il nesting manuale con gli ODL selezionati
     * @param request Parametri per la richiesta di nesting manuale
     * @returns Risposta con i layout ottimizzati
     */
    runManualNesting: async (request: NestingRequest): Promise<NestingResponse> => {
        const response = await fetch(`${API_URL}/nesting/manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nell\'esecuzione del nesting manuale');
        }

        return response.json();
    },

    /**
     * Conferma un risultato di nesting e aggiorna lo stato degli ODL a "Cura"
     * @param nestingId ID del risultato di nesting da confermare
     * @returns Risposta della conferma
     */
    confirmNesting: async (nestingId: number): Promise<{ success: boolean; message: string }> => {
        const request: NestingConfirmRequest = { nesting_id: nestingId };
        
        const response = await fetch(`${API_URL}/nesting/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nella conferma del nesting');
        }

        return response.json();
    },

    /**
     * Ottiene i parametri di ottimizzazione attivi
     * @returns Parametri di ottimizzazione
     */
    getParameters: async (): Promise<NestingParameters> => {
        const response = await fetch(`${API_URL}/nesting/params`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel recupero dei parametri di nesting');
        }

        return response.json();
    },

    /**
     * Aggiorna i parametri di ottimizzazione
     * @param params Nuovi parametri di ottimizzazione
     * @returns Risposta dell'aggiornamento
     */
    updateParameters: async (params: NestingParameters): Promise<{ success: boolean; message: string }> => {
        const response = await fetch(`${API_URL}/nesting/params`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nell\'aggiornamento dei parametri di nesting');
        }

        return response.json();
    },

    /**
     * Ottiene la lista dei risultati di nesting salvati
     * @param limit Numero massimo di risultati da restituire
     * @param offset Offset per la paginazione
     * @returns Lista dei risultati di nesting
     */
    getResults: async (limit: number = 10, offset: number = 0): Promise<NestingResultSummary[]> => {
        const response = await fetch(`${API_URL}/nesting/results?limit=${limit}&offset=${offset}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel recupero dei risultati di nesting');
        }

        return response.json();
    },

    /**
     * Ottiene i dettagli di un risultato di nesting specifico
     * @param nestingId ID del risultato di nesting
     * @returns Dettagli completi del risultato di nesting
     */
    getResultDetails: async (nestingId: number): Promise<any> => {
        const response = await fetch(`${API_URL}/nesting/results/${nestingId}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel recupero dei dettagli del risultato di nesting');
        }

        return response.json();
    },

    /**
     * Ottiene gli ODL in stato "Attesa Cura" per il nesting manuale
     * @returns Lista degli ODL in attesa di cura
     */
    getODLInAttesaCura: async (): Promise<ODLAttesaCura[]> => {
        // Nota: questo endpoint non esiste ancora, dovremo crearlo nell'API ODL
        const response = await fetch(`${API_URL}/odl?status=Attesa%20Cura&includeDetails=true`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore nel recupero degli ODL in attesa di cura');
        }

        return response.json();
    }
}; 