"""
Schema Pydantic per la gestione dei dati di nesting.

Questo modulo definisce i modelli di dati per:
- NestingRead: Schema per la lettura dei dati di nesting
- NestingCreate: Schema per la creazione di nuovi nesting
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class NestingBase(BaseModel):
    """
    Schema base per il nesting con i campi comuni.
    """
    note: Optional[str] = Field(
        default=None, 
        description="Note aggiuntive sul nesting",
        max_length=500
    )


class NestingCreate(NestingBase):
    """
    Schema per la creazione di un nuovo nesting.
    
    Contiene solo i campi che l'utente può specificare durante la creazione.
    I campi come ID e created_at vengono generati automaticamente dal sistema.
    """
    pass  # Per ora eredita solo da NestingBase


class NestingRead(NestingBase):
    """
    Schema per la lettura dei dati di nesting.
    
    Contiene tutti i campi inclusi quelli generati automaticamente dal sistema.
    """
    id: str = Field(
        description="Identificativo univoco del nesting"
    )
    created_at: datetime = Field(
        description="Data e ora di creazione del nesting"
    )
    stato: str = Field(
        description="Stato corrente del nesting",
        examples=["bozza", "confermato", "sospeso", "cura", "finito"]
    )
    
    # ✅ CAMPI AGGIUNTIVI: Aggiungo tutti i campi disponibili dal database
    autoclave_id: Optional[int] = Field(None, description="ID dell'autoclave")
    autoclave_nome: Optional[str] = Field(None, description="Nome dell'autoclave")
    ciclo_cura: Optional[str] = Field(None, description="Ciclo di cura")
    odl_inclusi: Optional[int] = Field(None, description="Numero di ODL inclusi")
    odl_esclusi: Optional[int] = Field(None, description="Numero di ODL esclusi")
    efficienza: Optional[float] = Field(None, description="Efficienza in percentuale")
    area_utilizzata: Optional[float] = Field(None, description="Area utilizzata in cm²")
    area_totale: Optional[float] = Field(None, description="Area totale disponibile in cm²")
    peso_totale: Optional[float] = Field(None, description="Peso totale in kg")
    valvole_utilizzate: Optional[int] = Field(None, description="Numero di valvole utilizzate")
    valvole_totali: Optional[int] = Field(None, description="Numero totale di valvole")

    class Config:
        """
        Configurazione del modello Pydantic.
        """
        # Permette la serializzazione da oggetti ORM (quando useremo SQLAlchemy)
        from_attributes = True
        
        # Esempio di come apparirà il JSON
        json_schema_extra = {
            "example": {
                "id": "123",
                "created_at": "2024-01-15T10:30:00",
                "note": "Nesting per ottimizzazione taglio lamiera",
                "stato": "confermato",
                "autoclave_id": 1,
                "autoclave_nome": "Autoclave Alpha",
                "ciclo_cura": "Standard 180°C",
                "odl_inclusi": 5,
                "odl_esclusi": 2,
                "efficienza": 75.5,
                "area_utilizzata": 3500.0,
                "area_totale": 4500.0,
                "peso_totale": 420.0,
                "valvole_utilizzate": 16,
                "valvole_totali": 20
            }
        }

class AutomaticNestingRequest(BaseModel):
    """Schema per la richiesta di nesting automatico"""
    force_regenerate: bool = Field(False, description="Forza la rigenerazione anche se esistono nesting in bozza")
    max_autoclaves: Optional[int] = Field(None, description="Numero massimo di autoclavi da utilizzare")
    priority_threshold: Optional[int] = Field(None, description="Soglia minima di priorità degli ODL da considerare")

class ODLNestingInfo(BaseModel):
    """Informazioni su un ODL nel contesto del nesting"""
    id: int = Field(..., description="ID dell'ODL")
    parte_codice: Optional[str] = Field(None, description="Codice della parte")
    tool_nome: Optional[str] = Field(None, description="Nome del tool")
    priorita: int = Field(..., description="Priorità dell'ODL")
    dimensioni: Dict[str, float] = Field(..., description="Dimensioni del tool (larghezza, lunghezza, peso)")
    ciclo_cura: Optional[str] = Field(None, description="Ciclo di cura richiesto")
    status: str = Field(..., description="Stato attuale dell'ODL")

class AutoclaveNestingInfo(BaseModel):
    """Informazioni su un'autoclave nel contesto del nesting"""
    id: int = Field(..., description="ID dell'autoclave")
    nome: str = Field(..., description="Nome dell'autoclave")
    area_piano: float = Field(..., description="Area del piano in cm²")
    max_load_kg: Optional[float] = Field(None, description="Carico massimo in kg")
    stato: str = Field(..., description="Stato dell'autoclave")

class NestingResultSummary(BaseModel):
    """Riepilogo di un risultato di nesting"""
    id: int = Field(..., description="ID del nesting result")
    autoclave_id: int = Field(..., description="ID dell'autoclave")
    autoclave_nome: str = Field(..., description="Nome dell'autoclave")
    ciclo_cura: str = Field(..., description="Ciclo di cura del gruppo")
    odl_inclusi: int = Field(..., description="Numero di ODL inclusi")
    odl_esclusi: int = Field(..., description="Numero di ODL esclusi")
    efficienza: float = Field(..., description="Efficienza di utilizzo in percentuale")
    area_utilizzata: float = Field(..., description="Area utilizzata in cm²")
    peso_totale: float = Field(..., description="Peso totale in kg")
    stato: str = Field(..., description="Stato del nesting")

class AutomaticNestingResponse(BaseModel):
    """Risposta della generazione automatica del nesting"""
    success: bool = Field(..., description="Indica se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio descrittivo del risultato")
    nesting_results: List[NestingResultSummary] = Field(..., description="Lista dei nesting generati")
    summary: Optional[Dict[str, Any]] = Field(None, description="Riepilogo statistico dell'operazione")

class NestingPreviewRequest(BaseModel):
    """Schema per la richiesta di preview del nesting"""
    include_excluded: bool = Field(True, description="Include gli ODL esclusi nella preview")
    group_by_cycle: bool = Field(True, description="Raggruppa per ciclo di cura")

class ODLGroupPreview(BaseModel):
    """Preview di un gruppo di ODL per ciclo di cura"""
    ciclo_cura: str = Field(..., description="Identificativo del ciclo di cura")
    odl_list: List[ODLNestingInfo] = Field(..., description="Lista degli ODL nel gruppo")
    total_area: float = Field(..., description="Area totale richiesta in cm²")
    total_weight: float = Field(..., description="Peso totale in kg")
    compatible_autoclaves: List[AutoclaveNestingInfo] = Field(..., description="Autoclavi compatibili")

class NestingPreviewResponse(BaseModel):
    """Risposta della preview del nesting"""
    success: bool = Field(..., description="Indica se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio descrittivo")
    odl_groups: List[ODLGroupPreview] = Field(..., description="Gruppi di ODL per ciclo di cura")
    available_autoclaves: List[AutoclaveNestingInfo] = Field(..., description="Autoclavi disponibili")
    total_odl_pending: int = Field(..., description="Totale ODL in attesa")

class NestingDetailResponse(BaseModel):
    """Dettagli completi di un nesting result"""
    id: int = Field(..., description="ID del nesting result")
    autoclave: AutoclaveNestingInfo = Field(..., description="Informazioni dell'autoclave")
    odl_inclusi: List[ODLNestingInfo] = Field(..., description="ODL inclusi nel nesting")
    odl_esclusi: List[ODLNestingInfo] = Field(..., description="ODL esclusi dal nesting")
    motivi_esclusione: List[str] = Field(..., description="Motivi di esclusione degli ODL")
    statistiche: Dict[str, float] = Field(..., description="Statistiche del nesting")
    stato: str = Field(..., description="Stato del nesting")
    note: Optional[str] = Field(None, description="Note aggiuntive")
    created_at: datetime = Field(..., description="Data di creazione")

class NestingStatusUpdate(BaseModel):
    """Schema per l'aggiornamento dello stato di un nesting"""
    stato: str = Field(..., description="Nuovo stato del nesting")
    note: Optional[str] = Field(None, description="Note aggiuntive")
    confermato_da_ruolo: Optional[str] = Field(None, description="Ruolo che conferma il nesting")


class NestingParameters(BaseModel):
    """Schema per i parametri regolabili dell'algoritmo di nesting"""
    distanza_minima_tool_cm: float = Field(
        default=2.0, 
        ge=0.1, 
        le=10.0,
        description="Distanza minima tra tool in centimetri"
    )
    padding_bordo_autoclave_cm: float = Field(
        default=1.5, 
        ge=0.1, 
        le=5.0,
        description="Padding dal bordo dell'autoclave in centimetri"
    )
    margine_sicurezza_peso_percent: float = Field(
        default=10.0, 
        ge=0.0, 
        le=50.0,
        description="Margine di sicurezza per il peso in percentuale"
    )
    priorita_minima: int = Field(
        default=1, 
        ge=1, 
        le=10,
        description="Priorità minima degli ODL da considerare"
    )
    efficienza_minima_percent: float = Field(
        default=60.0, 
        ge=30.0, 
        le=95.0,
        description="Efficienza minima richiesta per accettare un nesting"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "distanza_minima_tool_cm": 2.0,
                "padding_bordo_autoclave_cm": 1.5,
                "margine_sicurezza_peso_percent": 10.0,
                "priorita_minima": 1,
                "efficienza_minima_percent": 60.0
            }
        }


class NestingParametersResponse(BaseModel):
    """Risposta per i parametri di nesting"""
    success: bool = Field(..., description="Indica se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio descrittivo")
    parameters: NestingParameters = Field(..., description="Parametri attuali")


class AutomaticNestingRequestWithParams(AutomaticNestingRequest):
    """Schema esteso per la richiesta di nesting automatico con parametri personalizzati"""
    parameters: Optional[NestingParameters] = Field(
        None, 
        description="Parametri personalizzati per l'algoritmo di nesting"
    )


# ✅ NUOVO: Schema per la visualizzazione grafica del nesting
class ToolPosition(BaseModel):
    """Posizione di un tool nel layout del nesting"""
    odl_id: int = Field(..., description="ID dell'ODL")
    x: float = Field(..., description="Posizione X in mm")
    y: float = Field(..., description="Posizione Y in mm")
    width: float = Field(..., description="Larghezza del tool in mm")
    height: float = Field(..., description="Altezza del tool in mm")
    rotated: bool = Field(False, description="Se il tool è ruotato di 90°")
    piano: int = Field(1, description="Piano dell'autoclave (1 o 2)")


class ToolDetailInfo(BaseModel):
    """Informazioni dettagliate di un tool per il layout"""
    id: int = Field(..., description="ID del tool")
    part_number_tool: str = Field(..., description="Part number del tool")
    descrizione: Optional[str] = Field(None, description="Descrizione del tool")
    lunghezza_piano: float = Field(..., description="Lunghezza del piano in mm")
    larghezza_piano: float = Field(..., description="Larghezza del piano in mm")
    peso: Optional[float] = Field(None, description="Peso del tool in kg")
    materiale: Optional[str] = Field(None, description="Materiale del tool")
    orientamento_preferito: Optional[str] = Field(None, description="Orientamento preferito")


class ParteDetailInfo(BaseModel):
    """Informazioni dettagliate di una parte per il layout"""
    id: int = Field(..., description="ID della parte")
    part_number: str = Field(..., description="Part number della parte")
    descrizione_breve: str = Field(..., description="Descrizione breve")
    num_valvole_richieste: int = Field(..., description="Numero di valvole richieste")
    area_cm2: Optional[float] = Field(None, description="Area in cm²")


class ODLLayoutInfo(BaseModel):
    """Informazioni di un ODL per il layout del nesting"""
    id: int = Field(..., description="ID dell'ODL")
    priorita: int = Field(..., description="Priorità dell'ODL")
    parte: ParteDetailInfo = Field(..., description="Informazioni della parte")
    tool: ToolDetailInfo = Field(..., description="Informazioni del tool")


class AutoclaveLayoutInfo(BaseModel):
    """Informazioni di un'autoclave per il layout"""
    id: int = Field(..., description="ID dell'autoclave")
    nome: str = Field(..., description="Nome dell'autoclave")
    codice: str = Field(..., description="Codice dell'autoclave")
    lunghezza: float = Field(..., description="Lunghezza in mm")
    larghezza_piano: float = Field(..., description="Larghezza del piano in mm")
    temperatura_max: float = Field(..., description="Temperatura massima")
    num_linee_vuoto: int = Field(..., description="Numero di linee vuoto")


class NestingLayoutData(BaseModel):
    """Dati completi per la visualizzazione del layout di un nesting"""
    id: int = Field(..., description="ID del nesting")
    autoclave: AutoclaveLayoutInfo = Field(..., description="Informazioni dell'autoclave")
    odl_list: List[ODLLayoutInfo] = Field(..., description="Lista degli ODL nel nesting")
    posizioni_tool: List[ToolPosition] = Field(..., description="Posizioni dei tool nel layout")
    area_utilizzata: float = Field(..., description="Area utilizzata in cm²")
    area_totale: float = Field(..., description="Area totale disponibile in cm²")
    valvole_utilizzate: int = Field(..., description="Numero di valvole utilizzate")
    valvole_totali: int = Field(..., description="Numero totale di valvole")
    stato: str = Field(..., description="Stato del nesting")
    ciclo_cura_nome: Optional[str] = Field(None, description="Nome del ciclo di cura")
    created_at: datetime = Field(..., description="Data di creazione")
    note: Optional[str] = Field(None, description="Note aggiuntive")
    padding_mm: float = Field(10.0, description="Padding tra tool in mm")
    borda_mm: float = Field(20.0, description="Bordo dall'autoclave in mm")
    rotazione_abilitata: bool = Field(True, description="Se la rotazione è abilitata")


class MultiNestingLayoutData(BaseModel):
    """Dati per la visualizzazione di più nesting"""
    nesting_list: List[NestingLayoutData] = Field(..., description="Lista dei nesting")
    statistiche_globali: Dict[str, Any] = Field(..., description="Statistiche aggregate")


class OrientationCalculationRequest(BaseModel):
    """Richiesta per il calcolo dell'orientamento ottimale"""
    tool_length: float = Field(..., description="Lunghezza del tool in mm")
    tool_width: float = Field(..., description="Larghezza del tool in mm")
    autoclave_length: float = Field(..., description="Lunghezza dell'autoclave in mm")
    autoclave_width: float = Field(..., description="Larghezza dell'autoclave in mm")


class OrientationCalculationResponse(BaseModel):
    """Risposta del calcolo dell'orientamento ottimale"""
    should_rotate: bool = Field(..., description="Se il tool dovrebbe essere ruotato")
    normal_efficiency: float = Field(..., description="Efficienza orientamento normale")
    rotated_efficiency: float = Field(..., description="Efficienza orientamento ruotato")
    improvement_percentage: float = Field(..., description="Miglioramento percentuale")
    recommended_orientation: str = Field(..., description="Orientamento raccomandato")


class NestingLayoutResponse(BaseModel):
    """Risposta per i dati di layout del nesting"""
    success: bool = Field(..., description="Indica se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio descrittivo")
    layout_data: Optional[NestingLayoutData] = Field(None, description="Dati del layout")


class MultiNestingLayoutResponse(BaseModel):
    """Risposta per i dati di layout di più nesting"""
    success: bool = Field(..., description="Indica se l'operazione è riuscita")
    message: str = Field(..., description="Messaggio descrittivo")
    layout_data: Optional[MultiNestingLayoutData] = Field(None, description="Dati dei layout") 