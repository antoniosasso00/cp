"""
Servizio di logging per i batch nesting.
Gestisce la registrazione degli eventi e delle transizioni di stato dei batch.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.batch_history import BatchHistory
from models.system_log import SystemLog, EventType, LogLevel, UserRole
from services.system_log_service import SystemLogService

logger = logging.getLogger(__name__)

class BatchLogService:
    """
    Servizio per la gestione dei log e dello storico dei batch nesting.
    Registra eventi, transizioni di stato e crea record storici.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.system_log_service = SystemLogService(db)
    
    def log_event(self, batch_id: str, action: str, meta: Dict[str, Any] = None,
                  user_id: str = None, user_role: str = None) -> bool:
        """
        Registra un evento per un batch nesting.
        
        Args:
            batch_id: ID del batch per cui registrare l'evento
            action: Descrizione dell'azione/evento
            meta: Metadati aggiuntivi dell'evento (opzionale)
            user_id: ID dell'utente che ha scatenato l'evento (opzionale)
            user_role: Ruolo dell'utente (opzionale)
            
        Returns:
            bool: True se l'evento è stato registrato con successo
        """
        try:
            # Verifica che il batch esista
            batch = self.db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
            if not batch:
                logger.error(f"Tentativo di log per batch inesistente: {batch_id}")
                return False
            
            # Prepara i dettagli dell'evento
            event_details = {
                "batch_id": batch_id,
                "batch_nome": batch.nome,
                "stato_attuale": batch.stato,
                "autoclave_id": batch.autoclave_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Aggiungi metadati se forniti
            if meta:
                event_details.update(meta)
            
            # Determina il livello di log basandosi sull'azione
            log_level = self._determine_log_level(action)
            event_type = self._determine_event_type(action)
            
            # Registra nel sistema di log
            self.system_log_service.log_event(
                event_type=event_type,
                level=log_level,
                action=action,
                details=str(event_details),
                entity_type="batch_nesting",
                entity_id=batch_id,
                user_id=user_id,
                user_role=user_role or UserRole.SYSTEM.value
            )
            
            logger.info(f"Evento registrato per batch {batch_id}: {action}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Errore database durante log evento batch {batch_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Errore imprevisto durante log evento batch {batch_id}: {str(e)}")
            return False
    
    def log_state_transition(self, batch_id: str, old_state: str, new_state: str,
                           user_id: str = None, user_role: str = None,
                           reason: str = None) -> bool:
        """
        Registra una transizione di stato per un batch.
        
        Args:
            batch_id: ID del batch
            old_state: Stato precedente
            new_state: Nuovo stato
            user_id: ID dell'utente che ha causato la transizione
            user_role: Ruolo dell'utente
            reason: Motivo della transizione (opzionale)
            
        Returns:
            bool: True se la transizione è stata registrata con successo
        """
        meta = {
            "stato_precedente": old_state,
            "stato_nuovo": new_state,
            "motivo": reason or "Non specificato"
        }
        
        action = f"Transizione stato: {old_state} → {new_state}"
        
        return self.log_event(
            batch_id=batch_id,
            action=action,
            meta=meta,
            user_id=user_id,
            user_role=user_role
        )
    
    def create_history_record(self, batch_id: str, user_id: str = None,
                            user_role: str = None, additional_data: Dict[str, Any] = None) -> Optional[BatchHistory]:
        """
        Crea un record storico quando un batch viene completato (stato "cured").
        
        Args:
            batch_id: ID del batch completato
            user_id: ID dell'utente che ha completato il batch
            user_role: Ruolo dell'utente
            additional_data: Dati aggiuntivi da salvare nello storico
            
        Returns:
            BatchHistory: Record storico creato o None se fallito
        """
        try:
            # Recupera il batch
            batch = self.db.query(BatchNesting).filter(BatchNesting.id == batch_id).first()
            if not batch:
                logger.error(f"Batch non trovato per creazione storico: {batch_id}")
                return None
            
            # Verifica che il batch sia nello stato corretto
            if batch.stato != StatoBatchNestingEnum.CURED.value:
                logger.warning(f"Creazione storico per batch non in stato 'cured': {batch_id}")
            
            # Calcola efficienza reale (placeholder per ora)
            efficienza_reale = self._calculate_real_efficiency(batch, additional_data)
            
            # Crea il record storico
            history_record = BatchHistory(
                batch_id=batch_id,
                nome_batch=batch.nome,
                autoclave_id=batch.autoclave_id,
                autoclave_nome=batch.autoclave.nome if batch.autoclave else None,
                efficienza_teorica=batch.efficiency,
                efficienza_reale=efficienza_reale,
                peso_caricato_kg=batch.peso_totale_kg,
                area_utilizzata_cm2=batch.area_totale_utilizzata,
                valvole_utilizzate=batch.valvole_totali_utilizzate,
                numero_odl_completati=len(batch.odl_ids) if batch.odl_ids else 0,
                data_conferma=batch.data_conferma,
                data_fine_cura=batch.data_completamento,
                durata_cura_minuti=batch.durata_ciclo_minuti,
                configurazione_layout=batch.configurazione_json,
                parametri_cura=batch.parametri,
                odl_dettagli=self._extract_odl_details(batch),
                creato_da_utente=user_id,
                creato_da_ruolo=user_role
            )
            
            # Aggiungi dati aggiuntivi se forniti
            if additional_data:
                if 'peso_caricato_kg' in additional_data:
                    history_record.peso_caricato_kg = additional_data['peso_caricato_kg']
                if 'temperatura_max_raggiunta' in additional_data:
                    history_record.temperatura_max_raggiunta = additional_data['temperatura_max_raggiunta']
                if 'pressione_max_raggiunta' in additional_data:
                    history_record.pressione_max_raggiunta = additional_data['pressione_max_raggiunta']
                if 'note_operatore' in additional_data:
                    history_record.note_operatore = additional_data['note_operatore']
                if 'anomalie_rilevate' in additional_data:
                    history_record.anomalie_rilevate = additional_data['anomalie_rilevate']
                if 'eventi_critici' in additional_data:
                    history_record.eventi_critici = additional_data['eventi_critici']
            
            # Salva nel database
            self.db.add(history_record)
            self.db.commit()
            self.db.refresh(history_record)
            
            # Log dell'evento
            self.log_event(
                batch_id=batch_id,
                action="Creato record storico",
                meta={
                    "history_id": history_record.id,
                    "efficienza_teorica": batch.efficiency,
                    "efficienza_reale": efficienza_reale
                },
                user_id=user_id,
                user_role=user_role
            )
            
            logger.info(f"Record storico creato per batch {batch_id}: ID {history_record.id}")
            return history_record
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Errore database durante creazione storico batch {batch_id}: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Errore imprevisto durante creazione storico batch {batch_id}: {str(e)}")
            return None
    
    def get_batch_history(self, batch_id: str) -> List[BatchHistory]:
        """
        Recupera tutti i record storici per un batch.
        
        Args:
            batch_id: ID del batch
            
        Returns:
            Lista dei record storici
        """
        try:
            return self.db.query(BatchHistory).filter(
                BatchHistory.batch_id == batch_id
            ).order_by(BatchHistory.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Errore recupero storico batch {batch_id}: {str(e)}")
            return []
    
    def get_batch_logs(self, batch_id: str, limit: int = 50) -> List[SystemLog]:
        """
        Recupera i log degli eventi per un batch.
        
        Args:
            batch_id: ID del batch
            limit: Numero massimo di log da recuperare
            
        Returns:
            Lista dei log degli eventi
        """
        try:
            return self.db.query(SystemLog).filter(
                SystemLog.entity_type == "batch_nesting",
                SystemLog.entity_id == batch_id
            ).order_by(SystemLog.timestamp.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Errore recupero log batch {batch_id}: {str(e)}")
            return []
    
    # ==================== METODI PRIVATI ====================
    
    def _determine_log_level(self, action: str) -> LogLevel:
        """Determina il livello di log basandosi sull'azione"""
        critical_actions = ["Errore critico", "Fallimento", "Timeout"]
        warning_actions = ["Transizione stato", "Anomalia", "Esclusione ODL"]
        
        action_lower = action.lower()
        
        if any(critical in action_lower for critical in ["errore", "fallimento", "timeout"]):
            return LogLevel.ERROR
        elif any(warning in action_lower for warning in ["anomalia", "esclusione", "avviso"]):
            return LogLevel.WARNING
        else:
            return LogLevel.INFO
    
    def _determine_event_type(self, action: str) -> EventType:
        """Determina il tipo di evento basandosi sull'azione"""
        action_lower = action.lower()
        
        if "crea" in action_lower:
            return EventType.CREATE
        elif "aggiorna" in action_lower or "modifica" in action_lower:
            return EventType.UPDATE
        elif "elimina" in action_lower or "cancella" in action_lower:
            return EventType.DELETE
        elif "transizione" in action_lower or "stato" in action_lower:
            return EventType.STATE_CHANGE
        else:
            return EventType.OPERATION
    
    def _calculate_real_efficiency(self, batch: BatchNesting, additional_data: Dict[str, Any] = None) -> float:
        """
        Calcola l'efficienza reale del batch (placeholder per ora).
        In futuro integrerà dati reali dall'autoclave.
        """
        # TODO: Implementare calcolo efficienza reale basato su:
        # - Peso effettivo caricato vs peso teorico
        # - Area effettiva utilizzata vs area pianificata  
        # - Tempo ciclo reale vs tempo stimato
        # - Successo/fallimento ODL individuali
        
        # Per ora ritorna l'efficienza teorica con una leggera variazione
        base_efficiency = batch.efficiency
        
        if additional_data and 'peso_caricato_kg' in additional_data:
            peso_reale = additional_data['peso_caricato_kg']
            peso_teorico = batch.peso_totale_kg
            
            if peso_teorico > 0:
                peso_ratio = peso_reale / peso_teorico
                # Aggiusta l'efficienza in base al rapporto peso reale/teorico
                efficiency_adjustment = (peso_ratio - 1.0) * 10  # ±10% per ogni 10% di differenza peso
                base_efficiency += efficiency_adjustment
        
        # Limita tra 0 e 100
        return max(0.0, min(100.0, base_efficiency))
    
    def _extract_odl_details(self, batch: BatchNesting) -> List[Dict[str, Any]]:
        """Estrae i dettagli degli ODL per lo storico"""
        odl_details = []
        
        if batch.odl_ids:
            # TODO: Recuperare dettagli ODL dal database
            # Per ora restituisce una struttura base
            for odl_id in batch.odl_ids:
                odl_details.append({
                    "odl_id": odl_id,
                    "status": "completed",  # Placeholder
                    "success": True  # Placeholder
                })
        
        return odl_details 