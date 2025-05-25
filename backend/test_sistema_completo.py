#!/usr/bin/env python3
"""
Test completo del sistema di monitoraggio ODL
Verifica database, API e genera dati di test per la demo
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from models.db import get_db
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.odl_log import ODLLog
from services.odl_log_service import ODLLogService
from sqlalchemy.orm import joinedload

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSistemaCompleto:
    """Test completo del sistema di monitoraggio ODL"""
    
    def __init__(self):
        self.base_url = 'http://localhost:8000/api/v1/odl-monitoring/monitoring'
        self.db = next(get_db())
    
    def test_database_integrity(self):
        """Test 1: Verifica integrità database"""
        logger.info("🔍 Test 1: Verifica integrità database...")
        
        try:
            # Conta entità principali
            odl_count = self.db.query(ODL).count()
            parti_count = self.db.query(Parte).count()
            tools_count = self.db.query(Tool).count()
            logs_count = self.db.query(ODLLog).count()
            
            logger.info(f"  📊 ODL: {odl_count}")
            logger.info(f"  📦 Parti: {parti_count}")
            logger.info(f"  🔧 Tools: {tools_count}")
            logger.info(f"  📝 Logs: {logs_count}")
            
            # Verifica relazioni
            odl_con_relazioni = self.db.query(ODL).options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            ).first()
            
            if odl_con_relazioni:
                logger.info(f"  ✅ Relazioni ODL funzionanti: {odl_con_relazioni.parte.descrizione_breve} + {odl_con_relazioni.tool.part_number_tool}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Errore database: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test 2: Verifica tutti gli endpoint API"""
        logger.info("🔍 Test 2: Verifica endpoint API...")
        
        try:
            # Test statistiche
            response = requests.get(f'{self.base_url}/stats', timeout=10)
            if response.status_code != 200:
                logger.error(f"  ❌ Errore statistiche: {response.status_code}")
                return False
            
            stats = response.json()
            logger.info(f"  ✅ Statistiche: {stats['totale_odl']} ODL totali")
            
            # Test lista ODL
            response = requests.get(f'{self.base_url}?limit=5', timeout=10)
            if response.status_code != 200:
                logger.error(f"  ❌ Errore lista: {response.status_code}")
                return False
            
            odl_list = response.json()
            logger.info(f"  ✅ Lista: {len(odl_list)} ODL ricevuti")
            
            # Test dettaglio ODL
            if odl_list:
                first_odl_id = odl_list[0]['id']
                response = requests.get(f'{self.base_url}/{first_odl_id}', timeout=10)
                if response.status_code != 200:
                    logger.error(f"  ❌ Errore dettaglio: {response.status_code}")
                    return False
                
                detail = response.json()
                logger.info(f"  ✅ Dettaglio ODL {first_odl_id}: {len(detail.get('logs', []))} logs")
            
            # Test timeline
            if odl_list:
                response = requests.get(f'{self.base_url}/{first_odl_id}/timeline', timeout=10)
                if response.status_code != 200:
                    logger.error(f"  ❌ Errore timeline: {response.status_code}")
                    return False
                
                timeline = response.json()
                logger.info(f"  ✅ Timeline: {len(timeline.get('timeline', []))} eventi")
            
            return True
            
        except requests.exceptions.ConnectionError:
            logger.error("  ❌ Server non raggiungibile. Avvia con: python main.py")
            return False
        except Exception as e:
            logger.error(f"  ❌ Errore API: {e}")
            return False
    
    def genera_dati_demo(self):
        """Test 3: Genera dati di demo per test completi"""
        logger.info("🔍 Test 3: Generazione dati demo...")
        
        try:
            # Trova ODL esistenti
            odl_list = self.db.query(ODL).limit(5).all()
            
            if not odl_list:
                logger.warning("  ⚠️ Nessun ODL trovato per generare demo")
                return True
            
            # Genera log aggiuntivi per simulare avanzamento
            for i, odl in enumerate(odl_list[:3]):
                # Simula diversi stati per demo
                stati_demo = [
                    ("Preparazione", "Laminazione", "Avvio laminazione"),
                    ("Laminazione", "Attesa Cura", "Laminazione completata"),
                    ("Attesa Cura", "Cura", "Caricamento in autoclave")
                ]
                
                if i < len(stati_demo):
                    stato_prec, stato_nuovo, descrizione = stati_demo[i]
                    
                    # Crea log di avanzamento
                    ODLLogService.crea_log_evento(
                        db=self.db,
                        odl_id=odl.id,
                        evento="avanzamento_stato",
                        stato_nuovo=stato_nuovo,
                        stato_precedente=stato_prec,
                        descrizione=descrizione,
                        responsabile="Sistema Demo"
                    )
                    
                    # Aggiorna stato ODL
                    odl.status = stato_nuovo
                    odl.updated_at = datetime.now()
                    
                    logger.info(f"  ✅ ODL {odl.id}: {stato_prec} → {stato_nuovo}")
            
            self.db.commit()
            logger.info("  ✅ Dati demo generati con successo")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Errore generazione demo: {e}")
            self.db.rollback()
            return False
    
    def test_scenari_avanzati(self):
        """Test 4: Scenari avanzati di monitoraggio"""
        logger.info("🔍 Test 4: Scenari avanzati...")
        
        try:
            # Test filtri API
            response = requests.get(f'{self.base_url}?status_filter=Cura&limit=10', timeout=10)
            if response.status_code == 200:
                filtered_list = response.json()
                logger.info(f"  ✅ Filtro per stato 'Cura': {len(filtered_list)} ODL")
            
            # Test priorità
            response = requests.get(f'{self.base_url}?priorita_min=3&limit=10', timeout=10)
            if response.status_code == 200:
                priority_list = response.json()
                logger.info(f"  ✅ Filtro priorità ≥3: {len(priority_list)} ODL")
            
            # Test solo attivi
            response = requests.get(f'{self.base_url}?solo_attivi=false&limit=20', timeout=10)
            if response.status_code == 200:
                all_list = response.json()
                logger.info(f"  ✅ Tutti gli ODL (inclusi finiti): {len(all_list)} ODL")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Errore scenari avanzati: {e}")
            return False
    
    def test_performance(self):
        """Test 5: Performance e tempi di risposta"""
        logger.info("🔍 Test 5: Performance...")
        
        try:
            # Test tempo risposta statistiche
            start_time = time.time()
            response = requests.get(f'{self.base_url}/stats', timeout=10)
            stats_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"  ✅ Statistiche: {stats_time:.2f}s")
            
            # Test tempo risposta lista
            start_time = time.time()
            response = requests.get(f'{self.base_url}?limit=50', timeout=10)
            list_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"  ✅ Lista 50 ODL: {list_time:.2f}s")
            
            # Test tempo risposta dettaglio
            if response.status_code == 200:
                odl_list = response.json()
                if odl_list:
                    start_time = time.time()
                    detail_response = requests.get(f'{self.base_url}/{odl_list[0]["id"]}', timeout=10)
                    detail_time = time.time() - start_time
                    
                    if detail_response.status_code == 200:
                        logger.info(f"  ✅ Dettaglio ODL: {detail_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Errore test performance: {e}")
            return False
    
    def run_all_tests(self):
        """Esegue tutti i test in sequenza"""
        logger.info("🚀 AVVIO TEST COMPLETO SISTEMA MONITORAGGIO ODL")
        logger.info("=" * 60)
        
        tests = [
            ("Database Integrity", self.test_database_integrity),
            ("API Endpoints", self.test_api_endpoints),
            ("Dati Demo", self.genera_dati_demo),
            ("Scenari Avanzati", self.test_scenari_avanzati),
            ("Performance", self.test_performance)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    logger.info(f"✅ {test_name}: SUCCESSO")
                else:
                    logger.error(f"❌ {test_name}: FALLITO")
            except Exception as e:
                logger.error(f"💥 {test_name}: ERRORE - {e}")
                results.append((test_name, False))
        
        # Riepilogo finale
        logger.info("\n" + "=" * 60)
        logger.info("📊 RIEPILOGO TEST:")
        
        successi = sum(1 for _, result in results if result)
        totali = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} - {test_name}")
        
        logger.info(f"\n🎯 RISULTATO FINALE: {successi}/{totali} test superati")
        
        if successi == totali:
            logger.info("🎉 SISTEMA MONITORAGGIO ODL COMPLETAMENTE FUNZIONANTE!")
            logger.info("🌐 Accedi a: http://localhost:3000/dashboard/odl/monitoring")
        else:
            logger.warning(f"⚠️ {totali - successi} test falliti. Controlla i log sopra.")
        
        return successi == totali

def main():
    """Funzione principale"""
    tester = TestSistemaCompleto()
    
    # Aspetta che il server sia pronto
    logger.info("⏳ Attendo che il server sia pronto...")
    time.sleep(2)
    
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n🚀 SISTEMA PRONTO PER LA DEMO!")
        logger.info("📋 Cosa puoi testare:")
        logger.info("  1. Dashboard monitoraggio: http://localhost:3000/dashboard/odl/monitoring")
        logger.info("  2. API statistiche: http://localhost:8000/api/v1/odl-monitoring/monitoring/stats")
        logger.info("  3. Lista ODL: http://localhost:8000/api/v1/odl-monitoring/monitoring")
        logger.info("  4. Dettaglio ODL: http://localhost:8000/api/v1/odl-monitoring/monitoring/1")
    else:
        logger.error("💥 SISTEMA NON PRONTO - Controlla gli errori sopra")

if __name__ == "__main__":
    main() 