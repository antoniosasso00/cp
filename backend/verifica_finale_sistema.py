#!/usr/bin/env python3
"""
Verifica finale del sistema CarbonPilot
Controlla che tutto sia pronto per la demo del monitoraggio ODL
"""

import logging
import requests
import time
from pathlib import Path

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VerificaFinale:
    """Verifica finale del sistema completo"""
    
    def __init__(self):
        self.backend_url = 'http://localhost:8000'
        self.frontend_url = 'http://localhost:3000'
        self.monitoring_url = f'{self.backend_url}/api/v1/odl-monitoring/monitoring'
    
    def verifica_file_essenziali(self):
        """Verifica che tutti i file essenziali esistano"""
        logger.info("🔍 Verifica file essenziali...")
        
        file_essenziali = [
            # Backend (percorsi relativi dalla directory backend)
            'main.py',
            'api/routers/odl_monitoring.py',
            'services/odl_monitoring_service.py',
            'models/odl.py',
            'models/odl_log.py',
            'carbonpilot.db',
            
            # Frontend (percorsi relativi dalla root del progetto)
            '../frontend/src/components/odl-monitoring/ODLMonitoringDashboard.tsx',
            '../frontend/src/components/odl-monitoring/ODLMonitoringDetail.tsx',
            '../frontend/src/app/dashboard/odl/monitoring/page.tsx',
            '../frontend/package.json',
            
            # Documentazione (percorsi relativi dalla root del progetto)
            '../docs/MONITORAGGIO_ODL_COMPLETATO.md',
            '../docs/changelog.md'
        ]
        
        missing_files = []
        for file_path in file_essenziali:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ File mancanti: {missing_files}")
            return False
        
        logger.info("✅ Tutti i file essenziali presenti")
        return True
    
    def verifica_backend_attivo(self):
        """Verifica che il backend sia attivo e risponda"""
        logger.info("🔍 Verifica backend attivo...")
        
        try:
            response = requests.get(f'{self.backend_url}/docs', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend attivo e raggiungibile")
                return True
            else:
                logger.error(f"❌ Backend risponde con status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Backend non raggiungibile. Avvia con: cd backend && python main.py")
            return False
        except Exception as e:
            logger.error(f"❌ Errore verifica backend: {e}")
            return False
    
    def verifica_api_monitoraggio(self):
        """Verifica che le API di monitoraggio funzionino"""
        logger.info("🔍 Verifica API monitoraggio...")
        
        endpoints_test = [
            ('/stats', 'Statistiche'),
            ('?limit=5', 'Lista ODL'),
        ]
        
        for endpoint, descrizione in endpoints_test:
            try:
                response = requests.get(f'{self.monitoring_url}{endpoint}', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ {descrizione}: OK")
                else:
                    logger.error(f"❌ {descrizione}: Status {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"❌ {descrizione}: Errore {e}")
                return False
        
        logger.info("✅ Tutte le API di monitoraggio funzionanti")
        return True
    
    def verifica_dati_demo(self):
        """Verifica che ci siano dati di demo sufficienti"""
        logger.info("🔍 Verifica dati demo...")
        
        try:
            # Verifica statistiche
            response = requests.get(f'{self.monitoring_url}/stats', timeout=10)
            if response.status_code != 200:
                logger.error("❌ Impossibile ottenere statistiche")
                return False
            
            stats = response.json()
            totale_odl = stats.get('totale_odl', 0)
            
            if totale_odl < 5:
                logger.warning(f"⚠️ Solo {totale_odl} ODL presenti. Raccomandati almeno 5 per demo")
                return False
            
            # Verifica lista ODL
            response = requests.get(f'{self.monitoring_url}?limit=10', timeout=10)
            if response.status_code != 200:
                logger.error("❌ Impossibile ottenere lista ODL")
                return False
            
            odl_list = response.json()
            stati_presenti = set(odl['status'] for odl in odl_list)
            
            logger.info(f"✅ {totale_odl} ODL presenti con stati: {', '.join(stati_presenti)}")
            
            if len(stati_presenti) < 3:
                logger.warning("⚠️ Pochi stati diversi. Raccomandati almeno 3 stati per demo completa")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore verifica dati demo: {e}")
            return False
    
    def run_verifica_completa(self):
        """Esegue la verifica completa del sistema"""
        logger.info("🚀 VERIFICA FINALE SISTEMA CARBONPILOT")
        logger.info("=" * 60)
        
        verifiche = [
            ("File Essenziali", self.verifica_file_essenziali),
            ("Backend Attivo", self.verifica_backend_attivo),
            ("API Monitoraggio", self.verifica_api_monitoraggio),
            ("Dati Demo", self.verifica_dati_demo)
        ]
        
        risultati = []
        
        for nome_verifica, func_verifica in verifiche:
            logger.info(f"\n📋 {nome_verifica}...")
            try:
                risultato = func_verifica()
                risultati.append((nome_verifica, risultato))
                if risultato:
                    logger.info(f"✅ {nome_verifica}: PASS")
                else:
                    logger.error(f"❌ {nome_verifica}: FAIL")
            except Exception as e:
                logger.error(f"💥 {nome_verifica}: ERRORE - {e}")
                risultati.append((nome_verifica, False))
        
        # Riepilogo finale
        logger.info("\n" + "=" * 60)
        logger.info("📊 RIEPILOGO VERIFICA FINALE:")
        
        successi = sum(1 for _, risultato in risultati if risultato)
        totali = len(risultati)
        
        for nome, risultato in risultati:
            status = "✅ PASS" if risultato else "❌ FAIL"
            logger.info(f"  {status} - {nome}")
        
        logger.info(f"\n🎯 RISULTATO: {successi}/{totali} verifiche superate")
        
        if successi == totali:
            logger.info("\n🎉 SISTEMA COMPLETAMENTE PRONTO PER LA DEMO!")
            logger.info("🌟 ISTRUZIONI PER LA DEMO:")
            logger.info("  1. 🌐 Apri: http://localhost:3000/dashboard/odl/monitoring")
            logger.info("  2. 👤 Seleziona ruolo: ADMIN o RESPONSABILE")
            logger.info("  3. 🎯 Testa le funzionalità:")
            logger.info("     - Visualizza statistiche in tempo reale")
            logger.info("     - Filtra ODL per stato e priorità")
            logger.info("     - Clicca 'Dettagli' su un ODL per vista completa")
            logger.info("     - Esplora timeline eventi e log dettagliati")
            logger.info("     - Verifica alert automatici per ODL in ritardo")
            logger.info("  4. 🔧 API disponibili:")
            logger.info("     - http://localhost:8000/docs (Swagger UI)")
            logger.info("     - http://localhost:8000/api/v1/odl-monitoring/monitoring/stats")
            logger.info("\n🚀 BUONA DEMO!")
        else:
            logger.warning(f"\n⚠️ {totali - successi} verifiche fallite.")
            logger.warning("Risolvi i problemi sopra prima della demo.")
        
        return successi == totali

def main():
    """Funzione principale"""
    verifica = VerificaFinale()
    
    # Aspetta un momento per essere sicuri che i servizi siano pronti
    logger.info("⏳ Attendo che i servizi siano pronti...")
    time.sleep(2)
    
    success = verifica.run_verifica_completa()
    
    if not success:
        logger.error("\n💡 SUGGERIMENTI PER RISOLVERE I PROBLEMI:")
        logger.error("  1. Assicurati che il backend sia avviato: cd backend && python main.py")
        logger.error("  2. Assicurati che il frontend sia avviato: cd frontend && npm run dev")
        logger.error("  3. Verifica che non ci siano errori nei log dei servizi")
        logger.error("  4. Controlla che le porte 8000 e 3000 siano libere")

if __name__ == "__main__":
    main() 