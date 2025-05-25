from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enum per rappresentare i vari stati di una schedulazione
class ScheduleEntryStatusEnum(str, Enum):
    SCHEDULED = "scheduled"      # Schedulato automaticamente
    MANUAL = "manual"           # Schedulato manualmente
    PREVISIONALE = "previsionale"  # Schedulazione previsionale (da frequenza)
    IN_ATTESA = "in_attesa"     # In attesa di avvio
    IN_CORSO = "in_corso"       # In corso di esecuzione
    DONE = "done"               # Completato
    POSTICIPATO = "posticipato" # Posticipato dall'operatore

# Enum per il tipo di schedulazione
class ScheduleEntryTypeEnum(str, Enum):
    ODL_SPECIFICO = "odl_specifico"        # Schedulazione per ODL specifico
    CATEGORIA = "categoria"                # Schedulazione per categoria
    SOTTO_CATEGORIA = "sotto_categoria"    # Schedulazione per sotto-categoria
    RICORRENTE = "ricorrente"             # Schedulazione ricorrente

# Schema base per le proprietà comuni
class ScheduleEntryBase(BaseModel):
    autoclave_id: int = Field(..., description="ID dell'autoclave per cui è schedulato")
    start_datetime: datetime = Field(..., description="Data e ora di inizio della schedulazione")
    end_datetime: Optional[datetime] = Field(None, description="Data e ora di fine della schedulazione (calcolata automaticamente se disponibili dati storici)")
    priority_override: bool = Field(False, description="Indica se la priorità è stata sovrascritta manualmente")
    note: Optional[str] = Field(None, description="Note aggiuntive sulla schedulazione")

# Schema per la creazione
class ScheduleEntryCreate(ScheduleEntryBase):
    schedule_type: ScheduleEntryTypeEnum = Field(ScheduleEntryTypeEnum.ODL_SPECIFICO, description="Tipo di schedulazione")
    odl_id: Optional[int] = Field(None, description="ID dell'ODL schedulato (opzionale per schedulazioni per categoria)")
    categoria: Optional[str] = Field(None, description="Categoria per schedulazioni per categoria")
    sotto_categoria: Optional[str] = Field(None, description="Sotto-categoria per schedulazioni per sotto-categoria")
    status: ScheduleEntryStatusEnum = Field(ScheduleEntryStatusEnum.MANUAL, description="Stato corrente della schedulazione")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")
    is_recurring: bool = Field(False, description="Indica se è una schedulazione ricorrente")
    recurring_frequency: Optional[str] = Field(None, description="Frequenza ricorrenza (monthly, weekly, etc.)")
    pieces_per_month: Optional[int] = Field(None, description="Numero di pezzi da produrre al mese (per schedulazioni ricorrenti)")
    
    @validator('odl_id')
    def validate_odl_id(cls, v, values):
        schedule_type = values.get('schedule_type')
        if schedule_type == ScheduleEntryTypeEnum.ODL_SPECIFICO and v is None:
            raise ValueError('odl_id è obbligatorio per schedulazioni di tipo ODL_SPECIFICO')
        return v
    
    @validator('categoria')
    def validate_categoria(cls, v, values):
        schedule_type = values.get('schedule_type')
        if schedule_type == ScheduleEntryTypeEnum.CATEGORIA and not v:
            raise ValueError('categoria è obbligatoria per schedulazioni di tipo CATEGORIA')
        return v
    
    @validator('sotto_categoria')
    def validate_sotto_categoria(cls, v, values):
        schedule_type = values.get('schedule_type')
        if schedule_type == ScheduleEntryTypeEnum.SOTTO_CATEGORIA and not v:
            raise ValueError('sotto_categoria è obbligatoria per schedulazioni di tipo SOTTO_CATEGORIA')
        return v

# Schema per la creazione automatica
class ScheduleEntryAutoCreate(BaseModel):
    date: str = Field(..., description="Data per cui generare lo scheduling (YYYY-MM-DD)")

# Schema per la creazione di schedulazioni ricorrenti
class RecurringScheduleCreate(BaseModel):
    schedule_type: ScheduleEntryTypeEnum = Field(..., description="Tipo di schedulazione")
    autoclave_id: int = Field(..., description="ID dell'autoclave")
    categoria: Optional[str] = Field(None, description="Categoria (se tipo CATEGORIA)")
    sotto_categoria: Optional[str] = Field(None, description="Sotto-categoria (se tipo SOTTO_CATEGORIA)")
    pieces_per_month: int = Field(..., description="Numero di pezzi da produrre al mese")
    start_date: str = Field(..., description="Data di inizio (YYYY-MM-DD)")
    end_date: str = Field(..., description="Data di fine (YYYY-MM-DD)")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")

# Schema per gli aggiornamenti
class ScheduleEntryUpdate(BaseModel):
    schedule_type: Optional[ScheduleEntryTypeEnum] = Field(None, description="Tipo di schedulazione")
    odl_id: Optional[int] = Field(None, description="ID dell'ODL schedulato")
    autoclave_id: Optional[int] = Field(None, description="ID dell'autoclave")
    categoria: Optional[str] = Field(None, description="Categoria")
    sotto_categoria: Optional[str] = Field(None, description="Sotto-categoria")
    start_datetime: Optional[datetime] = Field(None, description="Data e ora di inizio della schedulazione")
    end_datetime: Optional[datetime] = Field(None, description="Data e ora di fine della schedulazione")
    status: Optional[ScheduleEntryStatusEnum] = Field(None, description="Stato corrente della schedulazione")
    priority_override: Optional[bool] = Field(None, description="Indica se la priorità è stata sovrascritta manualmente")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")
    note: Optional[str] = Field(None, description="Note aggiuntive")

# Schema per azioni dell'operatore
class ScheduleOperatorAction(BaseModel):
    action: str = Field(..., description="Azione da eseguire: 'avvia', 'posticipa', 'completa'")
    new_datetime: Optional[datetime] = Field(None, description="Nuova data/ora (per azione 'posticipa')")
    note: Optional[str] = Field(None, description="Note aggiuntive")

# Schema per ODL incluso nella risposta
class ODLInScheduleResponse(BaseModel):
    id: int = Field(..., description="ID univoco dell'ordine di lavoro")
    priorita: int = Field(..., description="Priorità dell'ordine di lavoro")
    status: str = Field(..., description="Stato corrente dell'ordine di lavoro")
    parte_id: int = Field(..., description="ID della parte associata all'ordine di lavoro")
    tool_id: int = Field(..., description="ID del tool utilizzato per l'ordine di lavoro")

    class Config:
        from_attributes = True

# Schema per Autoclave inclusa nella risposta
class AutoclaveInScheduleResponse(BaseModel):
    id: int = Field(..., description="ID univoco dell'autoclave")
    nome: str = Field(..., description="Nome identificativo dell'autoclave")
    codice: str = Field(..., description="Codice univoco dell'autoclave")
    num_linee_vuoto: int = Field(..., description="Numero di linee vuoto disponibili")

    class Config:
        from_attributes = True

# Schema per la risposta completa
class ScheduleEntryRead(ScheduleEntryBase):
    id: int = Field(..., description="ID univoco della schedulazione")
    schedule_type: ScheduleEntryTypeEnum = Field(..., description="Tipo di schedulazione")
    odl_id: Optional[int] = Field(None, description="ID dell'ODL schedulato")
    categoria: Optional[str] = Field(None, description="Categoria")
    sotto_categoria: Optional[str] = Field(None, description="Sotto-categoria")
    status: ScheduleEntryStatusEnum = Field(..., description="Stato corrente della schedulazione")
    created_by: Optional[str] = Field(None, description="Utente che ha creato la schedulazione")
    is_recurring: bool = Field(False, description="Indica se è una schedulazione ricorrente")
    pieces_per_month: Optional[int] = Field(None, description="Numero di pezzi da produrre al mese")
    estimated_duration_minutes: Optional[int] = Field(None, description="Durata stimata in minuti")
    created_at: datetime = Field(..., description="Data e ora di creazione del record")
    updated_at: datetime = Field(..., description="Data e ora dell'ultimo aggiornamento")
    odl: Optional[ODLInScheduleResponse] = Field(None, description="Informazioni sull'ODL schedulato")
    autoclave: AutoclaveInScheduleResponse = Field(..., description="Informazioni sull'autoclave")

    class Config:
        from_attributes = True

# Schema per la risposta dell'auto-generazione
class AutoScheduleResponse(BaseModel):
    schedules: List[ScheduleEntryRead] = Field(..., description="Lista delle schedulazioni generate")
    message: str = Field(..., description="Messaggio informativo sul risultato dell'operazione")
    count: int = Field(..., description="Numero di schedulazioni generate")

    class Config:
        from_attributes = True

# Schema per i tempi di produzione
class TempoProduzioneBase(BaseModel):
    part_number: Optional[str] = Field(None, description="Part number specifico")
    categoria: Optional[str] = Field(None, description="Categoria del prodotto")
    sotto_categoria: Optional[str] = Field(None, description="Sotto-categoria del prodotto")
    tempo_medio_minuti: float = Field(..., description="Tempo medio di produzione in minuti")
    tempo_minimo_minuti: Optional[float] = Field(None, description="Tempo minimo registrato")
    tempo_massimo_minuti: Optional[float] = Field(None, description="Tempo massimo registrato")
    numero_osservazioni: int = Field(1, description="Numero di osservazioni")
    note: Optional[str] = Field(None, description="Note aggiuntive")

class TempoProduzioneCreate(TempoProduzioneBase):
    pass

class TempoProduzioneRead(TempoProduzioneBase):
    id: int = Field(..., description="ID univoco")
    ultima_osservazione: datetime = Field(..., description="Data dell'ultima osservazione")
    created_at: datetime = Field(..., description="Data di creazione")
    updated_at: datetime = Field(..., description="Data di aggiornamento")

    class Config:
        from_attributes = True 