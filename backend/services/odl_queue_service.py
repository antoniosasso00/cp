"""
Servizio per la gestione automatica della coda degli ODL
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from models.odl import ODL
from models.tool import Tool
from models.parte import Parte
from schemas.odl import ODLUpdate
import logging

logger = logging.getLogger(__name__)

class ODLQueueService:
    """Servizio per gestire la coda automatica degli ODL"""
    
    @staticmethod
    def check_and_update_odl_queue(db: Session) -> List[dict]:
        """
        Controlla tutti gli ODL e aggiorna automaticamente lo stato in coda
        quando necessario
        
        Returns:
            Lista di ODL che sono stati aggiornati
        """
        updated_odls = []
        
        try:
            # Trova tutti gli ODL in stato "Laminazione" che potrebbero dover andare in coda
            odls_laminazione = db.query(ODL).filter(
                ODL.status == "Laminazione"
            ).all()
            
            for odl in odls_laminazione:
                # Controlla se tutti i tool associati alla parte sono occupati
                if ODLQueueService._are_all_tools_busy_for_parte(db, odl.parte_id, odl.id):
                    # Metti l'ODL in coda
                    motivo = ODLQueueService._get_blocking_reason(db, odl.parte_id)
                    
                    odl.status = "In Coda"
                    odl.motivo_blocco = motivo
                    
                    updated_odls.append({
                        'odl_id': odl.id,
                        'old_status': 'Laminazione',
                        'new_status': 'In Coda',
                        'motivo_blocco': motivo
                    })
                    
                    logger.info(f"ODL {odl.id} messo in coda: {motivo}")
            
            # Trova tutti gli ODL in stato "In Coda" che potrebbero poter ripartire
            odls_in_coda = db.query(ODL).filter(
                ODL.status == "In Coda"
            ).all()
            
            for odl in odls_in_coda:
                # Controlla se almeno un tool è ora disponibile
                if ODLQueueService._is_any_tool_available_for_parte(db, odl.parte_id):
                    # Rimuovi l'ODL dalla coda
                    odl.status = "Laminazione"
                    odl.motivo_blocco = None
                    
                    updated_odls.append({
                        'odl_id': odl.id,
                        'old_status': 'In Coda',
                        'new_status': 'Laminazione',
                        'motivo_blocco': None
                    })
                    
                    logger.info(f"ODL {odl.id} rimosso dalla coda - tool disponibile")
            
            # Salva le modifiche
            db.commit()
            
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento della coda ODL: {e}")
            db.rollback()
            raise e
        
        return updated_odls
    
    @staticmethod
    def _are_all_tools_busy_for_parte(db: Session, parte_id: int, current_odl_id: int) -> bool:
        """
        Controlla se tutti i tool associati a una parte sono occupati
        
        Args:
            db: Sessione database
            parte_id: ID della parte
            current_odl_id: ID dell'ODL corrente (da escludere dal controllo)
            
        Returns:
            True se tutti i tool sono occupati, False altrimenti
        """
        try:
            # Trova la parte
            parte = db.query(Parte).filter(Parte.id == parte_id).first()
            if not parte:
                return False
            
            # Ottieni tutti i tool associati alla parte
            tools_associati = parte.tools
            
            if not tools_associati:
                return False
            
            # Controlla se tutti i tool sono occupati
            for tool in tools_associati:
                # Un tool è considerato occupato se:
                # 1. Non è disponibile (disponibile = False)
                # 2. È utilizzato da un ODL attivo (diverso da quello corrente)
                
                if tool.disponibile:
                    # Controlla se il tool è utilizzato da altri ODL attivi
                    odl_attivi_con_tool = db.query(ODL).filter(
                        ODL.tool_id == tool.id,
                        ODL.id != current_odl_id,
                        ODL.status.in_(["Laminazione", "Attesa Cura", "Cura"])
                    ).count()
                    
                    if odl_attivi_con_tool == 0:
                        # Questo tool è disponibile
                        return False
            
            # Tutti i tool sono occupati
            return True
            
        except Exception as e:
            logger.error(f"Errore nel controllo disponibilità tool per parte {parte_id}: {e}")
            return False
    
    @staticmethod
    def _is_any_tool_available_for_parte(db: Session, parte_id: int) -> bool:
        """
        Controlla se almeno un tool associato a una parte è disponibile
        
        Args:
            db: Sessione database
            parte_id: ID della parte
            
        Returns:
            True se almeno un tool è disponibile, False altrimenti
        """
        return not ODLQueueService._are_all_tools_busy_for_parte(db, parte_id, -1)
    
    @staticmethod
    def _get_blocking_reason(db: Session, parte_id: int) -> str:
        """
        Genera una descrizione del motivo del blocco
        
        Args:
            db: Sessione database
            parte_id: ID della parte
            
        Returns:
            Stringa descrittiva del motivo del blocco
        """
        try:
            parte = db.query(Parte).filter(Parte.id == parte_id).first()
            if not parte:
                return "Parte non trovata"
            
            tools_associati = parte.tools
            if not tools_associati:
                return "Nessun tool associato alla parte"
            
            tool_names = [tool.part_number_tool for tool in tools_associati]
            
            if len(tool_names) == 1:
                return f"Tool {tool_names[0]} occupato"
            else:
                return f"Tutti i tool associati occupati: {', '.join(tool_names)}"
                
        except Exception as e:
            logger.error(f"Errore nella generazione del motivo di blocco: {e}")
            return "Errore nel determinare il motivo del blocco"
    
    @staticmethod
    def force_check_odl_status(db: Session, odl_id: int) -> Optional[dict]:
        """
        Forza il controllo dello stato di un singolo ODL
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL da controllare
            
        Returns:
            Dizionario con informazioni sull'aggiornamento o None se nessun cambiamento
        """
        try:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if not odl:
                return None
            
            if odl.status == "Laminazione":
                if ODLQueueService._are_all_tools_busy_for_parte(db, odl.parte_id, odl.id):
                    motivo = ODLQueueService._get_blocking_reason(db, odl.parte_id)
                    odl.status = "In Coda"
                    odl.motivo_blocco = motivo
                    db.commit()
                    
                    return {
                        'odl_id': odl.id,
                        'old_status': 'Laminazione',
                        'new_status': 'In Coda',
                        'motivo_blocco': motivo
                    }
            
            elif odl.status == "In Coda":
                if ODLQueueService._is_any_tool_available_for_parte(db, odl.parte_id):
                    odl.status = "Laminazione"
                    odl.motivo_blocco = None
                    db.commit()
                    
                    return {
                        'odl_id': odl.id,
                        'old_status': 'In Coda',
                        'new_status': 'Laminazione',
                        'motivo_blocco': None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Errore nel controllo forzato ODL {odl_id}: {e}")
            db.rollback()
            return None 