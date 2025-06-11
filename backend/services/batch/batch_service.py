"""
Servizio business logic batch nesting

Questo modulo contiene la logica di business per:
- Creazione batch robusti
- Distribuzione intelligente ODL
- Validazione dati batch
- Calcolo metriche
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from services.nesting_service import NestingService, NestingParameters

logger = logging.getLogger(__name__)

class BatchService:
    """Servizio per business logic batch nesting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_robust_batch(
        self,
        autoclave_id: str,
        odl_ids: List[str],
        nesting_result: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        nome: Optional[str] = None,
        creato_da_utente: str = "SYSTEM",
        creato_da_ruolo: str = "SYSTEM"
    ) -> BatchNesting:
        """
        Crea un batch robusto con validazioni complete
        
        Args:
            autoclave_id: ID dell'autoclave target
            odl_ids: Lista ODL da includere
            nesting_result: Risultato algoritmo nesting
            parameters: Parametri di generazione
            nome: Nome batch (opzionale, generato auto)
            creato_da_utente: Utente creatore
            creato_da_ruolo: Ruolo creatore
            
        Returns:
            BatchNesting: Batch creato
        """
        try:
            # Validazione dati
            autoclave = self.db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            if not autoclave:
                raise ValueError(f"Autoclave {autoclave_id} non trovata")
            
            # Verifica ODL esistenti
            existing_odls = self.db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
            if len(existing_odls) != len(odl_ids):
                missing_ids = set(odl_ids) - {str(odl.id) for odl in existing_odls}
                raise ValueError(f"ODL non trovati: {missing_ids}")
            
            # Genera nome se non specificato
            if not nome:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome = f"Robust_Nesting_{autoclave.nome}_{timestamp}"
            
            # Estrae metriche dal risultato nesting
            metrics = self._extract_nesting_metrics(nesting_result)
            
            # Crea batch
            batch_data = {
                "nome": nome,
                "autoclave_id": autoclave_id,
                "odl_ids": odl_ids,
                "parametri": parameters or {},
                "configurazione_json": nesting_result,
                "stato": StatoBatchNestingEnum.DRAFT.value,
                "creato_da_utente": creato_da_utente,
                "creato_da_ruolo": creato_da_ruolo,
                "numero_nesting": len(odl_ids),
                "efficienza_area": metrics.get("efficiency", 0.0),
                "peso_totale": metrics.get("total_weight", 0.0),
                "algorithm_status": metrics.get("algorithm_status", "UNKNOWN")
            }
            
            batch = BatchNesting(**batch_data)
            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)
            
            logger.info(f"✅ Creato batch robusto {batch.id} per autoclave {autoclave.nome}")
            logger.info(f"   - ODL: {len(odl_ids)}, Efficienza: {metrics.get('efficiency', 0):.1f}%")
            
            return batch
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Errore creazione batch robusto: {e}")
            raise
    
    def distribute_odls_intelligently(
        self,
        autoclavi: List[Autoclave],
        odl_ids: List[str]
    ) -> Dict[str, List[str]]:
        """
        Distribuisce ODL tra autoclavi in modo intelligente
        
        Strategy v2.0:
        - Distribuzione ciclica pura (round-robin)
        - Gestione pesi NULL con stima da area
        - Nessuna "distribuzione per carico minore"
        
        Args:
            autoclavi: Lista autoclavi disponibili
            odl_ids: Lista ODL da distribuire
            
        Returns:
            Dict[autoclave_id, odl_ids]: Distribuzione finale
        """
        if not autoclavi or not odl_ids:
            logger.warning("⚠️ Nessuna autoclave o ODL forniti per distribuzione")
            return {}
        
        logger.info(f"🔄 Distribuzione intelligente: {len(odl_ids)} ODL → {len(autoclavi)} autoclavi")
        
        # Algoritmo distribuzione ciclica v2.0
        distribution = {autoclave.id: [] for autoclave in autoclavi}
        
        for i, odl_id in enumerate(odl_ids):
            # Round-robin ciclico
            autoclave_index = i % len(autoclavi)
            target_autoclave = autoclavi[autoclave_index]
            distribution[target_autoclave.id].append(odl_id)
            
            logger.debug(f"   ODL {odl_id} → {target_autoclave.nome} (ciclo {autoclave_index})")
        
        # Log finale distribuzione
        for autoclave in autoclavi:
            assigned_count = len(distribution[autoclave.id])
            logger.info(f"📋 {autoclave.nome}: {assigned_count} ODL - {distribution[autoclave.id]}")
        
        return distribution
    
    def validate_batch_data(
        self,
        autoclave_id: str,
        odl_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Valida dati per creazione batch
        
        Returns:
            Dict con risultati validazione
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "autoclave": None,
            "odls": [],
            "total_weight": 0.0,
            "compatible_cycles": []
        }
        
        try:
            # Verifica autoclave
            autoclave = self.db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            if not autoclave:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Autoclave {autoclave_id} non trovata")
                return validation_results
            
            if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE.value:
                validation_results["warnings"].append(f"Autoclave {autoclave.nome} non disponibile (stato: {autoclave.stato})")
            
            validation_results["autoclave"] = autoclave
            
            # Verifica ODL
            odls = self.db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
            found_ids = {str(odl.id) for odl in odls}
            missing_ids = set(odl_ids) - found_ids
            
            if missing_ids:
                validation_results["valid"] = False
                validation_results["errors"].append(f"ODL non trovati: {missing_ids}")
                return validation_results
            
            # Verifica stati ODL
            non_curable_odls = [odl for odl in odls if odl.status != "Attesa Cura"]
            if non_curable_odls:
                validation_results["warnings"].append(
                    f"ODL non in 'Attesa Cura': {[odl.id for odl in non_curable_odls]}"
                )
            
            validation_results["odls"] = odls
            validation_results["total_weight"] = sum(odl.peso or 0 for odl in odls)
            
            # Verifica cicli di cura compatibili
            compatible_cycles = self._find_compatible_cure_cycles(odls)
            validation_results["compatible_cycles"] = compatible_cycles
            
            if not compatible_cycles:
                validation_results["warnings"].append("Nessun ciclo di cura comune trovato")
            
            logger.info(f"✅ Validazione batch: {len(odls)} ODL, peso {validation_results['total_weight']}kg")
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Errore validazione: {e}")
            logger.error(f"❌ Errore validazione batch: {e}")
        
        return validation_results
    
    def cleanup_old_batches(
        self,
        days_threshold: int = 7,
        stato_filter: str = "SOSPESO",
        autoclave_filter: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Pulisce batch vecchi per evitare sovraccarico sistema
        
        Returns:
            Dict con risultati cleanup
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            
            query = self.db.query(BatchNesting).filter(
                BatchNesting.created_at < cutoff_date,
                BatchNesting.stato == stato_filter
            )
            
            if autoclave_filter:
                autoclave = self.db.query(Autoclave).filter(Autoclave.nome == autoclave_filter).first()
                if autoclave:
                    query = query.filter(BatchNesting.autoclave_id == autoclave.id)
            
            old_batches = query.all()
            
            results = {
                "found_count": len(old_batches),
                "deleted_count": 0,
                "deleted_ids": [],
                "dry_run": dry_run,
                "cutoff_date": cutoff_date.isoformat(),
                "filters": {
                    "days_threshold": days_threshold,
                    "stato_filter": stato_filter,
                    "autoclave_filter": autoclave_filter
                }
            }
            
            if not dry_run and old_batches:
                for batch in old_batches:
                    try:
                        self.db.delete(batch)
                        results["deleted_ids"].append(batch.id)
                        results["deleted_count"] += 1
                    except Exception as e:
                        logger.error(f"Errore eliminazione batch {batch.id}: {e}")
                
                self.db.commit()
                logger.info(f"🧹 Cleanup completato: {results['deleted_count']} batch eliminati")
            else:
                logger.info(f"🔍 Dry run cleanup: {results['found_count']} batch da eliminare")
            
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Errore cleanup batch: {e}")
            raise
    
    def _extract_nesting_metrics(self, nesting_result: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae metriche dal risultato nesting"""
        return {
            "efficiency": nesting_result.get("efficiency", 0.0),
            "total_weight": nesting_result.get("total_weight", 0.0),
            "algorithm_status": nesting_result.get("algorithm_status", "UNKNOWN"),
            "positioned_tools": len(nesting_result.get("positioned_tools", [])),
            "excluded_odls": len(nesting_result.get("excluded_odls", []))
        }
    
    def _find_compatible_cure_cycles(self, odls: List[ODL]) -> List[Dict[str, Any]]:
        """Trova cicli di cura compatibili tra ODL"""
        # TODO: Implementare logica cicli compatibili
        return []

    @staticmethod
    def generate_batch_name(autoclave_nome: str, batch_type: str = "Batch") -> str:
        """Genera nome batch automatico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{batch_type}_{autoclave_nome}_{timestamp}" 