#!/usr/bin/env python
"""
Script per il seed dei dati demo nel database CarbonPilot.
Questo script è idempotente: crea i dati solo se non esistono già.
"""

import os
import sys
import json
import requests
import logging
import argparse
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

# Determina se lo script sta girando in un ambiente Docker
IN_DOCKER = os.path.exists('/.dockerenv')

# Se in Docker, usa l'host interno, altrimenti usa localhost
BASE_URL = "http://localhost:8000" if IN_DOCKER else os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

logger.info(f"{'Esecuzione in ambiente Docker, utilizzo' if IN_DOCKER else 'Utilizzo'} URL backend: {BASE_URL}")

# Dati demo predefiniti
CATALOGO_DEMO = {
    "part_number": "CP-DEMO",
    "descrizione": "Parte demo per test",
    "categoria": "DEMO",
    "attivo": True,
    "note": "Parte creata per test manuali"
}

TOOL_DEMO = {
    "codice": "ST-DEMO",
    "descrizione": "Stampo demo per test",
    "lunghezza_piano": 1000.0,
    "larghezza_piano": 500.0,
    "disponibile": True,
    "note": "Stampo creato per test manuali"
}

CICLO_CURA_DEMO = {
    "nome": "Ciclo Demo",
    "temperatura_stasi1": 120.0,
    "pressione_stasi1": 4.0,
    "durata_stasi1": 60,
    "attiva_stasi2": False,
    "descrizione": "Ciclo di cura demo con una sola stasi"
}

AUTOCLAVE_DEMO = {
    "nome": "Autoclave Demo",
    "codice": "AUTO-DEMO",
    "lunghezza": 2000.0,
    "larghezza_piano": 1000.0,
    "num_linee_vuoto": 4,
    "temperatura_max": 180.0,
    "pressione_max": 7.0,
    "stato": "DISPONIBILE",
    "produttore": "Demo",
    "anno_produzione": 2024,
    "note": "Autoclave creata per test manuali"
}

PARTE_DEMO = {
    "part_number": "CP-DEMO",
    "descrizione_breve": "Parte Demo",
    "num_valvole_richieste": 2,
    "note_produzione": "Parte creata per test manuali"
}

ODL_DEMO = {
    "priorita": 1,
    "status": "Attesa Cura",
    "note": "ODL demo in attesa di cura"
}

def post_if_missing(endpoint: str, unique_field: str, data: dict, debug: bool = False) -> Optional[dict]:
    """
    Crea un record solo se non esiste già un record con lo stesso valore nel campo unique_field.
    
    Args:
        endpoint: Nome dell'endpoint API (es. "catalogo", "tools")
        unique_field: Campo univoco per identificare il record (es. "part_number", "codice")
        data: Dati da inviare nella richiesta POST
        debug: Se True, mostra informazioni dettagliate sugli errori
    
    Returns:
        dict: Dati creati con l'ID incluso o None se fallisce o l'elemento esiste già
    """
    endpoint_url = f"{BASE_URL}{API_PREFIX}/{endpoint}/"
    try:
        # Verifica se esiste già un record con lo stesso valore
        r = requests.get(endpoint_url)
        if r.status_code == 200:
            existing_data = r.json()
            if any(d.get(unique_field) == data[unique_field] for d in existing_data):
                logger.info(f"[✔] {endpoint} già presente: {data[unique_field]}")
                # Recupera l'ID dell'elemento esistente per uso futuro
                for item in existing_data:
                    if item.get(unique_field) == data[unique_field]:
                        if debug:
                            logger.debug(f"ID recuperato per {endpoint}/{data[unique_field]}: {item.get('id')}")
                        return item
                return None
        
        # Se non esiste, crea il record
        if debug:
            logger.debug(f"Invio POST a {endpoint_url} con dati: {json.dumps(data, indent=2)}")
        
        r = requests.post(endpoint_url, json=data)
        if r.status_code in (200, 201):
            created_data = r.json()
            logger.info(f"[+] {endpoint} creato: {data[unique_field]} (ID: {created_data.get('id', 'N/A')})")
            return created_data
        else:
            logger.error(f"[!] Errore creazione {endpoint} (status {r.status_code}): {r.text}")
            if debug:
                logger.debug(f"Dati inviati: {json.dumps(data, indent=2)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"[!] Errore di connessione su {endpoint}: {e}")
    except Exception as e:
        logger.error(f"[!] Errore imprevisto su {endpoint}: {str(e)}")
    
    return None

def verify_endpoint(endpoint: str, expected_items: int = 1, debug: bool = False) -> bool:
    """
    Verifica che un endpoint restituisca i dati attesi.
    
    Args:
        endpoint: Nome dell'endpoint API
        expected_items: Numero minimo di elementi attesi
        debug: Se True, mostra informazioni dettagliate
    """
    endpoint_url = f"{BASE_URL}{API_PREFIX}/{endpoint}/"
    try:
        r = requests.get(endpoint_url)
        if r.status_code == 200:
            data = r.json()
            if debug:
                logger.debug(f"Risposta da {endpoint_url}: {len(data)} elementi")
            
            if len(data) >= expected_items:
                logger.info(f"[✔] {endpoint} verificato: {len(data)} elementi trovati")
                return True
            else:
                logger.error(f"[!] {endpoint} ha meno elementi del previsto: {len(data)} < {expected_items}")
        else:
            logger.error(f"[!] Errore verifica {endpoint}: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"[!] Errore verifica {endpoint}: {e}")
    return False

def seed_demo_data(debug: bool = False):
    """Funzione principale per il seed dei dati demo."""
    logger.info("\n🌱 Seed dati demo in corso...")
    
    # 1. Catalogo Part
    catalogo = post_if_missing("catalogo", "part_number", CATALOGO_DEMO, debug)
    if not catalogo:
        logger.error("❌ Impossibile creare il catalogo demo")
        return False
    
    # 2. Tool associato
    tool = post_if_missing("tools", "codice", TOOL_DEMO, debug)
    if not tool:
        logger.error("❌ Impossibile creare il tool demo")
        return False
    
    # 3. Ciclo di cura semplice
    ciclo_cura = post_if_missing("cicli-cura", "nome", CICLO_CURA_DEMO, debug)
    if not ciclo_cura:
        logger.error("❌ Impossibile creare il ciclo di cura demo")
        return False
    
    # 4. Autoclave disponibile
    autoclave = post_if_missing("autoclavi", "codice", AUTOCLAVE_DEMO, debug)
    if not autoclave:
        logger.error("❌ Impossibile creare l'autoclave demo")
        return False
    
    # 5. Parte associata al catalogo
    parte_data = PARTE_DEMO.copy()
    parte_data["ciclo_cura_id"] = ciclo_cura["id"]
    parte = post_if_missing("parti", "part_number", parte_data, debug)
    if not parte:
        logger.error("❌ Impossibile creare la parte demo")
        return False
    
    # Associa il tool alla parte
    tool_association_url = f"{BASE_URL}{API_PREFIX}/parti/{parte['id']}/tools/{tool['id']}"
    try:
        r = requests.post(tool_association_url)
        if r.status_code in (200, 201):
            logger.info(f"[+] Tool {tool['codice']} associato alla parte {parte['part_number']}")
        else:
            logger.warning(f"[!] Impossibile associare il tool alla parte: {r.status_code}")
    except Exception as e:
        logger.error(f"[!] Errore nell'associazione tool-parte: {e}")
    
    # 6. ODL in attesa di cura
    odl_data = ODL_DEMO.copy()
    odl_data["parte_id"] = parte["id"]
    odl_data["tool_id"] = tool["id"]
    odl = post_if_missing("odl", "parte_id", odl_data, debug)
    if not odl:
        logger.error("❌ Impossibile creare l'ODL demo")
        return False
    
    # Verifica finale
    logger.info("\n🔍 Verifica endpoint in corso...")
    success = all([
        verify_endpoint("catalogo", 1, debug),
        verify_endpoint("tools", 1, debug),
        verify_endpoint("cicli-cura", 1, debug),
        verify_endpoint("autoclavi", 1, debug),
        verify_endpoint("parti", 1, debug),
        verify_endpoint("odl", 1, debug)
    ])
    
    if success:
        logger.info("\n✨ Seed demo completato con successo!")
        logger.info("\n✅ Dati demo creati e verificati. Dashboard pronta per i test.")
    else:
        logger.error("\n❌ Alcuni endpoint non hanno restituito i dati attesi.")
        if not debug:
            logger.info("🔍 Riprova con l'opzione --debug per ottenere maggiori informazioni: python tools/seed_demo_data.py --debug")
    
    return success

def main():
    """Funzione principale per il seed dei dati demo."""
    parser = argparse.ArgumentParser(description="Seed di dati demo per CarbonPilot")
    parser.add_argument("--debug", action="store_true", help="Attiva la modalità debug con dettagli aggiuntivi")
    args = parser.parse_args()
    
    debug = args.debug
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Verifica connessione al backend
    try:
        r = requests.get(f"{BASE_URL}/docs")
        if r.status_code != 200:
            logger.warning(f"⚠️ Il backend potrebbe non essere attivo. Status: {r.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Impossibile connettersi al backend su {BASE_URL}")
        logger.info("Assicurati che il backend sia in esecuzione e l'URL sia corretto.")
        logger.info(f"URL backend corrente: {BASE_URL}")
        exit(1)
    
    # Esegui il seed
    if not seed_demo_data(debug):
        exit(1)

if __name__ == "__main__":
    main() 