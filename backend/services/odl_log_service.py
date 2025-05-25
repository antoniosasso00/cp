import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from models.odl import ODL
from models.odl_log import ODLLog
from models.nesting_result import NestingResult
from models.autoclave import Autoclave
from models.schedule_entry import ScheduleEntry
from schemas.odl_monitoring import ODLLogCreate

logger = logging.getLogger(__name__)

class ODLLogService:
    """Servizio per la gestione dei log degli ODL"""
    
    # Mapping degli eventi standard
    EVENTI_STANDARD = {
        "creato": "ODL creato nel sistema",
        "assegnato_nesting": "ODL assegnato a un nesting",
        "caricato_autoclave": "ODL caricato in autoclave",
        "avvio_cura": "Avviato ciclo di cura",
        "completato_cura": "Completato ciclo di cura",
        "finito": "ODL completato",
        "bloccato": "ODL bloccato",
        "sbloccato": "ODL sbloccato",
        "priorita_modificata": "Priorità ODL modificata",
        "note_aggiornate": "Note ODL aggiornate"
    }
    
    @staticmethod
    def crea_log_evento(
        db: Session,
        odl_id: int,
        evento: str,
        stato_nuovo: str,
        stato_precedente: Optional[str] = None,
        descrizione: Optional[str] = None,
        responsabile: Optional[str] = "Sistema",
        nesting_id: Optional[int] = None,
        autoclave_id: Optional[int] = None,
        schedule_entry_id: Optional[int] = None
    ) -> ODLLog:
        """
        Crea un nuovo log evento per un ODL
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
            evento: Tipo di evento
            stato_nuovo: Nuovo stato dell'ODL
            stato_precedente: Stato precedente (opzionale)
            descrizione: Descrizione dettagliata (opzionale)
            responsabile: Responsabile dell'evento
            nesting_id: ID del nesting associato (opzionale)
            autoclave_id: ID dell'autoclave (opzionale)
            schedule_entry_id: ID della schedulazione (opzionale)
        
        Returns:
            ODLLog: Il log creato
        """
        try:
            # Se non è fornita una descrizione, usa quella standard
            if not descrizione and evento in ODLLogService.EVENTI_STANDARD:
                descrizione = ODLLogService.EVENTI_STANDARD[evento]
            
            log_data = ODLLogCreate(
                odl_id=odl_id,
                evento=evento,
                stato_precedente=stato_precedente,
                stato_nuovo=stato_nuovo,
                descrizione=descrizione,
                responsabile=responsabile,
                nesting_id=nesting_id,
                autoclave_id=autoclave_id,
                schedule_entry_id=schedule_entry_id
            )
            
            db_log = ODLLog(**log_data.model_dump())
            db.add(db_log)
            db.commit()
            db.refresh(db_log)
            
            logger.info(f"Creato log evento '{evento}' per ODL {odl_id}")
            return db_log
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore durante la creazione del log per ODL {odl_id}: {str(e)}")
            raise
    
    @staticmethod
    def log_cambio_stato(
        db: Session,
        odl_id: int,
        stato_precedente: str,
        stato_nuovo: str,
        responsabile: Optional[str] = "Sistema",
        descrizione_aggiuntiva: Optional[str] = None
    ) -> ODLLog:
        """
        Registra un cambio di stato dell'ODL
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
            stato_precedente: Stato precedente
            stato_nuovo: Nuovo stato
            responsabile: Responsabile del cambio
            descrizione_aggiuntiva: Descrizione aggiuntiva
        
        Returns:
            ODLLog: Il log creato
        """
        evento = f"cambio_stato_{stato_nuovo.lower().replace(' ', '_')}"
        descrizione = f"Cambio stato da '{stato_precedente}' a '{stato_nuovo}'"
        
        if descrizione_aggiuntiva:
            descrizione += f". {descrizione_aggiuntiva}"
        
        return ODLLogService.crea_log_evento(
            db=db,
            odl_id=odl_id,
            evento=evento,
            stato_nuovo=stato_nuovo,
            stato_precedente=stato_precedente,
            descrizione=descrizione,
            responsabile=responsabile
        )
    
    @staticmethod
    def log_assegnazione_nesting(
        db: Session,
        odl_id: int,
        nesting_id: int,
        autoclave_id: int,
        responsabile: Optional[str] = "Sistema"
    ) -> ODLLog:
        """
        Registra l'assegnazione di un ODL a un nesting
        """
        # Ottieni informazioni sull'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
        autoclave_nome = autoclave.nome if autoclave else f"Autoclave {autoclave_id}"
        
        descrizione = f"ODL assegnato al nesting {nesting_id} per autoclave {autoclave_nome}"
        
        return ODLLogService.crea_log_evento(
            db=db,
            odl_id=odl_id,
            evento="assegnato_nesting",
            stato_nuovo="In Nesting",
            descrizione=descrizione,
            responsabile=responsabile,
            nesting_id=nesting_id,
            autoclave_id=autoclave_id
        )
    
    @staticmethod
    def log_avvio_schedulazione(
        db: Session,
        odl_id: int,
        schedule_entry_id: int,
        responsabile: Optional[str] = "Sistema"
    ) -> ODLLog:
        """
        Registra l'avvio di una schedulazione per un ODL
        """
        schedule_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == schedule_entry_id).first()
        
        descrizione = f"Avviata schedulazione {schedule_entry_id}"
        if schedule_entry and schedule_entry.autoclave:
            descrizione += f" su autoclave {schedule_entry.autoclave.nome}"
        
        return ODLLogService.crea_log_evento(
            db=db,
            odl_id=odl_id,
            evento="avvio_cura",
            stato_nuovo="Cura",
            descrizione=descrizione,
            responsabile=responsabile,
            schedule_entry_id=schedule_entry_id,
            autoclave_id=schedule_entry.autoclave_id if schedule_entry else None
        )
    
    @staticmethod
    def ottieni_logs_odl(
        db: Session,
        odl_id: int,
        limit: Optional[int] = None
    ) -> List[ODLLog]:
        """
        Ottiene i log di un ODL ordinati per timestamp decrescente
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
            limit: Limite numero di log da restituire
        
        Returns:
            List[ODLLog]: Lista dei log
        """
        query = db.query(ODLLog).filter(ODLLog.odl_id == odl_id).order_by(desc(ODLLog.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def calcola_tempo_in_stato(
        db: Session,
        odl_id: int,
        stato: str
    ) -> Optional[int]:
        """
        Calcola il tempo trascorso in un determinato stato (in minuti)
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
            stato: Stato per cui calcolare il tempo
        
        Returns:
            Optional[int]: Minuti trascorsi nello stato, None se non trovato
        """
        try:
            # Trova l'ultimo log di ingresso nello stato
            log_ingresso = db.query(ODLLog).filter(
                and_(
                    ODLLog.odl_id == odl_id,
                    ODLLog.stato_nuovo == stato
                )
            ).order_by(desc(ODLLog.timestamp)).first()
            
            if not log_ingresso:
                return None
            
            # Trova il log di uscita dallo stato (se esiste)
            log_uscita = db.query(ODLLog).filter(
                and_(
                    ODLLog.odl_id == odl_id,
                    ODLLog.stato_precedente == stato,
                    ODLLog.timestamp > log_ingresso.timestamp
                )
            ).order_by(ODLLog.timestamp).first()
            
            # Calcola il tempo
            fine = log_uscita.timestamp if log_uscita else datetime.now()
            delta = fine - log_ingresso.timestamp
            
            return int(delta.total_seconds() / 60)
            
        except Exception as e:
            logger.error(f"Errore nel calcolo tempo in stato per ODL {odl_id}: {str(e)}")
            return None
    
    @staticmethod
    def calcola_tempo_totale_produzione(
        db: Session,
        odl_id: int
    ) -> Optional[int]:
        """
        Calcola il tempo totale di produzione dell'ODL (dalla creazione al completamento)
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
        
        Returns:
            Optional[int]: Minuti totali di produzione, None se non completato
        """
        try:
            # Trova il log di creazione
            log_creazione = db.query(ODLLog).filter(
                and_(
                    ODLLog.odl_id == odl_id,
                    ODLLog.evento == "creato"
                )
            ).order_by(ODLLog.timestamp).first()
            
            # Trova il log di completamento
            log_completamento = db.query(ODLLog).filter(
                and_(
                    ODLLog.odl_id == odl_id,
                    ODLLog.stato_nuovo == "Finito"
                )
            ).order_by(desc(ODLLog.timestamp)).first()
            
            if not log_creazione:
                return None
            
            # Se non è completato, calcola fino ad ora
            fine = log_completamento.timestamp if log_completamento else datetime.now()
            delta = fine - log_creazione.timestamp
            
            return int(delta.total_seconds() / 60)
            
        except Exception as e:
            logger.error(f"Errore nel calcolo tempo totale per ODL {odl_id}: {str(e)}")
            return None
    
    @staticmethod
    def genera_logs_mancanti_per_odl_esistenti(db: Session) -> int:
        """
        Genera log di creazione per ODL esistenti che non hanno log
        
        Args:
            db: Sessione database
        
        Returns:
            int: Numero di log creati
        """
        try:
            # Trova ODL senza log
            odl_senza_log = db.query(ODL).filter(
                ~ODL.id.in_(
                    db.query(ODLLog.odl_id).distinct()
                )
            ).all()
            
            logs_creati = 0
            
            for odl in odl_senza_log:
                # Crea log di creazione con timestamp dell'ODL
                log = ODLLog(
                    odl_id=odl.id,
                    evento="creato",
                    stato_nuovo=odl.status,
                    descrizione="Log di creazione generato automaticamente",
                    responsabile="Sistema",
                    timestamp=odl.created_at
                )
                
                db.add(log)
                logs_creati += 1
            
            if logs_creati > 0:
                db.commit()
                logger.info(f"Generati {logs_creati} log di creazione per ODL esistenti")
            
            return logs_creati
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore durante la generazione dei log mancanti: {str(e)}")
            return 0 