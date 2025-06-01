#!/usr/bin/env python3
"""
Script per creare dati aggiuntivi di test per i tempi standard.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import SessionLocal
from models.odl import ODL
from models.tempo_fase import TempoFase
from models.parte import Parte
from datetime import datetime, timedelta

def create_additional_test_data():
    """Crea dati aggiuntivi di test per verificare le statistiche."""
    db = SessionLocal()
    
    try:
        # Trova la parte di test
        parte = db.query(Parte).filter(Parte.part_number == 'TEST-STD-001').first()
        if not parte:
            print("❌ Parte di test non trovata")
            return
        
        print("🔄 Creazione dati aggiuntivi...")
        
        # Crea 2 ODL aggiuntivi per avere più dati
        for i in range(2, 4):
            odl = ODL(
                parte_id=parte.id,
                tool_id=1,  # Usa il primo tool disponibile
                status='Finito',
                include_in_std=True,
                priorita=1,
                note=f'ODL aggiuntivo #{i+1} per test statistiche'
            )
            db.add(odl)
            db.flush()
            
            # Aggiungi tempi fasi con durate diverse
            lam_duration = 25 + (i * 8)  # Durate: 41, 49
            cura_duration = 55 + (i * 15)  # Durate: 85, 100
            
            tempo_lam = TempoFase(
                odl_id=odl.id,
                fase='laminazione',
                inizio_fase=datetime.now() - timedelta(hours=2),
                fine_fase=datetime.now() - timedelta(hours=1, minutes=30),
                durata_minuti=lam_duration
            )
            db.add(tempo_lam)
            
            tempo_cura = TempoFase(
                odl_id=odl.id,
                fase='cura',
                inizio_fase=datetime.now() - timedelta(hours=1, minutes=30),
                fine_fase=datetime.now() - timedelta(minutes=30),
                durata_minuti=cura_duration
            )
            db.add(tempo_cura)
            
            print(f'✅ ODL #{i+1} creato con laminazione: {lam_duration}min, cura: {cura_duration}min')
        
        db.commit()
        print('✅ Dati aggiuntivi creati con successo!')
        
        # Mostra un riepilogo dei dati
        print("\n📊 Riepilogo dati per TEST-STD-001:")
        
        # Query per ottenere tutti i tempi di laminazione
        lam_times = db.query(TempoFase.durata_minuti).join(ODL).join(Parte).filter(
            Parte.part_number == 'TEST-STD-001',
            TempoFase.fase == 'laminazione',
            TempoFase.durata_minuti > 0,
            ODL.include_in_std == True,
            ODL.status == 'Finito'
        ).all()
        
        # Query per ottenere tutti i tempi di cura
        cura_times = db.query(TempoFase.durata_minuti).join(ODL).join(Parte).filter(
            Parte.part_number == 'TEST-STD-001',
            TempoFase.fase == 'cura',
            TempoFase.durata_minuti > 0,
            ODL.include_in_std == True,
            ODL.status == 'Finito'
        ).all()
        
        lam_values = [t[0] for t in lam_times]
        cura_values = [t[0] for t in cura_times]
        
        print(f"Laminazione: {len(lam_values)} osservazioni - {lam_values}")
        print(f"Cura: {len(cura_values)} osservazioni - {cura_values}")
        
        if lam_values:
            import statistics
            print(f"  Media laminazione: {statistics.mean(lam_values):.1f}min")
            print(f"  Mediana laminazione: {statistics.median(lam_values):.1f}min")
        
        if cura_values:
            print(f"  Media cura: {statistics.mean(cura_values):.1f}min")
            print(f"  Mediana cura: {statistics.median(cura_values):.1f}min")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante la creazione dei dati: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_additional_test_data() 