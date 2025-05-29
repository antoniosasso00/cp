import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_, case

from models.odl import ODL
from models.odl_log import ODLLog
from models.parte import Parte
from models.tool import Tool
from models.nesting_result import NestingResult
from models.autoclave import Autoclave
from models.schedule_entry import ScheduleEntry
from models.ciclo_cura import CicloCura
from schemas.odl_monitoring import (
    ODLMonitoringRead, 
    ODLMonitoringSummary, 
    ODLMonitoringStats,
    ODLLogRead
)
from services.odl_log_service import ODLLogService
from services.state_tracking_service import StateTrackingService

logger = logging.getLogger(__name__)

class ODLMonitoringService:
    """Servizio per il monitoraggio completo degli ODL"""
    
    @staticmethod
    def ottieni_odl_monitoraggio_completo(
        db: Session,
        odl_id: int
    ) -> Optional[ODLMonitoringRead]:
        """
        Ottiene il monitoraggio completo di un singolo ODL
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
        
        Returns:
            Optional[ODLMonitoringRead]: Dati completi di monitoraggio
        """
        try:
            # Query principale con join ottimizzati
            odl = db.query(ODL).options(
                joinedload(ODL.parte),
                joinedload(ODL.tool),
                joinedload(ODL.logs)
            ).filter(ODL.id == odl_id).first()
            
            if not odl:
                return None
            
            # Ottieni informazioni nesting più recente
            nesting_info = ODLMonitoringService._ottieni_info_nesting(db, odl_id)
            
            # Ottieni informazioni schedulazione attiva
            schedule_info = ODLMonitoringService._ottieni_info_schedulazione(db, odl_id)
            
            # Ottieni informazioni ciclo di cura
            ciclo_info = ODLMonitoringService._ottieni_info_ciclo_cura(db, odl)
            
            # ✅ CORREZIONE: Calcola statistiche temporali usando StateTrackingService
            try:
                tempo_stato_corrente = StateTrackingService.calcola_tempo_in_stato_corrente(db, odl_id)
                tempo_totale = StateTrackingService.calcola_tempo_totale_produzione(db, odl_id)
                logger.info(f"✅ Tempi calcolati per ODL {odl_id}: stato corrente={tempo_stato_corrente}min, totale={tempo_totale}min")
            except Exception as e:
                logger.warning(f"⚠️ Errore calcolo tempi StateTrackingService per ODL {odl_id}: {str(e)}, fallback a ODLLogService")
                # Fallback al servizio precedente se StateTrackingService fallisce
                tempo_stato_corrente = ODLLogService.calcola_tempo_in_stato(db, odl_id, odl.status)
                tempo_totale = ODLLogService.calcola_tempo_totale_produzione(db, odl_id)
            
            # Prepara i log con informazioni aggiuntive
            logs_arricchiti = []
            
            # ✅ CORREZIONE: Validazione robusta dei logs
            if hasattr(odl, 'logs') and odl.logs is not None:
                try:
                    for log in odl.logs:
                        # Valida che il log abbia i campi essenziali
                        if not log or not hasattr(log, 'id') or not hasattr(log, 'evento') or not hasattr(log, 'timestamp'):
                            logger.warning(f"ODL {odl_id}: log entry mancante o invalido, saltato")
                            continue
                            
                        log_dict = {
                            "id": log.id,
                            "odl_id": log.odl_id,
                            "evento": log.evento or "evento_sconosciuto",
                            "stato_precedente": getattr(log, 'stato_precedente', None),
                            "stato_nuovo": getattr(log, 'stato_nuovo', None),
                            "descrizione": getattr(log, 'descrizione', None),
                            "responsabile": getattr(log, 'responsabile', None),
                            "nesting_id": getattr(log, 'nesting_id', None),
                            "autoclave_id": getattr(log, 'autoclave_id', None),
                            "schedule_entry_id": getattr(log, 'schedule_entry_id', None),
                            "timestamp": log.timestamp,
                            "nesting_stato": None,
                            "autoclave_nome": None
                        }
                        
                        # Aggiungi informazioni correlate se disponibili
                        try:
                            if log.nesting_id:
                                nesting = db.query(NestingResult).filter(NestingResult.id == log.nesting_id).first()
                                if nesting:
                                    log_dict["nesting_stato"] = nesting.stato
                        except Exception as e:
                            logger.warning(f"Errore nel recupero nesting {log.nesting_id}: {str(e)}")
                        
                        try:
                            if log.autoclave_id:
                                autoclave = db.query(Autoclave).filter(Autoclave.id == log.autoclave_id).first()
                                if autoclave:
                                    log_dict["autoclave_nome"] = autoclave.nome
                        except Exception as e:
                            logger.warning(f"Errore nel recupero autoclave {log.autoclave_id}: {str(e)}")
                        
                        # Crea l'oggetto ODLLogRead solo se i dati sono validi
                        try:
                            logs_arricchiti.append(ODLLogRead(**log_dict))
                        except Exception as e:
                            logger.error(f"Errore nella creazione ODLLogRead per log {log.id}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Errore durante l'elaborazione dei logs per ODL {odl_id}: {str(e)}")
                    logs_arricchiti = []  # Fallback a lista vuota
            else:
                logger.info(f"ODL {odl_id}: nessun log disponibile o logs è None")
                logs_arricchiti = []
            
            # Costruisci il risultato
            result = ODLMonitoringRead(
                # Informazioni base ODL
                id=odl.id,
                parte_id=odl.parte_id,
                tool_id=odl.tool_id,
                priorita=odl.priorita,
                status=odl.status,
                note=odl.note,
                motivo_blocco=odl.motivo_blocco,
                created_at=odl.created_at,
                updated_at=odl.updated_at,
                
                # Informazioni correlate
                parte_nome=odl.parte.descrizione_breve,
                parte_categoria=getattr(odl.parte, 'categoria', None),
                tool_nome=odl.tool.part_number_tool,
                
                # Informazioni nesting
                nesting_id=nesting_info.get("id"),
                nesting_stato=nesting_info.get("stato"),
                nesting_created_at=nesting_info.get("created_at"),
                
                # Informazioni autoclave
                autoclave_id=nesting_info.get("autoclave_id") or schedule_info.get("autoclave_id"),
                autoclave_nome=nesting_info.get("autoclave_nome") or schedule_info.get("autoclave_nome"),
                
                # Informazioni ciclo di cura
                ciclo_cura_id=ciclo_info.get("id"),
                ciclo_cura_nome=ciclo_info.get("nome"),
                
                # Informazioni schedulazione
                schedule_entry_id=schedule_info.get("id"),
                schedule_start=schedule_info.get("start_datetime"),
                schedule_end=schedule_info.get("end_datetime"),
                schedule_status=schedule_info.get("status"),
                
                # Log di avanzamento
                logs=logs_arricchiti,
                
                # Statistiche temporali
                tempo_in_stato_corrente=tempo_stato_corrente,
                tempo_totale_produzione=tempo_totale
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Errore durante il recupero del monitoraggio ODL {odl_id}: {str(e)}")
            return None
    
    @staticmethod
    def ottieni_lista_monitoraggio(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        priorita_min: Optional[int] = None,
        solo_attivi: bool = True
    ) -> List[ODLMonitoringSummary]:
        """
        Ottiene una lista riassuntiva del monitoraggio ODL
        
        Args:
            db: Sessione database
            skip: Numero di elementi da saltare
            limit: Limite elementi da restituire
            status_filter: Filtro per stato
            priorita_min: Priorità minima
            solo_attivi: Se True, esclude ODL completati
        
        Returns:
            List[ODLMonitoringSummary]: Lista riassuntiva
        """
        try:
            # Query base
            query = db.query(ODL).options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            )
            
            # Applicazione filtri
            if status_filter:
                query = query.filter(ODL.status == status_filter)
            
            if priorita_min:
                query = query.filter(ODL.priorita >= priorita_min)
            
            if solo_attivi:
                query = query.filter(ODL.status != "Finito")
            
            # Ordinamento per priorità e data di aggiornamento
            query = query.order_by(desc(ODL.priorita), desc(ODL.updated_at))
            
            # Paginazione
            odl_list = query.offset(skip).limit(limit).all()
            
            risultati = []
            
            for odl in odl_list:
                # Ottieni ultimo evento
                ultimo_log = db.query(ODLLog).filter(
                    ODLLog.odl_id == odl.id
                ).order_by(desc(ODLLog.timestamp)).first()
                
                # Ottieni informazioni nesting/autoclave
                nesting_info = ODLMonitoringService._ottieni_info_nesting(db, odl.id)
                schedule_info = ODLMonitoringService._ottieni_info_schedulazione(db, odl.id)
                
                # ✅ CORREZIONE: Calcola tempo nello stato corrente usando StateTrackingService
                try:
                    tempo_stato = StateTrackingService.calcola_tempo_in_stato_corrente(db, odl.id)
                except Exception as e:
                    logger.warning(f"⚠️ Errore calcolo tempo StateTrackingService per ODL {odl.id}: {str(e)}, fallback a ODLLogService")
                    tempo_stato = ODLLogService.calcola_tempo_in_stato(db, odl.id, odl.status)
                
                summary = ODLMonitoringSummary(
                    id=odl.id,
                    parte_nome=odl.parte.descrizione_breve,
                    tool_nome=odl.tool.part_number_tool,
                    status=odl.status,
                    priorita=odl.priorita,
                    created_at=odl.created_at,
                    updated_at=odl.updated_at,
                    nesting_stato=nesting_info.get("stato"),
                    autoclave_nome=nesting_info.get("autoclave_nome") or schedule_info.get("autoclave_nome"),
                    ultimo_evento=ultimo_log.evento if ultimo_log else None,
                    ultimo_evento_timestamp=ultimo_log.timestamp if ultimo_log else None,
                    tempo_in_stato_corrente=tempo_stato
                )
                
                risultati.append(summary)
            
            return risultati
            
        except Exception as e:
            logger.error(f"Errore durante il recupero della lista monitoraggio: {str(e)}")
            return []
    
    @staticmethod
    def ottieni_statistiche_monitoraggio(db: Session) -> ODLMonitoringStats:
        """
        Ottiene statistiche generali del monitoraggio ODL
        
        Args:
            db: Sessione database
        
        Returns:
            ODLMonitoringStats: Statistiche di monitoraggio
        """
        try:
            # Conteggio totale ODL
            totale_odl = db.query(ODL).count()
            
            # Conteggio per stato
            conteggi_stato = db.query(
                ODL.status,
                func.count(ODL.id).label('count')
            ).group_by(ODL.status).all()
            
            per_stato = {stato: count for stato, count in conteggi_stato}
            
            # ODL completati oggi
            oggi = datetime.now().date()
            completati_oggi = db.query(ODL).filter(
                and_(
                    ODL.status == "Finito",
                    func.date(ODL.updated_at) == oggi
                )
            ).count()
            
            # Calcola tempo medio di completamento (ultimi 30 giorni)
            trenta_giorni_fa = datetime.now() - timedelta(days=30)
            
            odl_completati_recenti = db.query(ODL).filter(
                and_(
                    ODL.status == "Finito",
                    ODL.updated_at >= trenta_giorni_fa
                )
            ).all()
            
            tempi_completamento = []
            for odl in odl_completati_recenti:
                tempo_totale = ODLLogService.calcola_tempo_totale_produzione(db, odl.id)
                if tempo_totale:
                    tempi_completamento.append(tempo_totale)
            
            media_tempo_completamento = None
            if tempi_completamento:
                media_minuti = sum(tempi_completamento) / len(tempi_completamento)
                media_tempo_completamento = media_minuti / 60  # Converti in ore
            
            # ODL in ritardo (logica semplificata: più di 24h nello stesso stato)
            ventiquattro_ore_fa = datetime.now() - timedelta(hours=24)
            
            odl_potenzialmente_in_ritardo = db.query(ODL).filter(
                and_(
                    ODL.status.in_(["Laminazione", "Attesa Cura", "Cura"]),
                    ODL.updated_at < ventiquattro_ore_fa
                )
            ).all()
            
            in_ritardo = 0
            for odl in odl_potenzialmente_in_ritardo:
                tempo_stato = ODLLogService.calcola_tempo_in_stato(db, odl.id, odl.status)
                if tempo_stato and tempo_stato > 1440:  # Più di 24 ore
                    in_ritardo += 1
            
            return ODLMonitoringStats(
                totale_odl=totale_odl,
                per_stato=per_stato,
                in_ritardo=in_ritardo,
                completati_oggi=completati_oggi,
                media_tempo_completamento=media_tempo_completamento
            )
            
        except Exception as e:
            logger.error(f"Errore durante il calcolo delle statistiche: {str(e)}")
            return ODLMonitoringStats(
                totale_odl=0,
                per_stato={},
                in_ritardo=0,
                completati_oggi=0,
                media_tempo_completamento=None
            )
    
    @staticmethod
    def _ottieni_info_nesting(db: Session, odl_id: int) -> Dict[str, Any]:
        """Ottiene informazioni sul nesting più recente per un ODL"""
        try:
            # Trova il nesting più recente che include questo ODL
            nesting = db.query(NestingResult).join(
                NestingResult.odl_list
            ).filter(
                ODL.id == odl_id
            ).order_by(desc(NestingResult.created_at)).first()
            
            if not nesting:
                return {}
            
            autoclave_nome = None
            if nesting.autoclave:
                autoclave_nome = nesting.autoclave.nome
            
            return {
                "id": nesting.id,
                "stato": nesting.stato,
                "created_at": nesting.created_at,
                "autoclave_id": nesting.autoclave_id,
                "autoclave_nome": autoclave_nome
            }
            
        except Exception as e:
            logger.error(f"Errore nel recupero info nesting per ODL {odl_id}: {str(e)}")
            return {}
    
    @staticmethod
    def _ottieni_info_schedulazione(db: Session, odl_id: int) -> Dict[str, Any]:
        """Ottiene informazioni sulla schedulazione attiva per un ODL"""
        try:
            # Trova la schedulazione più recente per questo ODL
            schedule = db.query(ScheduleEntry).options(
                joinedload(ScheduleEntry.autoclave)
            ).filter(
                ScheduleEntry.odl_id == odl_id
            ).order_by(desc(ScheduleEntry.created_at)).first()
            
            if not schedule:
                return {}
            
            autoclave_nome = None
            if schedule.autoclave:
                autoclave_nome = schedule.autoclave.nome
            
            return {
                "id": schedule.id,
                "start_datetime": schedule.start_datetime,
                "end_datetime": schedule.end_datetime,
                "status": schedule.status,
                "autoclave_id": schedule.autoclave_id,
                "autoclave_nome": autoclave_nome
            }
            
        except Exception as e:
            logger.error(f"Errore nel recupero info schedulazione per ODL {odl_id}: {str(e)}")
            return {}
    
    @staticmethod
    def _ottieni_info_ciclo_cura(db: Session, odl: ODL) -> Dict[str, Any]:
        """Ottiene informazioni sul ciclo di cura per un ODL"""
        try:
            # Il ciclo di cura è determinato dalla categoria della parte
            if not odl.parte or not hasattr(odl.parte, 'categoria'):
                return {}
            
            # Trova il ciclo di cura per la categoria
            ciclo = db.query(CicloCura).filter(
                CicloCura.categoria == odl.parte.categoria
            ).first()
            
            if not ciclo:
                return {}
            
            return {
                "id": ciclo.id,
                "nome": ciclo.nome
            }
            
        except Exception as e:
            logger.error(f"Errore nel recupero info ciclo cura per ODL {odl.id}: {str(e)}")
            return {} 