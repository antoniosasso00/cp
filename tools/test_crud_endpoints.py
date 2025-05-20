# tools/test_crud_endpoints.py

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Setup ambiente
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Endpoints da testare automaticamente - Metto catalogo per primo per garantire che esista
ENDPOINTS = [
    "catalogo",
    "tools",
    "autoclavi",
    "cicli-cura",
    "parte",
]

# Payload di esempio aggiornati
EXAMPLE_PAYLOADS = {
    "catalogo": {
        "part_number": "TEST-CAT-001",
        "descrizione": "Test Catalog Entry",
        "categoria": "Test",
        "attivo": True,
        "note": "Prova CRUD"
    },
    "tools": {
        "codice": "T-001",
        "descrizione": "Tool di test",
        "lunghezza_piano": 100.0,
        "larghezza_piano": 50.0,
        "disponibile": True,
        "in_manutenzione": False,
        "cicli_completati": 0
    },
    "autoclavi": {
        "nome": "Autoclave Test",
        "codice": "AUTO-T-001",
        "lunghezza": 1000.0,
        "larghezza_piano": 500.0,
        "num_linee_vuoto": 4,
        "temperatura_max": 180.0,
        "pressione_max": 7.0,
        "stato": "DISPONIBILE",
        "in_manutenzione": False
    },
    "cicli-cura": {
        "nome": "Ciclo Test",
        "temperatura_max": 180.0,
        "pressione_max": 6.0,
        "temperatura_stasi1": 150.0,
        "pressione_stasi1": 5.0,
        "durata_stasi1": 60,
        "attiva_stasi2": False
    },
    "parte": {
        "part_number": "TEST-CAT-001",
        "descrizione_breve": "Parte test",
        "num_valvole_richieste": 2,
        "tool_ids": []
    },
}

# Dati creati per riferimento
created_entities = {}

async def test_endpoint(endpoint: str):
    url = f"{BACKEND_URL}{API_PREFIX}/{endpoint}/"
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print(f"\n🔄 Testing: {endpoint.upper()}...")

        if endpoint == "parte":
            try:
                catalog_url = f"{BACKEND_URL}{API_PREFIX}/catalogo/TEST-CAT-001"
                r = await client.get(catalog_url)
                if r.status_code != 200:
                    print("Catalogo non trovato, lo creo...")
                    await client.post(f"{BACKEND_URL}{API_PREFIX}/catalogo/", json=EXAMPLE_PAYLOADS["catalogo"])
            except Exception as e:
                print(f"Errore nel controllo del catalogo: {e}")

        payload = EXAMPLE_PAYLOADS.get(endpoint)
        if not payload:
            print(f"⚠️ Nessun payload di esempio per {endpoint}, salto.")
            return

        try:
            r = await client.post(url, json=payload)
            print(f"POST {url} → {r.status_code}")
            if r.status_code not in (200, 201):
                print(f"❌ Errore nella creazione: {r.text}")
                return
            data = r.json()
            entity_id = data.get("id") or data.get("part_number") or data.get("codice")
            
            # Salva l'entità creata per riferimento
            created_entities[endpoint] = data

            # GET all
            r = await client.get(url)
            print(f"GET {url} → {r.status_code} | {len(r.json())} elementi trovati")

            # GET by ID or chiave
            if entity_id:
                get_url = f"{url}{entity_id}"
                r = await client.get(get_url)
                print(f"GET {get_url} → {r.status_code}")

                # DELETE
                delete_url = f"{url}{entity_id}"
                r = await client.delete(delete_url)
                print(f"DELETE {delete_url} → {r.status_code}")
        except Exception as e:
            print(f"❌ Errore durante test {endpoint}: {e}")


async def main():
    for endpoint in ENDPOINTS:
        await test_endpoint(endpoint)
    
    print("\n✅ Test completati!")
    
    if "catalogo" in created_entities:
        print(f"🗑️ Pulizia: rimuovo il catalogo di test {created_entities['catalogo']['part_number']}")
        
        # Assicuriamo che il catalogo venga eliminato alla fine
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{BACKEND_URL}{API_PREFIX}/catalogo/{created_entities['catalogo']['part_number']}")
        except Exception as e:
            print(f"Errore nella pulizia finale: {e}")

if __name__ == "__main__":
    asyncio.run(main())
