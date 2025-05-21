/**
 * Tipi TypeScript per il sistema di nesting delle parti in autoclave
 */

/**
 * Parametri di ottimizzazione per l'algoritmo di nesting
 */
export interface NestingParameters {
    /** Peso assegnato all'utilizzo delle valvole (0-10) */
    peso_valvole: number;
    /** Peso assegnato all'utilizzo dell'area (0-10) */
    peso_area: number;
    /** Peso assegnato alla priorità degli ODL (0-10) */
    peso_priorita: number;
    /** Spazio minimo in mm tra gli ODL nell'autoclave */
    spazio_minimo_mm: number;
}

/**
 * Richiesta per eseguire il nesting automatico o manuale
 */
export interface NestingRequest {
    /** Lista degli ID degli ODL da considerare (null = tutti gli ODL in attesa di cura) */
    odl_ids?: number[] | null;
    /** Lista degli ID delle autoclavi da considerare (null = tutte le autoclavi disponibili) */
    autoclave_ids?: number[] | null;
    /** Parametri personalizzati per l'ottimizzazione (null = usa i parametri attivi) */
    parameters?: NestingParameters | null; 
    /** Se true, esegue il nesting manuale con gli ODL specificati */
    manual?: boolean;
}

/**
 * Dettagli di posizionamento di un ODL nell'autoclave
 */
export interface ODLLayout {
    /** ID dell'ODL */
    odl_id: number;
    /** Coordinata X in mm */
    x: number;
    /** Coordinata Y in mm */
    y: number;
    /** Lunghezza dell'ODL in mm */
    lunghezza: number;
    /** Larghezza dell'ODL in mm */
    larghezza: number;
    /** Numero di valvole utilizzate da questo ODL */
    valvole_utilizzate: number;
    /** Nome della parte */
    parte_nome: string;
    /** Codice del tool */
    tool_codice: string;
    /** Priorità dell'ODL */
    priorita: number;
}

/**
 * Layout completo degli ODL in un'autoclave
 */
export interface AutoclaveLayout {
    /** ID dell'autoclave */
    autoclave_id: number;
    /** Nome dell'autoclave */
    autoclave_nome: string;
    /** Layout degli ODL nell'autoclave */
    odl_layout: ODLLayout[];
    /** Area totale dell'autoclave in mm² */
    area_totale_mm2: number;
    /** Area utilizzata dagli ODL in mm² */
    area_utilizzata_mm2: number;
    /** Percentuale di area utilizzata rispetto al totale */
    efficienza_area: number;
    /** Numero totale di valvole disponibili */
    valvole_totali: number;
    /** Numero di valvole utilizzate */
    valvole_utilizzate: number;
    /** ID del risultato di nesting salvato */
    nesting_id?: number;
}

/**
 * Risposta dal server per il nesting automatico o manuale
 */
export interface NestingResponse {
    /** Se true, il nesting è stato eseguito con successo */
    success: boolean;
    /** Messaggio informativo sul risultato */
    message: string;
    /** Layout risultanti (uno per ogni autoclave) */
    layouts: AutoclaveLayout[];
    /** Timestamp della risposta */
    timestamp: string;
}

/**
 * Richiesta per confermare un risultato di nesting
 */
export interface NestingConfirmRequest {
    /** ID del risultato di nesting da confermare */
    nesting_id: number;
}

/**
 * Risultato di nesting salvato
 */
export interface NestingResultSummary {
    /** ID del risultato */
    id: number;
    /** Codice identificativo del risultato */
    codice: string;
    /** Nome dell'autoclave */
    autoclave_nome: string;
    /** Se true, il risultato è stato confermato */
    confermato: boolean;
    /** Data di conferma (null se non confermato) */
    data_conferma: string | null;
    /** Percentuale di area utilizzata */
    efficienza_area: number;
    /** Numero di valvole utilizzate */
    valvole_utilizzate: number;
    /** Numero totale di valvole disponibili */
    valvole_totali: number;
    /** Se true, il nesting è stato generato manualmente */
    generato_manualmente: boolean;
    /** Data di creazione */
    created_at: string;
}

/**
 * ODL in attesa di cura
 */
export interface ODLAttesaCura {
    /** ID dell'ODL */
    id: number;
    /** ID della parte */
    parte_id: number;
    /** Nome della parte */
    parte_nome: string;
    /** ID del tool */
    tool_id: number; 
    /** Codice del tool */
    tool_codice: string;
    /** Priorità dell'ODL */
    priorita: number;
    /** Larghezza del tool in mm */
    larghezza: number;
    /** Lunghezza del tool in mm */
    lunghezza: number;
    /** Numero di valvole richieste */
    valvole_richieste: number;
    /** ID del ciclo di cura */
    ciclo_cura_id: number;
    /** Nome del ciclo di cura */
    ciclo_cura_nome: string;
} 