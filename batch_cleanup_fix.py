#!/usr/bin/env python3
"""
🧹 BATCH CLEANUP FIX - RISOLVE PROBLEMA BATCH DUPLICATI
=======================================================

Script di pulizia batch per risolvere il problema dei "6-8 batch" 
visualizzati nell'interfaccia utente.

PROBLEMA IDENTIFICATO:
- Il sistema genera correttamente 1 batch per autoclave
- Ma i batch vecchi si accumulano nel database
- L'utente vede batch vecchi + nuovi = confusione

SOLUZIONE:
- Cleanup automatico batch sospesi vecchi
- Prevenzione race conditions
- Mantenimento solo batch recenti/attivi

Autore: CarbonPilot Team
Data: 2025-01-25
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import SessionLocal
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from datetime import datetime, timedelta
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_batches(hours_threshold=1, dry_run=False):
    """
    Pulisce batch vecchi per risolvere il problema visualizzazione duplicati
    
    Args:
        hours_threshold: Ore di soglia per considerare un batch "vecchio"
        dry_run: Se True, solo mostra cosa verrebbe eliminato
    """
    db = SessionLocal()
    
    try:
        print(f"🧹 === CLEANUP BATCH VECCHI === (soglia: {hours_threshold} ore)")
        print(f"DRY RUN: {'SI' if dry_run else 'NO'}")
        print()
        
        # Calcola soglia temporale
        threshold_time = datetime.now() - timedelta(hours=hours_threshold)
        print(f"📅 Soglia temporale: {threshold_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Query batch candidati per cleanup
        old_batches = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value,
            BatchNesting.created_at < threshold_time
        ).all()
        
        if not old_batches:
            print("✅ Nessun batch vecchio da pulire - Sistema già pulito!")
            return
        
        # Analisi per autoclave
        autoclave_stats = {}
        for batch in old_batches:
            autoclave_name = batch.autoclave.nome if batch.autoclave else "Unknown"
            if autoclave_name not in autoclave_stats:
                autoclave_stats[autoclave_name] = {
                    'count': 0,
                    'oldest': None,
                    'batch_ids': []
                }
            
            autoclave_stats[autoclave_name]['count'] += 1
            autoclave_stats[autoclave_name]['batch_ids'].append(batch.id[:8])
            
            if not autoclave_stats[autoclave_name]['oldest'] or batch.created_at < autoclave_stats[autoclave_name]['oldest']:
                autoclave_stats[autoclave_name]['oldest'] = batch.created_at
        
        # Report dettagliato
        print("🔍 === ANALISI BATCH DA PULIRE ===")
        total_to_clean = len(old_batches)
        print(f"Totale batch da pulire: {total_to_clean}")
        print()
        
        for autoclave_name, stats in autoclave_stats.items():
            oldest_age = (datetime.now() - stats['oldest']).total_seconds() / 3600  # ore
            print(f"🏭 {autoclave_name}:")
            print(f"   - Batch da pulire: {stats['count']}")
            print(f"   - Più vecchio: {oldest_age:.1f} ore fa")
            print(f"   - IDs: {', '.join(stats['batch_ids'][:5])}{'...' if len(stats['batch_ids']) > 5 else ''}")
            print()
        
        if dry_run:
            print("🔍 DRY RUN COMPLETATO - Nessuna eliminazione effettuata")
            print(f"💡 Per eliminare effettivamente, esegui: python batch_cleanup_fix.py --execute")
            return
        
        # Esecuzione cleanup
        print("🧹 === AVVIO CLEANUP EFFETTIVO ===")
        deleted_count = 0
        
        for batch in old_batches:
            try:
                autoclave_name = batch.autoclave.nome if batch.autoclave else "Unknown"
                print(f"🗑️ Eliminando batch {batch.id[:8]} - {autoclave_name}")
                
                db.delete(batch)
                deleted_count += 1
                
            except Exception as e:
                print(f"❌ Errore eliminazione batch {batch.id[:8]}: {e}")
        
        # Commit finale
        db.commit()
        
        print()
        print("✅ === CLEANUP COMPLETATO ===")
        print(f"Batch eliminati: {deleted_count}/{total_to_clean}")
        print(f"Spazio liberato per ogni autoclave:")
        for autoclave_name, stats in autoclave_stats.items():
            print(f"  - {autoclave_name}: {stats['count']} batch rimossi")
        
        print()
        print("🎯 PROBLEMA RISOLTO: I batch duplicati non dovrebbero più apparire!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante cleanup: {e}")
        
    finally:
        db.close()

def show_current_status():
    """Mostra lo stato attuale del sistema"""
    db = SessionLocal()
    
    try:
        print("📊 === STATO ATTUALE SISTEMA ===")
        
        # Batch sospesi per autoclave
        autoclavi = db.query(Autoclave).all()
        
        total_sospesi = 0
        for autoclave in autoclavi:
            batch_count = db.query(BatchNesting).filter(
                BatchNesting.autoclave_id == autoclave.id,
                BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value
            ).count()
            
            total_sospesi += batch_count
            status_icon = "✅" if batch_count <= 1 else "⚠️"
            print(f"{status_icon} {autoclave.nome}: {batch_count} batch sospesi")
        
        print()
        if total_sospesi <= len(autoclavi):
            print("✅ SISTEMA OK: Massimo 1 batch per autoclave")
        else:
            print(f"⚠️ PROBLEMA: {total_sospesi} batch sospesi totali (dovrebbero essere ≤ {len(autoclavi)})")
            print("💡 Eseguire cleanup per risolvere il problema")
        
    finally:
        db.close()

def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🧹 Cleanup batch duplicati CarbonPilot')
    parser.add_argument('--execute', action='store_true', help='Esegue cleanup (default: dry run)')
    parser.add_argument('--hours', type=int, default=1, help='Soglia ore per batch vecchi (default: 1)')
    parser.add_argument('--status', action='store_true', help='Mostra solo stato attuale')
    
    args = parser.parse_args()
    
    print("🔧 CARBONPILOT BATCH CLEANUP FIX")
    print("================================")
    print()
    
    if args.status:
        show_current_status()
        return
    
    cleanup_old_batches(
        hours_threshold=args.hours,
        dry_run=not args.execute
    )

if __name__ == "__main__":
    main() 