#!/usr/bin/env python3
"""
🔍 DEBUG SISTEMA - ANALISI PROBLEMA MULTI-BATCH INTERMITTENTE
=============================================================

Analizza lo stato del sistema per identificare perché il multi-batch
a volte funziona e a volte no.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.db import SessionLocal
from models.autoclave import Autoclave
from models.batch_nesting import BatchNesting
from models.autoclave import StatoAutoclaveEnum
from models.batch_nesting import StatoBatchNestingEnum
from datetime import datetime, timedelta

def debug_sistema():
    print('🔍 === ANALISI APPROFONDITA STATO SISTEMA ===')
    print()
    
    db = SessionLocal()
    
    try:
        # 1. Stato autoclavi
        print('🏭 STATO AUTOCLAVI:')
        autoclavi = db.query(Autoclave).all()
        for autoclave in autoclavi:
            print(f'  - {autoclave.nome} (ID:{autoclave.id}): {autoclave.stato}')
        print()

        # 2. Batch in sospeso per autoclave
        print('📊 BATCH IN SOSPESO PER AUTOCLAVE:')
        batch_sospesi = db.query(BatchNesting).filter(
            BatchNesting.stato == StatoBatchNestingEnum.SOSPESO.value
        ).all()
        print(f'Totale batch sospesi: {len(batch_sospesi)}')

        autoclave_batch_count = {}
        for batch in batch_sospesi:
            autoclave_id = batch.autoclave_id
            if autoclave_id not in autoclave_batch_count:
                autoclave_batch_count[autoclave_id] = 0
            autoclave_batch_count[autoclave_id] += 1

        for autoclave in autoclavi:
            count = autoclave_batch_count.get(autoclave.id, 0)
            print(f'  - {autoclave.nome}: {count} batch sospesi')
        print()

        # 3. Autoclavi disponibili secondo la logica attuale
        print('✅ AUTOCLAVI DISPONIBILI (logica attuale):')
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        print(f'Totale disponibili: {len(autoclavi_disponibili)}')
        for autoclave in autoclavi_disponibili:
            batch_count = autoclave_batch_count.get(autoclave.id, 0)
            print(f'  - {autoclave.nome} (ID:{autoclave.id}): {batch_count} batch sospesi')
        print()

        # 4. Analisi batch recenti (ultimi 2 giorni)
        print('📅 BATCH GENERATI ULTIMI 2 GIORNI:')
        two_days_ago = datetime.now() - timedelta(days=2)
        recent_batches = db.query(BatchNesting).filter(
            BatchNesting.created_at >= two_days_ago
        ).order_by(BatchNesting.created_at.desc()).limit(10).all()
        
        print(f'Batch recenti: {len(recent_batches)}')
        for batch in recent_batches:
            autoclave_name = next((a.nome for a in autoclavi if a.id == batch.autoclave_id), 'Unknown')
            created_time = batch.created_at.strftime('%H:%M:%S') if batch.created_at else 'N/A'
            print(f'  - {created_time}: {autoclave_name} - {batch.stato} (ID: {batch.id[:8]}...)')
        print()

        # 5. Verifica possibili correlazioni temporali
        print('🔗 ANALISI CORRELAZIONI TEMPORALI:')
        if recent_batches:
            # Raggruppa batch per finestre di 5 minuti
            time_groups = {}
            for batch in recent_batches:
                if batch.created_at:
                    # Raggruppa per finestre di 5 minuti
                    time_key = batch.created_at.replace(second=0, microsecond=0)
                    time_key = time_key.replace(minute=(time_key.minute // 5) * 5)
                    
                    if time_key not in time_groups:
                        time_groups[time_key] = []
                    time_groups[time_key].append(batch)
            
            for time_key, batches in sorted(time_groups.items()):
                if len(batches) > 1:  # Potenziali multi-batch
                    autoclave_names = [next((a.nome for a in autoclavi if a.id == b.autoclave_id), 'Unknown') for b in batches]
                    unique_autoclavi = set(autoclave_names)
                    print(f'  {time_key.strftime("%H:%M")}: {len(batches)} batch - Autoclavi: {", ".join(unique_autoclavi)}')
                    if len(unique_autoclavi) > 1:
                        print('    ✅ MULTI-BATCH RILEVATO')
                    else:
                        print('    ❌ STESSA AUTOCLAVE')
        print()

        # 6. Possibili vincoli nascosti
        print('🚨 ANALISI POSSIBILI VINCOLI:')
        
        # Verifica se ci sono autoclavi "bloccate" da troppi batch
        problematic_autoclavi = []
        for autoclave in autoclavi_disponibili:
            count = autoclave_batch_count.get(autoclave.id, 0)
            if count > 20:  # Soglia arbitraria
                problematic_autoclavi.append((autoclave, count))
        
        if problematic_autoclavi:
            print('  ⚠️  AUTOCLAVI CON TROPPI BATCH SOSPESI:')
            for autoclave, count in problematic_autoclavi:
                print(f'    - {autoclave.nome}: {count} batch sospesi (possibile bottleneck)')
        
        # Verifica distribuzione ODL nei batch recenti
        print('  📊 DISTRIBUZIONE ODL NEI BATCH RECENTI:')
        for batch in recent_batches[:5]:  # Ultimi 5
            odl_count = len(batch.odl_ids) if batch.odl_ids else 0
            autoclave_name = next((a.nome for a in autoclavi if a.id == batch.autoclave_id), 'Unknown')
            print(f'    - {autoclave_name}: {odl_count} ODL')
        
        print()

        # 7. Verdetto finale
        print('🏁 === POSSIBILI CAUSE DEL PROBLEMA ===')
        
        if len(autoclavi_disponibili) < 2:
            print('❌ PROBLEMA PRINCIPALE: Meno di 2 autoclavi disponibili')
            print('   SOLUZIONE: Verificare stato autoclavi nel database')
        
        elif any(autoclave_batch_count.get(a.id, 0) > 30 for a in autoclavi_disponibili):
            print('❌ PROBLEMA SOSPETTO: Alcune autoclavi sovraccariche di batch sospesi')
            print('   SOLUZIONE: Confermare o eliminare batch vecchi')
            
        elif len(batch_sospesi) > 100:
            print('⚠️  PROBLEMA POSSIBILE: Troppi batch sospesi nel sistema')
            print('   SOLUZIONE: Cleanup batch vecchi o conferma batch pendenti')
            
        else:
            print('❓ PROBLEMA NASCOSTO: Possibile race condition o logica algoritmo')
            print('   SOLUZIONE: Analizzare log backend durante generazione')
        
        # Suggerimenti pratici
        print()
        print('🔧 AZIONI SUGGERITE:')
        print('1. Verificare log backend durante generazione multi-batch')
        print('2. Testare con meno ODL (2-3) per ridurre complessità')
        print('3. Confermare alcuni batch sospesi per liberare autoclavi')
        print('4. Verificare se problema è deterministico o casuale')
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_sistema() 