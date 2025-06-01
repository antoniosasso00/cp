#!/usr/bin/env python3
"""
🔧 SCRIPT DI ROBUSTEZZA E DIAGNOSTICA DEL MODULO NESTING
================================================

Questo script testa e risolve i problemi del modulo nesting:
1. Verifica stato del database e ODL disponibili
2. Testa la generazione del nesting 
3. Verifica caricamento dei risultati
4. Identifica e risolve i problemi comuni
5. Genera batch di test funzionanti per il frontend

Utilizzo: python test_nesting_robustness.py
"""

import sys
import json
import sqlite3
import requests
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurazione API
BASE_URL = "http://localhost:3001/api/v1"
DB_PATH = "carbonpilot.db"

class NestingRobustnessTest:
    """Classe per testare la robustezza del modulo nesting"""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "database_health": False,
            "odl_availability": False,
            "autoclave_availability": False,
            "nesting_generation": False,
            "batch_loading": False,
            "frontend_integration": False
        }
        
    def print_header(self, title: str):
        """Stampa un header formattato"""
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: int, title: str):
        """Stampa un passo del test"""
        print(f"\n📌 STEP {step}: {title}")
        print("-" * 40)
    
    def check_database_health(self) -> bool:
        """Verifica lo stato del database"""
        self.print_step(1, "VERIFICA STATO DATABASE")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Conta ODL per stato
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM odl 
                GROUP BY status
            """)
            odl_stats = dict(cursor.fetchall())
            
            # Conta autoclavi per stato
            cursor.execute("""
                SELECT stato, COUNT(*) 
                FROM autoclavi 
                GROUP BY stato
            """)
            autoclave_stats = dict(cursor.fetchall())
            
            # Conta batch nesting per stato
            cursor.execute("""
                SELECT stato, COUNT(*) 
                FROM batch_nesting 
                GROUP BY stato
            """)
            batch_stats = dict(cursor.fetchall())
            
            print(f"✅ Database accessibile:")
            print(f"  📋 ODL: {odl_stats}")
            print(f"  🏭 Autoclavi: {autoclave_stats}")
            print(f"  📦 Batch: {batch_stats}")
            
            # Verifica ODL in Attesa Cura
            attesa_cura = odl_stats.get('Attesa Cura', 0)
            disponibili = autoclave_stats.get('Disponibile', 0)
            
            if attesa_cura == 0:
                print("⚠️  Nessun ODL in 'Attesa Cura' - creazione ODL test...")
                self._create_test_odl(cursor)
                conn.commit()
                
            if disponibili == 0:
                print("⚠️  Nessuna autoclave 'Disponibile' - aggiornamento stato...")
                self._fix_autoclave_status(cursor)
                conn.commit()
            
            conn.close()
            self.test_results["database_health"] = True
            return True
            
        except Exception as e:
            print(f"❌ Errore database: {str(e)}")
            self.test_results["database_health"] = False
            return False
    
    def _create_test_odl(self, cursor):
        """Crea ODL di test se necessari"""
        try:
            # Crea alcuni ODL in Attesa Cura se non esistono
            cursor.execute("""
                SELECT COUNT(*) FROM odl WHERE status = 'Attesa Cura'
            """)
            count = cursor.fetchone()[0]
            
            if count < 3:
                # Ottieni parte e tool ID casuali
                cursor.execute("SELECT id FROM parti LIMIT 1")
                parte_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT id FROM tools LIMIT 3")
                tool_ids = [row[0] for row in cursor.fetchall()]
                
                for i, tool_id in enumerate(tool_ids):
                    cursor.execute("""
                        INSERT INTO odl (parte_id, tool_id, status, priorita, created_at, updated_at)
                        VALUES (?, ?, 'Attesa Cura', 1, ?, ?)
                    """, (parte_id, tool_id, datetime.now().isoformat(), datetime.now().isoformat()))
                
                print(f"✅ Creati {len(tool_ids)} ODL di test")
                
        except Exception as e:
            print(f"⚠️  Errore creazione ODL test: {str(e)}")
    
    def _fix_autoclave_status(self, cursor):
        """Aggiorna lo stato delle autoclavi"""
        try:
            cursor.execute("""
                UPDATE autoclavi 
                SET stato = 'Disponibile' 
                WHERE stato != 'Guasto'
            """)
            print("✅ Stato autoclavi aggiornato")
        except Exception as e:
            print(f"⚠️  Errore aggiornamento autoclavi: {str(e)}")
    
    def test_odl_availability(self) -> bool:
        """Testa la disponibilità di ODL per il nesting"""
        self.print_step(2, "VERIFICA ODL DISPONIBILI")
        
        try:
            response = self.session.get(f"{BASE_URL}/odl", params={"status": "Attesa Cura"})
            if response.status_code == 200:
                odl_data = response.json()
                print(f"✅ {len(odl_data)} ODL in 'Attesa Cura' disponibili")
                
                if len(odl_data) >= 2:
                    self.test_results["odl_availability"] = True
                    return True
                else:
                    print("⚠️  Servono almeno 2 ODL per il test nesting")
                    return False
            else:
                print(f"❌ Errore API ODL: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Errore test ODL: {str(e)}")
            return False
    
    def test_autoclave_availability(self) -> bool:
        """Testa la disponibilità di autoclavi"""
        self.print_step(3, "VERIFICA AUTOCLAVI DISPONIBILI")
        
        try:
            response = self.session.get(f"{BASE_URL}/autoclavi")
            if response.status_code == 200:
                autoclave_data = response.json()
                disponibili = [a for a in autoclave_data if a.get('stato') == 'Disponibile']
                
                print(f"✅ {len(disponibili)} autoclavi disponibili su {len(autoclave_data)} totali")
                
                if len(disponibili) >= 1:
                    self.test_results["autoclave_availability"] = True
                    return True
                else:
                    print("⚠️  Nessuna autoclave disponibile per il nesting")
                    return False
            else:
                print(f"❌ Errore API autoclavi: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Errore test autoclavi: {str(e)}")
            return False
    
    def test_nesting_generation(self) -> Optional[str]:
        """Testa la generazione del nesting"""
        self.print_step(4, "TEST GENERAZIONE NESTING")
        
        try:
            # Ottieni ODL disponibili
            odl_response = self.session.get(f"{BASE_URL}/odl", params={"status": "Attesa Cura", "limit": 3})
            if odl_response.status_code != 200:
                print("❌ Impossibile ottenere ODL")
                return None
                
            odl_data = odl_response.json()
            if len(odl_data) < 2:
                print("❌ ODL insufficienti per il test")
                return None
            
            # Ottieni autoclavi disponibili
            autoclave_response = self.session.get(f"{BASE_URL}/autoclavi")
            if autoclave_response.status_code != 200:
                print("❌ Impossibile ottenere autoclavi")
                return None
                
            autoclave_data = autoclave_response.json()
            disponibili = [a for a in autoclave_data if a.get('stato') == 'Disponibile']
            
            if not disponibili:
                print("❌ Nessuna autoclave disponibile")
                return None
            
            # Prepara richiesta nesting
            nesting_request = {
                "odl_ids": [str(odl["id"]) for odl in odl_data[:2]],
                "autoclave_ids": [str(disponibili[0]["id"])],
                "parametri": {
                    "padding_mm": 20,
                    "min_distance_mm": 15,
                    "priorita_area": True
                }
            }
            
            print(f"📤 Generazione nesting con {len(nesting_request['odl_ids'])} ODL...")
            
            # Esegui nesting
            nesting_response = self.session.post(f"{BASE_URL}/nesting/genera", json=nesting_request)
            
            if nesting_response.status_code == 200:
                result = nesting_response.json()
                print(f"✅ Nesting generato con successo!")
                print(f"  📦 Batch ID: {result.get('batch_id', 'N/A')}")
                print(f"  📊 Tool posizionati: {len(result.get('positioned_tools', []))}")
                print(f"  📊 ODL esclusi: {len(result.get('excluded_odls', []))}")
                print(f"  📊 Efficienza: {result.get('efficiency', 0):.1f}%")
                
                if result.get('success'):
                    self.test_results["nesting_generation"] = True
                    return result.get('batch_id')
                else:
                    print("⚠️  Nesting generato ma senza successo")
                    return None
            else:
                print(f"❌ Errore generazione nesting: {nesting_response.status_code}")
                print(f"    {nesting_response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Errore test nesting: {str(e)}")
            return None
    
    def test_batch_loading(self, batch_id: str) -> bool:
        """Testa il caricamento di un batch"""
        self.print_step(5, "TEST CARICAMENTO BATCH")
        
        try:
            # Test endpoint base
            response = self.session.get(f"{BASE_URL}/batch_nesting/{batch_id}")
            if response.status_code == 200:
                batch_data = response.json()
                print(f"✅ Batch base caricato:")
                print(f"  📛 Nome: {batch_data.get('nome', 'N/A')}")
                print(f"  📊 Stato: {batch_data.get('stato', 'N/A')}")
                print(f"  📋 ODL: {len(batch_data.get('odl_ids', []))}")
            else:
                print(f"❌ Errore caricamento batch base: {response.status_code}")
                return False
            
            # Test endpoint full
            full_response = self.session.get(f"{BASE_URL}/batch_nesting/{batch_id}/full")
            if full_response.status_code == 200:
                full_data = full_response.json()
                config = full_data.get('configurazione_json', {})
                tools = config.get('tool_positions', []) if config else []
                
                print(f"✅ Batch completo caricato:")
                print(f"  🔧 Tool posizionati: {len(tools)}")
                print(f"  📏 Canvas: {config.get('canvas_width', 0)}x{config.get('canvas_height', 0)}mm")
                print(f"  🏭 Autoclave: {full_data.get('autoclave', {}).get('nome', 'N/A')}")
                
                if tools:
                    self.test_results["batch_loading"] = True
                    return True
                else:
                    print("⚠️  Batch caricato ma senza tool posizionati")
                    return False
            else:
                print(f"❌ Errore caricamento batch full: {full_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Errore test caricamento: {str(e)}")
            return False
    
    def create_robust_test_batch(self) -> Optional[str]:
        """Crea un batch di test robusto con dati garantiti"""
        self.print_step(6, "CREAZIONE BATCH TEST ROBUSTO")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Ottieni dati reali dal database
            cursor.execute("""
                SELECT o.id, p.part_number, p.descrizione_breve, t.part_number_tool,
                       t.larghezza_piano, t.lunghezza_piano, t.peso
                FROM odl o
                JOIN parti p ON o.parte_id = p.id  
                JOIN tools t ON o.tool_id = t.id
                WHERE o.status = 'Attesa Cura'
                LIMIT 3
            """)
            odl_data = cursor.fetchall()
            
            cursor.execute("""
                SELECT id, nome, larghezza_piano, lunghezza
                FROM autoclavi 
                WHERE stato = 'Disponibile'
                LIMIT 1
            """)
            autoclave_data = cursor.fetchone()
            
            if len(odl_data) < 2 or not autoclave_data:
                print("❌ Dati insufficienti per creare batch test")
                return None
            
            # Genera batch_id e dati
            batch_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Calcola posizioni tool ottimizzate
            autoclave_width = autoclave_data[2]  # larghezza_piano
            autoclave_height = autoclave_data[3]  # lunghezza
            
            tool_positions = []
            current_x = 50
            current_y = 50
            
            for i, (odl_id, part_number, desc, tool_name, width, height, peso) in enumerate(odl_data[:2]):
                tool_positions.append({
                    "odl_id": odl_id,
                    "x": current_x,
                    "y": current_y,
                    "width": width or 200,
                    "height": height or 150,
                    "peso": peso or 5.0,
                    "rotated": False,
                    "part_number": part_number,
                    "descrizione": desc,
                    "tool_nome": tool_name
                })
                
                current_x += (width or 200) + 30
                if current_x > autoclave_width - 200:
                    current_x = 50
                    current_y += (height or 150) + 30
            
            # Configurazione JSON completa
            configurazione_json = {
                "canvas_width": float(autoclave_width),
                "canvas_height": float(autoclave_height),
                "scale_factor": 1.0,
                "tool_positions": tool_positions,
                "plane_assignments": {str(tp["odl_id"]): 1 for tp in tool_positions}
            }
            
            # Parametri nesting
            parametri = {
                "padding_mm": 20.0,
                "min_distance_mm": 15.0,
                "priorita_area": True,
                "accorpamento_odl": False,
                "use_secondary_plane": False,
                "max_weight_per_plane_kg": None
            }
            
            # Calcola statistiche
            total_weight = sum(tp["peso"] for tp in tool_positions)
            total_area = sum(tp["width"] * tp["height"] for tp in tool_positions)
            efficiency = (total_area / (autoclave_width * autoclave_height)) * 100
            
            # Inserisci batch nel database
            cursor.execute("""
                INSERT INTO batch_nesting (
                    id, nome, stato, autoclave_id, odl_ids, configurazione_json,
                    parametri, numero_nesting, peso_totale_kg, area_totale_utilizzata,
                    valvole_totali_utilizzate, note, creato_da_utente, creato_da_ruolo,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id,
                f"Test Robusto {timestamp}",
                'sospeso',
                autoclave_data[0],  # autoclave_id
                json.dumps([tp["odl_id"] for tp in tool_positions]),
                json.dumps(configurazione_json),
                json.dumps(parametri),
                1,
                total_weight,
                total_area / 10000,  # cm²
                len(tool_positions),
                f"Batch test robusto con {len(tool_positions)} tool posizionati. Efficienza: {efficiency:.1f}%",
                "test_robustness",
                "Curing",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Batch test robusto creato:")
            print(f"  📦 ID: {batch_id}")
            print(f"  🔧 Tool posizionati: {len(tool_positions)}")
            print(f"  ⚖️ Peso totale: {total_weight:.1f} kg")
            print(f"  📊 Efficienza: {efficiency:.1f}%")
            
            return batch_id
            
        except Exception as e:
            print(f"❌ Errore creazione batch test: {str(e)}")
            return None
    
    def test_frontend_integration(self, batch_id: str) -> bool:
        """Testa l'integrazione frontend simulando le chiamate"""
        self.print_step(7, "TEST INTEGRAZIONE FRONTEND")
        
        try:
            # Simula le chiamate che fa il frontend
            print("📡 Simulazione chiamate frontend...")
            
            # 1. Caricamento pagina risultato
            response = self.session.get(f"{BASE_URL}/batch_nesting/{batch_id}/full")
            if response.status_code != 200:
                print(f"❌ Fallimento caricamento dati: {response.status_code}")
                return False
            
            data = response.json()
            config = data.get('configurazione_json', {})
            tools = config.get('tool_positions', [])
            
            if not tools:
                print("❌ Nessun tool posizionato nel batch")
                return False
            
            print(f"✅ Frontend può caricare {len(tools)} tool posizionati")
            
            # 2. Test conferma batch (simulazione)
            print("🔄 Test chiamata conferma...")
            confirm_response = self.session.patch(
                f"{BASE_URL}/batch_nesting/{batch_id}/conferma",
                params={
                    "confermato_da_utente": "test_user",
                    "confermato_da_ruolo": "Curing"
                }
            )
            
            if confirm_response.status_code == 200:
                print("✅ Conferma batch funziona correttamente")
                self.test_results["frontend_integration"] = True
                return True
            else:
                print(f"⚠️  Conferma batch ha problemi: {confirm_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Errore test frontend: {str(e)}")
            return False
    
    def generate_summary_report(self):
        """Genera un report riassuntivo dei test"""
        self.print_header("REPORT RIASSUNTIVO TEST ROBUSTEZZA")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"📊 RISULTATI: {passed_tests}/{total_tests} test superati")
        print(f"{'='*60}")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        # Raccomandazioni
        print(f"\n🔧 RACCOMANDAZIONI:")
        if not self.test_results["database_health"]:
            print("  - Verificare connessione e struttura database")
        if not self.test_results["nesting_generation"]:
            print("  - Controllare parametri algoritmo nesting")
        if not self.test_results["batch_loading"]:
            print("  - Verificare serializzazione dati batch")
        if not self.test_results["frontend_integration"]:
            print("  - Testare manualmente l'interfaccia frontend")
        
        if passed_tests == total_tests:
            print("\n🎉 SISTEMA NESTING COMPLETAMENTE FUNZIONALE!")
        else:
            print(f"\n⚠️  SISTEMA PARZIALMENTE FUNZIONALE ({passed_tests}/{total_tests})")
    
    def run_comprehensive_test(self):
        """Esegue tutti i test di robustezza"""
        self.print_header("TEST ROBUSTEZZA MODULO NESTING")
        print("Analisi completa end-to-end del sistema...")
        
        # Test 1: Database
        if not self.check_database_health():
            print("❌ Test interrotto - problemi database")
            return
        
        # Test 2: ODL
        if not self.test_odl_availability():
            print("❌ Test interrotto - ODL non disponibili")
            return
        
        # Test 3: Autoclavi
        if not self.test_autoclave_availability():
            print("❌ Test interrotto - autoclavi non disponibili")
            return
        
        # Test 4: Generazione nesting
        batch_id = self.test_nesting_generation()
        if not batch_id:
            print("⚠️  Generazione nesting fallita - creazione batch test...")
            batch_id = self.create_robust_test_batch()
        
        if not batch_id:
            print("❌ Impossibile creare batch per i test")
            return
        
        # Test 5: Caricamento batch
        self.test_batch_loading(batch_id)
        
        # Test 6: Integrazione frontend
        self.test_frontend_integration(batch_id)
        
        # Report finale
        self.generate_summary_report()
        
        print(f"\n🔗 BATCH TEST CREATO: {batch_id}")
        print(f"   Frontend URL: http://localhost:3001/dashboard/curing/nesting/result/{batch_id}")

def main():
    """Funzione principale"""
    try:
        tester = NestingRobustnessTest()
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 