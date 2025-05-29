#!/usr/bin/env python3
"""
🧪 SEED SPECIFICO PER TEST NESTING
Crea dati di test ottimizzati per verificare:
- Sistema parametri nesting personalizzabili
- Preview nesting con parametri
- Generazione automatica nesting
- Calcolo posizioni 2D tool
"""

import sys
import os

# Aggiungi la directory backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.insert(0, parent_dir)

from models.db import SessionLocal, engine, Base
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.ciclo_cura import CicloCura
from models.nesting_result import NestingResult
from datetime import datetime, timedelta
import random

def create_test_nesting_data():
    """Crea dati di test specifici per il sistema nesting"""
    
    # Crea tutte le tabelle
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("🧪 Creazione seed per test nesting...")
        
        # ✅ STEP 1: Crea cicli di cura compatibili
        print("🔄 Creando cicli di cura...")
        
        cicli_cura = [
            CicloCura(
                nome="Ciclo Standard A",
                descrizione="Ciclo per parti in carbonio standard",
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,
                attiva_stasi2=False
            ),
            CicloCura(
                nome="Ciclo Rapido B",
                descrizione="Ciclo accelerato per parti piccole",
                temperatura_stasi1=160.0,
                pressione_stasi1=5.0,
                durata_stasi1=90,
                attiva_stasi2=False
            ),
            CicloCura(
                nome="Ciclo Intensivo C",
                descrizione="Ciclo per parti complesse",
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,
                attiva_stasi2=True,
                temperatura_stasi2=200.0,
                pressione_stasi2=8.0,
                durata_stasi2=60
            )
        ]
        
        for ciclo in cicli_cura:
            db.add(ciclo)
        
        db.flush()  # Per ottenere gli ID
        
        # ✅ STEP 2: Crea autoclavi disponibili con caratteristiche diverse
        print("🏭 Creando autoclavi disponibili...")
        
        autoclavi = [
            Autoclave(
                nome="Autoclave Alpha",
                codice="AUT-001",
                lunghezza=2000.0,  # 2000mm = 200cm
                larghezza_piano=1500.0,  # 1500mm = 150cm
                num_linee_vuoto=12,
                temperatura_max=220.0,
                pressione_max=10.0,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                produttore="Test Manufacturer",
                anno_produzione=2020,
                note="Autoclave grande per test nesting"
            ),
            Autoclave(
                nome="Autoclave Beta",
                codice="AUT-002", 
                lunghezza=1500.0,  # 1500mm = 150cm
                larghezza_piano=1200.0,  # 1200mm = 120cm
                num_linee_vuoto=8,
                temperatura_max=200.0,
                pressione_max=8.0,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                produttore="Test Manufacturer",
                anno_produzione=2019,
                note="Autoclave media standard"
            ),
            Autoclave(
                nome="Autoclave Gamma",
                codice="AUT-003",
                lunghezza=1000.0,  # 1000mm = 100cm
                larghezza_piano=800.0,  # 800mm = 80cm
                num_linee_vuoto=6,
                temperatura_max=180.0,
                pressione_max=6.0,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                produttore="Test Manufacturer",
                anno_produzione=2018,
                note="Autoclave piccola per test rapidi"
            )
        ]
        
        for autoclave in autoclavi:
            db.add(autoclave)
        
        db.flush()
        
        # ✅ STEP 3: Crea catalogo parti con dimensioni realistiche
        print("📋 Creando catalogo parti...")
        
        catalogo_parti = [
            # Parti piccole (per test padding/margine)
            Catalogo(
                part_number="CP-SMALL-001",
                descrizione="Componente piccolo A - Carbonio T700 - 50cm² - 0.2kg",
                categoria="Componenti",
                sotto_categoria="Piccoli",
                attivo=True
            ),
            Catalogo(
                part_number="CP-SMALL-002", 
                descrizione="Componente piccolo B - Carbonio T700 - 75cm² - 0.3kg",
                categoria="Componenti",
                sotto_categoria="Piccoli",
                attivo=True
            ),
            # Parti medie
            Catalogo(
                part_number="CP-MED-001",
                descrizione="Componente medio A - Carbonio T800 - 200cm² - 1.0kg",
                categoria="Componenti",
                sotto_categoria="Medi",
                attivo=True
            ),
            Catalogo(
                part_number="CP-MED-002",
                descrizione="Componente medio B - Carbonio T800 - 300cm² - 1.5kg",
                categoria="Componenti",
                sotto_categoria="Medi",
                attivo=True
            ),
            # Parti grandi
            Catalogo(
                part_number="CP-LARGE-001",
                descrizione="Componente grande A - Carbonio T1000 - 800cm² - 4.0kg",
                categoria="Componenti",
                sotto_categoria="Grandi",
                attivo=True
            ),
            Catalogo(
                part_number="CP-LARGE-002",
                descrizione="Componente grande B - Carbonio T1000 - 1200cm² - 6.0kg",
                categoria="Componenti",
                sotto_categoria="Grandi",
                attivo=True
            )
        ]
        
        for catalogo in catalogo_parti:
            db.add(catalogo)
        
        db.flush()
        
        # ✅ STEP 4: Crea parti con cicli di cura assegnati
        print("🔧 Creando parti...")
        
        parti = []
        for i, catalogo in enumerate(catalogo_parti):
            # Assegna ciclo di cura in modo bilanciato
            ciclo_index = i % len(cicli_cura)
            
            parte = Parte(
                part_number=catalogo.part_number,
                ciclo_cura_id=cicli_cura[ciclo_index].id,
                descrizione_breve=catalogo.descrizione.split(" - ")[0],  # Prima parte della descrizione
                num_valvole_richieste=random.randint(1, 4),  # 1-4 valvole
                note_produzione=f"Ciclo: {cicli_cura[ciclo_index].nome}"
            )
            parti.append(parte)
            db.add(parte)
        
        db.flush()
        
        # ✅ STEP 5: Crea tool con dimensioni realistiche
        print("🛠️ Creando tool...")
        
        # Definisci le aree target per ogni categoria
        aree_target = {
            "CP-SMALL-001": 50.0,
            "CP-SMALL-002": 75.0,
            "CP-MED-001": 200.0,
            "CP-MED-002": 300.0,
            "CP-LARGE-001": 800.0,
            "CP-LARGE-002": 1200.0
        }
        
        tools = []
        for i, parte in enumerate(parti):
            # Ottieni l'area target per questo part number
            area_target = aree_target.get(parte.part_number, 100.0)
            
            # Tool leggermente più grande della parte (margine 10-20%)
            area_tool = area_target * random.uniform(1.1, 1.2)
            
            # Calcola dimensioni rettangolari realistiche
            if area_tool <= 100:  # Parti piccole: più quadrate
                ratio = random.uniform(1.0, 1.5)
            elif area_tool <= 500:  # Parti medie: rettangolari
                ratio = random.uniform(1.2, 2.0)
            else:  # Parti grandi: molto rettangolari
                ratio = random.uniform(1.5, 3.0)
            
            larghezza_cm = (area_tool / ratio) ** 0.5
            lunghezza_cm = larghezza_cm * ratio
            
            # Converti in mm per il database
            lunghezza_mm = lunghezza_cm * 10
            larghezza_mm = larghezza_cm * 10
            
            # Calcola peso basato sull'area
            peso_kg = area_tool * 0.005  # 5g per cm²
            
            tool = Tool(
                part_number_tool=f"TOOL-{parte.part_number}",
                descrizione=f"Tool per {parte.part_number}",
                lunghezza_piano=lunghezza_mm,
                larghezza_piano=larghezza_mm,
                altezza=random.uniform(50, 150),  # Altezza variabile
                area=area_tool,
                peso=peso_kg,
                materiale="Alluminio 7075",
                note=f"Tool ottimizzato per {parte.descrizione_breve}"
            )
            tools.append(tool)
            db.add(tool)
        
        db.flush()
        
        # ✅ STEP 6: Crea ODL in stato "Attesa Cura" per test
        print("📦 Creando ODL in Attesa Cura...")
        
        odl_list = []
        for i in range(15):  # 15 ODL per test completo
            parte_index = i % len(parti)
            tool_index = i % len(tools)
            
            # Varia priorità e date
            priorita = random.choice([1, 2, 3, 4, 5])
            data_creazione = datetime.now() - timedelta(days=random.randint(1, 30))
            data_scadenza = data_creazione + timedelta(days=random.randint(7, 60))
            
            # Crea note con informazioni ciclo per il nesting
            ciclo_parte = parti[parte_index].ciclo_cura
            note_odl = f"Ciclo di cura: {ciclo_parte.nome} (ID: {ciclo_parte.id})\nPriorità: {priorita}\nTest nesting automatico"
            
            odl = ODL(
                numero_odl=f"ODL-TEST-{i+1:03d}",
                parte_id=parti[parte_index].id,
                tool_id=tools[tool_index].id,
                quantita=random.randint(1, 10),
                priorita=priorita,
                status="Attesa Cura",  # ✅ STATO CORRETTO PER NESTING
                data_creazione=data_creazione,
                data_scadenza=data_scadenza,
                note=note_odl,
                created_by="test_seed",
                assigned_to="operatore_test"
            )
            odl_list.append(odl)
            db.add(odl)
        
        db.flush()
        
        # ✅ STEP 7: Crea alcuni ODL in altri stati per controllo
        print("📋 Creando ODL in altri stati...")
        
        stati_altri = ["Preparazione", "Laminazione", "Cura", "Finito"]
        for i, stato in enumerate(stati_altri):
            odl_controllo = ODL(
                numero_odl=f"ODL-CTRL-{i+1:03d}",
                parte_id=parti[i % len(parti)].id,
                tool_id=tools[i % len(tools)].id,
                quantita=1,
                priorita=3,
                status=stato,
                data_creazione=datetime.now() - timedelta(days=5),
                data_scadenza=datetime.now() + timedelta(days=30),
                note=f"ODL di controllo in stato {stato}",
                created_by="test_seed",
                assigned_to="operatore_test"
            )
            db.add(odl_controllo)
        
        # ✅ STEP 8: Commit finale
        db.commit()
        
        # ✅ STEP 9: Stampa riassunto
        print("\n" + "="*60)
        print("🎉 SEED NESTING COMPLETATO!")
        print("="*60)
        print(f"✅ Cicli di cura creati: {len(cicli_cura)}")
        for ciclo in cicli_cura:
            print(f"   - {ciclo.nome} (ID: {ciclo.id})")
        
        print(f"\n✅ Autoclavi disponibili: {len(autoclavi)}")
        for autoclave in autoclavi:
            print(f"   - {autoclave.nome}: {autoclave.area_piano:.0f}cm² ({autoclave.num_linee_vuoto} valvole)")
        
        print(f"\n✅ ODL in Attesa Cura: {len(odl_list)}")
        for odl in odl_list[:5]:  # Mostra primi 5
            parte = next(p for p in parti if p.id == odl.parte_id)
            tool = next(t for t in tools if t.id == odl.tool_id)
            print(f"   - {odl.numero_odl}: {parte.part_number} ({tool.area:.0f}cm², {parte.num_valvole_richieste}v)")
        if len(odl_list) > 5:
            print(f"   ... e altri {len(odl_list)-5} ODL")
        
        print(f"\n✅ Catalogo parti: {len(catalogo_parti)} (da {min(c.area_cm2 for c in catalogo_parti):.0f} a {max(c.area_cm2 for c in catalogo_parti):.0f} cm²)")
        print(f"✅ Tool creati: {len(tools)}")
        print(f"✅ ODL controllo: {len(stati_altri)} (stati diversi)")
        
        print("\n🧪 PRONTO PER TEST:")
        print("   1. Preview nesting: GET /api/v1/nesting/preview")
        print("   2. Generazione automatica: POST /api/v1/nesting/generate")
        print("   3. Test parametri: ?padding=25&margine=60")
        print("   4. Frontend: http://localhost:3000/dashboard/curing/nesting")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la creazione del seed: {str(e)}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Avvio creazione seed per test nesting...")
    success = create_test_nesting_data()
    
    if success:
        print("\n✅ Seed completato con successo!")
        print("🔗 Avvia il backend e testa:")
        print("   cd backend && python -m uvicorn main:app --reload")
        print("   python test_nesting_integration.py")
    else:
        print("\n❌ Errore nella creazione del seed")
        exit(1) 