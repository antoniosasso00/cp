#!/usr/bin/env python3
"""
Test stress per l'algoritmo di nesting aeronautico.

Analizza:
- Performance con 45 ODL aeronautici
- Gestione vincoli cicli di cura
- Efficienza spaziale e temporale
- Bottleneck e aree di miglioramento
- Scalabilità dell'algoritmo

Utilizzo:
    python backend/scripts/stress_test_nesting.py
"""

import sys
import os
import time
import psutil
import tracemalloc
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from statistics import mean, median, stdev

# Aggiungi il path del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.odl import ODL
from models.autoclave import Autoclave
from models.ciclo_cura import CicloCura
from services.nesting_service import NestingService

# Configurazione database - usa lo stesso path del backend
backend_dir = Path(__file__).parent.parent
db_path = backend_dir / "carbonpilot.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class NestingStressTest:
    """Test stress per algoritmo di nesting aeronautico"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.results = []
        self.performance_data = []
        self.memory_usage = []
        
    def cleanup(self):
        """Pulizia risorse"""
        if self.session:
            self.session.close()
    
    def get_system_info(self):
        """Informazioni sistema per il test"""
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        return {
            "cpu_cores": cpu_count,
            "cpu_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2)
        }
    
    def load_test_data(self):
        """Carica i dati di test dal database"""
        print("📊 Caricamento dati di test...")
        
        odls = self.session.query(ODL).filter(ODL.status == "Attesa Cura").all()
        autoclavi = self.session.query(Autoclave).all()
        cicli_cura = self.session.query(CicloCura).all()
        
        print(f"   • ODL disponibili: {len(odls)}")
        print(f"   • Autoclavi disponibili: {len(autoclavi)}")
        print(f"   • Cicli di cura: {len(cicli_cura)}")
        
        # Analisi distribuzione tool
        tool_sizes = []
        tool_ratios = []
        tool_weights = []
        
        for odl in odls:
            if odl.tool:
                tool_sizes.append(odl.tool.lunghezza_piano * odl.tool.larghezza_piano)
                tool_ratios.append(odl.tool.lunghezza_piano / odl.tool.larghezza_piano)
                if odl.tool.peso:
                    tool_weights.append(odl.tool.peso)
        
        print(f"\n🔧 Analisi tools:")
        print(f"   • Area min/max: {min(tool_sizes):.0f} - {max(tool_sizes):.0f} mm²")
        print(f"   • Aspect ratio min/max: {min(tool_ratios):.1f} - {max(tool_ratios):.1f}")
        if tool_weights:
            print(f"   • Peso min/max: {min(tool_weights):.1f} - {max(tool_weights):.1f} kg")
        
        return odls, autoclavi, cicli_cura
    
    def analyze_cure_cycle_constraints(self, odls, cicli_cura):
        """Analizza i vincoli dei cicli di cura"""
        print("\n🔄 Analisi vincoli cicli di cura...")
        
        # Raggruppa ODL per ciclo di cura
        cicli_distribution = {}
        for odl in odls:
            if odl.parte and odl.parte.ciclo_cura_id:
                ciclo_id = odl.parte.ciclo_cura_id
                if ciclo_id not in cicli_distribution:
                    cicli_distribution[ciclo_id] = []
                cicli_distribution[ciclo_id].append(odl)
        
        print(f"   • Cicli di cura utilizzati: {len(cicli_distribution)}")
        
        for ciclo_id, odl_group in cicli_distribution.items():
            ciclo = self.session.query(CicloCura).filter(CicloCura.id == ciclo_id).first()
            if ciclo:
                print(f"     - {ciclo.nome}: {len(odl_group)} ODL")
                print(f"       Temp: {ciclo.temperatura_stasi1}°C, Pressione: {ciclo.pressione_stasi1} bar")
        
        return cicli_distribution
    
    def test_single_autoclave_performance(self, autoclave, odl_subset, test_name):
        """Test performance su singola autoclave"""
        print(f"\n⚡ Test: {test_name}")
        print(f"   Autoclave: {autoclave.nome} ({autoclave.lunghezza}x{autoclave.larghezza_piano}mm)")
        print(f"   ODL da testare: {len(odl_subset)}")
        
        # Preparazione parametri
        parametri = {
            "padding_mm": 5.0,
            "min_distance_mm": 10.0,
            "enable_rotation": True,
            "algorithm": "aerospace"
        }
        
        # Misura memory e tempo
        tracemalloc.start()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Crea il servizio di nesting
            nesting_service = NestingService(self.session)
            
            # Estrai solo gli ID degli ODL
            odl_ids = [odl.id for odl in odl_subset]
            
            # Esegui il nesting
            result = nesting_service.generate_nesting(
                odl_ids=odl_ids,
                autoclave_id=autoclave.id,
                parameters=parametri
            )
            
            # Misure finali
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            peak_memory_mb = peak / 1024 / 1024
            
            # Estrai metriche dal risultato
            efficiency = 0.0
            positioned_tools = 0
            algorithm_used = "unknown"
            
            if result and hasattr(result, 'configurazione_json') and result.configurazione_json:
                config = result.configurazione_json
                efficiency = config.get('efficiency_percentage', 0.0)
                positioned_tools = len(config.get('positioned_tools', []))
                algorithm_used = config.get('algorithm', 'unknown')
            
            # Salva i risultati
            test_result = {
                "test_name": test_name,
                "autoclave_name": autoclave.nome,
                "autoclave_area": autoclave.lunghezza * autoclave.larghezza_piano,
                "odl_count": len(odl_subset),
                "execution_time_s": round(execution_time, 3),
                "memory_used_mb": round(memory_used, 2),
                "peak_memory_mb": round(peak_memory_mb, 2),
                "efficiency_percentage": round(efficiency, 2),
                "positioned_tools": positioned_tools,
                "success_rate": (positioned_tools / len(odl_subset)) * 100 if odl_subset else 0,
                "algorithm_used": algorithm_used,
                "tools_per_second": round(len(odl_subset) / execution_time, 2) if execution_time > 0 else 0
            }
            
            self.results.append(test_result)
            
            print(f"   ✅ Risultati:")
            print(f"     • Tempo esecuzione: {execution_time:.3f}s")
            print(f"     • Memoria utilizzata: {memory_used:.2f} MB (picco: {peak_memory_mb:.2f} MB)")
            print(f"     • Efficienza spazio: {efficiency:.2f}%")
            print(f"     • Tool posizionati: {positioned_tools}/{len(odl_subset)} ({test_result['success_rate']:.1f}%)")
            print(f"     • Performance: {test_result['tools_per_second']:.2f} tool/sec")
            print(f"     • Algoritmo utilizzato: {algorithm_used}")
            
            return test_result
            
        except Exception as e:
            print(f"   ❌ Errore durante il test: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            
            # Comunque registra il fallimento
            test_result = {
                "test_name": test_name,
                "autoclave_name": autoclave.nome,
                "odl_count": len(odl_subset),
                "execution_time_s": time.time() - start_time,
                "error": str(e),
                "success": False
            }
            self.results.append(test_result)
            return test_result
    
    def run_scalability_tests(self, odls, autoclavi):
        """Test di scalabilità con numero crescente di ODL"""
        print("\n📈 Test di scalabilità...")
        
        # Test con sottogruppi di ODL crescenti
        test_sizes = [5, 10, 15, 25, 35, 45]
        autoclave = autoclavi[0]  # Usa la prima autoclave per coerenza
        
        for size in test_sizes:
            if size <= len(odls):
                odl_subset = odls[:size]
                self.test_single_autoclave_performance(
                    autoclave, 
                    odl_subset, 
                    f"Scalabilità {size} ODL"
                )
    
    def run_autoclave_comparison(self, odls, autoclavi):
        """Confronta performance tra diverse autoclavi"""
        print("\n🏭 Confronto performance autoclavi...")
        
        # Usa un sottoinsieme fisso di ODL per confronto equo
        odl_subset = odls[:20]  # Primi 20 ODL
        
        for autoclave in autoclavi:
            self.test_single_autoclave_performance(
                autoclave,
                odl_subset,
                f"Confronto autoclavi - {autoclave.nome}"
            )
    
    def run_algorithm_stress_test(self, odls, autoclavi):
        """Test stress specifico dell'algoritmo"""
        print("\n🔥 Test stress algoritmo...")
        
        # Test casi estremi
        autoclave = max(autoclavi, key=lambda a: a.lunghezza * a.larghezza_piano)  # Più grande
        
        # Test 1: Tutti gli ODL insieme
        self.test_single_autoclave_performance(
            autoclave,
            odls,
            "Stress Test - Tutti gli ODL"
        )
        
        # Test 2: ODL con tool più grandi (più complessi)
        large_odls = [odl for odl in odls if odl.tool and 
                     (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) > 500000]  # > 0.5 m²
        if large_odls:
            self.test_single_autoclave_performance(
                autoclave,
                large_odls,
                "Stress Test - Tool grandi"
            )
        
        # Test 3: ODL con aspect ratio estremi
        extreme_ratio_odls = [odl for odl in odls if odl.tool and 
                            (odl.tool.lunghezza_piano / odl.tool.larghezza_piano) > 5.0]
        if extreme_ratio_odls:
            self.test_single_autoclave_performance(
                autoclave,
                extreme_ratio_odls,
                "Stress Test - Aspect ratio estremi"
            )
    
    def analyze_bottlenecks(self):
        """Analizza i bottleneck identificati nei test"""
        print("\n🔍 Analisi bottleneck e criticità...")
        
        if not self.results:
            print("   ⚠️ Nessun risultato disponibile per l'analisi")
            return
        
        # Filtra solo i test riusciti
        successful_tests = [r for r in self.results if r.get('success', True)]
        
        if not successful_tests:
            print("   ❌ Nessun test riuscito per l'analisi")
            return
        
        # Analisi tempi di esecuzione
        execution_times = [r['execution_time_s'] for r in successful_tests]
        memory_usage = [r['memory_used_mb'] for r in successful_tests]
        efficiency_rates = [r['efficiency_percentage'] for r in successful_tests]
        success_rates = [r['success_rate'] for r in successful_tests]
        
        print(f"   📊 Statistiche performance ({len(successful_tests)} test):")
        print(f"     • Tempo esecuzione:")
        print(f"       - Media: {mean(execution_times):.3f}s")
        print(f"       - Mediana: {median(execution_times):.3f}s")
        print(f"       - Min/Max: {min(execution_times):.3f}s / {max(execution_times):.3f}s")
        if len(execution_times) > 1:
            print(f"       - Deviazione std: {stdev(execution_times):.3f}s")
        
        print(f"     • Utilizzo memoria:")
        print(f"       - Media: {mean(memory_usage):.2f} MB")
        print(f"       - Picco massimo: {max(memory_usage):.2f} MB")
        
        print(f"     • Efficienza spaziale:")
        print(f"       - Media: {mean(efficiency_rates):.2f}%")
        print(f"       - Migliore: {max(efficiency_rates):.2f}%")
        
        print(f"     • Tasso di successo posizionamento:")
        print(f"       - Media: {mean(success_rates):.1f}%")
        print(f"       - Minimo: {min(success_rates):.1f}%")
        
        # Identifica i test più problematici
        slow_tests = [r for r in successful_tests if r['execution_time_s'] > mean(execution_times) + stdev(execution_times)]
        if slow_tests:
            print(f"\n   ⚠️ Test più lenti del normale ({len(slow_tests)}):")
            for test in slow_tests:
                print(f"     • {test['test_name']}: {test['execution_time_s']:.3f}s")
        
        memory_heavy_tests = [r for r in successful_tests if r['memory_used_mb'] > mean(memory_usage) + (stdev(memory_usage) if len(memory_usage) > 1 else 0)]
        if memory_heavy_tests:
            print(f"\n   🧠 Test con alto uso memoria ({len(memory_heavy_tests)}):")
            for test in memory_heavy_tests:
                print(f"     • {test['test_name']}: {test['memory_used_mb']:.2f} MB")
        
        low_efficiency_tests = [r for r in successful_tests if r['efficiency_percentage'] < mean(efficiency_rates) - (stdev(efficiency_rates) if len(efficiency_rates) > 1 else 0)]
        if low_efficiency_tests:
            print(f"\n   📉 Test con bassa efficienza ({len(low_efficiency_tests)}):")
            for test in low_efficiency_tests:
                print(f"     • {test['test_name']}: {test['efficiency_percentage']:.2f}%")
    
    def generate_recommendations(self):
        """Genera raccomandazioni per miglioramenti"""
        print("\n💡 Raccomandazioni per miglioramenti...")
        
        if not self.results:
            print("   ⚠️ Nessun dato per generare raccomandazioni")
            return
        
        successful_tests = [r for r in self.results if r.get('success', True)]
        
        # Analisi performance
        if successful_tests:
            avg_time = mean([r['execution_time_s'] for r in successful_tests])
            avg_efficiency = mean([r['efficiency_percentage'] for r in successful_tests])
            avg_success_rate = mean([r['success_rate'] for r in successful_tests])
            
            print(f"   📊 Performance attuale:")
            print(f"     • Tempo medio: {avg_time:.3f}s")
            print(f"     • Efficienza media: {avg_efficiency:.2f}%")
            print(f"     • Successo posizionamento: {avg_success_rate:.1f}%")
            
            recommendations = []
            
            # Raccomandazioni basate sui risultati
            if avg_time > 10.0:
                recommendations.append("⚡ PERFORMANCE: Ottimizzare algoritmo per ridurre tempi >10s")
            
            if avg_efficiency < 60.0:
                recommendations.append("📐 EFFICIENZA: Migliorare algoritmo packing per >60% efficienza")
            
            if avg_success_rate < 90.0:
                recommendations.append("🎯 SUCCESSO: Implementare strategie fallback per migliorare posizionamento")
            
            # Analisi memoria
            max_memory = max([r.get('memory_used_mb', 0) for r in successful_tests])
            if max_memory > 500:  # >500MB
                recommendations.append("🧠 MEMORIA: Ottimizzare uso memoria (attualmente >500MB)")
            
            # Raccomandazioni specifiche
            recommendations.extend([
                "🔄 ALGORITMO: Implementare caching per configurazioni simili",
                "⚙️ PARAMETRI: Test automatico parametri ottimali per diversi tipi tool",
                "🏭 AUTOCLAVI: Pre-calcolo matrici di compatibilità autoclave-tool",
                "📊 MONITORING: Sistema di monitoring performance in produzione",
                "🔀 PARALLELIZZAZIONE: Valutare nesting parallelo per autoclavi multiple"
            ])
            
            print(f"\n   🎯 Raccomandazioni prioritarie:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"     {i}. {rec}")
            
            if len(recommendations) > 5:
                print(f"     ... e altre {len(recommendations)-5} raccomandazioni")
        
        # Raccomandazioni basate su errori
        failed_tests = [r for r in self.results if not r.get('success', True)]
        if failed_tests:
            print(f"\n   ❌ Test falliti ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"     • {test['test_name']}: {test.get('error', 'Errore sconosciuto')}")
            
            print(f"\n   🔧 Raccomandazioni per robustezza:")
            print(f"     • Implementare gestione errori più robusta")
            print(f"     • Aggiungere validazione parametri di input")
            print(f"     • Timeout configurabili per evitare blocchi")
    
    def save_results_to_file(self):
        """Salva i risultati su file per analisi future"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nesting_stress_test_{timestamp}.json"
        
        import json
        report = {
            "timestamp": timestamp,
            "system_info": self.get_system_info(),
            "test_results": self.results,
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r.get('success', True)]),
                "failed_tests": len([r for r in self.results if not r.get('success', True)])
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Risultati salvati in: {filename}")
        except Exception as e:
            print(f"\n❌ Errore nel salvataggio: {e}")
    
    def run_complete_stress_test(self):
        """Esegue il test stress completo"""
        print("🚀 AVVIO TEST STRESS NESTING AERONAUTICO")
        print("=" * 60)
        
        # Info sistema
        system_info = self.get_system_info()
        print(f"💻 Sistema di test:")
        print(f"   • CPU cores: {system_info['cpu_cores']} ({system_info['cpu_logical']} logical)")
        print(f"   • Memoria: {system_info['memory_available_gb']:.1f}GB disponibile / {system_info['memory_total_gb']:.1f}GB totale")
        
        try:
            # Carica dati
            odls, autoclavi, cicli_cura = self.load_test_data()
            
            if not odls:
                print("❌ Nessun ODL trovato per il test!")
                return
            
            if not autoclavi:
                print("❌ Nessuna autoclave trovata per il test!")
                return
            
            # Analisi vincoli cicli di cura
            self.analyze_cure_cycle_constraints(odls, cicli_cura)
            
            # Esegui i test
            self.run_scalability_tests(odls, autoclavi)
            self.run_autoclave_comparison(odls, autoclavi)
            self.run_algorithm_stress_test(odls, autoclavi)
            
            # Analisi risultati
            self.analyze_bottlenecks()
            self.generate_recommendations()
            
            # Salva risultati
            self.save_results_to_file()
            
            print("\n" + "=" * 60)
            print("✅ TEST STRESS COMPLETATO CON SUCCESSO!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Errore durante il test stress: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        finally:
            self.cleanup()

def main():
    """Funzione principale"""
    test = NestingStressTest()
    test.run_complete_stress_test()

if __name__ == "__main__":
    main() 