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
    "parti": {},
    "odl": {}
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
    """Crea gli ODL di test."""
    logger.info("==== Creazione ODL di Test ====")
    
    # Recupera i tools creati
    r = requests.get(f"{BASE_URL}{API_PREFIX}/tools/")
    if r.status_code != 200:
        logger.error(f"Errore nel recupero dei tools: {r.status_code}")
        return
    tools = r.json()
    
    # Recupera le parti create
    r = requests.get(f"{BASE_URL}{API_PREFIX}/parti/")
    if r.status_code != 200:
        logger.error(f"Errore nel recupero delle parti: {r.status_code}")
        return
    parti = r.json()
    
    if not tools or not parti:
        logger.error("Impossibile creare ODL: nessun tool o parte disponibile")
        return
    
    # Stati possibili per gli ODL
    stati = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]
    
    # Crea 5 ODL con stati diversi e priorità variabili
    for i in range(5):
        # Seleziona casualmente una parte e un tool
        parte = random.choice(parti)
        tool = random.choice(tools)
        
        # Crea l'ODL
        data = {
            "parte_id": parte["id"],
            "tool_id": tool["id"],
            "priorita": random.randint(1, 10),
            "status": stati[i],  # Un ODL per ogni stato
            "note": f"ODL di test #{i+1} per {parte['descrizione_breve']}"
        }
        
        # Crea l'ODL e salva l'ID
        odl = post_if_missing("odl", None, data, debug)
        if odl:
            created_ids["odl"][odl["id"]] = odl
    
    logger.info(f"[✔] Creati {len(created_ids['odl'])} ODL di test")

def seed_tempo_fasi(debug: bool = False):
    """Crea dati di test per il monitoraggio dei tempi delle fasi di produzione."""
    logger.info("==== Creazione Tempi Fasi di Test ====")
    
    # Otteniamo gli ODL per cui creare i dati di tempo
    if not created_ids["odl"]:
        logger.error("Nessun ODL disponibile per creare i tempi fase")
        return
    
    # Useremo 3 ODL per creare tempi di fase completi
    odl_ids = list(created_ids["odl"].keys())[:3]
    
    # Fasi di produzione da tracciare
    fasi = ["laminazione", "attesa_cura", "cura"]
    
    # Per ogni ODL creiamo un set completo di fasi
    for idx, odl_id in enumerate(odl_ids):
        # Tempi base per ogni fase (minuti)
        tempi_base = {
            "laminazione": 120,  # 2 ore
            "attesa_cura": 240,  # 4 ore
            "cura": 180  # 3 ore
        }
        
        # Data di base (3 giorni fa)
        now = datetime.now()
        start_date = now - timedelta(days=3)
        
        # Per ogni fase, crea un record di tempo
        for fase in fasi:
            # Data di inizio per questa fase
            inizio_fase = start_date.isoformat()
            
            # Calcola la durata con una leggera variazione casuale
            variazione = random.uniform(0.8, 1.2)  # +/- 20%
            durata_minuti = int(tempi_base[fase] * variazione)
            
            # Calcola la data di fine per questa fase
            fine_fase = (start_date + timedelta(minutes=durata_minuti)).isoformat()
            
            # Aggiorna la data di inizio per la prossima fase
            start_date = start_date + timedelta(minutes=durata_minuti)
            
            # Creazione dati tempo fase
            data = {
                "odl_id": odl_id,
                "fase": fase,
                "inizio_fase": inizio_fase,
                "fine_fase": fine_fase,
                "note": f"Fase {fase} per ODL {odl_id} (test seed)"
            }
            
            # Crea il record tempo fase
            response = requests.post(f"{BASE_URL}{API_PREFIX}/tempo-fasi/", json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"[✔] Creato tempo fase {fase} per ODL {odl_id}")
            else:
                logger.error(f"[!] Errore nella creazione tempo fase: {response.status_code} - {response.text}")
                if debug:
                    logger.debug(f"Dati inviati: {json.dumps(data, indent=2)}")
    
    logger.info("[✔] Seed dei tempi fase completato")

def main():
    parser = argparse.ArgumentParser(description="Script di seed per dati di test")
    parser.add_argument("--debug", action="store_true", help="Abilita log di debug")
    args = parser.parse_args()

    debug = args.debug

    try:
        seed_catalogo(debug)
        seed_tools(debug)
        seed_cicli_cura(debug)
        seed_autoclavi(debug)
        seed_parti(debug)
        seed_odl(debug)
        seed_tempo_fasi(debug)
        
        logger.info("✅ Seed completato con successo!")
    except Exception as e:
        logger.error(f"❌ Errore durante il seed: {e}", exc_info=True)
        sys.exit(1)

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