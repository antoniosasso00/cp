#!/usr/bin/env python
"""
Script per il seed minimale dei dati nel database CarbonPilot.
Popola il database con dati essenziali per testare il flusso ODL → nesting → cura.
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

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

# Dati di test minimali
CATALOGO_PARTS = [
    {
        "part_number": "TEST-001",
        "descrizione": "Pannello test leggero",
        "categoria": "TEST",
        "lunghezza": 800.0,
        "larghezza": 600.0,
        "altezza": 30.0,
        "attivo": True,
        "note": "Parte per test flusso completo"
    },
    {
        "part_number": "TEST-002", 
        "descrizione": "Supporto test pesante",
        "categoria": "TEST",
        "lunghezza": 1200.0,
        "larghezza": 800.0,
        "altezza": 60.0,
        "attivo": True,
        "note": "Parte per test carico pesante"
    }
]

TOOLS = [
    {
        "part_number_tool": "TOOL-LIGHT",
        "descrizione": "Stampo test leggero",
        "lunghezza_piano": 1000.0,
        "larghezza_piano": 700.0,
        "peso": 50.0,
        "materiale": "Alluminio",
        "disponibile": True,
        "note": "Tool leggero per test nesting"
    },
    {
        "part_number_tool": "TOOL-HEAVY",
        "descrizione": "Stampo test pesante", 
        "lunghezza_piano": 1500.0,
        "larghezza_piano": 900.0,
        "peso": 300.0,
        "materiale": "Acciaio",
        "disponibile": True,
        "note": "Tool pesante per test limiti peso"
    }
]

CICLI_CURA = [
    {
        "nome": "Ciclo Test",
        "temperatura_stasi1": 120.0,
        "pressione_stasi1": 4.0,
        "durata_stasi1": 30,
        "attiva_stasi2": False,
        "descrizione": "Ciclo rapido per test"
    }
]

AUTOCLAVI = [
    {
        "nome": "Autoclave Test",
        "codice": "TEST-AUTO",
        "lunghezza": 2000.0,
        "larghezza_piano": 1200.0,
        "num_linee_vuoto": 4,
        "temperatura_max": 150.0,
        "pressione_max": 6.0,
        "max_load_kg": 500.0,
        "stato": "DISPONIBILE",
        "produttore": "Test Corp",
        "anno_produzione": 2024,
        "note": "Autoclave configurabile per test"
    }
]

# Variabile globale per memorizzare gli ID dei dati creati
created_ids = {
    "cicli_cura": {},
    "tools": {},
    "parti": {},
    "odl": {},
    "autoclavi": {}
}

def clear_database():
    """Pulisce il database eliminando tutti i dati esistenti."""
    logger.info("🧹 Pulizia database in corso...")
    
    endpoints_to_clear = [
        "odl",
        "nesting-results", 
        "reports",
        "parti",
        "tools",
        "autoclavi",
        "cicli-cura",
        "catalogo"
    ]
    
    for endpoint in endpoints_to_clear:
        try:
            # Ottieni tutti gli elementi
            response = requests.get(f"{BASE_URL}{API_PREFIX}/{endpoint}/", timeout=30)
            if response.status_code == 200:
                items = response.json()
                
                # Elimina ogni elemento
                for item in items:
                    item_id = item.get('id') or item.get('part_number')
                    if item_id:
                        delete_response = requests.delete(f"{BASE_URL}{API_PREFIX}/{endpoint}/{item_id}", timeout=30)
                        if delete_response.status_code in [200, 204]:
                            logger.info(f"🗑️  Eliminato {endpoint}: {item_id}")
                        else:
                            logger.warning(f"⚠️  Errore eliminazione {endpoint}/{item_id}: {delete_response.status_code}")
            
        except Exception as e:
            logger.warning(f"⚠️  Errore durante pulizia {endpoint}: {str(e)}")
    
    logger.info("✅ Pulizia database completata")

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
    """Popola la tabella catalogo con i part numbers di test."""
    logger.info("🌱 Seeding catalogo test...")
    for part_data in CATALOGO_PARTS:
        result = post_if_missing("catalogo", "part_number", part_data, debug)

def seed_tools(debug: bool = False):
    """Popola la tabella tools con gli stampi di test."""
    logger.info("🌱 Seeding tools test...")
    for tool_data in TOOLS:
        result = post_if_missing("tools", "part_number_tool", tool_data, debug)
        if result:
            created_ids["tools"][tool_data["part_number_tool"]] = result["id"]

def seed_cicli_cura(debug: bool = False):
    """Popola la tabella cicli_cura con il ciclo di test."""
    logger.info("🌱 Seeding cicli cura test...")
    for ciclo_data in CICLI_CURA:
        result = post_if_missing("cicli-cura", "nome", ciclo_data, debug)
        if result:
            created_ids["cicli_cura"][ciclo_data["nome"]] = result["id"]

def seed_autoclavi(debug: bool = False):
    """Popola la tabella autoclavi con l'autoclave di test."""
    logger.info("🌱 Seeding autoclavi test...")
    for autoclave_data in AUTOCLAVI:
        result = post_if_missing("autoclavi", "codice", autoclave_data, debug)
        if result:
            created_ids["autoclavi"][autoclave_data["codice"]] = result["id"]

def seed_parti(debug: bool = False):
    """Popola la tabella parti collegando part_number e ciclo di cura."""
    logger.info("🌱 Seeding parti test...")
    
    ciclo_id = created_ids["cicli_cura"].get("Ciclo Test")
    if not ciclo_id:
        logger.error("❌ Ciclo Test non trovato")
        return
    
    # Associazioni part_number -> tool
    part_tool_mapping = {
        "TEST-001": "TOOL-LIGHT",
        "TEST-002": "TOOL-HEAVY"
    }
    
    for part_number, tool_code in part_tool_mapping.items():
        parte_data = {
            "part_number": part_number,
            "descrizione_breve": f"Parte test {part_number}",
            "num_valvole_richieste": 1,
            "ciclo_cura_id": ciclo_id,
            "note_produzione": f"Parte per test flusso - {part_number}"
        }
        
        result = post_if_missing("parti", "part_number", parte_data, debug)
        if result:
            created_ids["parti"][part_number] = result["id"]

def seed_odl(debug: bool = False):
    """Popola la tabella ODL con ordini in stato 'Preparazione'."""
    logger.info("🌱 Seeding ODL test...")
    
    # Associazioni parte -> tool
    parte_tool_mapping = {
        "TEST-001": "TOOL-LIGHT",
        "TEST-002": "TOOL-HEAVY"
    }
    
    # Creiamo 2 ODL in stato "Preparazione"
    for i, (part_number, tool_code) in enumerate(parte_tool_mapping.items(), 1):
        parte_id = created_ids["parti"].get(part_number)
        tool_id = created_ids["tools"].get(tool_code)
        
        if not parte_id or not tool_id:
            logger.warning(f"⚠️  Parte {part_number} o Tool {tool_code} non trovati")
            continue
        
        odl_data = {
            "parte_id": parte_id,
            "tool_id": tool_id,
            "priorita": i,
            "status": "Preparazione",
            "note": f"ODL test #{i} - {part_number} - Pronto per flusso completo"
        }
        
        result = post_if_missing("odl", None, odl_data, debug)
        if result:
            created_ids["odl"][f"test_odl_{i}"] = result["id"]

def print_test_summary():
    """Stampa un riassunto dei dati creati per il test."""
    logger.info("📋 RIASSUNTO DATI TEST CREATI:")
    logger.info("=" * 50)
    logger.info(f"📦 Catalogo Parts: {len(CATALOGO_PARTS)} (TEST-001, TEST-002)")
    logger.info(f"🔧 Tools: {len(TOOLS)} (TOOL-LIGHT 50kg, TOOL-HEAVY 300kg)")
    logger.info(f"🔄 Cicli Cura: {len(CICLI_CURA)} (Ciclo Test - 30min)")
    logger.info(f"🏭 Autoclavi: {len(AUTOCLAVI)} (TEST-AUTO - max 500kg)")
    logger.info(f"📋 Parti: {len(created_ids['parti'])} parti create")
    logger.info(f"📝 ODL: {len(created_ids['odl'])} ODL in 'Preparazione'")
    logger.info("=" * 50)
    logger.info("🎯 FLUSSO TEST SUGGERITO:")
    logger.info("1. Login come laminatore → avanza ODL a 'Attesa Cura'")
    logger.info("2. Login come autoclavista → crea nesting")
    logger.info("3. Conferma nesting → avvia cura")
    logger.info("4. Termina cura → genera report")
    logger.info("5. Visualizza report da admin/responsabile")
    logger.info("=" * 50)

def main(clear_db: bool = False):
    """Funzione principale per eseguire il seed di test."""
    logger.info("🚀 Avvio seed test del database CarbonPilot...")
    
    try:
        # Verifica connessione al backend
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            logger.error("❌ Backend non raggiungibile")
            return
        
        logger.info("✅ Backend raggiungibile")
        
        # Pulisci database se richiesto
        if clear_db:
            clear_database()
        
        # Esegui il seed in ordine
        seed_catalogo()
        seed_cicli_cura()
        seed_autoclavi()
        seed_tools()
        seed_parti()
        seed_odl()
        
        logger.info("🎉 Seed test terminato con successo!")
        print_test_summary()
        
    except Exception as e:
        logger.error(f"❌ Errore durante il seed: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed minimale per test CarbonPilot")
    parser.add_argument("--clear", action="store_true", help="Pulisce il database prima del seed")
    args = parser.parse_args()
    
    main(clear_db=args.clear) 