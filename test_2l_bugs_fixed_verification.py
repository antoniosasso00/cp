#!/usr/bin/env python3
"""
🧪 TEST VERIFICA RISOLUZIONE BUG 2L NESTING
===========================================

Script per verificare che entrambi i bug del sistema 2L siano stati risolti:
1. BUG #1: Minimo 2 cavalletti sempre rispettato
2. BUG #2: Tutti i risultati visualizzati correttamente

Autore: CarbonPilot Development Team
Data: Dicembre 2024
"""

import sys
import json
import requests
import time
from typing import Dict, List, Any

# Configurazione
BACKEND_URL = "http://localhost:8000"
TEST_ODL_IDS = [5, 6, 7, 8]  # ODL di test
TEST_AUTOCLAVE_2L_ID = 1  # Autoclave con supporto 2L

class Test2LBugsFixer:
    """Tester per verifica risoluzione bug 2L nesting"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        
    def test_bug_1_minimum_cavalletti(self) -> Dict[str, Any]:
        """
        🧪 TEST BUG #1: Verifica minimo 2 cavalletti sempre rispettato
        """
        print("\n🧪 TEST BUG #1: Verifica minimo 2 cavalletti sempre rispettato")
        print("=" * 60)
        
        test_result = {
            "test_name": "BUG #1 - Minimo 2 Cavalletti",
            "success": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Test configurazione con force_minimum_two=True (default)
            request_data = {
                "autoclavi_2l": [TEST_AUTOCLAVE_2L_ID],
                "odl_ids": TEST_ODL_IDS,
                "parametri": {
                    "padding_mm": 10,
                    "min_distance_mm": 8
                },
                "use_cavalletti": True,
                "prefer_base_level": False,
                "cavalletti_config": {
                    "min_distance_from_edge": 30.0,
                    "max_span_without_support": 400.0,
                    "min_distance_between_cavalletti": 200.0,
                    "safety_margin_x": 5.0,
                    "safety_margin_y": 5.0,
                    "prefer_symmetric": True,
                    "force_minimum_two": True  # ✅ CRITICO: Deve essere True
                }
            }
            
            print(f"📤 Invio richiesta 2L multi con force_minimum_two=True...")
            response = requests.post(
                f"{self.backend_url}/api/batch_nesting/2l-multi",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Risposta ricevuta, analisi cavalletti...")
                
                # Analizza ogni batch generato
                cavalletti_analysis = []
                for batch_result in data.get('batch_results', []):
                    batch_id = batch_result.get('batch_id')
                    
                    # Recupera dettagli batch
                    batch_response = requests.get(
                        f"{self.backend_url}/api/batch_nesting/result/{batch_id}",
                        timeout=30
                    )
                    
                    if batch_response.status_code == 200:
                        batch_data = batch_response.json()
                        configurazione = batch_data.get('configurazione_json', {})
                        cavalletti = configurazione.get('cavalletti', [])
                        
                        # Analizza cavalletti per ogni tool
                        cavalletti_per_tool = {}
                        for cavalletto in cavalletti:
                            odl_id = cavalletto.get('tool_odl_id')
                            if odl_id not in cavalletti_per_tool:
                                cavalletti_per_tool[odl_id] = []
                            cavalletti_per_tool[odl_id].append(cavalletto)
                        
                        # Verifica minimo 2 cavalletti per ogni tool livello 1
                        positioned_tools = configurazione.get('positioned_tools', [])
                        for tool in positioned_tools:
                            if tool.get('level') == 1:  # Tool su cavalletti
                                odl_id = tool.get('odl_id')
                                num_cavalletti = len(cavalletti_per_tool.get(odl_id, []))
                                
                                analysis = {
                                    'odl_id': odl_id,
                                    'batch_id': batch_id,
                                    'num_cavalletti': num_cavalletti,
                                    'tool_width': tool.get('width'),
                                    'tool_height': tool.get('height'),
                                    'compliant': num_cavalletti >= 2
                                }
                                cavalletti_analysis.append(analysis)
                                
                                if num_cavalletti >= 2:
                                    print(f"  ✅ ODL {odl_id}: {num_cavalletti} cavalletti (CONFORME)")
                                else:
                                    print(f"  ❌ ODL {odl_id}: {num_cavalletti} cavalletti (NON CONFORME!)")
                
                test_result['details'] = cavalletti_analysis
                
                # Verifica se tutti i tool hanno almeno 2 cavalletti
                non_compliant = [a for a in cavalletti_analysis if not a['compliant']]
                
                if len(non_compliant) == 0:
                    test_result['success'] = True
                    print(f"\n🎉 BUG #1 RISOLTO: Tutti i tool hanno minimo 2 cavalletti!")
                else:
                    test_result['success'] = False
                    test_result['errors'] = [f"ODL {nc['odl_id']} ha solo {nc['num_cavalletti']} cavalletti" for nc in non_compliant]
                    print(f"\n❌ BUG #1 NON RISOLTO: {len(non_compliant)} tool non conformi")
                
            else:
                test_result['errors'].append(f"HTTP {response.status_code}: {response.text}")
                print(f"❌ Errore richiesta: {response.status_code}")
                
        except Exception as e:
            test_result['errors'].append(str(e))
            print(f"❌ Errore durante test: {e}")
        
        return test_result
    
    def test_bug_2_visualization_data(self) -> Dict[str, Any]:
        """
        🧪 TEST BUG #2: Verifica che tutti i risultati vengano visualizzati correttamente
        """
        print("\n🧪 TEST BUG #2: Verifica visualizzazione risultati corretta")
        print("=" * 60)
        
        test_result = {
            "test_name": "BUG #2 - Visualizzazione Risultati",
            "success": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Genera batch 2L per test
            request_data = {
                "autoclavi_2l": [TEST_AUTOCLAVE_2L_ID],
                "odl_ids": TEST_ODL_IDS,
                "parametri": {
                    "padding_mm": 10,
                    "min_distance_mm": 8
                },
                "use_cavalletti": True,
                "prefer_base_level": False
            }
            
            print(f"📤 Generazione batch 2L per test visualizzazione...")
            response = requests.post(
                f"{self.backend_url}/api/batch_nesting/2l-multi",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                visualization_checks = []
                
                for batch_result in data.get('batch_results', []):
                    batch_id = batch_result.get('batch_id')
                    
                    # Recupera dati batch per visualizzazione
                    batch_response = requests.get(
                        f"{self.backend_url}/api/batch_nesting/result/{batch_id}",
                        timeout=30
                    )
                    
                    if batch_response.status_code == 200:
                        batch_data = batch_response.json()
                        configurazione = batch_data.get('configurazione_json', {})
                        
                        # Verifica presenza campi essenziali per visualizzazione
                        check = {
                            'batch_id': batch_id,
                            'has_positioned_tools': 'positioned_tools' in configurazione,
                            'has_positioned_tools_data': 'positioned_tools_data' in configurazione,
                            'has_cavalletti': 'cavalletti' in configurazione,
                            'has_autoclave_info': 'autoclave_info' in configurazione,
                            'has_canvas_dimensions': all(k in configurazione for k in ['canvas_width', 'canvas_height']),
                            'has_level_counts': all(k in configurazione for k in ['level_0_count', 'level_1_count']),
                            'positioned_tools_count': 0,
                            'tool_data_complete': True
                        }
                        
                        # Verifica completezza dati positioned_tools
                        positioned_tools = configurazione.get('positioned_tools', [])
                        check['positioned_tools_count'] = len(positioned_tools)
                        
                        for tool in positioned_tools:
                            required_fields = ['odl_id', 'x', 'y', 'width', 'height', 'level']
                            missing_fields = [f for f in required_fields if f not in tool]
                            if missing_fields:
                                check['tool_data_complete'] = False
                                check.setdefault('missing_fields', []).extend(missing_fields)
                        
                        visualization_checks.append(check)
                        
                        # Log risultati
                        print(f"  📊 Batch {batch_id}:")
                        print(f"     • positioned_tools: {check['has_positioned_tools']}")
                        print(f"     • positioned_tools_data: {check['has_positioned_tools_data']}")
                        print(f"     • cavalletti: {check['has_cavalletti']}")
                        print(f"     • canvas_dimensions: {check['has_canvas_dimensions']}")
                        print(f"     • tool_count: {check['positioned_tools_count']}")
                        print(f"     • data_complete: {check['tool_data_complete']}")
                
                test_result['details'] = visualization_checks
                
                # Verifica se tutti i controlli passano
                all_checks_pass = all(
                    check['has_positioned_tools'] and 
                    check['has_positioned_tools_data'] and
                    check['has_cavalletti'] and
                    check['has_canvas_dimensions'] and
                    check['tool_data_complete'] and
                    check['positioned_tools_count'] > 0
                    for check in visualization_checks
                )
                
                if all_checks_pass:
                    test_result['success'] = True
                    print(f"\n🎉 BUG #2 RISOLTO: Tutti i dati per visualizzazione sono presenti e completi!")
                else:
                    test_result['success'] = False
                    failed_checks = [c for c in visualization_checks if not (
                        c['has_positioned_tools'] and c['has_positioned_tools_data'] and
                        c['has_cavalletti'] and c['has_canvas_dimensions'] and c['tool_data_complete']
                    )]
                    test_result['errors'] = [f"Batch {c['batch_id']} ha controlli falliti" for c in failed_checks]
                    print(f"\n❌ BUG #2 NON RISOLTO: {len(failed_checks)} batch con dati incompleti")
            
            else:
                test_result['errors'].append(f"HTTP {response.status_code}: {response.text}")
                print(f"❌ Errore generazione batch: {response.status_code}")
                
        except Exception as e:
            test_result['errors'].append(str(e))
            print(f"❌ Errore durante test: {e}")
        
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        🚀 Esegue tutti i test di verifica bug fix
        """
        print("🚀 AVVIO TEST VERIFICA RISOLUZIONE BUG 2L NESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # Test BUG #1
        test1_result = self.test_bug_1_minimum_cavalletti()
        self.test_results.append(test1_result)
        
        # Test BUG #2
        test2_result = self.test_bug_2_visualization_data()
        self.test_results.append(test2_result)
        
        # Risultati finali
        elapsed_time = time.time() - start_time
        
        successes = sum(1 for t in self.test_results if t['success'])
        total_tests = len(self.test_results)
        
        final_result = {
            "overall_success": successes == total_tests,
            "tests_passed": successes,
            "total_tests": total_tests,
            "elapsed_time_seconds": elapsed_time,
            "test_details": self.test_results
        }
        
        print(f"\n🏁 RISULTATI FINALI TEST 2L BUG FIX")
        print("=" * 50)
        print(f"✅ Test superati: {successes}/{total_tests}")
        print(f"⏱️ Tempo totale: {elapsed_time:.2f}s")
        
        if final_result['overall_success']:
            print(f"\n🎉 TUTTI I BUG 2L SONO STATI RISOLTI CON SUCCESSO!")
            print(f"   • BUG #1 (Minimo 2 cavalletti): {'✅ RISOLTO' if test1_result['success'] else '❌ NON RISOLTO'}")
            print(f"   • BUG #2 (Visualizzazione): {'✅ RISOLTO' if test2_result['success'] else '❌ NON RISOLTO'}")
        else:
            print(f"\n⚠️ ALCUNI BUG NON SONO ANCORA COMPLETAMENTE RISOLTI")
            for test in self.test_results:
                if not test['success']:
                    print(f"   ❌ {test['test_name']}: {test['errors']}")
        
        return final_result

def main():
    """Entry point dello script"""
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Output JSON per automazione
        tester = Test2LBugsFixer()
        result = tester.run_all_tests()
        print(json.dumps(result, indent=2))
    else:
        # Output human-readable
        tester = Test2LBugsFixer()
        result = tester.run_all_tests()
        
        # Salva report dettagliato
        with open('test_2l_bugs_fixed_report.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📄 Report dettagliato salvato in: test_2l_bugs_fixed_report.json")

if __name__ == "__main__":
    main() 