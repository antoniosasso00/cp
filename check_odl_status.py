#!/usr/bin/env python3
"""
🔍 Script per verificare gli status degli ODL nel database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.db import SessionLocal
from backend.models.odl import ODL
from backend.models.autoclave import Autoclave, StatoAutoclaveEnum
from sqlalchemy import func, text

def main():
    """Verifica gli status ODL e autoclavi nel database"""
    
    print("🔍 ANALISI STATO DATABASE - CarbonPilot")
    print("="*60)
    
    # Crea sessione database
    db = SessionLocal()
    
    try:
        # 1. Conta ODL per status
        print("\n📋 CONTEGGIO ODL PER STATUS:")
        print("-"*40)
        odl_status_counts = db.query(ODL.status, func.count(ODL.id)).group_by(ODL.status).all()
        
        total_odl = 0
        for status, count in odl_status_counts:
            print(f"   Status: '{status}' -> {count} ODL")
            total_odl += count
            
        print(f"\n📊 TOTALE ODL: {total_odl}")
        
        # 2. Status validi dal modello ODL (enum inline)
        print(f"\n✅ STATUS ODL VALIDI (da modello):")
        print("-"*40)
        valid_statuses = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"]
        for status in valid_statuses:
            print(f"   - {status}")
        
        # 3. Mostra primi 10 ODL
        print(f"\n🔍 PRIMI 10 ODL DEL DATABASE:")
        print("-"*40)
        odl_list = db.query(ODL).limit(10).all()
        for odl in odl_list:
            print(f"   🆔 ID: {odl.id} | Status: '{odl.status}' | Priorità: {odl.priorita}")
        
        # 4. Conta autoclavi per status (con gestione errori)
        print(f"\n🏭 CONTEGGIO AUTOCLAVI PER STATUS:")
        print("-"*40)
        try:
            # Prova prima con query raw per evitare errori enum
            result = db.execute(text("SELECT stato, COUNT(*) FROM autoclavi GROUP BY stato"))
            autoclave_status_counts = result.fetchall()
            
            total_autoclavi = 0
            for stato, count in autoclave_status_counts:
                print(f"   Stato: '{stato}' -> {count} autoclavi")
                total_autoclavi += count
                
            print(f"\n📊 TOTALE AUTOCLAVI: {total_autoclavi}")
            
            # Mostra primi 5 autoclavi
            print(f"\n🔍 PRIMI 5 AUTOCLAVI DEL DATABASE:")
            print("-"*40)
            result = db.execute(text("SELECT id, nome, stato, larghezza_piano, lunghezza FROM autoclavi LIMIT 5"))
            autoclavi_raw = result.fetchall()
            for autoclave in autoclavi_raw:
                print(f"   🆔 ID: {autoclave[0]} | Nome: '{autoclave[1]}' | Stato: '{autoclave[2]}' | Dim: {autoclave[3]}x{autoclave[4]}")
            
        except Exception as autoclave_error:
            print(f"   ❌ Errore query autoclavi: {str(autoclave_error)}")
            # Fallback con conteggio semplice
            total_autoclavi = db.execute(text("SELECT COUNT(*) FROM autoclavi")).scalar()
            print(f"   📊 TOTALE AUTOCLAVI (fallback): {total_autoclavi}")
        
        # 5. Verifica enum validi per autoclavi  
        print(f"\n✅ STATI AUTOCLAVE VALIDI (da enum):")
        print("-"*40)
        for stato in StatoAutoclaveEnum:
            print(f"   - {stato.value}")
            
        # 6. Conta ODL che potrebbero essere "candidati" per nesting
        print(f"\n🎯 ANALISI CANDIDATI PER NESTING:")
        print("-"*40)
        
        # ODL in preparazione
        odl_preparazione = db.query(ODL).filter(ODL.status == "Preparazione").count()
        print(f"   ODL in 'Preparazione': {odl_preparazione}")
        
        # ODL in attesa cura (attuale filtro nell'API)
        odl_attesa_cura = db.query(ODL).filter(ODL.status == "Attesa cura").count()
        print(f"   ODL in 'Attesa cura': {odl_attesa_cura}")
        
        # ODL in attesa cura con case corretto
        odl_attesa_cura_correct = db.query(ODL).filter(ODL.status == "Attesa Cura").count()
        print(f"   ODL in 'Attesa Cura' (case corretto): {odl_attesa_cura_correct}")
        
        # ODL in coda
        odl_in_coda = db.query(ODL).filter(ODL.status == "In Coda").count()
        print(f"   ODL in 'In Coda': {odl_in_coda}")
        
        # Suggerimenti
        print(f"\n💡 SUGGERIMENTI:")
        print("-"*40)
        if odl_attesa_cura_correct == 0:
            if odl_preparazione > 0:
                print(f"   ⚠️  Nessun ODL in 'Attesa Cura', ma {odl_preparazione} in 'Preparazione'")
                print(f"   💡 Considera di modificare il filtro per includere 'Preparazione'")
            elif odl_in_coda > 0:
                print(f"   ⚠️  Nessun ODL in 'Attesa Cura', ma {odl_in_coda} 'In Coda'")
                print(f"   💡 Considera di modificare il filtro per includere 'In Coda'")
            else:
                print(f"   ❌ Nessun ODL disponibile per il nesting")
                print(f"   💡 Controlla se ci sono ODL creati o cambia loro status")
        else:
            print(f"   ✅ {odl_attesa_cura_correct} ODL disponibili per nesting!")
            
        # Verifica differenza case-sensitive
        print(f"\n🔍 VERIFICA CASE-SENSITIVE:")
        print("-"*40)
        print(f"   'Attesa cura' (minuscolo): {odl_attesa_cura} ODL")
        print(f"   'Attesa Cura' (maiuscolo): {odl_attesa_cura_correct} ODL")
        if odl_attesa_cura != odl_attesa_cura_correct:
            print(f"   ⚠️  PROBLEMA IDENTIFICATO: Case sensitivity!")
            print(f"   💡 L'API cerca 'Attesa cura' ma i dati contengono 'Attesa Cura'")
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 