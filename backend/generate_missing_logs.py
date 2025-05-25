#!/usr/bin/env python3
"""Script per generare log mancanti per ODL esistenti"""

import sys
sys.path.append('.')

from sqlalchemy.orm import sessionmaker
from models.db import engine
from services.odl_log_service import ODLLogService

def main():
    """Genera log mancanti per ODL esistenti"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔄 Generazione log mancanti per ODL esistenti...")
        
        # Genera log di creazione per ODL senza log
        logs_creati = ODLLogService.genera_logs_mancanti_per_odl_esistenti(db)
        
        if logs_creati > 0:
            print(f"✅ Generati {logs_creati} log di creazione")
        else:
            print("ℹ️  Nessun log mancante da generare")
        
        # Ora generiamo log aggiuntivi basati sullo stato attuale degli ODL
        print("\n🔄 Generazione log aggiuntivi basati sullo stato attuale...")
        
        from models.odl import ODL
        from models.odl_log import ODLLog
        from models.nesting_result import NestingResult
        from models.schedule_entry import ScheduleEntry
        from datetime import datetime, timedelta
        
        odl_list = db.query(ODL).all()
        logs_aggiuntivi = 0
        
        for odl in odl_list:
            # Verifica se l'ODL è in un nesting
            nesting = db.query(NestingResult).filter(
                NestingResult.odl_ids.contains([odl.id])
            ).first()
            
            if nesting and odl.status in ["Attesa Cura", "Cura"]:
                # Crea log di assegnazione al nesting se non esiste
                existing_nesting_log = db.query(ODLLog).filter(
                    ODLLog.odl_id == odl.id,
                    ODLLog.evento == "assegnato_nesting"
                ).first()
                
                if not existing_nesting_log:
                    # Simula timestamp di assegnazione (qualche ora fa)
                    timestamp_assegnazione = odl.created_at + timedelta(hours=1)
                    
                    log_nesting = ODLLog(
                        odl_id=odl.id,
                        evento="assegnato_nesting",
                        stato_precedente="Preparazione",
                        stato_nuovo="In Coda",
                        descrizione=f"ODL assegnato al nesting {nesting.id}",
                        responsabile="Sistema",
                        nesting_id=nesting.id,
                        autoclave_id=nesting.autoclave_id,
                        timestamp=timestamp_assegnazione
                    )
                    db.add(log_nesting)
                    logs_aggiuntivi += 1
            
            # Se l'ODL è in cura, crea log di avvio cura
            if odl.status == "Cura":
                existing_cura_log = db.query(ODLLog).filter(
                    ODLLog.odl_id == odl.id,
                    ODLLog.evento == "avvio_cura"
                ).first()
                
                if not existing_cura_log:
                    # Simula timestamp di avvio cura (qualche ora fa)
                    timestamp_cura = odl.created_at + timedelta(hours=2)
                    
                    log_cura = ODLLog(
                        odl_id=odl.id,
                        evento="avvio_cura",
                        stato_precedente="Attesa Cura",
                        stato_nuovo="Cura",
                        descrizione="Avviato ciclo di cura",
                        responsabile="Sistema",
                        timestamp=timestamp_cura
                    )
                    db.add(log_cura)
                    logs_aggiuntivi += 1
            
            # Se l'ODL è finito, crea log di completamento
            if odl.status == "Finito":
                existing_finito_log = db.query(ODLLog).filter(
                    ODLLog.odl_id == odl.id,
                    ODLLog.evento == "finito"
                ).first()
                
                if not existing_finito_log:
                    # Simula timestamp di completamento
                    timestamp_finito = odl.updated_at
                    
                    log_finito = ODLLog(
                        odl_id=odl.id,
                        evento="finito",
                        stato_precedente="Cura",
                        stato_nuovo="Finito",
                        descrizione="ODL completato con successo",
                        responsabile="Sistema",
                        timestamp=timestamp_finito
                    )
                    db.add(log_finito)
                    logs_aggiuntivi += 1
        
        if logs_aggiuntivi > 0:
            db.commit()
            print(f"✅ Generati {logs_aggiuntivi} log aggiuntivi")
        else:
            print("ℹ️  Nessun log aggiuntivo da generare")
        
        print(f"\n🎉 Processo completato! Totale log generati: {logs_creati + logs_aggiuntivi}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante la generazione dei log: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main() 