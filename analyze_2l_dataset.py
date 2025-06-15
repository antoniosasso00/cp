#!/usr/bin/env python3
"""
Analisi rapida dataset 2L per identificare problemi eligibilità
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import sqlite3

def analyze_2l_dataset():
    """Analizza il dataset 2L direttamente dal database SQLite"""
    print("🔍 ANALISI DATASET 2L")
    print("=" * 50)
    
    try:
        # Connessione diretta al database SQLite
        db_path = os.path.join('backend', 'carbonpilot.db')
        if not os.path.exists(db_path):
            db_path = 'carbonpilot.db'  # Fallback
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prima verifica le tabelle disponibili
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelle disponibili: {', '.join(tables)}")
        
        # 1. Autoclavi 2L
        cursor.execute("""
            SELECT nome, lunghezza, larghezza_piano, peso_max_per_cavalletto_kg, usa_cavalletti
            FROM autoclavi 
            WHERE usa_cavalletti = 1
        """)
        autoclavi_2l = cursor.fetchall()
        
        print(f"\n🏭 AUTOCLAVI 2L: {len(autoclavi_2l)}")
        for nome, lunghezza, larghezza, peso_max_cav, usa_cav in autoclavi_2l:
            print(f"   {nome}: {lunghezza}x{larghezza}mm, peso_max_cavalletto: {peso_max_cav}kg")
        
        # 2. Verifica struttura tabella tools
        cursor.execute("PRAGMA table_info(tools);")
        tools_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n🔧 Colonne tabella tools: {', '.join(tools_columns)}")
        
        # 3. Verifica struttura tabella odl
        cursor.execute("PRAGMA table_info(odl);")
        odl_columns = [row[1] for row in cursor.fetchall()]
        print(f"🔧 Colonne tabella odl: {', '.join(odl_columns)}")
        
        # 4. ODL disponibili con tool (usando colonne corrette)
        # Usa part_number_tool invece di nome se disponibile
        name_column = 'part_number_tool' if 'part_number_tool' in tools_columns else 'id'
        
        cursor.execute(f"""
            SELECT o.id, t.peso, t.lunghezza_piano, t.larghezza_piano, t.{name_column}
            FROM odl o
            JOIN tools t ON o.tool_id = t.id
            WHERE o.status = 'in_attesa_cura'
            LIMIT 20
        """)
        odls_data = cursor.fetchall()
        
        print(f"\n📦 ODL DISPONIBILI: {len(odls_data)}")
        
        if len(odls_data) == 0:
            # Prova con stati diversi
            cursor.execute(f"""
                SELECT DISTINCT status FROM odl LIMIT 10
            """)
            stati = [row[0] for row in cursor.fetchall()]
            print(f"   Stati ODL disponibili: {', '.join(stati)}")
            
            # Prova con qualsiasi stato
            cursor.execute(f"""
                SELECT o.id, t.peso, t.lunghezza_piano, t.larghezza_piano, t.{name_column}, o.status
                FROM odl o
                JOIN tools t ON o.tool_id = t.id
                LIMIT 20
            """)
            odls_data = cursor.fetchall()
            print(f"   ODL totali (qualsiasi stato): {len(odls_data)}")
        
        # 5. Analisi eligibilità con criteri attuali
        eligible_current = 0
        eligible_relaxed = 0
        weight_issues = 0
        size_issues = 0
        
        print(f"\n📊 ANALISI ELIGIBILITÀ (primi 20 ODL):")
        print(f"{'ODL':<6} {'Peso':<8} {'Dimensioni':<12} {'Eligible':<10} {'Motivo'}")
        print("-" * 60)
        
        for row in odls_data:
            if len(row) == 6:  # Include stato
                odl_id, peso, lunghezza, larghezza, nome, stato = row
            else:
                odl_id, peso, lunghezza, larghezza, nome = row
                stato = 'unknown'
            
            peso = peso or 0
            lunghezza = lunghezza or 0
            larghezza = larghezza or 0
            
            # Criteri attuali (restrittivi) - QUESTI SONO I CRITERI DEL PROBLEMA!
            peso_ok = peso <= 50.0
            size_ok = lunghezza <= 800.0 and larghezza <= 500.0
            eligible = peso_ok and size_ok
            
            # Criteri rilassati
            peso_ok_relaxed = peso <= 100.0
            size_ok_relaxed = lunghezza <= 1200.0 and larghezza <= 800.0
            eligible_relaxed_item = peso_ok_relaxed and size_ok_relaxed
            
            if eligible:
                eligible_current += 1
            if eligible_relaxed_item:
                eligible_relaxed += 1
            
            if not peso_ok:
                weight_issues += 1
            if not size_ok:
                size_issues += 1
            
            # Motivo esclusione
            motivo = []
            if not peso_ok:
                motivo.append(f"peso>{50}kg")
            if not size_ok:
                motivo.append("dimensioni")
            motivo_str = ", ".join(motivo) if motivo else "OK"
            
            dimensioni_str = f"{lunghezza:.0f}x{larghezza:.0f}"
            eligible_str = "✅" if eligible else "❌"
            
            print(f"{odl_id:<6} {peso:<8.1f} {dimensioni_str:<12} {eligible_str:<10} {motivo_str}")
        
        print(f"\n🎯 RIEPILOGO ELIGIBILITÀ:")
        print(f"   Tool totali analizzati: {len(odls_data)}")
        print(f"   Eligible (criteri attuali): {eligible_current} ({eligible_current/len(odls_data)*100:.1f}%)")
        print(f"   Eligible (criteri rilassati): {eligible_relaxed} ({eligible_relaxed/len(odls_data)*100:.1f}%)")
        print(f"   Problemi peso (>{50}kg): {weight_issues}")
        print(f"   Problemi dimensioni: {size_issues}")
        
        # 6. Proposta correzione
        print(f"\n💡 PROPOSTA CORREZIONE:")
        if eligible_current == 0:
            print("   ❌ PROBLEMA CRITICO: Nessun tool eligible con criteri attuali!")
            print("   🔧 SOLUZIONE: Rilassare criteri eligibilità")
            print(f"      - Peso massimo: da 50kg → 100kg")
            print(f"      - Dimensioni: da 500x800mm → 800x1200mm")
            print(f"   📈 RISULTATO: {eligible_relaxed} tool diventerebbero eligible")
        else:
            print(f"   ✅ {eligible_current} tool già eligible")
            print(f"   📈 Con criteri rilassati: +{eligible_relaxed - eligible_current} tool")
        
        # 7. Test distribuzione peso
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN t.peso <= 25 THEN 1 END) as peso_25,
                COUNT(CASE WHEN t.peso <= 50 THEN 1 END) as peso_50,
                COUNT(CASE WHEN t.peso <= 75 THEN 1 END) as peso_75,
                COUNT(CASE WHEN t.peso <= 100 THEN 1 END) as peso_100
            FROM odl o
            JOIN tools t ON o.tool_id = t.id
        """)
        peso_stats = cursor.fetchone()
        
        print(f"\n📊 DISTRIBUZIONE PESO (tutti gli ODL):")
        if peso_stats and peso_stats[0] > 0:
            print(f"   ≤25kg: {peso_stats[1]}/{peso_stats[0]} ({peso_stats[1]/peso_stats[0]*100:.1f}%)")
            print(f"   ≤50kg: {peso_stats[2]}/{peso_stats[0]} ({peso_stats[2]/peso_stats[0]*100:.1f}%)")
            print(f"   ≤75kg: {peso_stats[3]}/{peso_stats[0]} ({peso_stats[3]/peso_stats[0]*100:.1f}%)")
            print(f"   ≤100kg: {peso_stats[4]}/{peso_stats[0]} ({peso_stats[4]/peso_stats[0]*100:.1f}%)")
        
        conn.close()
        
        return eligible_current, eligible_relaxed, len(odls_data)
        
    except Exception as e:
        print(f"❌ Errore analisi: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

def propose_fixes():
    """Propone le correzioni da implementare"""
    print(f"\n🔧 CORREZIONI DA IMPLEMENTARE:")
    print("=" * 50)
    
    print("1. 📝 MODIFICA CRITERI ELIGIBILITÀ in generation.py:")
    print("   Linea ~1541-1545:")
    print("   ```python")
    print("   can_use_cavalletto = (")
    print("       (tool.peso or 0) <= 100.0 and  # Era 50.0")
    print("       (tool.larghezza_piano or 0) <= 800.0 and  # Era 500.0")
    print("       (tool.lunghezza_piano or 0) <= 1200.0  # Era 800.0")
    print("   )")
    print("   ```")
    
    print("\n2. 🔄 MODIFICA ALGORITMO SEQUENZIALE in solver_2l.py:")
    print("   Implementare distribuzione intelligente invece di riempimento completo livello 0")
    
    print("\n3. ⚙️ PARAMETRI DEFAULT PIÙ BILANCIATI:")
    print("   - prefer_base_level = False (per alcuni scenari)")
    print("   - level_preference_weight = 0.05 (ridotto)")
    
    print("\n4. 🎨 MIGLIORAMENTI FRONTEND NestingCanvas2L.tsx:")
    print("   - Verifica corretta interpretazione dati level/z_position")
    print("   - Miglioramento visualizzazione cavalletti")
    print("   - Debug info per tool positioning")

if __name__ == "__main__":
    eligible_current, eligible_relaxed, total = analyze_2l_dataset()
    propose_fixes()
    
    if eligible_current == 0:
        print(f"\n⚠️ PROBLEMA CONFERMATO: Nessun tool eligible per livello 1!")
        print(f"   Questo spiega perché tutti i tool vengono posizionati su livello 0.")
    else:
        print(f"\n✅ {eligible_current} tool eligible trovati.") 