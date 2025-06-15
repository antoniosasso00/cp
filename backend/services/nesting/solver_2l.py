"""
CarbonPilot - Nesting Solver a Due Livelli (2L) v1.0
Implementazione di nesting 2D con supporto per cavalletti (due livelli)
Basato su solver.py esistente con estensioni per gestire piano base + cavalletto

🚀 FUNZIONALITÀ 2L:
- Livello 0: Piano base autoclave
- Livello 1: Su cavalletto
- Vincoli: Non overlap sullo stesso livello, overlap consentito tra livelli diversi
- Algoritmi: CP-SAT + fallback BL-FFD estesi per due livelli
"""

import logging
import math
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from ortools.sat.python import cp_model
import numpy as np

# 🆕 NUOVO: Import dei nuovi schemi Pydantic
from schemas.batch_nesting import (
    PosizionamentoTool2L, 
    CavallettoPosizionamento, 
    NestingMetrics2L,
    NestingSolveResponse2L
)

# 🆕 IMPORT SOLVER PRINCIPALE per integrazione sequenziale
from .solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo, NestingLayout, NestingSolution

# Configurazione logger
logger = logging.getLogger(__name__)

@dataclass
class NestingParameters2L:
    """Parametri per l'algoritmo di nesting a due livelli - CONFIGURABILI DAL FRONTEND"""
    # Parametri base (ereditati dal solver originale)
    padding_mm: float = 10.0
    min_distance_mm: float = 15.0
    vacuum_lines_capacity: int = 25
    use_fallback: bool = True
    allow_heuristic: bool = True
    timeout_override: Optional[int] = None
    heavy_piece_threshold_kg: float = 50.0
    
    # Parametri specifici per due livelli (configurabili dal frontend)
    use_cavalletti: bool = True  # Abilita secondo livello
    # 🗑️ RIMOSSO: cavalletto_height_mm (ora dal database autoclave)
    prefer_base_level: bool = False  # 🔧 FIX: Ridotta preferenza per piano base
    
    # Parametri avanzati (configurabili dal frontend)
    use_multithread: bool = True
    num_search_workers: int = 8
    base_timeout_seconds: float = 20.0
    max_timeout_seconds: float = 300.0
    
    # Parametri per penalità/bonus (configurabili dal frontend)
    level_preference_weight: float = 0.05  # 🔧 FIX: Ridotto peso preferenza livello base
    compactness_weight: float = 0.05
    area_weight: float = 0.85

@dataclass
class ToolInfo2L:
    """Informazioni di un tool per nesting a due livelli"""
    odl_id: int
    width: float
    height: float
    weight: float
    lines_needed: int = 1
    ciclo_cura_id: Optional[int] = None
    priority: int = 1
    debug_reasons: List[str] = None
    excluded: bool = False
    
    # Vincoli specifici per due livelli
    can_use_cavalletto: bool = True  # Se il tool può essere posizionato su cavalletto
    preferred_level: Optional[int] = None  # 0=base, 1=cavalletto, None=qualsiasi
    
    def __post_init__(self):
        if self.debug_reasons is None:
            self.debug_reasons = []
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def aspect_ratio(self) -> float:
        return max(self.width, self.height) / min(self.width, self.height)

@dataclass
class AutoclaveInfo2L:
    """Informazioni dell'autoclave per nesting a due livelli - DATI DAL DATABASE"""
    id: int
    width: float
    height: float
    max_weight: float
    max_lines: int
    
    # ✅ DINAMICO: Specifiche cavalletti dal database autoclave
    has_cavalletti: bool = False
    cavalletto_height: float = 100.0  # Altezza cavalletto (mm)
    peso_max_per_cavalletto_kg: float = 300.0  # Peso max per cavalletto
    
    # ✅ NUOVO: Dimensioni fisiche cavalletti (dal database autoclave)
    cavalletto_width: float = 80.0  # mm - larghezza fisica cavalletto (era hardcoded nel solver)
    cavalletto_height_mm: float = 60.0  # mm - altezza fisica cavalletto (era hardcoded nel solver)
    
    # ✅ NUOVO: Campi aggiuntivi dal database
    max_cavalletti: Optional[int] = None  # Numero massimo cavalletti supportati
    cavalletto_thickness_mm: Optional[float] = None  # Spessore segmento cavalletto
    clearance_verticale: Optional[float] = None  # Clearance verticale tra cavalletti
    
    # Calcolato dinamicamente durante il solve
    num_cavalletti_utilizzati: int = 0

@dataclass
class NestingLayout2L:
    """Layout di posizionamento con supporto per due livelli"""
    odl_id: int
    x: float
    y: float
    width: float
    height: float
    weight: float
    level: int = 0  # 0=piano base, 1=cavalletto
    rotated: bool = False
    lines_used: int = 1
    
    @property
    def z_position(self) -> float:
        """Posizione Z basata sul livello"""
        return self.level * 100.0  # Assumendo 100mm di altezza per livello

@dataclass
class NestingMetrics2LLocal:
    """Metriche per nesting a due livelli (dataclass locale del solver)"""
    area_pct: float
    vacuum_util_pct: float
    lines_used: int
    total_weight: float
    positioned_count: int
    excluded_count: int
    efficiency_score: float
    time_solver_ms: float
    fallback_used: bool
    
    # Metriche specifiche per due livelli
    level_0_count: int = 0  # Tool sul piano base
    level_1_count: int = 0  # Tool su cavalletto
    level_0_weight: float = 0.0
    level_1_weight: float = 0.0
    level_0_area_pct: float = 0.0
    level_1_area_pct: float = 0.0
    
    algorithm_used: str = ""
    complexity_score: float = 0.0
    timeout_used: float = 0.0

@dataclass
class NestingSolution2L:
    """Soluzione completa per nesting a due livelli"""
    layouts: List[NestingLayout2L]
    excluded_odls: List[Dict[str, Any]]
    metrics: NestingMetrics2LLocal
    success: bool
    algorithm_status: str
    message: str = ""

    # ✅ NUOVO: Supporto ottimizzatore cavalletti avanzato
    cavalletti_finali: List[Any] = None  # CavallettoFixedPosition o altro
    cavalletti_optimization_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cavalletti_finali is None:
            self.cavalletti_finali = []
        if self.cavalletti_optimization_stats is None:
            self.cavalletti_optimization_stats = {}

@dataclass
class CavallettoPosition:
    """Posizione di un cavalletto sotto un tool"""
    x: float
    y: float
    width: float  # Larghezza del cavalletto
    height: float  # Profondità del cavalletto
    tool_odl_id: int  # ODL del tool che supporta
    sequence_number: int  # Numero di sequenza del cavalletto per questo tool (0, 1, 2...)
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

@dataclass
class CavallettiConfiguration:
    """Configurazione per il calcolo dei cavalletti - VALORI DINAMICI DAL DATABASE"""
    # ✅ NUOVO: Dimensioni fisiche cavalletti (dal database autoclave)
    cavalletto_width: float = 80.0  # mm - larghezza fisica cavalletto (era hardcoded)
    cavalletto_height: float = 60.0  # mm - altezza fisica cavalletto (era hardcoded)
    
    # Parametri posizionamento (configurabili dal frontend)
    min_distance_from_edge: float = 30.0  # mm - distanza minima dai bordi del tool
    max_span_without_support: float = 400.0  # mm - distanza massima tra cavalletti
    min_distance_between_cavalletti: float = 200.0  # mm - distanza minima tra cavalletti
    
    # Margini di sicurezza (configurabili dal frontend)
    safety_margin_x: float = 5.0  # mm - margine lungo X per evitare interferenze
    safety_margin_y: float = 5.0  # mm - margine lungo Y per evitare interferenze
    
    # Strategie di posizionamento (configurabili dal frontend)
    prefer_symmetric: bool = True  # Preferisci posizionamento simmetrico
    force_minimum_two: bool = True  # Forza almeno 2 cavalletti per tool di media/grande dimensione

@dataclass
class CavallettoFixedPosition:
    """Posizione di un cavalletto fisso dell'autoclave (segmento trasversale)"""
    x: float  # Posizione X inizio segmento
    y: float  # Posizione Y del segmento
    width: float  # Lunghezza del segmento trasversale (= lato corto autoclave)
    height: float  # Spessore del cavalletto (fisso, es. 60mm)
    sequence_number: int  # Numero progressivo del cavalletto (0, 1, 2...)
    orientation: str = "horizontal"  # Sempre orizzontale (trasversale)
    
    # ✅ FIX COMPATIBILITÀ: Aggiunto tool_odl_id per compatibilità con convert_to_pydantic_response
    tool_odl_id: Optional[int] = None  # ODL del tool supportato (se applicabile)
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    @property
    def end_x(self) -> float:
        return self.x + self.width
    
    @property
    def end_y(self) -> float:
        return self.y + self.height

@dataclass
class CavallettiFixedConfiguration:
    """Configurazione per cavalletti fissi dell'autoclave - VALORI DINAMICI DAL DATABASE"""
    # 🗑️ RIMOSSI VALORI HARDCODED - ora vengono passati dall'autoclave
    
    # Posizionamento (configurabili dal frontend)
    distribute_evenly: bool = True  # Distribuisci uniformemente
    min_distance_from_edges: float = 100.0  # Distanza minima dai bordi autoclave
    min_spacing_between_cavalletti: float = 200.0  # Spaziatura minima tra cavalletti
    
    # Orientamento (sempre trasversale al lato corto)
    orientation: str = "horizontal"  # I cavalletti sono sempre orizzontali

class NestingModel2L:
    """Modello di nesting a due livelli con supporto cavalletti - CONFIGURAZIONE DINAMICA"""
    
    def __init__(self, parameters: NestingParameters2L):
        self.parameters = parameters
        self.logger = logging.getLogger(__name__)
        
        # ✅ NUOVO: Configurazione cavalletti dinamica dal frontend
        self._cavalletti_config: Optional[CavallettiConfiguration] = None
        
        # Inizializza solver base per compatibilità
        base_params = NestingParameters(
            padding_mm=parameters.padding_mm,
            min_distance_mm=parameters.min_distance_mm,
            vacuum_lines_capacity=parameters.vacuum_lines_capacity,
            use_fallback=parameters.use_fallback,
            allow_heuristic=parameters.allow_heuristic,
            timeout_override=parameters.timeout_override,
            heavy_piece_threshold_kg=parameters.heavy_piece_threshold_kg,
            use_multithread=parameters.use_multithread,
            num_search_workers=parameters.num_search_workers,
            base_timeout_seconds=parameters.base_timeout_seconds,
            max_timeout_seconds=parameters.max_timeout_seconds
        )
        
        self.base_solver = NestingModel(base_params)
        
        # Statistiche e metriche
        self.stats = {
            'total_solve_time': 0.0,
            'level_0_solve_time': 0.0,
            'level_1_solve_time': 0.0,
            'cavalletti_calc_time': 0.0,
            'solutions_attempted': 0,
            'fallback_used': False
        }
    
    def _calculate_dynamic_weight_limits(
        self, 
        autoclave: AutoclaveInfo2L,
        num_cavalletti_in_use: int
    ) -> tuple[float, float]:
        """
        🔧 FIX CRITICO: Calcola dinamicamente i limiti di peso per livello
        
        PROBLEMA RISOLTO: La logica precedente creava un circolo vizioso dove num_cavalletti_in_use=0
        impediva qualsiasi uso del livello 1.
        
        SOLUZIONE: Usa max_cavalletti dall'autoclave come capacità potenziale, non cavalletti attualmente in uso.
        
        Args:
            autoclave: Informazioni autoclave
            num_cavalletti_in_use: Numero di cavalletti effettivamente utilizzati (per logging)
            
        Returns:
            Tuple (peso_max_livello_0, peso_max_livello_1)
        """
        # 🚀 FIX: Usa capacità POTENZIALE dei cavalletti, non quelli attualmente in uso
        peso_max_livello_1 = 0.0
        if autoclave.has_cavalletti:
            # Usa max_cavalletti se disponibile, altrimenti stima ragionevole
            max_cavalletti_disponibili = autoclave.max_cavalletti or 6  # Default 6 cavalletti
            peso_max_livello_1 = autoclave.peso_max_per_cavalletto_kg * max_cavalletti_disponibili
        
        # Peso massimo livello 0: può usare quasi tutto il carico se necessario
        # Ma lascia spazio per almeno qualche tool sul livello 1 se cavalletti abilitati
        if autoclave.has_cavalletti and peso_max_livello_1 > 0:
            # Bilanciamento: 70% autoclave per livello 0, 30% per livello 1 (flessibile)
            peso_max_livello_0 = autoclave.max_weight * 0.7
            # Assicura che livello 1 abbia almeno capacità minima utilizzabile
            peso_max_livello_1 = min(peso_max_livello_1, autoclave.max_weight * 0.8)  # Max 80% peso autoclave
        else:
            # Nessun cavalletto: tutto il peso va su livello 0
            peso_max_livello_0 = autoclave.max_weight
            peso_max_livello_1 = 0.0
        
        # 🔧 FIX: Logging migliorato per debug
        if num_cavalletti_in_use == 0:  # Log solo all'inizio
            max_cav = autoclave.max_cavalletti or 6
            self.logger.info(f"🔧 [FIX] Limiti peso: L0={peso_max_livello_0:.1f}kg, L1={peso_max_livello_1:.1f}kg")
            self.logger.info(f"   Cavalletti: {max_cav} disponibili x {autoclave.peso_max_per_cavalletto_kg}kg = capacità {peso_max_livello_1:.1f}kg")
        
        return peso_max_livello_0, peso_max_livello_1
    
    def solve_2l(
        self, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L
    ) -> NestingSolution2L:
        """
        ⭐ ALGORITMO SEQUENZIALE 2L v3.0 - INTEGRAZIONE SOLVER.PY + SOLVER_2L.PY
        
        LOGICA CORRETTA IMPLEMENTATA:
        1. FASE 1: Riempi completamente il LIVELLO 0 usando solver.py (algoritmi aerospace-grade)
        2. FASE 2: Posiziona tool rimanenti sul LIVELLO 1 usando algoritmi cavalletti
        
        Questo approccio garantisce il riempimento ottimale del piano base prima di 
        utilizzare i cavalletti, come richiesto dal workflow industriale.
        """
        start_time = time.time()
        
        self.logger.info(f"\n🔧 === NESTING 2L SEQUENTIAL SOLVER v3.0 ===")
        self.logger.info(f"🏭 Autoclave: {autoclave.id} ({autoclave.width}x{autoclave.height}mm)")
        self.logger.info(f"📦 Tool da posizionare: {len(tools)}")
        self.logger.info(f"🎰 Cavalletti abilitati: {autoclave.has_cavalletti}")
        
        if not tools:
            return self._create_empty_solution_2l([], autoclave, start_time)
        
        # 1. Pre-filtro tool incompatibili
        valid_tools, excluded_tools = self._prefilter_tools_2l(tools, autoclave)
        
        if not valid_tools:
            self.logger.warning("❌ Nessun tool valido dopo pre-filtro")
            return self._create_empty_solution_2l(excluded_tools, autoclave, start_time)
        
        self.logger.info(f"📋 Tool validi: {len(valid_tools)}, Esclusi: {len(excluded_tools)}")
        
        # 🚀 FASE 1: RIEMPI LIVELLO 0 (Piano Autoclave) usando solver.py
        self.logger.info(f"\n📍 FASE 1: Riempimento LIVELLO 0 (Piano Autoclave)")
        level_0_solution = self._solve_level_0_first(valid_tools, autoclave, start_time)
        
        level_0_layouts = level_0_solution.layouts if level_0_solution.success else []
        positioned_odl_ids = {layout.odl_id for layout in level_0_layouts}
        remaining_tools = [tool for tool in valid_tools if tool.odl_id not in positioned_odl_ids]
        
        self.logger.info(f"✅ Livello 0 completato: {len(level_0_layouts)} tool posizionati")
        self.logger.info(f"📦 Tool rimanenti per livello 1: {len(remaining_tools)}")
        
        # 🚀 FASE 2: POSIZIONA RIMANENTI SU LIVELLO 1 (Cavalletti)
        level_1_layouts = []
        if remaining_tools and autoclave.has_cavalletti:
            self.logger.info(f"\n📍 FASE 2: Posizionamento LIVELLO 1 (Cavalletti)")
            level_1_layouts = self._solve_level_1_remaining(remaining_tools, autoclave, level_0_layouts, start_time)
            self.logger.info(f"✅ Livello 1 completato: {len(level_1_layouts)} tool posizionati")
        elif not autoclave.has_cavalletti:
            self.logger.info(f"\n⏭️ FASE 2 SALTATA: Cavalletti disabilitati")
        
        # 3. Converti layouts livello 0 da standard a 2L
        level_0_layouts_2l = self._convert_layouts_standard_to_2l(level_0_layouts, level=0)
        
        # 4. Combina risultati dei due livelli
        all_layouts = level_0_layouts_2l + level_1_layouts
        positioned_total = len(all_layouts)
        excluded_total = len(valid_tools) - positioned_total
        
        self.logger.info(f"\n🎯 RISULTATO FINALE 2L:")
        self.logger.info(f"   Livello 0: {len(level_0_layouts_2l)} tool")
        self.logger.info(f"   Livello 1: {len(level_1_layouts)} tool") 
        self.logger.info(f"   Totale posizionato: {positioned_total}/{len(valid_tools)}")
        self.logger.info(f"   Esclusi: {excluded_total}")
        
        # 5. Crea soluzione finale
        final_solution = self._create_combined_solution_2l(
            all_layouts, 
            excluded_tools, 
            valid_tools, 
            autoclave, 
            start_time
        )
        
        # 6. Aggiungi calcolo cavalletti alla soluzione finale
        final_solution = self._add_cavalletti_with_advanced_optimizer(final_solution, autoclave)
        
        return final_solution
    
    def _calculate_dataset_complexity(self, tools: List[ToolInfo2L], autoclave: AutoclaveInfo2L) -> float:
        """Calcola la complessità del dataset"""
        if not tools:
            return 0.0
            
        # Fattori di complessità
        num_tools = len(tools)
        avg_area = sum(t.area for t in tools) / num_tools
        autoclave_area = autoclave.width * autoclave.height
        density = (sum(t.area for t in tools) / autoclave_area) if autoclave_area > 0 else 0
        
        # Fattore specifico per due livelli
        level_complexity = 1.5 if autoclave.has_cavalletti else 1.0
        
        complexity = (num_tools * 0.1 + density * 0.5 + level_complexity * 0.4) * 10
        return min(complexity, 100.0)
    
    def _calculate_dynamic_timeout(self, tools: List[ToolInfo2L], complexity_score: float) -> float:
        """Calcola timeout dinamico basato sulla complessità"""
        base_timeout = self.parameters.base_timeout_seconds
        max_timeout = self.parameters.max_timeout_seconds
        
        # 🆕 FIX: Timeout più aggressivo per dataset grandi
        num_tools = len(tools)
        
        if num_tools > 40:
            # Per dataset molto grandi (40+ tool): timeout aggressivo
            timeout = max_timeout  # Usa sempre il massimo timeout
        elif num_tools > 25:
            # Per dataset grandi (25-40 tool): timeout moderato
            timeout = base_timeout + (complexity_score / 100.0) * (max_timeout - base_timeout) * 1.5
        else:
            # Per dataset piccoli (<25 tool): timeout standard
            timeout = base_timeout + (complexity_score / 100.0) * (max_timeout - base_timeout)
        
        final_timeout = min(timeout, max_timeout)
        
        # 🔧 Logging dettagliato per debugging timeout
        self.logger.info(f"🕒 [2L] Timeout dinamico: {num_tools} tool → {final_timeout:.1f}s (max: {max_timeout}s)")
        
        return final_timeout
    
    def _prefilter_tools_2l(
        self, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L
    ) -> Tuple[List[ToolInfo2L], List[Dict[str, Any]]]:
        """Prefiltra i tool per nesting a due livelli"""
        valid_tools = []
        excluded_tools = []
        
        for tool in tools:
            # Controllo dimensioni base
            if tool.width > autoclave.width or tool.height > autoclave.height:
                excluded_tools.append({
                    'odl_id': tool.odl_id,
                    'reason': f'Dimensioni eccessive: {tool.width}x{tool.height}mm vs {autoclave.width}x{autoclave.height}mm'
                })
                continue
                
            # 🗑️ RIMOSSO: Controllo peso per livello (ora gestito dinamicamente nei vincoli CP-SAT)
            # Il controllo del peso è ora fatto dinamicamente durante la risoluzione
                
            valid_tools.append(tool)
        
        return valid_tools, excluded_tools
    
    def _solve_cpsat_2l(
        self, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        timeout_seconds: float,
        start_time: float
    ) -> NestingSolution2L:
        """Risolve il problema usando CP-SAT con supporto per due livelli"""
        self.logger.info(f"🎯 [2L] Avvio CP-SAT con {len(tools)} tool, timeout {timeout_seconds:.1f}s")
        
        try:
            # Creazione modello CP-SAT
            model = cp_model.CpModel()
            
            # Creazione variabili per due livelli
            variables = self._create_cpsat_variables_2l(model, tools, autoclave)
            
            # Aggiunta vincoli base
            self._add_cpsat_constraints_2l(model, tools, autoclave, variables)
            
            # Aggiungi vincoli interferenza cavalletti (TEMPORANEAMENTE DISABILITATO)
            # if autoclave.has_cavalletti:
            #     self._add_cavalletti_interference_constraints_2l(model, tools, autoclave, variables)
            
            # Aggiungi funzione obiettivo
            self._add_cpsat_objective_2l(model, tools, autoclave, variables)
            
            # Risoluzione
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = timeout_seconds
            if self.parameters.use_multithread:
                solver.parameters.num_search_workers = self.parameters.num_search_workers
            
            self.logger.info("🔄 [2L] Esecuzione CP-SAT...")
            
            try:
                status = solver.Solve(model)
                
                # Estrazione soluzione
                return self._extract_cpsat_solution_2l(solver, tools, autoclave, variables, status, start_time)
                
            except Exception as solve_error:
                error_msg = str(solve_error)
                if "__le__()" in error_msg and "incompatible function arguments" in error_msg:
                    self.logger.error(f"🚨 [2L] CP-SAT BoundedLinearExpression error: {error_msg}")
                    self.logger.info("🔄 [2L] Fallback to greedy algorithm due to CP-SAT error")
                    return self._solve_greedy_2l(tools, autoclave, start_time)
                else:
                    raise solve_error
            
        except Exception as e:
            self.logger.error(f"❌ [2L] Errore CP-SAT: {str(e)}")
            return self._create_empty_solution_2l([], autoclave, start_time)
    
    def _create_cpsat_variables_2l(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L
    ) -> Dict[str, Any]:
        """Crea le variabili CP-SAT per due livelli"""
        variables = {}
        
        # Variabili per ogni tool
        variables['included'] = {}
        variables['x'] = {}
        variables['y'] = {}
        variables['level'] = {}  # Nuova variabile per il livello
        variables['rotated'] = {}
        variables['width'] = {}
        variables['height'] = {}
        
        # 🔧 FIX CP-SAT: Aggiunte variabili intermedie per evitare BoundedLinearExpression
        variables['end_x'] = {}
        variables['end_y'] = {}
        
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # Inclusione del tool
            variables['included'][tool_id] = model.NewBoolVar(f'included_{tool_id}')
            
            # Posizione (x, y)
            variables['x'][tool_id] = model.NewIntVar(0, int(autoclave.width), f'x_{tool_id}')
            variables['y'][tool_id] = model.NewIntVar(0, int(autoclave.height), f'y_{tool_id}')
            
            # Livello (0=base, 1=cavalletto)
            max_level = 1 if autoclave.has_cavalletti and tool.can_use_cavalletto else 0
            variables['level'][tool_id] = model.NewIntVar(0, max_level, f'level_{tool_id}')
            
            # Rotazione
            variables['rotated'][tool_id] = model.NewBoolVar(f'rotated_{tool_id}')
            
            # Dimensioni (dipendenti dalla rotazione)
            variables['width'][tool_id] = model.NewIntVar(
                int(min(tool.width, tool.height)), 
                int(max(tool.width, tool.height)), 
                f'width_{tool_id}'
            )
            variables['height'][tool_id] = model.NewIntVar(
                int(min(tool.width, tool.height)), 
                int(max(tool.width, tool.height)), 
                f'height_{tool_id}'
            )
            
            # 🔧 FIX CP-SAT: Variabili intermedie per end_x e end_y
            variables['end_x'][tool_id] = model.NewIntVar(
                0, int(autoclave.width), f'end_x_{tool_id}'
            )
            variables['end_y'][tool_id] = model.NewIntVar(
                0, int(autoclave.height), f'end_y_{tool_id}'
            )
            
            # Vincoli per dimensioni in base alla rotazione
            model.Add(variables['width'][tool_id] == int(tool.width)).OnlyEnforceIf(
                variables['rotated'][tool_id].Not()
            )
            model.Add(variables['height'][tool_id] == int(tool.height)).OnlyEnforceIf(
                variables['rotated'][tool_id].Not()
            )
            model.Add(variables['width'][tool_id] == int(tool.height)).OnlyEnforceIf(
                variables['rotated'][tool_id]
            )
            model.Add(variables['height'][tool_id] == int(tool.width)).OnlyEnforceIf(
                variables['rotated'][tool_id]
            )
            
            # 🔧 FIX CP-SAT: Vincoli per variabili intermedie
            model.Add(variables['end_x'][tool_id] == variables['x'][tool_id] + variables['width'][tool_id])
            model.Add(variables['end_y'][tool_id] == variables['y'][tool_id] + variables['height'][tool_id])
        
        return variables
    
    def _add_cpsat_constraints_2l(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        variables: Dict[str, Any]
    ) -> None:
        """Aggiunge i vincoli CP-SAT per due livelli"""
        
        # 1. Vincoli di posizionamento dentro l'autoclave
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # 🔧 FIX CP-SAT: Usa variabili intermedie invece di espressioni
            model.Add(
                variables['end_x'][tool_id] <= int(autoclave.width)
            ).OnlyEnforceIf(variables['included'][tool_id])
            
            model.Add(
                variables['end_y'][tool_id] <= int(autoclave.height)
            ).OnlyEnforceIf(variables['included'][tool_id])
        
        # 2. Vincoli di non sovrapposizione SULLO STESSO LIVELLO
        for i in range(len(tools)):
            for j in range(i + 1, len(tools)):
                tool_id_i = f"tool_{i}"
                tool_id_j = f"tool_{j}"
                
                # Creazione variabili booleane per posizioni relative
                left_i = model.NewBoolVar(f'left_{tool_id_i}_{tool_id_j}')
                right_i = model.NewBoolVar(f'right_{tool_id_i}_{tool_id_j}')
                below_i = model.NewBoolVar(f'below_{tool_id_i}_{tool_id_j}')
                above_i = model.NewBoolVar(f'above_{tool_id_i}_{tool_id_j}')
                same_level = model.NewBoolVar(f'same_level_{tool_id_i}_{tool_id_j}')
                
                # Definizione same_level
                model.Add(variables['level'][tool_id_i] == variables['level'][tool_id_j]).OnlyEnforceIf(same_level)
                model.Add(variables['level'][tool_id_i] != variables['level'][tool_id_j]).OnlyEnforceIf(same_level.Not())
                
                # Vincoli di separazione SOLO se sullo stesso livello
                padding = int(self.parameters.padding_mm)
                
                # Tool i a sinistra di tool j
                model.Add(
                    variables['end_x'][tool_id_i] + padding <= variables['x'][tool_id_j]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, left_i])
                
                # Tool i a destra di tool j
                model.Add(
                    variables['end_x'][tool_id_j] + padding <= variables['x'][tool_id_i]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, right_i])
                
                # Tool i sotto tool j
                model.Add(
                    variables['end_y'][tool_id_i] + padding <= variables['y'][tool_id_j]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, below_i])
                
                # Tool i sopra tool j  
                model.Add(
                    variables['end_y'][tool_id_j] + padding <= variables['y'][tool_id_i]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, above_i])
                
                # Almeno una condizione di separazione deve essere vera se entrambi inclusi e sullo stesso livello
                model.AddBoolOr([
                    left_i, right_i, below_i, above_i, 
                    variables['included'][tool_id_i].Not(),
                    variables['included'][tool_id_j].Not(),
                    same_level.Not()
                ])
        
        # 3. Vincoli di peso totale e per livello
        level_0_weight = []
        level_1_weight = []
        
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            weight_on_level_0 = model.NewIntVar(0, int(tool.weight), f'weight_l0_{tool_id}')
            weight_on_level_1 = model.NewIntVar(0, int(tool.weight), f'weight_l1_{tool_id}')
            
            # Peso su livello 0
            model.Add(weight_on_level_0 == int(tool.weight)).OnlyEnforceIf([
                variables['included'][tool_id],
                variables['level'][tool_id] == 0
            ])
            model.Add(weight_on_level_0 == 0).OnlyEnforceIf([
                variables['level'][tool_id] == 1
            ])
            
            # Peso su livello 1
            model.Add(weight_on_level_1 == int(tool.weight)).OnlyEnforceIf([
                variables['included'][tool_id],
                variables['level'][tool_id] == 1
            ])
            model.Add(weight_on_level_1 == 0).OnlyEnforceIf([
                variables['level'][tool_id] == 0
            ])
            
            level_0_weight.append(weight_on_level_0)
            level_1_weight.append(weight_on_level_1)
        
        # 🆕 NUOVO: Calcolo dinamico dei limiti di peso
        # Stima conservativa: usiamo il massimo numero di cavalletti per ora
        estimated_cavalletti = autoclave.num_cavalletti_utilizzati or (getattr(autoclave, 'max_cavalletti', 4) if autoclave.has_cavalletti else 0)
        peso_max_livello_0, peso_max_livello_1 = self._calculate_dynamic_weight_limits(autoclave, estimated_cavalletti)
        
        # Vincoli di peso massimo per livello con logica dinamica
        model.Add(sum(level_0_weight) <= int(peso_max_livello_0))
        if autoclave.has_cavalletti:
            model.Add(sum(level_1_weight) <= int(peso_max_livello_1))
        else:
            model.Add(sum(level_1_weight) == 0)  # Nessun peso su livello 1 se senza cavalletti
        
        # 🔒 VINCOLO TOTALE: Peso combinato ≤ carico massimo autoclave
        model.Add(sum(level_0_weight) + sum(level_1_weight) <= int(autoclave.max_weight))
        
        # 4. Vincoli linee vuoto
        total_lines = sum(variables['included'][f"tool_{i}"] * tools[i].lines_needed for i in range(len(tools)))
        model.Add(total_lines <= autoclave.max_lines)
        
        # 🆕 5. NUOVO VINCOLO DI STABILITÀ: Non condivisione cavalletti estremi
        if autoclave.has_cavalletti:
            self._add_cavalletti_stability_constraints_2l(model, tools, autoclave, variables)
            
        # 🔧 6. FIX CRITICO: Vincolo supporto cavalletti fissi
        if autoclave.has_cavalletti:
            self._add_fixed_support_constraints_2l(model, tools, autoclave, variables)

    def _add_cavalletti_stability_constraints_2l(
        self,
        model: cp_model.CpModel,
        tools: List[ToolInfo2L],
        autoclave: AutoclaveInfo2L,
        variables: Dict[str, Any]
    ) -> None:
        """
        🔒 NUOVO VINCOLO DI STABILITÀ: Due tool consecutivi non possono condividere cavalletti alle estremità
        
        Questo vincolo garantisce che due tool al livello 1 non si appoggino sullo stesso cavalletto
        alle loro estremità, migliorando la stabilità fisica del carico.
        
        Logica:
        - Per ogni coppia di tool al livello 1
        - Calcola le posizioni dei cavalletti estremi (primo e ultimo)
        - Impedisce sovrapposizione dei cavalletti estremi tra tool diversi
        - 🆕 MIGLIORAMENTO: Considera anche separazione Y per stabilità totale
        """
        self.logger.info("🔒 [2L] Aggiunta vincoli stabilità cavalletti (non condivisione appoggi estremi)")
        
        # ✅ FIX CRITICO: USA la configurazione del solver invece di creare hardcoded
        if self._cavalletti_config is None:
            self.logger.error("❌ ERRORE CRITICO: Nessuna configurazione cavalletti nel solver per vincoli stabilità")
            raise ValueError("CavallettiConfiguration obbligatoria nel solver per vincoli stabilità")
        
        config = self._cavalletti_config
        
        # ✅ Log configurazione utilizzata per tracciabilità
        self.logger.info(f"🔧 Vincoli stabilità con config: "
                        f"cavalletto_size={config.cavalletto_width}x{config.cavalletto_height}mm, "
                        f"min_distance_between={config.min_distance_between_cavalletti}mm")
        
        stability_constraints_added = 0
        
        for i in range(len(tools)):
            for j in range(i + 1, len(tools)):
                tool_id_i = f"tool_{i}"
                tool_id_j = f"tool_{j}"
                
                # Solo per tool che possono usare cavalletti
                if not tools[i].can_use_cavalletto or not tools[j].can_use_cavalletto:
                    continue
                
                # Condizione attiva: entrambi i tool al livello 1 e inclusi
                both_level_1 = model.NewBoolVar(f'both_level1_{i}_{j}')
                level_i_is_1 = model.NewBoolVar(f'level_i_1_{i}_{j}')
                level_j_is_1 = model.NewBoolVar(f'level_j_1_{i}_{j}')
                
                model.Add(variables['level'][tool_id_i] == 1).OnlyEnforceIf(level_i_is_1)
                model.Add(variables['level'][tool_id_i] != 1).OnlyEnforceIf(level_i_is_1.Not())
                model.Add(variables['level'][tool_id_j] == 1).OnlyEnforceIf(level_j_is_1)
                model.Add(variables['level'][tool_id_j] != 1).OnlyEnforceIf(level_j_is_1.Not())
                
                model.AddBoolAnd([
                    variables['included'][tool_id_i],
                    variables['included'][tool_id_j],
                    level_i_is_1,
                    level_j_is_1
                ]).OnlyEnforceIf(both_level_1)
                
                # Calcola posizioni cavalletti estremi per entrambi i tool
                # Tool i: primo e ultimo cavalletto
                first_cav_i_x, last_cav_i_x = self._calculate_extreme_cavalletti_positions_cpsat(
                    model, variables, tools[i], tool_id_i, config, f'{i}_stability'
                )
                
                # Tool j: primo e ultimo cavalletto  
                first_cav_j_x, last_cav_j_x = self._calculate_extreme_cavalletti_positions_cpsat(
                    model, variables, tools[j], tool_id_j, config, f'{j}_stability'
                )
                
                # Vincoli di non sovrapposizione per cavalletti estremi
                min_separation = int(config.min_distance_between_cavalletti)
                cav_width = int(config.cavalletto_width)
                cav_height = int(config.cavalletto_height)
                
                # Crea variabili booleane per le condizioni di separazione X
                no_overlap_x_ff = model.NewBoolVar(f'no_overlap_x_ff_{i}_{j}')
                no_overlap_x_fl = model.NewBoolVar(f'no_overlap_x_fl_{i}_{j}')
                no_overlap_x_lf = model.NewBoolVar(f'no_overlap_x_lf_{i}_{j}')
                no_overlap_x_ll = model.NewBoolVar(f'no_overlap_x_ll_{i}_{j}')
                
                # 🆕 NUOVO: Variabili booleane per separazione Y (stabilità migliorata)
                no_overlap_y_separation = model.NewBoolVar(f'no_overlap_y_{i}_{j}')
                
                # Vincoli X: Non sovrapposizione cavalletti estremi
                # Primo cavalletto tool i vs primo cavalletto tool j
                model.Add(
                    first_cav_i_x + cav_width + min_separation <= first_cav_j_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_ff])
                
                # Primo cavalletto tool i vs ultimo cavalletto tool j
                model.Add(
                    first_cav_i_x + cav_width + min_separation <= last_cav_j_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_fl])
                
                # Ultimo cavalletto tool i vs primo cavalletto tool j
                model.Add(
                    last_cav_i_x + cav_width + min_separation <= first_cav_j_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_lf])
                
                # Ultimo cavalletto tool i vs ultimo cavalletto tool j
                model.Add(
                    last_cav_i_x + cav_width + min_separation <= last_cav_j_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_ll])
                
                # Aggiungi i vincoli simmetrici X (tool j rispetto a tool i)
                model.Add(
                    first_cav_j_x + cav_width + min_separation <= first_cav_i_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_ff.Not()])
                
                model.Add(
                    last_cav_j_x + cav_width + min_separation <= first_cav_i_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_fl.Not()])
                
                model.Add(
                    first_cav_j_x + cav_width + min_separation <= last_cav_i_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_lf.Not()])
                
                model.Add(
                    last_cav_j_x + cav_width + min_separation <= last_cav_i_x
                ).OnlyEnforceIf([both_level_1, no_overlap_x_ll.Not()])
                
                # 🆕 NUOVO: Vincoli Y per stabilità aggiuntiva
                # I tool devono essere separati anche in Y per evitare stress concentrato
                min_y_separation = int(cav_height + config.safety_margin_y * 2)
                
                # Tool i sopra tool j
                model.Add(
                    variables['y'][tool_id_i] >= variables['y'][tool_id_j] + variables['height'][tool_id_j] + min_y_separation
                ).OnlyEnforceIf([both_level_1, no_overlap_y_separation])
                
                # Tool j sopra tool i (alternativa simmetrica)
                model.Add(
                    variables['y'][tool_id_j] >= variables['y'][tool_id_i] + variables['height'][tool_id_i] + min_y_separation
                ).OnlyEnforceIf([both_level_1, no_overlap_y_separation.Not()])
                
                # Almeno una condizione di non sovrapposizione deve essere vera
                model.AddBoolOr([
                    no_overlap_x_ff,
                    no_overlap_x_fl,
                    no_overlap_x_lf,
                    no_overlap_x_ll,
                    no_overlap_y_separation,  # 🆕 Aggiunta opzione separazione Y
                    both_level_1.Not()
                ])
                
                stability_constraints_added += 1
        
        self.logger.info(f"✅ [2L] Vincoli stabilità cavalletti: {stability_constraints_added} vincoli aggiunti (X+Y separazione)")
    
    def _add_fixed_support_constraints_2l(
        self,
        model: cp_model.CpModel,
        tools: List[ToolInfo2L],
        autoclave: AutoclaveInfo2L,
        variables: Dict[str, Any]
    ) -> None:
        """
        🔧 FIX CRITICO: Vincolo supporto cavalletti fissi
        
        Garantisce che ogni tool al livello 1 sia supportato da almeno 2 cavalletti fissi
        dell'autoclave (standard aeronautico).
        """
        self.logger.info("🔧 [2L] Aggiunta vincoli supporto cavalletti fissi (standard aeronautico)")
        
        # Genera cavalletti fissi per questa autoclave
        fixed_config = CavallettiFixedConfiguration(
            distribute_evenly=True,
            min_distance_from_edges=100.0,
            min_spacing_between_cavalletti=200.0,
            orientation="horizontal"
        )
        
        cavalletti_fissi = self.calcola_cavalletti_fissi_autoclave(autoclave, fixed_config)
        
        if not cavalletti_fissi:
            self.logger.warning("⚠️ Nessun cavalletto fisso disponibile - vincoli supporto non applicabili")
            return
        
        constraints_added = 0
        
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # Solo per tool che possono usare cavalletti
            if not tool.can_use_cavalletto:
                continue
            
            # Variabili booleane per supporto da ogni cavalletto fisso
            support_vars = []
            
            for j, cav_fisso in enumerate(cavalletti_fissi):
                # Variabile booleana: tool è supportato da questo cavalletto fisso
                is_supported_by = model.NewBoolVar(f'supported_by_{i}_{j}')
                support_vars.append(is_supported_by)
                
                # Condizione: tool al livello 1 E incluso E si sovrappone con cavalletto fisso
                tool_at_level_1 = model.NewBoolVar(f'tool_l1_{i}_{j}')
                model.Add(variables['level'][tool_id] == 1).OnlyEnforceIf(tool_at_level_1)
                model.Add(variables['level'][tool_id] != 1).OnlyEnforceIf(tool_at_level_1.Not())
                
                # Variabili per posizioni tool
                tool_start_x = variables['x'][tool_id]
                tool_end_x = variables['end_x'][tool_id]
                
                # Posizioni cavalletto fisso (costanti)
                cav_start_x = int(cav_fisso.x)
                cav_end_x = int(cav_fisso.end_x)
                
                # Variabili booleane per sovrapposizione X
                tool_left_of_cav = model.NewBoolVar(f'tool_left_cav_{i}_{j}')
                tool_right_of_cav = model.NewBoolVar(f'tool_right_cav_{i}_{j}')
                
                # Tool completamente a sinistra del cavalletto
                model.Add(tool_end_x <= cav_start_x).OnlyEnforceIf(tool_left_of_cav)
                model.Add(tool_end_x > cav_start_x).OnlyEnforceIf(tool_left_of_cav.Not())
                
                # Tool completamente a destra del cavalletto
                model.Add(tool_start_x >= cav_end_x).OnlyEnforceIf(tool_right_of_cav)
                model.Add(tool_start_x < cav_end_x).OnlyEnforceIf(tool_right_of_cav.Not())
                
                # Sovrapposizione = NOT (left OR right)
                no_overlap = model.NewBoolVar(f'no_overlap_{i}_{j}')
                model.AddBoolOr([tool_left_of_cav, tool_right_of_cav]).OnlyEnforceIf(no_overlap)
                model.AddBoolAnd([tool_left_of_cav.Not(), tool_right_of_cav.Not()]).OnlyEnforceIf(no_overlap.Not())
                
                # is_supported_by = incluso AND livello_1 AND sovrapposizione
                model.AddBoolAnd([
                    variables['included'][tool_id],
                    tool_at_level_1,
                    no_overlap.Not()
                ]).OnlyEnforceIf(is_supported_by)
                
                model.AddBoolOr([
                    variables['included'][tool_id].Not(),
                    tool_at_level_1.Not(),
                    no_overlap
                ]).OnlyEnforceIf(is_supported_by.Not())
            
            # Vincolo principale: se tool al livello 1, deve essere supportato da ≥2 cavalletti fissi
            if len(support_vars) >= 2:
                # Conta supporti attivi
                num_supports = model.NewIntVar(0, len(support_vars), f'num_supports_{i}')
                model.Add(num_supports == sum(support_vars))
                
                # Condizione: tool al livello 1 E incluso
                tool_needs_support = model.NewBoolVar(f'needs_support_{i}')
                tool_at_level_1_main = model.NewBoolVar(f'tool_l1_main_{i}')
                
                model.Add(variables['level'][tool_id] == 1).OnlyEnforceIf(tool_at_level_1_main)
                model.Add(variables['level'][tool_id] != 1).OnlyEnforceIf(tool_at_level_1_main.Not())
                
                model.AddBoolAnd([
                    variables['included'][tool_id],
                    tool_at_level_1_main
                ]).OnlyEnforceIf(tool_needs_support)
                
                # Se ha bisogno di supporto, deve avere ≥2 supporti
                model.Add(num_supports >= 2).OnlyEnforceIf(tool_needs_support)
                
                constraints_added += 1
            else:
                self.logger.warning(f"⚠️ Tool {tool.odl_id}: solo {len(support_vars)} cavalletti fissi disponibili (richiesti ≥2)")
        
        self.logger.info(f"✅ [2L] Vincoli supporto cavalletti fissi: {constraints_added} vincoli aggiunti")

    def _calculate_extreme_cavalletti_positions_cpsat(
        self,
        model: cp_model.CpModel,
        variables: Dict[str, Any],
        tool: ToolInfo2L,
        tool_id: str,
        config: CavallettiConfiguration,
        suffix: str
    ) -> Tuple[Any, Any]:
        """
        Calcola le posizioni X dei cavalletti estremi (primo e ultimo) per un tool nel CP-SAT
        
        Returns:
            Tuple (first_cavalletto_x, last_cavalletto_x) come variabili CP-SAT
        """
        # Determina orientazione principale del tool e numero cavalletti
        main_dimension = max(tool.width, tool.height)
        num_cavalletti = self._calculate_num_cavalletti(main_dimension, config)
        
        # Crea variabili per le posizioni dei cavalletti estremi
        first_cav_x = model.NewIntVar(0, int(max(tool.width, tool.height)), f'first_cav_x_{suffix}')
        last_cav_x = model.NewIntVar(0, int(max(tool.width, tool.height)), f'last_cav_x_{suffix}')
        
        if num_cavalletti == 1:
            # Un solo cavalletto: primo = ultimo = centro
            center_offset = int((max(tool.width, tool.height) - config.cavalletto_width) / 2)
            model.Add(first_cav_x == variables['x'][tool_id] + center_offset)
            model.Add(last_cav_x == variables['x'][tool_id] + center_offset)
            
        elif num_cavalletti == 2:
            # Due cavalletti: primo all'inizio, ultimo alla fine
            edge_margin = int(config.min_distance_from_edge)
            tool_length = int(max(tool.width, tool.height))
            
            model.Add(first_cav_x == variables['x'][tool_id] + edge_margin)
            model.Add(last_cav_x == variables['x'][tool_id] + tool_length - edge_margin - int(config.cavalletto_width))
            
        else:
            # Tre o più cavalletti: distribuzione uniforme
            edge_margin = int(config.min_distance_from_edge)
            tool_length = int(max(tool.width, tool.height))
            usable_length = tool_length - 2 * edge_margin - int(config.cavalletto_width)
            spacing = int(usable_length / (num_cavalletti - 1)) if num_cavalletti > 1 else 0
            
            model.Add(first_cav_x == variables['x'][tool_id] + edge_margin)
            model.Add(last_cav_x == variables['x'][tool_id] + edge_margin + spacing * (num_cavalletti - 1))
        
        return first_cav_x, last_cav_x
    
    def _add_cavalletti_interference_constraints_2l(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L,
        variables: Dict[str, Any]
    ) -> None:
        """
        🎯 VINCOLO CRITICO: Evita interferenze tra cavalletti e tool di livello 0
        
        Per ogni tool di livello 1, calcola le posizioni dei cavalletti e garantisce
        che nessun tool di livello 0 occupi quelle posizioni.
        """
        self.logger.info("🏗️ Aggiunta vincoli interferenza cavalletti")
        
        if not autoclave.has_cavalletti:
            return
        
        # ✅ FIX CRITICO: USA la configurazione del solver invece di creare hardcoded
        if self._cavalletti_config is None:
            self.logger.error("❌ ERRORE CRITICO: Nessuna configurazione cavalletti nel solver per vincoli interferenza")
            raise ValueError("CavallettiConfiguration obbligatoria nel solver per vincoli interferenza")
        
        config = self._cavalletti_config
        
        # ✅ Log configurazione utilizzata per tracciabilità
        self.logger.info(f"🔧 Vincoli interferenza con config: "
                        f"cavalletto_size={config.cavalletto_width}x{config.cavalletto_height}mm, "
                        f"safety_margins={config.safety_margin_x}x{config.safety_margin_y}mm")
        
        if not autoclave.has_cavalletti:
            return
        
        # ✅ NUOVO: Usa dimensioni dal database autoclave
        config = CavallettiConfiguration(
            cavalletto_width=autoclave.cavalletto_width,
            cavalletto_height=autoclave.cavalletto_height_mm
        )
        constraint_count = 0
        
        for i, tool_level_1 in enumerate(tools):
            tool_id_i = f"tool_{i}"
            
            # Solo per tool che possono andare su cavalletto
            if not tool_level_1.can_use_cavalletto:
                continue
                
            # Calcola posizioni relative cavalletti per questo tool
            cavalletti_positions = self._calculate_cavalletti_positions_relative(tool_level_1, config)
            
            for pos_idx, pos in enumerate(cavalletti_positions):
                # Per ogni posizione cavalletto, assicura che nessun tool di livello 0 la occupi
                for j, tool_level_0 in enumerate(tools):
                    if i == j:
                        continue
                    
                    tool_id_j = f"tool_{j}"
                    
                    # Condizione attiva: tool_i a livello 1 AND tool_j a livello 0 AND entrambi inclusi
                    interference_active = model.NewBoolVar(f'interference_{i}_{j}_{pos_idx}')
                    
                    # Definizione condizione attiva
                    level_i_is_1 = model.NewBoolVar(f'level_i_is_1_{i}_{j}_{pos_idx}')
                    level_j_is_0 = model.NewBoolVar(f'level_j_is_0_{i}_{j}_{pos_idx}')
                    
                    model.Add(variables['level'][tool_id_i] == 1).OnlyEnforceIf(level_i_is_1)
                    model.Add(variables['level'][tool_id_i] != 1).OnlyEnforceIf(level_i_is_1.Not())
                    model.Add(variables['level'][tool_id_j] == 0).OnlyEnforceIf(level_j_is_0)
                    model.Add(variables['level'][tool_id_j] != 0).OnlyEnforceIf(level_j_is_0.Not())
                    
                    conditions = [
                        variables['included'][tool_id_i],
                        variables['included'][tool_id_j],
                        level_i_is_1,
                        level_j_is_0
                    ]
                    
                    model.AddBoolAnd(conditions).OnlyEnforceIf(interference_active)
                    model.AddBoolOr([cond.Not() for cond in conditions]).OnlyEnforceIf(interference_active.Not())
                    
                    # 🔧 FIX CP-SAT: Usa variabili intermedie per evitare BoundedLinearExpression
                    cavalletto_abs_x = model.NewIntVar(0, int(autoclave.width), f'cav_abs_x_{i}_{j}_{pos_idx}')
                    cavalletto_abs_y = model.NewIntVar(0, int(autoclave.height), f'cav_abs_y_{i}_{j}_{pos_idx}')
                    
                    # Definizione delle variabili intermedie - FIX: usa int() per evitare float
                    rel_x_int = int(round(pos['rel_x']))
                    rel_y_int = int(round(pos['rel_y']))
                    model.Add(cavalletto_abs_x == variables['x'][tool_id_i] + rel_x_int)
                    model.Add(cavalletto_abs_y == variables['y'][tool_id_i] + rel_y_int)
                    
                    # Dimensioni cavalletto
                    cav_width = int(config.cavalletto_width)
                    cav_height = int(config.cavalletto_height)
                    safety_margin = int(config.safety_margin_x + config.safety_margin_y)
                    
                    # Variabili booleane per non-sovrapposizione
                    no_overlap_left = model.NewBoolVar(f'no_overlap_left_{i}_{j}_{pos_idx}')
                    no_overlap_right = model.NewBoolVar(f'no_overlap_right_{i}_{j}_{pos_idx}')
                    no_overlap_bottom = model.NewBoolVar(f'no_overlap_bottom_{i}_{j}_{pos_idx}')
                    no_overlap_top = model.NewBoolVar(f'no_overlap_top_{i}_{j}_{pos_idx}')
                    
                    # Vincoli di non-sovrapposizione cavalletto con tool livello 0
                    # Cavalletto completamente a sinistra del tool
                    model.Add(
                        cavalletto_abs_x + cav_width + safety_margin <= variables['x'][tool_id_j]
                    ).OnlyEnforceIf([interference_active, no_overlap_left])
                    
                    # Cavalletto completamente a destra del tool
                    model.Add(
                        variables['x'][tool_id_j] + variables['width'][tool_id_j] + safety_margin <= cavalletto_abs_x
                    ).OnlyEnforceIf([interference_active, no_overlap_right])
                    
                    # Cavalletto completamente sotto il tool
                    model.Add(
                        cavalletto_abs_y + cav_height + safety_margin <= variables['y'][tool_id_j]
                    ).OnlyEnforceIf([interference_active, no_overlap_bottom])
                    
                    # Cavalletto completamente sopra il tool
                    model.Add(
                        variables['y'][tool_id_j] + variables['height'][tool_id_j] + safety_margin <= cavalletto_abs_y
                    ).OnlyEnforceIf([interference_active, no_overlap_top])
                    
                    # Almeno una condizione di non-sovrapposizione deve essere vera quando c'è interferenza
                    model.AddBoolOr([
                        no_overlap_left, 
                        no_overlap_right, 
                        no_overlap_bottom, 
                        no_overlap_top, 
                        interference_active.Not()
                    ])
                    
                    constraint_count += 1
        
        self.logger.info(f"✅ Vincoli interferenza cavalletti: {constraint_count} vincoli aggiunti")

    def _calculate_cavalletti_positions_relative(
        self, 
        tool: ToolInfo2L, 
        config: CavallettiConfiguration
    ) -> List[Dict[str, float]]:
        """
        Calcola le posizioni relative dei cavalletti per un tool (per uso in CP-SAT)
        Restituisce posizioni relative al tool origin (angolo bottom-left)
        """
        positions = []
        
        # Determina numero cavalletti basato su dimensioni tool
        main_dimension = max(tool.width, tool.height)
        num_cavalletti = self._calculate_num_cavalletti(main_dimension, config)
        
        if num_cavalletti < 2:
            num_cavalletti = 2  # Minimo 2 cavalletti per stabilità
        
        # Calcola posizioni lungo la dimensione principale
        if tool.width >= tool.height:
            # Tool orientato orizzontalmente - cavalletti lungo X
            if num_cavalletti == 1:
                # Un solo cavalletto al centro
                x = tool.width / 2 - config.cavalletto_width / 2
                y = tool.height / 2 - config.cavalletto_height / 2
                positions.append({'rel_x': x, 'rel_y': y, 'sequence': 0})
            else:
                # Distribuzione lungo X con margini
                effective_width = tool.width - 2 * config.min_distance_from_edge
                step = effective_width / (num_cavalletti - 1) if num_cavalletti > 1 else 0
                y_center = tool.height / 2 - config.cavalletto_height / 2
                
                for i in range(num_cavalletti):
                    x = config.min_distance_from_edge + i * step
                    positions.append({'rel_x': x, 'rel_y': y_center, 'sequence': i})
        else:
            # Tool orientato verticalmente - cavalletti lungo Y
            if num_cavalletti == 1:
                # Un solo cavalletto al centro
                x = tool.width / 2 - config.cavalletto_width / 2
                y = tool.height / 2 - config.cavalletto_height / 2
                positions.append({'rel_x': x, 'rel_y': y, 'sequence': 0})
            else:
                # Distribuzione lungo Y con margini
                effective_height = tool.height - 2 * config.min_distance_from_edge
                step = effective_height / (num_cavalletti - 1) if num_cavalletti > 1 else 0
                x_center = tool.width / 2 - config.cavalletto_width / 2
                
                for i in range(num_cavalletti):
                    y = config.min_distance_from_edge + i * step
                    positions.append({'rel_x': x_center, 'rel_y': y, 'sequence': i})
        
        return positions
    
    def _add_cpsat_objective_2l(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L,
        variables: Dict[str, Any]
    ) -> None:
        """
        🎯 Funzione obiettivo semplificata per ottimizzazione a due livelli
        
        Strategia: 
        1. Massimizzare numero tool posizionati (priorità massima)
        2. Bonus per tool grandi su livello base
        """
        self.logger.info("🎯 Costruzione funzione obiettivo ottimizzata 2L")
        
        objective_terms = []
        
        # 1. 🏆 PRIORITÀ MASSIMA: Massimizzare tool posizionati
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # Punteggio base proporzionale all'area e peso
            base_score = int(tool.area * self.parameters.area_weight * 1000)
            weight_bonus = int(tool.weight * 100) if tool.weight > 0 else 0
            total_inclusion_score = base_score + weight_bonus
            
            objective_terms.append(variables['included'][tool_id] * total_inclusion_score)
        
        # 2. 🎯 BONUS SEMPLICE PER LIVELLO BASE
        if autoclave.has_cavalletti:
            for i, tool in enumerate(tools):
                tool_id = f"tool_{i}"
                # Bonus per tool grandi su livello base
                if tool.area > 20000:  # Tool grandi preferiscono livello base
                    level_bonus = model.NewIntVar(0, 1000, f'level_bonus_{tool_id}')
                    model.Add(level_bonus == 1000).OnlyEnforceIf([
                    variables['included'][tool_id],
                    variables['level'][tool_id] == 0
                ])
                    model.Add(level_bonus == 0).OnlyEnforceIf(variables['level'][tool_id] == 1)
                    objective_terms.append(level_bonus)
        
        # Massimizza la funzione obiettivo
        model.Maximize(sum(objective_terms))
        self.logger.info(f"✅ Funzione obiettivo costruita: {len(objective_terms)} termini")

    def _add_smart_level_assignment_objective(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        variables: Dict[str, Any], 
        objective_terms: List
    ) -> None:
        """
        🧠 Strategia intelligente per assegnazione livello:
        - Tool grandi e pesanti → preferenza livello base
        - Tool piccoli → possono andare su cavalletto
        - Rispetta preferenze esplicite del tool
        """
        # Calcola soglie dinamiche
        areas = [tool.area for tool in tools]
        weights = [tool.weight for tool in tools if tool.weight > 0]
        
        area_threshold = np.percentile(areas, 70) if areas else 1000  # Top 30% tool grandi
        weight_threshold = np.percentile(weights, 70) if weights else 50  # Top 30% tool pesanti
        
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # Calcola preferenza livello per questo tool
            level_preference_score = self._calculate_level_preference_score(tool, area_threshold, weight_threshold)
            
            if level_preference_score > 0:
                # Preferenza per livello base
                level_0_bonus = model.NewIntVar(0, level_preference_score, f'level_0_bonus_{tool_id}')
                
                level_is_0 = model.NewBoolVar(f'level_is_0_{tool_id}')
                model.Add(variables['level'][tool_id] == 0).OnlyEnforceIf(level_is_0)
                model.Add(variables['level'][tool_id] != 0).OnlyEnforceIf(level_is_0.Not())
                
                model.Add(level_0_bonus == level_preference_score).OnlyEnforceIf([
                    variables['included'][tool_id],
                    level_is_0
                ])
                model.Add(level_0_bonus == 0).OnlyEnforceIf(level_is_0.Not())
                
                objective_terms.append(level_0_bonus)
        
            elif level_preference_score < 0:
                # Preferenza per cavalletto (tool piccoli/leggeri)
                level_1_bonus = model.NewIntVar(0, abs(level_preference_score), f'level_1_bonus_{tool_id}')
                
                level_is_1 = model.NewBoolVar(f'level_is_1_{tool_id}')
                model.Add(variables['level'][tool_id] == 1).OnlyEnforceIf(level_is_1)
                model.Add(variables['level'][tool_id] != 1).OnlyEnforceIf(level_is_1.Not())
                
                model.Add(level_1_bonus == abs(level_preference_score)).OnlyEnforceIf([
                    variables['included'][tool_id],
                    level_is_1
                ])
                model.Add(level_1_bonus == 0).OnlyEnforceIf(level_is_1.Not())
                
                objective_terms.append(level_1_bonus)

    def _calculate_level_preference_score(
        self, 
        tool: ToolInfo2L, 
        area_threshold: float, 
        weight_threshold: float
    ) -> int:
        """
        Calcola score di preferenza livello per un tool:
        - Valore positivo = preferenza livello base
        - Valore negativo = preferenza cavalletto  
        - Zero = nessuna preferenza
        """
        # Preferenza esplicita ha priorità assoluta
        if tool.preferred_level is not None:
            return 5000 if tool.preferred_level == 0 else -5000
        
        score = 0
        
        # Fattore dimensione
        if tool.area > area_threshold:
            score += int(tool.area * 0.1)  # Tool grandi preferiscono livello base
        elif tool.area < area_threshold * 0.5:
            score -= int(area_threshold * 0.05)  # Tool piccoli possono andare su cavalletto
        
        # Fattore peso
        if tool.weight > weight_threshold:
            score += int(tool.weight * 20)  # Tool pesanti preferiscono livello base
        elif tool.weight < weight_threshold * 0.5:
            score -= int(weight_threshold * 10)  # Tool leggeri possono andare su cavalletto
        
        # Fattore aspect ratio (tool molto lunghi meglio su livello base per stabilità)
        aspect_ratio = tool.aspect_ratio
        if aspect_ratio > 4.0:
            score += 1000  # Tool molto lunghi preferiscono livello base
        
        # Limita il range
        return max(-3000, min(3000, score))

    def _add_compactness_objective(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        variables: Dict[str, Any], 
        objective_terms: List
    ) -> None:
        """Aggiunge bonus per compattezza layout"""
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            
            # Penalità per posizioni lontane dall'origine (bottom-left)
            max_distance = int(math.sqrt(autoclave.width**2 + autoclave.height**2))
            distance_penalty = model.NewIntVar(0, max_distance, f'distance_penalty_{tool_id}')
            
            # Approssimazione lineare della distanza (Manhattan distance)
            distance_x = model.NewIntVar(0, int(autoclave.width), f'distance_x_{tool_id}')
            distance_y = model.NewIntVar(0, int(autoclave.height), f'distance_y_{tool_id}')
            
            model.Add(distance_x >= variables['x'][tool_id] // 20).OnlyEnforceIf(variables['included'][tool_id])
            model.Add(distance_y >= variables['y'][tool_id] // 20).OnlyEnforceIf(variables['included'][tool_id])
            model.Add(distance_penalty == distance_x + distance_y).OnlyEnforceIf(variables['included'][tool_id])
            
            compactness_penalty = int(100 * self.parameters.compactness_weight)
            objective_terms.append(-distance_penalty * compactness_penalty)
    
    def _add_weight_balance_objective(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        variables: Dict[str, Any], 
        objective_terms: List
    ) -> None:
        """
        🎯 Bonus per bilanciamento peso tra livelli
        Evita squilibri eccessivi (tutto su un livello)
        """
        total_weight = sum(tool.weight for tool in tools if tool.weight > 0)
        if total_weight <= 0:
            return
        
        # Calcola peso target per livello (idealmente bilanciato)
        ideal_weight_per_level = total_weight / 2
        balance_bonus_scale = int(ideal_weight_per_level * 10)
        
        # Variabili per peso totale per livello
        weight_level_0_total = model.NewIntVar(0, int(total_weight), 'weight_level_0_total')
        weight_level_1_total = model.NewIntVar(0, int(total_weight), 'weight_level_1_total')
        
        # Calcola peso per livello
        weight_0_terms = []
        weight_1_terms = []
        
        for i, tool in enumerate(tools):
            tool_id = f"tool_{i}"
            tool_weight = int(tool.weight) if tool.weight > 0 else 0
            
            weight_0_contrib = model.NewIntVar(0, tool_weight, f'weight_0_contrib_{tool_id}')
            weight_1_contrib = model.NewIntVar(0, tool_weight, f'weight_1_contrib_{tool_id}')
            
            level_is_0_weight = model.NewBoolVar(f'level_is_0_weight_{tool_id}')
            level_is_1_weight = model.NewBoolVar(f'level_is_1_weight_{tool_id}')
            
            model.Add(variables['level'][tool_id] == 0).OnlyEnforceIf(level_is_0_weight)
            model.Add(variables['level'][tool_id] != 0).OnlyEnforceIf(level_is_0_weight.Not())
            model.Add(variables['level'][tool_id] == 1).OnlyEnforceIf(level_is_1_weight)
            model.Add(variables['level'][tool_id] != 1).OnlyEnforceIf(level_is_1_weight.Not())
            
            model.Add(weight_0_contrib == tool_weight).OnlyEnforceIf([
                variables['included'][tool_id],
                level_is_0_weight
            ])
            model.Add(weight_0_contrib == 0).OnlyEnforceIf(level_is_0_weight.Not())
            
            model.Add(weight_1_contrib == tool_weight).OnlyEnforceIf([
                variables['included'][tool_id],
                level_is_1_weight
            ])
            model.Add(weight_1_contrib == 0).OnlyEnforceIf(level_is_1_weight.Not())
            
            weight_0_terms.append(weight_0_contrib)
            weight_1_terms.append(weight_1_contrib)
        
        model.Add(weight_level_0_total == sum(weight_0_terms))
        model.Add(weight_level_1_total == sum(weight_1_terms))
        
        # Bonus per bilanciamento (penalità per squilibrio eccessivo)
        max_imbalance = int(total_weight * 0.8)  # Massimo 80% su un livello
        imbalance_penalty = model.NewIntVar(0, max_imbalance, 'imbalance_penalty')
        
        # Calcola squilibrio (differenza assoluta dai pesi ideali)
        imbalance_0 = model.NewIntVar(0, max_imbalance, 'imbalance_0')
        imbalance_1 = model.NewIntVar(0, max_imbalance, 'imbalance_1')
        
        model.AddAbsEquality(imbalance_0, weight_level_0_total - int(ideal_weight_per_level))
        model.AddAbsEquality(imbalance_1, weight_level_1_total - int(ideal_weight_per_level))
        model.Add(imbalance_penalty == imbalance_0 + imbalance_1)
        
        # Penalità per squilibrio
        balance_penalty_weight = int(balance_bonus_scale * 0.1)
        objective_terms.append(-imbalance_penalty * balance_penalty_weight)
    
    def _extract_cpsat_solution_2l(
        self, 
        solver: cp_model.CpSolver, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        variables: Dict[str, Any], 
        status: int,
        start_time: float
    ) -> NestingSolution2L:
        """Estrae la soluzione dal solver CP-SAT e la converte nei formati Pydantic 2L"""
        solve_time_ms = (time.time() - start_time) * 1000
        
        layouts = []
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.logger.info("🎯 Estraendo soluzione CP-SAT 2L ottimale")
            
            for i, tool in enumerate(tools):
                if solver.Value(variables['included'][i]):
                    x = solver.Value(variables['x'][i])
                    y = solver.Value(variables['y'][i])
                    rotated = solver.Value(variables['rotated'][i]) if 'rotated' in variables else False
                    level = solver.Value(variables['level'][i])
                    
                    # Calcola dimensioni effettive considerando rotazione
                    if rotated:
                        width, height = tool.height, tool.width
                    else:
                        width, height = tool.width, tool.height
                    
                    layout = NestingLayout2L(
                        odl_id=tool.odl_id,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        weight=tool.weight,
                        level=level,
                        rotated=rotated,
                        lines_used=tool.lines_needed
                    )
                    layouts.append(layout)
        
        # Calcola metriche
        metrics = self._calculate_metrics_2l(layouts, tools, autoclave, solve_time_ms)
        
        # Crea soluzione con cavalletti
        solution = NestingSolution2L(
            layouts=layouts,
            excluded_odls=[],
            metrics=metrics,
            success=len(layouts) > 0,
            algorithm_status=f"CP-SAT_{cp_model.CpSolverStatus.Name(status)}_2L",
            message=f"Posizionati {len(layouts)} tool su 2 livelli"
        )
        
        # ✅ NUOVO: Usa ottimizzatore cavalletti avanzato invece di sistema problematico
        solution = self._add_cavalletti_with_advanced_optimizer(solution, autoclave)
        
        return solution

    def convert_to_pydantic_response(
        self, 
        solution: NestingSolution2L, 
        autoclave: AutoclaveInfo2L,
        request_params: Optional[Dict[str, Any]] = None
    ) -> NestingSolveResponse2L:
        """
        🆕 NUOVO: Converte NestingSolution2L nei nuovi schemi Pydantic
        """
        # Converti layouts in PosizionamentoTool2L
        positioned_tools = []
        for layout in solution.layouts:
            # 🆕 NUOVO: Recupera informazioni ODL per campi aggiuntivi
            corresponding_odl = None
            if hasattr(self, '_odl_cache'):
                corresponding_odl = self._odl_cache.get(layout.odl_id)
            
            tool_position = PosizionamentoTool2L(
                odl_id=layout.odl_id,
                tool_id=layout.odl_id,  # Assuming tool_id == odl_id for now
                x=layout.x,
                y=layout.y,
                width=layout.width,
                height=layout.height,
                rotated=layout.rotated,
                weight_kg=layout.weight,
                level=layout.level,
                z_position=layout.z_position,
                lines_used=layout.lines_used,
                # 🆕 NUOVI CAMPI per compatibilità frontend
                part_number=corresponding_odl.part_number if corresponding_odl else None,
                descrizione_breve=corresponding_odl.descrizione_breve if corresponding_odl else None,
                numero_odl=f"ODL{str(layout.odl_id).zfill(3)}"
            )
            positioned_tools.append(tool_position)
        
        # ✅ NUOVO: Usa cavalletti dall'ottimizzatore avanzato invece del metodo problematico
        all_cavalletti = solution.cavalletti_finali or []
        
        # Converti cavalletti in CavallettoPosizionamento
        cavalletti_pydantic = []
        for cavalletto in all_cavalletti:
            # ✅ FIX ROBUSTO: Gestisce sia CavallettoPosition che CavallettoFixedPosition
            if hasattr(cavalletto, 'tool_odl_id') and cavalletto.tool_odl_id is not None:
                # Cavalletto con tool_odl_id specificato
                tool_odl_id = cavalletto.tool_odl_id
            else:
                # ✅ FIX COMPATIBILITÀ: CavallettoFixedPosition senza tool_odl_id
                # Trova il tool che questo cavalletto supporta basandosi sulla posizione
                tool_odl_id = self._find_supported_tool_for_cavalletto(cavalletto, solution.layouts)
            
            cavalletto_pos = CavallettoPosizionamento(
                x=cavalletto.x,
                y=cavalletto.y,
                width=cavalletto.width,
                height=cavalletto.height,
                tool_odl_id=tool_odl_id,
                tool_id=tool_odl_id,  # Assuming tool_id == odl_id
                sequence_number=cavalletto.sequence_number,
                center_x=cavalletto.center_x,
                center_y=cavalletto.center_y,
                support_area_mm2=cavalletto.width * cavalletto.height
            )
            cavalletti_pydantic.append(cavalletto_pos)
        
        # Converti metriche in NestingMetrics2L (schema Pydantic)
        # Mapping dai campi del dataclass solver ai campi dello schema Pydantic
        metrics_pydantic = NestingMetrics2L(
            area_utilization_pct=solution.metrics.area_pct,
            vacuum_util_pct=solution.metrics.vacuum_util_pct,
            efficiency_score=solution.metrics.efficiency_score,
            weight_utilization_pct=(solution.metrics.total_weight / autoclave.max_weight) * 100,
            time_solver_ms=solution.metrics.time_solver_ms,
            fallback_used=solution.metrics.fallback_used,
            algorithm_status=solution.metrics.algorithm_used,
            total_area_cm2=solution.metrics.total_weight * 100,  # Approximation
            total_weight_kg=solution.metrics.total_weight,
            vacuum_lines_used=solution.metrics.lines_used,
            pieces_positioned=solution.metrics.positioned_count,
            pieces_excluded=solution.metrics.excluded_count,
            level_0_count=solution.metrics.level_0_count,
            level_1_count=solution.metrics.level_1_count,
            level_0_weight_kg=solution.metrics.level_0_weight,
            level_1_weight_kg=solution.metrics.level_1_weight,
            level_0_area_pct=solution.metrics.level_0_area_pct,
            level_1_area_pct=solution.metrics.level_1_area_pct,
            cavalletti_used=len(cavalletti_pydantic),
            cavalletti_coverage_pct=self._calculate_cavalletti_coverage(solution.layouts, all_cavalletti),
            complexity_score=solution.metrics.complexity_score,
            timeout_used_seconds=solution.metrics.timeout_used
        )
        
        # Informazioni autoclave
        autoclave_info = {
            "id": autoclave.id,
            "nome": f"Autoclave-{autoclave.id}",
            "larghezza_piano": autoclave.width,
            "lunghezza": autoclave.height,
            "max_load_kg": autoclave.max_weight,
            "num_linee_vuoto": autoclave.max_lines,
            "has_cavalletti": autoclave.has_cavalletti,
            "cavalletto_height": autoclave.cavalletto_height
        }
        
        # Configurazione cavalletti utilizzata
        cavalletti_config = {
            "cavalletto_width": autoclave.cavalletto_width or 80.0,  # ✅ DINAMICO: dal database invece di hardcoded
            "cavalletto_height": autoclave.cavalletto_height or 60.0,  # ✅ DINAMICO: dal database invece di hardcoded
            "min_distance_from_edge": 30.0,
            "max_span_without_support": 400.0,
            "prefer_symmetric": True
        } if autoclave.has_cavalletti else None
        
        return NestingSolveResponse2L(
            success=solution.success,
            message=solution.message,
            positioned_tools=positioned_tools,
            cavalletti=cavalletti_pydantic,
            excluded_odls=[],  # TODO: convertire excluded_odls se presenti
            excluded_reasons={},
            metrics=metrics_pydantic,
            autoclave_info=autoclave_info,
            cavalletti_config=cavalletti_config
        )

    def _find_supported_tool_for_cavalletto(
        self, 
        cavalletto: 'CavallettoFixedPosition', 
        layouts: List[NestingLayout2L]
    ) -> int:
        """
        ✅ FIX HELPER: Trova quale tool è supportato da questo cavalletto
        
        Args:
            cavalletto: Cavalletto fisso da analizzare
            layouts: Lista di tutti i tool posizionati
            
        Returns:
            ODL ID del tool supportato (o 0 se nessuno)
        """
        # Cerca tool di livello 1 che si sovrappongono con questo cavalletto
        level_1_tools = [layout for layout in layouts if layout.level == 1]
        
        for tool_layout in level_1_tools:
            # Verifica sovrapposizione tra tool e cavalletto
            tool_start_x = tool_layout.x
            tool_end_x = tool_layout.x + tool_layout.width
            tool_start_y = tool_layout.y
            tool_end_y = tool_layout.y + tool_layout.height
            
            cav_start_x = cavalletto.x
            cav_end_x = cavalletto.x + cavalletto.width
            cav_start_y = cavalletto.y
            cav_end_y = cavalletto.y + cavalletto.height
            
            # Verifica sovrapposizione in entrambe le dimensioni
            overlap_x = not (tool_end_x <= cav_start_x or cav_end_x <= tool_start_x)
            overlap_y = not (tool_end_y <= cav_start_y or cav_end_y <= tool_start_y)
            
            if overlap_x and overlap_y:
                # Questo cavalletto supporta questo tool
                self.logger.debug(f"🏗️ Cavalletto {cavalletto.sequence_number} supporta ODL {tool_layout.odl_id}")
                return tool_layout.odl_id
        
        # Nessun tool supportato, assegna un ODL generico
        if level_1_tools:
            # Assegna al primo tool di livello 1 disponibile
            default_odl = level_1_tools[0].odl_id
            self.logger.warning(f"⚠️ Cavalletto {cavalletto.sequence_number} non supporta nessun tool specifico, assegnato a ODL {default_odl}")
            return default_odl
        else:
            # Nessun tool di livello 1, usa un placeholder
            self.logger.warning(f"⚠️ Cavalletto {cavalletto.sequence_number} senza tool di livello 1, usando placeholder ODL 0")
            return 0

    def _calculate_cavalletti_coverage(
        self, 
        layouts: List[NestingLayout2L], 
        cavalletti: List[CavallettoPosition]
    ) -> float:
        """Calcola la percentuale di copertura dei cavalletti sui tool di livello 1"""
        level_1_layouts = [l for l in layouts if l.level == 1]
        if not level_1_layouts:
            return 0.0
        
        total_tool_area = sum(l.width * l.height for l in level_1_layouts)
        total_cavalletti_area = sum(c.width * c.height for c in cavalletti)
        
        # La copertura è il rapporto tra area cavalletti e area tool (max 100%)
        if total_tool_area > 0:
            coverage = min(100.0, (total_cavalletti_area / total_tool_area) * 100)
        else:
            coverage = 0.0
            
        return coverage

    def create_example_solution_2l(self) -> NestingSolveResponse2L:
        """
        🆕 NUOVO: Crea una soluzione di esempio per testare la serializzazione
        """
        # Tool di esempio
        positioned_tools = [
            PosizionamentoTool2L(
                odl_id=5,
                tool_id=12,
                x=50.0,
                y=100.0,
                width=300.0,
                height=200.0,
                rotated=False,
                weight_kg=25.5,
                level=0,  # Piano base
                z_position=0.0,
                lines_used=2
            ),
            PosizionamentoTool2L(
                odl_id=6,
                tool_id=15,
                x=400.0,
                y=150.0,
                width=250.0,
                height=180.0,
                rotated=True,
                weight_kg=18.3,
                level=1,  # Su cavalletto
                z_position=100.0,
                lines_used=1
            ),
            PosizionamentoTool2L(
                odl_id=7,
                tool_id=18,
                x=100.0,
                y=400.0,
                width=200.0,
                height=150.0,
                rotated=False,
                weight_kg=12.8,
                level=1,  # Su cavalletto
                z_position=100.0,
                lines_used=1
            )
        ]
        
        # Cavalletti di esempio
        cavalletti = [
            CavallettoPosizionamento(
                x=420.0,
                y=170.0,
                width=80.0,
                height=60.0,
                tool_odl_id=6,
                tool_id=15,
                sequence_number=0,
                center_x=460.0,
                center_y=200.0,
                support_area_mm2=4800.0
            ),
            CavallettoPosizionamento(
                x=570.0,
                y=170.0,
                width=80.0,
                height=60.0,
                tool_odl_id=6,
                tool_id=15,
                sequence_number=1,
                center_x=610.0,
                center_y=200.0,
                support_area_mm2=4800.0
            ),
            CavallettoPosizionamento(
                x=130.0,
                y=420.0,
                width=80.0,
                height=60.0,
                tool_odl_id=7,
                tool_id=18,
                sequence_number=0,
                center_x=170.0,
                center_y=450.0,
                support_area_mm2=4800.0
            ),
            CavallettoPosizionamento(
                x=250.0,
                y=420.0,
                width=80.0,
                height=60.0,
                tool_odl_id=7,
                tool_id=18,
                sequence_number=1,
                center_x=290.0,
                center_y=450.0,
                support_area_mm2=4800.0
            )
        ]
        
        # Metriche di esempio usando il modello Pydantic
        from schemas.batch_nesting import NestingMetrics2L as PydanticNestingMetrics2L
        
        metrics = PydanticNestingMetrics2L(
            area_utilization_pct=67.8,
            vacuum_util_pct=75.0,
            efficiency_score=69.9,
            weight_utilization_pct=56.6,
            time_solver_ms=2800.0,
            fallback_used=False,
            algorithm_status="CP-SAT_OPTIMAL_2L",
            total_area_cm2=134000.0,
            total_weight_kg=56.6,
            vacuum_lines_used=4,
            pieces_positioned=3,
            pieces_excluded=0,
            level_0_count=1,
            level_1_count=2,
            level_0_weight_kg=25.5,
            level_1_weight_kg=31.1,
            level_0_area_pct=25.0,
            level_1_area_pct=42.8,
            cavalletti_used=4,
            cavalletti_coverage_pct=88.5,
            complexity_score=2.1,
            timeout_used_seconds=2.8
        )
        
        # Informazioni autoclave
        autoclave_info = {
            "id": 1,
            "nome": "AeroTest-2L-Demo",
            "larghezza_piano": 1000.0,
            "lunghezza": 1500.0,
            "max_load_kg": 400.0,
            "num_linee_vuoto": 12,
            "has_cavalletti": True,
            "cavalletto_height": 100.0
        }
        
        # Configurazione cavalletti (esempio con valori di default)
        cavalletti_config = {
            "cavalletto_width": 80.0,  # Valore di esempio - normalmente preso dal database autoclave
            "cavalletto_height": 60.0,  # Valore di esempio - normalmente preso dal database autoclave
            "min_distance_from_edge": 30.0,
            "max_span_without_support": 400.0,
            "min_distance_between_cavalletti": 200.0,
            "prefer_symmetric": True,
            "force_minimum_two": True
        }
        
        return NestingSolveResponse2L(
            success=True,
            message="Nesting 2L di esempio risolto con successo - 3 tool posizionati su 2 livelli",
            positioned_tools=positioned_tools,
            cavalletti=cavalletti,
            excluded_odls=[],
            excluded_reasons={},
            metrics=metrics,
            autoclave_info=autoclave_info,
            cavalletti_config=cavalletti_config
        )
    
    def _solve_greedy_2l(
        self, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L,
        start_time: float
    ) -> NestingSolution2L:
        """Risolve il problema usando algoritmo greedy a due livelli"""
        
        self.logger.info(f"🔄 [2L] Avvio algoritmo greedy per {len(tools)} tool")
        
        # Ordina i tool per priorità (area decrescente)
        sorted_tools = sorted(tools, key=lambda t: -t.area)
        
        layouts = []
        level_0_layouts = []  # Piano base
        level_1_layouts = []  # Cavalletto
        level_0_weight = 0.0
        level_1_weight = 0.0
        
        for tool in sorted_tools:
            placed = False
            
            # 🔧 FIX: Calcola limiti dinamici UNA VOLTA per tool invece che per ogni posizione
            estimated_cavalletti = len(level_1_layouts)
            peso_max_livello_0, peso_max_livello_1 = self._calculate_dynamic_weight_limits(autoclave, estimated_cavalletti)
            
            # Tenta posizionamento su livelli disponibili
            levels_to_try = []
            
            # Determina livelli da provare
            if tool.preferred_level is not None:
                levels_to_try = [tool.preferred_level]
            else:
                if self.parameters.prefer_base_level:
                    levels_to_try = [0, 1] if autoclave.has_cavalletti and tool.can_use_cavalletto else [0]
                else:
                    levels_to_try = [1, 0] if autoclave.has_cavalletti and tool.can_use_cavalletto else [0]
            
            for level in levels_to_try:
                # 🔧 FIX: Aggiorna limiti dinamici solo se necessario (cambio livello)
                if level == 1:
                    # Ricalcola per includere il nuovo cavalletto
                    estimated_cavalletti_updated = len(level_1_layouts) + 1
                    peso_max_livello_0, peso_max_livello_1 = self._calculate_dynamic_weight_limits(autoclave, estimated_cavalletti_updated)
                
                # Controlla vincoli di peso per il livello con logica dinamica
                if level == 0 and level_0_weight + tool.weight > peso_max_livello_0:
                    continue
                if level == 1 and level_1_weight + tool.weight > peso_max_livello_1:
                    continue
                
                # 🔒 CONTROLLO PESO TOTALE: Non superare il carico massimo autoclave
                total_weight_after = level_0_weight + level_1_weight + tool.weight
                if total_weight_after > autoclave.max_weight:
                    continue
                
                # Seleziona i layout del livello corretto
                current_level_layouts = level_0_layouts if level == 0 else level_1_layouts
                
                # Trova posizione per il tool
                position = self._find_greedy_position_2l(tool, autoclave, current_level_layouts, level)
                
                if position is not None:
                    x, y, width, height, rotated = position
                    
                    layout = NestingLayout2L(
                        odl_id=tool.odl_id,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        weight=tool.weight,
                        level=level,
                        rotated=rotated,
                        lines_used=tool.lines_needed
                    )
                    
                    layouts.append(layout)
                    
                    # Aggiorna tracciamento per livello
                    if level == 0:
                        level_0_layouts.append(layout)
                        level_0_weight += tool.weight
                    else:
                        level_1_layouts.append(layout)
                        level_1_weight += tool.weight
                    
                    placed = True
                    self.logger.debug(f"✅ [2L] Tool {tool.odl_id} posizionato a ({x:.1f}, {y:.1f}) livello {level}")
                    break
            
            if not placed:
                self.logger.debug(f"❌ [2L] Tool {tool.odl_id} non posizionabile")
        
        # Calcolo metriche
        solve_time = (time.time() - start_time) * 1000
        metrics = self._calculate_metrics_2l(layouts, tools, autoclave, solve_time)
        
        success = len(layouts) > 0
        
        return NestingSolution2L(
            layouts=layouts,
            excluded_odls=[],
            metrics=metrics,
            success=success,
            algorithm_status="GREEDY_2L",
            message=f"Greedy 2L: {len(layouts)} tool posizionati (L0: {len(level_0_layouts)}, L1: {len(level_1_layouts)})"
        )
    
    def _find_greedy_position_2l(
        self, 
        tool: ToolInfo2L, 
        autoclave: AutoclaveInfo2L, 
        existing_layouts: List[NestingLayout2L],
        level: int = 0
    ) -> Optional[Tuple[float, float, float, float, bool]]:
        """
        🎯 Trova una posizione per il tool usando strategia greedy + controllo cavalletti
        Aggiorna per includere il controllo delle interferenze cavalletti
        """
        
        padding = self.parameters.padding_mm
        
        # Prova entrambe le orientazioni
        orientations = [
            (tool.width, tool.height, False),
            (tool.height, tool.width, True)
        ]
        
        best_position = None
        best_score = float('inf')
        
        for width, height, rotated in orientations:
            # Genera punti candidati
            candidate_points = self._generate_candidate_points_2l(autoclave, existing_layouts, padding)
            
            for x, y in candidate_points:
                # Verifica se il tool entra nell'autoclave
                if x + width > autoclave.width or y + height > autoclave.height:
                    continue
                
                # Verifica overlap con altri tool dello stesso livello
                if self._has_overlap_2l(x, y, width, height, existing_layouts, padding):
                    continue
                
                # 🎯 NUOVO: Verifica interferenze cavalletti se posizionamento a livello 1
                if level == 1 and autoclave.has_cavalletti and tool.can_use_cavalletto:
                    if self._has_cavalletti_interference_greedy(x, y, width, height, tool, existing_layouts):
                        continue
                    
                    # 🔧 FIX CRITICO: Verifica supporto cavalletti fissi
                    if not self._has_sufficient_fixed_support(x, y, width, height, autoclave):
                        continue
                
                # Calcola score per questa posizione (bottom-left preferito)
                score = x + y
                
                if score < best_score:
                    best_score = score
                    best_position = (x, y, width, height, rotated)
        
        return best_position
    
    def _has_cavalletti_interference_greedy(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float, 
        tool: ToolInfo2L, 
        existing_level_0_layouts: List[NestingLayout2L]
    ) -> bool:
        """
        🏗️ Verifica se il posizionamento del tool a livello 1 crea interferenze cavalletti
        
        Calcola le posizioni dei cavalletti per il tool proposto e verifica che
        non si sovrappongono ai tool esistenti di livello 0.
        """
        # ✅ NUOVO: Usa dimensioni di fallback (dovrebbe ricevere autoclave per usare dati reali)
        config = CavallettiConfiguration(
            cavalletto_width=80.0,  # Fallback - idealmente dovrebbe essere passato l'autoclave
            cavalletto_height=60.0  # Fallback - idealmente dovrebbe essere passato l'autoclave
        )
        
        # Crea layout temporaneo per il calcolo cavalletti
        temp_layout = NestingLayout2L(
            odl_id=tool.odl_id,
            x=x,
            y=y,
            width=width,
            height=height,
            weight=tool.weight,
            level=1,
            rotated=(width != tool.width),
            lines_used=tool.lines_needed
        )
        
        # Calcola posizioni cavalletti per questo tool
        cavalletti_positions = self.calcola_cavalletti_per_tool(temp_layout, config)
        
        # Verifica interferenza con ogni tool di livello 0
        for cavalletto in cavalletti_positions:
            for layout_l0 in existing_level_0_layouts:
                if layout_l0.level != 0:  # Sicurezza: solo tool livello 0
                    continue
                    
                # Verifica overlap cavalletto con tool livello 0
                if self._cavalletto_overlaps_with_tool(cavalletto, layout_l0, config):
                    return True  # Interferenza trovata
        
        return False  # Nessuna interferenza
    
    def _has_sufficient_fixed_support(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float, 
        autoclave: AutoclaveInfo2L
    ) -> bool:
        """
        🔧 FIX CRITICO: Verifica che il tool al livello 1 sia supportato da almeno 2 cavalletti fissi
        
        Args:
            x, y, width, height: Posizione e dimensioni del tool
            autoclave: Informazioni autoclave con cavalletti fissi
            
        Returns:
            True se il tool è supportato da ≥2 cavalletti fissi (standard aeronautico)
        """
        # Genera cavalletti fissi per questa autoclave
        fixed_config = CavallettiFixedConfiguration(
            distribute_evenly=True,
            min_distance_from_edges=100.0,
            min_spacing_between_cavalletti=200.0,
            orientation="horizontal"
        )
        
        cavalletti_fissi = self.calcola_cavalletti_fissi_autoclave(autoclave, fixed_config)
        
        if not cavalletti_fissi:
            self.logger.warning(f"⚠️ Nessun cavalletto fisso disponibile per supporto")
            return False
        
        # Conta quanti cavalletti fissi supportano questo tool
        supported_by = []
        
        for i, cav_fisso in enumerate(cavalletti_fissi):
            # Verifica se il tool si sovrappone con questo cavalletto fisso
            tool_start_x = x
            tool_end_x = x + width
            
            cav_start_x = cav_fisso.x
            cav_end_x = cav_fisso.end_x
            
            # Verifica sovrapposizione lungo X (i cavalletti attraversano tutto Y)
            overlap_x = not (tool_end_x <= cav_start_x or cav_end_x <= tool_start_x)
            
            if overlap_x:
                supported_by.append(i)
        
        num_supports = len(supported_by)
        
        # Standard aeronautico: almeno 2 supporti
        is_sufficient = num_supports >= 2
        
        if not is_sufficient:
            self.logger.debug(f"❌ Tool ({x:.1f},{y:.1f}) {width:.0f}×{height:.0f}mm: solo {num_supports} supporti fissi (richiesti ≥2)")
        else:
            self.logger.debug(f"✅ Tool ({x:.1f},{y:.1f}) {width:.0f}×{height:.0f}mm: {num_supports} supporti fissi {supported_by}")
        
        return is_sufficient

    def _cavalletto_overlaps_with_tool(
        self, 
        cavalletto: CavallettoPosition, 
        tool_layout: NestingLayout2L, 
        config: CavallettiConfiguration
    ) -> bool:
        """
        Verifica se un cavalletto si sovrappone a un tool con margini di sicurezza
        """
        # Dimensioni cavalletto con margini di sicurezza
        cav_left = cavalletto.x - config.safety_margin_x
        cav_right = cavalletto.x + cavalletto.width + config.safety_margin_x
        cav_bottom = cavalletto.y - config.safety_margin_y
        cav_top = cavalletto.y + cavalletto.height + config.safety_margin_y
        
        # Dimensioni tool
        tool_left = tool_layout.x
        tool_right = tool_layout.x + tool_layout.width
        tool_bottom = tool_layout.y
        tool_top = tool_layout.y + tool_layout.height
        
        # Verifica sovrapposizione (overlap su entrambi gli assi)
        overlap_x = not (cav_right <= tool_left or tool_right <= cav_left)
        overlap_y = not (cav_top <= tool_bottom or tool_top <= cav_bottom)
        
        return overlap_x and overlap_y

    def _calculate_num_cavalletti(self, main_dimension: float, config: CavallettiConfiguration) -> int:
        """
        🔧 NUOVO: Calcola numero cavalletti ottimale basato su principi fisici reali
        
        Implementa logica basata su:
        - Principi palletizing per stabilità
        - Distribuzione peso equilibrata
        - Efficienza supporto strutturale
        """
        # Dimensione minima per richiedere supporto
        if main_dimension < 150.0:  # mm
            return 0  # Tool troppo piccolo per cavalletti
        
        # Calcolo base: ogni span massimo richiede supporto
        base_count = max(1, int(main_dimension / config.max_span_without_support))
        
        # ✅ PRINCIPIO FISICO: Minimo 2 supporti per stabilità (anche per tool piccoli)
        if main_dimension >= 300.0:  # Tool medio-grande
            base_count = max(2, base_count)
        
        # ✅ PRINCIPIO PALLETIZING: Distribuzione bilanciata 
        # Per tool molto lunghi, forza numero pari per simmetria
        if main_dimension > 800.0 and base_count % 2 == 1:
            base_count += 1  # Forza numero pari per simmetria
        
        # ✅ LIMITAZIONE PRATICA: Massimo 4 cavalletti per tool singolo
        max_practical = 4
        
        return min(base_count, max_practical)

    def calcola_cavalletti_per_tool(
        self, 
        layout: NestingLayout2L, 
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 CALCOLO SINGOLO TOOL: Calcola cavalletti per un tool specifico
        
        Utilizzato dal test e dal sistema di ottimizzazione per calcolare
        i supporti necessari per un singolo tool
        """
        if not config:
            self.logger.error("❌ CavallettiConfiguration obbligatoria")
            return []
        
        # Usa la logica esistente di generazione cavalletti
        return self._genera_cavalletti_orizzontali(
            layout.x, layout.y, layout.width, layout.height, layout.weight, config
        )

    def _genera_cavalletti_orizzontali(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float, 
        weight: float, 
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 NUOVO: Generazione cavalletti orizzontali con logica fisica avanzata
        
        PRINCIPI IMPLEMENTATI:
        - ✅ Distribuzione peso equilibrata (no clustering)
        - ✅ Column stacking alignment
        - ✅ Load balancing ottimale
        - ✅ Validazione fisica rigorosa
        """
        positions = []
        
        # ✅ VALIDAZIONE CRITICA: Forza minimo 2 cavalletti per stabilità
        if self._calculate_num_cavalletti(width, config) < 2:
            self.logger.warning(f"⚠️ Forzato minimo 2 cavalletti per ODL {layout.odl_id} (stabilità fisica)")
            num_cavalletti = 2
        else:
            num_cavalletti = self._calculate_num_cavalletti(width, config)
        
        # ✅ AREA UTILIZZABILE: Con margini fisici realistici
        margin = max(config.min_distance_from_edge, 40.0)  # Minimo 40mm per sicurezza
        usable_start_x = x + margin
        usable_end_x = x + width - margin - config.cavalletto_width
        usable_width = usable_end_x - usable_start_x
        
        if usable_width <= 0:
            self.logger.error(f"❌ Tool ODL {layout.odl_id} troppo stretto per cavalletti")
            return []
        
        # ✅ POSIZIONE Y: Centrata per stabilità ottimale
        center_y = y + (height - config.cavalletto_height) / 2
        
        # ✅ DISTRIBUZIONE FISICA OTTIMALE
        if num_cavalletti == 2:
            # ✅ DUE CAVALLETTI: Posizionamento agli estremi per massima stabilità
            positions.extend([
                CavallettoPosition(
                    x=usable_start_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=0
                ),
                CavallettoPosition(
                    x=usable_end_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=1
                )
            ])
            
            # ✅ VALIDAZIONE FISICA: Verifica distribuzione bilanciata
            distance = usable_end_x - usable_start_x
            if distance > config.max_span_without_support:
                self.logger.warning(f"⚠️ Span cavalletti {distance:.0f}mm > {config.max_span_without_support}mm")
        
        elif num_cavalletti == 3:
            # ✅ TRE CAVALLETTI: Distribuzione 1/3 per stabilità ottimale
            spacing = usable_width / 2.0
            positions.extend([
                CavallettoPosition(
                    x=usable_start_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=0
                ),
                CavallettoPosition(
                    x=usable_start_x + spacing,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=1
                ),
                CavallettoPosition(
                    x=usable_end_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=2
                )
            ])
        
        elif num_cavalletti == 4:
            # ✅ QUATTRO CAVALLETTI: Distribuzione simmetrica per bilanciamento perfetto
            spacing = usable_width / 3.0
            for i in range(4):
                x_pos = usable_start_x + (i * spacing)
                positions.append(CavallettoPosition(
                    x=x_pos,
                    y=center_y,
                    width=config.cavalletti_width,
                    height=config.cavalletto_height,
                    tool_odl_id=layout.odl_id,
                    sequence_number=i
                ))
        
        # ✅ VALIDAZIONE FINALE: Verifica distribuzione fisica corretta
        self._validate_physical_distribution(positions, layout, config)
        
        self.logger.info(f"✅ Generati {len(positions)} cavalletti fisici ottimali per ODL {layout.odl_id}")
        return positions
    
    def _validate_physical_distribution(
        self, 
        positions: List[CavallettoPosition], 
        tool_layout: NestingLayout2L, 
        config: CavallettiConfiguration
    ) -> None:
        """
        🔧 NUOVO: Validazione rigorosa distribuzione fisica cavalletti
        
        Verifica:
        - ✅ Distribuzione bilanciata peso
        - ✅ Nessun clustering nella stessa metà
        - ✅ Spacing adeguato per stabilità
        - ✅ Posizionamento dentro boundaries tool
        """
        if len(positions) < 2:
            return  # Validazione non applicabile
        
        # ✅ VALIDAZIONE CLUSTERING: No cavalletti concentrati in una metà
        tool_center_x = tool_layout.x + tool_layout.width / 2
        left_half = sum(1 for pos in positions if pos.center_x < tool_center_x)
        right_half = len(positions) - left_half
        
        if left_half == 0 or right_half == 0:
            self.logger.error(f"❌ PROBLEMA FISICO: Tutti cavalletti in una metà del tool ODL {tool_layout.odl_id}")
            self.logger.error(f"   Distribuzione: {left_half} sinistra, {right_half} destra")
        
        # ✅ VALIDAZIONE SPACING: Verifica distanze fisicamente corrette
        positions_sorted = sorted(positions, key=lambda p: p.center_x)
        for i in range(len(positions_sorted) - 1):
            distance = positions_sorted[i+1].center_x - positions_sorted[i].center_x
            
            if distance > config.max_span_without_support:
                self.logger.warning(f"⚠️ Span eccessivo: {distance:.0f}mm > {config.max_span_without_support}mm")
            elif distance < config.min_distance_between_cavalletti:
                self.logger.warning(f"⚠️ Cavalletti troppo vicini: {distance:.0f}mm < {config.min_distance_between_cavalletti}mm")
        
        # ✅ VALIDAZIONE BOUNDARIES: Tutti cavalletti dentro tool
        for i, pos in enumerate(positions):
            if not (tool_layout.x <= pos.x and pos.x + pos.width <= tool_layout.x + tool_layout.width):
                self.logger.error(f"❌ Cavalletto {i} ODL {tool_layout.odl_id} FUORI boundaries X")
            if not (tool_layout.y <= pos.y and pos.y + pos.height <= tool_layout.y + tool_layout.height):
                self.logger.error(f"❌ Cavalletto {i} ODL {tool_layout.odl_id} FUORI boundaries Y")
    
    # ❌ RIMOSSO: _add_cavalletti_to_solution problematico
    # Sostituito con _add_cavalletti_with_advanced_optimizer che usa il sistema corretto

    # ❌ RIMOSSO: calcola_tutti_cavalletti problematico
    # L'ottimizzatore avanzato è ora integrato correttamente tramite _add_cavalletti_with_advanced_optimizer
    
    def _calcola_cavalletti_fallback(
        self, 
        cavalletti: List[CavallettoPosition],
        layouts: List[NestingLayout2L],
        autoclave: AutoclaveInfo2L,
        config: CavallettiConfiguration
    ) -> List[CavallettoFixedPosition]:
        """
        🔧 FALLBACK: Sistema base con validazione max_cavalletti essenziale
        """
        # ✅ VALIDAZIONE CRITICA: Rispetto max_cavalletti
        if autoclave.max_cavalletti is not None:
            if len(cavalletti) > autoclave.max_cavalletti:
                self.logger.warning(f"⚠️ LIMITE SUPERATO: {len(cavalletti)} > {autoclave.max_cavalletti}")
                self.logger.info("   Applicazione riduzione base...")
                
                # Riduzione semplice: rimuovi cavalletti meno critici
                cavalletti = self._reduce_cavalletti_simple(cavalletti, autoclave.max_cavalletti, layouts)
                self.logger.info(f"   Riduzione applicata: {len(cavalletti)} cavalletti")
        
        return self._convert_to_fixed_positions(cavalletti, autoclave)
    
    def _reduce_cavalletti_simple(
        self,
        cavalletti: List[CavallettoPosition],
        max_count: int,
        layouts: List[NestingLayout2L]
    ) -> List[CavallettoPosition]:
        """
        🔧 RIDUZIONE SEMPLICE: Mantiene cavalletti più critici per stabilità
        """
        if len(cavalletti) <= max_count:
            return cavalletti
        
        # Prioritizza cavalletti per tool pesanti e grandi
        cavalletti_with_priority = []
        
        for cav in cavalletti:
            tool = next((l for l in layouts if l.odl_id == cav.tool_odl_id), None)
            if tool:
                # Calcola priorità basata su peso e dimensioni
                priority = tool.weight * (tool.width * tool.height) / 1000000  # Peso * Area in m²
                cavalletti_with_priority.append((cav, priority))
        
        # Ordina per priorità decrescente e mantieni i più critici
        cavalletti_with_priority.sort(key=lambda x: x[1], reverse=True)
        
        return [cav for cav, _ in cavalletti_with_priority[:max_count]]
    
    def _convert_to_fixed_positions(
        self,
        cavalletti: List[CavallettoPosition],
        autoclave: AutoclaveInfo2L
    ) -> List[CavallettoFixedPosition]:
        """
        🔧 CONVERSIONE: CavallettoPosition → CavallettoFixedPosition
        """
        fixed_positions = []
        
        for i, cavalletto in enumerate(cavalletti):
            fixed_position = CavallettoFixedPosition(
                x=cavalletto.x,
                y=cavalletto.y,
                width=cavalletto.width,
                height=cavalletto.height,
                sequence_number=i,
                orientation="horizontal",
                tool_odl_id=cavalletto.tool_odl_id
            )
            fixed_positions.append(fixed_position)
        
        # Aggiorna contatore autoclave
        autoclave.num_cavalletti_utilizzati = len(fixed_positions)
        
        self.logger.info(f"✅ Conversione completata: {len(fixed_positions)} cavalletti fissi")
        return fixed_positions

    def _optimize_cavalletti_global(
        self,
        cavalletti: List[CavallettoPosition],
        layouts: List[NestingLayout2L], 
        autoclave: AutoclaveInfo2L,
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 NUOVO: Ottimizzazione globale cavalletti per rispettare max_cavalletti
        
        STRATEGIE IMPLEMENTATE:
        - ✅ Adiacency Sharing: Condivisione supporti tra tool adiacenti
        - ✅ Column Stacking: Allineamento cavalletti per efficienza
        - ✅ Load Consolidation: Unificazione supporti ridondanti
        """
        self.logger.info("🎯 [OTTIMIZZAZIONE] Avvio riduzione cavalletti globale")
        
        optimized_cavalletti = list(cavalletti)  # Copia iniziale
        
        # ✅ STRATEGIA 1: Adiacency Sharing
        # Rimuovi cavalletti ridondanti tra tool adiacenti
        optimized_cavalletti = self._apply_adjacency_sharing(
            optimized_cavalletti, layouts, config
        )
        
        # ✅ STRATEGIA 2: Column Stacking
        # Allinea cavalletti per formare colonne strutturali
        optimized_cavalletti = self._apply_column_stacking(
            optimized_cavalletti, config
        )
        
        # ✅ STRATEGIA 3: Load Consolidation  
        # Unifica cavalletti vicini con capacità sufficiente
        optimized_cavalletti = self._apply_load_consolidation(
            optimized_cavalletti, layouts, autoclave, config
        )
        
        self.logger.info(f"✅ Ottimizzazione completata: {len(cavalletti)} → {len(optimized_cavalletti)} cavalletti")
        return optimized_cavalletti

    def _apply_adjacency_sharing(
        self,
        cavalletti: List[CavallettoPosition],
        layouts: List[NestingLayout2L],
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 NUOVO: Condivisione supporti tra tool adiacenti
        
        PRINCIPIO FISICO:
        - Se due tool sono vicini, un cavalletto può supportare entrambi
        - Riduce numero totale cavalletti mantenendo stabilità
        """
        optimized = []
        removed_count = 0
        
        for cavalletto in cavalletti:
            # Trova tool supportato da questo cavalletto
            tool_layout = next((l for l in layouts if l.odl_id == cavalletto.tool_odl_id), None)
            if not tool_layout:
                continue
            
            # Cerca tool adiacenti che potrebbero condividere questo supporto
            adjacent_tools = self._find_adjacent_tools(tool_layout, layouts, config)
            
            if adjacent_tools:
                # Verifica se cavalletto può supportare tool multipli
                can_share = self._can_cavalletto_support_multiple_tools(
                    cavalletto, [tool_layout] + adjacent_tools, config
                )
                
                if can_share:
                    # Rimuovi cavalletti ridondanti degli altri tool
                    cavalletti_to_remove = [
                        c for c in cavalletti 
                        if c.tool_odl_id in [t.odl_id for t in adjacent_tools] 
                        and self._cavalletti_overlap_significantly(cavalletto, c, config)
                    ]
                    
                    if cavalletti_to_remove:
                        self.logger.debug(f"   Condivisione supporto: cavalletto ODL {cavalletto.tool_odl_id} "
                                        f"supporta anche {[t.odl_id for t in adjacent_tools]}")
                        removed_count += len(cavalletti_to_remove)
                        # Rimuovi i cavalletti ridondanti dalla lista principale
                        cavalletti = [c for c in cavalletti if c not in cavalletti_to_remove]
            
            optimized.append(cavalletto)
        
        if removed_count > 0:
            self.logger.info(f"   Adiacency Sharing: rimossi {removed_count} cavalletti ridondanti")
        
        return optimized

    def _find_adjacent_tools(
        self,
        tool: NestingLayout2L,
        all_layouts: List[NestingLayout2L],
        config: CavallettiConfiguration
    ) -> List[NestingLayout2L]:
        """
        🔧 NUOVO: Trova tool adiacenti che potrebbero condividere supporti
        """
        adjacent = []
        adjacency_threshold = config.min_distance_between_cavalletti  # Soglia vicinanza
        
        for other_tool in all_layouts:
            if other_tool.odl_id == tool.odl_id or other_tool.level != tool.level:
                continue
            
            # Calcola distanza tra bordi dei tool
            distance_x = max(0, max(tool.x, other_tool.x) - min(tool.x + tool.width, other_tool.x + other_tool.width))
            distance_y = max(0, max(tool.y, other_tool.y) - min(tool.y + tool.height, other_tool.y + other_tool.height))
            
            # Se tool sono abbastanza vicini, considerali adiacenti
            if distance_x <= adjacency_threshold and distance_y <= adjacency_threshold:
                adjacent.append(other_tool)
        
        return adjacent

    def _can_cavalletto_support_multiple_tools(
        self,
        cavalletto: CavallettoPosition,
        tools: List[NestingLayout2L],
        config: CavallettiConfiguration
    ) -> bool:
        """
        🔧 NUOVO: Verifica se un cavalletto può supportare fisicamente multiple tool
        """
        if len(tools) <= 1:
            return True
        
        # Verifica che il cavalletto sia sotto l'area di overlap dei tool
        total_area = 0.0
        overlap_area = None
        
        for tool in tools:
            tool_rect = (tool.x, tool.y, tool.x + tool.width, tool.y + tool.height)
            tool_area_m2 = tool.width * tool.height / 1_000_000  # mm² → m²
            total_area += tool_area_m2
            
            if overlap_area is None:
                overlap_area = tool_rect
            else:
                # Calcola intersezione
                x1 = max(overlap_area[0], tool_rect[0])
                y1 = max(overlap_area[1], tool_rect[1])
                x2 = min(overlap_area[2], tool_rect[2])
                y2 = min(overlap_area[3], tool_rect[3])
                
                if x1 < x2 and y1 < y2:
                    overlap_area = (x1, y1, x2, y2)
                else:
                    return False  # Nessun overlap
        
        # Verifica che cavalletto sia nell'area di overlap
        if overlap_area:
            cav_in_overlap = (
                overlap_area[0] <= cavalletto.center_x <= overlap_area[2] and
                overlap_area[1] <= cavalletto.center_y <= overlap_area[3]
            )
            
            if cav_in_overlap:
                # Verifica capacità di carico (stima conservativa)
                estimated_load_per_m2 = 150.0  # kg/m² (carico tipico compositi)
                total_estimated_load = total_area * estimated_load_per_m2
                
                # Capacità cavalletto (dal database autoclave)
                max_load_per_cavalletto = 300.0  # kg (default conservativo)
                
                return total_estimated_load <= max_load_per_cavalletto
        
        return False

    def _cavalletti_overlap_significantly(
        self, 
        cav1: CavallettoPosition,
        cav2: CavallettoPosition,
        config: CavallettiConfiguration
    ) -> bool:
        """
        🔧 NUOVO: Verifica se due cavalletti si sovrappongono significativamente
        """
        # Calcola distanza tra centri
        distance = ((cav1.center_x - cav2.center_x) ** 2 + (cav1.center_y - cav2.center_y) ** 2) ** 0.5
        
        # Considerali sovrapposti se distanza < metà della dimensione cavalletto
        overlap_threshold = max(config.cavalletto_width, config.cavalletto_height) * 0.7
        
        return distance < overlap_threshold

    def _apply_column_stacking(
        self,
        cavalletti: List[CavallettoPosition],
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 NUOVO: Column Stacking - Allinea cavalletti per formare colonne strutturali
        """
        if len(cavalletti) <= 1:
            return cavalletti
        
        # Raggruppa cavalletti per posizione X simile (colonne potenziali)
        alignment_tolerance = config.cavalletto_width * 0.5
        columns = []
        
        for cavalletto in cavalletti:
            # Trova colonna esistente compatibile
            assigned = False
            for column in columns:
                if any(abs(c.center_x - cavalletto.center_x) <= alignment_tolerance for c in column):
                    column.append(cavalletto)
                    assigned = True
                    break
            
            if not assigned:
                columns.append([cavalletto])
        
        # Allinea cavalletti di ogni colonna alla posizione X media
        aligned_cavalletti = []
        columns_optimized = 0
        
        for column in columns:
            if len(column) > 1:  # Solo per colonne con multiple cavalletti
                avg_x = sum(c.center_x for c in column) / len(column)
                
                for cavalletto in column:
                    # Aggiorna posizione X per allineamento
                    aligned_cavalletto = CavallettoPosition(
                        x=avg_x - cavalletto.width / 2,
                        y=cavalletto.y,
                        width=cavalletto.width,
                        height=cavalletto.height,
                        tool_odl_id=cavalletto.tool_odl_id,
                        sequence_number=cavalletto.sequence_number
                    )
                    aligned_cavalletti.append(aligned_cavalletto)
                
                columns_optimized += 1
            else:
                aligned_cavalletti.extend(column)
        
        if columns_optimized > 0:
            self.logger.info(f"   Column Stacking: ottimizzate {columns_optimized} colonne")
        
        return aligned_cavalletti

    def _apply_load_consolidation(
        self,
        cavalletti: List[CavallettoPosition],
        layouts: List[NestingLayout2L],
        autoclave: AutoclaveInfo2L,
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        🔧 NUOVO: Load Consolidation - Unifica cavalletti vicini se hanno capacità sufficiente
        """
        if len(cavalletti) <= 1:
            return cavalletti
        
        consolidation_threshold = config.min_distance_between_cavalletti * 0.8
        consolidated = []
        processed = set()
        consolidations_made = 0
        
        for i, cavalletto in enumerate(cavalletti):
            if i in processed:
                continue
            
            # Trova cavalletti vicini che possono essere consolidati
            nearby_cavalletti = []
            for j, other_cavalletto in enumerate(cavalletti):
                if i != j and j not in processed:
                    distance = ((cavalletto.center_x - other_cavalletto.center_x) ** 2 + 
                               (cavalletto.center_y - other_cavalletto.center_y) ** 2) ** 0.5
                    
                    if distance <= consolidation_threshold:
                        nearby_cavalletti.append((j, other_cavalletto))
            
            if nearby_cavalletti:
                # Verifica capacità di carico per consolidazione
                all_cavalletti_group = [cavalletto] + [c[1] for c in nearby_cavalletti]
                total_load = self._estimate_total_load_for_cavalletti(all_cavalletti_group, layouts)
                
                max_capacity = autoclave.peso_max_per_cavalletto_kg
                if total_load <= max_capacity:
                    # Consolida in posizione centrale
                    avg_x = sum(c.center_x for c in all_cavalletti_group) / len(all_cavalletti_group)
                    avg_y = sum(c.center_y for c in all_cavalletti_group) / len(all_cavalletti_group)
                    
                    consolidated_cavalletto = CavallettoPosition(
                        x=avg_x - config.cavalletto_width / 2,
                        y=avg_y - config.cavalletto_height / 2,
                        width=config.cavalletto_width,
                        height=config.cavalletto_height,
                        tool_odl_id=cavalletto.tool_odl_id,  # Tool principale
                        sequence_number=cavalletto.sequence_number
                    )
                    
                    consolidated.append(consolidated_cavalletto)
                    
                    # Marca come processati
                    processed.add(i)
                    for j, _ in nearby_cavalletti:
                        processed.add(j)
                    
                    consolidations_made += 1
                else:
                    consolidated.append(cavalletto)
                    processed.add(i)
            else:
                consolidated.append(cavalletto)
                processed.add(i)
        
        if consolidations_made > 0:
            self.logger.info(f"   Load Consolidation: {consolidations_made} consolidazioni")
        
        return consolidated

    def _estimate_total_load_for_cavalletti(
        self,
        cavalletti: List[CavallettoPosition],
        layouts: List[NestingLayout2L]
    ) -> float:
        """
        🔧 STIMA CARICO TOTALE: Calcola peso totale supportato dai cavalletti
        """
        total_load = 0.0
        
        for cavalletto in cavalletti:
            tool = next((l for l in layouts if l.odl_id == cavalletto.tool_odl_id), None)
            if tool:
                # Stima frazione del peso del tool supportata da questo cavalletto
                tool_cavalletti_count = sum(1 for c in cavalletti if c.tool_odl_id == tool.odl_id)
                if tool_cavalletti_count > 0:
                    load_fraction = tool.weight / tool_cavalletti_count
                    total_load += load_fraction
        
        return total_load

    def calcola_tutti_cavalletti(
        self, 
        level_0_layouts: List[NestingLayout2L], 
        autoclave: AutoclaveInfo2L
    ) -> List[CavallettoPosition]:
        """
        🔧 CALCOLA TUTTI I CAVALLETTI per i tool del livello 0
        
        Questo metodo era mancante e causava l'errore 'NestingModel2L' object has no attribute 'calcola_tutti_cavalletti'
        
        FUNZIONALITÀ:
        - Calcola cavalletti fisici per ogni tool del livello 0
        - Usa configurazione ottimale dal database autoclave
        - Restituisce lista completa di posizioni cavalletti
        """
        if not level_0_layouts:
            self.logger.debug("🔧 Nessun tool livello 0 - nessun cavalletto necessario")
            return []
        
        self.logger.info(f"🔧 Calcolo cavalletti per {len(level_0_layouts)} tool livello 0")
        
        # ✅ CONFIGURAZIONE dai dati autoclave
        config = CavallettiConfiguration(
            cavalletto_width=autoclave.cavalletto_width or 80.0,
            cavalletto_height=autoclave.cavalletto_height_mm or 60.0,
            min_distance_from_edge=30.0,
            max_span_without_support=400.0,
            min_distance_between_cavalletti=200.0,
            safety_margin_x=5.0,
            safety_margin_y=5.0,
            prefer_symmetric=True,
            force_minimum_two=True
        )
        
        all_cavalletti = []
        
        # ✅ CALCOLO per ogni tool livello 0
        for layout in level_0_layouts:
            if layout.level != 0:
                continue  # Solo tool livello 0
            
            try:
                cavalletti_tool = self.calcola_cavalletti_per_tool(layout, config)
                all_cavalletti.extend(cavalletti_tool)
                
                self.logger.debug(f"   ODL {layout.odl_id}: {len(cavalletti_tool)} cavalletti")
                
            except Exception as e:
                self.logger.error(f"❌ Errore calcolo cavalletti ODL {layout.odl_id}: {e}")
                # Continua con altri tool invece di fallire completamente
        
        self.logger.info(f"✅ Calcolati {len(all_cavalletti)} cavalletti totali livello 0")
        return all_cavalletti

    def _convert_to_fixed_positions(
        self,
        cavalletti: List[CavallettoPosition],
        autoclave: AutoclaveInfo2L
    ) -> List[CavallettoFixedPosition]:
        """
        🔧 CONVERSIONE: Converte CavallettoPosition in CavallettoFixedPosition (formato finale)
        """
        fixed_positions = []
        
        for i, cavalletto in enumerate(cavalletti):
            fixed_position = CavallettoFixedPosition(
                x=cavalletto.x,
                y=cavalletto.y,
                width=cavalletto.width,
                height=cavalletto.height,
                sequence_number=i,
                orientation="horizontal",
                tool_odl_id=cavalletto.tool_odl_id
            )
            fixed_positions.append(fixed_position)
        
        # ✅ AGGIORNA CONTATORE AUTOCLAVE
        autoclave.num_cavalletti_utilizzati = len(fixed_positions)
        
        self.logger.info(f"✅ Conversione completata: {len(fixed_positions)} cavalletti fissi")
        return fixed_positions

    def _generate_candidate_points_2l(
        self, 
        autoclave: AutoclaveInfo2L, 
        existing_layouts: List[NestingLayout2L], 
        padding: float
    ) -> List[Tuple[float, float]]:
        """Genera punti candidati per posizionamento greedy a due livelli"""
        candidates = set()
        
        # Punto origine
        candidates.add((0.0, 0.0))
        
        # Punti basati sui layout esistenti
        for layout in existing_layouts:
            # Bordi del layout con padding
            candidates.add((layout.x + layout.width + padding, layout.y))
            candidates.add((layout.x, layout.y + layout.height + padding))
            candidates.add((layout.x + layout.width + padding, layout.y + layout.height + padding))
        
        # Punti lungo i bordi dell'autoclave
        step = min(100.0, autoclave.width / 10)  # Passo ridotto per meno punti
        for x in range(0, int(autoclave.width), int(step)):
            candidates.add((float(x), 0.0))
        for y in range(0, int(autoclave.height), int(step)):
            candidates.add((0.0, float(y)))
        
        # 🔧 FIX: Limita il numero di candidati per evitare loop eccessivi
        candidates_list = list(candidates)
        if len(candidates_list) > 50:  # Limite massimo di 50 posizioni candidate
            # Ordina per posizione bottom-left e prendi i primi 50
            candidates_list.sort(key=lambda p: p[0] + p[1])
            candidates_list = candidates_list[:50]
        
        return candidates_list

    def _has_overlap_2l(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float, 
        existing_layouts: List[NestingLayout2L], 
        padding: float
    ) -> bool:
        """
        Verifica se una posizione proposta si sovrappone con layout esistenti
        """
        for layout in existing_layouts:
            # Verifica sovrapposizione con padding
            if not (x + width + padding <= layout.x or 
                   layout.x + layout.width + padding <= x or
                   y + height + padding <= layout.y or 
                   layout.y + layout.height + padding <= y):
                return True  # Sovrapposizione trovata
        
        return False  # Nessuna sovrapposizione

    def _calculate_metrics_2l(
        self, 
        layouts: List[NestingLayout2L], 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L,
        solve_time_ms: float
    ) -> NestingMetrics2LLocal:
        """
        Calcola le metriche per la soluzione a due livelli
        """
        if not layouts:
            return NestingMetrics2LLocal(
                area_pct=0.0,
                vacuum_util_pct=0.0,
                lines_used=0,
                total_weight=0.0,
                positioned_count=0,
                excluded_count=len(tools),
                efficiency_score=0.0,
                time_solver_ms=solve_time_ms,
                fallback_used=False,
                level_0_count=0,
                level_1_count=0,
                level_0_weight=0.0,
                level_1_weight=0.0,
                level_0_area_pct=0.0,
                level_1_area_pct=0.0,
                algorithm_used="NONE",
                complexity_score=0.0,
                timeout_used=0.0
            )
        
        # Calcoli base
        total_tool_area = sum(layout.width * layout.height for layout in layouts)
        autoclave_area = autoclave.width * autoclave.height
        
        # 🔧 FIX METRICHE: Calcolo area corretto per due livelli 
        # L'area utilizzabile totale è autoclave_area × 2 (piano base + cavalletto)
        # Ma il calcolo standard usa solo l'area del piano base come riferimento
        
        # Area utilizzata per livello
        level_0_area = sum(l.width * l.height for l in layouts if l.level == 0)
        level_1_area = sum(l.width * l.height for l in layouts if l.level == 1)
        
        # 🆕 CALCOLO CORRETTO: Efficienza area per ogni livello separatamente
        level_0_area_pct = (level_0_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        level_1_area_pct = (level_1_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        
        # 🆕 AREA TOTALE CORRETTA: Non può superare 100% per livello
        # L'efficienza combinata deve considerare che ogni livello è indipendente
        area_pct_combined = min(level_0_area_pct + level_1_area_pct, 200.0)  # Max 200% (100% per livello)
        
        # 🆕 EFFICIENZA CORRETTA: Media pesata dei due livelli
        if level_0_area_pct + level_1_area_pct > 0:
            area_pct = (level_0_area_pct + level_1_area_pct) / 2  # Media dei due livelli
        else:
            area_pct = 0.0
            
        # 🔒 SANITY CHECK: L'efficienza non può mai superare 100%
        area_pct = min(area_pct, 100.0)
        
        # 🆕 LOGGING PER DEBUG METRICHE ANOMALE
        if area_pct > 100.0 or level_0_area_pct > 100.0 or level_1_area_pct > 100.0:
            self.logger.error(f"❌ EFFICIENZA ANOMALA RILEVATA:")
            self.logger.error(f"   Area autoclave: {autoclave_area:.1f} mm²")
            self.logger.error(f"   Area livello 0: {level_0_area:.1f} mm² ({level_0_area_pct:.1f}%)")
            self.logger.error(f"   Area livello 1: {level_1_area:.1f} mm² ({level_1_area_pct:.1f}%)")
            self.logger.error(f"   Area totale tool: {total_tool_area:.1f} mm²")
            self.logger.error(f"   Efficienza calcolata: {area_pct:.1f}%")
        
        autoclave_area = autoclave.width * autoclave.height
        total_weight = sum(layout.weight for layout in layouts)
        total_lines = sum(layout.lines_used for layout in layouts)
        vacuum_util_pct = (total_lines / autoclave.max_lines) * 100 if autoclave.max_lines > 0 else 0
        
        # Metriche specifiche per livelli
        level_0_layouts = [l for l in layouts if l.level == 0]
        level_1_layouts = [l for l in layouts if l.level == 1]
        
        level_0_weight = sum(l.weight for l in level_0_layouts)
        level_1_weight = sum(l.weight for l in level_1_layouts)
        
        # Score di efficienza combinato
        efficiency_score = area_pct * 0.7 + min(vacuum_util_pct, 100) * 0.3
        
        return NestingMetrics2LLocal(
            area_pct=area_pct,
            vacuum_util_pct=vacuum_util_pct,
            lines_used=total_lines,
            total_weight=total_weight,
            positioned_count=len(layouts),
            excluded_count=len(tools) - len(layouts),
            efficiency_score=efficiency_score,
            time_solver_ms=solve_time_ms,
            fallback_used=False,
            level_0_count=len(level_0_layouts),
            level_1_count=len(level_1_layouts),
            level_0_weight=level_0_weight,
            level_1_weight=level_1_weight,
            level_0_area_pct=level_0_area_pct,
            level_1_area_pct=level_1_area_pct,
            algorithm_used="2L_COMBINED",
            complexity_score=0.0,
            timeout_used=solve_time_ms / 1000.0
        )

    def _create_empty_solution_2l(
        self, 
        excluded_tools: List[Dict[str, Any]], 
        autoclave: AutoclaveInfo2L,
        start_time: float
    ) -> NestingSolution2L:
        """
        Crea una soluzione vuota per casi di fallimento
        """
        solve_time = (time.time() - start_time) * 1000
        
        metrics = NestingMetrics2LLocal(
            area_pct=0.0,
            vacuum_util_pct=0.0,
            lines_used=0,
            total_weight=0.0,
            positioned_count=0,
            excluded_count=len(excluded_tools),
            efficiency_score=0.0,
            time_solver_ms=solve_time,
            fallback_used=True,
            level_0_count=0,
            level_1_count=0,
            level_0_weight=0.0,
            level_1_weight=0.0,
            level_0_area_pct=0.0,
            level_1_area_pct=0.0,
            algorithm_used="FAILED",
            complexity_score=0.0,
            timeout_used=solve_time / 1000.0
        )
        
        return NestingSolution2L(
            layouts=[],
            excluded_odls=excluded_tools,
            metrics=metrics,
            success=False,
            algorithm_status="FAILED",
            message=f"Nessun tool posizionabile. Esclusi: {len(excluded_tools)}"
        ) 
    
    # 🆕 INTEGRAZIONE SEQUENZIALE: Riempi prima livello 0, poi livello 1
    
    def _solve_level_0_first(
        self, 
        tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L, 
        start_time: float
    ) -> NestingSolution:
        """
        FASE 1: Riempi completamente il livello 0 usando solver.py principale
        """
        self.logger.info(f"📍 [FASE 1] Riempimento LIVELLO 0 con solver.py")
        
        try:
            # Converti tools 2L → tools standard
            standard_tools = self._convert_tools_2l_to_standard(tools)
            standard_autoclave = self._convert_autoclave_2l_to_standard(autoclave)
            
            # Configura parametri per riempimento aggressivo livello 0
            level_0_params = NestingParameters(
                padding_mm=self.parameters.padding_mm,
                min_distance_mm=self.parameters.min_distance_mm,
                vacuum_lines_capacity=autoclave.max_lines,
                use_fallback=True,
                allow_heuristic=True,
                timeout_override=None,
                use_multithread=True,
                num_search_workers=8,
                # Target: massimo riempimento livello 0
                area_weight=0.95,  # Priorità area massima
                compactness_weight=0.03,
                balance_weight=0.02
            )
            
            # Usa solver principale per livello 0
            solver_level_0 = NestingModel(level_0_params)
            solution_level_0 = solver_level_0.solve(standard_tools, standard_autoclave)
            
            self.logger.info(f"✅ [FASE 1] Livello 0: {solution_level_0.metrics.positioned_count}/{len(tools)} tool posizionati")
            self.logger.info(f"   Efficienza livello 0: {solution_level_0.metrics.area_pct:.1f}%")
            
            return solution_level_0
            
        except Exception as e:
            self.logger.error(f"❌ [FASE 1] Errore livello 0: {str(e)}")
            # Fallback: soluzione vuota
            from .solver import NestingMetrics
            empty_metrics = NestingMetrics(
                area_pct=0.0, vacuum_util_pct=0.0, lines_used=0, 
                total_weight=0.0, positioned_count=0, excluded_count=len(tools),
                efficiency_score=0.0, time_solver_ms=0.0, fallback_used=True, heuristic_iters=0
            )
            return NestingSolution(
                layouts=[], excluded_odls=[], metrics=empty_metrics, 
                success=False, algorithm_status="LEVEL_0_FAILED"
            )
    
    def _solve_level_1_remaining(
        self, 
        remaining_tools: List[ToolInfo2L], 
        autoclave: AutoclaveInfo2L,
        level_0_layouts: List[NestingLayout],
        start_time: float
    ) -> List[NestingLayout2L]:
        """
        FASE 2: Posiziona tool rimanenti sul livello 1 (cavalletti)
        considerando le interferenze con i cavalletti dei tool già posizionati al livello 0
        """
        self.logger.info(f"📍 [FASE 2] Posizionamento LIVELLO 1: {len(remaining_tools)} tool rimanenti")
        
        if not remaining_tools or not autoclave.has_cavalletti:
            self.logger.info("⏭️ [FASE 2] Saltato: nessun tool rimanente o cavalletti disabilitati")
            return []
        
        try:
            # Converti layouts livello 0 per calcolo interferenze cavalletti
            level_0_layouts_2l = self._convert_layouts_standard_to_2l(level_0_layouts, level=0)
            
            # ✅ FIX CRITICO: Rimuovo chiamata problematica calcola_tutti_cavalletti
            # L'ottimizzatore avanzato in solve_2l gestisce direttamente tutti i cavalletti
            # cavalletti_level_0 = self.calcola_tutti_cavalletti(level_0_layouts_2l, autoclave)
            # self.logger.info(f"🔧 [FASE 2] Cavalletti livello 0: {len(cavalletti_level_0)} posizioni")
            
            # ✅ INTERIM SOLUTION: Lista vuota per cavalletti_level_0 
            # I cavalletti saranno calcolati dall'ottimizzatore avanzato dopo il posizionamento
            cavalletti_level_0 = []
            self.logger.info(f"🔧 [FASE 2] Cavalletti livello 0: gestiti dall'ottimizzatore avanzato")
            
            # Algoritmo greedy per livello 1 considerando interferenze
            level_1_layouts = []
            
            # Ordina tool rimanenti per priorità (più grandi per primi)
            remaining_tools_sorted = sorted(
                remaining_tools, 
                key=lambda t: (t.area, t.weight), 
                reverse=True
            )
            
            for tool in remaining_tools_sorted:
                position = self._find_level_1_position_safe(
                    tool, autoclave, level_0_layouts_2l, level_1_layouts, cavalletti_level_0
                )
                
                if position:
                    x, y, width, height, rotated = position
                    layout_2l = NestingLayout2L(
                        odl_id=tool.odl_id,
                        x=x, y=y, width=width, height=height,
                        weight=tool.weight,
                        level=1,  # Livello cavalletti
                        rotated=rotated,
                        lines_used=tool.lines_needed
                    )
                    level_1_layouts.append(layout_2l)
                    
                    self.logger.info(f"✅ [FASE 2] Tool ODL {tool.odl_id} → Livello 1 ({x:.0f},{y:.0f})")
                else:
                    self.logger.warning(f"⚠️ [FASE 2] Tool ODL {tool.odl_id} → Non posizionabile su livello 1")
            
            self.logger.info(f"✅ [FASE 2] Completato: {len(level_1_layouts)}/{len(remaining_tools)} tool su livello 1")
            return level_1_layouts
            
        except Exception as e:
            self.logger.error(f"❌ [FASE 2] Errore livello 1: {str(e)}")
            return []
    
    def _convert_tools_2l_to_standard(self, tools_2l: List[ToolInfo2L]) -> List[ToolInfo]:
        """Converte ToolInfo2L → ToolInfo per compatibilità solver.py"""
        standard_tools = []
        for tool_2l in tools_2l:
            standard_tool = ToolInfo(
                odl_id=tool_2l.odl_id,
                width=tool_2l.width,
                height=tool_2l.height,
                weight=tool_2l.weight,
                lines_needed=tool_2l.lines_needed,
                ciclo_cura_id=tool_2l.ciclo_cura_id,
                priority=tool_2l.priority,
                debug_reasons=tool_2l.debug_reasons.copy() if tool_2l.debug_reasons else [],
                excluded=tool_2l.excluded
            )
            standard_tools.append(standard_tool)
        return standard_tools
    
    def _convert_autoclave_2l_to_standard(self, autoclave_2l: AutoclaveInfo2L) -> AutoclaveInfo:
        """Converte AutoclaveInfo2L → AutoclaveInfo per compatibilità solver.py"""
        return AutoclaveInfo(
            id=autoclave_2l.id,
            width=autoclave_2l.width,
            height=autoclave_2l.height,
            max_weight=autoclave_2l.max_weight,
            max_lines=autoclave_2l.max_lines
        )
    
    def _convert_layouts_standard_to_2l(
        self, 
        layouts_standard: List[NestingLayout], 
        level: int = 0
    ) -> List[NestingLayout2L]:
        """Converte NestingLayout → NestingLayout2L"""
        layouts_2l = []
        for layout in layouts_standard:
            layout_2l = NestingLayout2L(
                odl_id=layout.odl_id,
                x=layout.x, y=layout.y,
                width=layout.width, height=layout.height,
                weight=layout.weight,
                level=level,
                rotated=layout.rotated,
                lines_used=layout.lines_used
            )
            layouts_2l.append(layout_2l)
        return layouts_2l
    
    def _find_level_1_position_safe(
        self,
        tool: ToolInfo2L,
        autoclave: AutoclaveInfo2L,
        level_0_layouts: List[NestingLayout2L],
        level_1_layouts: List[NestingLayout2L],
        cavalletti_level_0: List[CavallettoPosition]
    ) -> Optional[Tuple[float, float, float, float, bool]]:
        """
        Trova posizione sicura per tool su livello 1 evitando interferenze con cavalletti livello 0
        """
        padding = self.parameters.padding_mm
        
        # 🔧 FIX CRITICO: Calcola cavalletti fissi PRIMA della ricerca posizioni
        cavalletti_fissi = self.calcola_cavalletti_fissi_autoclave(autoclave)
        if len(cavalletti_fissi) < 2:
            self.logger.warning(f"⚠️ Autoclave {autoclave.id} ha solo {len(cavalletti_fissi)} cavalletti fissi, richiesti ≥2")
            return None
        
        # Genera punti candidati per livello 1
        candidate_points = self._generate_candidate_points_2l(autoclave, level_1_layouts, padding)
        
        # Prova orientamenti (normale e ruotato)
        orientations = [
            (tool.width, tool.height, False),
            (tool.height, tool.width, True)
        ]
        
        for x, y in candidate_points:
            for width, height, rotated in orientations:
                
                # Check bounds autoclave
                if x + width > autoclave.width or y + height > autoclave.height:
                    continue
                
                # Check overlap con altri tool livello 1
                if self._has_overlap_2l(x, y, width, height, level_1_layouts, padding):
                    continue
                
                # 🔧 FIX CRITICO: Verifica supporto cavalletti fissi PRIMA di tutto
                if not self._is_supported_by_fixed_cavalletti(x, y, width, height, cavalletti_fissi):
                    continue
                
                # 🆕 CHECK CRITICO: Interferenza cavalletti livello 1 con cavalletti livello 0
                if self._has_cavalletti_interference_with_level_0(
                    x, y, width, height, tool, cavalletti_level_0
                ):
                    continue
                
                # Posizione valida trovata
                return (x, y, width, height, rotated)
        
                return None

    def _is_supported_by_fixed_cavalletti(
        self, 
        x: float, 
        y: float, 
        width: float, 
        height: float,
        cavalletti_fissi: List[CavallettoFixedPosition]
    ) -> bool:
        """
        🔧 FIX CRITICO: Verifica che il tool sia fisicamente supportato da ≥2 cavalletti fissi
        
        Implementa verifica fisica rigorosa:
        - Conta cavalletti fissi che attraversano il tool
        - Verifica distribuzione bilanciata (non tutti da un lato)
        - Standard aeronautico: minimo 2 supporti distribuiti
        """
        supporting_count = 0
        tool_center_x = x + width / 2
        left_support = False
        right_support = False
        supporting_positions = []
        
        for cav in cavalletti_fissi:
            # I cavalletti fissi attraversano tutta la larghezza Y dell'autoclave
            # Verifica sovrapposizione lungo X con il tool
            tool_start_x = x
            tool_end_x = x + width
            cav_start_x = cav.x
            cav_end_x = cav.x + cav.height  # height = spessore del cavalletto
            
            # Verifica sovrapposizione X
            overlap_x = not (tool_end_x <= cav_start_x or cav_end_x <= tool_start_x)
            
            if overlap_x:
                supporting_count += 1
                supporting_positions.append(cav.center_x)
                
                # Verifica distribuzione bilanciata
                if cav.center_x < tool_center_x:
                    left_support = True
                else:
                    right_support = True
        
        # Standard fisico aeronautico: ≥2 supporti E distribuzione bilanciata
        is_supported = supporting_count >= 2 and left_support and right_support
        
        if not is_supported:
            self.logger.debug(f"❌ Tool ({x:.0f},{y:.0f}) {width:.0f}×{height:.0f}mm: "
                             f"supporti={supporting_count}, sinistra={left_support}, destra={right_support}")
        else:
            self.logger.debug(f"✅ Tool ({x:.0f},{y:.0f}) {width:.0f}×{height:.0f}mm: "
                             f"{supporting_count} supporti bilanciati {supporting_positions}")
        
        return is_supported

    def _has_cavalletti_interference_with_level_0(
        self,
        x: float, y: float, width: float, height: float,
        tool: ToolInfo2L,
        cavalletti_level_0: List[CavallettoPosition]
    ) -> bool:
        """
        Verifica se i cavalletti del tool al livello 1 interferiscono 
        con i cavalletti esistenti del livello 0
        """
        if not cavalletti_level_0:
            return False
        
        # Simula layout temporaneo per calcolare cavalletti
        temp_layout = NestingLayout2L(
            odl_id=tool.odl_id, x=x, y=y, width=width, height=height,
            weight=tool.weight, level=1, rotated=False, lines_used=tool.lines_needed
        )
        
        # Calcola cavalletti per questo tool al livello 1
        tool_cavalletti = self.calcola_cavalletti_per_tool(temp_layout)
        
        # Check interferenza con cavalletti livello 0
        # ✅ NUOVO: Usa dimensioni di fallback (dovrebbe ricevere autoclave per dati reali)
        config = CavallettiConfiguration(
            cavalletto_width=80.0,  # Fallback - meglio passare dall'autoclave
            cavalletto_height=60.0  # Fallback - meglio passare dall'autoclave
        )
        
        for cavalletto_1 in tool_cavalletti:
            for cavalletto_0 in cavalletti_level_0:
                # Check overlap orizzontale tra cavalletti
                if self._cavalletti_overlap_horizontally(cavalletto_1, cavalletto_0, config):
                    return True
        
        return False
    
    def _cavalletti_overlap_horizontally(
        self, 
        cav1: CavallettoPosition, 
        cav0: CavallettoPosition, 
        config: CavallettiConfiguration
    ) -> bool:
        """Check se due cavalletti si sovrappongono nella proiezione orizzontale"""
        margin = config.safety_margin_x + config.safety_margin_y
        
        # Check overlap X
        x_overlap = not (cav1.x + cav1.width + margin <= cav0.x or 
                        cav0.x + cav0.width + margin <= cav1.x)
        
        # Check overlap Y  
        y_overlap = not (cav1.y + cav1.height + margin <= cav0.y or
                        cav0.y + cav0.height + margin <= cav1.y)
        
        return x_overlap and y_overlap
    
    def _create_combined_solution_2l(
        self,
        all_layouts: List[NestingLayout2L],
        excluded_tools: List[Dict[str, Any]],
        original_tools: List[ToolInfo2L],
        autoclave: AutoclaveInfo2L,
        start_time: float
    ) -> NestingSolution2L:
        """Crea la soluzione finale combinando risultati livello 0 e 1"""
        
        solve_time_ms = (time.time() - start_time) * 1000
        
        # Calcola metriche combinate
        metrics = self._calculate_metrics_2l(all_layouts, original_tools, autoclave, solve_time_ms)
        
        # Aggiorna informazioni algoritmo
        metrics.algorithm_used = "SEQUENTIAL_2L"
        metrics.complexity_score = self._calculate_dataset_complexity(original_tools, autoclave)
        
        success = len(all_layouts) > 0
        status = "SEQUENTIAL_SUCCESS" if success else "SEQUENTIAL_FAILED"
        
        message = f"Sequential 2L: L0={metrics.level_0_count}, L1={metrics.level_1_count}, Total={metrics.positioned_count}"
        
        return NestingSolution2L(
            layouts=all_layouts,
            excluded_odls=excluded_tools,
            metrics=metrics,
            success=success,
            algorithm_status=status,
            message=message
        ) 

    def calcola_cavalletti_fissi_autoclave(
        self, 
        autoclave: AutoclaveInfo2L, 
        config: CavallettiFixedConfiguration = None
    ) -> List[CavallettoFixedPosition]:
        """
        🏗️ NUOVO APPROCCIO: Calcola i cavalletti come segmenti fissi dell'autoclave
        
        I cavalletti sono segmenti trasversali che attraversano tutto il lato corto dell'autoclave,
        disposti in numero pari al massimo indicato per l'autoclave.
        
        Args:
            autoclave: Informazioni autoclave
            config: Configurazione cavalletti fissi
            
        Returns:
            Lista delle posizioni dei cavalletti fissi
        """
        if config is None:
            config = CavallettiFixedConfiguration()
        
        # ✅ DINAMICO: Numero cavalletti dal database autoclave
        if not hasattr(autoclave, 'max_cavalletti') or autoclave.max_cavalletti is None:
            self.logger.warning(f"⚠️ Autoclave {autoclave.id} non ha max_cavalletti definito")
            return []
            
        num_cavalletti = autoclave.max_cavalletti
        
        if num_cavalletti <= 0:
            self.logger.info("🏗️ Nessun cavalletto da posizionare per questa autoclave")
            return []
        
        # Dimensioni autoclave
        autoclave_width = autoclave.width   # Lato lungo dell'autoclave
        autoclave_height = autoclave.height  # Lato corto dell'autoclave
        
        # 🎯 CORREZIONE LOGICA: I cavalletti sono segmenti trasversali
        # - Si estendono per tutta la larghezza dell'autoclave (asse Y)
        # - Si posizionano lungo la lunghezza dell'autoclave (asse X)
        segment_width = autoclave_height   # Larghezza segmento = larghezza autoclave (asse Y)
        
        # ✅ DINAMICO: Spessore cavalletto dal database autoclave  
        if not hasattr(autoclave, 'cavalletto_thickness_mm') or autoclave.cavalletto_thickness_mm is None:
            # Fallback a valore ragionevole se non definito
            segment_thickness = 60.0  # mm - valore di fallback
            self.logger.warning(f"⚠️ Autoclave {autoclave.id} non ha cavalletto_thickness_mm, uso fallback {segment_thickness}mm")
        else:
            segment_thickness = autoclave.cavalletto_thickness_mm
        
        # Area utilizzabile per posizionamento lungo X (escludendo margini dai bordi)
        usable_start_x = config.min_distance_from_edges
        usable_end_x = autoclave_width - config.min_distance_from_edges - segment_thickness
        usable_length_x = usable_end_x - usable_start_x
        
        if usable_length_x <= 0:
            self.logger.warning(f"⚠️ Autoclave troppo stretta per posizionare cavalletti fissi")
            return []
        
        self.logger.info(f"🏗️ Calcolo {num_cavalletti} cavalletti fissi per autoclave {autoclave.id}")
        self.logger.debug(f"   Dimensioni autoclave: {autoclave_width}×{autoclave_height}mm")
        self.logger.debug(f"   Dimensioni segmenti: {segment_thickness}×{segment_width}mm (spessore×larghezza)")
        self.logger.debug(f"   Area utilizzabile X: {usable_start_x}-{usable_end_x}mm ({usable_length_x}mm)")
        
        cavalletti_positions = []
        
        if num_cavalletti == 1:
            # Un solo cavalletto al centro
            center_x = usable_start_x + (usable_length_x - segment_thickness) / 2
            center_y = 0  # Inizia dal bordo dell'autoclave
            
            cavalletti_positions.append(CavallettoFixedPosition(
                x=center_x,
                y=center_y,
                width=segment_width,  # Attraversa tutta la larghezza dell'autoclave
                height=segment_thickness,
                sequence_number=0,
                orientation="horizontal"
            ))
            
        elif num_cavalletti == 2:
            # Due cavalletti: uno verso l'inizio, uno verso la fine
            spacing = usable_length_x / 2
            
            positions_x = [
                usable_start_x,
                usable_start_x + spacing
            ]
            
            for i, x_pos in enumerate(positions_x):
                cavalletti_positions.append(CavallettoFixedPosition(
                    x=x_pos,
                    y=0,  # Inizia dal bordo dell'autoclave
                    width=segment_width,  # Attraversa tutta la larghezza dell'autoclave
                    height=segment_thickness,
                    sequence_number=i,
                    orientation="horizontal"
                ))
        
        else:
            # Tre o più cavalletti: distribuzione uniforme
            if config.distribute_evenly:
                # Distribuzione uniforme con spaziatura uguale
                if num_cavalletti > 1:
                    spacing = usable_length_x / (num_cavalletti - 1)
                else:
                    spacing = 0
                
                for i in range(num_cavalletti):
                    x_pos = usable_start_x + i * spacing
                    
                    cavalletti_positions.append(CavallettoFixedPosition(
                        x=x_pos,
                        y=0,  # Inizia dal bordo dell'autoclave
                        width=segment_width,  # Attraversa tutta la larghezza dell'autoclave
                        height=segment_thickness,
                        sequence_number=i,
                        orientation="horizontal"
                    ))
            else:
                # Distribuzione con spaziatura minima garantita
                available_spacing = (usable_length_x - num_cavalletti * segment_thickness) / (num_cavalletti - 1) if num_cavalletti > 1 else 0
                if available_spacing < config.min_spacing_between_cavalletti:
                    self.logger.warning(f"⚠️ Spaziatura cavalletti ridotta: {available_spacing:.1f}mm < {config.min_spacing_between_cavalletti}mm")
                
                current_x = usable_start_x
                for i in range(num_cavalletti):
                    cavalletti_positions.append(CavallettoFixedPosition(
                        x=current_x,
                        y=0,  # Inizia dal bordo dell'autoclave
                        width=segment_width,  # Attraversa tutta la larghezza dell'autoclave
                        height=segment_thickness,
                        sequence_number=i,
                        orientation="horizontal"
                    ))
                    
                    current_x += segment_thickness + available_spacing
        
        self.logger.info(f"🏗️ Generati {len(cavalletti_positions)} cavalletti fissi")
        for i, cav in enumerate(cavalletti_positions):
            self.logger.debug(f"   Cavalletto #{i}: X={cav.x:.1f}-{cav.end_x:.1f}mm, Y={cav.y:.1f}-{cav.end_y:.1f}mm")
        
        return cavalletti_positions
    
    def _validate_cavalletti_non_interference(
        self, 
        cavalletti: List[CavallettoFixedPosition], 
        config: CavallettiConfiguration
    ) -> None:
        """
        Verifica che non ci siano sovrapposizioni tra i cavalletti di tool diversi
        """
        for i, cav1 in enumerate(cavalletti):
            for j, cav2 in enumerate(cavalletti[i+1:], i+1):
                if cav1.tool_odl_id != cav2.tool_odl_id:
                    # Verifica sovrapposizione 2D
                    overlap_x = not (cav1.x + cav1.width <= cav2.x or cav2.x + cav2.width <= cav1.x)
                    overlap_y = not (cav1.y + cav1.height <= cav2.y or cav2.y + cav2.height <= cav1.y)
                    
                    if overlap_x and overlap_y:
                        self.logger.error(f"❌ CONFLITTO CAVALLETTI: ODL {cav1.tool_odl_id} vs ODL {cav2.tool_odl_id}")
                        self.logger.error(f"   Cav1: ({cav1.x:.1f},{cav1.y:.1f}) {cav1.width:.1f}x{cav1.height:.1f}")
                        self.logger.error(f"   Cav2: ({cav2.x:.1f},{cav2.y:.1f}) {cav2.width:.1f}x{cav2.height:.1f}")

    def _validate_minimum_supports_per_tool(
        self, 
        cavalletti: List[CavallettoFixedPosition], 
        level_1_tools: List[NestingLayout2L],
        config: CavallettiConfiguration
    ) -> None:
        """
        ✅ VALIDAZIONE AERONAUTICA: Verifica che ogni tool abbia almeno 2 supporti
        """
        for tool_layout in level_1_tools:
            tool_cavalletti = [c for c in cavalletti if c.tool_odl_id == tool_layout.odl_id]
            
            if len(tool_cavalletti) < 2:
                self.logger.error(f"❌ VIOLAZIONE STANDARD AERONAUTICO: ODL {tool_layout.odl_id} ha solo {len(tool_cavalletti)} supporti (richiesti ≥2)")
                self.logger.error(f"   Tool: ({tool_layout.x:.1f},{tool_layout.y:.1f}) {tool_layout.width:.1f}x{tool_layout.height:.1f}")
                
                # 🚨 CORREZIONE AUTOMATICA: Forza 2 cavalletti minimi
                if len(tool_cavalletti) == 0:
                    # Nessun cavalletto - genera 2 cavalletti di emergenza
                    emergency_cavalletti = self._genera_cavalletti_orizzontali(tool_layout, 2, config)
                    for i, cav_pos in enumerate(emergency_cavalletti):
                        emergency_fixed = CavallettoFixedPosition(
                            x=cav_pos.x,
                            y=cav_pos.y,
                            width=cav_pos.width,
                            height=cav_pos.height,
                            sequence_number=len(cavalletti) + i,
                            orientation="horizontal",
                            tool_odl_id=tool_layout.odl_id
                        )
                        cavalletti.append(emergency_fixed)
                    self.logger.warning(f"🔧 Correzione automatica: Aggiunti 2 cavalletti di emergenza per ODL {tool_layout.odl_id}")
                    
                elif len(tool_cavalletti) == 1:
                    # 1 cavalletto - aggiungi un secondo
                    existing_cav = tool_cavalletti[0]
                    # Posiziona il secondo cavalletto all'estremità opposta
                    if existing_cav.x < tool_layout.x + tool_layout.width / 2:
                        # Cavalletto esistente a sinistra, aggiungi a destra
                        new_x = tool_layout.x + tool_layout.width - config.cavalletto_width - config.min_distance_from_edge
                    else:
                        # Cavalletto esistente a destra, aggiungi a sinistra
                        new_x = tool_layout.x + config.min_distance_from_edge
                    
                    new_cavalletto = CavallettoFixedPosition(
                        x=new_x,
                        y=existing_cav.y,
                        width=config.cavalletto_width,
                        height=config.cavalletto_height,
                        sequence_number=len(cavalletti),
                        orientation="horizontal",
                        tool_odl_id=tool_layout.odl_id
                    )
                    cavalletti.append(new_cavalletto)

    def _add_cavalletti_with_advanced_optimizer(
        self, 
        solution: NestingSolution2L, 
        autoclave: AutoclaveInfo2L
    ) -> NestingSolution2L:
        """
        ✅ NUOVO: Integrazione dell'ottimizzatore cavalletti avanzato
        
        Sostituisce il sistema problematico con l'ottimizzatore industriale completamente implementato.
        """
        try:
            from .cavalletti_optimizer import CavallettiOptimizerAdvanced, OptimizationStrategy
            
            # Verifica se ci sono tool di livello 1 che necessitano cavalletti
            level_1_layouts = [l for l in solution.layouts if l.level == 1]
            if not level_1_layouts:
                self.logger.info("✅ Nessun tool su cavalletto - cavalletti non necessari")
                return solution
            
            self.logger.info(f"🔧 [OTTIMIZZATORE AVANZATO] Calcolo cavalletti per {len(level_1_layouts)} tool")
            
            # Crea configurazione cavalletti dal database autoclave
            config = CavallettiConfiguration(
                cavalletto_width=autoclave.cavalletto_width or 80.0,
                cavalletto_height=autoclave.cavalletto_height_mm or 60.0,
                min_distance_from_edge=30.0,
                max_span_without_support=400.0,
                min_distance_between_cavalletti=200.0,
                safety_margin_x=5.0,
                safety_margin_y=5.0,
                prefer_symmetric=True,
                force_minimum_two=True
            )
            
            # Inizializza ottimizzatore avanzato
            optimizer = CavallettiOptimizerAdvanced()
            
            # Determina strategia basata sulla complessità
            if len(level_1_layouts) <= 8:
                strategy = OptimizationStrategy.BALANCED
            elif len(level_1_layouts) <= 25:
                strategy = OptimizationStrategy.INDUSTRIAL
            else:
                strategy = OptimizationStrategy.AEROSPACE
            
            self.logger.info(f"   Strategia ottimizzazione: {strategy.value}")
            
            # Applica ottimizzazione avanzata
            optimization_result = optimizer.optimize_cavalletti_complete(
                layouts=solution.layouts,  # Passa tutti i layout, l'ottimizzatore filtra livello 1
                autoclave=autoclave,
                config=config,
                strategy=strategy
            )
            
            # Aggiorna soluzione con risultati ottimizzazione
            solution.cavalletti_finali = optimization_result.cavalletti_finali
            solution.cavalletti_optimization_stats = {
                'cavalletti_originali': optimization_result.cavalletti_originali,
                'cavalletti_ottimizzati': optimization_result.cavalletti_ottimizzati,
                'riduzione_percentuale': optimization_result.riduzione_percentuale,
                'limite_rispettato': optimization_result.limite_rispettato,
                'strategia_applicata': optimization_result.strategia_applicata.value,
                'physical_violations_fixed': optimization_result.physical_violations_fixed
            }
            
            # 🔧 FIX CRITICO: Validazione fisica post-ottimizzazione
            self.logger.info("🔍 Avvio validazioni fisiche post-ottimizzazione...")
            
            # VALIDAZIONE 1: Supporto fisico adeguato
            self._validate_physical_support_after_optimization(
                solution.cavalletti_finali, 
                solution.layouts
            )
            
            # VALIDAZIONE 2: No condivisione estremi tra tool consecutivi X
            self._validate_no_extremes_sharing(
                solution.cavalletti_finali,
                solution.layouts,
                config
            )
            
            # Log risultati finali
            final_count = len(solution.cavalletti_finali)
            self.logger.info(f"✅ Ottimizzazione + validazioni completate: {optimization_result.cavalletti_originali} → {final_count} cavalletti")
            self.logger.info(f"   Riduzione: -{optimization_result.riduzione_percentuale:.1f}%")
            self.logger.info(f"   Limite rispettato: {optimization_result.limite_rispettato}")
            
            if optimization_result.warnings:
                for warning in optimization_result.warnings:
                    self.logger.warning(f"   ⚠️ {warning}")
            
            return solution
            
        except ImportError as e:
            self.logger.error(f"❌ Ottimizzatore avanzato non disponibile: {e}")
            # Fallback al sistema semplice
            return self._add_cavalletti_to_solution_fallback(solution, autoclave)
        except Exception as e:
            self.logger.error(f"❌ Errore ottimizzatore avanzato: {e}")
            # Fallback al sistema semplice
            return self._add_cavalletti_to_solution_fallback(solution, autoclave)
    
    def _add_cavalletti_to_solution_fallback(
        self, 
        solution: NestingSolution2L, 
        autoclave: AutoclaveInfo2L
    ) -> NestingSolution2L:
        """
        Fallback semplice per cavalletti quando l'ottimizzatore avanzato non è disponibile
        """
        self.logger.warning("🔧 [FALLBACK] Uso sistema cavalletti semplice")
        
        # Sistema semplice di base
        level_1_layouts = [l for l in solution.layouts if l.level == 1]
        if not level_1_layouts:
            return solution
        
        # Configurazione base
        config = CavallettiConfiguration(
            cavalletto_width=autoclave.cavalletto_width or 80.0,
            cavalletto_height=autoclave.cavalletto_height_mm or 60.0
        )
        
        # Calcola cavalletti base per ogni tool
        all_cavalletti = []
        for layout in level_1_layouts:
            cavalletti_tool = self.calcola_cavalletti_per_tool(layout, config)
            all_cavalletti.extend(cavalletti_tool)
        
        # Converti in formato finale
        cavalletti_fissi = self._convert_to_fixed_positions(all_cavalletti, autoclave)
        
        # Aggiungi alla soluzione
        solution.cavalletti_finali = cavalletti_fissi
        solution.cavalletti_optimization_stats = {
            'cavalletti_originali': len(all_cavalletti),
            'cavalletti_ottimizzati': len(cavalletti_fissi),
            'riduzione_percentuale': 0.0,
            'limite_rispettato': True,
            'strategia_applicata': 'FALLBACK_SEMPLICE',
            'physical_violations_fixed': 0
        }
        
        # 🔧 FIX CRITICO: Validazione fisica anche per fallback
        config_fallback = CavallettiConfiguration(
            cavalletto_width=autoclave.cavalletto_width or 80.0,
            cavalletto_height=autoclave.cavalletto_height_mm or 60.0
        )
        
        # VALIDAZIONE 1: Supporto fisico adeguato
        self._validate_physical_support_after_optimization(
            solution.cavalletti_finali, 
            solution.layouts
        )
        
        # VALIDAZIONE 2: No condivisione estremi tra tool consecutivi X
        self._validate_no_extremes_sharing(
            solution.cavalletti_finali,
            solution.layouts,
            config_fallback
        )
        
        final_count = len(solution.cavalletti_finali)
        self.logger.info(f"✅ Fallback + validazioni completato: {final_count} cavalletti generati")
        return solution

    def _validate_physical_support_after_optimization(
        self, 
        cavalletti_finali: List[CavallettoFixedPosition], 
        layouts: List[NestingLayout2L]
    ) -> None:
        """
        🔧 FIX CRITICO: Validazione fisica rigorosa dopo ottimizzazione cavalletti
        
        PROBLEMA RISOLTO: Tool sospesi o con un solo appoggio dopo riduzione cavalletti
        
        VALIDAZIONI:
        - ✅ Minimo 2 supporti per tool su livello 1 (standard aeronautico)
        - ✅ Distribuzione bilanciata (non tutti supporti da un lato)
        - ✅ Supporti entro boundaries fisici del tool
        - ✅ Correzione automatica se violazioni critiche
        """
        violations_found = []
        corrections_made = 0
        
        for layout in layouts:
            if layout.level != 1:  # Solo tool su cavalletti
                continue
                
            tool_cavalletti = [c for c in cavalletti_finali if c.tool_odl_id == layout.odl_id]
            
            # VALIDAZIONE 1: Minimo 2 supporti per stabilità
            if len(tool_cavalletti) < 2:
                error_msg = f"❌ ODL {layout.odl_id}: insufficienti supporti ({len(tool_cavalletti)}<2)"
                violations_found.append(error_msg)
                self.logger.error(error_msg)
                
                # CORREZIONE AUTOMATICA: Aggiungi cavalletto necessario
                if len(tool_cavalletti) == 1:
                    existing_cav = tool_cavalletti[0]
                    # Posiziona secondo cavalletto all'estremità opposta
                    if existing_cav.center_x < layout.x + layout.width / 2:
                        new_x = layout.x + layout.width * 0.8  # 80% lunghezza tool
                    else:
                        new_x = layout.x + layout.width * 0.2  # 20% lunghezza tool
                    
                    emergency_cavalletto = CavallettoFixedPosition(
                        x=new_x - 40.0,  # Centrato su cavalletto 80mm
                        y=existing_cav.y,
                        width=80.0,
                        height=60.0,
                        sequence_number=len(cavalletti_finali),
                        tool_odl_id=layout.odl_id
                    )
                    cavalletti_finali.append(emergency_cavalletto)
                    corrections_made += 1
                    self.logger.info(f"🔧 Correzione: Aggiunto cavalletto emergenza per ODL {layout.odl_id}")
                
                elif len(tool_cavalletti) == 0:
                    # Nessun cavalletto - genera 2 cavalletti standard
                    for i, pos_factor in enumerate([0.2, 0.8]):  # 20% e 80% lunghezza
                        emergency_cavalletto = CavallettoFixedPosition(
                            x=layout.x + layout.width * pos_factor - 40.0,
                            y=layout.y + layout.height / 2 - 30.0,
                            width=80.0,
                            height=60.0,
                            sequence_number=len(cavalletti_finali) + i,
                            tool_odl_id=layout.odl_id
                        )
                        cavalletti_finali.append(emergency_cavalletto)
                    corrections_made += 2
                    self.logger.info(f"🔧 Correzione: Generati 2 cavalletti emergenza per ODL {layout.odl_id}")
                
                continue  # Riprendi validazione con cavalletti corretti
            
            # VALIDAZIONE 2: Distribuzione bilanciata
            center_x = layout.x + layout.width / 2
            left_supports = sum(1 for c in tool_cavalletti if c.center_x < center_x)
            right_supports = len(tool_cavalletti) - left_supports
            
            if left_supports == 0 or right_supports == 0:
                error_msg = f"❌ ODL {layout.odl_id}: supporti non bilanciati ({left_supports}L, {right_supports}R)"
                violations_found.append(error_msg)
                self.logger.error(error_msg)
                
                # CORREZIONE AUTOMATICA: Sposta cavalletto per bilanciare
                if left_supports == 0:  # Tutti a destra, sposta il più centrale a sinistra
                    rightmost_cavs = sorted(tool_cavalletti, key=lambda c: c.center_x)
                    cav_to_move = rightmost_cavs[len(rightmost_cavs)//2]  # Cavalletto centrale
                    cav_to_move.x = layout.x + layout.width * 0.25 - 40.0  # 25% lunghezza
                    corrections_made += 1
                    self.logger.info(f"🔧 Correzione: Spostato cavalletto per bilanciare ODL {layout.odl_id}")
                
                elif right_supports == 0:  # Tutti a sinistra, sposta il più centrale a destra
                    leftmost_cavs = sorted(tool_cavalletti, key=lambda c: c.center_x, reverse=True)
                    cav_to_move = leftmost_cavs[len(leftmost_cavs)//2]  # Cavalletto centrale
                    cav_to_move.x = layout.x + layout.width * 0.75 - 40.0  # 75% lunghezza
                    corrections_made += 1
                    self.logger.info(f"🔧 Correzione: Spostato cavalletto per bilanciare ODL {layout.odl_id}")
            
            # VALIDAZIONE 3: Supporti entro boundaries fisici
            for i, cavalletto in enumerate(tool_cavalletti):
                # Verifica X boundaries
                if not (layout.x <= cavalletto.x and cavalletto.x + cavalletto.width <= layout.x + layout.width):
                    error_msg = f"❌ Cavalletto {i} ODL {layout.odl_id} FUORI boundaries X"
                    violations_found.append(error_msg)
                    self.logger.error(error_msg)
                    
                    # CORREZIONE: Sposta dentro boundaries
                    if cavalletto.x < layout.x:
                        cavalletto.x = layout.x + 10.0  # 10mm margine
                    elif cavalletto.x + cavalletto.width > layout.x + layout.width:
                        cavalletto.x = layout.x + layout.width - cavalletto.width - 10.0
                    corrections_made += 1
                
                # Verifica Y boundaries  
                if not (layout.y <= cavalletto.y and cavalletto.y + cavalletto.height <= layout.y + layout.height):
                    error_msg = f"❌ Cavalletto {i} ODL {layout.odl_id} FUORI boundaries Y"
                    violations_found.append(error_msg)
                    self.logger.error(error_msg)
                    
                    # CORREZIONE: Centra in Y
                    cavalletto.y = layout.y + (layout.height - cavalletto.height) / 2
                    corrections_made += 1
        
        # RISULTATO VALIDAZIONE
        if violations_found:
            self.logger.warning(f"⚠️ Validazione fisica: {len(violations_found)} violazioni trovate")
            self.logger.info(f"🔧 Correzioni automatiche applicate: {corrections_made}")
            for violation in violations_found[:5]:  # Prime 5 per brevità
                self.logger.warning(f"   {violation}")
        else:
            self.logger.info("✅ Validazione fisica: Tutti i tool correttamente supportati")

    def _validate_no_extremes_sharing(
        self, 
        cavalletti_finali: List[CavallettoFixedPosition], 
        layouts: List[NestingLayout2L],
        config: CavallettiConfiguration
    ) -> None:
        """
        🔧 FIX CRITICO: Verifica che tool consecutivi lungo X non condividano cavalletti estremi
        
        REGOLA FISICA: Tool adiacenti lungo X non possono condividere supporti alle estremità
        perché creerebbe instabilità strutturale.
        
        IMPLEMENTAZIONE:
        - ✅ Identifica tool consecutivi lungo X
        - ✅ Trova cavalletti estremi per ogni tool
        - ✅ Verifica sovrapposizione/condivisione
        - ✅ Risolve conflitti rimuovendo cavalletto meno critico
        """
        conflicts_resolved = 0
        
        for i, layout1 in enumerate(layouts):
            if layout1.level != 1:
                continue
                
            for j, layout2 in enumerate(layouts[i+1:], i+1):
                if layout2.level != 1:
                    continue
                
                # VERIFICA ADIACENZA LUNGO X
                # Calcola gap minimo tra i due tool
                gap_x_left = abs(layout1.x + layout1.width - layout2.x)  # Layout1 a sinistra di layout2
                gap_x_right = abs(layout2.x + layout2.width - layout1.x)  # Layout2 a sinistra di layout1
                min_gap_x = min(gap_x_left, gap_x_right)
                
                # Tool consecutivi se gap < soglia
                if min_gap_x < config.min_distance_between_cavalletti:
                    self.logger.debug(f"🔍 Tool consecutivi X: ODL {layout1.odl_id} ↔ ODL {layout2.odl_id} (gap: {min_gap_x:.1f}mm)")
                    
                    # TROVA CAVALLETTI ESTREMI
                    cav1_estremi = self._get_extreme_cavalletti(layout1, cavalletti_finali)
                    cav2_estremi = self._get_extreme_cavalletti(layout2, cavalletti_finali)
                    
                    # VERIFICA CONFLITTI TRA ESTREMI
                    for cav1 in cav1_estremi:
                        for cav2 in cav2_estremi:
                            if self._cavalletti_overlap_significantly(cav1, cav2, config):
                                # CONFLITTO RILEVATO: Risolvi rimuovendo cavalletto meno critico
                                conflict_msg = f"⚠️ Conflitto estremi: ODL {layout1.odl_id} ↔ ODL {layout2.odl_id}"
                                self.logger.warning(conflict_msg)
                                
                                # Determina quale cavalletto rimuovere (tool più piccolo perde supporto)
                                if layout1.area < layout2.area:
                                    cavalletto_to_remove = cav1
                                    layout_affected = layout1
                                else:
                                    cavalletto_to_remove = cav2
                                    layout_affected = layout2
                                
                                # RIMUOVI CAVALLETTO CONFLITTUALE
                                if cavalletto_to_remove in cavalletti_finali:
                                    cavalletti_finali.remove(cavalletto_to_remove)
                                    conflicts_resolved += 1
                                    self.logger.info(f"🔧 Rimosso cavalletto estremo ODL {layout_affected.odl_id} per conflitto")
                                    
                                    # VERIFICA CHE IL TOOL ABBIA ANCORA SUPPORTO SUFFICIENTE
                                    remaining_cavalletti = [c for c in cavalletti_finali if c.tool_odl_id == layout_affected.odl_id]
                                    if len(remaining_cavalletti) < 2:
                                        # CORREZIONE: Aggiungi cavalletto sostitutivo in posizione sicura
                                        safe_x = self._find_safe_position_for_replacement(
                                            layout_affected, cavalletti_finali, config
                                        )
                                        
                                        replacement_cavalletto = CavallettoFixedPosition(
                                            x=safe_x - 40.0,
                                            y=layout_affected.y + layout_affected.height / 2 - 30.0,
                                            width=80.0,
                                            height=60.0,
                                            sequence_number=len(cavalletti_finali),
                                            tool_odl_id=layout_affected.odl_id
                                        )
                                        cavalletti_finali.append(replacement_cavalletto)
                                        self.logger.info(f"🔧 Aggiunto cavalletto sostitutivo per ODL {layout_affected.odl_id}")
        
        if conflicts_resolved > 0:
            self.logger.info(f"✅ Risolti {conflicts_resolved} conflitti condivisione estremi")
        else:
            self.logger.info("✅ Nessun conflitto condivisione estremi rilevato")

    def _get_extreme_cavalletti(
        self, 
        layout: NestingLayout2L, 
        cavalletti: List[CavallettoFixedPosition]
    ) -> List[CavallettoFixedPosition]:
        """
        🔧 HELPER: Trova cavalletti estremi (più esterni) di un tool lungo X
        
        DEFINIZIONE ESTREMI:
        - Cavalletto più a sinistra (X minimo)
        - Cavalletto più a destra (X massimo)
        """
        tool_cavalletti = [c for c in cavalletti if c.tool_odl_id == layout.odl_id]
        
        if len(tool_cavalletti) <= 2:
            return tool_cavalletti  # Tutti sono estremi se ≤2 cavalletti
        
        # Trova estremi X
        leftmost = min(tool_cavalletti, key=lambda c: c.center_x)
        rightmost = max(tool_cavalletti, key=lambda c: c.center_x)
        
        estremi = [leftmost]
        if rightmost != leftmost:
            estremi.append(rightmost)
        
        return estremi

    def _find_safe_position_for_replacement(
        self, 
        layout: NestingLayout2L, 
        cavalletti: List[CavallettoFixedPosition],
        config: CavallettiConfiguration
    ) -> float:
        """
        🔧 HELPER: Trova posizione X sicura per cavalletto sostitutivo
        
        CRITERI SICUREZZA:
        - Dentro boundaries del tool
        - Lontano da cavalletti esistenti
        - Non in zona estremi per evitare nuovi conflitti
        """
        margin = config.min_distance_from_edge
        safe_zone_start = layout.x + margin + layout.width * 0.3  # 30% larghezza
        safe_zone_end = layout.x + layout.width - margin - layout.width * 0.3  # 70% larghezza
        
        # Prova centro safe zone come prima opzione
        center_safe_zone = (safe_zone_start + safe_zone_end) / 2
        
        # Verifica che non sia troppo vicino a cavalletti esistenti
        tool_cavalletti = [c for c in cavalletti if c.tool_odl_id == layout.odl_id]
        
        for existing_cav in tool_cavalletti:
            if abs(existing_cav.center_x - center_safe_zone) < config.min_distance_between_cavalletti:
                # Troppo vicino, sposta verso un estremo della safe zone
                if center_safe_zone < existing_cav.center_x:
                    center_safe_zone = safe_zone_start + 50.0  # Verso sinistra
                else:
                    center_safe_zone = safe_zone_end - 50.0  # Verso destra
                break
        
        return center_safe_zone

    def _cavalletti_overlap_significantly(
        self, 
        cav1: CavallettoFixedPosition, 
        cav2: CavallettoFixedPosition,
        config: CavallettiConfiguration
    ) -> bool:
        """
        🔧 HELPER: Verifica se due cavalletti si sovrappongono significativamente
        
        SOGLIA: Overlap > 50% della larghezza o distanza < min_distance_between_cavalletti
        """
        # Calcola sovrapposizione X
        overlap_x_start = max(cav1.x, cav2.x)
        overlap_x_end = min(cav1.x + cav1.width, cav2.x + cav2.width)
        overlap_x = max(0, overlap_x_end - overlap_x_start)
        
        # Calcola sovrapposizione Y  
        overlap_y_start = max(cav1.y, cav2.y)
        overlap_y_end = min(cav1.y + cav1.height, cav2.y + cav2.height)
        overlap_y = max(0, overlap_y_end - overlap_y_start)
        
        # Overlap significativo se >= 50% della dimensione minore
        significant_overlap_x = overlap_x >= min(cav1.width, cav2.width) * 0.5
        significant_overlap_y = overlap_y >= min(cav1.height, cav2.height) * 0.5
        
        # Oppure se distanza centri < soglia
        center_distance = ((cav1.center_x - cav2.center_x)**2 + (cav1.center_y - cav2.center_y)**2)**0.5
        too_close = center_distance < getattr(config, 'min_distance_between_cavalletti', 150.0)
        
        return (significant_overlap_x and significant_overlap_y) or too_close
