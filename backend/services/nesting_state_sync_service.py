"""
Servizio per la sincronizzazione degli stati tra Nesting, ODL e Autoclavi.

Questo servizio garantisce la coerenza dei dati quando cambiano gli stati del nesting,
aggiornando automaticamente gli stati correlati di ODL e autoclavi.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl_log import ODLLog
from models.tempo_fase import TempoFase
from services.state_tracking_service import StateTrackingService

logger = logging.getLogger(__name__)


class NestingStateSyncService:
    """
    Servizio per la sincronizzazione automatica degli stati nel sistema nesting.
    
    Gestisce le transizioni di stato e mantiene la coerenza tra:
    - Stato del nesting
    - Stati degli ODL inclusi
    - Stato dell'autoclave associata
    - Fasi temporali degli ODL
    """
    
    # Definizione delle transizioni di stato valide
    TRANSIZIONI_VALIDE = {
        "Bozza": ["Confermato", "In sospeso"],
        "Creato": ["Confermato", "In sospeso"], 
        "In sospeso": ["Caricato", "Confermato"],
        "Confermato": ["Caricato", "In sospeso"],
        "Caricato": ["Finito", "Cura"],  # "Cura" per compatibilità
        "Cura": ["Finito"],
        "Finito": []  # Stato finale
    }
    
    @classmethod
    def validate_state_transition(cls, stato_corrente: str, nuovo_stato: str) -> bool:
        """
        Valida se una transizione di stato è permessa.
        
        Args:
            stato_corrente: Stato attuale del nesting
            nuovo_stato: Nuovo stato richiesto
            
        Returns:
            bool: True se la transizione è valida
        """
        transizioni_permesse = cls.TRANSIZIONI_VALIDE.get(stato_corrente, [])
        return nuovo_stato in transizioni_permesse
    
    @classmethod
    def get_valid_transitions(cls, stato_corrente: str) -> List[str]:
        """
        Ottiene le transizioni valide per uno stato corrente.
        
        Args:
            stato_corrente: Stato attuale del nesting
            
        Returns:
            List[str]: Lista degli stati raggiungibili
        """
        return cls.TRANSIZIONI_VALIDE.get(stato_corrente, [])
    
    @classmethod
    def sync_nesting_state_change(
        cls,
        db: Session,
        nesting: NestingResult,
        nuovo_stato: str,
        responsabile: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sincronizza il cambio di stato del nesting con ODL e autoclave.
        
        Args:
            db: Sessione del database
            nesting: Istanza del nesting da aggiornare
            nuovo_stato: Nuovo stato del nesting
            responsabile: Utente responsabile del cambio
            note: Note aggiuntive
            
        Returns:
            Dict[str, Any]: Risultato della sincronizzazione
        """
        stato_precedente = nesting.stato
        timestamp = datetime.now()
        responsabile = responsabile or "sistema"
        
        logger.info(f"🔄 Inizio sincronizzazione nesting {nesting.id}: {stato_precedente} → {nuovo_stato}")
        
        # Validazione transizione
        if not cls.validate_state_transition(stato_precedente, nuovo_stato):
            raise ValueError(
                f"Transizione non valida da '{stato_precedente}' a '{nuovo_stato}'. "
                f"Transizioni permesse: {cls.get_valid_transitions(stato_precedente)}"
            )
        
        risultato = {
            "nesting_id": nesting.id,
            "stato_precedente": stato_precedente,
            "nuovo_stato": nuovo_stato,
            "odl_aggiornati": [],
            "autoclave_aggiornata": False,
            "fasi_temporali_aggiornate": [],
            "errori": []
        }
        
        try:
            # 1. Aggiorna stato del nesting
            nesting.stato = nuovo_stato
            
            # 2. Sincronizzazione specifica per stato
            if nuovo_stato == "Confermato":
                risultato.update(cls._sync_stato_confermato(db, nesting, responsabile, timestamp))
                
            elif nuovo_stato in ["Caricato", "Cura"]:
                risultato.update(cls._sync_stato_caricato(db, nesting, responsabile, timestamp))
                
            elif nuovo_stato == "Finito":
                risultato.update(cls._sync_stato_finito(db, nesting, responsabile, timestamp))
            
            logger.info(f"✅ Sincronizzazione nesting {nesting.id} completata con successo")
            
        except Exception as e:
            logger.error(f"❌ Errore durante sincronizzazione nesting {nesting.id}: {str(e)}")
            risultato["errori"].append(str(e))
            raise
        
        return risultato
    
    @classmethod
    def _sync_stato_confermato(
        cls,
        db: Session,
        nesting: NestingResult,
        responsabile: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Sincronizzazione per stato 'Confermato'."""
        logger.info(f"🔄 Nesting {nesting.id} confermato - verifica ODL in 'Attesa Cura'")
        
        risultato = {"odl_verificati": [], "odl_non_validi": []}
        
        # Verifica che tutti gli ODL siano in "Attesa Cura"
        if nesting.odl_ids:
            odl_inclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids)).all()
            
            for odl in odl_inclusi:
                if odl.status != "Attesa Cura":
                    risultato["odl_non_validi"].append({
                        "id": odl.id,
                        "stato_attuale": odl.status,
                        "stato_richiesto": "Attesa Cura"
                    })
                else:
                    risultato["odl_verificati"].append(odl.id)
            
            if risultato["odl_non_validi"]:
                raise ValueError(
                    f"Gli ODL {[odl['id'] for odl in risultato['odl_non_validi']]} "
                    f"non sono in stato 'Attesa Cura'"
                )
        
        return risultato
    
    @classmethod
    def _sync_stato_caricato(
        cls,
        db: Session,
        nesting: NestingResult,
        responsabile: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Sincronizzazione per stato 'Caricato' o 'Cura'."""
        logger.info(f"🔄 Nesting {nesting.id} caricato - sincronizzazione ODL e autoclave")
        
        risultato = {
            "odl_aggiornati": [],
            "autoclave_aggiornata": False,
            "fasi_temporali_aggiornate": []
        }
        
        # 1. Aggiorna stato autoclave
        if nesting.autoclave and nesting.autoclave.stato != StatoAutoclaveEnum.IN_USO:
            if nesting.autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
                raise ValueError(
                    f"L'autoclave '{nesting.autoclave.nome}' è nello stato "
                    f"'{nesting.autoclave.stato.value}' e non può essere utilizzata"
                )
            
            stato_precedente_autoclave = nesting.autoclave.stato
            nesting.autoclave.stato = StatoAutoclaveEnum.IN_USO
            risultato["autoclave_aggiornata"] = True
            
            logger.info(f"🏭 Autoclave {nesting.autoclave.nome}: {stato_precedente_autoclave.value} → IN_USO")
        
        # 2. Aggiorna stati ODL
        if nesting.odl_ids:
            odl_inclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids)).all()
            
            for odl in odl_inclusi:
                if odl.status != "Cura":
                    odl_result = cls._aggiorna_odl_a_cura(
                        db, odl, nesting.id, responsabile, timestamp, nesting.autoclave_id
                    )
                    risultato["odl_aggiornati"].append(odl_result)
                    risultato["fasi_temporali_aggiornate"].extend(odl_result.get("fasi_aggiornate", []))
        
        return risultato
    
    @classmethod
    def _sync_stato_finito(
        cls,
        db: Session,
        nesting: NestingResult,
        responsabile: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Sincronizzazione per stato 'Finito'."""
        logger.info(f"🔄 Nesting {nesting.id} completato - finalizzazione ODL e autoclave")
        
        risultato = {
            "odl_aggiornati": [],
            "autoclave_aggiornata": False,
            "fasi_temporali_aggiornate": []
        }
        
        # 1. Aggiorna stati ODL
        if nesting.odl_ids:
            odl_inclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids)).all()
            
            for odl in odl_inclusi:
                if odl.status != "Finito":
                    odl_result = cls._aggiorna_odl_a_finito(
                        db, odl, nesting.id, responsabile, timestamp, nesting.autoclave_id
                    )
                    risultato["odl_aggiornati"].append(odl_result)
                    risultato["fasi_temporali_aggiornate"].extend(odl_result.get("fasi_aggiornate", []))
        
        # 2. Libera autoclave
        if nesting.autoclave and nesting.autoclave.stato == StatoAutoclaveEnum.IN_USO:
            stato_precedente_autoclave = nesting.autoclave.stato
            nesting.autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
            risultato["autoclave_aggiornata"] = True
            
            logger.info(f"🏭 Autoclave {nesting.autoclave.nome}: {stato_precedente_autoclave.value} → DISPONIBILE")
        
        return risultato
    
    @classmethod
    def _aggiorna_odl_a_cura(
        cls,
        db: Session,
        odl: ODL,
        nesting_id: int,
        responsabile: str,
        timestamp: datetime,
        autoclave_id: Optional[int]
    ) -> Dict[str, Any]:
        """Aggiorna un ODL allo stato 'Cura'."""
        stato_precedente = odl.status
        odl.status = "Cura"
        odl.previous_status = stato_precedente
        
        # Registra il cambio di stato
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl.id,
            stato_precedente=stato_precedente,
            stato_nuovo="Cura",
            responsabile=responsabile,
            ruolo_responsabile="curing",
            note=f"ODL aggiornato automaticamente per nesting {nesting_id}"
        )
        
        # Crea log specifico
        odl_log = ODLLog(
            odl_id=odl.id,
            evento="stato_aggiornato_nesting",
            stato_precedente=stato_precedente,
            stato_nuovo="Cura",
            descrizione=f"Stato aggiornato automaticamente per sincronizzazione nesting {nesting_id}",
            responsabile=responsabile,
            nesting_id=nesting_id,
            autoclave_id=autoclave_id
        )
        db.add(odl_log)
        
        # Gestione fasi temporali
        fasi_aggiornate = cls._gestisci_fasi_temporali_cura(db, odl.id, timestamp, nesting_id)
        
        logger.info(f"📋 ODL {odl.id}: {stato_precedente} → Cura")
        
        return {
            "odl_id": odl.id,
            "stato_precedente": stato_precedente,
            "stato_nuovo": "Cura",
            "fasi_aggiornate": fasi_aggiornate
        }
    
    @classmethod
    def _aggiorna_odl_a_finito(
        cls,
        db: Session,
        odl: ODL,
        nesting_id: int,
        responsabile: str,
        timestamp: datetime,
        autoclave_id: Optional[int]
    ) -> Dict[str, Any]:
        """Aggiorna un ODL allo stato 'Finito'."""
        stato_precedente = odl.status
        odl.status = "Finito"
        odl.previous_status = stato_precedente
        
        # Registra il cambio di stato
        StateTrackingService.registra_cambio_stato(
            db=db,
            odl_id=odl.id,
            stato_precedente=stato_precedente,
            stato_nuovo="Finito",
            responsabile=responsabile,
            ruolo_responsabile="curing",
            note=f"ODL completato automaticamente per nesting {nesting_id}"
        )
        
        # Crea log specifico
        odl_log = ODLLog(
            odl_id=odl.id,
            evento="completato_nesting",
            stato_precedente=stato_precedente,
            stato_nuovo="Finito",
            descrizione=f"ODL completato automaticamente per finalizzazione nesting {nesting_id}",
            responsabile=responsabile,
            nesting_id=nesting_id,
            autoclave_id=autoclave_id
        )
        db.add(odl_log)
        
        # Gestione fasi temporali
        fasi_aggiornate = cls._gestisci_fasi_temporali_finito(db, odl.id, timestamp)
        
        logger.info(f"📋 ODL {odl.id}: {stato_precedente} → Finito")
        
        return {
            "odl_id": odl.id,
            "stato_precedente": stato_precedente,
            "stato_nuovo": "Finito",
            "fasi_aggiornate": fasi_aggiornate
        }
    
    @classmethod
    def _gestisci_fasi_temporali_cura(
        cls,
        db: Session,
        odl_id: int,
        timestamp: datetime,
        nesting_id: int
    ) -> List[Dict[str, Any]]:
        """Gestisce le fasi temporali per il passaggio a 'Cura'."""
        fasi_aggiornate = []
        
        # Chiudi fase "attesa_cura" se attiva
        fase_attesa = db.query(TempoFase).filter(
            TempoFase.odl_id == odl_id,
            TempoFase.fase == "attesa_cura",
            TempoFase.fine_fase == None
        ).first()
        
        if fase_attesa:
            durata = int((timestamp - fase_attesa.inizio_fase).total_seconds() / 60)
            fase_attesa.fine_fase = timestamp
            fase_attesa.durata_minuti = durata
            fase_attesa.note = f"{fase_attesa.note or ''} - Completata con caricamento nesting"
            
            fasi_aggiornate.append({
                "fase": "attesa_cura",
                "azione": "chiusa",
                "durata_minuti": durata
            })
        
        # Apri fase "cura" se non esiste
        fase_cura_esistente = db.query(TempoFase).filter(
            TempoFase.odl_id == odl_id,
            TempoFase.fase == "cura",
            TempoFase.fine_fase == None
        ).first()
        
        if not fase_cura_esistente:
            nuova_fase_cura = TempoFase(
                odl_id=odl_id,
                fase="cura",
                inizio_fase=timestamp,
                note=f"Fase cura iniziata con aggiornamento nesting {nesting_id}"
            )
            db.add(nuova_fase_cura)
            
            fasi_aggiornate.append({
                "fase": "cura",
                "azione": "aperta",
                "inizio": timestamp
            })
        
        return fasi_aggiornate
    
    @classmethod
    def _gestisci_fasi_temporali_finito(
        cls,
        db: Session,
        odl_id: int,
        timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Gestisce le fasi temporali per il passaggio a 'Finito'."""
        fasi_aggiornate = []
        
        # Chiudi fase "cura" se attiva
        fase_cura = db.query(TempoFase).filter(
            TempoFase.odl_id == odl_id,
            TempoFase.fase == "cura",
            TempoFase.fine_fase == None
        ).first()
        
        if fase_cura:
            durata = int((timestamp - fase_cura.inizio_fase).total_seconds() / 60)
            fase_cura.fine_fase = timestamp
            fase_cura.durata_minuti = durata
            fase_cura.note = f"{fase_cura.note or ''} - Completata con finalizzazione nesting"
            
            fasi_aggiornate.append({
                "fase": "cura",
                "azione": "chiusa",
                "durata_minuti": durata
            })
        
        return fasi_aggiornate 