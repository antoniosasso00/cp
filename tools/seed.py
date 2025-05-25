#!/usr/bin/env python
"""
🌱 Script di Seed Unificato per CarbonPilot
===========================================

Questo script popola l'intero sistema con dati coerenti e realistici:
- 4 ODL in stati differenti
- 2 cicli di cura
- 2 nesting già pronti
- 1 autoclave attiva
- 1 report già completato

Lo script è idempotente: rimuove i dati precedenti se presenti.
"""

import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Setup del percorso per importare i modelli
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa i modelli e la configurazione del database
try:
    from models.db import SessionLocal, engine
    from models import (
        Base, Catalogo, Parte, Tool, Autoclave, StatoAutoclaveEnum,
        CicloCura, ODL, NestingResult, Report, ReportTypeEnum,
        TempoFase, ODLLog
    )
    from sqlalchemy.orm import Session
    from sqlalchemy import text
except ImportError as e:
    logger.error(f"❌ Errore nell'importazione dei modelli: {e}")
    logger.error("Assicurati di essere nella directory root del progetto")
    sys.exit(1)

class SeedData:
    """Classe per gestire i dati di seed e i contatori"""
    
    def __init__(self):
        self.contatori = {
            "catalogo": 0,
            "tools": 0,
            "cicli_cura": 0,
            "autoclavi": 0,
            "parti": 0,
            "odl": 0,
            "nesting": 0,
            "report": 0,
            "tempo_fasi": 0,
            "odl_logs": 0
        }
        self.created_ids = {}

    def increment(self, entity: str, count: int = 1):
        """Incrementa il contatore per un'entità"""
        self.contatori[entity] += count

    def store_id(self, entity: str, key: str, id_value: int):
        """Memorizza un ID creato per riferimenti futuri"""
        if entity not in self.created_ids:
            self.created_ids[entity] = {}
        self.created_ids[entity][key] = id_value

    def get_id(self, entity: str, key: str) -> Optional[int]:
        """Recupera un ID memorizzato"""
        return self.created_ids.get(entity, {}).get(key)

def clear_database(db: Session, debug: bool = False):
    """
    Rimuove tutti i dati esistenti dal database (idempotente).
    Mantiene la struttura delle tabelle.
    """
    logger.info("🧹 Pulizia database esistente...")
    
    try:
        # Ordine di cancellazione per rispettare le foreign key
        tables_to_clear = [
            "tempo_fasi",
            "odl_logs", 
            "nesting_result_odl",  # Tabella di associazione
            "nesting_results",
            "reports",
            "odl",
            "parte_tool_association",  # Tabella di associazione
            "parti",
            "cataloghi",
            "tools",
            "cicli_cura",
            "autoclavi"
        ]
        
        for table in tables_to_clear:
            try:
                result = db.execute(text(f"DELETE FROM {table}"))
                if debug:
                    logger.debug(f"Cancellati {result.rowcount} record da {table}")
            except Exception as e:
                if debug:
                    logger.debug(f"Tabella {table} non trovata o già vuota: {e}")
        
        db.commit()
        logger.info("✅ Database pulito con successo")
        
    except Exception as e:
        logger.error(f"❌ Errore durante la pulizia del database: {e}")
        db.rollback()
        raise

def seed_catalogo(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea i dati del catalogo"""
    logger.info("📚 Creazione Catalogo...")
    
    catalogo_items = [
        {
            "part_number": "CPX-101",
            "descrizione": "Pannello laterale sinistro in composito",
            "categoria": "PANNELLI",
            "sotto_categoria": "LATERALI",
            "attivo": True,
            "lunghezza": 2000.0,
            "larghezza": 1000.0,
            "altezza": 50.0,
            "note": "Pannello strutturale per lato sinistro"
        },
        {
            "part_number": "CPX-102", 
            "descrizione": "Pannello laterale destro in composito",
            "categoria": "PANNELLI",
            "sotto_categoria": "LATERALI",
            "attivo": True,
            "lunghezza": 2000.0,
            "larghezza": 1000.0,
            "altezza": 50.0,
            "note": "Pannello strutturale per lato destro"
        },
        {
            "part_number": "CPX-201",
            "descrizione": "Supporto motore rinforzato",
            "categoria": "SUPPORTI",
            "sotto_categoria": "MOTORE",
            "attivo": True,
            "lunghezza": 1500.0,
            "larghezza": 800.0,
            "altezza": 100.0,
            "note": "Supporto strutturale per motore elettrico"
        },
        {
            "part_number": "CPX-301",
            "descrizione": "Coperchio vano batterie",
            "categoria": "COPERCHI",
            "sotto_categoria": "BATTERIE",
            "attivo": True,
            "lunghezza": 1200.0,
            "larghezza": 600.0,
            "altezza": 30.0,
            "note": "Coperchio protettivo vano batterie"
        },
        {
            "part_number": "CPX-401",
            "descrizione": "Fascia frontale aerodinamica",
            "categoria": "FASCE",
            "sotto_categoria": "FRONTALI",
            "attivo": True,
            "lunghezza": 1800.0,
            "larghezza": 900.0,
            "altezza": 40.0,
            "note": "Fascia frontale con profilo aerodinamico"
        }
    ]
    
    for item in catalogo_items:
        catalogo = Catalogo(**item)
        db.add(catalogo)
        seed_data.increment("catalogo")
        if debug:
            logger.debug(f"Creato catalogo: {item['part_number']}")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['catalogo']} elementi del catalogo")

def seed_tools(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea gli strumenti (tool)"""
    logger.info("🔧 Creazione Tools...")
    
    tools_data = [
        {
            "part_number_tool": "ST-101",
            "descrizione": "Stampo per pannelli laterali - Doppia cavità",
            "lunghezza_piano": 2200.0,
            "larghezza_piano": 1100.0,
            "disponibile": True,
            "note": "Stampo principale per pannelli laterali con sistema di riscaldamento integrato"
        },
        {
            "part_number_tool": "ST-201",
            "descrizione": "Stampo supporto motore - Cavità singola rinforzata",
            "lunghezza_piano": 1600.0,
            "larghezza_piano": 900.0,
            "disponibile": True,
            "note": "Stampo dedicato per supporti motore con rinforzi strutturali"
        },
        {
            "part_number_tool": "ST-301",
            "descrizione": "Stampo universale coperchi e fasce",
            "lunghezza_piano": 1900.0,
            "larghezza_piano": 1000.0,
            "disponibile": True,
            "note": "Stampo versatile per coperchi e fasce con inserti intercambiabili"
        },
        {
            "part_number_tool": "ST-401",
            "descrizione": "Stampo prototipazione rapida",
            "lunghezza_piano": 1000.0,
            "larghezza_piano": 600.0,
            "disponibile": False,  # Non disponibile per test
            "note": "Stampo per prototipazione e test - Attualmente in manutenzione"
        }
    ]
    
    for i, tool_data in enumerate(tools_data, 1):
        tool = Tool(**tool_data)
        db.add(tool)
        db.flush()  # Per ottenere l'ID
        seed_data.store_id("tools", f"tool_{i}", tool.id)
        seed_data.increment("tools")
        if debug:
            logger.debug(f"Creato tool: {tool_data['part_number_tool']} (ID: {tool.id})")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['tools']} tools")

def seed_cicli_cura(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea i cicli di cura"""
    logger.info("🌡️ Creazione Cicli di Cura...")
    
    cicli_data = [
        {
            "nome": "Ciclo Standard",
            "temperatura_stasi1": 120.0,
            "pressione_stasi1": 4.0,
            "durata_stasi1": 60,
            "attiva_stasi2": False,
            "descrizione": "Ciclo standard per parti non critiche e coperchi"
        },
        {
            "nome": "Ciclo Avanzato",
            "temperatura_stasi1": 130.0,
            "pressione_stasi1": 5.0,
            "durata_stasi1": 45,
            "attiva_stasi2": True,
            "temperatura_stasi2": 140.0,
            "pressione_stasi2": 6.0,
            "durata_stasi2": 30,
            "descrizione": "Ciclo avanzato per parti strutturali e supporti"
        }
    ]
    
    for i, ciclo_data in enumerate(cicli_data, 1):
        ciclo = CicloCura(**ciclo_data)
        db.add(ciclo)
        db.flush()
        seed_data.store_id("cicli_cura", f"ciclo_{i}", ciclo.id)
        seed_data.increment("cicli_cura")
        if debug:
            logger.debug(f"Creato ciclo: {ciclo_data['nome']} (ID: {ciclo.id})")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['cicli_cura']} cicli di cura")

def seed_autoclavi(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea le autoclavi"""
    logger.info("🏭 Creazione Autoclavi...")
    
    autoclavi_data = [
        {
            "nome": "Autoclave Principale",
            "codice": "AUTO-001",
            "lunghezza": 3000.0,
            "larghezza_piano": 1500.0,
            "num_linee_vuoto": 4,
            "temperatura_max": 180.0,
            "pressione_max": 7.0,
            "stato": StatoAutoclaveEnum.DISPONIBILE,  # Autoclave attiva
            "produttore": "Scholz",
            "anno_produzione": 2023,
            "note": "Autoclave principale per produzione - Completamente operativa"
        },
        {
            "nome": "Autoclave Secondaria",
            "codice": "AUTO-002",
            "lunghezza": 2500.0,
            "larghezza_piano": 1200.0,
            "num_linee_vuoto": 3,
            "temperatura_max": 180.0,
            "pressione_max": 7.0,
            "stato": StatoAutoclaveEnum.MANUTENZIONE,
            "produttore": "Scholz",
            "anno_produzione": 2022,
            "note": "Autoclave secondaria - In manutenzione programmata"
        }
    ]
    
    for i, autoclave_data in enumerate(autoclavi_data, 1):
        autoclave = Autoclave(**autoclave_data)
        db.add(autoclave)
        db.flush()
        seed_data.store_id("autoclavi", f"autoclave_{i}", autoclave.id)
        seed_data.increment("autoclavi")
        if debug:
            logger.debug(f"Creata autoclave: {autoclave_data['nome']} (ID: {autoclave.id}, Stato: {autoclave_data['stato'].value})")
    
    db.commit()
    logger.info(f"✅ Create {seed_data.contatori['autoclavi']} autoclavi (1 attiva)")

def seed_parti(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea le parti"""
    logger.info("🔩 Creazione Parti...")
    
    parti_data = [
        {
            "part_number": "CPX-101",
            "descrizione_breve": "Pannello SX",
            "num_valvole_richieste": 4,
            "ciclo_cura_id": seed_data.get_id("cicli_cura", "ciclo_1"),
            "note_produzione": "Pannello laterale sinistro - Attenzione alla direzione fibre"
        },
        {
            "part_number": "CPX-102",
            "descrizione_breve": "Pannello DX",
            "num_valvole_richieste": 4,
            "ciclo_cura_id": seed_data.get_id("cicli_cura", "ciclo_1"),
            "note_produzione": "Pannello laterale destro - Speculare al sinistro"
        },
        {
            "part_number": "CPX-201",
            "descrizione_breve": "Supporto Motore",
            "num_valvole_richieste": 6,
            "ciclo_cura_id": seed_data.get_id("cicli_cura", "ciclo_2"),
            "note_produzione": "Supporto motore - Parte critica, controllo qualità esteso"
        },
        {
            "part_number": "CPX-301",
            "descrizione_breve": "Coperchio Batterie",
            "num_valvole_richieste": 2,
            "ciclo_cura_id": seed_data.get_id("cicli_cura", "ciclo_1"),
            "note_produzione": "Coperchio vano batterie - Verificare tenuta"
        },
        {
            "part_number": "CPX-401",
            "descrizione_breve": "Fascia Frontale",
            "num_valvole_richieste": 3,
            "ciclo_cura_id": seed_data.get_id("cicli_cura", "ciclo_2"),
            "note_produzione": "Fascia frontale - Controllo finitura superficiale"
        }
    ]
    
    # Associazioni parte-tool
    parte_tool_associations = [
        (1, [1]),  # CPX-101 -> ST-101
        (2, [1]),  # CPX-102 -> ST-101
        (3, [2]),  # CPX-201 -> ST-201
        (4, [3]),  # CPX-301 -> ST-301
        (5, [3])   # CPX-401 -> ST-301
    ]
    
    for i, parte_data in enumerate(parti_data, 1):
        parte = Parte(**parte_data)
        db.add(parte)
        db.flush()
        
        # Aggiungi associazioni con i tools
        tool_indices = parte_tool_associations[i-1][1]
        for tool_idx in tool_indices:
            tool_id = seed_data.get_id("tools", f"tool_{tool_idx}")
            if tool_id:
                tool = db.query(Tool).filter(Tool.id == tool_id).first()
                if tool:
                    parte.tools.append(tool)
        
        seed_data.store_id("parti", f"parte_{i}", parte.id)
        seed_data.increment("parti")
        if debug:
            logger.debug(f"Creata parte: {parte_data['part_number']} (ID: {parte.id})")
    
    db.commit()
    logger.info(f"✅ Create {seed_data.contatori['parti']} parti")

def seed_odl(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea 4 ODL in stati differenti"""
    logger.info("📋 Creazione ODL...")
    
    # Stati differenti per i 4 ODL
    stati_odl = ["Preparazione", "Laminazione", "Attesa Cura", "Cura"]
    
    odl_data = [
        {
            "parte_id": seed_data.get_id("parti", "parte_1"),  # CPX-101
            "tool_id": seed_data.get_id("tools", "tool_1"),    # ST-101
            "priorita": 8,
            "status": stati_odl[0],
            "note": "ODL prioritario per pannello sinistro - Cliente urgente"
        },
        {
            "parte_id": seed_data.get_id("parti", "parte_3"),  # CPX-201
            "tool_id": seed_data.get_id("tools", "tool_2"),    # ST-201
            "priorita": 10,
            "status": stati_odl[1],
            "note": "ODL supporto motore - Laminazione in corso"
        },
        {
            "parte_id": seed_data.get_id("parti", "parte_2"),  # CPX-102
            "tool_id": seed_data.get_id("tools", "tool_1"),    # ST-101
            "priorita": 6,
            "status": stati_odl[2],
            "note": "ODL pannello destro - In attesa di slot autoclave"
        },
        {
            "parte_id": seed_data.get_id("parti", "parte_4"),  # CPX-301
            "tool_id": seed_data.get_id("tools", "tool_3"),    # ST-301
            "priorita": 4,
            "status": stati_odl[3],
            "note": "ODL coperchio batterie - Cura in corso"
        }
    ]
    
    for i, odl_info in enumerate(odl_data, 1):
        odl = ODL(**odl_info)
        db.add(odl)
        db.flush()
        seed_data.store_id("odl", f"odl_{i}", odl.id)
        seed_data.increment("odl")
        if debug:
            logger.debug(f"Creato ODL {i}: Stato '{odl_info['status']}' (ID: {odl.id})")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['odl']} ODL in stati differenti")

def seed_nesting_results(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea 2 nesting già pronti"""
    logger.info("📦 Creazione Nesting Results...")
    
    autoclave_id = seed_data.get_id("autoclavi", "autoclave_1")  # Autoclave principale
    
    # Primo nesting - Confermato
    nesting1_data = {
        "autoclave_id": autoclave_id,
        "odl_ids": [
            seed_data.get_id("odl", "odl_1"),
            seed_data.get_id("odl", "odl_2")
        ],
        "odl_esclusi_ids": [],
        "motivi_esclusione": [],
        "stato": "Confermato",
        "confermato_da_ruolo": "supervisor",
        "area_utilizzata": 2800.0,
        "area_totale": 4500.0,  # 3000 x 1500 mm
        "valvole_utilizzate": 12,  # 4 + 6 + 2 valvole
        "valvole_totali": 4,
        "note": "Nesting ottimizzato per pannelli e supporto motore",
        "posizioni_tool": [
            {
                "odl_id": seed_data.get_id("odl", "odl_1"),
                "x": 100.0,
                "y": 100.0,
                "width": 2200.0,
                "height": 1100.0
            },
            {
                "odl_id": seed_data.get_id("odl", "odl_2"),
                "x": 100.0,
                "y": 1300.0,
                "width": 1600.0,
                "height": 900.0
            }
        ]
    }
    
    nesting1 = NestingResult(**nesting1_data)
    db.add(nesting1)
    db.flush()
    
    # Aggiungi ODL al nesting
    for odl_id in nesting1_data["odl_ids"]:
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            nesting1.odl_list.append(odl)
    
    seed_data.store_id("nesting", "nesting_1", nesting1.id)
    seed_data.increment("nesting")
    
    # Secondo nesting - In sospeso
    nesting2_data = {
        "autoclave_id": autoclave_id,
        "odl_ids": [
            seed_data.get_id("odl", "odl_3"),
            seed_data.get_id("odl", "odl_4")
        ],
        "odl_esclusi_ids": [],
        "motivi_esclusione": [],
        "stato": "In sospeso",
        "confermato_da_ruolo": None,
        "area_utilizzata": 2100.0,
        "area_totale": 4500.0,
        "valvole_utilizzate": 6,  # 4 + 2 valvole
        "valvole_totali": 4,
        "note": "Nesting in attesa di conferma per coperchi e fasce",
        "posizioni_tool": [
            {
                "odl_id": seed_data.get_id("odl", "odl_3"),
                "x": 200.0,
                "y": 200.0,
                "width": 2200.0,
                "height": 1100.0
            },
            {
                "odl_id": seed_data.get_id("odl", "odl_4"),
                "x": 200.0,
                "y": 1400.0,
                "width": 1900.0,
                "height": 1000.0
            }
        ]
    }
    
    nesting2 = NestingResult(**nesting2_data)
    db.add(nesting2)
    db.flush()
    
    # Aggiungi ODL al nesting
    for odl_id in nesting2_data["odl_ids"]:
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            nesting2.odl_list.append(odl)
    
    seed_data.store_id("nesting", "nesting_2", nesting2.id)
    seed_data.increment("nesting")
    
    db.commit()
    
    if debug:
        logger.debug(f"Creato nesting 1: {nesting1_data['stato']} (ID: {nesting1.id})")
        logger.debug(f"Creato nesting 2: {nesting2_data['stato']} (ID: {nesting2.id})")
    
    logger.info(f"✅ Creati {seed_data.contatori['nesting']} nesting results")

def seed_report(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea 1 report già completato"""
    logger.info("📊 Creazione Report...")
    
    # Crea directory reports se non esiste
    reports_dir = BACKEND_DIR / "reports" / "generated"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Dati del report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_produzione_{timestamp}.pdf"
    file_path = str(reports_dir / filename)
    
    report_data = {
        "filename": filename,
        "file_path": file_path,
        "report_type": ReportTypeEnum.PRODUZIONE,
        "generated_for_user_id": None,  # Per ora nullable
        "period_start": datetime.now() - timedelta(days=7),
        "period_end": datetime.now(),
        "include_sections": "produzione,tempi,qualita",
        "file_size_bytes": 245760  # ~240KB simulato
    }
    
    report = Report(**report_data)
    db.add(report)
    db.flush()
    
    # Crea un file PDF fittizio per il test
    try:
        with open(file_path, 'w') as f:
            f.write(f"# Report di Produzione CarbonPilot\n")
            f.write(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Periodo: {report_data['period_start'].strftime('%d/%m/%Y')} - {report_data['period_end'].strftime('%d/%m/%Y')}\n")
            f.write(f"\nQuesto è un file di test per il seed del database.\n")
    except Exception as e:
        if debug:
            logger.debug(f"Impossibile creare file PDF fittizio: {e}")
    
    # Collega il report al primo nesting
    nesting_id = seed_data.get_id("nesting", "nesting_1")
    if nesting_id:
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if nesting:
            nesting.report_id = report.id
    
    seed_data.store_id("report", "report_1", report.id)
    seed_data.increment("report")
    
    db.commit()
    
    if debug:
        logger.debug(f"Creato report: {filename} (ID: {report.id})")
    
    logger.info(f"✅ Creato {seed_data.contatori['report']} report completato")

def seed_tempo_fasi(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea dati di tempo fasi per alcuni ODL"""
    logger.info("⏱️ Creazione Tempi Fasi...")
    
    # Crea tempi fasi per i primi 2 ODL
    fasi = ["laminazione", "attesa_cura", "cura"]
    base_time = datetime.now() - timedelta(days=2)
    
    for odl_idx in [1, 2]:
        odl_id = seed_data.get_id("odl", f"odl_{odl_idx}")
        if not odl_id:
            continue
            
        current_time = base_time
        
        for fase in fasi:
            # Durate realistiche per ogni fase
            durate = {
                "laminazione": timedelta(hours=2, minutes=random.randint(0, 30)),
                "attesa_cura": timedelta(hours=4, minutes=random.randint(0, 60)),
                "cura": timedelta(hours=3, minutes=random.randint(0, 45))
            }
            
            inizio_fase = current_time
            fine_fase = current_time + durate[fase]
            
            tempo_fase_data = {
                "odl_id": odl_id,
                "fase": fase,
                "inizio_fase": inizio_fase,
                "fine_fase": fine_fase,
                "note": f"Fase {fase} per ODL {odl_idx} - Monitoraggio automatico"
            }
            
            tempo_fase = TempoFase(**tempo_fase_data)
            db.add(tempo_fase)
            seed_data.increment("tempo_fasi")
            
            current_time = fine_fase + timedelta(minutes=15)  # Pausa tra fasi
            
            if debug:
                logger.debug(f"Creato tempo fase {fase} per ODL {odl_idx}")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['tempo_fasi']} tempi fasi")

def seed_odl_logs(db: Session, seed_data: SeedData, debug: bool = False):
    """Crea alcuni log per gli ODL"""
    logger.info("📝 Creazione ODL Logs...")
    
    # Crea log per tutti gli ODL
    for odl_idx in range(1, 5):
        odl_id = seed_data.get_id("odl", f"odl_{odl_idx}")
        if not odl_id:
            continue
        
        # Log di creazione
        log_creazione = ODLLog(
            odl_id=odl_id,
            azione="Creazione ODL",
            dettagli=f"ODL {odl_idx} creato automaticamente dal sistema di seed",
            timestamp=datetime.now() - timedelta(days=1, hours=odl_idx)
        )
        db.add(log_creazione)
        seed_data.increment("odl_logs")
        
        # Log di cambio stato (se non è in preparazione)
        if odl_idx > 1:
            log_stato = ODLLog(
                odl_id=odl_id,
                azione="Cambio Stato",
                dettagli=f"ODL {odl_idx} passato in stato operativo",
                timestamp=datetime.now() - timedelta(hours=odl_idx * 2)
            )
            db.add(log_stato)
            seed_data.increment("odl_logs")
        
        if debug:
            logger.debug(f"Creati log per ODL {odl_idx}")
    
    db.commit()
    logger.info(f"✅ Creati {seed_data.contatori['odl_logs']} log ODL")

def print_summary(seed_data: SeedData):
    """Stampa il riepilogo finale delle entità create"""
    logger.info("\n" + "="*60)
    logger.info("📊 RIEPILOGO SEED COMPLETATO")
    logger.info("="*60)
    
    total_entities = sum(seed_data.contatori.values())
    
    for entity, count in seed_data.contatori.items():
        if count > 0:
            emoji_map = {
                "catalogo": "📚",
                "tools": "🔧", 
                "cicli_cura": "🌡️",
                "autoclavi": "🏭",
                "parti": "🔩",
                "odl": "📋",
                "nesting": "📦",
                "report": "📊",
                "tempo_fasi": "⏱️",
                "odl_logs": "📝"
            }
            emoji = emoji_map.get(entity, "📄")
            entity_name = entity.replace("_", " ").title()
            logger.info(f"{emoji} {entity_name}: {count}")
    
    logger.info("-" * 60)
    logger.info(f"🎯 TOTALE ENTITÀ CREATE: {total_entities}")
    logger.info("="*60)
    
    # Verifica requisiti specifici
    logger.info("\n✅ VERIFICA REQUISITI:")
    logger.info(f"   • 4 ODL in stati differenti: {'✅' if seed_data.contatori['odl'] >= 4 else '❌'}")
    logger.info(f"   • 2 cicli di cura: {'✅' if seed_data.contatori['cicli_cura'] >= 2 else '❌'}")
    logger.info(f"   • 2 nesting già pronti: {'✅' if seed_data.contatori['nesting'] >= 2 else '❌'}")
    logger.info(f"   • 1 autoclave attiva: {'✅' if seed_data.contatori['autoclavi'] >= 1 else '❌'}")
    logger.info(f"   • 1 report già completato: {'✅' if seed_data.contatori['report'] >= 1 else '❌'}")

def main():
    """Funzione principale del seed"""
    parser = argparse.ArgumentParser(description="🌱 Script di Seed Unificato CarbonPilot")
    parser.add_argument("--debug", action="store_true", help="Abilita log di debug dettagliati")
    parser.add_argument("--no-clear", action="store_true", help="Non pulire il database esistente")
    args = parser.parse_args()
    
    logger.info("🌱 Avvio Seed Unificato CarbonPilot")
    logger.info("="*50)
    
    # Inizializza i dati di seed
    seed_data = SeedData()
    
    # Crea una sessione del database
    db = SessionLocal()
    
    try:
        # Pulizia database (se richiesta)
        if not args.no_clear:
            clear_database(db, args.debug)
        else:
            logger.info("⚠️ Saltata pulizia database (--no-clear)")
        
        # Esegui il seed in ordine
        seed_catalogo(db, seed_data, args.debug)
        seed_tools(db, seed_data, args.debug)
        seed_cicli_cura(db, seed_data, args.debug)
        seed_autoclavi(db, seed_data, args.debug)
        seed_parti(db, seed_data, args.debug)
        seed_odl(db, seed_data, args.debug)
        seed_nesting_results(db, seed_data, args.debug)
        seed_report(db, seed_data, args.debug)
        seed_tempo_fasi(db, seed_data, args.debug)
        seed_odl_logs(db, seed_data, args.debug)
        
        # Stampa riepilogo finale
        print_summary(seed_data)
        
        logger.info("\n🎉 SEED COMPLETATO CON SUCCESSO!")
        
    except Exception as e:
        logger.error(f"❌ Errore durante il seed: {e}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        db.rollback()
        sys.exit(1)
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 