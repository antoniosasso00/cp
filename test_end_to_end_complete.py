#!/usr/bin/env python3
"""
🔄 TEST END-TO-END COMPLETO DEL SISTEMA CARBONPILOT
===================================================

Questo script testa l'intero flusso del sistema:
1. Preparazione dati
2. Creazione batch nesting 
3. Esecuzione algoritmo nesting
4. Visualizzazione risultati
5. Conferma batch
6. Chiusura batch
"""

import sys
import os

# Aggiungi il path del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import json
import logging
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import del sistema
from backend.models.db import engine, SessionLocal
from backend.models.odl import ODL
from backend.models.tool import Tool
from backend.models.parte import Parte
from backend.models.autoclave import Autoclave
from backend.models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from backend.models.nesting_result import NestingResult
from backend.services.nesting_service import NestingService, NestingParameters

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EndToEndTest:
    """Classe per eseguire test end-to-end completi"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.nesting_service = NestingService()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    def print_header(self, title: str):
        """Stampa un header formattato"""
        print(f"\n{'='*60}")
        print(f"🔄 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str, result: str = ""):
        """Stampa un passaggio del test"""
        print(f"📋 {step}")
        if result:
            print(f"   ✅ {result}")
    
    def check_database_status(self):
        """Verifica lo stato del database"""
        self.print_header("FASE 1: VERIFICA DATABASE")
        
        try:
            # Conta elementi principali
            odl_count = self.db.query(ODL).count()
            tool_count = self.db.query(Tool).count()
            autoclave_count = self.db.query(Autoclave).count()
            batch_count = self.db.query(BatchNesting).count()
            
            self.print_step("Conteggio entità", f"ODL: {odl_count}, Tools: {tool_count}, Autoclavi: {autoclave_count}, Batch: {batch_count}")
            
            # Verifica ODL disponibili per nesting
            odl_disponibili = self.db.query(ODL).filter(
                ODL.status.in_(['Preparazione', 'Pronto'])
            ).all()
            
            self.print_step("ODL disponibili per nesting", f"{len(odl_disponibili)} ODL trovati")
            
            for odl in odl_disponibili[:3]:  # Mostra solo i primi 3
                parte_desc = odl.parte.descrizione_breve if odl.parte else "N/A"
                tool_pn = odl.tool.part_number_tool if odl.tool else "N/A"
                print(f"   • ODL {odl.id}: {parte_desc} (Tool: {tool_pn})")
                
            return odl_disponibili
            
        except Exception as e:
            logger.error(f"❌ Errore verifica database: {e}")
            return []
    
    def create_test_batch(self, odl_list):
        """Crea un batch di test per il nesting"""
        self.print_header("FASE 2: CREAZIONE BATCH NESTING")
        
        try:
            # Seleziona i primi 3-5 ODL per il test
            selected_odls = odl_list[:min(5, len(odl_list))]
            odl_ids = [odl.id for odl in selected_odls]
            
            # Seleziona la prima autoclave disponibile
            autoclave = self.db.query(Autoclave).filter(
                Autoclave.stato == 'DISPONIBILE'
            ).first()
            
            if not autoclave:
                autoclave = self.db.query(Autoclave).first()
                self.print_step("Autoclave", f"⚠️ Nessuna autoclave disponibile, uso {autoclave.nome}")
            else:
                self.print_step("Autoclave selezionata", f"{autoclave.nome} ({autoclave.larghezza_piano}x{autoclave.lunghezza}mm)")
            
            # Crea il batch
            batch = BatchNesting(
                nome=f"TEST_BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                odl_ids=odl_ids,
                autoclave_id=autoclave.id,
                parametri={
                    "padding_mm": 20,
                    "min_distance_mm": 15,
                    "priorita_area": True,
                    "accorpamento_odl": False
                },
                stato=StatoBatchNestingEnum.SOSPESO.value,
                creato_da_utente="test_system"
            )
            
            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)
            
            self.print_step("Batch creato", f"ID: {batch.id}, ODL: {len(odl_ids)}")
            
            return batch, autoclave
            
        except Exception as e:
            logger.error(f"❌ Errore creazione batch: {e}")
            self.db.rollback()
            return None, None
    
    def execute_nesting_algorithm(self, batch, autoclave):
        """Esegue l'algoritmo di nesting"""
        self.print_header("FASE 3: ESECUZIONE ALGORITMO NESTING")
        
        try:
            # Prepara parametri per l'algoritmo
            parameters = NestingParameters(
                padding_mm=batch.parametri.get('padding_mm', 20),
                min_distance_mm=batch.parametri.get('min_distance_mm', 15),
                priorita_area=batch.parametri.get('priorita_area', True),
                accorpamento_odl=batch.parametri.get('accorpamento_odl', False)
            )
            
            self.print_step("Avvio algoritmo", f"ODL: {len(batch.odl_ids)}, Parametri: {parameters}")
            
            start_time = time.time()
            
            # Esegue il nesting
            result = self.nesting_service.generate_nesting(
                db=self.db,
                odl_ids=batch.odl_ids,
                autoclave_id=batch.autoclave_id,
                parameters=parameters
            )
            
            execution_time = time.time() - start_time
            
            self.print_step("Algoritmo completato", f"Tempo: {execution_time:.2f}s, Successo: {result.success}")
            
            if result.success:
                self.print_step("Risultati nesting", 
                    f"Tools posizionati: {len(result.positioned_tools)}, "
                    f"Esclusi: {len(result.excluded_odls)}, "
                    f"Efficienza: {result.efficiency:.1f}%"
                )
                
                # Mostra dettagli posizioni
                for i, pos in enumerate(result.positioned_tools[:3]):  # Prime 3 posizioni
                    print(f"   • ODL {pos.odl_id}: ({pos.x:.1f}, {pos.y:.1f}) {pos.width:.1f}x{pos.height:.1f}mm")
                
                # Mostra esclusioni
                for excl in result.excluded_odls:
                    print(f"   ⚠️ ODL {excl['odl_id']} escluso: {excl['motivo']}")
            else:
                self.print_step("Errore algoritmo", f"Status: {result.algorithm_status}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Errore esecuzione nesting: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_nesting_results(self, batch, nesting_result):
        """Salva i risultati del nesting nel database"""
        self.print_header("FASE 4: SALVATAGGIO RISULTATI")
        
        try:
            # Crea record NestingResult
            db_result = NestingResult(
                batch_id=batch.id,
                autoclave_id=batch.autoclave_id,
                odl_ids=batch.odl_ids,
                odl_esclusi_ids=[excl['odl_id'] for excl in nesting_result.excluded_odls],
                motivi_esclusione=[excl['motivo'] for excl in nesting_result.excluded_odls],
                posizioni_tool=[
                    {
                        'odl_id': pos.odl_id,
                        'piano': 1,  # Per ora solo piano 1
                        'x': pos.x,
                        'y': pos.y,
                        'width': pos.width,
                        'height': pos.height,
                        'rotated': getattr(pos, 'rotated', False)
                    }
                    for pos in nesting_result.positioned_tools
                ],
                peso_totale_kg=nesting_result.total_weight,
                area_utilizzata=nesting_result.used_area,
                area_totale=nesting_result.total_area,
                stato="In sospeso"
            )
            
            self.db.add(db_result)
            
            # Aggiorna il batch con i campi corretti del modello
            batch.stato = StatoBatchNestingEnum.CONFERMATO.value
            batch.numero_nesting = 1  # Un nesting result
            batch.peso_totale_kg = int(nesting_result.total_weight)
            batch.area_totale_utilizzata = int(nesting_result.used_area)
            batch.valvole_totali_utilizzate = len(nesting_result.positioned_tools)
            
            self.db.commit()
            self.db.refresh(db_result)
            
            self.print_step("Risultati salvati", f"NestingResult ID: {db_result.id}")
            
            return db_result
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio risultati: {e}")
            self.db.rollback()
            return None
    
    def simulate_batch_confirmation(self, batch, nesting_result):
        """Simula la conferma del batch"""
        self.print_header("FASE 5: SIMULAZIONE CONFERMA BATCH")
        
        try:
            # Aggiorna stato batch
            batch.stato = StatoBatchNestingEnum.CONFERMATO.value
            batch.data_conferma = datetime.utcnow()
            batch.confermato_da_utente = "test_system"
            batch.confermato_da_ruolo = "ADMIN"
            
            # Aggiorna stato autoclave
            autoclave = self.db.query(Autoclave).get(batch.autoclave_id)
            autoclave.stato = 'IN_USO'
            
            # Aggiorna stato ODL posizionati
            positioned_odl_ids = [pos.odl_id for pos in nesting_result.positioned_tools] if nesting_result else []
            
            odls_to_update = self.db.query(ODL).filter(ODL.id.in_(positioned_odl_ids)).all()
            for odl in odls_to_update:
                odl.previous_status = odl.status
                odl.status = 'Caricato'
            
            self.db.commit()
            
            self.print_step("Batch confermato", f"ODL aggiornati: {len(odls_to_update)}")
            self.print_step("Autoclave aggiornata", f"{autoclave.nome} -> IN_USO")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore conferma batch: {e}")
            self.db.rollback()
            return False
    
    def simulate_curing_cycle(self, batch):
        """Simula il ciclo di cura"""
        self.print_header("FASE 6: SIMULAZIONE CICLO DI CURA")
        
        try:
            # Aggiorna stato per simulare avvio cura - rimaniamo su CONFERMATO
            # batch.stato = StatoBatchNestingEnum.CONFERMATO.value  # Già confermato
            batch.inizio_cura = datetime.utcnow()
            
            self.db.commit()
            
            self.print_step("Ciclo di cura avviato", f"Inizio: {batch.inizio_cura}")
            
            # Simula attesa (in un test reale questo sarebbe molto più lungo)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore simulazione cura: {e}")
            return False
    
    def simulate_batch_completion(self, batch):
        """Simula il completamento del batch"""
        self.print_header("FASE 7: SIMULAZIONE COMPLETAMENTO BATCH")
        
        try:
            # Aggiorna stato batch
            batch.stato = StatoBatchNestingEnum.TERMINATO.value
            batch.data_completamento = datetime.utcnow()
            
            if batch.inizio_cura:
                durata = (batch.data_completamento - batch.inizio_cura).total_seconds() / 60
                batch.durata_ciclo_minuti = int(durata)
            
            # Libera autoclave
            autoclave = self.db.query(Autoclave).get(batch.autoclave_id)
            autoclave.stato = 'DISPONIBILE'
            
            # Aggiorna stato ODL
            if batch.odl_ids:
                odls = self.db.query(ODL).filter(ODL.id.in_(batch.odl_ids)).all()
                for odl in odls:
                    if odl.status == 'Caricato':
                        odl.previous_status = odl.status
                        odl.status = 'Completato'
            
            self.db.commit()
            
            self.print_step("Batch completato", f"Durata: {batch.durata_ciclo_minuti} min")
            self.print_step("Sistema ripristinato", "Autoclave disponibile, ODL completati")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore completamento batch: {e}")
            self.db.rollback()
            return False
    
    def generate_final_report(self, batch):
        """Genera un report finale del test"""
        self.print_header("FASE 8: REPORT FINALE")
        
        try:
            # Raccogli statistiche
            total_odls = len(batch.odl_ids) if batch.odl_ids else 0
            
            positioned_count = batch.valvole_totali_utilizzate or 0
            excluded_count = total_odls - positioned_count
            
            efficiency = 0
            if batch.area_totale_utilizzata and hasattr(batch, 'autoclave'):
                autoclave = self.db.query(Autoclave).get(batch.autoclave_id)
                if autoclave and autoclave.larghezza_piano and autoclave.lunghezza:
                    total_area = autoclave.larghezza_piano * autoclave.lunghezza
                    efficiency = (batch.area_totale_utilizzata / total_area) * 100
            
            total_weight = batch.peso_totale_kg or 0
            
            durata_totale = 0
            if batch.data_completamento and batch.created_at:
                durata_totale = (batch.data_completamento - batch.created_at).total_seconds() / 60
            
            # Stampa report
            print(f"📊 STATISTICHE FINALI:")
            print(f"   • Batch ID: {batch.id}")
            print(f"   • Nome: {batch.nome}")
            print(f"   • Status finale: {batch.stato}")
            print(f"   • ODL totali: {total_odls}")
            print(f"   • ODL posizionati: {positioned_count}")
            print(f"   • ODL esclusi: {excluded_count}")
            if batch.area_totale_utilizzata and batch.autoclave:
                print(f"   • Efficienza: {efficiency:.1f}%")
                print(f"   • Peso totale: {total_weight:.1f} kg")
            print(f"   • Durata totale processo: {durata_totale:.1f} min")
            
            if batch.durata_ciclo_minuti:
                print(f"   • Durata ciclo cura: {batch.durata_ciclo_minuti} min")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore generazione report: {e}")
            return False
    
    def run_complete_test(self):
        """Esegue il test end-to-end completo"""
        try:
            print("🚀 AVVIO TEST END-TO-END COMPLETO")
            print(f"Timestamp: {datetime.now()}")
            
            # Fase 1: Verifica database
            odl_list = self.check_database_status()
            if not odl_list:
                print("❌ Nessun ODL disponibile per il test")
                return False
            
            # Fase 2: Crea batch
            batch, autoclave = self.create_test_batch(odl_list)
            if not batch:
                print("❌ Impossibile creare batch di test")
                return False
            
            # Fase 3: Esegui nesting
            nesting_result = self.execute_nesting_algorithm(batch, autoclave)
            if not nesting_result:
                print("❌ Errore nell'algoritmo di nesting")
                return False
            
            # Fase 4: Salva risultati
            db_result = self.save_nesting_results(batch, nesting_result)
            if not db_result:
                print("❌ Errore nel salvataggio")
                return False
            
            # Fase 5: Conferma batch
            if not self.simulate_batch_confirmation(batch, nesting_result):
                print("❌ Errore nella conferma")
                return False
            
            # Fase 6: Simula cura
            if not self.simulate_curing_cycle(batch):
                print("❌ Errore nella simulazione cura")
                return False
            
            # Fase 7: Completa batch
            if not self.simulate_batch_completion(batch):
                print("❌ Errore nel completamento")
                return False
            
            # Fase 8: Report finale
            if not self.generate_final_report(batch):
                print("❌ Errore nel report finale")
                return False
            
            print("\n🎉 TEST END-TO-END COMPLETATO CON SUCCESSO!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore critico nel test: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Funzione principale"""
    try:
        tester = EndToEndTest()
        success = tester.run_complete_test()
        
        if success:
            print("\n✅ TUTTI I TEST SONO PASSATI!")
            sys.exit(0)
        else:
            print("\n❌ ALCUNI TEST SONO FALLITI!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 