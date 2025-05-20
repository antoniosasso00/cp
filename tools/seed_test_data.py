#!/usr/bin/env python
"""
Script per il seed dei dati di test nel database CarbonPilot.
Questo script è idempotente: crea i dati solo se non esistono già.
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

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
                print(f"[✔] {endpoint} già presente: {data[unique_field]}")
                return
        
        # Se non esiste, crea il record
        r = requests.post(f"{BASE_URL}{API_PREFIX}/{endpoint}/", json=data)
        if r.status_code in (200, 201):
            print(f"[+] {endpoint} creato: {data[unique_field]}")
        else:
            print(f"[!] Errore creazione {endpoint}: {r.text}")
    except Exception as e:
        print(f"[!] Errore su {endpoint}: {e}")

def main():
    """Funzione principale per il seed dei dati di test."""
    print("\n🌱 Seed dati di test in corso...")
    
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
        "in_manutenzione": False,
        "cicli_completati": 0
    })
    
    # 3. Ciclo Cura
    post_if_missing("cicli-cura", "nome", {
        "nome": "CURA-TEST",
        "temperatura_max": 180,
        "pressione_max": 5.5,
        "temperatura_stasi1": 120,
        "pressione_stasi1": 4.0,
        "durata_stasi1": 60,
        "attiva_stasi2": False
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
    
    print("\n✨ Seed completato!")

if __name__ == "__main__":
    main() 