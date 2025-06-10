#!/usr/bin/env python3
"""
🚀 SISTEMA TEST AVANZATO NESTING ALGORITHM OPTIMIZATION
Test completo per miglioramenti algoritmo di nesting con focus su:
- Efficienza rotazioni (90° e 45°)
- Timeout ottimale 
- Algoritmi aerospace-grade
- Performance metrics detailed
"""

import sys
import os
import time
import json
import math
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# Aggiungi il path di backend al PYTHONPATH
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from services.nesting.solver import (
    NestingModel, NestingParameters, ToolInfo, AutoclaveInfo, 
    NestingSolution, NestingLayout
)

@dataclass
class TestCase:
    """Caso di test per valutazione algoritmo"""
    name: str
    description: str
    tools: List[ToolInfo]
    autoclave: AutoclaveInfo
    expected_min_efficiency: float = 50.0
    complexity_level: str = "MEDIUM"  # SIMPLE, MEDIUM, COMPLEX, EXTREME

@dataclass 
class TestResult:
    """Risultato dettagliato di un test"""
    test_name: str
    algorithm_status: str
    success: bool
    positioned_count: int
    total_count: int
    efficiency_score: float
    area_usage_pct: float
    execution_time_ms: float
    rotation_used: bool
    fallback_used: bool
    timeout_reached: bool
    improvements_suggested: List[str]

class NestingTestSuite:
    """Suite di test completa per algoritmo nesting"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        
    def create_test_cases(self) -> List[TestCase]:
        """Crea casi di test graduali per valutazione algoritmo"""
        test_cases = []
        
        # 🔧 TEST 1: ULTRA-SEMPLICE - Verifica funzionamento base
        simple_tools = [
            ToolInfo(odl_id=1, width=100, height=80, weight=2.0, lines_needed=1),
            ToolInfo(odl_id=2, width=120, height=90, weight=3.0, lines_needed=1),
        ]
        simple_autoclave = AutoclaveInfo(id=1, width=500, height=400, max_weight=100, max_lines=10)
        test_cases.append(TestCase(
            name="ULTRA_SIMPLE",
            description="2 pezzi piccoli in autoclave grande - test base",
            tools=simple_tools,
            autoclave=simple_autoclave,
            expected_min_efficiency=80.0,
            complexity_level="SIMPLE"
        ))
        
        # 🔧 TEST 2: ROTAZIONE CRITICA - ODL stretti che beneficiano rotazione
        rotation_tools = [
            ToolInfo(odl_id=3, width=300, height=50, weight=4.0, lines_needed=1),  # Molto stretto
            ToolInfo(odl_id=4, width=280, height=60, weight=5.0, lines_needed=2),  # Stretto
            ToolInfo(odl_id=5, width=200, height=80, weight=3.0, lines_needed=1),  # Normale
        ]
        rotation_autoclave = AutoclaveInfo(id=2, width=400, height=600, max_weight=50, max_lines=15)
        test_cases.append(TestCase(
            name="ROTATION_CRITICAL", 
            description="Pezzi stretti che richiedono rotazione intelligente",
            tools=rotation_tools,
            autoclave=rotation_autoclave,
            expected_min_efficiency=70.0,
            complexity_level="MEDIUM"
        ))
        
        # 🔧 TEST 3: EFFICIENZA ALTA - Molti pezzi per test compattazione
        efficiency_tools = []
        for i in range(8):
            efficiency_tools.append(ToolInfo(
                odl_id=10+i, 
                width=random.randint(80, 150), 
                height=random.randint(60, 120),
                weight=random.uniform(2.0, 8.0),
                lines_needed=random.randint(1, 3)
            ))
        efficiency_autoclave = AutoclaveInfo(id=3, width=800, height=600, max_weight=100, max_lines=25)
        test_cases.append(TestCase(
            name="HIGH_EFFICIENCY",
            description="8 pezzi misti per test efficienza compattazione",
            tools=efficiency_tools,
            autoclave=efficiency_autoclave,
            expected_min_efficiency=65.0,
            complexity_level="MEDIUM"
        ))
        
        # 🔧 TEST 4: VINCOLI STRINGENTI - Test limiti peso/linee vuoto
        constrained_tools = []
        for i in range(6):
            constrained_tools.append(ToolInfo(
                odl_id=20+i,
                width=random.randint(100, 200),
                height=random.randint(80, 150), 
                weight=15.0,  # Peso alto per test vincoli
                lines_needed=4   # Linee vuoto alte
            ))
        constrained_autoclave = AutoclaveInfo(id=4, width=600, height=500, max_weight=70, max_lines=18)
        test_cases.append(TestCase(
            name="CONSTRAINED_RESOURCES",
            description="Vincoli stringenti peso/linee vuoto",
            tools=constrained_tools,
            autoclave=constrained_autoclave, 
            expected_min_efficiency=45.0,
            complexity_level="COMPLEX"
        ))
        
        # 🔧 TEST 5: PERFORMANCE ESTREMA - Stress test per timeout
        extreme_tools = []
        for i in range(15):
            extreme_tools.append(ToolInfo(
                odl_id=30+i,
                width=random.randint(50, 300),
                height=random.randint(40, 250),
                weight=random.uniform(1.0, 12.0),
                lines_needed=random.randint(1, 4)
            ))
        extreme_autoclave = AutoclaveInfo(id=5, width=1000, height=800, max_weight=150, max_lines=40)
        test_cases.append(TestCase(
            name="EXTREME_PERFORMANCE",
            description="15 pezzi variabili - stress test performance",
            tools=extreme_tools,
            autoclave=extreme_autoclave,
            expected_min_efficiency=55.0,
            complexity_level="EXTREME"
        ))
        
        return test_cases
    
    def test_rotation_strategies(self, tools: List[ToolInfo], autoclave: AutoclaveInfo) -> Dict[str, TestResult]:
        """Test strategie di rotazione: Nessuna, 90°, 45° (sperimentale)"""
        results = {}
        
        # 🔄 TEST 90° STANDARD
        print("🔄 Test rotazione 90° standard...")
        params_90 = NestingParameters(
            enable_rotation_optimization=True,
            padding_mm=0.5,
            timeout_override=60
        )
        solver_90 = NestingModel(params_90)
        start_time = time.time()
        solution_90 = solver_90.solve(tools, autoclave)
        exec_time = (time.time() - start_time) * 1000
        
        results["rotation_90"] = TestResult(
            test_name="ROTATION_90_DEGREES",
            algorithm_status=solution_90.algorithm_status,
            success=solution_90.success,
            positioned_count=len(solution_90.layouts),
            total_count=len(tools),
            efficiency_score=solution_90.metrics.efficiency_score,
            area_usage_pct=solution_90.metrics.area_pct,
            execution_time_ms=exec_time,
            rotation_used=solution_90.metrics.rotation_used,
            fallback_used=solution_90.metrics.fallback_used,
            timeout_reached=exec_time > 59000,
            improvements_suggested=[]
        )
        
        # 🔄 TEST NESSUNA ROTAZIONE
        print("🔄 Test senza rotazione...")
        params_none = NestingParameters(
            enable_rotation_optimization=False,
            padding_mm=0.5,
            timeout_override=60
        )
        solver_none = NestingModel(params_none)
        start_time = time.time()
        solution_none = solver_none.solve(tools, autoclave)
        exec_time = (time.time() - start_time) * 1000
        
        results["no_rotation"] = TestResult(
            test_name="NO_ROTATION",
            algorithm_status=solution_none.algorithm_status,
            success=solution_none.success,
            positioned_count=len(solution_none.layouts),
            total_count=len(tools),
            efficiency_score=solution_none.metrics.efficiency_score,
            area_usage_pct=solution_none.metrics.area_pct,
            execution_time_ms=exec_time,
            rotation_used=False,
            fallback_used=solution_none.metrics.fallback_used,
            timeout_reached=exec_time > 59000,
            improvements_suggested=[]
        )
        
        # 🔄 TEST 45° SPERIMENTALE
        print("🔄 Test rotazione 45° sperimentale...")
        # Implementiamo un algoritmo sperimentale per rotazioni a 45°
        results["rotation_45"] = self._test_45_degree_rotation(tools, autoclave)
        
        return results
    
    def _test_45_degree_rotation(self, tools: List[ToolInfo], autoclave: AutoclaveInfo) -> TestResult:
        """Test sperimentale rotazioni a 45° - non implementato completamente"""
        start_time = time.time()
        
        # Per ora simuliamo il test con un approccio semplificato
        # La rotazione a 45° aumenta le dimensioni del bounding box
        # width_45 = width*cos(45°) + height*sin(45°) = (width + height) / √2
        # height_45 = width*sin(45°) + height*cos(45°) = (width + height) / √2
        
        positioned_count = 0
        total_area = 0
        sqrt2 = math.sqrt(2)
        
        for tool in tools:
            # Calcola dimensioni con rotazione a 45°
            diagonal_size = (tool.width + tool.height) / sqrt2
            
            # Verifica se entra nell'autoclave
            if diagonal_size <= min(autoclave.width, autoclave.height):
                positioned_count += 1
                # Area effettiva del pezzo (non del bounding box)
                total_area += tool.width * tool.height
        
        autoclave_area = autoclave.width * autoclave.height
        area_pct = (total_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        efficiency_score = area_pct * 0.8  # Efficienza ridotta per complessità 45°
        
        exec_time = (time.time() - start_time) * 1000
        
        improvements = []
        if positioned_count < len(tools):
            improvements.append("Rotazione 45° riduce capacità per complessità geometrica")
        if efficiency_score < 50:
            improvements.append("Algoritmo 45° richiede ottimizzazioni avanzate")
        
        return TestResult(
            test_name="ROTATION_45_EXPERIMENTAL",
            algorithm_status="EXPERIMENTAL_45_DEGREES",
            success=positioned_count > 0,
            positioned_count=positioned_count,
            total_count=len(tools),
            efficiency_score=efficiency_score,
            area_usage_pct=area_pct,
            execution_time_ms=exec_time,
            rotation_used=positioned_count > 0,
            fallback_used=False,
            timeout_reached=False,
            improvements_suggested=improvements
        )
    
    def test_timeout_optimization(self, tools: List[ToolInfo], autoclave: AutoclaveInfo) -> Dict[str, TestResult]:
        """Test diversi timeout per trovare l'ottimale"""
        timeout_tests = [30, 60, 120, 300, 600]  # Secondi
        results = {}
        
        for timeout in timeout_tests:
            print(f"⏱️ Test timeout {timeout}s...")
            
            params = NestingParameters(
                timeout_override=timeout,
                enable_rotation_optimization=True,
                use_multithread=True,
                num_search_workers=8,
                use_grasp_heuristic=True
            )
            
            solver = NestingModel(params)
            start_time = time.time()
            solution = solver.solve(tools, autoclave)
            exec_time = (time.time() - start_time) * 1000
            
            improvements = []
            if exec_time < timeout * 800:  # Se termina prima dell'80% del timeout
                improvements.append(f"Timeout {timeout}s sovrabbondante - può essere ridotto")
            elif exec_time >= timeout * 950:  # Se va in timeout
                improvements.append(f"Timeout {timeout}s insufficiente - aumentare")
            else:
                improvements.append(f"Timeout {timeout}s ottimale per questo caso")
            
            results[f"timeout_{timeout}s"] = TestResult(
                test_name=f"TIMEOUT_{timeout}S",
                algorithm_status=solution.algorithm_status,
                success=solution.success,
                positioned_count=len(solution.layouts),
                total_count=len(tools),
                efficiency_score=solution.metrics.efficiency_score,
                area_usage_pct=solution.metrics.area_pct,
                execution_time_ms=exec_time,
                rotation_used=solution.metrics.rotation_used,
                fallback_used=solution.metrics.fallback_used,
                timeout_reached=exec_time >= timeout * 950,
                improvements_suggested=improvements
            )
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Esegue test completo dell'algoritmo di nesting"""
        print("🚀 === AVVIO TEST SUITE ALGORITMO NESTING ===\n")
        
        test_cases = self.create_test_cases()
        all_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"📋 TEST CASE {i}/5: {test_case.name}")
            print(f"   📝 {test_case.description}")
            print(f"   🎯 Target efficienza minima: {test_case.expected_min_efficiency}%")
            print(f"   📊 Complessità: {test_case.complexity_level}")
            print(f"   🔧 Tools: {len(test_case.tools)}, Autoclave: {test_case.autoclave.width}x{test_case.autoclave.height}mm\n")
            
            case_results = {}
            
            # Test rotazioni
            print("   🔄 Testing strategie di rotazione...")
            rotation_results = self.test_rotation_strategies(test_case.tools, test_case.autoclave)
            case_results["rotations"] = rotation_results
            
            # Test timeout solo sui casi complessi per risparmiare tempo
            if test_case.complexity_level in ["COMPLEX", "EXTREME"]:
                print("   ⏱️ Testing timeout optimization...")
                timeout_results = self.test_timeout_optimization(test_case.tools, test_case.autoclave)
                case_results["timeouts"] = timeout_results
            
            all_results[test_case.name] = case_results
            print()
        
        return all_results
    
    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analisi completa dei risultati per identificare migliorie"""
        print("📊 === ANALISI RISULTATI E RACCOMANDAZIONI ===\n")
        
        analysis = {
            "rotation_analysis": {},
            "timeout_analysis": {},
            "efficiency_trends": {},
            "recommendations": []
        }
        
        # Analisi rotazioni
        rotation_benefits = []
        for test_name, test_data in results.items():
            if "rotations" in test_data:
                rot_data = test_data["rotations"]
                
                # Confronta efficienza con/senza rotazione
                eff_90 = rot_data.get("rotation_90", {}).efficiency_score if hasattr(rot_data.get("rotation_90", {}), 'efficiency_score') else 0
                eff_none = rot_data.get("no_rotation", {}).efficiency_score if hasattr(rot_data.get("no_rotation", {}), 'efficiency_score') else 0
                eff_45 = rot_data.get("rotation_45", {}).efficiency_score if hasattr(rot_data.get("rotation_45", {}), 'efficiency_score') else 0
                
                benefit_90 = eff_90 - eff_none
                benefit_45 = eff_45 - eff_none
                
                rotation_benefits.append({
                    "test": test_name,
                    "benefit_90": benefit_90,
                    "benefit_45": benefit_45,
                    "best_strategy": "90°" if benefit_90 > benefit_45 else "45°" if benefit_45 > 0 else "Nessuna"
                })
        
        analysis["rotation_analysis"] = {
            "avg_benefit_90": sum(r["benefit_90"] for r in rotation_benefits) / len(rotation_benefits) if rotation_benefits else 0,
            "avg_benefit_45": sum(r["benefit_45"] for r in rotation_benefits) / len(rotation_benefits) if rotation_benefits else 0,
            "tests_benefiting_rotation": len([r for r in rotation_benefits if r["benefit_90"] > 5])
        }
        
        # Raccomandazioni
        recommendations = []
        
        if analysis["rotation_analysis"]["avg_benefit_90"] > 10:
            recommendations.append("✅ Rotazione 90° molto benefica - mantenere abilitata di default")
        elif analysis["rotation_analysis"]["avg_benefit_90"] > 5:
            recommendations.append("🟡 Rotazione 90° moderatamente benefica - abilitare per casi complessi")
        else:
            recommendations.append("🟠 Rotazione 90° poco benefica - valutare disabilitazione per performance")
        
        if analysis["rotation_analysis"]["avg_benefit_45"] > 5:
            recommendations.append("🔬 Rotazione 45° mostra potenziale - implementazione completa raccomandata")
        else:
            recommendations.append("❌ Rotazione 45° non giustificata - focus su ottimizzazioni 90°")
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    def print_detailed_report(self, results: Dict[str, Any], analysis: Dict[str, Any]):
        """Stampa report dettagliato dei risultati"""
        print("📈 === REPORT DETTAGLIATO PERFORMANCE ===\n")
        
        for test_name, test_data in results.items():
            print(f"🧪 TEST: {test_name}")
            
            if "rotations" in test_data:
                print("   📊 ROTAZIONI:")
                for rot_type, rot_result in test_data["rotations"].items():
                    if hasattr(rot_result, 'efficiency_score'):
                        print(f"      {rot_type}: {rot_result.efficiency_score:.1f}% efficienza, {rot_result.positioned_count} pezzi")
            
            if "timeouts" in test_data:
                print("   ⏱️ TIMEOUT:")
                best_timeout = None
                best_efficiency = 0
                for timeout_type, timeout_result in test_data["timeouts"].items():
                    if hasattr(timeout_result, 'efficiency_score'):
                        if timeout_result.efficiency_score > best_efficiency:
                            best_efficiency = timeout_result.efficiency_score
                            best_timeout = timeout_type
                        print(f"      {timeout_type}: {timeout_result.efficiency_score:.1f}% efficienza")
                if best_timeout:
                    print(f"      🏆 Migliore: {best_timeout}")
            
            print()
        
        print("🎯 === RACCOMANDAZIONI IMPLEMENTAZIONE ===")
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"{i}. {rec}")

def main():
    """Funzione principale per eseguire i test"""
    print("🚀 CarbonPilot Nesting Algorithm Optimization Suite")
    print("=" * 60)
    
    suite = NestingTestSuite()
    
    try:
        # Esegui test completo
        results = suite.run_comprehensive_test()
        
        # Analizza risultati
        analysis = suite.analyze_results(results)
        
        # Stampa report
        suite.print_detailed_report(results, analysis)
        
        # Salva risultati su file JSON per analisi successive
        output_file = "nesting_test_results.json"
        with open(output_file, 'w') as f:
            # Converti risultati in formato serializzabile
            serializable_results = {}
            for test_name, test_data in results.items():
                serializable_results[test_name] = {}
                for category, category_data in test_data.items():
                    serializable_results[test_name][category] = {}
                    for subtest, result in category_data.items():
                        if hasattr(result, '__dict__'):
                            serializable_results[test_name][category][subtest] = asdict(result)
                        else:
                            serializable_results[test_name][category][subtest] = result
            
            json.dump({
                "results": serializable_results,
                "analysis": analysis,
                "timestamp": time.time()
            }, f, indent=2)
        
        print(f"\n💾 Risultati salvati in: {output_file}")
        print("\n✅ TEST SUITE COMPLETATA CON SUCCESSO!")
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 