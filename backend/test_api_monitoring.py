#!/usr/bin/env python3
"""
Test delle API di monitoraggio ODL
"""

import requests
import json
import time
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_monitoring_apis():
    """Test delle API di monitoraggio ODL"""
    
    base_url = 'http://localhost:8000/api/v1/odl-monitoring/monitoring'
    
    try:
        # Aspetta che il server si avvii
        logger.info("⏳ Attendo avvio server...")
        time.sleep(3)
        
        # Test 1: Statistiche
        logger.info("🔍 Test statistiche...")
        response = requests.get(f'{base_url}/stats', timeout=10)
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"✅ Statistiche ricevute:")
            logger.info(f"  - Totale ODL: {stats.get('totale_odl', 0)}")
            logger.info(f"  - In ritardo: {stats.get('in_ritardo', 0)}")
            logger.info(f"  - Completati oggi: {stats.get('completati_oggi', 0)}")
            logger.info(f"  - Per stato: {stats.get('per_stato', {})}")
        else:
            logger.error(f"❌ Errore statistiche: {response.status_code} - {response.text}")
            return False
        
        # Test 2: Lista ODL
        logger.info("🔍 Test lista ODL...")
        response = requests.get(f'{base_url}?limit=3', timeout=10)
        if response.status_code == 200:
            odl_list = response.json()
            logger.info(f"✅ Lista ODL ricevuta ({len(odl_list)} elementi)")
            for odl in odl_list[:2]:
                logger.info(f"  - ODL {odl['id']}: {odl['status']} - {odl['parte_nome']}")
        else:
            logger.error(f"❌ Errore lista: {response.status_code} - {response.text}")
            return False
        
        # Test 3: Dettaglio ODL specifico
        if odl_list:
            first_odl_id = odl_list[0]['id']
            logger.info(f"🔍 Test dettaglio ODL {first_odl_id}...")
            response = requests.get(f'{base_url}/{first_odl_id}', timeout=10)
            if response.status_code == 200:
                odl_detail = response.json()
                logger.info(f"✅ Dettaglio ODL {first_odl_id} ricevuto")
                logger.info(f"  - Parte: {odl_detail.get('parte_nome')}")
                logger.info(f"  - Tool: {odl_detail.get('tool_nome')}")
                logger.info(f"  - Logs: {len(odl_detail.get('logs', []))}")
            else:
                logger.error(f"❌ Errore dettaglio: {response.status_code} - {response.text}")
                return False
        
        logger.info("✅ Tutti i test API completati con successo!")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Impossibile connettersi al server. Assicurati che sia avviato con: python main.py")
        return False
    except Exception as e:
        logger.error(f"❌ Errore durante i test: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Avvio test API monitoraggio ODL...")
    success = test_monitoring_apis()
    
    if success:
        logger.info("🎉 Test completati con successo!")
    else:
        logger.error("💥 Test falliti!") 