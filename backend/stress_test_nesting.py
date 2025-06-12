#!/usr/bin/env python3
"""
CarbonPilot - Stress Test Sistema Nesting
==========================================
Stress test completo per ottimizzare performance e identificare bottleneck
Obiettivo: 45+ ODL su 3 autoclavi in tempi ragionevoli con efficienza massima
"""

import time
import statistics
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Database e modelli
from api.database import get_db
from models.odl import ODL
from models.autoclave import Autoclave
from models.tool import Tool
from services.nesting_service import NestingService
from services.nesting.solver import NestingParameters

# Configurazione logging per lo stress test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NestingStressTest:
    """Classe per eseguire stress test completo sul sistema nesting"""
    
    def __init__(self):
        self.nesting_service = NestingService()
        self.results = []
        self.dataset_analysis = {}
        
    def analyze_dataset_complexity(self):
        """Analizza la complessità del dataset per stress test intelligenti"""
        logger.info("🔍 === ANALISI COMPLESSITÀ DATASET ===")
        
        db = next(get_db())
        try:
            # ===== ANALISI ODL =====
            odls = db.query(ODL).filter(ODL.status != 'Finito').all()
            logger.info(f"📋 ODL disponibili: {len(odls)}")
            
            if not odls:
                logger.warning("❌ Nessun ODL disponibile per stress test")
                return None
            
            # Analisi caratteristiche ODL
            odl_stats = {
                'total_count': len(odls),
                'statuses': {},
                'priorities': {},
                'complexity_factors': []
            }
            
            for odl in odls:
                # Conta stati
                status = odl.status
                odl_stats['statuses'][status] = odl_stats['statuses'].get(status, 0) + 1
                
                # Conta priorità
                priority = getattr(odl, 'priorita', 1)
                odl_stats['priorities'][priority] = odl_stats['priorities'].get(priority, 0) + 1
            
            # ===== ANALISI TOOL =====
            tools = db.query(Tool).join(ODL).filter(ODL.status != 'Finito').all()
            logger.info(f"🔧 Tool disponibili: {len(tools)}")
            
            if not tools:
                logger.warning("❌ Nessun tool disponibile per stress test")
                return None
                
            # Analisi dimensioni e caratteristiche tool
            areas = []
            weights = []
            aspect_ratios = []
            valid_tools_count = 0
            
            for tool in tools:
                try:
                    # Gestione campi tool corretti
                    if hasattr(tool, 'lunghezza_piano') and hasattr(tool, 'larghezza_piano'):
                        width = float(tool.lunghezza_piano or 0)
                        height = float(tool.larghezza_piano or 0)
                    else:
                        continue
                        
                    if width > 0 and height > 0:
                        area = width * height
                        areas.append(area)
                        aspect_ratios.append(max(width, height) / min(width, height))
                        valid_tools_count += 1
                        
                        # Peso 
                        weight = 0
                        if hasattr(tool, 'peso') and tool.peso:
                            weight = float(tool.peso)
                        
                        if weight > 0:
                            weights.append(weight)
                            
                except (ValueError, AttributeError, TypeError) as e:
                    logger.debug(f"Tool {tool.id} saltato per errore: {e}")
                    continue
            
            tool_stats = {
                'total_count': len(tools),
                'valid_count': valid_tools_count,
                'area_stats': {
                    'min': min(areas) if areas else 0,
                    'max': max(areas) if areas else 0,
                    'avg': statistics.mean(areas) if areas else 0,
                    'median': statistics.median(areas) if areas else 0
                },
                'weight_stats': {
                    'min': min(weights) if weights else 0,
                    'max': max(weights) if weights else 0,
                    'avg': statistics.mean(weights) if weights else 0,
                    'median': statistics.median(weights) if weights else 0,
                    'available_count': len(weights)
                },
                'aspect_ratio_stats': {
                    'min': min(aspect_ratios) if aspect_ratios else 0,
                    'max': max(aspect_ratios) if aspect_ratios else 0,
                    'avg': statistics.mean(aspect_ratios) if aspect_ratios else 0
                }
            }
            
            # ===== ANALISI AUTOCLAVI =====
            autoclavi = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()
            logger.info(f"🏭 Autoclavi disponibili: {len(autoclavi)}")
            
            autoclave_stats = {
                'total_count': len(autoclavi),
                'capacities': [],
                'sizes': []
            }
            
            for autoclave in autoclavi:
                try:
                    # Dimensioni autoclave
                    width = float(autoclave.lunghezza or 0)
                    height = float(autoclave.larghezza_piano or 0)
                    if width > 0 and height > 0:
                        autoclave_stats['sizes'].append({
                            'id': autoclave.id,
                            'nome': autoclave.nome,
                            'width': width,
                            'height': height,
                            'area': width * height,
                            'vacuum_lines': getattr(autoclave, 'num_linee_vuoto', 0)
                        })
                        
                    # Capacità peso
                    capacity = float(getattr(autoclave, 'max_load_kg', 0) or 0)
                    if capacity > 0:
                        autoclave_stats['capacities'].append(capacity)
                        
                except (ValueError, AttributeError, TypeError) as e:
                    logger.debug(f"Autoclave {autoclave.id} saltata per errore: {e}")
                    continue
            
            # ===== CALCOLO INDICI COMPLESSITÀ =====
            complexity_index = 0
            
            # Fattore 1: Numero tool per autoclave
            if autoclavi and valid_tools_count > 0:
                tools_per_autoclave = valid_tools_count / len(autoclavi)
                complexity_index += min(tools_per_autoclave / 10, 5)  # Max 5 punti
            
            # Fattore 2: Variabilità dimensioni tool
            if len(areas) > 1:
                area_cv = statistics.stdev(areas) / statistics.mean(areas)
                complexity_index += min(area_cv * 10, 3)  # Max 3 punti
            
            # Fattore 3: Aspect ratio estremi
            if aspect_ratios:
                max_aspect_ratio = max(aspect_ratios)
                complexity_index += min(max_aspect_ratio / 5, 2)  # Max 2 punti
            
            self.dataset_analysis = {
                'timestamp': datetime.now().isoformat(),
                'odl_stats': odl_stats,
                'tool_stats': tool_stats,
                'autoclave_stats': autoclave_stats,
                'complexity_index': complexity_index,
                'recommended_batch_sizes': self._calculate_recommended_batch_sizes(
                    valid_tools_count, len(autoclavi), complexity_index
                )
            }
            
            # Log risultati
            logger.info(f"📊 RISULTATI ANALISI:")
            logger.info(f"   🔧 Tool validi: {valid_tools_count}/{len(tools)}")
            logger.info(f"   📐 Area tool: {tool_stats['area_stats']['min']:.0f}-{tool_stats['area_stats']['max']:.0f}mm² (avg: {tool_stats['area_stats']['avg']:.0f})")
            logger.info(f"   ⚖️ Peso tool: {tool_stats['weight_stats']['available_count']} disponibili, {tool_stats['weight_stats']['min']:.1f}-{tool_stats['weight_stats']['max']:.1f}kg")
            logger.info(f"   📏 Aspect ratio: {tool_stats['aspect_ratio_stats']['min']:.1f}-{tool_stats['aspect_ratio_stats']['max']:.1f} (avg: {tool_stats['aspect_ratio_stats']['avg']:.1f})")
            logger.info(f"   🏭 Autoclavi: {len(autoclavi)} disponibili")
            if autoclave_stats['sizes']:
                for size in autoclave_stats['sizes']:
                    logger.info(f"      {size['nome']}: {size['width']:.0f}×{size['height']:.0f}mm ({size['area']:.0f}mm²)")
            logger.info(f"   🎯 Indice complessità: {complexity_index:.1f}/10")
            
            return self.dataset_analysis
            
        finally:
            db.close()
            
    def _calculate_recommended_batch_sizes(self, total_tools: int, num_autoclavi: int, complexity: float) -> List[int]:
        """Calcola dimensioni batch consigliate basate su complessità"""
        if total_tools == 0:
            return []
            
        # Dimensioni base per test progressivi
        base_sizes = [5, 10, 15, 20, 30]
        
        # Aggiusta per complessità
        if complexity > 7:  # Alta complessità
            base_sizes = [3, 5, 8, 12, 18]
        elif complexity < 3:  # Bassa complessità
            base_sizes = [10, 20, 30, 45, min(total_tools, 60)]
            
        # Filtra per dimensioni disponibili
        return [size for size in base_sizes if size <= total_tools]
    
    def run_performance_tests(self, parameter_sets: Optional[List[Dict]] = None):
        """Esegue test di performance con diversi set di parametri"""
        logger.info("🚀 === STRESS TEST PERFORMANCE ===")
        
        if not self.dataset_analysis:
            logger.error("❌ Eseguire prima analyze_dataset_complexity()")
            return None
            
        db = next(get_db())
        try:
            # Ottieni dati reali
            odl_ids = [odl.id for odl in db.query(ODL).filter(ODL.status != 'Finito').all()]
            autoclave_ids = [a.id for a in db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()]
            
            if not odl_ids or not autoclave_ids:
                logger.error("❌ Dataset insufficiente per test")
                return None
            
            # Set di parametri di default se non forniti
            if parameter_sets is None:
                parameter_sets = [
                    {'name': 'SPEED_OPTIMIZED', 'padding_mm': 5.0, 'min_distance_mm': 8.0, 'timeout_override': 30},
                    {'name': 'BALANCED', 'padding_mm': 10.0, 'min_distance_mm': 15.0, 'timeout_override': 60},
                    {'name': 'QUALITY_OPTIMIZED', 'padding_mm': 15.0, 'min_distance_mm': 20.0, 'timeout_override': 120},
                    {'name': 'AEROSPACE_GRADE', 'padding_mm': 0.5, 'min_distance_mm': 0.5, 'timeout_override': 300}
                ]
            
            # Dimensioni batch per test
            recommended_sizes = self.dataset_analysis['recommended_batch_sizes']
            test_sizes = recommended_sizes[:3] if len(recommended_sizes) >= 3 else recommended_sizes
            
            logger.info(f"🧪 Test con dimensioni batch: {test_sizes}")
            logger.info(f"⚙️ Set parametri: {[p['name'] for p in parameter_sets]}")
            
            test_results = []
            
            for param_set in parameter_sets:
                logger.info(f"\n🔧 Test parametri: {param_set['name']}")
                
                # Crea parametri nesting
                parameters = NestingParameters(
                    padding_mm=param_set['padding_mm'],
                    min_distance_mm=param_set['min_distance_mm'],
                    timeout_override=param_set.get('timeout_override'),
                    use_multithread=True,
                    num_search_workers=8,
                    use_grasp_heuristic=True,
                )
                
                param_results = {
                    'parameter_set': param_set,
                    'size_results': []
                }
                
                for size in test_sizes:
                    logger.info(f"   📊 Test dimensione: {size} ODL")
                    
                    # Seleziona subset di ODL
                    test_odl_subset = odl_ids[:size]
                    
                    # Esegui test
                    start_time = time.time()
                    result = self.nesting_service.generate_robust_nesting(
                        db, test_odl_subset, autoclave_ids, parameters
                    )
                    execution_time = time.time() - start_time
                    
                    # Analizza risultati
                    test_result = self._analyze_test_result(result, size, execution_time)
                    test_result['parameter_set'] = param_set['name']
                    
                    param_results['size_results'].append(test_result)
                    
                    # Log risultato
                    logger.info(f"      ✅ {test_result['batch_count']} batch, "
                              f"{test_result['total_positioned']}/{size} tool, "
                              f"{test_result['avg_efficiency']:.1f}% eff, "
                              f"{execution_time:.2f}s")
                
                test_results.append(param_results)
            
            self.results.extend(test_results)
            return test_results
            
        finally:
            db.close()
    
    def test_scalability(self, max_odls: Optional[int] = None):
        """Test di scalabilità con incremento graduale ODL"""
        logger.info("📈 === TEST SCALABILITÀ ===")
        
        if not self.dataset_analysis:
            logger.error("❌ Eseguire prima analyze_dataset_complexity()")
            return None
            
        db = next(get_db())
        try:
            # Ottieni dataset completo
            all_odl_ids = [odl.id for odl in db.query(ODL).filter(ODL.status != 'Finito').all()]
            autoclave_ids = [a.id for a in db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()]
            
            if not all_odl_ids or not autoclave_ids:
                logger.error("❌ Dataset insufficiente per test scalabilità")
                return None
            
            # Calcola dimensioni test
            max_test_size = max_odls or min(len(all_odl_ids), 45)  # Default 45 ODL
            step_size = max(1, max_test_size // 10)  # 10 punti di test
            test_sizes = list(range(5, max_test_size + 1, step_size))
            
            # Assicurati di includere il target massimo
            if max_test_size not in test_sizes:
                test_sizes.append(max_test_size)
            
            logger.info(f"🎯 Test scalabilità: {test_sizes}")
            
            # Parametri ottimizzati per scalabilità
            parameters = NestingParameters(
                padding_mm=8.0,
                min_distance_mm=12.0,
                timeout_override=None,  # Timeout dinamico
                use_multithread=True,
                num_search_workers=8,
                use_grasp_heuristic=True,
            )
            
            scalability_results = []
            
            for size in test_sizes:
                logger.info(f"\n📊 Test scalabilità: {size} ODL")
                
                # Timeout adattivo per scalabilità
                timeout = min(300, max(30, size * 3))  # 3s per ODL, max 5min
                parameters.timeout_override = timeout
                
                test_odl_subset = all_odl_ids[:size]
                
                start_time = time.time()
                result = self.nesting_service.generate_robust_nesting(
                    db, test_odl_subset, autoclave_ids, parameters
                )
                execution_time = time.time() - start_time
                
                # Analizza risultati
                test_result = self._analyze_test_result(result, size, execution_time)
                test_result['timeout_used'] = timeout
                test_result['time_per_odl'] = execution_time / size
                
                scalability_results.append(test_result)
                
                # Log progresso
                logger.info(f"   ✅ {test_result['batch_count']} batch generati")
                logger.info(f"   📈 {test_result['total_positioned']}/{size} tool posizionati ({test_result['utilization_rate']*100:.1f}%)")
                logger.info(f"   ⚡ {test_result['avg_efficiency']:.1f}% efficienza media")
                logger.info(f"   ⏱️ {execution_time:.2f}s totali ({test_result['time_per_odl']:.3f}s/ODL)")
                
                # Stop se timeout eccessivo
                if execution_time > 600:  # 10 minuti
                    logger.warning(f"⏰ Test interrotto: timeout eccessivo ({execution_time:.1f}s)")
                    break
            
            return scalability_results
            
        finally:
            db.close()
    
    def _analyze_test_result(self, result: Dict[str, Any], expected_size: int, execution_time: float) -> Dict[str, Any]:
        """Analizza un risultato di test e estrae metriche"""
        try:
            # Gestione formato risultato flessibile
            if result.get('success', False):
                # Multi-batch format
                if 'batches' in result and result['batches']:
                    batches = result['batches']
                    total_positioned = sum(batch.get('metrics', {}).get('positioned_count', 0) for batch in batches)
                    total_excluded = sum(batch.get('metrics', {}).get('excluded_count', 0) for batch in batches)
                    efficiencies = [batch.get('metrics', {}).get('area_pct', 0) for batch in batches]
                    algorithms = [batch.get('algorithm_status', 'UNKNOWN') for batch in batches]
                    
                elif 'best_result' in result:
                    # Single best result format
                    best = result['best_result']
                    total_positioned = best.get('metrics', {}).get('positioned_count', 0)
                    total_excluded = best.get('metrics', {}).get('excluded_count', 0)
                    efficiencies = [best.get('metrics', {}).get('area_pct', 0)]
                    algorithms = [best.get('algorithm_status', 'UNKNOWN')]
                    
                else:
                    # Direct format
                    total_positioned = result.get('positioned_count', 0)
                    total_excluded = result.get('excluded_count', expected_size - total_positioned)
                    efficiencies = [result.get('efficiency', 0)]
                    algorithms = [result.get('algorithm_status', 'UNKNOWN')]
                
                # Calcola metriche aggregate
                avg_efficiency = statistics.mean(efficiencies) if efficiencies else 0
                max_efficiency = max(efficiencies) if efficiencies else 0
                min_efficiency = min(efficiencies) if efficiencies else 0
                
                return {
                    'success': True,
                    'batch_count': len(result.get('batches', [])) if 'batches' in result else 1,
                    'total_positioned': total_positioned,
                    'total_excluded': total_excluded,
                    'expected_size': expected_size,
                    'utilization_rate': total_positioned / expected_size if expected_size > 0 else 0,
                    'avg_efficiency': avg_efficiency,
                    'max_efficiency': max_efficiency,
                    'min_efficiency': min_efficiency,
                    'execution_time': execution_time,
                    'algorithms_used': list(set(algorithms)),
                    'performance_score': self._calculate_performance_score(
                        total_positioned, expected_size, avg_efficiency, execution_time
                    )
                }
            else:
                return {
                    'success': False,
                    'batch_count': 0,
                    'total_positioned': 0,
                    'total_excluded': expected_size,
                    'expected_size': expected_size,
                    'utilization_rate': 0,
                    'avg_efficiency': 0,
                    'max_efficiency': 0,
                    'min_efficiency': 0,
                    'execution_time': execution_time,
                    'algorithms_used': [],
                    'performance_score': 0,
                    'error_message': result.get('message', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"❌ Errore analisi risultato: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
    
    def _calculate_performance_score(self, positioned: int, expected: int, efficiency: float, time_sec: float) -> float:
        """Calcola un punteggio di performance combinato"""
        # Punteggio utilizzo (40%)
        utilization_score = (positioned / expected) * 100 if expected > 0 else 0
        
        # Punteggio efficienza (40%)
        efficiency_score = efficiency
        
        # Punteggio velocità (20%) - penalizza tempi lunghi
        time_penalty = max(0, 100 - (time_sec * 2))  # Penalità dopo 50s
        
        return (utilization_score * 0.4 + efficiency_score * 0.4 + time_penalty * 0.2)
    
    def generate_optimization_recommendations(self) -> Dict[str, Any]:
        """Genera raccomandazioni per ottimizzazioni basate sui test"""
        logger.info("🎯 === RACCOMANDAZIONI OTTIMIZZAZIONE ===")
        
        if not self.results or not self.dataset_analysis:
            logger.error("❌ Eseguire prima i test per generare raccomandazioni")
            return {}
        
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'dataset_summary': {
                'complexity_index': self.dataset_analysis['complexity_index'],
                'tool_count': self.dataset_analysis['tool_stats']['valid_count'],
                'autoclave_count': self.dataset_analysis['autoclave_stats']['total_count']
            },
            'performance_analysis': {},
            'bottlenecks': [],
            'optimizations': [],
            'parameter_recommendations': {},
            'scalability_limits': {}
        }
        
        # Analizza performance per trovare pattern
        all_results = []
        for test_batch in self.results:
            if isinstance(test_batch, list):
                all_results.extend(test_batch)
            elif 'size_results' in test_batch:
                all_results.extend(test_batch['size_results'])
            else:
                all_results.append(test_batch)
        
        if not all_results:
            logger.warning("⚠️ Nessun risultato valido per analisi")
            return recommendations
        
        # Performance analysis
        success_rate = len([r for r in all_results if r.get('success', False)]) / len(all_results)
        avg_efficiency = statistics.mean([r.get('avg_efficiency', 0) for r in all_results if r.get('success', False)])
        avg_utilization = statistics.mean([r.get('utilization_rate', 0) for r in all_results if r.get('success', False)])
        avg_time_per_odl = statistics.mean([r.get('execution_time', 0) / max(r.get('expected_size', 1), 1) for r in all_results if r.get('success', False)])
        
        recommendations['performance_analysis'] = {
            'success_rate': success_rate,
            'avg_efficiency': avg_efficiency,
            'avg_utilization': avg_utilization,
            'avg_time_per_odl': avg_time_per_odl
        }
        
        # Identifica bottleneck
        if success_rate < 0.8:
            recommendations['bottlenecks'].append("Basso tasso di successo - rivedere vincoli geometrici")
        if avg_efficiency < 50:
            recommendations['bottlenecks'].append("Bassa efficienza - ottimizzare algoritmi di posizionamento")
        if avg_time_per_odl > 5:
            recommendations['bottlenecks'].append("Tempi di calcolo elevati - ridurre timeout o semplificare")
        if avg_utilization < 0.7:
            recommendations['bottlenecks'].append("Basso utilizzo tool - rivedere filtri pre-processing")
        
        # Genera ottimizzazioni specifiche
        complexity = self.dataset_analysis['complexity_index']
        
        if complexity > 7:  # Alta complessità
            recommendations['optimizations'].extend([
                "Implementare pre-filtering intelligente per tool incompatibili",
                "Usare timeout dinamico basato su complessità",
                "Attivare algoritmi semplificati per batch grandi",
                "Considerare partizionamento batch per tool problematici"
            ])
        elif complexity < 3:  # Bassa complessità
            recommendations['optimizations'].extend([
                "Aumentare dimensioni batch per sfruttare semplicità",
                "Usare parametri aggressivi per efficienza massima",
                "Ridurre timeout per velocizzare processing",
                "Sperimentare algoritmi avanzati per efficienza premium"
            ])
        else:  # Complessità media
            recommendations['optimizations'].extend([
                "Bilanciare timeout e qualità risultati",
                "Usare algoritmi adattivi basati su dimensione batch",
                "Implementare caching per configurazioni simili",
                "Ottimizzare parallelizzazione per multi-autoclave"
            ])
        
        # Raccomandazioni parametri
        if avg_efficiency > 70:
            recommended_params = {
                'padding_mm': 5.0,
                'min_distance_mm': 8.0,
                'timeout_strategy': 'aggressive'
            }
        elif avg_efficiency > 50:
            recommended_params = {
                'padding_mm': 10.0,
                'min_distance_mm': 15.0,
                'timeout_strategy': 'balanced'
            }
        else:
            recommended_params = {
                'padding_mm': 0.5,
                'min_distance_mm': 0.5,
                'timeout_strategy': 'aerospace_grade'
            }
        
        recommendations['parameter_recommendations'] = recommended_params
        
        # Limiti scalabilità
        max_successful_size = max([r.get('expected_size', 0) for r in all_results if r.get('success', False)], default=0)
        max_reasonable_time = max([r.get('execution_time', 0) for r in all_results if r.get('execution_time', 0) < 300], default=0)
        
        recommendations['scalability_limits'] = {
            'max_odls_tested': max_successful_size,
            'max_reasonable_time': max_reasonable_time,
            'recommended_batch_limit': min(30, max_successful_size) if max_successful_size > 0 else 20,
            'estimated_45_odl_time': avg_time_per_odl * 45 if avg_time_per_odl > 0 else 'unknown'
        }
        
        # Log raccomandazioni
        logger.info("🎯 RACCOMANDAZIONI GENERATE:")
        logger.info(f"   📊 Performance: {success_rate:.1%} successo, {avg_efficiency:.1f}% efficienza")
        logger.info(f"   ⚡ Velocità: {avg_time_per_odl:.2f}s per ODL")
        logger.info(f"   🎯 Batch limite raccomandato: {recommendations['scalability_limits']['recommended_batch_limit']} ODL")
        logger.info(f"   ⏱️ Stima 45 ODL: {recommendations['scalability_limits']['estimated_45_odl_time']}")
        
        return recommendations
    
    def save_results(self, filename: Optional[str] = None):
        """Salva tutti i risultati in un file JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.json"
        
        full_results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'test_version': '1.0.0',
                'description': 'CarbonPilot Nesting Stress Test Results'
            },
            'dataset_analysis': self.dataset_analysis,
            'test_results': self.results,
            'recommendations': self.generate_optimization_recommendations()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Risultati salvati in: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio: {e}")
            return None

def main():
    """Esegue lo stress test completo"""
    logger.info("🚀 === AVVIO STRESS TEST CARBONPILOT NESTING ===")
    
    # Inizializza stress test
    stress_test = NestingStressTest()
    
    try:
        # 1. Analisi dataset
        logger.info("\n📊 FASE 1: Analisi Dataset")
        dataset_analysis = stress_test.analyze_dataset_complexity()
        if not dataset_analysis:
            logger.error("❌ Impossibile analizzare dataset - test interrotto")
            return
        
        # 2. Test performance con diversi parametri
        logger.info("\n⚡ FASE 2: Test Performance")
        performance_results = stress_test.run_performance_tests()
        if not performance_results:
            logger.warning("⚠️ Test performance falliti")
        
        # 3. Test scalabilità
        logger.info("\n📈 FASE 3: Test Scalabilità")
        scalability_results = stress_test.test_scalability(max_odls=45)
        if scalability_results:
            stress_test.results.append(scalability_results)
        
        # 4. Genera raccomandazioni
        logger.info("\n🎯 FASE 4: Raccomandazioni")
        recommendations = stress_test.generate_optimization_recommendations()
        
        # 5. Salva risultati
        logger.info("\n💾 FASE 5: Salvataggio")
        results_file = stress_test.save_results()
        
        logger.info("\n✅ === STRESS TEST COMPLETATO ===")
        if results_file:
            logger.info(f"📄 Risultati disponibili in: {results_file}")
        
        # Summary finale
        if recommendations:
            logger.info(f"\n📋 SUMMARY:")
            perf = recommendations['performance_analysis']
            limits = recommendations['scalability_limits']
            logger.info(f"   🎯 Successo: {perf['success_rate']:.1%}")
            logger.info(f"   ⚡ Efficienza: {perf['avg_efficiency']:.1f}%")
            logger.info(f"   🏭 Utilizzo: {perf['avg_utilization']:.1%}")
            logger.info(f"   ⏱️ Velocità: {perf['avg_time_per_odl']:.2f}s/ODL")
            logger.info(f"   📊 Limite raccomandato: {limits['recommended_batch_limit']} ODL")
        
    except Exception as e:
        logger.error(f"❌ Errore durante stress test: {e}")
        raise

if __name__ == "__main__":
    main() 