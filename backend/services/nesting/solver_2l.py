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
    prefer_base_level: bool = True  # Preferenza per il piano base
    
    # Parametri avanzati (configurabili dal frontend)
    use_multithread: bool = True
    num_search_workers: int = 8
    base_timeout_seconds: float = 20.0
    max_timeout_seconds: float = 300.0
    
    # Parametri per penalità/bonus (configurabili dal frontend)
    level_preference_weight: float = 0.1  # Peso preferenza livello base
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
        🔧 Calcola dinamicamente i limiti di peso per livello
        
        Args:
            autoclave: Informazioni autoclave
            num_cavalletti_in_use: Numero di cavalletti effettivamente utilizzati
            
        Returns:
            Tuple (peso_max_livello_0, peso_max_livello_1)
        """
        # Peso massimo livello 1 basato sui cavalletti utilizzati
        peso_max_livello_1 = 0.0
        if autoclave.has_cavalletti and num_cavalletti_in_use > 0:
            peso_max_livello_1 = autoclave.peso_max_per_cavalletto_kg * num_cavalletti_in_use
        
        # Peso massimo livello 0: il rimanente del carico totale autoclave
        peso_max_livello_0 = autoclave.max_weight - peso_max_livello_1
        
        # Assicuriamoci che il livello 0 abbia almeno capacità minima
        peso_max_livello_0 = max(peso_max_livello_0, autoclave.max_weight * 0.3)
        
        # 🔧 FIX: Logging ridotto - solo per cavalletti > 0 e con frequenza limitata
        if num_cavalletti_in_use > 0 and num_cavalletti_in_use % 5 == 0:
            self.logger.info(f"🔧 Limiti dinamici: L0={peso_max_livello_0:.1f}kg, L1={peso_max_livello_1:.1f}kg (cavalletti: {num_cavalletti_in_use})")
        
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
        final_solution = self._add_cavalletti_to_solution(final_solution, autoclave)
        
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
            
            # Il tool deve stare dentro l'autoclave
            model.Add(
                variables['x'][tool_id] + variables['width'][tool_id] <= int(autoclave.width)
            ).OnlyEnforceIf(variables['included'][tool_id])
            
            model.Add(
                variables['y'][tool_id] + variables['height'][tool_id] <= int(autoclave.height)
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
                    variables['x'][tool_id_i] + variables['width'][tool_id_i] + padding <= variables['x'][tool_id_j]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, left_i])
                
                # Tool i a destra di tool j
                model.Add(
                    variables['x'][tool_id_j] + variables['width'][tool_id_j] + padding <= variables['x'][tool_id_i]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, right_i])
                
                # Tool i sotto tool j
                model.Add(
                    variables['y'][tool_id_i] + variables['height'][tool_id_i] + padding <= variables['y'][tool_id_j]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, below_i])
                
                # Tool i sopra tool j
                model.Add(
                    variables['y'][tool_id_j] + variables['height'][tool_id_j] + padding <= variables['y'][tool_id_i]
                ).OnlyEnforceIf([variables['included'][tool_id_i], variables['included'][tool_id_j], same_level, above_i])
                
                # Almeno una condizione deve essere vera se entrambi inclusi e sullo stesso livello
                model.AddBoolOr([left_i, right_i, below_i, above_i, same_level.Not()]).OnlyEnforceIf([
                    variables['included'][tool_id_i], 
                    variables['included'][tool_id_j]
                ])
        
        # 3. 🆕 NUOVI VINCOLI PESO DINAMICI
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
    
        # 4. 🎯 VINCOLI CRITICI: Evitare interferenze tra cavalletti e tool di livello 0
        self._add_cavalletti_interference_constraints_2l(model, tools, autoclave, variables)

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
                    
                    # Definizione delle variabili intermedie
                    model.Add(cavalletto_abs_x == variables['x'][tool_id_i] + int(pos['rel_x']))
                    model.Add(cavalletto_abs_y == variables['y'][tool_id_i] + int(pos['rel_y']))
                    
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
        
        # 🆕 NUOVO: Aggiungi cavalletti alla soluzione
        solution = self._add_cavalletti_to_solution(solution, autoclave)
        
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
        
        # Calcola tutti i cavalletti per i tool di livello 1
        all_cavalletti = self.calcola_tutti_cavalletti(solution.layouts, autoclave)
        
        # Converti cavalletti in CavallettoPosizionamento
        cavalletti_pydantic = []
        for cavalletto in all_cavalletti:
            cavalletto_pos = CavallettoPosizionamento(
                x=cavalletto.x,
                y=cavalletto.y,
                width=cavalletto.width,
                height=cavalletto.height,
                tool_odl_id=cavalletto.tool_odl_id,
                tool_id=cavalletto.tool_odl_id,  # Assuming tool_id == odl_id
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
        non si sovrappongano ai tool esistenti di livello 0.
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
        Calcola il numero di cavalletti necessari basato sulla dimensione principale
        """
        if main_dimension <= config.max_span_without_support:
            return 1  # Un solo cavalletto è sufficiente
        elif main_dimension <= config.max_span_without_support * 2:
            return 2  # Due cavalletti
        else:
            # Calcola numero basato sulla distanza massima senza supporto
            num = math.ceil(main_dimension / config.max_span_without_support)
            return min(num, 5)  # Massimo 5 cavalletti

    def calcola_cavalletti_per_tool(
        self, 
        tool_layout: NestingLayout2L, 
        config: CavallettiConfiguration = None
    ) -> List[CavallettoPosition]:
        """
        Calcola le posizioni dei cavalletti per un singolo tool
        
        Args:
            tool_layout: Layout del tool per cui calcolare i cavalletti
            config: Configurazione cavalletti (opzionale)
            
        Returns:
            Lista delle posizioni dei cavalletti
        """
        if config is None:
            # ✅ NUOVO: Usa dimensioni di default (dovrebbe essere passato dal chiamante)
            config = CavallettiConfiguration(
                cavalletto_width=80.0,  # Fallback - meglio passare da autoclave
                cavalletto_height=60.0  # Fallback - meglio passare da autoclave
            )
        
        # Determina orientazione e numero cavalletti
        main_dimension = max(tool_layout.width, tool_layout.height)
        num_cavalletti = self._calculate_num_cavalletti(main_dimension, config)
        
        # Scegli strategia di posizionamento
        if tool_layout.width >= tool_layout.height:
            # Tool orientato orizzontalmente - cavalletti lungo X
            return self._genera_cavalletti_orizzontali(tool_layout, num_cavalletti, config)
        else:
            # Tool orientato verticalmente - cavalletti lungo Y  
            return self._genera_cavalletti_verticali(tool_layout, num_cavalletti, config)

    def _genera_cavalletti_orizzontali(
        self, 
        tool_layout: NestingLayout2L, 
        num_cavalletti: int, 
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        Genera posizioni per cavalletti disposti orizzontalmente (lungo asse X)
        """
        positions = []
        
        # Area utilizzabile per cavalletti (con margini dai bordi)
        usable_start_x = tool_layout.x + config.min_distance_from_edge
        usable_end_x = tool_layout.x + tool_layout.width - config.min_distance_from_edge
        usable_width = usable_end_x - usable_start_x
        
        if usable_width <= 0:
            self.logger.warning(f"⚠️ Tool ODL {tool_layout.odl_id} troppo stretto per cavalletti")
            return []
        
        # Posizione Y centrale del tool (cavalletti al centro della profondità)
        center_y = tool_layout.y + (tool_layout.height - config.cavalletto_height) / 2
        
        if num_cavalletti == 1:
            # Un solo cavalletto al centro
            center_x = tool_layout.x + (tool_layout.width - config.cavalletto_width) / 2
            positions.append(CavallettoPosition(
                x=center_x,
                y=center_y,
                width=config.cavalletto_width,
                height=config.cavalletto_height,
                tool_odl_id=tool_layout.odl_id,
                sequence_number=0
            ))
        
        elif num_cavalletti == 2:
            # Due cavalletti alle estremità
            if config.prefer_symmetric:
                # Posizionamento simmetrico
                spacing = usable_width - config.cavalletto_width
                left_x = usable_start_x
                right_x = usable_start_x + spacing
            else:
                # Posizionamento ai bordi utilizzabili
                left_x = usable_start_x
                right_x = usable_end_x - config.cavalletto_width
            
            positions.extend([
                CavallettoPosition(
                    x=left_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=0
                ),
                CavallettoPosition(
                    x=right_x,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=1
                )
            ])
        
        else:
            # Tre o più cavalletti - distribuzione equidistante
            spacing = (usable_width - config.cavalletto_width) / (num_cavalletti - 1)
            
            for i in range(num_cavalletti):
                x_pos = usable_start_x + i * spacing
                
                positions.append(CavallettoPosition(
                    x=x_pos,
                    y=center_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=i
                ))
        
        self.logger.debug(f"🔧 Cavalletti orizzontali per ODL {tool_layout.odl_id}: {len(positions)} posizioni")
        
        return positions
    
    def _genera_cavalletti_verticali(
        self, 
        tool_layout: NestingLayout2L, 
        num_cavalletti: int, 
        config: CavallettiConfiguration
    ) -> List[CavallettoPosition]:
        """
        Genera posizioni per cavalletti disposti verticalmente (lungo asse Y)
        
        Args:
            tool_layout: Layout del tool
            num_cavalletti: Numero di cavalletti da posizionare
            config: Configurazione cavalletti
            
        Returns:
            Lista posizioni cavalletti
        """
        
        positions = []
        
        # Area utilizzabile per cavalletti (con margini dai bordi)
        usable_start_y = tool_layout.y + config.min_distance_from_edge
        usable_end_y = tool_layout.y + tool_layout.height - config.min_distance_from_edge
        usable_height = usable_end_y - usable_start_y
        
        if usable_height <= 0:
            self.logger.warning(f"⚠️ Tool ODL {tool_layout.odl_id} troppo corto per cavalletti")
            return []
        
        # Posizione X centrale del tool (cavalletti al centro della larghezza)
        center_x = tool_layout.x + (tool_layout.width - config.cavalletto_width) / 2
        
        if num_cavalletti == 1:
            # Un solo cavalletto al centro
            center_y = tool_layout.y + (tool_layout.height - config.cavalletto_height) / 2
            positions.append(CavallettoPosition(
                x=center_x,
                y=center_y,
                width=config.cavalletto_width,
                height=config.cavalletto_height,
                tool_odl_id=tool_layout.odl_id,
                sequence_number=0
            ))
        
        elif num_cavalletti == 2:
            # Due cavalletti alle estremità
            if config.prefer_symmetric:
                # Posizionamento simmetrico
                spacing = usable_height - config.cavalletto_height
                top_y = usable_start_y
                bottom_y = usable_start_y + spacing
            else:
                # Posizionamento ai bordi utilizzabili
                top_y = usable_start_y
                bottom_y = usable_end_y - config.cavalletto_height
            
            positions.extend([
                CavallettoPosition(
                    x=center_x,
                    y=top_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=0
                ),
                CavallettoPosition(
                    x=center_x,
                    y=bottom_y,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=1
                )
            ])
        
        else:
            # Tre o più cavalletti - distribuzione equidistante
            spacing = (usable_height - config.cavalletto_height) / (num_cavalletti - 1)
            
            for i in range(num_cavalletti):
                y_pos = usable_start_y + i * spacing
                
                positions.append(CavallettoPosition(
                    x=center_x,
                    y=y_pos,
                    width=config.cavalletto_width,
                    height=config.cavalletto_height,
                    tool_odl_id=tool_layout.odl_id,
                    sequence_number=i
                ))
        
        self.logger.debug(f"🔧 Cavalletti verticali per ODL {tool_layout.odl_id}: {len(positions)} posizioni")
        
        return positions
    
    def _add_cavalletti_to_solution(self, solution: NestingSolution2L, autoclave: AutoclaveInfo2L) -> NestingSolution2L:
        """
        Aggiunge il calcolo automatico dei cavalletti alla soluzione esistente
        
        Args:
            solution: Soluzione di nesting esistente
            autoclave: Informazioni autoclave
            
        Returns:
            Soluzione aggiornata con posizioni cavalletti incluse
        """
        
        if not autoclave.has_cavalletti:
            self.logger.debug("🔸 Autoclave senza cavalletti, nessun calcolo necessario")
            return solution
        
        if not solution.success or not solution.layouts:
            self.logger.debug("🔸 Soluzione non valida o vuota, nessun calcolo cavalletti")
            return solution
        
        self.logger.info("🔧 [2L] Calcolo automatico cavalletti per soluzione...")
        
        # 🏗️ AGGIORNATO: Calcola posizioni cavalletti fissi per autoclave
        tool_layouts = solution.layouts.copy()  # Copia per non modificare l'originale
        cavalletti_positions = self.calcola_tutti_cavalletti(tool_layouts, autoclave)
        
        if not cavalletti_positions:
            self.logger.info("🔸 Nessun cavalletto necessario (nessun tool al livello 1)")
            return solution
        
        # Crea nuova soluzione estesa con cavalletti
        extended_solution = NestingSolution2L(
            layouts=tool_layouts,  # Layout tool originali
            excluded_odls=solution.excluded_odls,
            metrics=solution.metrics,
            success=solution.success,
            algorithm_status=solution.algorithm_status,
            message=solution.message
        )
        
        # Aggiungi informazioni cavalletti al messaggio
        num_level_1_tools = len([l for l in tool_layouts if l.level == 1])
        extended_solution.message += f" + {len(cavalletti_positions)} cavalletti per {num_level_1_tools} tool livello 1"
        
        # Memorizza le posizioni cavalletti come metadata (non come layout aggiuntivi)
        # In una implementazione reale, potresti voler estendere NestingSolution2L 
        # per includere un campo cavalletti_positions
        if hasattr(extended_solution, '__dict__'):
            extended_solution.__dict__['cavalletti_positions'] = cavalletti_positions
        
        self.logger.info(f"✅ [2L] Cavalletti calcolati: {len(cavalletti_positions)} posizioni generate")
        
        return extended_solution

    def calcola_tutti_cavalletti(
        self, 
        layouts: List[NestingLayout2L], 
        autoclave: AutoclaveInfo2L, 
        config: CavallettiConfiguration = None
    ) -> List[CavallettoPosition]:
        """
        🏗️ CALCOLO CAVALLETTI AGGIORNATO: Utilizza il nuovo approccio con cavalletti fissi
        
        Calcola i cavalletti come segmenti fissi dell'autoclave che attraversano 
        trasversalmente tutto il piano, poi li converte nel formato legacy per compatibilità.
        
        Args:
            layouts: Lista di tutti i layout posizionati
            autoclave: Informazioni autoclave per calcolo cavalletti fissi  
            config: Configurazione cavalletti (legacy, mantenuto per compatibilità)
            
        Returns:
            Lista completa di tutte le posizioni dei cavalletti (formato legacy)
        """
        
        level_1_tools = [layout for layout in layouts if layout.level == 1]
        
        if not level_1_tools:
            self.logger.info("🔧 Nessun tool al livello 1, nessun cavalletto necessario")
            return []
        
        self.logger.info(f"🏗️ NUOVO APPROCCIO: Calcolo cavalletti fissi per {len(level_1_tools)} tool al livello 1")
        
        # ✅ PRIORITÀ: Usa configurazione dal frontend se disponibile
        if config is None:
            if hasattr(self, '_cavalletti_config') and self._cavalletti_config is not None:
                config = self._cavalletti_config
                self.logger.info("🔧 Usando configurazione cavalletti dal frontend")
            else:
                # ✅ NUOVO: Usa dimensioni dal database autoclave invece di valori hardcoded
                config = CavallettiConfiguration(
                    cavalletto_width=autoclave.cavalletto_width,
                    cavalletto_height=autoclave.cavalletto_height_mm
                )
                self.logger.info("⚠️ Usando configurazione cavalletti di default con dimensioni dal database")
        
        # 🎯 APPROCCIO CORRETTO: Calcola cavalletti come segmenti fissi dell'autoclave
        fixed_config = CavallettiFixedConfiguration(
            distribute_evenly=True,
            min_distance_from_edges=config.min_distance_from_edge,
            min_spacing_between_cavalletti=config.min_distance_between_cavalletti,
            orientation="horizontal"
        )
        cavalletti_fissi = self.calcola_cavalletti_fissi_autoclave(autoclave, fixed_config)
        
        if not cavalletti_fissi:
            self.logger.warning("⚠️ Nessun cavalletto fisso calcolato per questa autoclave")
            return []
        
        # 🔄 Conversione per compatibilità con codice esistente
        legacy_cavalletti = self.converti_cavalletti_fissi_a_legacy(cavalletti_fissi, level_1_tools)
        
        # Verifica sovrapposizioni (mantenuto per compatibilità)
        conflicts = self._check_cavalletti_conflicts(legacy_cavalletti)
        if conflicts:
            self.logger.warning(f"⚠️ Rilevati {len(conflicts)} conflitti tra cavalletti legacy")
            for conflict in conflicts:
                self.logger.warning(f"   Conflitto: {conflict}")
        
        self.logger.info(f"🏗️ Cavalletti fissi: {len(cavalletti_fissi)} → Legacy: {len(legacy_cavalletti)}")
        
        return legacy_cavalletti
    
    def calcola_tutti_cavalletti_legacy(
        self, 
        layouts: List[NestingLayout2L], 
        config: CavallettiConfiguration = None
    ) -> List[CavallettoPosition]:
        """
        🔧 METODO LEGACY: Mantiene il vecchio approccio per compatibilità
        
        Calcola cavalletti individuali per ogni tool (approccio precedente).
        Mantenuto per fallback in caso di problemi con il nuovo sistema.
        """
        
        if config is None:
            # ✅ NUOVO: Usa dimensioni dal database autoclave
            config = CavallettiConfiguration(
                cavalletto_width=80.0,  # Fallback di default - idealmente dovrebbe essere passato
                cavalletto_height=60.0  # Fallback di default - idealmente dovrebbe essere passato
            )
        
        all_cavalletti = []
        level_1_tools = [layout for layout in layouts if layout.level == 1]
        
        self.logger.info(f"🔧 LEGACY: Calcolo cavalletti per {len(level_1_tools)} tool al livello 1")
        
        for tool_layout in level_1_tools:
            cavalletti = self.calcola_cavalletti_per_tool(tool_layout, config)
            all_cavalletti.extend(cavalletti)
            
            self.logger.debug(f"🔧 Tool ODL {tool_layout.odl_id}: {len(cavalletti)} cavalletti aggiunti")
        
        # Verifica sovrapposizioni tra cavalletti
        conflicts = self._check_cavalletti_conflicts(all_cavalletti)
        if conflicts:
            self.logger.warning(f"⚠️ Rilevati {len(conflicts)} conflitti tra cavalletti")
            for conflict in conflicts:
                self.logger.warning(f"   Conflitto: {conflict}")
        
        self.logger.info(f"🔧 Totale cavalletti calcolati: {len(all_cavalletti)}")
        
        return all_cavalletti
    
    def _check_cavalletti_conflicts(self, cavalletti: List[CavallettoPosition]) -> List[str]:
        """
        Verifica conflitti/sovrapposizioni tra cavalletti
        
        Args:
            cavalletti: Lista di posizioni cavalletti
            
        Returns:
            Lista di messaggi di conflitto
        """
        
        conflicts = []
        
        for i, cav1 in enumerate(cavalletti):
            for j, cav2 in enumerate(cavalletti[i+1:], start=i+1):
                # Verifica sovrapposizione
                if not (cav1.x + cav1.width <= cav2.x or 
                       cav2.x + cav2.width <= cav1.x or
                       cav1.y + cav1.height <= cav2.y or 
                       cav2.y + cav2.height <= cav1.y):
                    
                    conflicts.append(
                        f"Cavalletto ODL {cav1.tool_odl_id}#{cav1.sequence_number} "
                        f"sovrappone cavalletto ODL {cav2.tool_odl_id}#{cav2.sequence_number}"
                    )
        
        return conflicts

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
        area_pct = (total_tool_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        
        total_weight = sum(layout.weight for layout in layouts)
        total_lines = sum(layout.lines_used for layout in layouts)
        vacuum_util_pct = (total_lines / autoclave.max_lines) * 100 if autoclave.max_lines > 0 else 0
        
        # Metriche specifiche per livelli
        level_0_layouts = [l for l in layouts if l.level == 0]
        level_1_layouts = [l for l in layouts if l.level == 1]
        
        level_0_area = sum(l.width * l.height for l in level_0_layouts)
        level_1_area = sum(l.width * l.height for l in level_1_layouts)
        
        level_0_area_pct = (level_0_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        level_1_area_pct = (level_1_area / autoclave_area) * 100 if autoclave_area > 0 else 0
        
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
            
            # Calcola posizioni cavalletti per tool livello 0
            cavalletti_level_0 = self.calcola_tutti_cavalletti(level_0_layouts_2l)
            self.logger.info(f"🔧 [FASE 2] Cavalletti livello 0: {len(cavalletti_level_0)} posizioni")
            
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
                
                # 🆕 CHECK CRITICO: Interferenza cavalletti livello 1 con cavalletti livello 0
                if self._has_cavalletti_interference_with_level_0(
                    x, y, width, height, tool, cavalletti_level_0
                ):
                    continue
                
                # Posizione valida trovata
                return (x, y, width, height, rotated)
        
        return None
    
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
    
    def converti_cavalletti_fissi_a_legacy(
        self, 
        cavalletti_fissi: List[CavallettoFixedPosition], 
        layouts_level_1: List[NestingLayout2L]
    ) -> List[CavallettoPosition]:
        """
        🔄 CONVERSIONE COMPATIBILITÀ: Converte cavalletti fissi nel formato legacy
        per mantenere compatibilità con il codice esistente
        
        Args:
            cavalletti_fissi: Cavalletti fissi dell'autoclave
            layouts_level_1: Tool posizionati al livello 1 (sui cavalletti)
            
        Returns:
            Lista cavalletti nel formato legacy compatibile
        """
        legacy_cavalletti = []
        
        # Per ogni tool al livello 1, trova i cavalletti fissi che lo supportano
        for tool_layout in layouts_level_1:
            tool_cavalletti = []
            
            for cav_fisso in cavalletti_fissi:
                # Verifica se il tool si sovrappone con questo cavalletto fisso
                tool_start_x = tool_layout.x
                tool_end_x = tool_layout.x + tool_layout.width
                tool_start_y = tool_layout.y
                tool_end_y = tool_layout.y + tool_layout.height
                
                cav_start_x = cav_fisso.x
                cav_end_x = cav_fisso.end_x
                cav_start_y = cav_fisso.y
                cav_end_y = cav_fisso.end_y
                
                # Verifica sovrapposizione
                overlap_x = not (tool_end_x <= cav_start_x or cav_end_x <= tool_start_x)
                overlap_y = not (tool_end_y <= cav_start_y or cav_end_y <= tool_start_y)
                
                if overlap_x and overlap_y:
                    # Il tool si sovrappone con questo cavalletto fisso
                    # Crea una rappresentazione legacy del cavalletto
                    legacy_cav = CavallettoPosition(
                        x=cav_fisso.x,
                        y=cav_fisso.y,
                        width=cav_fisso.width,
                        height=cav_fisso.height,
                        tool_odl_id=tool_layout.odl_id,
                        sequence_number=cav_fisso.sequence_number
                    )
                    tool_cavalletti.append(legacy_cav)
            
            legacy_cavalletti.extend(tool_cavalletti)
        
        self.logger.debug(f"🔄 Convertiti {len(legacy_cavalletti)} cavalletti fissi in formato legacy")
        return legacy_cavalletti