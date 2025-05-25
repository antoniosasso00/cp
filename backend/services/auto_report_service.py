"""
Servizio per la generazione automatica di report PDF al termine dei cicli di cura.
Questo servizio si occupa di:
1. Rilevare quando un ciclo di cura è completato
2. Generare automaticamente un report PDF dettagliato
3. Collegare il report al nesting corrispondente
4. Gestire errori e logging
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from models.nesting_result import NestingResult
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.report import Report, ReportTypeEnum
from services.report_service import ReportService

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoReportService:
    """Servizio per la generazione automatica di report PDF al termine dei cicli di cura"""
    
    def __init__(self, db: Session):
        """
        Inizializza il servizio di auto-report.
        
        Args:
            db: Sessione del database
        """
        self.db = db
        self.report_service = ReportService(db)
        
    def check_completed_cycles(self) -> List[Dict[str, Any]]:
        """
        Controlla se ci sono cicli di cura completati che non hanno ancora un report.
        
        Returns:
            Lista di dizionari con informazioni sui cicli completati
        """
        try:
            # Trova tutte le schedule entries completate nelle ultime 24 ore
            # che non hanno ancora un report associato
            yesterday = datetime.now() - timedelta(days=1)
            
            completed_schedules = self.db.query(ScheduleEntry).filter(
                and_(
                    ScheduleEntry.status == ScheduleEntryStatus.DONE.value,
                    ScheduleEntry.updated_at >= yesterday
                )
            ).all()
            
            cycles_to_process = []
            
            for schedule in completed_schedules:
                # Trova il nesting associato a questa schedule entry
                nesting = self._find_nesting_for_schedule(schedule)
                
                if nesting and not nesting.report_id:
                    # Questo nesting non ha ancora un report
                    cycle_info = {
                        'schedule_id': schedule.id,
                        'nesting_id': nesting.id,
                        'autoclave_id': schedule.autoclave_id,
                        'odl_id': schedule.odl_id,
                        'completed_at': schedule.updated_at,
                        'nesting': nesting,
                        'schedule': schedule
                    }
                    cycles_to_process.append(cycle_info)
                    
            logger.info(f"Trovati {len(cycles_to_process)} cicli completati senza report")
            return cycles_to_process
            
        except Exception as e:
            logger.error(f"Errore durante il controllo dei cicli completati: {e}")
            return []
    
    def _find_nesting_for_schedule(self, schedule: ScheduleEntry) -> Optional[NestingResult]:
        """
        Trova il nesting associato a una schedule entry.
        
        Args:
            schedule: Schedule entry completata
            
        Returns:
            NestingResult associato o None
        """
        try:
            # Cerca nesting per autoclave e ODL
            if schedule.odl_id:
                # Cerca nesting che contiene questo ODL specifico
                nestings = self.db.query(NestingResult).filter(
                    and_(
                        NestingResult.autoclave_id == schedule.autoclave_id,
                        NestingResult.odl_ids.contains([schedule.odl_id])
                    )
                ).all()
                
                # Prendi il nesting più recente
                if nestings:
                    return max(nestings, key=lambda n: n.created_at)
            
            # Se non trova per ODL specifico, cerca per autoclave e periodo
            start_time = schedule.start_datetime - timedelta(hours=2)
            end_time = schedule.end_datetime or datetime.now()
            end_time = end_time + timedelta(hours=2)
            
            nesting = self.db.query(NestingResult).filter(
                and_(
                    NestingResult.autoclave_id == schedule.autoclave_id,
                    NestingResult.created_at >= start_time,
                    NestingResult.created_at <= end_time
                )
            ).order_by(NestingResult.created_at.desc()).first()
            
            return nesting
            
        except Exception as e:
            logger.error(f"Errore durante la ricerca del nesting per schedule {schedule.id}: {e}")
            return None
    
    async def generate_cycle_completion_report(self, cycle_info: Dict[str, Any]) -> Optional[Report]:
        """
        Genera un report PDF per un ciclo di cura completato.
        
        Args:
            cycle_info: Informazioni sul ciclo completato
            
        Returns:
            Report generato o None in caso di errore
        """
        try:
            nesting = cycle_info['nesting']
            schedule = cycle_info['schedule']
            
            logger.info(f"Generazione report per nesting {nesting.id} (schedule {schedule.id})")
            
            # Prepara i dati per il report
            report_data = self._prepare_cycle_report_data(cycle_info)
            
            # Genera il report PDF specializzato per cicli di cura
            file_path, report_record = await self._generate_cycle_pdf_report(report_data)
            
            # Collega il report al nesting
            nesting.report_id = report_record.id
            self.db.commit()
            
            logger.info(f"✅ Report generato con successo: {file_path}")
            return report_record
            
        except Exception as e:
            logger.error(f"❌ Errore durante la generazione del report per ciclo {cycle_info.get('nesting_id')}: {e}")
            return None
    
    def _prepare_cycle_report_data(self, cycle_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara i dati necessari per il report del ciclo di cura.
        
        Args:
            cycle_info: Informazioni sul ciclo completato
            
        Returns:
            Dizionario con tutti i dati per il report
        """
        nesting = cycle_info['nesting']
        schedule = cycle_info['schedule']
        
        # Carica l'autoclave con i dettagli
        autoclave = self.db.query(Autoclave).filter(
            Autoclave.id == nesting.autoclave_id
        ).first()
        
        # Carica gli ODL con le parti e i cicli di cura
        odl_list = self.db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(ODL.id.in_(nesting.odl_ids)).all()
        
        # Calcola i parametri del ciclo
        cycle_params = self._calculate_cycle_parameters(odl_list)
        
        # Calcola la durata effettiva del ciclo
        duration_minutes = None
        if schedule.start_datetime and schedule.end_datetime:
            duration = schedule.end_datetime - schedule.start_datetime
            duration_minutes = int(duration.total_seconds() / 60)
        
        return {
            'nesting_id': nesting.id,
            'nesting_date': nesting.created_at,
            'autoclave': autoclave,
            'odl_list': odl_list,
            'cycle_params': cycle_params,
            'duration_minutes': duration_minutes,
            'start_datetime': schedule.start_datetime,
            'end_datetime': schedule.end_datetime,
            'area_utilizzata': nesting.area_utilizzata,
            'area_totale': nesting.area_totale,
            'valvole_utilizzate': nesting.valvole_utilizzate,
            'valvole_totali': nesting.valvole_totali,
            'posizioni_tool': nesting.posizioni_tool,
            'note': nesting.note,
            'stato_finale': nesting.stato
        }
    
    def _calculate_cycle_parameters(self, odl_list: List[ODL]) -> Dict[str, Any]:
        """
        Calcola i parametri del ciclo di cura basandosi sugli ODL inclusi.
        
        Args:
            odl_list: Lista degli ODL nel nesting
            
        Returns:
            Dizionario con i parametri del ciclo
        """
        if not odl_list:
            return {}
        
        # Trova tutti i cicli di cura unici
        cicli_cura = []
        for odl in odl_list:
            if odl.parte and odl.parte.ciclo_cura:
                cicli_cura.append(odl.parte.ciclo_cura)
        
        if not cicli_cura:
            return {}
        
        # Calcola i parametri massimi (per sicurezza)
        temp_max = max(ciclo.temperatura_max for ciclo in cicli_cura)
        pressione_max = max(ciclo.pressione_max for ciclo in cicli_cura)
        
        # Calcola la durata totale stimata
        durata_totale = 0
        for ciclo in cicli_cura:
            durata_totale += ciclo.durata_stasi1
            if ciclo.attiva_stasi2 and ciclo.durata_stasi2:
                durata_totale += ciclo.durata_stasi2
        
        return {
            'temperatura_max': temp_max,
            'pressione_max': pressione_max,
            'durata_stimata_minuti': durata_totale,
            'cicli_utilizzati': [ciclo.nome for ciclo in set(cicli_cura)]
        }
    
    async def _generate_cycle_pdf_report(self, report_data: Dict[str, Any]) -> tuple[str, Report]:
        """
        Genera il PDF del report per il ciclo di cura completato.
        
        Args:
            report_data: Dati del ciclo di cura
            
        Returns:
            Tupla con path del file e record del report
        """
        # Usa il servizio report esistente con dati personalizzati
        return await self.report_service.generate_report(
            report_type=ReportTypeEnum.NESTING,
            start_date=report_data['nesting_date'],
            end_date=report_data['end_datetime'] or datetime.now(),
            include_sections=['header', 'nesting', 'odl', 'ciclo_cura'],
            user_id=None  # Report automatico
        )
    
    async def process_all_completed_cycles(self) -> Dict[str, Any]:
        """
        Processa tutti i cicli di cura completati e genera i report mancanti.
        
        Returns:
            Dizionario con statistiche del processo
        """
        logger.info("🚀 Avvio processo di generazione automatica report...")
        
        completed_cycles = self.check_completed_cycles()
        
        stats = {
            'cycles_found': len(completed_cycles),
            'reports_generated': 0,
            'errors': 0,
            'generated_reports': []
        }
        
        for cycle_info in completed_cycles:
            try:
                report = await self.generate_cycle_completion_report(cycle_info)
                if report:
                    stats['reports_generated'] += 1
                    stats['generated_reports'].append({
                        'nesting_id': cycle_info['nesting_id'],
                        'report_id': report.id,
                        'filename': report.filename
                    })
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Errore durante il processo del ciclo {cycle_info.get('nesting_id')}: {e}")
                stats['errors'] += 1
        
        logger.info(f"✅ Processo completato: {stats['reports_generated']} report generati, {stats['errors']} errori")
        return stats 