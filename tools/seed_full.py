#!/usr/bin/env python
"""
Script per il seed completo dei dati nel database CarbonPilot.
Popola il database con dati estesi per testare tutte le funzionalità.
"""

import os
import sys
import json
import requests
import logging
import random
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

# Determina se stiamo eseguendo in Docker o in locale
def is_running_in_docker():
    try:
        with open('/proc/self/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return False

# Imposta l'URL del backend in base all'ambiente
if is_running_in_docker():
    BASE_URL = "http://backend:8000"
    logger.info("Esecuzione in ambiente Docker, utilizzo URL backend: %s", BASE_URL)
else:
    BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    logger.info("Esecuzione in ambiente locale, utilizzo URL backend: %s", BASE_URL)

API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Dati di test completi
CATALOGO_PARTS = [
    {"part_number": "CPX-101", "descrizione": "Pannello laterale sinistro", "categoria": "PANNELLI", "lunghezza": 1200.0, "larghezza": 800.0, "altezza": 50.0, "attivo": True},
    {"part_number": "CPX-102", "descrizione": "Pannello laterale destro", "categoria": "PANNELLI", "lunghezza": 1200.0, "larghezza": 800.0, "altezza": 50.0, "attivo": True},
    {"part_number": "CPX-201", "descrizione": "Supporto motore principale", "categoria": "SUPPORTI", "lunghezza": 800.0, "larghezza": 600.0, "altezza": 80.0, "attivo": True},
    {"part_number": "CPX-202", "descrizione": "Supporto motore secondario", "categoria": "SUPPORTI", "lunghezza": 600.0, "larghezza": 400.0, "altezza": 60.0, "attivo": True},
    {"part_number": "CPX-301", "descrizione": "Coperchio vano batterie", "categoria": "COPERCHI", "lunghezza": 900.0, "larghezza": 700.0, "altezza": 30.0, "attivo": True},
    {"part_number": "CPX-302", "descrizione": "Coperchio vano elettronica", "categoria": "COPERCHI", "lunghezza": 700.0, "larghezza": 500.0, "altezza": 25.0, "attivo": True},
    {"part_number": "CPX-401", "descrizione": "Fascia frontale superiore", "categoria": "FASCE", "lunghezza": 1500.0, "larghezza": 300.0, "altezza": 40.0, "attivo": True},
    {"part_number": "CPX-402", "descrizione": "Fascia frontale inferiore", "categoria": "FASCE", "lunghezza": 1500.0, "larghezza": 250.0, "altezza": 35.0, "attivo": True},
    {"part_number": "CPX-501", "descrizione": "Rinforzo strutturale A", "categoria": "RINFORZI", "lunghezza": 1000.0, "larghezza": 200.0, "altezza": 60.0, "attivo": True},
    {"part_number": "CPX-502", "descrizione": "Rinforzo strutturale B", "categoria": "RINFORZI", "lunghezza": 800.0, "larghezza": 150.0, "altezza": 45.0, "attivo": True}
]

TOOLS = [
    {"part_number_tool": "ST-101", "descrizione": "Stampo pannelli laterali grandi", "lunghezza_piano": 2000.0, "larghezza_piano": 1200.0, "peso": 150.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-102", "descrizione": "Stampo pannelli laterali piccoli", "lunghezza_piano": 1500.0, "larghezza_piano": 1000.0, "peso": 120.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-201", "descrizione": "Stampo supporti motore", "lunghezza_piano": 1200.0, "larghezza_piano": 800.0, "peso": 200.0, "materiale": "Acciaio", "disponibile": True},
    {"part_number_tool": "ST-202", "descrizione": "Stampo supporti secondari", "lunghezza_piano": 800.0, "larghezza_piano": 600.0, "peso": 80.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-301", "descrizione": "Stampo coperchi grandi", "lunghezza_piano": 1000.0, "larghezza_piano": 800.0, "peso": 100.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-302", "descrizione": "Stampo coperchi piccoli", "lunghezza_piano": 800.0, "larghezza_piano": 600.0, "peso": 70.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-401", "descrizione": "Stampo fasce lunghe", "lunghezza_piano": 1800.0, "larghezza_piano": 400.0, "peso": 90.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-402", "descrizione": "Stampo fasce corte", "lunghezza_piano": 1200.0, "larghezza_piano": 350.0, "peso": 60.0, "materiale": "Alluminio", "disponibile": True},
    {"part_number_tool": "ST-501", "descrizione": "Stampo rinforzi strutturali", "lunghezza_piano": 1200.0, "larghezza_piano": 300.0, "peso": 110.0, "materiale": "Acciaio", "disponibile": True},
    {"part_number_tool": "ST-502", "descrizione": "Stampo rinforzi leggeri", "lunghezza_piano": 1000.0, "larghezza_piano": 250.0, "peso": 50.0, "materiale": "Alluminio", "disponibile": True}
]

CICLI_CURA = [
    {"nome": "Ciclo Standard", "temperatura_stasi1": 120.0, "pressione_stasi1": 4.0, "durata_stasi1": 60, "attiva_stasi2": False, "descrizione": "Ciclo standard per parti non critiche"},
    {"nome": "Ciclo Avanzato", "temperatura_stasi1": 130.0, "pressione_stasi1": 5.0, "durata_stasi1": 45, "attiva_stasi2": True, "temperatura_stasi2": 140.0, "pressione_stasi2": 6.0, "durata_stasi2": 30, "descrizione": "Ciclo avanzato per parti strutturali"},
    {"nome": "Ciclo Rapido", "temperatura_stasi1": 110.0, "pressione_stasi1": 3.5, "durata_stasi1": 45, "attiva_stasi2": False, "descrizione": "Ciclo rapido per parti semplici"},
    {"nome": "Ciclo Critico", "temperatura_stasi1": 140.0, "pressione_stasi1": 6.0, "durata_stasi1": 90, "attiva_stasi2": True, "temperatura_stasi2": 150.0, "pressione_stasi2": 7.0, "durata_stasi2": 60, "descrizione": "Ciclo per parti critiche ad alta resistenza"}
]

AUTOCLAVI = [
    {"nome": "Autoclave Alpha", "codice": "AUTO-001", "lunghezza": 3000.0, "larghezza_piano": 1800.0, "num_linee_vuoto": 6, "temperatura_max": 180.0, "pressione_max": 8.0, "max_load_kg": 1500.0, "stato": "DISPONIBILE", "produttore": "Scholz", "anno_produzione": 2023},
    {"nome": "Autoclave Beta", "codice": "AUTO-002", "lunghezza": 2500.0, "larghezza_piano": 1500.0, "num_linee_vuoto": 4, "temperatura_max": 170.0, "pressione_max": 7.0, "max_load_kg": 1200.0, "stato": "DISPONIBILE", "produttore": "Scholz", "anno_produzione": 2022},
    {"nome": "Autoclave Gamma", "codice": "AUTO-003", "lunghezza": 2800.0, "larghezza_piano": 1600.0, "num_linee_vuoto": 5, "temperatura_max": 175.0, "pressione_max": 7.5, "max_load_kg": 1300.0, "stato": "MANUTENZIONE", "produttore": "Scholz", "anno_produzione": 2021},
    {"nome": "Autoclave Delta", "codice": "AUTO-004", "lunghezza": 2200.0, "larghezza_piano": 1200.0, "num_linee_vuoto": 3, "temperatura_max": 160.0, "pressione_max": 6.5, "max_load_kg": 800.0, "stato": "DISPONIBILE", "produttore": "Scholz", "anno_produzione": 2020}
]

# Variabile globale per memorizzare gli ID dei dati creati
created_ids = {
    "cicli_cura": {},
    "tools": {},
    "parti": {},
    "odl": {},
    "autoclavi": {},
    "nesting_results": {}
}

def post_if_missing(endpoint: str, unique_field: str, data: dict, debug: bool = False) -> Optional[dict]:
    """Crea un record solo se non esiste già."""
    endpoint_url = f"{BASE_URL}{API_PREFIX}/{endpoint}/"
    try:
        # Per ODL, non controlliamo duplicati perché non hanno campo univoco
        if endpoint == "odl":
            response = requests.post(endpoint_url, json=data, timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Creato {endpoint}: {result.get('id', 'N/A')}")
                return result
            else:
                logger.error(f"❌ Errore creazione {endpoint}: {response.status_code} - {response.text}")
                return None
        
        # Per altri endpoint, controlliamo se esiste già
        get_response = requests.get(endpoint_url, timeout=30)
        if get_response.status_code == 200:
            existing_items = get_response.json()
            for item in existing_items:
                if item.get(unique_field) == data.get(unique_field):
                    logger.info(f"⏭️  {endpoint} con {unique_field}='{data.get(unique_field)}' già esistente")
                    return item
        
        # Se non esiste, lo creiamo
        response = requests.post(endpoint_url, json=data, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ Creato {endpoint}: {data.get(unique_field, result.get('id', 'N/A'))}")
            return result
        else:
            logger.error(f"❌ Errore creazione {endpoint}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore durante creazione {endpoint}: {str(e)}")
        return None

def seed_catalogo(debug: bool = False):
    """Popola la tabella catalogo con i part numbers."""
    logger.info("🌱 Seeding catalogo...")
    for part_data in CATALOGO_PARTS:
        result = post_if_missing("catalogo", "part_number", part_data, debug)

def seed_tools(debug: bool = False):
    """Popola la tabella tools con gli stampi."""
    logger.info("🌱 Seeding tools...")
    for tool_data in TOOLS:
        result = post_if_missing("tools", "part_number_tool", tool_data, debug)
        if result:
            created_ids["tools"][tool_data["part_number_tool"]] = result["id"]

def seed_cicli_cura(debug: bool = False):
    """Popola la tabella cicli_cura."""
    logger.info("🌱 Seeding cicli cura...")
    for ciclo_data in CICLI_CURA:
        result = post_if_missing("cicli-cura", "nome", ciclo_data, debug)
        if result:
            created_ids["cicli_cura"][ciclo_data["nome"]] = result["id"]

def seed_autoclavi(debug: bool = False):
    """Popola la tabella autoclavi."""
    logger.info("🌱 Seeding autoclavi...")
    for autoclave_data in AUTOCLAVI:
        result = post_if_missing("autoclavi", "codice", autoclave_data, debug)
        if result:
            created_ids["autoclavi"][autoclave_data["codice"]] = result["id"]

def seed_parti(debug: bool = False):
    """Popola la tabella parti collegando part_number e cicli di cura."""
    logger.info("🌱 Seeding parti...")
    
    # Associazioni part_number -> ciclo di cura
    part_ciclo_mapping = {
        "CPX-101": "Ciclo Standard",
        "CPX-102": "Ciclo Standard", 
        "CPX-201": "Ciclo Avanzato",
        "CPX-202": "Ciclo Standard",
        "CPX-301": "Ciclo Rapido",
        "CPX-302": "Ciclo Rapido",
        "CPX-401": "Ciclo Standard",
        "CPX-402": "Ciclo Standard",
        "CPX-501": "Ciclo Critico",
        "CPX-502": "Ciclo Avanzato"
    }
    
    for part_number, ciclo_nome in part_ciclo_mapping.items():
        ciclo_id = created_ids["cicli_cura"].get(ciclo_nome)
        if not ciclo_id:
            logger.warning(f"⚠️  Ciclo '{ciclo_nome}' non trovato per parte {part_number}")
            continue
            
        parte_data = {
            "part_number": part_number,
            "descrizione_breve": f"Parte {part_number}",
            "num_valvole_richieste": random.randint(1, 3),
            "ciclo_cura_id": ciclo_id,
            "note_produzione": f"Note per {part_number}"
        }
        
        result = post_if_missing("parti", "part_number", parte_data, debug)
        if result:
            created_ids["parti"][part_number] = result["id"]

def seed_odl(debug: bool = False):
    """Popola la tabella ODL con ordini in vari stati."""
    logger.info("🌱 Seeding ODL...")
    
    # Stati possibili per gli ODL
    stati_odl = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"]
    
    # Associazioni parte -> tool
    parte_tool_mapping = {
        "CPX-101": "ST-101", "CPX-102": "ST-101",
        "CPX-201": "ST-201", "CPX-202": "ST-202", 
        "CPX-301": "ST-301", "CPX-302": "ST-302",
        "CPX-401": "ST-401", "CPX-402": "ST-402",
        "CPX-501": "ST-501", "CPX-502": "ST-502"
    }
    
    # Creiamo 10 ODL distribuiti in vari stati
    for i in range(10):
        part_number = random.choice(list(parte_tool_mapping.keys()))
        tool_code = parte_tool_mapping[part_number]
        
        parte_id = created_ids["parti"].get(part_number)
        tool_id = created_ids["tools"].get(tool_code)
        
        if not parte_id or not tool_id:
            logger.warning(f"⚠️  Parte {part_number} o Tool {tool_code} non trovati")
            continue
        
        # Distribuiamo gli stati: più ODL in "Attesa Cura" per il test
        if i < 4:
            status = "Attesa Cura"
        elif i < 6:
            status = "Finito"
        elif i < 8:
            status = "Preparazione"
        else:
            status = random.choice(stati_odl)
        
        odl_data = {
            "parte_id": parte_id,
            "tool_id": tool_id,
            "priorita": random.randint(1, 5),
            "status": status,
            "note": f"ODL di test #{i+1} - {part_number}"
        }
        
        result = post_if_missing("odl", None, odl_data, debug)
        if result:
            created_ids["odl"][f"odl_{i+1}"] = result["id"]

def seed_nesting_results(debug: bool = False):
    """Crea alcuni risultati di nesting di esempio."""
    logger.info("🌱 Seeding nesting results...")
    
    # Prendiamo l'autoclave Alpha per i test
    autoclave_id = created_ids["autoclavi"].get("AUTO-001")
    if not autoclave_id:
        logger.warning("⚠️  Autoclave AUTO-001 non trovata per nesting")
        return
    
    # Nesting 1: Completato
    nesting_data_1 = {
        "autoclave_id": autoclave_id,
        "odl_ids": list(created_ids["odl"].values())[:3],
        "stato": "Completato",
        "area_utilizzata": 450.0,
        "area_totale": 540.0,
        "valvole_utilizzate": 6,
        "valvole_totali": 6,
        "peso_totale_kg": 420.0,
        "area_piano_1": 300.0,
        "area_piano_2": 150.0,
        "superficie_piano_2_max": 200.0,
        "note": "Nesting completato con successo"
    }
    
    # Nesting 2: In sospeso
    nesting_data_2 = {
        "autoclave_id": autoclave_id,
        "odl_ids": list(created_ids["odl"].values())[3:5],
        "stato": "In sospeso",
        "area_utilizzata": 280.0,
        "area_totale": 540.0,
        "valvole_utilizzate": 4,
        "valvole_totali": 6,
        "peso_totale_kg": 250.0,
        "area_piano_1": 200.0,
        "area_piano_2": 80.0,
        "superficie_piano_2_max": 200.0,
        "note": "Nesting in attesa di conferma"
    }
    
    # Nesting 3: Errore
    nesting_data_3 = {
        "autoclave_id": autoclave_id,
        "odl_ids": list(created_ids["odl"].values())[5:7],
        "stato": "Errore",
        "area_utilizzata": 0.0,
        "area_totale": 540.0,
        "valvole_utilizzate": 0,
        "valvole_totali": 6,
        "peso_totale_kg": 0.0,
        "area_piano_1": 0.0,
        "area_piano_2": 0.0,
        "superficie_piano_2_max": 200.0,
        "note": "Errore durante il calcolo del nesting"
    }
    
    for i, nesting_data in enumerate([nesting_data_1, nesting_data_2, nesting_data_3], 1):
        try:
            response = requests.post(f"{BASE_URL}{API_PREFIX}/nesting-results/", json=nesting_data, timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                created_ids["nesting_results"][f"nesting_{i}"] = result["id"]
                logger.info(f"✅ Creato nesting result #{i}: {result['id']}")
            else:
                logger.error(f"❌ Errore creazione nesting #{i}: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Errore durante creazione nesting #{i}: {str(e)}")

def seed_reports(debug: bool = False):
    """Crea alcuni report di esempio."""
    logger.info("🌱 Seeding reports...")
    
    # Report 1: Report di produzione
    report_data_1 = {
        "filename": "report_produzione_2024_01.pdf",
        "file_path": "/reports/report_produzione_2024_01.pdf",
        "report_type": "produzione",
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-31T23:59:59",
        "include_sections": "produzione,tempi",
        "file_size_bytes": 1024000
    }
    
    # Report 2: Report qualità
    report_data_2 = {
        "filename": "report_qualita_2024_01.pdf", 
        "file_path": "/reports/report_qualita_2024_01.pdf",
        "report_type": "qualita",
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-31T23:59:59",
        "include_sections": "qualita,difetti",
        "file_size_bytes": 856000
    }
    
    # Report 3: Report nesting
    report_data_3 = {
        "filename": "report_nesting_2024_01.pdf",
        "file_path": "/reports/report_nesting_2024_01.pdf", 
        "report_type": "nesting",
        "period_start": "2024-01-01T00:00:00",
        "period_end": "2024-01-31T23:59:59",
        "include_sections": "nesting,efficienza",
        "file_size_bytes": 1200000
    }
    
    for i, report_data in enumerate([report_data_1, report_data_2, report_data_3], 1):
        try:
            response = requests.post(f"{BASE_URL}{API_PREFIX}/reports/", json=report_data, timeout=30)
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Creato report #{i}: {result['filename']}")
            else:
                logger.error(f"❌ Errore creazione report #{i}: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Errore durante creazione report #{i}: {str(e)}")

def main():
    """Funzione principale per eseguire il seed completo."""
    logger.info("🚀 Avvio seed completo del database CarbonPilot...")
    
    try:
        # Verifica connessione al backend
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            logger.error("❌ Backend non raggiungibile")
            return
        
        logger.info("✅ Backend raggiungibile")
        
        # Esegui il seed in ordine
        seed_catalogo()
        seed_cicli_cura()
        seed_autoclavi()
        seed_tools()
        seed_parti()
        seed_odl()
        seed_nesting_results()
        seed_reports()
        
        logger.info("🎉 Seed completo terminato con successo!")
        logger.info(f"📊 Dati creati: {len(created_ids['parti'])} parti, {len(created_ids['tools'])} tools, {len(created_ids['odl'])} ODL")
        
    except Exception as e:
        logger.error(f"❌ Errore durante il seed: {str(e)}")

if __name__ == "__main__":
    main() 