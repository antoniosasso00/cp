#!/usr/bin/env python
"""
Script per il seed dei dati di test nel database CarbonPilot.
Questo script è idempotente: crea i dati solo se non esistono già.
"""

import os
import sys
import json
import requests
import logging
import argparse
import random
import socket
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

# Dati di test predefiniti
CATALOGO_PARTS = [
    {
        "part_number": "CPX-101",
        "descrizione": "Pannello laterale sinistro",
        "categoria": "PANNELLI",
        "attivo": True,
        "note": "Pannello in composito per lato sinistro"
    },
    {
        "part_number": "CPX-102",
        "descrizione": "Pannello laterale destro",
        "categoria": "PANNELLI",
        "attivo": True,
        "note": "Pannello in composito per lato destro"
    },
    {
        "part_number": "CPX-201",
        "descrizione": "Supporto motore",
        "categoria": "SUPPORTI",
        "attivo": True,
        "note": "Supporto in composito per motore"
    },
    {
        "part_number": "CPX-301",
        "descrizione": "Coperchio vano batterie",
        "categoria": "COPERCHI",
        "attivo": True,
        "note": "Coperchio in composito per vano batterie"
    },
    {
        "part_number": "CPX-401",
        "descrizione": "Fascia frontale",
        "categoria": "FASCE",
        "attivo": True,
        "note": "Fascia in composito per parte frontale"
    }
]

TOOLS = [
    {
        "codice": "ST-101",
        "descrizione": "Stampo pannelli laterali",
        "lunghezza_piano": 2000.0,
        "larghezza_piano": 1000.0,
        "disponibile": True,
        "note": "Stampo principale per pannelli laterali"
    },
    {
        "codice": "ST-201",
        "descrizione": "Stampo supporto motore",
        "lunghezza_piano": 1500.0,
        "larghezza_piano": 800.0,
        "disponibile": True,
        "note": "Stampo dedicato per supporti motore"
    },
    {
        "codice": "ST-301",
        "descrizione": "Stampo coperchi e fasce",
        "lunghezza_piano": 1800.0,
        "larghezza_piano": 900.0,
        "disponibile": True,
        "note": "Stampo versatile per coperchi e fasce"
    }
]

CICLI_CURA = [
    {
        "nome": "Ciclo Standard",
        "temperatura_stasi1": 120.0,
        "pressione_stasi1": 4.0,
        "durata_stasi1": 60,
        "attiva_stasi2": False,
        "descrizione": "Ciclo standard per parti non critiche"
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
        "descrizione": "Ciclo avanzato per parti strutturali"
    }
]

AUTOCLAVI = [
    {
        "nome": "Autoclave Principale",
        "codice": "AUTO-001",
        "lunghezza": 3000.0,
        "larghezza_piano": 1500.0,
        "num_linee_vuoto": 4,
        "temperatura_max": 180.0,
        "pressione_max": 7.0,
        "stato": "DISPONIBILE",
        "produttore": "Scholz",
        "anno_produzione": 2023,
        "note": "Autoclave principale per produzione"
    },
    {
        "nome": "Autoclave Secondaria",
        "codice": "AUTO-002",
        "lunghezza": 2500.0,
        "larghezza_piano": 1200.0,
        "num_linee_vuoto": 3,
        "temperatura_max": 180.0,
        "pressione_max": 7.0,
        "stato": "DISPONIBILE",
        "produttore": "Scholz",
        "anno_produzione": 2022,
        "note": "Autoclave secondaria per piccole parti"
    },
    {
        "nome": "Autoclave Manutenzione",
        "codice": "AUTO-003",
        "lunghezza": 2800.0,
        "larghezza_piano": 1400.0,
        "num_linee_vuoto": 4,
        "temperatura_max": 180.0,
        "pressione_max": 7.0,
        "stato": "MANUTENZIONE",
        "produttore": "Scholz",
        "anno_produzione": 2021,
        "note": "In manutenzione programmata"
    }
]

# Variabile globale per memorizzare gli ID dei dati creati
created_ids = {
    "cicli_cura": {},
    "tools": {},
    "parti": {}
}

def post_if_missing(endpoint: str, unique_field: str, data: dict, debug: bool = False) -> Optional[dict]:
    """
    Crea un record solo se non esiste già un record con lo stesso valore nel campo unique_field.
    
    Args:
        endpoint: Nome dell'endpoint API (es. "catalogo", "tools")
        unique_field: Campo univoco per identificare il record (es. "part_number", "codice")
                      Se l'endpoint è "odl", questo parametro è ignorato perché gli ODL non hanno un campo univoco
        data: Dati da inviare nella richiesta POST
        debug: Se True, mostra informazioni dettagliate sugli errori
    
    Returns:
        dict: Dati creati con l'ID incluso o None se fallisce o l'elemento esiste già
    """
    endpoint_url = f"{BASE_URL}{API_PREFIX}/{endpoint}/"
    try:
        # Per ODL non facciamo la verifica di esistenza, creiamo sempre un nuovo record
        if endpoint == "odl":
            if debug:
                logger.debug(f"Creazione ODL: {json.dumps(data, indent=2)}")
            
            r = requests.post(endpoint_url, json=data)
            if r.status_code == 200 or r.status_code == 201:
                created_data = r.json()
                logger.info(f"[✔] {endpoint} creato con ID {created_data.get('id', 'N/A')}")
                return created_data
            else:
                logger.error(f"[!] Errore creazione {endpoint}: {r.status_code} - {r.text}")
                if debug:
                    logger.debug(f"Dati inviati: {json.dumps(data, indent=2)}")
                return None
        
        # Per altri endpoint, verifica se esiste già
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
        
        # POST per creare il record
        r = requests.post(endpoint_url, json=data)
        if r.status_code == 200 or r.status_code == 201:
            created_data = r.json()
            logger.info(f"[✔] {endpoint} creato: {data[unique_field]}")
            return created_data
        elif r.status_code == 422:
            error_data = r.json()
            if debug:
                logger.debug(f"Errore validazione: {json.dumps(error_data, indent=2)}")
                
            # Prova a correggere errori comuni
            if 'detail' in error_data:
                for error in error_data['detail']:
                    if error['type'] == 'missing':
                        field = error['loc'][1]
                        logger.warning(f"Campo mancante: {field}. Tentativo di correzione...")
                        
                        # Valori di default
                        if field in ['disponibile', 'attivo']:
                            data[field] = True
                        elif field.startswith('num_'):
                            data[field] = 1
                        elif field.endswith('_id'):
                            data[field] = None
                
                # Riprova con i dati corretti
                if debug:
                    logger.debug(f"Riprovo con dati corretti: {json.dumps(data, indent=2)}")
                r = requests.post(endpoint_url, json=data)
                if r.status_code == 200 or r.status_code == 201:
                    created_data = r.json()
                    logger.info(f"[✔] {endpoint} creato dopo correzione: {data[unique_field]}")
                    return created_data
                else:
                    logger.error(f"[!] Errore creazione {endpoint} dopo correzione: {r.text}")
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

def seed_catalogo(debug: bool = False):
    """Popola il catalogo con parti predefinite."""
    logger.info("\n📦 Popolamento catalogo parti...")
    for part in CATALOGO_PARTS:
        post_if_missing("catalogo", "part_number", part, debug)

def seed_tools(debug: bool = False):
    """Popola gli stampi con dati predefiniti."""
    logger.info("\n🔧 Popolamento stampi...")
    for i, tool in enumerate(TOOLS):
        created_tool = post_if_missing("tools", "codice", tool, debug)
        if created_tool and created_tool.get('id'):
            idx = i + 1  # Gli indici iniziano da 1 nello script seed
            created_ids["tools"][idx] = created_tool.get('id')
            if debug:
                logger.debug(f"Memorizzato Tool ID: {created_tool.get('id')} per indice {idx}")

def seed_cicli_cura(debug: bool = False):
    """Popola i cicli di cura con dati predefiniti."""
    logger.info("\n🔄 Popolamento cicli di cura...")
    for i, ciclo in enumerate(CICLI_CURA):
        created_ciclo = post_if_missing("cicli-cura", "nome", ciclo, debug)
        if created_ciclo and created_ciclo.get('id'):
            idx = i + 1  # Gli indici iniziano da 1 nello script seed
            created_ids["cicli_cura"][idx] = created_ciclo.get('id')
            if debug:
                logger.debug(f"Memorizzato Ciclo Cura ID: {created_ciclo.get('id')} per indice {idx}")

def seed_autoclavi(debug: bool = False):
    """Popola le autoclavi con dati predefiniti."""
    logger.info("\n🏭 Popolamento autoclavi...")
    for autoclave in AUTOCLAVI:
        post_if_missing("autoclavi", "codice", autoclave, debug)

def seed_parti(debug: bool = False):
    """Popola le parti con dati predefiniti."""
    logger.info("\n📋 Popolamento parti...")
    
    # Adatta i dati delle parti usando gli ID effettivi
    modified_parti = []
    for parte in PARTI:
        modified_parte = parte.copy()
        
        # Sostituisci gli ID dei cicli di cura con quelli effettivi
        if "ciclo_cura_id" in modified_parte and modified_parte["ciclo_cura_id"] in created_ids["cicli_cura"]:
            idx = modified_parte["ciclo_cura_id"]
            modified_parte["ciclo_cura_id"] = created_ids["cicli_cura"].get(idx)
            if debug:
                logger.debug(f"Sostituito ciclo_cura_id {idx} con {modified_parte['ciclo_cura_id']}")
        
        # Sostituisci gli ID dei tool con quelli effettivi
        if "tool_ids" in modified_parte:
            tool_ids = []
            for tool_idx in modified_parte["tool_ids"]:
                if tool_idx in created_ids["tools"]:
                    tool_ids.append(created_ids["tools"][tool_idx])
            modified_parte["tool_ids"] = tool_ids
            if debug:
                logger.debug(f"Sostituiti tool_ids {parte['tool_ids']} con {modified_parte['tool_ids']}")
        
        modified_parti.append(modified_parte)
    
    # Crea le parti
    for i, parte in enumerate(modified_parti):
        created_parte = post_if_missing("parti", "part_number", parte, debug)
        if created_parte and created_parte.get('id'):
            idx = i + 1
            created_ids["parti"][idx] = created_parte.get('id')
            if debug:
                logger.debug(f"Memorizzato Parte ID: {created_parte.get('id')} per indice {idx}")

def seed_odl(debug: bool = False):
    """Popola gli ordini di lavoro con dati di test."""
    logger.info("\n📝 Popolamento ordini di lavoro (ODL)...")
    
    # Ottieni tutte le parti
    r = requests.get(f"{BASE_URL}{API_PREFIX}/parti/")
    if r.status_code != 200:
        logger.error(f"[!] Impossibile ottenere l'elenco delle parti: {r.status_code}")
        return
    
    parti = r.json()
    if not parti:
        logger.error("[!] Nessuna parte trovata, impossibile creare ODL")
        return
    
    status_options = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]
    
    for i, parte in enumerate(parti):
        parte_id = parte["id"]
        
        # Ottieni i tool associati a questa parte
        tool_ids = [tool["id"] for tool in parte.get("tools", [])]
        
        if not tool_ids:
            logger.warning(f"[!] La parte {parte['part_number']} non ha tool associati, salto creazione ODL")
            continue
        
        # Crea da 1 a 2 ODL per ogni parte
        num_odl = random.randint(1, 2)
        for j in range(num_odl):
            # Seleziona un tool casuale tra quelli associati alla parte
            tool_id = random.choice(tool_ids)
            
            # Crea l'ODL
            odl_data = {
                "parte_id": parte_id,
                "tool_id": tool_id,
                "priorita": random.randint(1, 3),
                "status": random.choice(status_options),
                "note": f"ODL di test per {parte['part_number']}, creato automaticamente."
            }
            
            created_odl = post_if_missing("odl", "id", odl_data, debug)
            if not created_odl and debug:
                logger.debug(f"ODL non creato o già esistente per parte_id={parte_id}, tool_id={tool_id}")

def main():
    """Funzione principale per il seed dei dati di test."""
    parser = argparse.ArgumentParser(description="Seed di dati di test per CarbonPilot")
    parser.add_argument("--debug", action="store_true", help="Attiva la modalità debug con dettagli aggiuntivi")
    args = parser.parse_args()
    
    debug = args.debug
    if debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info("\n🌱 Seed dati di test in corso...")
    
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
    
    # Popolamento dati
    seed_catalogo(debug)
    seed_tools(debug)
    seed_cicli_cura(debug)
    seed_autoclavi(debug)
    seed_parti(debug)
    seed_odl(debug)
    
    # Verifica finale
    logger.info("\n🔍 Verifica endpoint in corso...")
    success = all([
        verify_endpoint("catalogo", len(CATALOGO_PARTS), debug),
        verify_endpoint("tools", len(TOOLS), debug),
        verify_endpoint("cicli-cura", len(CICLI_CURA), debug),
        verify_endpoint("autoclavi", len(AUTOCLAVI), debug),
        verify_endpoint("parti", len(PARTI), debug),
        verify_endpoint("odl", 1, debug)
    ])
    
    if success:
        logger.info("\n✨ Seed e verifica completati con successo!")
        logger.info("\n✅ Seed completato. Dati visibili nel frontend. Dashboard pronta.")
    else:
        logger.error("\n❌ Alcuni endpoint non hanno restituito i dati attesi. Controlla i log per i dettagli.")
        if not debug:
            logger.info("🔍 Riprova con l'opzione --debug per ottenere maggiori informazioni: python tools/seed_test_data.py --debug")

# Definizione delle parti (da usare dopo aver ottenuto gli ID dai cicli di cura e tool)
PARTI = [
    {
        "part_number": "CPX-101",
        "descrizione_breve": "Pannello SX",
        "num_valvole_richieste": 4,
        "ciclo_cura_id": 1,  # Ciclo Standard
        "tool_ids": [1],     # ST-101
        "note_produzione": "Pannello laterale sinistro"
    },
    {
        "part_number": "CPX-102",
        "descrizione_breve": "Pannello DX",
        "num_valvole_richieste": 4,
        "ciclo_cura_id": 1,  # Ciclo Standard
        "tool_ids": [1],     # ST-101
        "note_produzione": "Pannello laterale destro"
    },
    {
        "part_number": "CPX-201",
        "descrizione_breve": "Supporto Motore",
        "num_valvole_richieste": 6,
        "ciclo_cura_id": 2,  # Ciclo Avanzato
        "tool_ids": [2],     # ST-201
        "note_produzione": "Supporto motore con rinforzi"
    },
    {
        "part_number": "CPX-301",
        "descrizione_breve": "Coperchio Batterie",
        "num_valvole_richieste": 2,
        "ciclo_cura_id": 1,  # Ciclo Standard
        "tool_ids": [3],     # ST-301
        "note_produzione": "Coperchio vano batterie"
    },
    {
        "part_number": "CPX-401",
        "descrizione_breve": "Fascia Frontale",
        "num_valvole_richieste": 3,
        "ciclo_cura_id": 2,  # Ciclo Avanzato
        "tool_ids": [3],     # ST-301
        "note_produzione": "Fascia frontale con rinforzi"
    }
]

if __name__ == "__main__":
    main() 