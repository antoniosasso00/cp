#!/usr/bin/env python3
"""
Script per popolare il database con dati di test realistici
Crea entità per Tools, Parts, ODL, Autoclavi, Cicli Cura, Nesting e Schedule
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Setup del path per importare i moduli del backend
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "backend"))

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """Configura la connessione al database e crea le tabelle"""
    try:
        from models.db import engine, Base, SessionLocal
        from models import *  # Importa tutti i modelli
        
        logger.info("🗃️ Creazione tabelle database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelle create con successo!")
        
        return SessionLocal()
    except Exception as e:
        logger.error(f"❌ Errore nella configurazione database: {str(e)}")
        raise

def clear_existing_data(db):
    """Pulisce i dati esistenti (opzionale)"""
    try:
        from models.nesting import Nesting
        from models.schedule import Schedule
        from models.tempo_fasi import TempoFasi
        from models.odl import ODL
        from models.parte import Parte
        from models.tool import Tool
        from models.autoclave import Autoclave
        from models.ciclo_cura import CicloCura
        from models.catalogo import Catalogo
        
        logger.info("🧹 Pulizia dati esistenti...")
        
        # Ordine importante per rispettare le foreign key
        db.query(TempoFasi).delete()
        db.query(Nesting).delete()
        db.query(Schedule).delete()
        db.query(ODL).delete()
        db.query(Parte).delete()
        db.query(Tool).delete()
        db.query(Autoclave).delete()
        db.query(CicloCura).delete()
        db.query(Catalogo).delete()
        
        db.commit()
        logger.info("✅ Dati esistenti rimossi")
        
    except Exception as e:
        logger.error(f"❌ Errore nella pulizia dati: {str(e)}")
        db.rollback()
        raise

def create_catalogo_data(db):
    """Crea dati di test per il catalogo"""
    from models.catalogo import Catalogo
    
    logger.info("📦 Creazione dati Catalogo...")
    
    catalogo_items = [
        {
            "part_number": "CF-WING-001",
            "descrizione": "Ala principale in fibra di carbonio",
            "categoria": "Strutturale",
            "sotto_categoria": "Ala",
            "attivo": True,
            "note": "Componente principale per aeromobili"
        },
        {
            "part_number": "CF-FUSE-002",
            "descrizione": "Sezione fusoliera anteriore",
            "categoria": "Strutturale", 
            "sotto_categoria": "Fusoliera",
            "attivo": True,
            "note": "Sezione anteriore della fusoliera"
        },
        {
            "part_number": "CF-TAIL-003",
            "descrizione": "Stabilizzatore verticale",
            "categoria": "Strutturale",
            "sotto_categoria": "Coda",
            "attivo": True,
            "note": "Componente di controllo verticale"
        },
        {
            "part_number": "CF-PANEL-004",
            "descrizione": "Pannello decorativo interno",
            "categoria": "Estetico",
            "sotto_categoria": "Interni",
            "attivo": True,
            "note": "Pannello per interni cabina"
        },
        {
            "part_number": "CF-BRACKET-005",
            "descrizione": "Staffa di supporto motore",
            "categoria": "Strutturale",
            "sotto_categoria": "Supporti",
            "attivo": True,
            "note": "Supporto per montaggio motore"
        }
    ]
    
    created_items = []
    for item_data in catalogo_items:
        item = Catalogo(**item_data)
        db.add(item)
        created_items.append(item)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_items)} elementi catalogo")
    return created_items

def create_cicli_cura_data(db):
    """Crea dati di test per i cicli di cura"""
    from models.ciclo_cura import CicloCura
    
    logger.info("🔥 Creazione dati Cicli Cura...")
    
    cicli_data = [
        {
            "nome": "Ciclo Standard 180°C",
            "temperatura_stasi1": 180.0,
            "pressione_stasi1": 6.0,
            "durata_stasi1": 120,
            "attiva_stasi2": True,
            "temperatura_stasi2": 200.0,
            "pressione_stasi2": 8.0,
            "durata_stasi2": 60
        },
        {
            "nome": "Ciclo Rapido 160°C",
            "temperatura_stasi1": 160.0,
            "pressione_stasi1": 5.0,
            "durata_stasi1": 90,
            "attiva_stasi2": False
        },
        {
            "nome": "Ciclo Alta Temperatura 220°C",
            "temperatura_stasi1": 220.0,
            "pressione_stasi1": 10.0,
            "durata_stasi1": 180,
            "attiva_stasi2": True,
            "temperatura_stasi2": 240.0,
            "pressione_stasi2": 12.0,
            "durata_stasi2": 90
        }
    ]
    
    created_cicli = []
    for ciclo_data in cicli_data:
        ciclo = CicloCura(**ciclo_data)
        db.add(ciclo)
        created_cicli.append(ciclo)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_cicli)} cicli di cura")
    return created_cicli

def create_tools_data(db):
    """Crea dati di test per i tools"""
    from models.tool import Tool
    
    logger.info("🔧 Creazione dati Tools...")
    
    tools_data = [
        {
            "part_number_tool": "TOOL-WING-001",
            "descrizione": "Stampo per ala principale",
            "lunghezza_piano": 2000.0,
            "larghezza_piano": 800.0,
            "disponibile": True,
            "note": "Stampo per componenti alari"
        },
        {
            "part_number_tool": "TOOL-FUSE-002",
            "descrizione": "Stampo fusoliera sezione A",
            "lunghezza_piano": 1500.0,
            "larghezza_piano": 600.0,
            "disponibile": True,
            "note": "Stampo per sezioni fusoliera"
        },
        {
            "part_number_tool": "TOOL-PANEL-003",
            "descrizione": "Stampo pannelli decorativi",
            "lunghezza_piano": 1000.0,
            "larghezza_piano": 500.0,
            "disponibile": True,
            "note": "Stampo per pannelli interni"
        },
        {
            "part_number_tool": "TOOL-BRACKET-004",
            "descrizione": "Stampo staffe supporto",
            "lunghezza_piano": 800.0,
            "larghezza_piano": 400.0,
            "disponibile": False,
            "note": "Stampo per staffe di supporto - in manutenzione"
        }
    ]
    
    created_tools = []
    for tool_data in tools_data:
        tool = Tool(**tool_data)
        db.add(tool)
        created_tools.append(tool)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_tools)} tools")
    return created_tools

def create_autoclavi_data(db):
    """Crea dati di test per le autoclavi"""
    from models.autoclave import Autoclave
    
    logger.info("🏭 Creazione dati Autoclavi...")
    
    autoclavi_data = [
        {
            "nome": "Autoclave Alpha",
            "codice": "AUT-001",
            "lunghezza": 3000.0,
            "larghezza_piano": 1500.0,
            "num_linee_vuoto": 4,
            "stato": "DISPONIBILE",
            "temperatura_max": 250.0,
            "pressione_max": 15.0,
            "produttore": "ThermoTech",
            "anno_produzione": 2020,
            "note": "Autoclave principale per produzione"
        },
        {
            "nome": "Autoclave Beta",
            "codice": "AUT-002", 
            "lunghezza": 2500.0,
            "larghezza_piano": 1200.0,
            "num_linee_vuoto": 3,
            "stato": "DISPONIBILE",
            "temperatura_max": 220.0,
            "pressione_max": 12.0,
            "produttore": "CarbonCure",
            "anno_produzione": 2019,
            "note": "Autoclave secondaria"
        },
        {
            "nome": "Autoclave Gamma",
            "codice": "AUT-003",
            "lunghezza": 2000.0,
            "larghezza_piano": 1000.0,
            "num_linee_vuoto": 2,
            "stato": "MANUTENZIONE",
            "temperatura_max": 200.0,
            "pressione_max": 10.0,
            "produttore": "CompositePro",
            "anno_produzione": 2018,
            "note": "In manutenzione programmata"
        }
    ]
    
    created_autoclavi = []
    for autoclave_data in autoclavi_data:
        autoclave = Autoclave(**autoclave_data)
        db.add(autoclave)
        created_autoclavi.append(autoclave)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_autoclavi)} autoclavi")
    return created_autoclavi

def create_parti_data(db, catalogo_items, cicli_cura, tools):
    """Crea dati di test per le parti"""
    from models.parte import Parte
    
    logger.info("🧩 Creazione dati Parti...")
    
    parti_data = [
        {
            "part_number": "CF-WING-001",
            "descrizione_breve": "Ala principale",
            "num_valvole_richieste": 8,
            "note_produzione": "Richiede attenzione particolare nelle curve",
            "ciclo_cura_id": cicli_cura[0].id,
            "tool_ids": [tools[0].id]
        },
        {
            "part_number": "CF-FUSE-002", 
            "descrizione_breve": "Fusoliera anteriore",
            "num_valvole_richieste": 6,
            "note_produzione": "Verificare allineamento con sezioni adiacenti",
            "ciclo_cura_id": cicli_cura[1].id,
            "tool_ids": [tools[1].id]
        },
        {
            "part_number": "CF-PANEL-004",
            "descrizione_breve": "Pannello decorativo",
            "num_valvole_richieste": 2,
            "note_produzione": "Finitura superficiale critica",
            "ciclo_cura_id": cicli_cura[0].id,
            "tool_ids": [tools[2].id]
        },
        {
            "part_number": "CF-BRACKET-005",
            "descrizione_breve": "Staffa supporto motore",
            "num_valvole_richieste": 4,
            "note_produzione": "Controllo dimensionale rigoroso",
            "ciclo_cura_id": cicli_cura[2].id,
            "tool_ids": [tools[3].id]
        }
    ]
    
    created_parti = []
    for parte_data in parti_data:
        tool_ids = parte_data.pop('tool_ids')
        parte = Parte(**parte_data)
        
        # Associa i tools
        for tool_id in tool_ids:
            tool = next((t for t in tools if t.id == tool_id), None)
            if tool:
                parte.tools.append(tool)
        
        db.add(parte)
        created_parti.append(parte)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_parti)} parti")
    return created_parti

def create_odl_data(db, parti, tools):
    """Crea dati di test per gli ODL"""
    from models.odl import ODL
    
    logger.info("📋 Creazione dati ODL...")
    
    odl_data = [
        {
            "parte_id": parti[0].id,
            "tool_id": tools[0].id,
            "priorita": 1,
            "status": "Laminazione",
            "note": "ODL prioritario per consegna urgente"
        },
        {
            "parte_id": parti[1].id,
            "tool_id": tools[1].id,
            "priorita": 2,
            "status": "Preparazione",
            "note": "In preparazione per laminazione"
        },
        {
            "parte_id": parti[2].id,
            "tool_id": tools[2].id,
            "priorita": 3,
            "status": "Attesa Cura",
            "note": "Pronto per autoclave"
        },
        {
            "parte_id": parti[3].id,
            "tool_id": tools[3].id,
            "priorita": 4,
            "status": "Finito",
            "note": "Completato e controllato"
        },
        {
            "parte_id": parti[0].id,
            "tool_id": tools[0].id,
            "priorita": 5,
            "status": "Cura",
            "note": "In autoclave - ciclo in corso"
        }
    ]
    
    created_odl = []
    for odl_item_data in odl_data:
        odl = ODL(**odl_item_data)
        db.add(odl)
        created_odl.append(odl)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_odl)} ODL")
    return created_odl

def create_tempo_fasi_data(db, odl_list):
    """Crea dati di test per i tempi delle fasi"""
    from models.tempo_fasi import TempoFasi
    
    logger.info("⏱️ Creazione dati Tempo Fasi...")
    
    base_time = datetime.now() - timedelta(days=2)
    
    tempo_fasi_data = []
    
    for i, odl in enumerate(odl_list[:3]):  # Solo per i primi 3 ODL
        # Fase laminazione
        inizio_lam = base_time + timedelta(hours=i*8)
        fine_lam = inizio_lam + timedelta(hours=2, minutes=30)
        
        tempo_fasi_data.append({
            "odl_id": odl.id,
            "fase": "laminazione",
            "inizio_fase": inizio_lam,
            "fine_fase": fine_lam,
            "durata_minuti": 150,
            "note": f"Laminazione completata per ODL {odl.id}"
        })
        
        # Fase attesa cura
        inizio_attesa = fine_lam
        fine_attesa = inizio_attesa + timedelta(hours=4)
        
        tempo_fasi_data.append({
            "odl_id": odl.id,
            "fase": "attesa_cura",
            "inizio_fase": inizio_attesa,
            "fine_fase": fine_attesa,
            "durata_minuti": 240,
            "note": f"Attesa cura per ODL {odl.id}"
        })
        
        # Fase cura (solo per ODL completati)
        if i < 2:
            inizio_cura = fine_attesa
            fine_cura = inizio_cura + timedelta(hours=3)
            
            tempo_fasi_data.append({
                "odl_id": odl.id,
                "fase": "cura",
                "inizio_fase": inizio_cura,
                "fine_fase": fine_cura,
                "durata_minuti": 180,
                "note": f"Cura completata per ODL {odl.id}"
            })
    
    created_tempi = []
    for tempo_data in tempo_fasi_data:
        tempo = TempoFasi(**tempo_data)
        db.add(tempo)
        created_tempi.append(tempo)
    
    db.commit()
    logger.info(f"✅ Creati {len(created_tempi)} record tempo fasi")
    return created_tempi

def create_nesting_data(db, autoclavi, odl_list):
    """Crea dati di test per il nesting"""
    from models.nesting import Nesting
    
    logger.info("🧩 Creazione dati Nesting...")
    
    # Crea un nesting con i primi 3 ODL nell'autoclave Alpha
    nesting_data = {
        "autoclave_id": autoclavi[0].id,
        "odl_ids": [odl_list[0].id, odl_list[1].id, odl_list[2].id],
        "area_utilizzata": 3500000.0,  # 3.5 m²
        "area_totale": 4500000.0,      # 4.5 m²
        "valvole_utilizzate": 16,
        "valvole_totali": 20
    }
    
    nesting = Nesting(
        autoclave_id=nesting_data["autoclave_id"],
        area_utilizzata=nesting_data["area_utilizzata"],
        area_totale=nesting_data["area_totale"],
        valvole_utilizzate=nesting_data["valvole_utilizzate"],
        valvole_totali=nesting_data["valvole_totali"]
    )
    
    # Associa gli ODL
    for odl_id in nesting_data["odl_ids"]:
        odl = next((o for o in odl_list if o.id == odl_id), None)
        if odl:
            nesting.odl_list.append(odl)
    
    db.add(nesting)
    db.commit()
    
    logger.info("✅ Creato 1 nesting")
    return [nesting]

def create_schedule_data(db, autoclavi, nesting_list):
    """Crea dati di test per gli schedule"""
    from models.schedule import Schedule
    
    logger.info("📅 Creazione dati Schedule...")
    
    # Crea uno schedule per il nesting creato
    schedule_data = {
        "autoclave_id": autoclavi[0].id,
        "nesting_id": nesting_list[0].id,
        "data_inizio_prevista": datetime.now() + timedelta(hours=2),
        "data_fine_prevista": datetime.now() + timedelta(hours=8),
        "stato": "PROGRAMMATO",
        "note": "Schedule automatico per nesting ottimizzato"
    }
    
    schedule = Schedule(**schedule_data)
    db.add(schedule)
    db.commit()
    
    logger.info("✅ Creato 1 schedule")
    return [schedule]

def print_summary(db):
    """Stampa un riepilogo dei dati creati"""
    from models.catalogo import Catalogo
    from models.ciclo_cura import CicloCura
    from models.tool import Tool
    from models.autoclave import Autoclave
    from models.parte import Parte
    from models.odl import ODL
    from models.tempo_fasi import TempoFasi
    from models.nesting import Nesting
    from models.schedule import Schedule
    
    logger.info("\n📊 RIEPILOGO DATI CREATI")
    logger.info("=" * 50)
    
    counts = {
        "Catalogo": db.query(Catalogo).count(),
        "Cicli Cura": db.query(CicloCura).count(),
        "Tools": db.query(Tool).count(),
        "Autoclavi": db.query(Autoclave).count(),
        "Parti": db.query(Parte).count(),
        "ODL": db.query(ODL).count(),
        "Tempo Fasi": db.query(TempoFasi).count(),
        "Nesting": db.query(Nesting).count(),
        "Schedule": db.query(Schedule).count()
    }
    
    for entity, count in counts.items():
        logger.info(f"✅ {entity}: {count} record")
    
    total = sum(counts.values())
    logger.info(f"\n🎯 Totale record creati: {total}")

def main():
    """Funzione principale"""
    logger.info("🌱 SEED DATABASE CARBONPILOT")
    logger.info("=" * 60)
    
    try:
        # Setup database
        db = setup_database()
        
        # Opzione per pulire i dati esistenti
        clear_existing = input("Vuoi pulire i dati esistenti? (y/N): ").lower().strip()
        if clear_existing == 'y':
            clear_existing_data(db)
        
        # Crea i dati in ordine di dipendenza
        logger.info("🚀 Inizio creazione dati di test...")
        
        catalogo_items = create_catalogo_data(db)
        cicli_cura = create_cicli_cura_data(db)
        tools = create_tools_data(db)
        autoclavi = create_autoclavi_data(db)
        parti = create_parti_data(db, catalogo_items, cicli_cura, tools)
        odl_list = create_odl_data(db, parti, tools)
        tempo_fasi = create_tempo_fasi_data(db, odl_list)
        nesting_list = create_nesting_data(db, autoclavi, odl_list)
        schedule_list = create_schedule_data(db, autoclavi, nesting_list)
        
        # Riepilogo finale
        print_summary(db)
        
        logger.info("\n🎉 SEED COMPLETATO CON SUCCESSO!")
        logger.info("Il database è ora popolato con dati di test realistici.")
        logger.info("Puoi testare l'applicazione con questi dati.")
        
    except Exception as e:
        logger.error(f"❌ Errore durante il seed: {str(e)}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main() 