"""
Script di test per verificare il funzionamento del sistema di auto-generazione report PDF.
Questo script simula il completamento di un ciclo di cura e verifica che venga generato
automaticamente un report PDF.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from models.db import get_db
from models.nesting_result import NestingResult
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
from models.autoclave import Autoclave
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from services.auto_report_service import AutoReportService

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Configura la connessione al database"""
    engine = create_engine("sqlite:///carbonpilot.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

async def test_auto_report_generation():
    """
    Test principale per la generazione automatica di report.
    """
    logger.info("🧪 Avvio test di generazione automatica report...")
    
    # Configura il database
    db = setup_database()
    
    try:
        # 1. Trova un nesting esistente per il test
        nesting = db.query(NestingResult).filter(
            NestingResult.report_id.is_(None)  # Senza report
        ).first()
        
        if not nesting:
            logger.warning("⚠️ Nessun nesting senza report trovato. Creazione di dati di test...")
            # Qui potresti creare dati di test se necessario
            return False
        
        logger.info(f"📋 Trovato nesting ID {nesting.id} per il test")
        
        # 2. Crea o trova una schedule entry completata
        schedule = db.query(ScheduleEntry).filter(
            ScheduleEntry.autoclave_id == nesting.autoclave_id,
            ScheduleEntry.status == ScheduleEntryStatus.DONE.value
        ).first()
        
        if not schedule:
            logger.info("📅 Creazione di una schedule entry di test...")
            schedule = ScheduleEntry(
                autoclave_id=nesting.autoclave_id,
                start_datetime=datetime.now() - timedelta(hours=2),
                end_datetime=datetime.now() - timedelta(minutes=30),
                status=ScheduleEntryStatus.DONE.value,
                note="Test automatico - ciclo completato"
            )
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
        
        logger.info(f"⏰ Schedule entry ID {schedule.id} - Status: {schedule.status}")
        
        # 3. Inizializza il servizio di auto-report
        auto_report_service = AutoReportService(db)
        
        # 4. Controlla i cicli completati
        logger.info("🔍 Controllo cicli completati...")
        completed_cycles = auto_report_service.check_completed_cycles()
        logger.info(f"📊 Trovati {len(completed_cycles)} cicli completati")
        
        # 5. Se non ci sono cicli completati, simula uno
        if not completed_cycles:
            logger.info("🎭 Simulazione di un ciclo completato...")
            cycle_info = {
                'schedule_id': schedule.id,
                'nesting_id': nesting.id,
                'autoclave_id': nesting.autoclave_id,
                'odl_id': None,
                'completed_at': datetime.now(),
                'nesting': nesting,
                'schedule': schedule
            }
            
            # Genera il report per questo ciclo
            logger.info("📄 Generazione report per il ciclo simulato...")
            report = await auto_report_service.generate_cycle_completion_report(cycle_info)
            
            if report:
                logger.info(f"✅ Report generato con successo!")
                logger.info(f"   - ID Report: {report.id}")
                logger.info(f"   - Filename: {report.filename}")
                logger.info(f"   - Path: {report.file_path}")
                
                # Verifica che il nesting sia stato aggiornato
                db.refresh(nesting)
                if nesting.report_id == report.id:
                    logger.info(f"✅ Nesting aggiornato correttamente con report_id: {nesting.report_id}")
                else:
                    logger.error(f"❌ Errore: nesting non aggiornato correttamente")
                    return False
                
                return True
            else:
                logger.error("❌ Errore durante la generazione del report")
                return False
        
        # 6. Processa tutti i cicli completati
        logger.info("🚀 Processo di auto-generazione per tutti i cicli...")
        stats = await auto_report_service.process_all_completed_cycles()
        
        logger.info("📈 Statistiche del processo:")
        logger.info(f"   - Cicli trovati: {stats['cycles_found']}")
        logger.info(f"   - Report generati: {stats['reports_generated']}")
        logger.info(f"   - Errori: {stats['errors']}")
        
        if stats['generated_reports']:
            logger.info("📋 Report generati:")
            for report_info in stats['generated_reports']:
                logger.info(f"   - Nesting {report_info['nesting_id']}: {report_info['filename']}")
        
        return stats['reports_generated'] > 0 or stats['errors'] == 0
        
    except Exception as e:
        logger.error(f"❌ Errore durante il test: {e}")
        return False
    finally:
        db.close()

async def test_report_for_specific_nesting(nesting_id: int):
    """
    Test per generare un report per un nesting specifico.
    
    Args:
        nesting_id: ID del nesting per cui generare il report
    """
    logger.info(f"🎯 Test generazione report per nesting specifico ID {nesting_id}")
    
    db = setup_database()
    
    try:
        # Trova il nesting
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            logger.error(f"❌ Nesting con ID {nesting_id} non trovato")
            return False
        
        logger.info(f"📋 Nesting trovato: {nesting.id} - Autoclave: {nesting.autoclave_id}")
        
        # Inizializza il servizio
        auto_report_service = AutoReportService(db)
        
        # Crea una schedule entry fittizia
        schedule = ScheduleEntry(
            autoclave_id=nesting.autoclave_id,
            start_datetime=nesting.created_at,
            end_datetime=datetime.now(),
            status=ScheduleEntryStatus.DONE.value
        )
        
        cycle_info = {
            'schedule_id': 0,
            'nesting_id': nesting.id,
            'autoclave_id': nesting.autoclave_id,
            'odl_id': None,
            'completed_at': datetime.now(),
            'nesting': nesting,
            'schedule': schedule
        }
        
        # Genera il report
        report = await auto_report_service.generate_cycle_completion_report(cycle_info)
        
        if report:
            logger.info(f"✅ Report generato con successo per nesting {nesting_id}!")
            logger.info(f"   - Report ID: {report.id}")
            logger.info(f"   - Filename: {report.filename}")
            return True
        else:
            logger.error(f"❌ Errore durante la generazione del report per nesting {nesting_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante il test per nesting {nesting_id}: {e}")
        return False
    finally:
        db.close()

def list_available_nestings():
    """Lista i nesting disponibili per il test"""
    logger.info("📋 Lista nesting disponibili per il test:")
    
    db = setup_database()
    
    try:
        nestings = db.query(NestingResult).all()
        
        for nesting in nestings:
            has_report = "✅" if nesting.report_id else "❌"
            logger.info(f"   - ID {nesting.id}: Autoclave {nesting.autoclave_id}, Report: {has_report}")
        
        return nestings
        
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero dei nesting: {e}")
        return []
    finally:
        db.close()

async def main():
    """Funzione principale per eseguire i test"""
    logger.info("🚀 Avvio test sistema auto-report CarbonPilot")
    
    # Lista i nesting disponibili
    nestings = list_available_nestings()
    
    if not nestings:
        logger.error("❌ Nessun nesting trovato nel database")
        return
    
    # Test 1: Auto-generazione generale
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Auto-generazione generale")
    logger.info("="*50)
    
    success1 = await test_auto_report_generation()
    
    # Test 2: Generazione per nesting specifico
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Generazione per nesting specifico")
    logger.info("="*50)
    
    # Prendi il primo nesting senza report
    target_nesting = None
    for nesting in nestings:
        if not nesting.report_id:
            target_nesting = nesting
            break
    
    success2 = True
    if target_nesting:
        success2 = await test_report_for_specific_nesting(target_nesting.id)
    else:
        logger.info("ℹ️ Tutti i nesting hanno già un report associato")
    
    # Risultati finali
    logger.info("\n" + "="*50)
    logger.info("RISULTATI FINALI")
    logger.info("="*50)
    
    if success1 and success2:
        logger.info("🎉 Tutti i test sono stati completati con successo!")
    else:
        logger.warning("⚠️ Alcuni test hanno avuto problemi")
        logger.info(f"   - Test auto-generazione: {'✅' if success1 else '❌'}")
        logger.info(f"   - Test nesting specifico: {'✅' if success2 else '❌'}")

if __name__ == "__main__":
    asyncio.run(main()) 