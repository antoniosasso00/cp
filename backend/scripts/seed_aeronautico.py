#!/usr/bin/env python3
"""
Script per il seeding del database con dati aeronautici realistici.

Genera:
- 45 ODL in stato "Attesa Cura"
- Tool di varie dimensioni (fino a 450mm max)
- 2 valvole per ogni tool
- Peso nullo per tutti i tool
- 4 cicli di cura diversi
- 3 autoclavi con specifiche aeronautiche

Utilizzo:
    python backend/scripts/seed_aeronautico.py
"""

import sys
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Aggiungi il path del backend per import dei modelli
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.catalogo import Catalogo
from models.parte import Parte  
from models.tool import Tool
from models.odl import ODL
from models.ciclo_cura import CicloCura
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.associations import parte_tool_association

# Configurazione database - usa lo stesso path del backend
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
db_path = backend_dir / "carbonpilot.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clear_existing_data(session):
    """Pulisce i dati esistenti per evitare conflitti"""
    print("🧹 Pulizia dati esistenti...")
    
    # Ordine di eliminazione per rispettare le foreign key
    session.execute(text("DELETE FROM nesting_result_odl"))
    session.execute(text("DELETE FROM parte_tool_association"))
    session.execute(text("DELETE FROM odl"))
    session.execute(text("DELETE FROM parti"))
    session.execute(text("DELETE FROM tools"))
    session.execute(text("DELETE FROM cataloghi"))
    session.execute(text("DELETE FROM cicli_cura"))
    session.execute(text("DELETE FROM autoclavi"))
    
    session.commit()
    print("✅ Dati esistenti eliminati")

def create_cicli_cura(session):
    """Crea 4 cicli di cura aeronautici diversi"""
    print("🔄 Creazione cicli di cura aeronautici...")
    
    cicli = [
        {
            "nome": "AERO_180_STANDARD",
            "descrizione": "Ciclo standard per compositi aeronautici - 180°C",
            "temperatura_stasi1": 180.0,
            "pressione_stasi1": 7.0,
            "durata_stasi1": 120,
            "attiva_stasi2": True,
            "temperatura_stasi2": 180.0,
            "pressione_stasi2": 7.0,
            "durata_stasi2": 90
        },
        {
            "nome": "AERO_160_DELICATE",
            "descrizione": "Ciclo delicato per compositi sensibili - 160°C",
            "temperatura_stasi1": 160.0,
            "pressione_stasi1": 6.0,
            "durata_stasi1": 150,
            "attiva_stasi2": False,
            "temperatura_stasi2": None,
            "pressione_stasi2": None,
            "durata_stasi2": None
        },
        {
            "nome": "AERO_200_REINFORCED",
            "descrizione": "Ciclo rinforzato per compositi strutturali - 200°C",
            "temperatura_stasi1": 200.0,
            "pressione_stasi1": 8.5,
            "durata_stasi1": 180,
            "attiva_stasi2": True,
            "temperatura_stasi2": 200.0,
            "pressione_stasi2": 8.5,
            "durata_stasi2": 60
        },
        {
            "nome": "AERO_220_EXTREME",
            "descrizione": "Ciclo estremo per compositi ad alte prestazioni - 220°C",
            "temperatura_stasi1": 220.0,
            "pressione_stasi1": 10.0,
            "durata_stasi1": 240,
            "attiva_stasi2": True,
            "temperatura_stasi2": 200.0,
            "pressione_stasi2": 8.0,
            "durata_stasi2": 45
        }
    ]
    
    cicli_creati = []
    for ciclo_data in cicli:
        ciclo = CicloCura(**ciclo_data)
        session.add(ciclo)
        cicli_creati.append(ciclo)
    
    session.commit()
    print(f"✅ Creati {len(cicli_creati)} cicli di cura")
    return cicli_creati

def create_autoclavi(session):
    """Crea 3 autoclavi con specifiche aeronautiche realistiche e supporto 2L"""
    print("🏭 Creazione autoclavi aeronautiche con supporto 2L...")
    
    autoclavi_data = [
        {
            "nome": "AEROSPACE_PANINI_XL",
            "codice": "ASP_001",
            "lunghezza": 8000.0,  # 8m - GRANDE
            "larghezza_piano": 1900.0,  # 1.9m - STANDARD
            "num_linee_vuoto": 16,
            "temperatura_max": 250.0,
            "pressione_max": 12.0,
            "max_load_kg": 3000.0,
            "stato": StatoAutoclaveEnum.DISPONIBILE,
            "produttore": "Panini Aerospace",
            "anno_produzione": 2021,
            "note": "Autoclave extra-large per compositi aeronautici - 8m x 1.9m - Supporto cavalletti 2L",
            # 🆕 SUPPORTO 2L CON CAVALLETTI
            "usa_cavalletti": True,
            "altezza_cavalletto_standard": 100.0,  # 100mm come da specifiche
            "max_cavalletti": 6,  # Molti cavalletti per autoclave grande
            "clearance_verticale": 50.0,  # 50mm di clearance
            "peso_max_per_cavalletto_kg": 300.0  # 300kg per cavalletto - capacità elevata
        },
        {
            "nome": "AEROSPACE_ISMAR_L",
            "codice": "ASI_002", 
            "lunghezza": 4500.0,  # 4.5m - MEDIA
            "larghezza_piano": 1900.0,  # 1.9m - STANDARD
            "num_linee_vuoto": 12,
            "temperatura_max": 230.0,
            "pressione_max": 10.0,
            "max_load_kg": 2000.0,
            "stato": StatoAutoclaveEnum.DISPONIBILE,
            "produttore": "ISMAR Systems",
            "anno_produzione": 2020,
            "note": "Autoclave large per componenti strutturali - 4.5m x 1.9m - Supporto cavalletti 2L",
            # 🆕 SUPPORTO 2L CON CAVALLETTI LIMITATO
            "usa_cavalletti": True,
            "altezza_cavalletto_standard": 100.0,  # 100mm come da specifiche
            "max_cavalletti": 4,  # Cavalletti limitati per autoclave media
            "clearance_verticale": 40.0,  # 40mm di clearance
            "peso_max_per_cavalletto_kg": 250.0  # 250kg per cavalletto - capacità media
        },
        {
            "nome": "AEROSPACE_MAROSO_M",
            "codice": "ASM_003",
            "lunghezza": 2900.0,  # 2.9m - COMPATTA
            "larghezza_piano": 1900.0,  # 1.9m - STANDARD
            "num_linee_vuoto": 8,
            "temperatura_max": 200.0,
            "pressione_max": 8.0,
            "max_load_kg": 1500.0,
            "stato": StatoAutoclaveEnum.DISPONIBILE,
            "produttore": "Maroso Technologies",
            "anno_produzione": 2019,
            "note": "Autoclave medium per componenti specializzati - 2.9m x 1.9m - Solo piano base",
            # 🆕 SOLO PIANO BASE (NESSUN CAVALLETTO)
            "usa_cavalletti": False,
            "altezza_cavalletto_standard": None,
            "max_cavalletti": 0,
            "clearance_verticale": None,
            "peso_max_per_cavalletto_kg": None  # Non usa cavalletti
        }
    ]
    
    autoclavi_create = []
    for autoclave_data in autoclavi_data:
        autoclave = Autoclave(**autoclave_data)
        session.add(autoclave)
        autoclavi_create.append(autoclave)
    
    session.commit()
    print(f"✅ Create {len(autoclavi_create)} autoclavi con configurazione 2L")
    return autoclavi_create

def generate_aeronautical_tools(session):
    """Genera tool aeronautici con aspect ratio completamente casuali e dimensioni varie"""
    print("🔧 Generazione tools aeronautici...")
    
    # Pattern aeronautici comuni (senza vincoli di ratio)
    patterns = [
        ("WING", "Spar", "Longeron wing structure"),
        ("FUSE", "Frame", "Fuselage frame component"),
        ("CTRL", "Surface", "Control surface element"),
        ("LAND", "Gear", "Landing gear component"),
        ("DOOR", "Panel", "Door panel structure"),
        ("NACELLE", "Cowl", "Engine nacelle cowling"),
        ("STAB", "Rib", "Stabilizer rib structure"),
        ("FLAP", "Segment", "Flap segment component"),
        ("RUDDER", "Section", "Rudder section panel"),
        ("AILERON", "Tab", "Aileron tab element"),
        ("ENGINE", "Mount", "Engine mounting bracket"),
        ("ANTENNA", "Array", "Antenna array panel"),
        ("SENSOR", "Housing", "Sensor housing unit"),
        ("WIRE", "Tray", "Wire management tray"),
        ("VENT", "Duct", "Ventilation duct section")
    ]
    
    # Range di dimensioni base (larghezza in mm) - più ampio
    base_width_ranges = [
        (60, 180),     # Piccoli
        (150, 350),    # Piccoli-medi
        (300, 500),    # Medi
        (450, 700),    # Medi-grandi
        (650, 950),    # Grandi
        (900, 1200),   # Molto grandi
        (1100, 1500)   # Extra grandi
    ]
    
    # Distribuzione aspect ratio MOLTO più casuale e allungata
    # Peso maggiore sui ratio alti, pochi casi quasi-quadrati
    aspect_ratio_distribution = [
        # Ratio, Peso nella distribuzione
        (1.2, 5),    # Quasi quadrato - RARO (5%)
        (1.5, 8),    # Leggermente rettangolare - POCO (8%)
        (2.0, 12),   # Rettangolare medio - NORMALE (12%)
        (2.5, 15),   # Rettangolare - COMUNE (15%)
        (3.0, 15),   # Lungo - COMUNE (15%)
        (4.0, 12),   # Molto lungo - NORMALE (12%)
        (5.0, 10),   # Estremamente lungo - OCCASIONALE (10%)
        (6.0, 8),    # Ultra lungo - POCO (8%)
        (7.0, 6),    # Estremo - RARO (6%)
        (8.0, 4),    # Massimo - MOLTO RARO (4%)
        (10.0, 3),   # Eccezionale - RARISSIMO (3%)
        (12.0, 2)    # Ultra eccezionale - ECCEZIONALE (2%)
    ]
    
    # Crea lista pesata per selezione casuale
    weighted_ratios = []
    for ratio, weight in aspect_ratio_distribution:
        weighted_ratios.extend([ratio] * weight)
    
    tools_created = []
    
    for i in range(45):
        # Seleziona pattern casuale
        prefix, component, description = random.choice(patterns)
        
        # Seleziona larghezza base casuale
        width_range = random.choice(base_width_ranges)
        larghezza = round(random.uniform(width_range[0], width_range[1]), 1)
        
        # Seleziona aspect ratio casuale dalla distribuzione pesata
        ratio = random.choice(weighted_ratios)
        
        # Aggiungi variazione casuale al ratio (±15%)
        ratio_variation = random.uniform(0.85, 1.15)
        final_ratio = ratio * ratio_variation
        
        # Calcola lunghezza
        lunghezza = round(larghezza * final_ratio, 1)
        
        # Occasionalmente inverti le dimensioni per ancora più varietà (15% chance)
        if random.random() < 0.15:
            larghezza, lunghezza = lunghezza, larghezza
            final_ratio = 1.0 / final_ratio
        
        # Assicurati che rientri nell'autoclave più piccola (2900x1900mm)
        max_length = 2850.0  # Margine di sicurezza
        max_width = 1850.0   # Margine di sicurezza
        
        if lunghezza > max_length:
            lunghezza = max_length
            larghezza = min(lunghezza / final_ratio, max_width)
        if larghezza > max_width:
            larghezza = max_width
            lunghezza = min(larghezza * final_ratio, max_length)
        
        # Assicurati dimensioni minime ragionevoli
        larghezza = max(larghezza, 80.0)
        lunghezza = max(lunghezza, 80.0)
        
        # Arrotonda per numeri puliti
        larghezza = round(larghezza, 1)
        lunghezza = round(lunghezza, 1)
        
        # Ricalcola il ratio finale effettivo
        actual_ratio = lunghezza / larghezza
        
        # Genera peso realistico basato su dimensioni e materiale
        area_m2 = (lunghezza * larghezza) / 1_000_000
        material = random.choice(["Aluminum", "Steel", "Composite", "Invar", "Titanium"])
        
        # Densità tipiche per materiali tool (kg/m² per spessore ~50mm)
        density_map = {
            "Aluminum": 135,    # 2700 kg/m³ * 0.05m
            "Steel": 390,       # 7800 kg/m³ * 0.05m  
            "Composite": 75,    # 1500 kg/m³ * 0.05m
            "Invar": 405,       # 8100 kg/m³ * 0.05m
            "Titanium": 225     # 4500 kg/m³ * 0.05m
        }
        
        peso = round(area_m2 * density_map[material], 1)
        
        tool_data = {
            "part_number_tool": f"{prefix}_{component}_{str(i+1).zfill(3)}",
            "descrizione": f"{description} - {lunghezza:.0f}x{larghezza:.0f}mm (ratio {actual_ratio:.1f}:1)",
            "lunghezza_piano": lunghezza,
            "larghezza_piano": larghezza,
            "peso": peso,
            "materiale": material,
            "disponibile": True,
            "note": f"Aeronautical tool - {material} - {peso}kg - Aspect ratio {actual_ratio:.1f}:1"
        }
        
        tool = Tool(**tool_data)
        session.add(tool)
        tools_created.append(tool)
    
    session.commit()
    print(f"✅ Creati {len(tools_created)} tools aeronautici con aspect ratio casuali e variabili")
    return tools_created

def generate_aeronautical_catalog(session, tools, cicli_cura):
    """Genera catalogo per le parti aeronautiche"""
    print("📋 Generazione catalogo aeronautico...")
    
    catalog_entries = []
    
    for i, tool in enumerate(tools):
        # Estrai il prefisso dal part_number_tool per coerenza
        prefix = tool.part_number_tool.split('_')[0]
        
        catalog_data = {
            "part_number": f"PN_{prefix}_{str(i+1).zfill(4)}",
            "descrizione": f"Aeronautical composite part - {tool.part_number_tool}",
            "categoria": "AERONAUTICAL_COMPOSITE",
            "sotto_categoria": random.choice(["Primary Structure", "Secondary Structure", "Control Surface", "Landing Gear"]),
            "attivo": True,
            "note": f"High-performance composite part for aerospace applications - {random.choice(['Airbus', 'Boeing', 'Leonardo', 'Safran', 'Collins'])}"
        }
        
        catalog = Catalogo(**catalog_data)
        session.add(catalog)
        catalog_entries.append(catalog)
    
    session.commit()
    print(f"✅ Creati {len(catalog_entries)} entry nel catalogo")
    return catalog_entries

def generate_aeronautical_parts(session, catalog_entries, tools, cicli_cura):
    """Genera parti aeronautiche"""
    print("🏗️ Generazione parti aeronautiche...")
    
    parts_created = []
    
    for i, (catalog, tool) in enumerate(zip(catalog_entries, tools)):
        # Assegna ciclo di cura casuale
        ciclo = random.choice(cicli_cura)
        
        part_data = {
            "part_number": catalog.part_number,
            "descrizione_breve": f"Composite part {catalog.part_number}",
            "num_valvole_richieste": 2,  # 2 valvole per ogni tool come richiesto
            "ciclo_cura_id": ciclo.id,
            "note_produzione": f"Requires {ciclo.nome} curing cycle - Handle with care"
        }
        
        part = Parte(**part_data)
        session.add(part)
        parts_created.append(part)
    
    session.commit()
    
    # Crea associazioni parte-tool
    for part, tool in zip(parts_created, tools):
        part.tools.append(tool)
    
    session.commit()
    print(f"✅ Create {len(parts_created)} parti aeronautiche")
    return parts_created

def generate_aeronautical_odl(session, parts):
    """Genera 45 ODL in stato 'Attesa Cura'"""
    print("📋 Generazione ODL aeronautici...")
    
    odl_created = []
    
    for i, part in enumerate(parts):
        # Genera numero ODL nel formato aeronautico
        year = datetime.now().year
        odl_number = f"AERO_{year}_{str(i+1).zfill(4)}"
        
        # Priorità basata su criticità (componenti strutturali hanno priorità più alta)
        priority = 1
        if "WING" in part.part_number or "FUSE" in part.part_number:
            priority = 3  # Alta priorità per strutture primarie
        elif "CTRL" in part.part_number or "LAND" in part.part_number:
            priority = 2  # Media priorità per sistemi di controllo
        
        # Seleziona tool casuale tra quelli associati alla parte
        tool = part.tools[0] if part.tools else None
        
        if not tool:
            print(f"⚠️ Parte {part.part_number} non ha tool associati, saltata")
            continue
        
        odl_data = {
            "numero_odl": odl_number,
            "parte_id": part.id,
            "tool_id": tool.id,
            "priorita": priority,
            "status": "Attesa Cura",  # Tutti in attesa di cura come richiesto
            "include_in_std": True,
            "note": f"Aeronautical composite part ready for curing - Priority {priority}",
            "motivo_blocco": None
        }
        
        odl = ODL(**odl_data)
        session.add(odl)
        odl_created.append(odl)
    
    session.commit()
    print(f"✅ Creati {len(odl_created)} ODL in stato 'Attesa Cura'")
    return odl_created

def print_summary(cicli_cura, autoclavi, tools, parts, odl_list):
    """Stampa un riepilogo dei dati generati"""
    print("\n" + "="*60)
    print("🚀 SEED AERONAUTICO 2L COMPLETATO CON SUCCESSO!")
    print("="*60)
    
    print(f"\n📊 RIEPILOGO DATI GENERATI:")
    print(f"   • Cicli di cura: {len(cicli_cura)}")
    print(f"   • Autoclavi: {len(autoclavi)}")
    print(f"   • Tools: {len(tools)}")
    print(f"   • Parti: {len(parts)}")
    print(f"   • ODL: {len(odl_list)}")
    
    print(f"\n🔧 SPECIFICHE TOOLS:")
    lunghezze = [t.lunghezza_piano for t in tools]
    larghezze = [t.larghezza_piano for t in tools]
    ratios = [t.lunghezza_piano / t.larghezza_piano for t in tools]
    pesi = [t.peso for t in tools if t.peso]
    
    print(f"   • Lunghezza: {min(lunghezze):.0f}-{max(lunghezze):.0f}mm (media: {sum(lunghezze)/len(lunghezze):.0f}mm)")
    print(f"   • Larghezza: {min(larghezze):.0f}-{max(larghezze):.0f}mm (media: {sum(larghezze)/len(larghezze):.0f}mm)")
    print(f"   • Rapporti L/W: {min(ratios):.1f}:1 - {max(ratios):.1f}:1 (media: {sum(ratios)/len(ratios):.1f}:1)")
    print(f"   • Peso: {min(pesi):.1f}-{max(pesi):.1f}kg (media: {sum(pesi)/len(pesi):.1f}kg)")
    print(f"   • Valvole per tool: 2")
    
    print(f"\n🏭 AUTOCLAVI CON SUPPORTO 2L:")
    for autoclave in autoclavi:
        cavalletti_status = "🟢 2L ATTIVO" if autoclave.usa_cavalletti else "🔴 Solo piano base"
        print(f"   • {autoclave.nome}: {autoclave.lunghezza}x{autoclave.larghezza_piano}mm - {cavalletti_status}")
        print(f"     Linee vuoto: {autoclave.num_linee_vuoto}, Max load: {autoclave.max_load_kg}kg")
        
        if autoclave.usa_cavalletti:
            print(f"     🔧 Cavalletti: H={autoclave.altezza_cavalletto_standard}mm, Max={autoclave.max_cavalletti}, Clearance={autoclave.clearance_verticale}mm")
            print(f"     🔄 Livello 0: Piano base autoclave")
            print(f"     🔄 Livello 1: Cavalletti supporto (+{autoclave.altezza_cavalletto_standard}mm)")
            print(f"     📊 Peso per cavalletto: {autoclave.peso_max_per_cavalletto_kg}kg")
            max_peso_livello_1 = autoclave.peso_max_per_cavalletto_kg * autoclave.max_cavalletti
            print(f"     📊 Peso max livello 1: {max_peso_livello_1:.0f}kg ({autoclave.max_cavalletti} cavalletti × {autoclave.peso_max_per_cavalletto_kg}kg)")
            print(f"     🔒 Vincolo totale: Max {autoclave.max_load_kg}kg complessivi")
    
    print(f"\n🔄 CICLI DI CURA:")
    for ciclo in cicli_cura:
        stasi2_text = f" + {ciclo.temperatura_stasi2}°C x {ciclo.durata_stasi2}min" if ciclo.attiva_stasi2 else ""
        print(f"   • {ciclo.nome}: {ciclo.temperatura_stasi1}°C x {ciclo.durata_stasi1}min{stasi2_text}")
    
    print(f"\n📋 ODL STATUS:")
    print(f"   • Tutti i {len(odl_list)} ODL sono in stato 'Attesa Cura'")
    
    priority_counts = {}
    for odl in odl_list:
        priority_counts[odl.priorita] = priority_counts.get(odl.priorita, 0) + 1
    
    print(f"   • Distribuzione priorità:")
    for priority, count in sorted(priority_counts.items()):
        print(f"     - Priorità {priority}: {count} ODL")
    
    print(f"\n🆕 MODALITÀ 2L SUPPORTATA:")
    cavalletti_count = sum(1 for a in autoclavi if a.usa_cavalletti)
    print(f"   • Autoclavi con supporto cavalletti: {cavalletti_count}/{len(autoclavi)}")
    print(f"   • Livello 0: Piano base dell'autoclave")
    print(f"   • Livello 1: Cavalletti di supporto (100mm altezza)")
    print(f"   • Peso dinamico: Basato su capacità × numero cavalletti utilizzati")
    print(f"   • Compatibilità: Multi-batch supportato")
    print(f"   • Vincolo: Peso totale ≤ carico massimo autoclave")
    
    print(f"\n✅ Il database è ora pronto per testare il nesting aeronautico 2L!")
    print("="*60)

def main():
    """Funzione principale per il seeding"""
    print("🚀 AVVIO SEED AERONAUTICO")
    print("="*50)
    
    # Crea le tabelle se non esistono
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        # 1. Pulisci dati esistenti
        clear_existing_data(session)
        
        # 2. Crea cicli di cura
        cicli_cura = create_cicli_cura(session)
        
        # 3. Crea autoclavi
        autoclavi = create_autoclavi(session)
        
        # 4. Genera tools
        tools = generate_aeronautical_tools(session)
        
        # 5. Genera catalogo
        catalog_entries = generate_aeronautical_catalog(session, tools, cicli_cura)
        
        # 6. Genera parti
        parts = generate_aeronautical_parts(session, catalog_entries, tools, cicli_cura)
        
        # 7. Genera ODL
        odl_list = generate_aeronautical_odl(session, parts)
        
        # 8. Stampa riepilogo
        print_summary(cicli_cura, autoclavi, tools, parts, odl_list)
        
    except Exception as e:
        print(f"❌ Errore durante il seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 