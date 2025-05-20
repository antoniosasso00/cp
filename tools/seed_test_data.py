#!/usr/bin/env python
"""
Script per il seed dei dati di test nel database CarbonPilot.
Questo script è idempotente: crea i dati solo se non esistono già.
"""

import os
import sys
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

def post_if_missing(endpoint: str, unique_field: str, data: dict):
    """
    Crea un record solo se non esiste già un record con lo stesso valore nel campo unique_field.
    
    Args:
        endpoint: Nome dell'endpoint API (es. "catalogo", "tools")
        unique_field: Campo univoco per identificare il record (es. "part_number", "codice")
        data: Dati da inviare nella richiesta POST
    """
    try:
        # Verifica se esiste già un record con lo stesso valore
        r = requests.get(f"{BASE_URL}{API_PREFIX}/{endpoint}/")
        if r.status_code == 200:
            existing_data = r.json()
            if any(d.get(unique_field) == data[unique_field] for d in existing_data):
                logger.info(f"[✔] {endpoint} già presente: {data[unique_field]}")
                return
        
        # Se non esiste, crea il record
        r = requests.post(f"{BASE_URL}{API_PREFIX}/{endpoint}/", json=data)
        if r.status_code in (200, 201):
            logger.info(f"[+] {endpoint} creato: {data[unique_field]}")
        elif r.status_code in (400, 422):
            error_msg = r.json().get('detail', r.text)
            logger.warning(f"[!] Errore validazione {endpoint}: {error_msg}")
            # Prova a correggere i dati e riprova
            if endpoint == "autoclavi":
                data["reparto"] = "TEST"
                data["lunghezza_piano"] = data.pop("lunghezza", 1000.0)
                r = requests.post(f"{BASE_URL}{API_PREFIX}/{endpoint}/", json=data)
                if r.status_code in (200, 201):
                    logger.info(f"[+] {endpoint} creato (dopo correzione): {data[unique_field]}")
                else:
                    logger.error(f"[!] Errore creazione {endpoint} dopo correzione: {r.text}")
        else:
            logger.error(f"[!] Errore creazione {endpoint}: {r.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"[!] Errore di connessione su {endpoint}: {e}")
    except Exception as e:
        logger.error(f"[!] Errore imprevisto su {endpoint}: {e}")

def verify_endpoint(endpoint: str, expected_items: int = 1):
    """
    Verifica che un endpoint restituisca i dati attesi.
    
    Args:
        endpoint: Nome dell'endpoint API
        expected_items: Numero minimo di elementi attesi
    """
    try:
        r = requests.get(f"{BASE_URL}{API_PREFIX}/{endpoint}/")
        if r.status_code == 200:
            data = r.json()
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

def main():
    """Funzione principale per il seed dei dati di test."""
    logger.info("\n🌱 Seed dati di test in corso...")
    
    # 1. Catalogo
    post_if_missing("catalogo", "part_number", {
        "part_number": "TEST-CAT-001",
        "descrizione": "Parte test per CRUD",
        "categoria": "TEST",
        "attivo": True,
        "note": "creata per testing"
    })
    
    # 2. Tool
    post_if_missing("tools", "codice", {
        "codice": "TOOL-TEST-001",
        "descrizione": "Stampo test",
        "lunghezza_piano": 100.0,
        "larghezza_piano": 50.0,
        "disponibile": True,
        "in_manutenzione": False
    })
    
    # 3. Ciclo Cura
    post_if_missing("cicli-cura", "nome", {
        "nome": "CURA-TEST",
        "temperatura_max": 180,
        "pressione_max": 5.5,
        "temperatura_stasi1": 120,
        "pressione_stasi1": 4.0,
        "durata_stasi1": 60,
        "attiva_stasi2": False,
        "temperatura_stasi2": None,
        "pressione_stasi2": None,
        "durata_stasi2": None
    })
    
    # 4. Autoclave
    post_if_missing("autoclavi", "codice", {
        "nome": "Autoclave Test",
        "codice": "AUTO-TEST-001",
        "lunghezza": 1000.0,
        "larghezza_piano": 500.0,
        "num_linee_vuoto": 4,
        "temperatura_max": 180.0,
        "pressione_max": 7.0,
        "stato": "DISPONIBILE",
        "in_manutenzione": False
    })
    
    # 5. Parte
    post_if_missing("parte", "part_number", {
        "part_number": "TEST-CAT-001",
        "descrizione_breve": "Parte Test",
        "num_valvole_richieste": 4,
        "ciclo_cura_id": 1,
        "tool_ids": [1],
        "note_produzione": "Parte di test"
    })
    
    # Verifica finale
    logger.info("\n🔍 Verifica endpoint in corso...")
    success = all([
        verify_endpoint("catalogo"),
        verify_endpoint("tools"),
        verify_endpoint("cicli-cura"),
        verify_endpoint("autoclavi"),
        verify_endpoint("parte")
    ])
    
    if success:
        logger.info("\n✨ Seed e verifica completati con successo!")
        logger.info("\n✅ Seed completato. Dati visibili nel frontend. Dashboard pronta.")
    else:
        logger.error("\n❌ Alcuni endpoint non hanno restituito i dati attesi. Controlla i log per i dettagli.")

if __name__ == "__main__":
    main() 