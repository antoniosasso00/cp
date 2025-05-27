import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.odl import ODL
from models.state_log import StateLog
from models.system_log import UserRole

logger = logging.getLogger(__name__)

class StateTrackingService:
    """
    Servizio dedicato al tracciamento preciso dei cambi di stato degli ODL.
    
    Questo servizio gestisce:
    - Registrazione timestamp precisi per ogni cambio di stato
    - Validazione delle transizioni di stato
    - Calcolo dei tempi di permanenza in ogni stato
    - Generazione di timeline complete per gli ODL
    """
    
    @staticmethod
    def registra_cambio_stato(
        db: Session,
        odl_id: int,
        stato_precedente: Optional[str],
        stato_nuovo: str,
        responsabile: Optional[str] = None,
        ruolo_responsabile: Optional[str] = None,
        note: Optional[str] = None
    ) -> StateLog:
        """
        Registra un cambio di stato per un ODL con timestamp preciso.
        
        Args:
            db: Sessione del database
            odl_id: ID dell'ODL
            stato_precedente: Stato precedente (None per creazione)
            stato_nuovo: Nuovo stato
            responsabile: Utente responsabile del cambio
            ruolo_responsabile: Ruolo dell'utente (clean_room, curing, admin)
            note: Note aggiuntive
            
        Returns:
            StateLog: Record del cambio di stato creato
        """
        try:
            # Crea il record di cambio stato
            state_log = StateLog(
                odl_id=odl_id,
                stato_precedente=stato_precedente,
                stato_nuovo=stato_nuovo,
                timestamp=datetime.now(),
                responsabile=responsabile,
                ruolo_responsabile=ruolo_responsabile,
                note=note
            )
            
            db.add(state_log)
            db.flush()  # Per ottenere l'ID
            
            logger.info(f"✅ Registrato cambio stato ODL {odl_id}: '{stato_precedente}' → '{stato_nuovo}' da {responsabile or 'sistema'}")
            
            return state_log
            
        except Exception as e:
            logger.error(f"❌ Errore nella registrazione cambio stato ODL {odl_id}: {str(e)}")
            raise
    
    @staticmethod
    def ottieni_timeline_stati(db: Session, odl_id: int) -> List[Dict[str, Any]]:
        """
        Ottiene la timeline completa dei cambi di stato per un ODL.
        
        Args:
            db: Sessione del database
            odl_id: ID dell'ODL
            
        Returns:
            Lista di dizionari con informazioni sui cambi di stato
        """
        try:
            # Recupera tutti i cambi di stato ordinati per timestamp
            state_logs = db.query(StateLog).filter(
                StateLog.odl_id == odl_id
            ).order_by(StateLog.timestamp.asc()).all()
            
            timeline = []
            
            for i, log in enumerate(state_logs):
                # Calcola la durata nello stato precedente
                durata_minuti = None
                if i > 0:
                    durata_delta = log.timestamp - state_logs[i-1].timestamp
                    durata_minuti = int(durata_delta.total_seconds() / 60)
                
                timeline.append({
                    "id": log.id,
                    "stato_precedente": log.stato_precedente,
                    "stato_nuovo": log.stato_nuovo,
                    "timestamp": log.timestamp,
                    "responsabile": log.responsabile,
                    "ruolo_responsabile": log.ruolo_responsabile,
                    "note": log.note,
                    "durata_stato_precedente_minuti": durata_minuti
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"❌ Errore nel recupero timeline ODL {odl_id}: {str(e)}")
            return []
    
    @staticmethod
    def calcola_tempo_in_stato_corrente(db: Session, odl_id: int) -> Optional[int]:
        """
        Calcola il tempo trascorso nello stato corrente in minuti.
        
        Args:
            db: Sessione del database
            odl_id: ID dell'ODL
            
        Returns:
            Tempo in minuti nello stato corrente, None se non trovato
        """
        try:
            # Trova l'ultimo cambio di stato
            ultimo_cambio = db.query(StateLog).filter(
                StateLog.odl_id == odl_id
            ).order_by(StateLog.timestamp.desc()).first()
            
            if not ultimo_cambio:
                return None
            
            # Calcola la differenza con ora corrente
            ora_corrente = datetime.now()
            durata_delta = ora_corrente - ultimo_cambio.timestamp
            durata_minuti = int(durata_delta.total_seconds() / 60)
            
            return durata_minuti
            
        except Exception as e:
            logger.error(f"❌ Errore nel calcolo tempo stato corrente ODL {odl_id}: {str(e)}")
            return None
    
    @staticmethod
    def calcola_tempo_totale_produzione(db: Session, odl_id: int) -> Optional[int]:
        """
        Calcola il tempo totale di produzione dall'inizio alla fine.
        
        Args:
            db: Sessione del database
            odl_id: ID dell'ODL
            
        Returns:
            Tempo totale in minuti, None se non completato
        """
        try:
            # Trova il primo e ultimo cambio di stato
            primo_cambio = db.query(StateLog).filter(
                StateLog.odl_id == odl_id
            ).order_by(StateLog.timestamp.asc()).first()
            
            ultimo_cambio = db.query(StateLog).filter(
                StateLog.odl_id == odl_id
            ).order_by(StateLog.timestamp.desc()).first()
            
            if not primo_cambio or not ultimo_cambio:
                return None
            
            # Se l'ODL è finito, calcola il tempo totale
            if ultimo_cambio.stato_nuovo == "Finito":
                durata_delta = ultimo_cambio.timestamp - primo_cambio.timestamp
                durata_minuti = int(durata_delta.total_seconds() / 60)
                return durata_minuti
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Errore nel calcolo tempo totale produzione ODL {odl_id}: {str(e)}")
            return None
    
    @staticmethod
    def ottieni_statistiche_stati(db: Session, odl_id: int) -> Dict[str, Any]:
        """
        Ottiene statistiche dettagliate sui tempi di permanenza in ogni stato.
        
        Args:
            db: Sessione del database
            odl_id: ID dell'ODL
            
        Returns:
            Dizionario con statistiche per ogni stato
        """
        try:
            timeline = StateTrackingService.ottieni_timeline_stati(db, odl_id)
            
            if not timeline:
                return {}
            
            statistiche = {}
            
            # Calcola tempo per ogni stato
            for i, evento in enumerate(timeline):
                stato = evento["stato_nuovo"]
                
                if stato not in statistiche:
                    statistiche[stato] = {
                        "tempo_totale_minuti": 0,
                        "numero_ingressi": 0,
                        "primo_ingresso": evento["timestamp"],
                        "ultimo_ingresso": evento["timestamp"]
                    }
                
                statistiche[stato]["numero_ingressi"] += 1
                statistiche[stato]["ultimo_ingresso"] = evento["timestamp"]
                
                # Calcola durata nello stato
                if i < len(timeline) - 1:
                    # Non è l'ultimo stato, calcola durata fino al prossimo cambio
                    prossimo_evento = timeline[i + 1]
                    durata_delta = prossimo_evento["timestamp"] - evento["timestamp"]
                    durata_minuti = int(durata_delta.total_seconds() / 60)
                    statistiche[stato]["tempo_totale_minuti"] += durata_minuti
                else:
                    # È l'ultimo stato, calcola durata fino ad ora (se non finito)
                    if stato != "Finito":
                        ora_corrente = datetime.now()
                        durata_delta = ora_corrente - evento["timestamp"]
                        durata_minuti = int(durata_delta.total_seconds() / 60)
                        statistiche[stato]["tempo_totale_minuti"] += durata_minuti
            
            return statistiche
            
        except Exception as e:
            logger.error(f"❌ Errore nel calcolo statistiche stati ODL {odl_id}: {str(e)}")
            return {}
    
    @staticmethod
    def valida_transizione_stato(stato_attuale: str, stato_nuovo: str, ruolo: Optional[str] = None) -> tuple[bool, str]:
        """
        Valida se una transizione di stato è permessa.
        
        Args:
            stato_attuale: Stato corrente dell'ODL
            stato_nuovo: Stato richiesto
            ruolo: Ruolo dell'utente che richiede il cambio
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        # Definisci le transizioni valide per ogni ruolo
        transizioni_clean_room = {
            "Preparazione": ["Laminazione"],
            "Laminazione": ["Attesa Cura"]
        }
        
        transizioni_curing = {
            "Attesa Cura": ["Cura"],
            "Cura": ["Finito"]
        }
        
        transizioni_admin = {
            "Preparazione": ["Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"],
            "Laminazione": ["Preparazione", "In Coda", "Attesa Cura", "Cura", "Finito"],
            "In Coda": ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"],
            "Attesa Cura": ["Preparazione", "Laminazione", "In Coda", "Cura", "Finito"],
            "Cura": ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Finito"],
            "Finito": ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura"]
        }
        
        # Seleziona le transizioni in base al ruolo
        if ruolo == "clean_room":
            transizioni_permesse = transizioni_clean_room
        elif ruolo == "curing":
            transizioni_permesse = transizioni_curing
        elif ruolo == "admin":
            transizioni_permesse = transizioni_admin
        else:
            # Ruolo generico o non specificato - usa regole admin
            transizioni_permesse = transizioni_admin
        
        # Verifica se la transizione è permessa
        if stato_attuale not in transizioni_permesse:
            return False, f"Stato '{stato_attuale}' non gestito per il ruolo {ruolo or 'generico'}"
        
        if stato_nuovo not in transizioni_permesse[stato_attuale]:
            stati_permessi = ", ".join(transizioni_permesse[stato_attuale])
            return False, f"Transizione da '{stato_attuale}' a '{stato_nuovo}' non permessa per {ruolo or 'ruolo generico'}. Stati permessi: {stati_permessi}"
        
        return True, "Transizione valida" 