#!/usr/bin/env python3
"""
Seed Edge Cases Data per CarbonPilot
Carica dati di test specifici per edge cases dell'algoritmo di nesting.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from api.database import get_db
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura
from models.parte import Parte
from models.tool import Tool
from models.odl import ODL

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EdgeDataSeeder:
    """Classe per creare dati edge cases per testing del nesting"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_base_data(self):
        """Crea dati base necessari (autoclave, cicli cura, catalogo)"""
        logger.info("📋 Creazione dati base...")
        
        # Controlla se autoclave di test esiste già
        autoclave = self.db.query(Autoclave).filter(
            Autoclave.codice == "EDGE-001"
        ).first()
        
        if autoclave:
            logger.info(f"✅ Autoclave di test già esistente: ID {autoclave.id}")
            self.autoclave_id = autoclave.id
        else:
            # Crea autoclave di test
            autoclave = Autoclave(
                nome="EdgeTest-Autoclave",
                codice="EDGE-001",
                produttore="Test Manufacturer",
                anno_produzione=2024,
                lunghezza=2000.0,  # 2 metri
                larghezza_piano=1200.0,  # 1.2 metri
                temperatura_max=180.0,
                pressione_max=8.0,
                max_load_kg=800.0,
                num_linee_vuoto=10,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                note="Autoclave dedicata ai test edge cases"
            )
            self.db.add(autoclave)
            self.db.flush()
            self.autoclave_id = autoclave.id
            logger.info(f"✅ Autoclave creata: ID {self.autoclave_id}")
        
        # Controlla se ciclo di cura esiste già
        ciclo_cura = self.db.query(CicloCura).filter(
            CicloCura.nome == "EdgeTest-Cycle"
        ).first()
        
        if ciclo_cura:
            logger.info(f"✅ Ciclo cura di test già esistente: ID {ciclo_cura.id}")
            self.ciclo_cura_id = ciclo_cura.id
        else:
            # Crea ciclo di cura standard
            ciclo_cura = CicloCura(
                nome="EdgeTest-Cycle",
                descrizione="Ciclo di cura per test edge cases",
                temperatura_stasi1=165.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,
                attiva_stasi2=False
            )
            self.db.add(ciclo_cura)
            self.db.flush()
            self.ciclo_cura_id = ciclo_cura.id
            logger.info(f"✅ Ciclo cura creato: ID {self.ciclo_cura_id}")
        
        self.db.commit()
        
    def cleanup_existing_edge_data(self):
        """Pulisce i dati edge cases esistenti per evitare duplicati"""
        logger.info("🧹 Pulizia dati edge cases esistenti...")
        
        try:
            # Elimina ODL edge cases esistenti
            edge_patterns = [
                "%Edge case: pezzo gigante%",
                "%Edge case B:%", 
                "%Edge case C:%",
                "%Edge case D:%",
                "%Edge case E:%"
            ]
            
            total_deleted = 0
            for pattern in edge_patterns:
                odl_to_delete = self.db.query(ODL).filter(ODL.note.like(pattern)).all()
                for odl in odl_to_delete:
                    self.db.delete(odl)
                    total_deleted += 1
            
            # Elimina tools edge cases
            tool_patterns = [
                "TOOL-GIANT-A%",
                "TOOL-VACUUM-B%", 
                "TOOL-STRESS-C%",
                "TOOL-LOWEFF-D%",
                "TOOL-HAPPY-E%"
            ]
            
            for pattern in tool_patterns:
                tools_to_delete = self.db.query(Tool).filter(Tool.part_number_tool.like(pattern)).all()
                for tool in tools_to_delete:
                    self.db.delete(tool)
            
            # Elimina parti edge cases
            part_patterns = [
                "GIANT-WING-A%",
                "VACUUM-TEST-B%", 
                "STRESS-TEST-C%",
                "LOW-EFF-D%",
                "HAPPY-PATH-E%"
            ]
            
            for pattern in part_patterns:
                parts_to_delete = self.db.query(Parte).filter(Parte.part_number.like(pattern)).all()
                for part in parts_to_delete:
                    self.db.delete(part)
            
            # Elimina cataloghi edge cases
            catalogs_to_delete = self.db.query(Catalogo).filter(
                Catalogo.part_number.like("GIANT-WING-A%") |
                Catalogo.part_number.like("VACUUM-TEST-B%") |
                Catalogo.part_number.like("STRESS-TEST-C%") |
                Catalogo.part_number.like("LOW-EFF-D%") |
                Catalogo.part_number.like("HAPPY-PATH-E%")
            ).all()
            
            for catalog in catalogs_to_delete:
                self.db.delete(catalog)
            
            self.db.commit()
            logger.info(f"✅ Puliti {total_deleted} ODL e dati correlati")
            
        except Exception as e:
            logger.error(f"💥 Errore durante pulizia: {str(e)}")
            self.db.rollback()
            raise
        
    def create_scenario_a_giant_piece(self):
        """
        Scenario A: 1 pezzo gigante (area > autoclave)
        Scopo: Testare gestione pezzi che non possono fisicamente essere caricati
        """
        logger.info("🅰️  Creazione Scenario A: Pezzo Gigante")
        
        # Catalogo
        catalog = Catalogo(
            part_number="GIANT-WING-A01",
            descrizione="Wing panel gigante per test edge case",
            categoria="Test Components",
            sotto_categoria="Giant Parts",
            attivo=True
        )
        self.db.add(catalog)
        
        # Tool gigante (più grande dell'autoclave)
        tool = Tool(
            part_number_tool="TOOL-GIANT-A01",
            descrizione="Tool per wing panel gigante - dimensioni eccessive",
            lunghezza_piano=2500.0,  # 2.5m > autoclave 2.0m
            larghezza_piano=1500.0,  # 1.5m > autoclave 1.2m
            peso=100.0,
            materiale="Alluminio",
            disponibile=True,
            note="Tool gigante per test edge case - NON dovrebbe mai essere posizionato"
        )
        self.db.add(tool)
        
        # Parte
        parte = Parte(
            part_number="GIANT-WING-A01",
            ciclo_cura_id=self.ciclo_cura_id,
            descrizione_breve="Wing panel gigante",
            num_valvole_richieste=5,
            note_produzione="Test edge case: dimensioni eccessive"
        )
        self.db.add(parte)
        self.db.flush()
        
        # ODL
        odl = ODL(
            parte_id=parte.id,
            tool_id=tool.id,
            status="Preparazione",
            priorita=5,
            note="Edge case: pezzo gigante che non può essere caricato"
        )
        self.db.add(odl)
        
        self.db.commit()
        logger.info("✅ Scenario A completato - 1 ODL con pezzo gigante")
        
    def create_scenario_b_vacuum_overflow(self):
        """
        Scenario B: 6 pezzi, linee_vuoto = capacità + 1
        Scopo: Testare gestione limite linee vuoto
        """
        logger.info("🅱️  Creazione Scenario B: Overflow Linee Vuoto")
        
        for i in range(6):
            # Catalogo
            catalog = Catalogo(
                part_number=f"VACUUM-TEST-B{i+1:02d}",
                descrizione=f"Componente test vacuum line #{i+1}",
                categoria="Test Components",
                sotto_categoria="Vacuum Test",
                attivo=True
            )
            self.db.add(catalog)
            
            # Tool medio
            tool = Tool(
                part_number_tool=f"TOOL-VACUUM-B{i+1:02d}",
                descrizione=f"Tool per test vacuum line #{i+1}",
                lunghezza_piano=400.0,
                larghezza_piano=300.0,
                peso=25.0,
                materiale="Alluminio",
                disponibile=True,
                note=f"Tool #{i+1} per test linee vuoto"
            )
            self.db.add(tool)
            
            # Parte con richiesta 2 linee vuoto (totale = 12 > capacità 10)
            parte = Parte(
                part_number=f"VACUUM-TEST-B{i+1:02d}",
                ciclo_cura_id=self.ciclo_cura_id,
                descrizione_breve=f"Componente vacuum test #{i+1}",
                num_valvole_richieste=2,  # 6 * 2 = 12 > 10 (capacità)
                note_produzione="Test edge case: overflow linee vuoto"
            )
            self.db.add(parte)
            self.db.flush()
            
            # ODL
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status="Preparazione",
                priorita=3,
                note=f"Edge case B: pezzo #{i+1} per test overflow vacuum"
            )
            self.db.add(odl)
            
        self.db.commit()
        logger.info("✅ Scenario B completato - 6 ODL per test overflow linee vuoto")
        
    def create_scenario_c_stress_performance(self):
        """
        Scenario C: 50 pezzi misti (stress performance)
        Scopo: Testare performance dell'algoritmo con molti pezzi
        """
        logger.info("🆒 Creazione Scenario C: Stress Performance (50 pezzi)")
        
        # Varie dimensioni per stress test
        piece_configs = [
            # Piccoli (20 pezzi)
            *[(150, 100, 5, 1) for _ in range(20)],
            # Medi (20 pezzi)
            *[(300, 250, 15, 1) for _ in range(20)],
            # Grandi (10 pezzi)
            *[(500, 400, 35, 2) for _ in range(10)]
        ]
        
        for i, (length, width, weight, vacuum_lines) in enumerate(piece_configs):
            # Catalogo
            catalog = Catalogo(
                part_number=f"STRESS-TEST-C{i+1:03d}",
                descrizione=f"Componente stress test #{i+1}",
                categoria="Test Components",
                sotto_categoria=f"Stress Test Batch {i//10 + 1}",
                attivo=True
            )
            self.db.add(catalog)
            
            # Tool con dimensioni variabili
            tool = Tool(
                part_number_tool=f"TOOL-STRESS-C{i+1:03d}",
                descrizione=f"Tool stress test #{i+1}",
                lunghezza_piano=float(length),
                larghezza_piano=float(width),
                peso=float(weight),
                materiale="Alluminio" if i % 2 == 0 else "Acciaio",
                disponibile=True,
                note=f"Tool #{i+1} per stress test performance"
            )
            self.db.add(tool)
            
            # Parte
            parte = Parte(
                part_number=f"STRESS-TEST-C{i+1:03d}",
                ciclo_cura_id=self.ciclo_cura_id,
                descrizione_breve=f"Componente stress #{i+1}",
                num_valvole_richieste=vacuum_lines,
                note_produzione="Test edge case: stress performance"
            )
            self.db.add(parte)
            self.db.flush()
            
            # ODL con priorità variabile
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status="Preparazione",
                priorita=(i % 5) + 1,  # Priorità da 1 a 5
                note=f"Edge case C: pezzo #{i+1} per stress test"
            )
            self.db.add(odl)
            
            # Commit ogni 10 elementi per performance
            if (i + 1) % 10 == 0:
                self.db.commit()
                logger.info(f"💾 Salvati primi {i+1} pezzi scenario C")
        
        self.db.commit()
        logger.info("✅ Scenario C completato - 50 ODL per stress test")
        
    def create_scenario_d_low_efficiency(self):
        """
        Scenario D: 10 pezzi, padding = 100mm (bassa efficienza)
        Scopo: Testare comportamento con parametri che riducono l'efficienza
        """
        logger.info("🅳 Creazione Scenario D: Bassa Efficienza (padding elevato)")
        
        for i in range(10):
            # Catalogo
            catalog = Catalogo(
                part_number=f"LOW-EFF-D{i+1:02d}",
                descrizione=f"Componente low efficiency #{i+1}",
                categoria="Test Components",
                sotto_categoria="Low Efficiency Test",
                attivo=True
            )
            self.db.add(catalog)
            
            # Tool medio-grande con forme dispari
            base_size = 300 + (i * 50)  # Dimensioni crescenti
            tool = Tool(
                part_number_tool=f"TOOL-LOWEFF-D{i+1:02d}",
                descrizione=f"Tool low efficiency #{i+1}",
                lunghezza_piano=float(base_size),
                larghezza_piano=float(base_size - 100),  # Forme rettangolari
                peso=20.0 + (i * 5),
                materiale="Alluminio",
                disponibile=True,
                note=f"Tool #{i+1} per test bassa efficienza"
            )
            self.db.add(tool)
            
            # Parte
            parte = Parte(
                part_number=f"LOW-EFF-D{i+1:02d}",
                ciclo_cura_id=self.ciclo_cura_id,
                descrizione_breve=f"Componente low efficiency #{i+1}",
                num_valvole_richieste=1,
                note_produzione="Test edge case: bassa efficienza"
            )
            self.db.add(parte)
            self.db.flush()
            
            # ODL
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status="Preparazione",
                priorita=2,
                note=f"Edge case D: pezzo #{i+1} per test bassa efficienza"
            )
            self.db.add(odl)
            
        self.db.commit()
        logger.info("✅ Scenario D completato - 10 ODL per test bassa efficienza")
        
    def create_scenario_e_happy_path(self):
        """
        Scenario E: 15 pezzi realistici (happy path)
        Scopo: Testare scenario realistico che dovrebbe funzionare bene
        """
        logger.info("🅴 Creazione Scenario E: Happy Path (scenario realistico)")
        
        # Configurazioni realistiche per un buon nesting
        realistic_configs = [
            # 5 pezzi piccoli
            *[(200, 150, 8, 1) for _ in range(5)],
            # 5 pezzi medi
            *[(350, 280, 18, 1) for _ in range(5)],
            # 3 pezzi grandi
            *[(450, 380, 32, 2) for _ in range(3)],
            # 2 pezzi extra
            (280, 220, 12, 1),
            (320, 300, 22, 1)
        ]
        
        for i, (length, width, weight, vacuum_lines) in enumerate(realistic_configs):
            # Catalogo
            catalog = Catalogo(
                part_number=f"HAPPY-PATH-E{i+1:02d}",
                descrizione=f"Componente realistico #{i+1}",
                categoria="Aerospace Components",
                sotto_categoria="Wing Brackets" if i < 8 else "Support Plates",
                attivo=True
            )
            self.db.add(catalog)
            
            # Tool realistico
            tool = Tool(
                part_number_tool=f"TOOL-HAPPY-E{i+1:02d}",
                descrizione=f"Tool realistico #{i+1}",
                lunghezza_piano=float(length),
                larghezza_piano=float(width),
                peso=float(weight),
                materiale="Alluminio",
                disponibile=True,
                note=f"Tool #{i+1} per happy path test"
            )
            self.db.add(tool)
            
            # Parte
            parte = Parte(
                part_number=f"HAPPY-PATH-E{i+1:02d}",
                ciclo_cura_id=self.ciclo_cura_id,
                descrizione_breve=f"Componente realistico #{i+1}",
                num_valvole_richieste=vacuum_lines,
                note_produzione="Test edge case: happy path scenario"
            )
            self.db.add(parte)
            self.db.flush()
            
            # ODL con priorità realistica
            priority = 3 if i < 10 else 4  # Priorità medio-alta
            odl = ODL(
                parte_id=parte.id,
                tool_id=tool.id,
                status="Preparazione",
                priorita=priority,
                note=f"Edge case E: pezzo #{i+1} per happy path"
            )
            self.db.add(odl)
            
        self.db.commit()
        logger.info("✅ Scenario E completato - 15 ODL per happy path test")

def main():
    """Main function"""
    logger.info("🚀 AVVIO SEED EDGE CASES DATA")
    logger.info("=" * 60)
    
    try:
        # Ottieni sessione database
        db_gen = get_db()
        db = next(db_gen)
        
        # Assicurati che le tabelle esistano
        from api.database import engine
        from models.base import Base
        logger.info("🔧 Creazione tabelle se necessario...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelle verificate/create")
        
        # Crea seeder
        seeder = EdgeDataSeeder(db)
        
        # Crea dati base
        seeder.create_base_data()
        
        # Pulisci dati edge cases esistenti
        seeder.cleanup_existing_edge_data()
        
        # Crea tutti gli scenari
        seeder.create_scenario_a_giant_piece()
        seeder.create_scenario_b_vacuum_overflow()
        seeder.create_scenario_c_stress_performance()
        seeder.create_scenario_d_low_efficiency()
        seeder.create_scenario_e_happy_path()
        
        logger.info("=" * 60)
        logger.info("🎉 SEED EDGE CASES COMPLETATO CON SUCCESSO!")
        logger.info("📊 Riepilogo dati creati:")
        logger.info("   🅰️  Scenario A: 1 ODL (pezzo gigante)")
        logger.info("   🅱️  Scenario B: 6 ODL (overflow vacuum)")
        logger.info("   🆒 Scenario C: 50 ODL (stress performance)")
        logger.info("   🅳 Scenario D: 10 ODL (bassa efficienza)")
        logger.info("   🅴 Scenario E: 15 ODL (happy path)")
        logger.info("   📈 TOTALE: 82 ODL pronti per test edge cases")
        
        print("✅ Seed edge cases completato con successo!")
        print("💡 Puoi ora eseguire edge_tests.py per avviare i test")
        
    except Exception as e:
        logger.error(f"💥 Errore durante seed edge cases: {str(e)}")
        print("❌ Seed edge cases fallito!")
        print(f"🔍 Errore: {str(e)}")
        sys.exit(1)
    finally:
        # Chiudi sessione database
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    main() 