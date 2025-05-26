#!/usr/bin/env python3
"""
Script di debug locale per CarbonPilot
Fornisce utilities per il debug e il testing locale dell'applicazione
"""

import os
import sys
import logging
import requests
import json
from pathlib import Path

# Setup del path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione URL
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

def check_backend_health():
    """Verifica che il backend sia raggiungibile"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend raggiungibile")
            return True
        else:
            logger.error(f"❌ Backend risponde con status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Backend non raggiungibile: {e}")
        return False

def check_database_connection():
    """Verifica la connessione al database"""
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/catalogo/", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Database connesso")
            return True
        else:
            logger.error(f"❌ Errore database: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Errore connessione database: {e}")
        return False

def list_all_endpoints():
    """Lista tutti gli endpoint disponibili"""
    endpoints = [
        "catalogo",
        "tools", 
        "cicli-cura",
        "autoclavi",
        "parti",
        "odl",
        "nesting",
        "schedule",
        "tempo-fasi"
    ]
    
    logger.info("📋 Verifica endpoint API:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/{endpoint}/", timeout=5)
            count = len(response.json()) if response.status_code == 200 else 0
            status = "✅" if response.status_code == 200 else "❌"
            logger.info(f"{status} {endpoint}: {count} record")
        except Exception as e:
            logger.error(f"❌ {endpoint}: Errore - {e}")

def debug_odl_status():
    """Debug dello stato degli ODL"""
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/odl/", timeout=5)
        if response.status_code == 200:
            odl_list = response.json()
            logger.info(f"📋 ODL totali: {len(odl_list)}")
            
            # Raggruppa per status
            status_count = {}
            for odl in odl_list:
                status = odl.get('status', 'N/A')
                status_count[status] = status_count.get(status, 0) + 1
            
            for status, count in status_count.items():
                logger.info(f"   {status}: {count}")
        else:
            logger.error(f"❌ Errore recupero ODL: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Errore debug ODL: {e}")

def debug_nesting_optimization():
    """Debug dell'ottimizzazione nesting"""
    try:
        # Verifica se ci sono ODL pronti per il nesting
        response = requests.get(f"{BASE_URL}{API_PREFIX}/odl/", timeout=5)
        if response.status_code == 200:
            odl_list = response.json()
            ready_odl = [odl for odl in odl_list if odl.get('status') == 'Attesa Cura']
            logger.info(f"🧩 ODL pronti per nesting: {len(ready_odl)}")
            
            # Verifica autoclavi disponibili
            response = requests.get(f"{BASE_URL}{API_PREFIX}/autoclavi/", timeout=5)
            if response.status_code == 200:
                autoclavi = response.json()
                available = [a for a in autoclavi if a.get('stato') == 'DISPONIBILE']
                logger.info(f"🏭 Autoclavi disponibili: {len(available)}")
        else:
            logger.error(f"❌ Errore debug nesting: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Errore debug nesting: {e}")

def run_full_debug():
    """Esegue un debug completo del sistema"""
    logger.info("🔍 AVVIO DEBUG COMPLETO CARBONPILOT")
    logger.info("=" * 50)
    
    # Verifica connessioni
    if not check_backend_health():
        return False
    
    if not check_database_connection():
        return False
    
    # Verifica endpoint
    list_all_endpoints()
    
    # Debug specifici
    debug_odl_status()
    debug_nesting_optimization()
    
    logger.info("✅ Debug completato")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script di debug locale per CarbonPilot")
    parser.add_argument("--full", action="store_true", help="Esegue debug completo")
    parser.add_argument("--health", action="store_true", help="Verifica solo la salute del backend")
    parser.add_argument("--endpoints", action="store_true", help="Lista tutti gli endpoint")
    parser.add_argument("--odl", action="store_true", help="Debug stato ODL")
    parser.add_argument("--nesting", action="store_true", help="Debug nesting")
    
    args = parser.parse_args()
    
    if args.full:
        run_full_debug()
    elif args.health:
        check_backend_health()
        check_database_connection()
    elif args.endpoints:
        list_all_endpoints()
    elif args.odl:
        debug_odl_status()
    elif args.nesting:
        debug_nesting_optimization()
    else:
        # Default: debug completo
        run_full_debug() 