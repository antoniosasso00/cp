"""
PERFORMANCE OPTIMIZER per NESTING CARBONPILOT
==============================================

Modulo di ottimizzazione performance che implementa:
1. Pre-filtering intelligente
2. Timeout dinamico avanzato
3. Caching per tool identici
4. Parallelizzazione multi-livello
5. Parametri adattivi
6. Fallback ottimizzati

Integrato modulare con il sistema esistente senza modifiche breaking.
"""

import time
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Metriche di performance per analisi e ottimizzazione"""
    tool_count: int
    autoclave_area: float
    avg_tool_area: float
    max_tool_area: float
    complexity_factor: float  # aspect ratio variance
    density_ratio: float      # tool_area / autoclave_area
    predicted_difficulty: str # EASY, MEDIUM, HARD, EXTREME

@dataclass 
class OptimizationResult:
    """Risultato di un'ottimizzazione applicata"""
    optimization_type: str
    time_saved_ms: float
    efficiency_gain_pct: float
    cache_hits: int
    parallel_speedup: float

class ToolCache:
    """Cache intelligente per tool con dimensioni e pesi identici"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def _tool_hash(self, tool_width: float, tool_height: float, tool_weight: float) -> str:
        """Genera hash univoco per tool con dimensioni e peso"""
        key = f"{tool_width:.1f}x{tool_height:.1f}x{tool_weight:.1f}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def get_layout(self, tool_width: float, tool_height: float, tool_weight: float, 
                   autoclave_id: int) -> Optional[Dict]:
        """Recupera layout cached per tool identico"""
        with self._lock:
            tool_hash = self._tool_hash(tool_width, tool_height, tool_weight)
            cache_key = f"{tool_hash}_{autoclave_id}"
            
            if cache_key in self.cache:
                self.hits += 1
                return self.cache[cache_key].copy()
            
            self.misses += 1
            return None
    
    def store_layout(self, tool_width: float, tool_height: float, tool_weight: float,
                     autoclave_id: int, layout: Dict):
        """Memorizza layout per riuso futuro"""
        with self._lock:
            if len(self.cache) >= self.max_size:
                # Rimuovi il più vecchio (LRU semplificato)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            tool_hash = self._tool_hash(tool_width, tool_height, tool_weight)
            cache_key = f"{tool_hash}_{autoclave_id}"
            self.cache[cache_key] = layout.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiche cache per monitoring"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate_pct': hit_rate,
            'size': len(self.cache)
        }

class PerformanceOptimizer:
    """Ottimizzatore di performance per il sistema nesting"""
    
    def __init__(self):
        self.tool_cache = ToolCache()
        self.optimization_stats = []
        
    def analyze_complexity(self, tools: List[Dict], autoclave: Dict) -> PerformanceMetrics:
        """Analizza la complessità del problema per ottimizzazioni targeted"""
        
        tool_areas = [t.get('tool_width', 0) * t.get('tool_height', 0) for t in tools]
        autoclave_area = autoclave.get('lunghezza', 0) * autoclave.get('larghezza_piano', 0)
        
        if not tool_areas or autoclave_area == 0:
            return PerformanceMetrics(
                tool_count=len(tools), autoclave_area=0, avg_tool_area=0,
                max_tool_area=0, complexity_factor=1.0, density_ratio=0,
                predicted_difficulty="UNKNOWN"
            )
        
        # Calcola aspect ratios per complexity factor
        aspect_ratios = []
        for tool in tools:
            w, h = tool.get('tool_width', 1), tool.get('tool_height', 1)
            if w > 0 and h > 0:
                aspect_ratios.append(max(w, h) / min(w, h))
        
        avg_tool_area = statistics.mean(tool_areas)
        max_tool_area = max(tool_areas)
        complexity_factor = statistics.stdev(aspect_ratios) if len(aspect_ratios) > 1 else 1.0
        density_ratio = sum(tool_areas) / autoclave_area
        
        # Predici difficoltà per timeout dinamico
        if density_ratio > 0.8 or complexity_factor > 3.0 or len(tools) > 30:
            difficulty = "EXTREME"
        elif density_ratio > 0.6 or complexity_factor > 2.0 or len(tools) > 15:
            difficulty = "HARD"
        elif density_ratio > 0.4 or complexity_factor > 1.5 or len(tools) > 8:
            difficulty = "MEDIUM"
        else:
            difficulty = "EASY"
        
        return PerformanceMetrics(
            tool_count=len(tools),
            autoclave_area=autoclave_area,
            avg_tool_area=avg_tool_area,
            max_tool_area=max_tool_area,
            complexity_factor=complexity_factor,
            density_ratio=density_ratio,
            predicted_difficulty=difficulty
        )
    
    def compute_dynamic_timeout(self, metrics: PerformanceMetrics) -> int:
        """Calcola timeout dinamico basato su complessità del problema"""
        
        base_timeout = {
            "EASY": 15,
            "MEDIUM": 45,
            "HARD": 120,
            "EXTREME": 300
        }.get(metrics.predicted_difficulty, 60)
        
        # Aggiustamenti per fattori specifici
        complexity_bonus = min(60, int(metrics.complexity_factor * 10))
        density_bonus = min(60, int(metrics.density_ratio * 100))
        size_bonus = min(120, int(metrics.tool_count * 2))
        
        dynamic_timeout = base_timeout + complexity_bonus + density_bonus + size_bonus
        
        # Limiti assoluti
        return max(10, min(300, dynamic_timeout))
    
    def pre_filter_tools(self, tools: List[Dict], autoclave: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Pre-filtering intelligente per escludere tool problematici"""
        
        valid_tools = []
        excluded_tools = []
        
        autoclave_w = autoclave.get('lunghezza', 0)
        autoclave_h = autoclave.get('larghezza_piano', 0)
        autoclave_area = autoclave_w * autoclave_h
        
        for tool in tools:
            tool_w = tool.get('tool_width', 0)
            tool_h = tool.get('tool_height', 0)
            tool_area = tool_w * tool_h
            tool_weight = tool.get('tool_weight', 0)
            
            exclude_reasons = []
            
            # 1. Filtro area minima (tool troppo piccoli inefficienti)
            if tool_area < 1000:  # 1000mm²
                exclude_reasons.append("Area troppo piccola (< 1000mm²)")
            
            # 2. Filtro compatibilità autoclave (con margine per rotazione)
            margin = 20  # mm di margine
            fits_normal = (tool_w + margin <= autoclave_w and tool_h + margin <= autoclave_h)
            fits_rotated = (tool_h + margin <= autoclave_w and tool_w + margin <= autoclave_h)
            
            if not fits_normal and not fits_rotated:
                exclude_reasons.append("Non compatibile con autoclave (troppo grande)")
            
            # 3. Filtro aspect ratio estremo
            if tool_w > 0 and tool_h > 0:
                aspect_ratio = max(tool_w, tool_h) / min(tool_w, tool_h)
                if aspect_ratio > 15:  # Molto sottile/lungo
                    exclude_reasons.append(f"Aspect ratio estremo ({aspect_ratio:.1f}:1)")
            
            # 4. Filtro peso
            max_weight = autoclave.get('max_load_kg', 1000)
            if tool_weight > max_weight * 0.8:  # Tool usa > 80% capacità peso
                exclude_reasons.append("Peso eccessivo per autoclave")
            
            # 5. Filtro area eccessiva
            if autoclave_area > 0 and tool_area > autoclave_area * 0.9:
                exclude_reasons.append("Area eccessiva (> 90% autoclave)")
            
            if exclude_reasons:
                excluded_tools.append({
                    'odl_id': tool.get('odl_id'),
                    'motivo': 'Pre-filtering intelligente',
                    'dettagli': '; '.join(exclude_reasons)
                })
            else:
                valid_tools.append(tool)
        
        logger.info(f"Pre-filtering: {len(valid_tools)} valid, {len(excluded_tools)} excluded")
        return valid_tools, excluded_tools
    
    def optimize_parameters(self, tools: List[Dict], autoclave: Dict, 
                          base_params: Dict) -> Dict[str, Any]:
        """Ottimizza parametri dinamicamente basandosi sul problema"""
        
        metrics = self.analyze_complexity(tools, autoclave)
        optimized_params = base_params.copy()
        
        # Parametri adattivi per efficienza
        if metrics.density_ratio > 0.7:  # Alta densità = parametri aggressivi
            optimized_params['padding_mm'] = max(1, base_params.get('padding_mm', 10) * 0.5)
            optimized_params['min_distance_mm'] = max(2, base_params.get('min_distance_mm', 15) * 0.6)
        elif metrics.density_ratio < 0.3:  # Bassa densità = parametri conservativi
            optimized_params['padding_mm'] = base_params.get('padding_mm', 10) * 1.5
            optimized_params['min_distance_mm'] = base_params.get('min_distance_mm', 15) * 1.3
        
        # Timeout dinamico
        optimized_params['timeout_override'] = self.compute_dynamic_timeout(metrics)
        
        # Strategia multithread per problemi complessi
        if metrics.predicted_difficulty in ["HARD", "EXTREME"]:
            optimized_params['use_multithread'] = True
            optimized_params['num_search_workers'] = 8
        else:
            optimized_params['num_search_workers'] = 4
        
        # Attiva GRASP per problemi difficili
        if metrics.tool_count > 20 or metrics.complexity_factor > 2.5:
            optimized_params['use_grasp_heuristic'] = True
            optimized_params['max_iterations_grasp'] = min(10, max(3, metrics.tool_count // 5))
        
        return optimized_params
    
    def parallel_autoclave_processing(self, tools: List[Dict], autoclaves: List[Dict],
                                    nesting_func, parameters: Dict) -> List[Dict]:
        """Processa autoclavi in parallelo per ridurre tempo totale"""
        
        results = []
        start_time = time.time()
        
        # Per poche autoclavi, non conviene parallelizzare
        if len(autoclaves) <= 1:
            for autoclave in autoclaves:
                result = nesting_func(tools, autoclave, parameters)
                results.append({
                    'autoclave_id': autoclave.get('id'),
                    'result': result,
                    'processing_time': time.time() - start_time
                })
            return results
        
        # Parallelizzazione con ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(4, len(autoclaves))) as executor:
            # Submetti tutti i task
            future_to_autoclave = {
                executor.submit(nesting_func, tools, autoclave, parameters): autoclave
                for autoclave in autoclaves
            }
            
            # Raccogli risultati man mano che completano
            for future in as_completed(future_to_autoclave):
                autoclave = future_to_autoclave[future]
                try:
                    result = future.result(timeout=300)  # 5 min timeout per autoclave
                    results.append({
                        'autoclave_id': autoclave.get('id'),
                        'result': result,
                        'processing_time': time.time() - start_time
                    })
                except Exception as e:
                    logger.error(f"Errore processing autoclave {autoclave.get('id')}: {e}")
                    results.append({
                        'autoclave_id': autoclave.get('id'),
                        'result': None,
                        'error': str(e),
                        'processing_time': time.time() - start_time
                    })
        
        total_time = time.time() - start_time
        logger.info(f"Parallel processing completed: {len(autoclaves)} autoclaves in {total_time:.2f}s")
        
        return results
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Riassunto delle ottimizzazioni applicate per monitoring"""
        
        cache_stats = self.tool_cache.get_stats()
        
        return {
            'cache_performance': cache_stats,
            'optimizations_applied': len(self.optimization_stats),
            'total_time_saved_ms': sum(opt.time_saved_ms for opt in self.optimization_stats),
            'avg_efficiency_gain_pct': statistics.mean([opt.efficiency_gain_pct for opt in self.optimization_stats]) if self.optimization_stats else 0
        }

# Singleton instance per utilizzo globale
performance_optimizer = PerformanceOptimizer() 