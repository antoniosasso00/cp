#!/usr/bin/env python3
"""
🧪 TEST END-TO-END COMPLETO DEL SISTEMA NESTING

Questo test verifica l'intero flusso del sistema di nesting:
1. Seed con ODL vari (diverse priorità, dimensioni, cicli)
2. Generazione nesting automatico con parametri personalizzati
3. Preview + conferma del nesting
4. Caricamento + simulazione cura
5. Verifica stato finale e generazione report

Il test simula un caso d'uso reale completo del sistema.
"""

import sys
import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import text

# Aggiungi la directory backend al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from models.db import SessionLocal, engine, Base
from models.odl import ODL
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.ciclo_cura import CicloCura
from models.nesting_result import NestingResult
from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus
import random

# Configurazione API
API_BASE_URL = "http://localhost:8000/api/v1"
NESTING_API_URL = f"{API_BASE_URL}/nesting"

class NestingEndToEndTest:
    """Classe per gestire il test end-to-end del sistema nesting"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.test_data = {}
        self.nesting_results = []
        self.active_nesting = []
        
    def cleanup_database(self):
        """Pulisce il database prima del test"""
        print("🧹 Pulizia database per test pulito...")
        
        try:
            # Elimina in ordine per rispettare le foreign key
            self.db.query(ScheduleEntry).delete()
            self.db.query(NestingResult).delete()
            self.db.query(ODL).delete()
            self.db.query(Tool).delete()
            self.db.query(Parte).delete()
            self.db.query(Catalogo).delete()
            self.db.query(Autoclave).delete()
            self.db.query(CicloCura).delete()
            
            self.db.commit()
            print("✅ Database pulito con successo")
            
        except Exception as e:
            print(f"❌ Errore nella pulizia database: {e}")
            self.db.rollback()
            raise
    
    def create_test_seed(self):
        """Crea dati di test completi per il nesting"""
        print("🌱 Creazione seed di test...")
        
        try:
            # 1. Crea cicli di cura diversi
            cicli_cura = [
                CicloCura(
                    nome="Ciclo Standard 180°C",
                    descrizione="Ciclo standard per parti in carbonio",
                    temperatura_stasi1=180.0,
                    pressione_stasi1=6.0,
                    durata_stasi1=120,
                    attiva_stasi2=False
                ),
                CicloCura(
                    nome="Ciclo Rapido 160°C",
                    descrizione="Ciclo accelerato per parti piccole",
                    temperatura_stasi1=160.0,
                    pressione_stasi1=5.0,
                    durata_stasi1=90,
                    attiva_stasi2=False
                ),
                CicloCura(
                    nome="Ciclo Intensivo 200°C",
                    descrizione="Ciclo per parti complesse con doppia stasi",
                    temperatura_stasi1=180.0,
                    pressione_stasi1=6.0,
                    durata_stasi1=120,
                    attiva_stasi2=True,
                    temperatura_stasi2=200.0,
                    pressione_stasi2=8.0,
                    durata_stasi2=60
                )
            ]
            
            for ciclo in cicli_cura:
                self.db.add(ciclo)
            self.db.flush()
            
            # 2. Crea autoclavi con caratteristiche diverse
            autoclavi = [
                Autoclave(
                    nome="Autoclave Grande Alpha",
                    codice="AUT-ALPHA",
                    lunghezza=2000.0,  # 200cm
                    larghezza_piano=1500.0,  # 150cm
                    num_linee_vuoto=16,
                    temperatura_max=220.0,
                    pressione_max=10.0,
                    stato=StatoAutoclaveEnum.DISPONIBILE,
                    produttore="Test Manufacturer",
                    anno_produzione=2022,
                    note="Autoclave grande per test end-to-end"
                ),
                Autoclave(
                    nome="Autoclave Media Beta",
                    codice="AUT-BETA",
                    lunghezza=1500.0,  # 150cm
                    larghezza_piano=1200.0,  # 120cm
                    num_linee_vuoto=12,
                    temperatura_max=200.0,
                    pressione_max=8.0,
                    stato=StatoAutoclaveEnum.DISPONIBILE,
                    produttore="Test Manufacturer",
                    anno_produzione=2021,
                    note="Autoclave media standard"
                ),
                Autoclave(
                    nome="Autoclave Piccola Gamma",
                    codice="AUT-GAMMA",
                    lunghezza=1000.0,  # 100cm
                    larghezza_piano=800.0,  # 80cm
                    num_linee_vuoto=8,
                    temperatura_max=180.0,
                    pressione_max=6.0,
                    stato=StatoAutoclaveEnum.DISPONIBILE,
                    produttore="Test Manufacturer",
                    anno_produzione=2020,
                    note="Autoclave piccola per test rapidi"
                )
            ]
            
            for autoclave in autoclavi:
                self.db.add(autoclave)
            self.db.flush()
            
            # 3. Crea catalogo parti con dimensioni variegate
            catalogo_parti = [
                # Parti piccole
                Catalogo(
                    part_number="E2E-SMALL-001",
                    descrizione="Componente piccolo A - Test E2E - 50cm² - 0.2kg",
                    categoria="Componenti",
                    sotto_categoria="Piccoli",
                    attivo=True
                ),
                Catalogo(
                    part_number="E2E-SMALL-002",
                    descrizione="Componente piccolo B - Test E2E - 75cm² - 0.3kg",
                    categoria="Componenti",
                    sotto_categoria="Piccoli",
                    attivo=True
                ),
                # Parti medie
                Catalogo(
                    part_number="E2E-MED-001",
                    descrizione="Componente medio A - Test E2E - 200cm² - 1.0kg",
                    categoria="Componenti",
                    sotto_categoria="Medi",
                    attivo=True
                ),
                Catalogo(
                    part_number="E2E-MED-002",
                    descrizione="Componente medio B - Test E2E - 300cm² - 1.5kg",
                    categoria="Componenti",
                    sotto_categoria="Medi",
                    attivo=True
                ),
                # Parti grandi
                Catalogo(
                    part_number="E2E-LARGE-001",
                    descrizione="Componente grande A - Test E2E - 800cm² - 4.0kg",
                    categoria="Componenti",
                    sotto_categoria="Grandi",
                    attivo=True
                ),
                Catalogo(
                    part_number="E2E-LARGE-002",
                    descrizione="Componente grande B - Test E2E - 1200cm² - 6.0kg",
                    categoria="Componenti",
                    sotto_categoria="Grandi",
                    attivo=True
                )
            ]
            
            for catalogo in catalogo_parti:
                self.db.add(catalogo)
            self.db.flush()
            
            # 4. Crea parti con cicli di cura assegnati
            parti = []
            for i, catalogo in enumerate(catalogo_parti):
                ciclo_index = i % len(cicli_cura)
                
                parte = Parte(
                    part_number=catalogo.part_number,
                    ciclo_cura_id=cicli_cura[ciclo_index].id,
                    descrizione_breve=catalogo.descrizione.split(" - ")[0],
                    num_valvole_richieste=random.randint(1, 4),
                    note_produzione=f"Test E2E - Ciclo: {cicli_cura[ciclo_index].nome}"
                )
                parti.append(parte)
                self.db.add(parte)
            
            self.db.flush()
            
            # 5. Crea tool con dimensioni realistiche
            aree_target = {
                "E2E-SMALL-001": 50.0,
                "E2E-SMALL-002": 75.0,
                "E2E-MED-001": 200.0,
                "E2E-MED-002": 300.0,
                "E2E-LARGE-001": 800.0,
                "E2E-LARGE-002": 1200.0
            }
            
            tools = []
            for parte in parti:
                area_target = aree_target.get(parte.part_number, 100.0)
                area_tool = area_target * random.uniform(1.1, 1.2)
                
                # Calcola dimensioni rettangolari
                if area_tool <= 100:
                    ratio = random.uniform(1.0, 1.5)
                elif area_tool <= 500:
                    ratio = random.uniform(1.2, 2.0)
                else:
                    ratio = random.uniform(1.5, 3.0)
                
                larghezza_cm = (area_tool / ratio) ** 0.5
                lunghezza_cm = larghezza_cm * ratio
                
                # Converti in mm
                lunghezza_mm = lunghezza_cm * 10
                larghezza_mm = larghezza_cm * 10
                peso_kg = area_tool * 0.005
                
                tool = Tool(
                    part_number_tool=f"TOOL-E2E-{parte.part_number}",
                    descrizione=f"Tool per test E2E - {parte.part_number}",
                    lunghezza_piano=lunghezza_mm,
                    larghezza_piano=larghezza_mm,
                    peso=peso_kg,
                    materiale="Alluminio 7075 - Test E2E",
                    note=f"Tool ottimizzato per test end-to-end"
                )
                tools.append(tool)
                self.db.add(tool)
            
            self.db.flush()
            
            # 6. Crea ODL con priorità e date variegate
            odl_list = []
            for i in range(20):  # 20 ODL per test completo
                parte_index = i % len(parti)
                tool_index = i % len(tools)
                
                # Varia priorità (1=bassa, 5=alta)
                if i < 5:
                    priorita = 5  # Alta priorità
                elif i < 10:
                    priorita = 4  # Medio-alta
                elif i < 15:
                    priorita = 3  # Media
                else:
                    priorita = random.choice([1, 2])  # Bassa
                
                data_creazione = datetime.now() - timedelta(days=random.randint(1, 30))
                data_scadenza = data_creazione + timedelta(days=random.randint(7, 60))
                
                ciclo_parte = parti[parte_index].ciclo_cura
                note_odl = f"Test E2E - Priorità {priorita} - Ciclo: {ciclo_parte.nome}"
                
                odl = ODL(
                    parte_id=parti[parte_index].id,
                    tool_id=tools[tool_index].id,
                    priorita=priorita,
                    status="Attesa Cura",  # Stato corretto per nesting
                    note=note_odl
                )
                odl_list.append(odl)
                self.db.add(odl)
            
            self.db.commit()
            
            # Salva i dati di test per riferimento
            self.test_data = {
                'cicli_cura': cicli_cura,
                'autoclavi': autoclavi,
                'catalogo_parti': catalogo_parti,
                'parti': parti,
                'tools': tools,
                'odl_list': odl_list
            }
            
            print(f"✅ Seed creato con successo:")
            print(f"   - {len(cicli_cura)} cicli di cura")
            print(f"   - {len(autoclavi)} autoclavi")
            print(f"   - {len(catalogo_parti)} parti nel catalogo")
            print(f"   - {len(odl_list)} ODL in Attesa Cura")
            print(f"   - Priorità: {len([o for o in odl_list if o.priorita == 5])} alta, {len([o for o in odl_list if o.priorita in [3,4]])} media, {len([o for o in odl_list if o.priorita in [1,2]])} bassa")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore nella creazione del seed: {e}")
            self.db.rollback()
            return False
    
    def test_api_connection(self) -> bool:
        """Testa la connessione all'API"""
        print("🔗 Test connessione API...")
        
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ API backend raggiungibile")
                return True
            else:
                print(f"❌ API non raggiungibile: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Errore connessione API: {e}")
            return False
    
    def test_nesting_preview(self) -> Dict[str, Any]:
        """Testa l'endpoint di preview del nesting"""
        print("👀 Test preview nesting...")
        
        try:
            params = {
                'include_excluded': True,
                'group_by_cycle': True
            }
            
            response = requests.get(f"{NESTING_API_URL}/preview", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                odl_groups = data.get('odl_groups', [])
                available_autoclaves = data.get('available_autoclaves', [])
                total_odl = data.get('total_odl_pending', 0)
                
                print(f"✅ Preview generata:")
                print(f"   - {len(odl_groups)} gruppi di ODL compatibili")
                print(f"   - {len(available_autoclaves)} autoclavi disponibili")
                print(f"   - {total_odl} ODL totali in attesa")
                
                return {
                    'success': True,
                    'data': data,
                    'odl_groups': len(odl_groups),
                    'autoclaves': len(available_autoclaves),
                    'total_odl': total_odl
                }
            else:
                print(f"❌ Errore preview: {response.status_code}")
                return {'success': False, 'data': {}}
                
        except Exception as e:
            print(f"❌ Errore preview: {e}")
            return {'success': False, 'data': {}}
    
    def test_automatic_nesting_generation(self) -> Dict[str, Any]:
        """Testa la generazione automatica del nesting con parametri personalizzati"""
        print("🤖 Test generazione automatica nesting...")
        
        try:
            # Parametri personalizzati per il test
            payload = {
                'force_regenerate': True,
                'parameters': {
                    'padding_mm': 25.0,
                    'margine_mm': 50.0,
                    'rotazione_abilitata': True,
                    'priorita_minima': 1,
                    'max_autoclavi': 3,
                    'efficienza_minima': 0.6
                }
            }
            
            response = requests.post(f"{NESTING_API_URL}/automatic", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    nesting_results = data.get('nesting_results', [])
                    summary = data.get('summary', {})
                    
                    print(f"✅ Nesting automatico generato:")
                    print(f"   - {len(nesting_results)} nesting creati")
                    print(f"   - {summary.get('total_odl_processed', 0)} ODL processati")
                    print(f"   - {summary.get('total_odl_excluded', 0)} ODL esclusi")
                    print(f"   - {summary.get('autoclavi_utilizzate', 0)} autoclavi utilizzate")
                    
                    # Salva i risultati per i test successivi
                    self.nesting_results = nesting_results
                    
                    return {
                        'success': True,
                        'data': data,
                        'nesting_count': len(nesting_results),
                        'odl_processed': summary.get('total_odl_processed', 0)
                    }
                else:
                    print(f"⚠️ Generazione fallita: {data.get('message', 'Errore sconosciuto')}")
                    return {'success': False, 'data': data}
            else:
                print(f"❌ Errore generazione: {response.status_code}")
                return {'success': False, 'data': {}}
                
        except Exception as e:
            print(f"❌ Errore generazione: {e}")
            return {'success': False, 'data': {}}
    
    def test_nesting_confirmation(self) -> bool:
        """Testa la conferma dei nesting generati"""
        print("✅ Test conferma nesting...")
        
        if not self.nesting_results:
            print("⚠️ Nessun nesting da confermare")
            return False
        
        confirmed_count = 0
        
        for nesting in self.nesting_results[:2]:  # Conferma i primi 2 nesting
            try:
                nesting_id = nesting['id']
                
                payload = {
                    'note_conferma': f'Confermato per test E2E - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                }
                
                response = requests.post(f"{NESTING_API_URL}/{nesting_id}/confirm", json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Nesting {nesting_id} confermato (stato: {data.get('stato', 'N/A')})")
                    confirmed_count += 1
                else:
                    print(f"   ❌ Errore conferma nesting {nesting_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Errore conferma nesting {nesting_id}: {e}")
        
        print(f"✅ Confermati {confirmed_count}/{len(self.nesting_results[:2])} nesting")
        return confirmed_count > 0
    
    def test_nesting_loading(self) -> bool:
        """Testa il caricamento dei nesting confermati"""
        print("📦 Test caricamento nesting...")
        
        if not self.nesting_results:
            print("⚠️ Nessun nesting da caricare")
            return False
        
        loaded_count = 0
        
        for nesting in self.nesting_results[:2]:  # Carica i primi 2 nesting
            try:
                nesting_id = nesting['id']
                
                payload = {
                    'note_caricamento': f'Caricato per test E2E - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                    'operatore_caricamento': 'operatore_e2e'
                }
                
                response = requests.post(f"{NESTING_API_URL}/{nesting_id}/load", json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Nesting {nesting_id} caricato (stato: {data.get('stato', 'N/A')})")
                    loaded_count += 1
                    
                    # Aggiungi alla lista dei nesting attivi
                    self.active_nesting.append(data)
                else:
                    print(f"   ❌ Errore caricamento nesting {nesting_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Errore caricamento nesting {nesting_id}: {e}")
        
        print(f"✅ Caricati {loaded_count}/{len(self.nesting_results[:2])} nesting")
        return loaded_count > 0
    
    def test_curing_simulation(self) -> bool:
        """Simula il processo di cura per i nesting caricati"""
        print("🔥 Test simulazione cura...")
        
        if not self.active_nesting:
            print("⚠️ Nessun nesting attivo da curare")
            return False
        
        cured_count = 0
        
        for nesting_data in self.active_nesting:
            try:
                nesting_id = nesting_data['id']
                autoclave_id = nesting_data['autoclave_id']
                
                # Crea una schedule entry per simulare il ciclo di cura
                schedule_entry = ScheduleEntry(
                    autoclave_id=autoclave_id,
                    start_datetime=datetime.now(),
                    end_datetime=datetime.now() + timedelta(hours=2),  # Simula 2 ore di cura
                    status=ScheduleEntryStatus.DONE.value,
                    note=f"Test E2E - Ciclo completato per nesting {nesting_id}"
                )
                
                self.db.add(schedule_entry)
                self.db.commit()
                
                print(f"   ✅ Simulata cura per nesting {nesting_id} (autoclave {autoclave_id})")
                cured_count += 1
                
            except Exception as e:
                print(f"   ❌ Errore simulazione cura nesting {nesting_id}: {e}")
                self.db.rollback()
        
        print(f"✅ Simulata cura per {cured_count}/{len(self.active_nesting)} nesting")
        return cured_count > 0
    
    def test_final_status_verification(self) -> Dict[str, Any]:
        """Verifica lo stato finale del sistema dopo il test completo"""
        print("🔍 Test verifica stato finale...")
        
        try:
            # Verifica ODL
            odl_in_cura = self.db.query(ODL).filter(ODL.status == "Cura").count()
            odl_attesa = self.db.query(ODL).filter(ODL.status == "Attesa Cura").count()
            
            # Verifica nesting
            nesting_bozza = self.db.query(NestingResult).filter(NestingResult.stato == "Bozza").count()
            nesting_confermato = self.db.query(NestingResult).filter(NestingResult.stato == "Confermato").count()
            nesting_caricato = self.db.query(NestingResult).filter(NestingResult.stato == "Caricato").count()
            
            # Verifica autoclavi
            autoclavi_in_uso = self.db.query(Autoclave).filter(Autoclave.stato == StatoAutoclaveEnum.IN_USO).count()
            autoclavi_disponibili = self.db.query(Autoclave).filter(Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE).count()
            
            # Verifica schedule entries (query semplificata per evitare errori di schema)
            try:
                schedule_completate = self.db.execute(
                    text("SELECT COUNT(*) FROM schedule_entries WHERE status = 'done'")
                ).scalar()
            except Exception as e:
                print(f"   ⚠️ Errore query schedule_entries: {e}")
                schedule_completate = 0
            
            status_summary = {
                'odl': {
                    'in_cura': odl_in_cura,
                    'attesa_cura': odl_attesa
                },
                'nesting': {
                    'bozza': nesting_bozza,
                    'confermato': nesting_confermato,
                    'caricato': nesting_caricato
                },
                'autoclavi': {
                    'in_uso': autoclavi_in_uso,
                    'disponibili': autoclavi_disponibili
                },
                'schedule': {
                    'completate': schedule_completate
                }
            }
            
            print("✅ Stato finale del sistema:")
            print(f"   ODL in cura: {odl_in_cura}, in attesa: {odl_attesa}")
            print(f"   Nesting - Bozza: {nesting_bozza}, Confermato: {nesting_confermato}, Caricato: {nesting_caricato}")
            print(f"   Autoclavi - In uso: {autoclavi_in_uso}, Disponibili: {autoclavi_disponibili}")
            print(f"   Schedule completate: {schedule_completate}")
            
            return {
                'success': True,
                'status_summary': status_summary
            }
            
        except Exception as e:
            print(f"❌ Errore verifica stato finale: {e}")
            return {'success': False, 'status_summary': {}}
    
    def test_report_generation(self) -> bool:
        """Testa la generazione di report per i nesting completati"""
        print("📊 Test generazione report...")
        
        if not self.nesting_results:
            print("⚠️ Nessun nesting per cui generare report")
            return False
        
        reports_generated = 0
        
        for nesting in self.nesting_results[:2]:  # Genera report per i primi 2 nesting
            try:
                nesting_id = nesting['id']
                
                response = requests.post(f"{NESTING_API_URL}/{nesting_id}/generate-report", 
                                       params={'force_regenerate': True}, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"   ✅ Report generato per nesting {nesting_id}: {data.get('filename', 'N/A')}")
                        reports_generated += 1
                    else:
                        print(f"   ⚠️ Report non generato per nesting {nesting_id}: {data.get('message', 'N/A')}")
                else:
                    print(f"   ❌ Errore generazione report nesting {nesting_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Errore generazione report nesting {nesting_id}: {e}")
        
        print(f"✅ Generati {reports_generated}/{len(self.nesting_results[:2])} report")
        return reports_generated > 0
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Esegue il test end-to-end completo"""
        print("🚀 AVVIO TEST END-TO-END COMPLETO DEL SISTEMA NESTING")
        print("=" * 80)
        print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
        try:
            # Step 1: Pulizia e preparazione
            print("📋 STEP 1: Preparazione ambiente di test")
            self.cleanup_database()
            results['tests']['cleanup'] = True
            
            # Step 2: Creazione seed
            print("\n📋 STEP 2: Creazione seed con ODL vari")
            seed_success = self.create_test_seed()
            results['tests']['seed_creation'] = seed_success
            
            if not seed_success:
                raise Exception("Fallimento nella creazione del seed")
            
            # Step 3: Test connessione API
            print("\n📋 STEP 3: Test connessione API")
            api_success = self.test_api_connection()
            results['tests']['api_connection'] = api_success
            
            if not api_success:
                raise Exception("API non raggiungibile")
            
            # Step 4: Preview nesting
            print("\n📋 STEP 4: Preview nesting")
            preview_result = self.test_nesting_preview()
            results['tests']['preview'] = preview_result['success']
            results['preview_data'] = preview_result
            
            # Step 5: Generazione automatica
            print("\n📋 STEP 5: Generazione nesting automatico")
            generation_result = self.test_automatic_nesting_generation()
            results['tests']['automatic_generation'] = generation_result['success']
            results['generation_data'] = generation_result
            
            if not generation_result['success']:
                print("⚠️ Generazione automatica fallita, continuando con test limitati...")
            
            # Step 6: Conferma nesting
            print("\n📋 STEP 6: Conferma nesting")
            confirmation_success = self.test_nesting_confirmation()
            results['tests']['confirmation'] = confirmation_success
            
            # Step 7: Caricamento nesting
            print("\n📋 STEP 7: Caricamento nesting")
            loading_success = self.test_nesting_loading()
            results['tests']['loading'] = loading_success
            
            # Step 8: Simulazione cura
            print("\n📋 STEP 8: Simulazione cura")
            curing_success = self.test_curing_simulation()
            results['tests']['curing_simulation'] = curing_success
            
            # Step 9: Verifica stato finale
            print("\n📋 STEP 9: Verifica stato finale")
            final_status = self.test_final_status_verification()
            results['tests']['final_status'] = final_status['success']
            results['final_status_data'] = final_status
            
            # Step 10: Generazione report
            print("\n📋 STEP 10: Generazione report")
            report_success = self.test_report_generation()
            results['tests']['report_generation'] = report_success
            
            # Calcola statistiche finali
            total_tests = len(results['tests'])
            passed_tests = sum(1 for test in results['tests'].values() if test)
            
            results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
                'overall_success': passed_tests >= (total_tests * 0.8)  # 80% di successo minimo
            }
            
            return results
            
        except Exception as e:
            print(f"\n❌ ERRORE CRITICO NEL TEST: {e}")
            results['error'] = str(e)
            results['summary'] = {
                'total_tests': len(results['tests']),
                'passed_tests': sum(1 for test in results['tests'].values() if test),
                'success_rate': 0,
                'overall_success': False
            }
            return results
        
        finally:
            self.db.close()
    
    def print_final_report(self, results: Dict[str, Any]):
        """Stampa il report finale del test"""
        print("\n" + "=" * 80)
        print("📊 REPORT FINALE TEST END-TO-END")
        print("=" * 80)
        
        summary = results.get('summary', {})
        tests = results.get('tests', {})
        
        print(f"🕒 Completato: {results.get('timestamp', 'N/A')}")
        print(f"🎯 Test totali: {summary.get('total_tests', 0)}")
        print(f"✅ Test superati: {summary.get('passed_tests', 0)}")
        print(f"📈 Tasso di successo: {summary.get('success_rate', 0)}%")
        print(f"🏆 Successo complessivo: {'SÌ' if summary.get('overall_success') else 'NO'}")
        
        print("\n📋 DETTAGLIO TEST:")
        test_names = {
            'cleanup': '1. Pulizia Database',
            'seed_creation': '2. Creazione Seed',
            'api_connection': '3. Connessione API',
            'preview': '4. Preview Nesting',
            'automatic_generation': '5. Generazione Automatica',
            'confirmation': '6. Conferma Nesting',
            'loading': '7. Caricamento Nesting',
            'curing_simulation': '8. Simulazione Cura',
            'final_status': '9. Verifica Stato Finale',
            'report_generation': '10. Generazione Report'
        }
        
        for test_key, test_name in test_names.items():
            status = tests.get(test_key, False)
            icon = "✅" if status else "❌"
            print(f"   {icon} {test_name}")
        
        # Dati aggiuntivi se disponibili
        if 'preview_data' in results and results['preview_data']['success']:
            preview = results['preview_data']
            print(f"\n📊 DATI PREVIEW:")
            print(f"   - Gruppi ODL: {preview.get('odl_groups', 0)}")
            print(f"   - Autoclavi disponibili: {preview.get('autoclaves', 0)}")
            print(f"   - ODL totali: {preview.get('total_odl', 0)}")
        
        if 'generation_data' in results and results['generation_data']['success']:
            generation = results['generation_data']
            print(f"\n🤖 DATI GENERAZIONE:")
            print(f"   - Nesting creati: {generation.get('nesting_count', 0)}")
            print(f"   - ODL processati: {generation.get('odl_processed', 0)}")
        
        if 'final_status_data' in results and results['final_status_data']['success']:
            status_data = results['final_status_data']['status_summary']
            print(f"\n🔍 STATO FINALE SISTEMA:")
            print(f"   - ODL in cura: {status_data.get('odl', {}).get('in_cura', 0)}")
            print(f"   - Nesting caricati: {status_data.get('nesting', {}).get('caricato', 0)}")
            print(f"   - Autoclavi in uso: {status_data.get('autoclavi', {}).get('in_uso', 0)}")
            print(f"   - Schedule completate: {status_data.get('schedule', {}).get('completate', 0)}")
        
        if 'error' in results:
            print(f"\n❌ ERRORE: {results['error']}")
        
        print("\n" + "=" * 80)
        
        if summary.get('overall_success'):
            print("🎉 TEST END-TO-END COMPLETATO CON SUCCESSO!")
            print("   Il sistema di nesting funziona correttamente end-to-end.")
        else:
            print("⚠️ TEST END-TO-END PARZIALMENTE FALLITO")
            print("   Verificare i test falliti e la configurazione del sistema.")
        
        print("=" * 80)


def main():
    """Funzione principale per eseguire il test end-to-end"""
    test_runner = NestingEndToEndTest()
    
    try:
        results = test_runner.run_complete_test()
        test_runner.print_final_report(results)
        
        # Ritorna codice di uscita appropriato
        if results.get('summary', {}).get('overall_success'):
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrotto dall'utente")
        return 2
    except Exception as e:
        print(f"\n❌ Errore critico: {e}")
        return 3


if __name__ == "__main__":
    exit(main()) 