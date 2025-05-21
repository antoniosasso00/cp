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
API_PREFIX = os.getenv("API_PREFIX", "/api")

logger.info(f"{'Esecuzione in ambiente Docker, utilizzo' if IN_DOCKER else 'Utilizzo'} URL backend: {BASE_URL}")

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
        "in_manutenzione": False,
        "note": "Stampo principale per pannelli laterali"
    },
    {
        "codice": "ST-201",
        "descrizione": "Stampo supporto motore",
        "lunghezza_piano": 1500.0,
        "larghezza_piano": 800.0,
        "disponibile": True,
        "in_manutenzione": False,
        "note": "Stampo dedicato per supporti motore"
    },
    {
        "codice": "ST-301",
        "descrizione": "Stampo coperchi e fasce",
        "lunghezza_piano": 1800.0,
        "larghezza_piano": 900.0,
        "disponibile": True,
        "in_manutenzione": False,
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
    "tools": {}
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
        
        # Correzioni specifiche per endpoint
        if endpoint == "cicli-cura":
            # Rimuovi i campi calcolati non presenti nel database
            if "temperatura_max" in data:
                del data["temperatura_max"]
            if "pressione_max" in data:
                del data["pressione_max"]
        
        r = requests.post(endpoint_url, json=data)
        if r.status_code in (200, 201):
            created_data = r.json()
            logger.info(f"[+] {endpoint} creato: {data[unique_field]} (ID: {created_data.get('id', 'N/A')})")
            return created_data
        elif r.status_code in (400, 422):
            error_msg = r.json()
            logger.warning(f"[!] Errore validazione {endpoint}: {error_msg}")
            
            if debug:
                logger.debug(f"Dettagli errore: {json.dumps(error_msg, indent=2)}")
                logger.debug(f"Dati inviati: {json.dumps(data, indent=2)}")
            
            # Tentativi di correzione dei dati
            if endpoint == "autoclavi" and "stato" in data:
                logger.debug(f"Tentativo correzione stato autoclave da {data['stato']} a DISPONIBILE")
                data["stato"] = "DISPONIBILE"
                r = requests.post(endpoint_url, json=data)
                if r.status_code in (200, 201):
                    created_data = r.json()
                    logger.info(f"[+] {endpoint} creato (dopo correzione): {data[unique_field]}")
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
    for parte in modified_parti:
        post_if_missing("parti", "part_number", parte, debug)

def seed_odl(debug: bool = False):
    """Crea ODL di test, associandoli a Parti e Tools esistenti"""
    logger.info("Popolamento ODL...")
    
    # Recupera le parti esistenti
    parti_url = f"{BASE_URL}{API_PREFIX}/parti/"
    try:
        parti_response = requests.get(parti_url)
        if parti_response.status_code != 200 or not parti_response.json():
            logger.error(f"Impossibile recuperare le parti: {parti_response.status_code}")
            return
        
        parti = parti_response.json()
        logger.info(f"Recuperate {len(parti)} parti")
        
        # Recupera i tool esistenti
        tools_url = f"{BASE_URL}{API_PREFIX}/tools/"
        tools_response = requests.get(tools_url)
        if tools_response.status_code != 200 or not tools_response.json():
            logger.error(f"Impossibile recuperare i tools: {tools_response.status_code}")
            return
        
        tools = tools_response.json()
        logger.info(f"Recuperati {len(tools)} tools")
        
        # Creazione di 5 ODL di test con status diversi
        odl_stati = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]
        
        for i in range(min(5, len(parti))):
            # Seleziona una parte e un tool esistenti
            parte = parti[i % len(parti)]
            tool = tools[i % len(tools)]
            
            # Crea l'ODL con priorità variabile e stato diverso
            odl_data = {
                "parte_id": parte["id"],
                "tool_id": tool["id"],
                "priorita": i + 1,
                "status": odl_stati[i % len(odl_stati)],
                "note": f"ODL di test #{i+1} creato automaticamente - {parte['part_number']} con {tool['codice']}"
            }
            
            # Usa una ricerca per verificare se esiste già un ODL simile
            odl_url = f"{BASE_URL}{API_PREFIX}/odl/"
            search_params = {
                "parte_id": odl_data["parte_id"],
                "tool_id": odl_data["tool_id"],
                "status": odl_data["status"]
            }
            
            search_response = requests.get(odl_url, params=search_params)
            if search_response.status_code == 200 and search_response.json():
                logger.info(f"[✔] ODL già presente: Parte {parte['part_number']}, Tool {tool['codice']}, Status {odl_data['status']}")
                continue
            
            # Crea l'ODL se non esiste già
            result = requests.post(odl_url, json=odl_data)
            if result.status_code in [200, 201]:
                logger.info(f"[✓] Creato ODL: Parte {parte['part_number']}, Tool {tool['codice']}, Status {odl_data['status']}")
            else:
                logger.error(f"[✗] Errore nella creazione dell'ODL: {result.status_code}")
                if debug:
                    logger.debug(f"Dettagli errore: {result.text}")
        
        # Verifica se gli ODL sono stati creati
        verify_endpoint("odl", expected_items=1, debug=debug)
        
    except Exception as e:
        logger.error(f"Errore durante il popolamento degli ODL: {str(e)}")

def seed_odl_completati(debug: bool = False):
    """Crea ODL completati con tempi di fase registrati per l'analisi statistica"""
    logger.info("\n📊 Popolamento ODL completati con tempi di fase...")
    
    # Recupera le parti esistenti
    parti_url = f"{BASE_URL}{API_PREFIX}/parti/"
    try:
        parti_response = requests.get(parti_url)
        if parti_response.status_code != 200 or not parti_response.json():
            logger.error(f"Impossibile recuperare le parti: {parti_response.status_code}")
            return
        
        parti = parti_response.json()
        
        # Recupera i tool esistenti
        tools_url = f"{BASE_URL}{API_PREFIX}/tools/"
        tools_response = requests.get(tools_url)
        if tools_response.status_code != 200 or not tools_response.json():
            logger.error(f"Impossibile recuperare i tools: {tools_response.status_code}")
            return
        
        tools = tools_response.json()
        
        # Elenco di durate di fase variabili (in minuti) per ODL completati
        # [laminazione, attesa_cura, cura]
        tempo_fasi_completate = [
            # PN: CPX-101 - Pannello SX
            [120, 45, 65],  # Primo ODL completato
            [130, 40, 70],  # Secondo ODL completato 
            [115, 50, 60],  # Terzo ODL completato
            
            # PN: CPX-201 - Supporto Motore 
            [150, 60, 90],  # Primo ODL completato
            [145, 65, 85],  # Secondo ODL completato
            
            # PN: CPX-401 - Fascia Frontale
            [100, 30, 50],  # Primo ODL completato
            [110, 35, 55],  # Secondo ODL completato
        ]
        
        # Crea ODL completati per diverse parti
        # Configura quali parti utilizzare per gli ODL completati
        parti_odl_completati = [0, 0, 0, 2, 2, 4, 4]  # Indici delle parti in parti[]
        
        for i, idx_parte in enumerate(parti_odl_completati):
            if idx_parte >= len(parti):
                logger.warning(f"Indice parte non valido: {idx_parte}")
                continue
                
            parte = parti[idx_parte]
            tool = tools[idx_parte % len(tools)]
            
            # Verifica se esiste già un ODL simile
            odl_url = f"{BASE_URL}{API_PREFIX}/odl/"
            search_params = {
                "parte_id": parte["id"],
                "tool_id": tool["id"],
                "status": "Finito"
            }
            
            search_response = requests.get(odl_url, params=search_params)
            if search_response.status_code == 200 and len(search_response.json()) > 0:
                logger.info(f"[✔] ODL completato già presente: Parte {parte['part_number']}, Tool {tool['codice']}")
                continue
            
            # Crea l'ODL completato
            odl_data = {
                "parte_id": parte["id"],
                "tool_id": tool["id"],
                "priorita": 1,  # Priorità bassa per ODL completati
                "status": "Finito",
                "note": f"ODL completato di test #{i+1} - {parte['part_number']} con {tool['codice']}"
            }
            
            # Crea l'ODL
            odl_response = requests.post(odl_url, json=odl_data)
            if odl_response.status_code not in [200, 201]:
                logger.error(f"[✗] Errore nella creazione dell'ODL completato: {odl_response.status_code}")
                if debug:
                    logger.debug(f"Dettagli errore: {odl_response.text}")
                continue
            
            odl_creato = odl_response.json()
            odl_id = odl_creato["id"]
            logger.info(f"[✓] Creato ODL completato: ID {odl_id}, Parte {parte['part_number']}, Tool {tool['codice']}")
            
            # Per ogni ODL, crea i tempi delle 3 fasi
            # Calcola le date di inizio/fine progressive partendo da 10 giorni fa
            from datetime import datetime, timedelta
            
            tempo_fasi = ["laminazione", "attesa_cura", "cura"]
            data_fine_corrente = datetime.now() - timedelta(days=1)  # ODL finito ieri
            
            # Inversione dell'ordine: prima cura, poi attesa, poi laminazione
            for j in range(2, -1, -1):
                fase = tempo_fasi[j]
                durata = tempo_fasi_completate[i][j]
                
                # Calcola inizio sottraendo la durata dalla fine
                data_inizio = data_fine_corrente - timedelta(minutes=durata)
                
                # Crea il record del tempo fase
                tempo_fase_data = {
                    "odl_id": odl_id,
                    "fase": fase,
                    "inizio_fase": data_inizio.isoformat(),
                    "fine_fase": data_fine_corrente.isoformat(),
                    "durata_minuti": durata,
                    "note": f"Fase {fase} completata in {durata} minuti"
                }
                
                tempo_fase_url = f"{BASE_URL}{API_PREFIX}/tempo-fasi/"
                tempo_fase_response = requests.post(tempo_fase_url, json=tempo_fase_data)
                
                if tempo_fase_response.status_code in [200, 201]:
                    tempo_fase_id = tempo_fase_response.json()["id"]
                    logger.info(f"  [✓] Creato tempo fase: {fase}, durata {durata} min (ID: {tempo_fase_id})")
                else:
                    logger.error(f"  [✗] Errore nella creazione del tempo fase {fase}: {tempo_fase_response.status_code}")
                    if debug:
                        logger.debug(f"  Dettagli errore: {tempo_fase_response.text}")
                
                # La fine di questa fase diventa l'inizio della fase precedente
                data_fine_corrente = data_inizio
        
        # Crea anche ODL in corso con solo prima/seconda fase
        # Questa volta usando le parti rimanenti
        stati_incompleti = ["Laminazione", "Attesa Cura"]
        fasi_incomplete = ["laminazione", "attesa_cura"]
        parti_odl_incompleti = [1, 3]  # Indici delle parti in parti[]
        
        for i, idx_parte in enumerate(parti_odl_incompleti):
            if idx_parte >= len(parti):
                continue
                
            parte = parti[idx_parte]
            tool = tools[idx_parte % len(tools)]
            
            # Crea l'ODL in stato non completato
            stato_odl = stati_incompleti[i % len(stati_incompleti)]
            
            # Verifica se esiste già un ODL simile
            odl_url = f"{BASE_URL}{API_PREFIX}/odl/"
            search_params = {
                "parte_id": parte["id"],
                "tool_id": tool["id"],
                "status": stato_odl
            }
            
            search_response = requests.get(odl_url, params=search_params)
            if search_response.status_code == 200 and len(search_response.json()) > 0:
                logger.info(f"[✔] ODL incompleto già presente: Parte {parte['part_number']}, Tool {tool['codice']}, Stato {stato_odl}")
                continue
            
            odl_data = {
                "parte_id": parte["id"],
                "tool_id": tool["id"],
                "priorita": 3,  # Priorità media
                "status": stato_odl,
                "note": f"ODL in corso di test - {parte['part_number']} con {tool['codice']}"
            }
            
            odl_response = requests.post(odl_url, json=odl_data)
            if odl_response.status_code not in [200, 201]:
                logger.error(f"[✗] Errore nella creazione dell'ODL incompleto: {odl_response.status_code}")
                continue
            
            odl_creato = odl_response.json()
            odl_id = odl_creato["id"]
            logger.info(f"[✓] Creato ODL incompleto: ID {odl_id}, Parte {parte['part_number']}, Tool {tool['codice']}, Stato {stato_odl}")
            
            # Registra solo le fasi precedenti a quella corrente
            fase_corrente = fasi_incomplete[i % len(fasi_incomplete)]
            fasi_da_registrare = []
            
            if fase_corrente == "attesa_cura":
                fasi_da_registrare.append("laminazione")  # Registra laminazione se siamo in attesa cura
            
            # Aggiungi la fase corrente (senza fine)
            tempo_fase_url = f"{BASE_URL}{API_PREFIX}/tempo-fasi/"
            
            # Prima registra le fasi completate
            for fase in fasi_da_registrare:
                durata = 120  # Durata standard per le fasi completate
                data_fine = datetime.now() - timedelta(hours=2)
                data_inizio = data_fine - timedelta(minutes=durata)
                
                tempo_fase_data = {
                    "odl_id": odl_id,
                    "fase": fase,
                    "inizio_fase": data_inizio.isoformat(),
                    "fine_fase": data_fine.isoformat(),
                    "durata_minuti": durata,
                    "note": f"Fase {fase} completata"
                }
                
                tempo_fase_response = requests.post(tempo_fase_url, json=tempo_fase_data)
                if tempo_fase_response.status_code in [200, 201]:
                    logger.info(f"  [✓] Creato tempo fase completata: {fase}")
                else:
                    logger.error(f"  [✗] Errore nella creazione del tempo fase {fase}: {tempo_fase_response.status_code}")
            
            # Poi registra la fase corrente (senza fine)
            tempo_fase_data = {
                "odl_id": odl_id,
                "fase": fase_corrente,
                "inizio_fase": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "fine_fase": None,
                "durata_minuti": None,
                "note": f"Fase {fase_corrente} in corso"
            }
            
            tempo_fase_response = requests.post(tempo_fase_url, json=tempo_fase_data)
            if tempo_fase_response.status_code in [200, 201]:
                logger.info(f"  [✓] Creato tempo fase in corso: {fase_corrente}")
            else:
                logger.error(f"  [✗] Errore nella creazione del tempo fase {fase_corrente}: {tempo_fase_response.status_code}")
                if debug:
                    logger.debug(f"  Dettagli errore: {tempo_fase_response.text}")
        
    except Exception as e:
        logger.error(f"Errore durante il popolamento degli ODL completati: {str(e)}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())

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
    seed_odl_completati(debug)
    
    # Verifica finale
    logger.info("\n🔍 Verifica endpoint in corso...")
    success = all([
        verify_endpoint("catalogo", len(CATALOGO_PARTS), debug),
        verify_endpoint("tools", len(TOOLS), debug),
        verify_endpoint("cicli-cura", len(CICLI_CURA), debug),
        verify_endpoint("autoclavi", len(AUTOCLAVI), debug),
        verify_endpoint("parti", len(PARTI), debug),
        verify_endpoint("odl", expected_items=1, debug=debug)
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