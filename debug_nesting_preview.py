"""
Script di debug per analizzare il problema della preview del nesting
"""
import sys
import os
sys.path.append('./backend')

import sqlite3
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, joinedload
    
    # Setup database connection
    DATABASE_URL = "sqlite:///./carbonpilot.db"
    engine = create_engine(DATABASE_URL, echo=False)
    
    from backend.models.nesting_result import NestingResult
    from backend.models.odl import ODL
    
    SQLAlchemy_available = True
except ImportError as e:
    print(f"⚠️ SQLAlchemy non disponibile: {e}")
    SQLAlchemy_available = False

def debug_nesting_data():
    print("🔍 DEBUG: Analisi dati nesting preview")
    print("=" * 60)
    
    # 1. Controllo diretto del database
    print("\n1️⃣ Controllo tabelle database:")
    conn = sqlite3.connect('carbonpilot.db')
    cursor = conn.cursor()
    
    # Conta record nelle tabelle principali
    cursor.execute('SELECT COUNT(*) FROM nesting_results')
    nesting_count = cursor.fetchone()[0]
    print(f"   - nesting_results: {nesting_count} record")
    
    cursor.execute('SELECT COUNT(*) FROM odl')
    odl_count = cursor.fetchone()[0]
    print(f"   - odl: {odl_count} record")
    
    cursor.execute('SELECT COUNT(*) FROM nesting_result_odl')
    association_count = cursor.fetchone()[0]
    print(f"   - nesting_result_odl: {association_count} record")
    
    # 1.5. Vediamo quali nesting esistono
    print(f"\n1.5️⃣ Nesting esistenti:")
    cursor.execute('SELECT id, stato, autoclave_id, created_at FROM nesting_results ORDER BY id')
    nesting_list = cursor.fetchall()
    for nesting in nesting_list:
        print(f"   - ID {nesting[0]}: stato={nesting[1]}, autoclave_id={nesting[2]}, created={nesting[3]}")
    
    if not nesting_list:
        print("   ❌ Nessun nesting trovato!")
        conn.close()
        return
    
    # Prendi il primo nesting disponibile
    first_nesting_id = nesting_list[0][0]
    print(f"\n🎯 Analizziamo il nesting ID {first_nesting_id}:")
    
    # 2. Analisi dettagliata nesting
    print(f"\n2️⃣ Analisi nesting ID {first_nesting_id}:")
    cursor.execute('SELECT * FROM nesting_results WHERE id = ?', (first_nesting_id,))
    nesting_data = cursor.fetchone()
    if nesting_data:
        print(f"   - Stato: {nesting_data[2]}")  # stato è la 3a colonna
        print(f"   - ODL IDs (JSON): {nesting_data[4]}")  # odl_ids
        print(f"   - Posizioni tool (JSON): {nesting_data[19] if len(nesting_data) > 19 else 'N/A'}")  # posizioni_tool
    else:
        print(f"   ❌ Nesting {first_nesting_id} non trovato!")
        return
    
    # 3. Controllo associazioni per nesting
    print(f"\n3️⃣ Associazioni ODL per nesting {first_nesting_id}:")
    cursor.execute('SELECT odl_id FROM nesting_result_odl WHERE nesting_result_id = ?', (first_nesting_id,))
    associated_odls = [row[0] for row in cursor.fetchall()]
    print(f"   - ODL associati via tabella intermedia: {associated_odls}")
    
    # 4. Dettagli ODL associati
    if associated_odls:
        print(f"\n4️⃣ Dettagli ODL associati:")
        for odl_id in associated_odls:
            cursor.execute('''
                SELECT o.id, o.status, o.parte_id, o.tool_id, p.part_number, t.part_number_tool
                FROM odl o
                LEFT JOIN parti p ON o.parte_id = p.id
                LEFT JOIN tools t ON o.tool_id = t.id
                WHERE o.id = ?
            ''', (odl_id,))
            odl_details = cursor.fetchone()
            if odl_details:
                print(f"   - ODL {odl_details[0]}: status={odl_details[1]}, parte={odl_details[4]}, tool={odl_details[5]}")
    
    conn.close()
    
    # 5. Test con SQLAlchemy
    if SQLAlchemy_available:
        print(f"\n5️⃣ Test con SQLAlchemy ORM:")
        try:
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Query con joinedload come nel service
            nesting = session.query(NestingResult).options(
                joinedload(NestingResult.autoclave),
                joinedload(NestingResult.odl_list).joinedload(ODL.tool),
                joinedload(NestingResult.odl_list).joinedload(ODL.parte)
            ).filter(NestingResult.id == first_nesting_id).first()
            
            if nesting:
                print(f"   - Nesting trovato: ID {nesting.id}")
                print(f"   - Autoclave: {nesting.autoclave.nome if nesting.autoclave else 'None'}")
                print(f"   - ODL list length: {len(nesting.odl_list) if nesting.odl_list else 'None'}")
                
                if nesting.odl_list:
                    for i, odl in enumerate(nesting.odl_list):
                        print(f"     - ODL {i+1}: ID={odl.id}, status={odl.status}")
                        print(f"       - Tool: {odl.tool.part_number_tool if odl.tool else 'None'}")
                        print(f"       - Parte: {odl.parte.part_number if odl.parte else 'None'}")
                else:
                    print("   ❌ Nessun ODL nella relazione odl_list!")
            else:
                print(f"   ❌ Nesting {first_nesting_id} non trovato con SQLAlchemy!")
            
            session.close()
            
        except Exception as e:
            print(f"   ❌ Errore SQLAlchemy: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Debug completato")

if __name__ == "__main__":
    debug_nesting_data() 