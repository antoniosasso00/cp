#!/usr/bin/env python3
"""
CarbonPilot - Complete Nesting Seed v2.0.0-EXPANDED
Script unificato per creare dati di test completi per l'algoritmo di nesting.

REQUISITI v2.0.0:
- 30 ODL (invece di 20)
- 3 cicli di cura (Aeronautico, Automotive, Marine)
- 3 autoclavi (Large, Medium, Compact) 
- Tools diversificati con dimensioni e materiali varie

Integra e migliora i precedenti script di seed.
Utilizza la configurazione database corretta del backend.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from models.db import SessionLocal, Base, engine, test_database_connection
    from models.autoclave import Autoclave, StatoAutoclaveEnum
    from models.catalogo import Catalogo
    from models.ciclo_cura import CicloCura
    from models.parte import Parte
    from models.tool import Tool
    from models.odl import ODL
    from models.batch_nesting import BatchNesting
    # 🔧 IMPORTA TUTTI I MODELLI per assicurarsi che le tabelle vengano create
    from models.nesting_result import NestingResult
    from models.report import Report
    from models.schedule_entry import ScheduleEntry
    from models.state_log import StateLog
    from models.system_log import SystemLog
    from models.tempo_fase import TempoFase
    from models.tempo_produzione import TempoProduzione
    from models.standard_time import StandardTime
    from models.odl_log import ODLLog
    from models.batch_history import BatchHistory
    import random
except ImportError as e:
    print(f"❌ Errore import: {e}")
    print("Assicurati di essere nell'ambiente virtuale corretto e che il backend sia configurato")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteNestingSeed:
    """Classe per creare un set completo di dati per il testing del nesting v2.0.0"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.scenarios_created = []
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
            logger.error(f"❌ Errore durante il seeding: {exc_val}")
        self.db.close()
    
    def cleanup_existing_test_data(self):
        """Pulisce tutti i dati di test esistenti per evitare conflitti"""
        logger.info("🧹 Pulizia dati test esistenti...")
        
        try:
            # 🔧 PRIMA: Crea le tabelle se non esistono
            logger.info("📋 Creazione tabelle database...")
            Base.metadata.create_all(bind=engine)
            
            # 🔧 Verifica se ci sono dati da pulire
            try:
                # Test se le tabelle esistono e hanno dati
                batch_count = self.db.query(BatchNesting).count()
                odl_count = self.db.query(ODL).count()
                tool_count = self.db.query(Tool).count()
                
                if batch_count == 0 and odl_count == 0 and tool_count == 0:
                    logger.info("ℹ️ Database vuoto, nessuna pulizia necessaria")
                    return
                    
                logger.info(f"📊 Dati esistenti: {batch_count} batch, {odl_count} ODL, {tool_count} tools")
                
                # Elimina tutti i dati esistenti per ricominciare da zero
                logger.info("🗑️ Eliminazione completa dati esistenti...")
                
                # Elimina in ordine per rispettare i constraint
                self.db.query(BatchNesting).delete()
                self.db.query(ODL).delete()
                self.db.query(Tool).delete()
                self.db.query(Parte).delete()
                self.db.query(Catalogo).delete()
                self.db.query(Autoclave).delete()
                self.db.query(CicloCura).delete()
                
                self.db.commit()
                logger.info("✅ Pulizia completa completata")
                
            except Exception as e:
                logger.info(f"ℹ️ Errore durante pulizia (probabilmente database vuoto): {str(e)}")
                self.db.rollback()
                
        except Exception as e:
            logger.error(f"💥 Errore durante pulizia: {str(e)}")
            self.db.rollback()
            raise

    def create_autoclaves(self) -> List[Autoclave]:
        """Crea 3 autoclavi diverse per testing"""
        logger.info("🏭 Creazione 3 autoclavi diverse...")
        
        autoclavi_configs = [
            {
                "nome": "NestingTest-Large-v2.0.0",
                "codice": "NEST-LARGE-001", 
                "produttore": "TestCorp Aerospace",
                "larghezza": 1500.0,  # Grande
                "lunghezza": 2500.0,
                "temp_max": 220.0,
                "press_max": 10.0,
                "max_load": 800.0,
                "linee_vuoto": 12,
                "note": "Autoclave grande per test nesting v2.0.0"
            },
            {
                "nome": "NestingTest-Medium-v2.0.0", 
                "codice": "NEST-MEDIUM-002",
                "produttore": "TestCorp Industrial",
                "larghezza": 1200.0,  # Media 
                "lunghezza": 2000.0,
                "temp_max": 200.0,
                "press_max": 8.0,
                "max_load": 500.0,
                "linee_vuoto": 8,
                "note": "Autoclave media per test nesting v2.0.0"
            },
            {
                "nome": "NestingTest-Compact-v2.0.0",
                "codice": "NEST-COMPACT-003",
                "produttore": "TestCorp Precision", 
                "larghezza": 800.0,   # Compatta
                "lunghezza": 1500.0,
                "temp_max": 180.0,
                "press_max": 6.0,
                "max_load": 300.0,
                "linee_vuoto": 6,
                "note": "Autoclave compatta per test nesting v2.0.0"
            }
        ]
        
        autoclavi_create = []
        for config in autoclavi_configs:
            autoclave = Autoclave(
                nome=config["nome"],
                codice=config["codice"], 
                produttore=config["produttore"],
                anno_produzione=2024,
                larghezza_piano=config["larghezza"],
                lunghezza=config["lunghezza"],
                temperatura_max=config["temp_max"],
                pressione_max=config["press_max"],
                max_load_kg=config["max_load"],
                num_linee_vuoto=config["linee_vuoto"],
                stato=StatoAutoclaveEnum.DISPONIBILE,
                note=config["note"]
            )
            self.db.add(autoclave)
            autoclavi_create.append(autoclave)
        
        self.db.flush()
        
        logger.info(f"✅ Create 3 autoclavi:")
        for auto in autoclavi_create:
            logger.info(f"   🏭 {auto.nome} ({auto.larghezza_piano}x{auto.lunghezza}mm, {auto.num_linee_vuoto} linee)")
        
        return autoclavi_create

    def create_cure_cycles(self) -> List[CicloCura]:
        """Crea 3 cicli di cura diversi"""
        logger.info("🔄 Creazione 3 cicli di cura...")
        
        cicli_configs = [
            {
                "nome": "Aeronautico-Standard-v2.0.0",
                "descrizione": "Ciclo standard per componenti aeronautici",
                "temp_stasi1": 180.0,
                "press_stasi1": 6.0,
                "durata_stasi1": 120,
                "attiva_stasi2": False
            },
            {
                "nome": "Automotive-Heavy-v2.0.0", 
                "descrizione": "Ciclo rinforzato per automotive pesante",
                "temp_stasi1": 200.0,
                "press_stasi1": 8.0,
                "durata_stasi1": 90,
                "attiva_stasi2": True,
                "temp_stasi2": 220.0,
                "press_stasi2": 10.0,
                "durata_stasi2": 60
            },
            {
                "nome": "Marine-Precision-v2.0.0",
                "descrizione": "Ciclo precisione per componenti marini",
                "temp_stasi1": 160.0,
                "press_stasi1": 5.0,
                "durata_stasi1": 150,
                "attiva_stasi2": False
            }
        ]
        
        cicli_create = []
        for config in cicli_configs:
            ciclo = CicloCura(
                nome=config["nome"],
                descrizione=config["descrizione"],
                temperatura_stasi1=config["temp_stasi1"],
                pressione_stasi1=config["press_stasi1"],
                durata_stasi1=config["durata_stasi1"],
                attiva_stasi2=config.get("attiva_stasi2", False)
            )
            
            if config.get("attiva_stasi2"):
                ciclo.temperatura_stasi2 = config.get("temp_stasi2")
                ciclo.pressione_stasi2 = config.get("press_stasi2")
                ciclo.durata_stasi2 = config.get("durata_stasi2")
            
            self.db.add(ciclo)
            cicli_create.append(ciclo)
        
        self.db.flush()
        
        logger.info(f"✅ Creati 3 cicli di cura:")
        for ciclo in cicli_create:
            logger.info(f"   🔄 {ciclo.nome} ({ciclo.temperatura_stasi1}°C, {ciclo.durata_stasi1}min)")
        
        return cicli_create

    def create_comprehensive_scenario(self, autoclavi: List[Autoclave], cicli: List[CicloCura]) -> Dict[str, Any]:
        """
        Crea scenario completo con 30 ODL, tools diversificati, 3 autoclavi e 3 cicli
        """
        logger.info("🚀 Creazione scenario completo: 30 ODL con varietà massima")
        
        # 1. Crea catalogo part numbers diversificati (30 categorie)
        part_numbers = [
            # STRUTTURALI (12)
            ("STRUCT-WING-BRACKET-L", "Supporto ala sinistra", "Strutturale", "Brackets"),
            ("STRUCT-WING-BRACKET-R", "Supporto ala destra", "Strutturale", "Brackets"), 
            ("STRUCT-ENGINE-MOUNT-F", "Attacco motore frontale", "Strutturale", "Mounts"),
            ("STRUCT-ENGINE-MOUNT-R", "Attacco motore posteriore", "Strutturale", "Mounts"),
            ("STRUCT-LANDING-MAIN", "Carrello principale", "Strutturale", "Landing"),
            ("STRUCT-LANDING-NOSE", "Carrello di prua", "Strutturale", "Landing"),
            ("STRUCT-FUSELAGE-F", "Struttura fusoliera frontale", "Strutturale", "Fuselage"),
            ("STRUCT-FUSELAGE-R", "Struttura fusoliera posteriore", "Strutturale", "Fuselage"),
            ("STRUCT-TAIL-VERTICAL", "Struttura timone verticale", "Strutturale", "Empennage"),
            ("STRUCT-TAIL-HORIZONTAL", "Struttura timone orizzontale", "Strutturale", "Empennage"),
            ("STRUCT-WING-SPAR-L", "Longherone ala sinistra", "Strutturale", "Spars"),
            ("STRUCT-WING-SPAR-R", "Longherone ala destra", "Strutturale", "Spars"),
            
            # PROPULSIONE (6)
            ("ENGINE-INLET-DUCT", "Condotto aspirazione motore", "Propulsione", "Ducts"),
            ("ENGINE-EXHAUST-NOZZLE", "Ugello scarico motore", "Propulsione", "Nozzles"),
            ("ENGINE-FAN-BLADE", "Pala ventola motore", "Propulsione", "Blades"),
            ("ENGINE-COMPRESSOR", "Compressore motore", "Propulsione", "Compressors"),
            ("ENGINE-TURBINE-DISK", "Disco turbina", "Propulsione", "Turbines"),
            ("ENGINE-COMBUSTION-CHAMBER", "Camera combustione", "Propulsione", "Chambers"),
            
            # CONTROLLI (6)
            ("CONTROL-AILERON-L", "Alettone sinistro", "Controlli", "Primary"),
            ("CONTROL-AILERON-R", "Alettone destro", "Controlli", "Primary"),
            ("CONTROL-RUDDER", "Timone di direzione", "Controlli", "Primary"),
            ("CONTROL-ELEVATOR", "Timone di profondità", "Controlli", "Primary"),
            ("CONTROL-TRIM-TAB", "Aletta compensatrice", "Controlli", "Secondary"),
            ("CONTROL-FLAP-MAIN", "Flap principale", "Controlli", "Secondary"),
            
            # ELETTRONICA (6)
            ("ELEC-AVIONICS-NAV", "Sistema navigazione", "Elettronica", "Navigation"),
            ("ELEC-AVIONICS-COM", "Sistema comunicazioni", "Elettronica", "Communication"),
            ("ELEC-FLIGHT-CONTROL", "Controllo di volo", "Elettronica", "Flight"),
            ("ELEC-ENGINE-CONTROL", "Controllo motore", "Elettronica", "Engine"),
            ("ELEC-POWER-DIST", "Distribuzione energia", "Elettronica", "Power"),
            ("ELEC-WEATHER-RADAR", "Radar meteorologico", "Elettronica", "Sensors")
        ]
        
        # Crea catalogo
        for part_num, desc, cat, subcat in part_numbers:
            catalogo = Catalogo(
                part_number=part_num,
                descrizione=desc,
                categoria=cat,
                sotto_categoria=subcat,
                attivo=True
            )
            self.db.add(catalogo)
        
        # 2. Crea parti associate ai cicli (distribuiti tra i 3 cicli)
        parti_configs = []
        
        # Distribuisci parti tra i 3 cicli
        aeronautic_parts = part_numbers[:12]  # Prime 12 parti → ciclo aeronautico
        automotive_parts = part_numbers[12:24] # Parti 13-24 → ciclo automotive
        marine_parts = part_numbers[24:]       # Ultime 6 parti → ciclo marine
        
        # Parti aeronautiche (valvole 1-3)
        for part_num, desc, _, _ in aeronautic_parts:
            valvole = random.randint(1, 3)
            parti_configs.append((part_num, f"{desc} - produzione aeronautica", valvole, cicli[0].id))
        
        # Parti automotive (valvole 2-4)
        for part_num, desc, _, _ in automotive_parts:
            valvole = random.randint(2, 4)
            parti_configs.append((part_num, f"{desc} - produzione automotive", valvole, cicli[1].id))
        
        # Parti marine (valvole 1-2)
        for part_num, desc, _, _ in marine_parts:
            valvole = random.randint(1, 2)
            parti_configs.append((part_num, f"{desc} - produzione marine", valvole, cicli[2].id))
        
        parti_create = []
        for part_num, desc_breve, valvole, ciclo_id in parti_configs:
            parte = Parte(
                part_number=part_num,
                descrizione_breve=desc_breve,
                ciclo_cura_id=ciclo_id,
                num_valvole_richieste=valvole,
                note_produzione=f"Test nesting v2.0.0 - {valvole} linee vuoto"
            )
            self.db.add(parte)
            parti_create.append(parte)
        
        self.db.flush()
        
        # 3. Crea tools con dimensioni molto diversificate (30 tools unici)
        tool_configs = [
            # STRUTTURALI - Tools grandi e pesanti
            ("STRUCT-WING-BRACKET-L", 400, 350, 28.0, "Acciaio Inox"),
            ("STRUCT-WING-BRACKET-R", 400, 350, 28.0, "Acciaio Inox"),
            ("STRUCT-ENGINE-MOUNT-F", 500, 400, 45.0, "Acciaio Maraging"),
            ("STRUCT-ENGINE-MOUNT-R", 500, 400, 45.0, "Acciaio Maraging"),
            ("STRUCT-LANDING-MAIN", 600, 450, 65.0, "Acciaio Inox"),
            ("STRUCT-LANDING-NOSE", 400, 300, 35.0, "Acciaio Inox"),
            ("STRUCT-FUSELAGE-F", 800, 300, 40.0, "Alluminio 7075"),
            ("STRUCT-FUSELAGE-R", 800, 300, 40.0, "Alluminio 7075"),
            ("STRUCT-TAIL-VERTICAL", 350, 600, 25.0, "Alluminio 7075"),
            ("STRUCT-TAIL-HORIZONTAL", 450, 250, 18.0, "Alluminio 7075"),
            ("STRUCT-WING-SPAR-L", 900, 200, 22.0, "Fibra di Carbonio"),
            ("STRUCT-WING-SPAR-R", 900, 200, 22.0, "Fibra di Carbonio"),
            
            # PROPULSIONE - Tools precisione media
            ("ENGINE-INLET-DUCT", 300, 350, 22.0, "Titanio Ti-6Al-4V"),
            ("ENGINE-EXHAUST-NOZZLE", 250, 300, 20.0, "Titanio Ti-6Al-4V"),
            ("ENGINE-FAN-BLADE", 150, 400, 12.0, "Titanio Ti-6Al-4V"),
            ("ENGINE-COMPRESSOR", 280, 280, 25.0, "Acciaio Inox"),
            ("ENGINE-TURBINE-DISK", 320, 320, 35.0, "Superleghe Inconel"),
            ("ENGINE-COMBUSTION-CHAMBER", 400, 400, 30.0, "Superleghe Inconel"),
            
            # CONTROLLI - Tools lunghi e sottili
            ("CONTROL-AILERON-L", 800, 200, 15.0, "Alluminio 7075"),
            ("CONTROL-AILERON-R", 800, 200, 15.0, "Alluminio 7075"),
            ("CONTROL-RUDDER", 400, 300, 18.0, "Alluminio 7075"),
            ("CONTROL-ELEVATOR", 600, 250, 16.0, "Alluminio 7075"),
            ("CONTROL-TRIM-TAB", 200, 150, 5.0, "Alluminio 6061"),
            ("CONTROL-FLAP-MAIN", 700, 250, 20.0, "Alluminio 7075"),
            
            # ELETTRONICA - Tools piccoli e leggeri
            ("ELEC-AVIONICS-NAV", 200, 150, 4.0, "Alluminio 6061"),
            ("ELEC-AVIONICS-COM", 180, 120, 3.5, "Alluminio 6061"),
            ("ELEC-FLIGHT-CONTROL", 250, 200, 6.0, "Alluminio 6061"),
            ("ELEC-ENGINE-CONTROL", 220, 180, 5.5, "Alluminio 6061"),
            ("ELEC-POWER-DIST", 300, 250, 8.0, "Alluminio 6061"),
            ("ELEC-WEATHER-RADAR", 350, 200, 7.0, "Alluminio 6061")
        ]
        
        tools_create = []
        for part_num, width, height, weight, material in tool_configs:
            tool_part_num = f"TOOL-{part_num}"
            tool = Tool(
                part_number_tool=tool_part_num,
                descrizione=f"Tool per {part_num} - nesting test v2.0.0",
                larghezza_piano=float(width),
                lunghezza_piano=float(height),
                peso=float(weight),
                materiale=material,
                disponibile=True,
                note=f"Tool v2.0.0 - {width}x{height}mm, {weight}kg, {material}"
            )
            self.db.add(tool)
            tools_create.append(tool)
        
        self.db.flush()
        
        # 4. Associa tools alle parti
        for i, parte in enumerate(parti_create):
            tool = tools_create[i]
            tool.parti.append(parte)
        
        # 5. Crea 30 ODL distribuiti per priorità
        odls_create = []
        
        # Priorità distribuite: 10 alta (1), 12 media (2), 8 bassa (3)
        priorities = [1]*10 + [2]*12 + [3]*8
        random.shuffle(priorities)
        
        # Status distribuiti: 22 "Attesa Cura" (pronti per nesting), 8 "Preparazione"
        status_list = ["Attesa Cura"]*22 + ["Preparazione"]*8
        random.shuffle(status_list)
        
        for i, (parte, priority, status) in enumerate(zip(parti_create, priorities, status_list)):
            tool = tools_create[i]
            
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status=status,
                priorita=priority,
                note=f"ODL nesting test v2.0.0 #{i+1:02d} - {parte.part_number} (P{priority}, {status})"
            )
            self.db.add(odl)
            odls_create.append(odl)
        
        self.db.commit()
        
        # 6. Calcola statistiche per ogni autoclave
        stats_autoclavi = []
        for autoclave in autoclavi:
            total_area_autoclave = autoclave.larghezza_piano * autoclave.lunghezza
            total_area_tools = sum(t.larghezza_piano * t.lunghezza_piano for t in tools_create)
            total_weight_tools = sum(t.peso for t in tools_create)
            total_valvole = sum(p.num_valvole_richieste for p in parti_create)
            
            stats = {
                "autoclave_id": autoclave.id,
                "autoclave_name": autoclave.nome,
                "autoclave_size": f"{autoclave.larghezza_piano}x{autoclave.lunghezza}mm",
                "autoclave_area_mm2": total_area_autoclave,
                "tools_area_mm2": total_area_tools,
                "coverage_potential": min(100, (total_area_tools / total_area_autoclave) * 100),
                "weight_capacity": f"{total_weight_tools:.1f}/{autoclave.max_load_kg}kg",
                "valve_capacity": f"{total_valvole}/{autoclave.num_linee_vuoto}",
                "valve_utilization": (total_valvole / autoclave.num_linee_vuoto) * 100
            }
            stats_autoclavi.append(stats)
        
        scenario_info = {
            "nome": "Scenario Completo Espanso v2.0.0",
            "autoclavi": stats_autoclavi,
            "cicli_cura": [{"id": c.id, "nome": c.nome} for c in cicli],
            "odl_ids": [odl.id for odl in odls_create],
            "num_tools": len(tools_create),
            "num_parti": len(parti_create),
            "total_weight": sum(t.peso for t in tools_create),
            "categories": {
                "Strutturale": 12,
                "Propulsione": 6,
                "Controlli": 6,
                "Elettronica": 6
            }
        }
        
        self.scenarios_created.append(scenario_info)
        
        # Conta ODL per status
        attesa_cura_count = len([odl for odl in odls_create if odl.status == "Attesa Cura"])
        preparazione_count = len([odl for odl in odls_create if odl.status == "Preparazione"])
        
        logger.info(f"✅ Scenario completo creato:")
        logger.info(f"   🏭 Autoclavi: {len(autoclavi)} (Large, Medium, Compact)")
        logger.info(f"   🔄 Cicli cura: {len(cicli)} (Aeronautico, Automotive, Marine)")
        logger.info(f"   📦 Tools: {len(tools_create)} tools unici")
        logger.info(f"   📋 ODL: {len(odls_create)} ordini (P1:10, P2:12, P3:8)")
        logger.info(f"   ✅ ODL pronti nesting: {attesa_cura_count}/30 ('Attesa Cura')")
        logger.info(f"   ⏳ ODL in preparazione: {preparazione_count}/30")
        logger.info(f"   🏷️ Categorie: {scenario_info['categories']}")
        logger.info(f"   ⚖️ Peso totale: {scenario_info['total_weight']:.1f}kg")
        
        for stats in stats_autoclavi:
            logger.info(f"   📊 {stats['autoclave_name']}: copertura {stats['coverage_potential']:.1f}%, "
                       f"valvole {stats['valve_utilization']:.1f}%")
        
        return scenario_info
    
    def print_summary(self):
        """Stampa un riassunto completo degli scenari creati"""
        logger.info("=" * 80)
        logger.info("🎉 SEED COMPLETO v2.0.0 TERMINATO CON SUCCESSO!")
        logger.info("=" * 80)
        
        for i, scenario in enumerate(self.scenarios_created, 1):
            logger.info(f"""
📋 SCENARIO {i}: {scenario['nome']}
   🏭 Autoclavi: {len(scenario['autoclavi'])} disponibili
   🔄 Cicli cura: {len(scenario['cicli_cura'])} tipi
   📦 Tools creati: {scenario['num_tools']} (tutti diversi)
   📋 ODL totali: {len(scenario['odl_ids'])}
   🏷️ Categorie: {', '.join(f'{k}:{v}' for k, v in scenario['categories'].items())}
            """)
            
            for autoclave_stats in scenario['autoclavi']:
                logger.info(f"   🏭 {autoclave_stats['autoclave_name']}: "
                           f"{autoclave_stats['autoclave_size']}, "
                           f"copertura {autoclave_stats['coverage_potential']:.1f}%")
        
        logger.info(f"""
🚀 COMANDI PER TESTARE (PRONTI SUBITO):
   1. Avvia backend: uvicorn backend.main:app --reload
   2. Test autoclave grande: POST /nesting/solve con autoclave_id={self.scenarios_created[0]['autoclavi'][0]['autoclave_id']}
   3. Test autoclave media: POST /nesting/solve con autoclave_id={self.scenarios_created[0]['autoclavi'][1]['autoclave_id']}
   4. Test autoclave compatta: POST /nesting/solve con autoclave_id={self.scenarios_created[0]['autoclavi'][2]['autoclave_id']}

✅ 22/30 ODL GIÀ PRONTI per nesting (status 'Attesa Cura')!
⏳ 8/30 ODL in 'Preparazione' (per test workflow completo)

🎯 TARGET ATTESI:
   - Autoclave grande: efficiency ≥ 80%, ~20-22 pezzi
   - Autoclave media: efficiency ≥ 70%, ~15-18 pezzi  
   - Autoclave compatta: efficiency ≥ 60%, ~10-15 pezzi

🎉 Database pronto per test IMMEDIATI del nesting!
        """)


def main():
    """Funzione principale per eseguire il seed completo v2.0.0"""
    logger.info("🚀 AVVIO SEED COMPLETO NESTING v2.0.0-EXPANDED")
    logger.info("=" * 80)
    
    # Testa connessione database
    if not test_database_connection():
        logger.error("❌ Impossibile connettersi al database. Verifica la configurazione.")
        return False
    
    try:
        with CompleteNestingSeed() as seeder:
            # 1. Pulisci dati esistenti
            seeder.cleanup_existing_test_data()
            
            # 2. Crea 3 autoclavi
            autoclavi = seeder.create_autoclaves()
            
            # 3. Crea 3 cicli di cura
            cicli = seeder.create_cure_cycles()
            
            # 4. Crea scenario completo (30 ODL, tools diversificati)
            seeder.create_comprehensive_scenario(autoclavi, cicli)
            
            # 5. Stampa riassunto
            seeder.print_summary()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante il seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("✅ Seed v2.0.0 completato con successo!")
    else:
        logger.error("❌ Seed v2.0.0 fallito!")
        sys.exit(1) 