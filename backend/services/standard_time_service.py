"""
Servizio per il calcolo automatico dei tempi standard di produzione.
Analizza i dati storici delle fasi e calcola media, mediana e percentile 90.
"""

import logging
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError

from models.standard_time import StandardTime
from models.tempo_fase import TempoFase
from models.odl import ODL
from models.parte import Parte
from services.system_log_service import SystemLogService
from models.system_log import EventType, UserRole, LogLevel

# Configurazione logger
logger = logging.getLogger(__name__)

class StandardTimeService:
    """Servizio per gestire i tempi standard di produzione."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def recalc_std_times(self, user_id: str = "system", user_role: str = "ADMIN") -> Dict[str, any]:
        """
        Ricalcola tutti i tempi standard basandosi sui dati storici delle fasi completate.
        
        Args:
            user_id: ID dell'utente che richiede il ricalcolo
            user_role: Ruolo dell'utente che richiede il ricalcolo
            
        Returns:
            Dizionario con statistiche del ricalcolo
        """
        try:
            logger.info("🔄 Avvio ricalcolo tempi standard...")
            
            # Converti il ruolo stringa in enum
            user_role_enum = UserRole.ADMIN if user_role == "ADMIN" else UserRole.RESPONSABILE
            
            # Log dell'evento di inizio
            SystemLogService.log_event(
                db=self.db,
                event_type=EventType.CALCULATION,
                action="Inizio ricalcolo tempi standard",
                entity_type="standard_time",
                user_id=user_id,
                user_role=user_role_enum,
                details="Avvio ricalcolo automatico dei tempi standard"
            )
            
            # Ottieni tutti i dati storici raggruppati per part_number e fase
            phase_data = self._get_historical_phase_data()
            
            stats = {
                "total_combinations": len(phase_data),
                "updated_records": 0,
                "created_records": 0,
                "errors": 0,
                "details": []
            }
            
            # Processa ogni combinazione part_number + fase
            for (part_number, fase), durations in phase_data.items():
                try:
                    result = self._calculate_and_save_standard_time(
                        part_number=part_number,
                        fase=fase,
                        durations=durations,
                        user_id=user_id
                    )
                    
                    if result["action"] == "created":
                        stats["created_records"] += 1
                    else:
                        stats["updated_records"] += 1
                        
                    stats["details"].append({
                        "part_number": part_number,
                        "fase": fase,
                        "action": result["action"],
                        "records_analyzed": result["records_analyzed"],
                        "avg_minutes": result["avg_minutes"],
                        "median_minutes": result["median_minutes"],
                        "p90_minutes": result["p90_minutes"]
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Errore durante il calcolo per {part_number}-{fase}: {str(e)}")
                    stats["errors"] += 1
                    stats["details"].append({
                        "part_number": part_number,
                        "fase": fase,
                        "action": "error",
                        "error": str(e)
                    })
            
            # Commit finale
            self.db.commit()
            
            # Log dell'evento di completamento
            SystemLogService.log_event(
                db=self.db,
                event_type=EventType.CALCULATION,
                action="Completato ricalcolo tempi standard",
                entity_type="standard_time",
                user_id=user_id,
                user_role=user_role_enum,
                details=f"Ricalcolo completato: {stats['updated_records']} aggiornati, {stats['created_records']} creati, {stats['errors']} errori"
            )
            
            logger.info(f"✅ Ricalcolo completato: {stats['updated_records']} aggiornati, {stats['created_records']} creati")
            return stats
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Errore durante il ricalcolo dei tempi standard: {str(e)}")
            
            # Log dell'errore
            SystemLogService.log_event(
                db=self.db,
                event_type=EventType.SYSTEM_ERROR,
                action="Errore durante ricalcolo tempi standard",
                entity_type="standard_time",
                user_id=user_id,
                user_role=user_role_enum,
                details=f"Errore: {str(e)}"
            )
            
            raise Exception(f"Errore durante il ricalcolo dei tempi standard: {str(e)}")
    
    def _get_historical_phase_data(self) -> Dict[Tuple[str, str], List[int]]:
        """
        Ottiene tutti i dati storici delle fasi completate raggruppati per part_number e fase.
        
        Returns:
            Dizionario con chiave (part_number, fase) e valore lista delle durate in minuti
        """
        logger.info("📊 Raccolta dati storici delle fasi...")
        
        # Query per ottenere tutti i tempi delle fasi completate per ODL validi
        query = (
            self.db.query(
                Parte.part_number,
                TempoFase.fase,
                TempoFase.durata_minuti
            )
            .join(ODL, TempoFase.odl_id == ODL.id)
            .join(Parte, ODL.parte_id == Parte.id)
            .filter(
                and_(
                    TempoFase.durata_minuti.isnot(None),  # Solo fasi completate
                    TempoFase.durata_minuti > 0,          # Durata valida
                    ODL.include_in_std == True,           # ODL inclusi nei tempi standard
                    ODL.status == "Finito"                # Solo ODL completati
                )
            )
        )
        
        results = query.all()
        logger.info(f"🔍 Trovati {len(results)} record di fasi completate")
        
        # Raggruppa i dati per combinazione part_number + fase
        phase_data = {}
        for part_number, fase, durata_minuti in results:
            key = (part_number, fase)
            if key not in phase_data:
                phase_data[key] = []
            phase_data[key].append(durata_minuti)
        
        logger.info(f"📈 Raggruppamento completato: {len(phase_data)} combinazioni part_number-fase")
        return phase_data
    
    def _calculate_and_save_standard_time(
        self, 
        part_number: str, 
        fase: str, 
        durations: List[int],
        user_id: str
    ) -> Dict[str, any]:
        """
        Calcola le statistiche per una combinazione part_number + fase e salva nel database.
        
        Args:
            part_number: Part number del prodotto
            fase: Fase di produzione
            durations: Lista delle durate in minuti
            user_id: ID dell'utente che richiede il calcolo
            
        Returns:
            Dizionario con i risultati del calcolo
        """
        if not durations:
            raise ValueError(f"Nessuna durata disponibile per {part_number}-{fase}")
        
        # Calcola le statistiche
        avg_minutes = statistics.mean(durations)
        median_minutes = statistics.median(durations)
        
        # Calcola il percentile 90
        sorted_durations = sorted(durations)
        p90_index = int(0.9 * len(sorted_durations))
        p90_minutes = sorted_durations[min(p90_index, len(sorted_durations) - 1)]
        
        # Usa la media come valore standard (come specificato nei requisiti)
        standard_minutes = avg_minutes
        
        logger.debug(f"📊 Statistiche {part_number}-{fase}: "
                    f"avg={avg_minutes:.1f}, median={median_minutes:.1f}, p90={p90_minutes:.1f}")
        
        # Verifica se esiste già un record
        existing_record = (
            self.db.query(StandardTime)
            .filter(
                and_(
                    StandardTime.part_number == part_number,
                    StandardTime.phase == fase
                )
            )
            .first()
        )
        
        # Prepara le note con le statistiche
        note = (
            f"Auto-calcolato da {len(durations)} osservazioni. "
            f"Media: {avg_minutes:.1f}min, Mediana: {median_minutes:.1f}min, P90: {p90_minutes:.1f}min"
        )
        
        if existing_record:
            # Aggiorna il record esistente
            existing_record.minutes = standard_minutes
            existing_record.note = note
            existing_record.updated_at = datetime.utcnow()
            action = "updated"
        else:
            # Crea un nuovo record
            new_record = StandardTime(
                part_number=part_number,
                phase=fase,
                minutes=standard_minutes,
                note=note
            )
            self.db.add(new_record)
            action = "created"
        
        return {
            "action": action,
            "records_analyzed": len(durations),
            "avg_minutes": round(avg_minutes, 1),
            "median_minutes": round(median_minutes, 1),
            "p90_minutes": round(p90_minutes, 1)
        }
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Ottiene statistiche generali sui tempi standard.
        
        Returns:
            Dizionario con statistiche sui tempi standard
        """
        try:
            # Conta i record totali
            total_records = self.db.query(StandardTime).count()
            
            # Conta i part number unici
            unique_parts = (
                self.db.query(StandardTime.part_number)
                .distinct()
                .count()
            )
            
            # Conta le fasi uniche
            unique_phases = (
                self.db.query(StandardTime.phase)
                .distinct()
                .count()
            )
            
            # Ottieni l'ultimo aggiornamento
            latest_update = (
                self.db.query(func.max(StandardTime.updated_at))
                .scalar()
            )
            
            return {
                "total_records": total_records,
                "unique_part_numbers": unique_parts,
                "unique_phases": unique_phases,
                "last_update": latest_update.isoformat() if latest_update else None
            }
            
        except Exception as e:
            logger.error(f"❌ Errore durante il calcolo delle statistiche: {str(e)}")
            raise Exception(f"Errore durante il calcolo delle statistiche: {str(e)}")
    
    def get_top_variances(self, limit: int = 5, days: int = 30) -> List[Dict]:
        """
        Ottiene i part-number con il maggiore scostamento percentuale tra tempo reale e tempo standard.
        
        Args:
            limit: Numero massimo di risultati da restituire (default: 5)
            days: Numero di giorni da considerare per i tempi osservati (default: 30)
            
        Returns:
            Lista di dizionari con part_number, fase, delta_percent ordinati per scostamento decrescente
        """
        try:
            logger.info(f"🔍 Calcolo top {limit} scostamenti negli ultimi {days} giorni...")
            
            # Calcola la data limite
            data_limite = datetime.now() - timedelta(days=days)
            
            # Query per ottenere i tempi osservati raggruppati per part_number e fase
            tempi_osservati_query = (
                self.db.query(
                    Parte.part_number,
                    TempoFase.fase,
                    func.avg(TempoFase.durata_minuti).label('media_osservata'),
                    func.count(TempoFase.id).label('numero_osservazioni')
                )
                .join(ODL, TempoFase.odl_id == ODL.id)
                .join(Parte, ODL.parte_id == Parte.id)
                .filter(
                    and_(
                        TempoFase.durata_minuti.isnot(None),
                        TempoFase.durata_minuti > 0,
                        ODL.include_in_std == True,
                        ODL.status == "Finito",
                        TempoFase.created_at >= data_limite
                    )
                )
                .group_by(Parte.part_number, TempoFase.fase)
                .having(func.count(TempoFase.id) >= 3)  # Almeno 3 osservazioni per essere significativo
            )
            
            tempi_osservati = {
                (row.part_number, row.fase): {
                    'media_osservata': float(row.media_osservata),
                    'numero_osservazioni': row.numero_osservazioni
                }
                for row in tempi_osservati_query.all()
            }
            
            # Ottieni tutti i tempi standard per le combinazioni presenti nei dati osservati
            part_numbers = list(set(key[0] for key in tempi_osservati.keys()))
            fasi = list(set(key[1] for key in tempi_osservati.keys()))
            
            tempi_standard_query = (
                self.db.query(StandardTime)
                .filter(
                    and_(
                        StandardTime.part_number.in_(part_numbers),
                        StandardTime.phase.in_(fasi)
                    )
                )
            )
            
            tempi_standard = {
                (st.part_number, st.phase): st.minutes
                for st in tempi_standard_query.all()
            }
            
            # Calcola gli scostamenti
            scostamenti = []
            for (part_number, fase), dati_osservati in tempi_osservati.items():
                tempo_standard = tempi_standard.get((part_number, fase))
                
                if tempo_standard and tempo_standard > 0:
                    media_osservata = dati_osservati['media_osservata']
                    delta_percent = ((media_osservata - tempo_standard) / tempo_standard) * 100
                    
                    # Determina il colore del delta
                    colore_delta = "verde"
                    abs_delta = abs(delta_percent)
                    if abs_delta > 10:
                        colore_delta = "rosso"
                    elif abs_delta > 5:
                        colore_delta = "giallo"
                    
                    scostamenti.append({
                        "part_number": part_number,
                        "fase": fase,
                        "delta_percent": round(delta_percent, 1),
                        "abs_delta_percent": round(abs_delta, 1),
                        "tempo_osservato": round(media_osservata, 1),
                        "tempo_standard": round(tempo_standard, 1),
                        "numero_osservazioni": dati_osservati['numero_osservazioni'],
                        "colore_delta": colore_delta
                    })
            
            # Ordina per scostamento assoluto decrescente e prendi i primi N
            scostamenti_ordinati = sorted(
                scostamenti, 
                key=lambda x: x['abs_delta_percent'], 
                reverse=True
            )[:limit]
            
            logger.info(f"✅ Trovati {len(scostamenti_ordinati)} scostamenti significativi")
            return scostamenti_ordinati
            
        except Exception as e:
            logger.error(f"❌ Errore durante il calcolo degli scostamenti: {str(e)}")
            raise Exception(f"Errore durante il calcolo degli scostamenti: {str(e)}")


def recalc_std_times(db: Session, user_id: str = "system", user_role: str = "ADMIN") -> Dict[str, any]:
    """
    Funzione helper per il ricalcolo dei tempi standard.
    
    Args:
        db: Sessione del database
        user_id: ID dell'utente che richiede il ricalcolo
        user_role: Ruolo dell'utente che richiede il ricalcolo
        
    Returns:
        Dizionario con statistiche del ricalcolo
    """
    service = StandardTimeService(db)
    return service.recalc_std_times(user_id=user_id, user_role=user_role) 