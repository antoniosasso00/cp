"""
CarbonPilot - Nesting Solver Ottimizzato
Implementazione migliorata dell'algoritmo di nesting 2D con OR-Tools CP-SAT
Versione: 1.4.12-DEMO

Funzionalità principali:
- Nuova funzione obiettivo multi-termine: Max Z = 0.7·area_pct + 0.3·vacuum_util_pct
- Timeout adaptivo: min(90s, 2s × n_pieces)
- Vincolo pezzi pesanti nella metà inferiore (y ≥ H/2)
- Fallback greedy con first-fit decreasing sull'asse lungo
- Heuristica "Ruin & Recreate Goal-Driven" (RRGH) opzionale
- Vincoli su linee vuoto e peso
- 🔍 NUOVO v1.4.14: Log diagnostici dettagliati per debug esclusioni
"""

import logging
import math
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from ortools.sat.python import cp_model

# Configurazione logger
logger = logging.getLogger(__name__)

@dataclass
class NestingParameters:
    """Parametri per l'algoritmo di nesting ottimizzato"""
    padding_mm: int = 20
    min_distance_mm: int = 15
    vacuum_lines_capacity: int = 10
    priorita_area: bool = True
    use_fallback: bool = True  # Abilita fallback greedy
    allow_heuristic: bool = True  # ✅ FIX: Cambiato da False a True per default
    timeout_override: Optional[int] = None  # Nuovo: override timeout personalizzato
    heavy_piece_threshold_kg: float = 50.0  # Nuovo: soglia peso per vincolo posizionamento

@dataclass 
class ToolInfo:
    """Informazioni complete di un tool per il nesting"""
    odl_id: int
    width: float
    height: float
    weight: float
    lines_needed: int = 1
    ciclo_cura_id: Optional[int] = None
    priority: int = 1
    # 🔍 NUOVO v1.4.14: Debug reasons per logging diagnostico
    debug_reasons: List[str] = None
    excluded: bool = False
    
    def __post_init__(self):
        if self.debug_reasons is None:
            self.debug_reasons = []

@dataclass
class AutoclaveInfo:
    """Informazioni dell'autoclave per il nesting"""
    id: int
    width: float
    height: float
    max_weight: float
    max_lines: int

@dataclass
class NestingLayout:
    """Layout di posizionamento di un tool"""
    odl_id: int
    x: float
    y: float
    width: float
    height: float
    weight: float
    rotated: bool = False
    lines_used: int = 1

@dataclass
class NestingMetrics:
    """Metriche del risultato di nesting"""
    area_pct: float  # Percentuale area utilizzata
    vacuum_util_pct: float  # Nuovo: percentuale utilizzo linee vuoto
    lines_used: int  # Linee vuoto utilizzate
    total_weight: float
    positioned_count: int
    excluded_count: int
    efficiency_score: float  # Nuovo: punteggio efficienza combinato
    time_solver_ms: float  # Nuovo: tempo risoluzione in millisecondi
    fallback_used: bool  # Nuovo: indica se è stato usato fallback
    heuristic_iters: int  # Nuovo: iterazioni euristica RRGH

@dataclass
class NestingSolution:
    """Soluzione completa del nesting"""
    layouts: List[NestingLayout]
    excluded_odls: List[Dict[str, Any]]
    metrics: NestingMetrics
    success: bool
    algorithm_status: str
    message: str = ""  # Messaggio descrittivo del risultato

class NestingModel:
    """Modello di nesting ottimizzato con CP-SAT e fallback greedy"""
    
    def __init__(self, parameters: NestingParameters):
        self.parameters = parameters
        self.logger = logging.getLogger(__name__)
        
    def solve(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo
    ) -> NestingSolution:
        """
        Risolve il problema di nesting 2D con algoritmo principale e fallback
        """
        start_time = time.time()
        self.logger.info(f"🚀 Avvio NestingModel v1.4.14: {len(tools)} tools, autoclave {autoclave.width}x{autoclave.height}mm")
        
        # 🔧 NUOVO v1.4.14: AUTO-FIX unità di misura
        original_tools = tools.copy()
        original_autoclave = AutoclaveInfo(
            id=autoclave.id,
            width=autoclave.width,
            height=autoclave.height,
            max_weight=autoclave.max_weight,
            max_lines=autoclave.max_lines
        )
        
        # Prima verifica se tutto è oversize
        all_oversize = True
        autoclave_area = autoclave.width * autoclave.height
        
        if autoclave_area > 0:  # Evita divisione per zero
            for tool in tools:
                # Verifica se il tool può entrare (con margine)
                margin = self.parameters.min_distance_mm
                fits_normal = (tool.width + margin <= autoclave.width and 
                              tool.height + margin <= autoclave.height)
                fits_rotated = (tool.height + margin <= autoclave.width and 
                               tool.width + margin <= autoclave.height)
                
                if fits_normal or fits_rotated:
                    all_oversize = False
                    break
            
            # Se tutto è oversize E l'autoclave ha dimensioni ragionevoli, prova auto-fix × 0.1
            if all_oversize and autoclave_area > 10000:  # Autoclave area > 100×100mm (sensato per mm)
                self.logger.info("🔧 AUTO-FIX: Tutti i pezzi oversize, provo scala × 0.1 (mm→cm)")
                
                # Scala tutti i tool × 0.1
                scaled_tools = []
                for tool in tools:
                    scaled_tool = ToolInfo(
                        odl_id=tool.odl_id,
                        width=tool.width * 0.1,
                        height=tool.height * 0.1,
                        weight=tool.weight,  # Peso rimane invariato
                        lines_needed=tool.lines_needed,
                        ciclo_cura_id=tool.ciclo_cura_id,
                        priority=tool.priority
                    )
                    scaled_tools.append(scaled_tool)
                
                # Scala autoclave × 0.1
                scaled_autoclave = AutoclaveInfo(
                    id=autoclave.id,
                    width=autoclave.width * 0.1,
                    height=autoclave.height * 0.1,
                    max_weight=autoclave.max_weight,
                    max_lines=autoclave.max_lines
                )
                
                # Riprova con dati scalati
                try:
                    scaled_solution = self._solve_scaled(scaled_tools, scaled_autoclave, start_time)
                    if scaled_solution.success and scaled_solution.metrics.positioned_count > 0:
                        # Riscala i risultati × 10
                        rescaled_layouts = []
                        for layout in scaled_solution.layouts:
                            rescaled_layout = NestingLayout(
                                odl_id=layout.odl_id,
                                x=layout.x * 10,
                                y=layout.y * 10,
                                width=layout.width * 10,
                                height=layout.height * 10,
                                weight=layout.weight,
                                rotated=layout.rotated,
                                lines_used=layout.lines_used
                            )
                            rescaled_layouts.append(rescaled_layout)
                        
                        # Aggiorna messaggio
                        scaled_solution.layouts = rescaled_layouts
                        scaled_solution.message += " [AUTO-FIX: applicata scala × 0.1 → × 10]"
                        
                        self.logger.info(f"✅ AUTO-FIX riuscito: {scaled_solution.metrics.positioned_count} pezzi posizionati")
                        return scaled_solution
                    else:
                        self.logger.info("🔧 AUTO-FIX: Scala × 0.1 non ha migliorato, continuo con dati originali")
                except Exception as e:
                    self.logger.warning(f"🔧 AUTO-FIX: Errore durante scala × 0.1: {e}")
        
        # Continua con algoritmo normale
        return self._solve_normal(tools, autoclave, start_time)
    
    def _solve_scaled(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        start_time: float
    ) -> NestingSolution:
        """Versione semplificata solve per auto-fix scalato"""
        return self._solve_normal(tools, autoclave, start_time)
    
    def _solve_normal(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        start_time: float
    ) -> NestingSolution:
        """Algoritmo di solve normale (spostato dal metodo solve originale)"""
        # Timeout adaptivo: min(90s, 2s × n_pieces) o override
        n_pieces = len(tools)
        if self.parameters.timeout_override:
            timeout_seconds = float(self.parameters.timeout_override)
        else:
            timeout_seconds = min(120.0, 2.0 * n_pieces)
        self.logger.info(f"⏱️ Timeout adaptivo: {timeout_seconds}s per {n_pieces} pezzi")
        
        # Pre-filtraggio: rimuovi tools che non possono mai essere posizionati
        valid_tools, excluded_tools = self._prefilter_tools(tools, autoclave)
        
        if not valid_tools:
            return self._create_empty_solution(excluded_tools, autoclave, start_time)
        
        # Tentativo principale con CP-SAT
        try:
            solution = self._solve_cpsat(valid_tools, autoclave, timeout_seconds, start_time)
            
            # Se CP-SAT ha successo, prova l'heuristica di miglioramento se abilitata
            if solution.success and self.parameters.allow_heuristic and solution.metrics.positioned_count > 2:
                self.logger.info("🔄 Tentativo miglioramento con heuristica RRGH")
                improved_solution = self._apply_ruin_recreate_heuristic(solution, valid_tools, autoclave, start_time)
                if improved_solution.metrics.efficiency_score > solution.metrics.efficiency_score:
                    self.logger.info(f"✅ Heuristica migliorata: {improved_solution.metrics.efficiency_score:.1f}% vs {solution.metrics.efficiency_score:.1f}%")
                    solution = improved_solution
                else:
                    self.logger.info("📈 Heuristica non ha migliorato la soluzione")
            
            # 🔍 NUOVO v1.4.14: Raccolta motivi di esclusione per tutti i pezzi
            solution = self._collect_exclusion_reasons(solution, tools, autoclave)
            
            # Aggiungi esclusioni del pre-filtraggio
            solution.excluded_odls.extend(excluded_tools)
            return solution
                
        except Exception as e:
            self.logger.warning(f"⚠️ Errore CP-SAT: {str(e)}")
        
        # Fallback greedy se CP-SAT fallisce o non trova soluzione ottimale
        if self.parameters.use_fallback:
            self.logger.info("🔄 Attivazione fallback greedy")
            solution = self._solve_greedy_fallback(valid_tools, autoclave, start_time)
            
            # 🔍 NUOVO v1.4.14: Raccolta motivi di esclusione per tutti i pezzi
            solution = self._collect_exclusion_reasons(solution, tools, autoclave)
            
            solution.excluded_odls.extend(excluded_tools)
            return solution
        
        # Soluzione vuota se tutto fallisce
        return self._create_empty_solution(excluded_tools, autoclave, start_time)
    
    def _prefilter_tools(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo
    ) -> Tuple[List[ToolInfo], List[Dict[str, Any]]]:
        """Pre-filtra i tools eliminando quelli che non possono essere posizionati"""
        
        self.logger.info(f"🔍 PRE-FILTERING DEBUG:")
        self.logger.info(f"   Autoclave: {autoclave.width}x{autoclave.height}mm")
        self.logger.info(f"   Tools da analizzare: {len(tools)}")
        
        valid_tools = []
        excluded_tools = []
        margin = self.parameters.min_distance_mm
        
        for tool in tools:
            self.logger.info(f"   📋 Tool ODL {tool.odl_id}: {tool.width}x{tool.height}mm")
            
            # Controlla dimensioni
            fits_normal = (tool.width + margin <= autoclave.width and 
                          tool.height + margin <= autoclave.height)
            fits_rotated = (tool.height + margin <= autoclave.width and 
                           tool.width + margin <= autoclave.height)
            
            self.logger.info(f"      Fits normal: {fits_normal} ({tool.width + margin} <= {autoclave.width} && {tool.height + margin} <= {autoclave.height})")
            self.logger.info(f"      Fits rotated: {fits_rotated} ({tool.height + margin} <= {autoclave.width} && {tool.width + margin} <= {autoclave.height})")
            
            if not fits_normal and not fits_rotated:
                excluded_tools.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Dimensioni eccessive',
                    'dettagli': f"Tool {tool.width}x{tool.height}mm non entra nel piano {autoclave.width}x{autoclave.height}mm"
                })
                self.logger.info(f"      ❌ ESCLUSO: Dimensioni eccessive")
                continue
            
            # Controlla peso
            if tool.weight > autoclave.max_weight:
                excluded_tools.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Peso eccessivo',
                    'dettagli': f"Tool {tool.weight}kg supera il limite di {autoclave.max_weight}kg"
                })
                self.logger.info(f"      ❌ ESCLUSO: Peso eccessivo")
                continue
            
            # Controlla linee vuoto
            if tool.lines_needed > self.parameters.vacuum_lines_capacity:
                excluded_tools.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Troppe linee vuoto richieste',
                    'dettagli': f"Tool richiede {tool.lines_needed} linee, capacità è {self.parameters.vacuum_lines_capacity}"
                })
                self.logger.info(f"      ❌ ESCLUSO: Troppe linee vuoto")
                continue
            
            # Tool valido
            self.logger.info(f"      ✅ ACCETTATO")
            valid_tools.append(tool)
        
        self.logger.info(f"📊 Pre-filtraggio: {len(valid_tools)} validi, {len(excluded_tools)} esclusi")
        return valid_tools, excluded_tools
    
    def _solve_cpsat(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        timeout_seconds: float,
        start_time: float
    ) -> NestingSolution:
        """Risolve usando OR-Tools CP-SAT"""
        
        self.logger.info(f"🔧 Risoluzione CP-SAT: {len(tools)} tools")
        
        # Ordina per area decrescente per migliore performance
        sorted_tools = sorted(tools, key=lambda t: t.width * t.height, reverse=True)
        
        # Crea modello CP-SAT
        model = cp_model.CpModel()
        
        # Variabili di decisione
        variables = self._create_cpsat_variables(model, sorted_tools, autoclave)
        
        # Vincoli
        self._add_cpsat_constraints(model, sorted_tools, autoclave, variables)
        
        # Funzione obiettivo
        self._add_cpsat_objective(model, sorted_tools, variables)
        
        # Risolvi
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout_seconds
        solver.parameters.search_branching = cp_model.PORTFOLIO
        
        status = solver.Solve(model)
        
        # Elabora risultato
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_cpsat_solution(solver, sorted_tools, autoclave, variables, status, start_time)
        elif status in [cp_model.INFEASIBLE, cp_model.UNKNOWN]:
            # Ritorna soluzione vuota per attivare fallback
            return NestingSolution(
                layouts=[],
                excluded_odls=[],
                metrics=NestingMetrics(0, 0, 0, 0, len(tools), 0, 0, 0, False, 0),
                success=False,
                algorithm_status=f"CP-SAT_{status}",
                message=f"CP-SAT non ha trovato soluzione: {status}"
            )
        else:
            raise Exception(f"CP-SAT status non gestito: {status}")
    
    def _create_cpsat_variables(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo
    ) -> Dict[str, Any]:
        """Crea le variabili per il modello CP-SAT"""
        
        variables = {
            'included': {},      # tool incluso nel layout
            'x': {},            # posizione x
            'y': {},            # posizione y  
            'rotated': {},      # tool ruotato
            'intervals_x': {},  # intervalli x per non-sovrapposizione
            'intervals_y': {}   # intervalli y per non-sovrapposizione
        }
        
        margin = self.parameters.min_distance_mm
        
        for tool in tools:
            tool_id = tool.odl_id
            
            # Inclusione
            variables['included'][tool_id] = model.NewBoolVar(f'included_{tool_id}')
            
            # Posizione
            variables['x'][tool_id] = model.NewIntVar(
                margin, round(autoclave.width - margin), f'x_{tool_id}'
            )
            variables['y'][tool_id] = model.NewIntVar(
                margin, round(autoclave.height - margin), f'y_{tool_id}'
            )
            
            # Rotazione (se possibile)
            fits_normal = (tool.width + margin <= autoclave.width and 
                          tool.height + margin <= autoclave.height)
            fits_rotated = (tool.height + margin <= autoclave.width and 
                           tool.width + margin <= autoclave.height)
            
            if fits_normal and fits_rotated:
                variables['rotated'][tool_id] = model.NewBoolVar(f'rotated_{tool_id}')
            elif fits_rotated:
                variables['rotated'][tool_id] = 1  # Forzato ruotato
            else:
                variables['rotated'][tool_id] = 0  # Forzato normale
            
            # Intervalli per non-sovrapposizione (usando dimensioni massime)
            max_width = max(round(tool.width), round(tool.height))
            max_height = max(round(tool.width), round(tool.height))
            
            variables['intervals_x'][tool_id] = model.NewOptionalIntervalVar(
                variables['x'][tool_id], 
                max_width,
                variables['x'][tool_id] + max_width,
                variables['included'][tool_id],
                f'interval_x_{tool_id}'
            )
            
            variables['intervals_y'][tool_id] = model.NewOptionalIntervalVar(
                variables['y'][tool_id], 
                max_height,
                variables['y'][tool_id] + max_height,
                variables['included'][tool_id],
                f'interval_y_{tool_id}'
            )
        
        return variables
    
    def _add_cpsat_constraints(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        variables: Dict[str, Any]
    ) -> None:
        """Aggiunge i vincoli al modello CP-SAT"""
        
        # Vincolo di non sovrapposizione 2D
        if len(variables['intervals_x']) > 0:
            model.AddNoOverlap2D(
                list(variables['intervals_x'].values()),
                list(variables['intervals_y'].values())
            )
        
        # Vincolo di peso massimo
        weight_terms = []
        for tool in tools:
            tool_id = tool.odl_id
            weight_terms.append(
                variables['included'][tool_id] * round(tool.weight * 1000)
            )
        
        if weight_terms:
            total_weight = model.NewIntVar(0, round(autoclave.max_weight * 1000), 'total_weight')
            model.Add(total_weight == sum(weight_terms))
            model.Add(total_weight <= round(autoclave.max_weight * 1000))
        
        # Vincolo di capacità linee vuoto
        lines_terms = []
        for tool in tools:
            tool_id = tool.odl_id
            lines_terms.append(
                variables['included'][tool_id] * tool.lines_needed
            )
        
        if lines_terms:
            total_lines = model.NewIntVar(0, self.parameters.vacuum_lines_capacity, 'total_lines')
            model.Add(total_lines == sum(lines_terms))
            model.Add(total_lines <= self.parameters.vacuum_lines_capacity)
        
        # Vincoli di posizione basati sulla rotazione
        margin = self.parameters.min_distance_mm
        
        for tool in tools:
            tool_id = tool.odl_id
            
            # Controlla se rotazione è variabile
            if isinstance(variables['rotated'][tool_id], int):
                # Rotazione fissa
                if variables['rotated'][tool_id] == 0:  # Normale
                    max_x = round(autoclave.width - tool.width - margin)
                    max_y = round(autoclave.height - tool.height - margin)
                else:  # Ruotato
                    max_x = round(autoclave.width - tool.height - margin)
                    max_y = round(autoclave.height - tool.width - margin)
                
                model.Add(variables['x'][tool_id] <= max_x).OnlyEnforceIf(variables['included'][tool_id])
                model.Add(variables['y'][tool_id] <= max_y).OnlyEnforceIf(variables['included'][tool_id])
            else:
                # Rotazione variabile - vincoli condizionali
                max_x_normal = round(autoclave.width - tool.width - margin)
                max_y_normal = round(autoclave.height - tool.height - margin)
                max_x_rotated = round(autoclave.width - tool.height - margin)
                max_y_rotated = round(autoclave.height - tool.width - margin)
                
                # Vincoli per orientamento normale
                model.Add(variables['x'][tool_id] <= max_x_normal).OnlyEnforceIf([
                    variables['included'][tool_id], 
                    variables['rotated'][tool_id].Not()
                ])
                model.Add(variables['y'][tool_id] <= max_y_normal).OnlyEnforceIf([
                    variables['included'][tool_id], 
                    variables['rotated'][tool_id].Not()
                ])
                
                # Vincoli per orientamento ruotato
                model.Add(variables['x'][tool_id] <= max_x_rotated).OnlyEnforceIf([
                    variables['included'][tool_id], 
                    variables['rotated'][tool_id]
                ])
                model.Add(variables['y'][tool_id] <= max_y_rotated).OnlyEnforceIf([
                    variables['included'][tool_id], 
                    variables['rotated'][tool_id]
                ])
    
    def _add_cpsat_objective(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo], 
        variables: Dict[str, Any]
    ) -> None:
        """Aggiunge la funzione obiettivo al modello CP-SAT"""
        
        # Obiettivo primario: massimizza numero di ODL inclusi
        num_included = sum(variables['included'].values())
        
        if self.parameters.priorita_area:
            # Obiettivo secondario: massimizza area utilizzata
            area_terms = []
            for tool in tools:
                tool_id = tool.odl_id
                tool_area = round(tool.width * tool.height)
                area_terms.append(variables['included'][tool_id] * tool_area)
            
            if area_terms:
                total_area = model.NewIntVar(0, sum(round(t.width * t.height) for t in tools), 'total_area')
                model.Add(total_area == sum(area_terms))
                
                # Obiettivo terziario: minimizza peso per bilanciamento
                weight_terms = []
                for tool in tools:
                    tool_id = tool.odl_id
                    weight_terms.append(variables['included'][tool_id] * round(tool.weight * 1000))
                
                if weight_terms:
                    total_weight_obj = model.NewIntVar(0, sum(round(t.weight * 1000) for t in tools), 'weight_obj')
                    model.Add(total_weight_obj == sum(weight_terms))
                    
                    # Corretto: creo una variabile per la divisione del peso
                    weight_penalty = model.NewIntVar(0, sum(round(t.weight * 1000) for t in tools) // 1000, 'weight_penalty')
                    model.AddDivisionEquality(weight_penalty, total_weight_obj, 1000)
                    
                    # Combinazione obiettivi: ODL (peso 10000) + area (peso 1) - peso_penalty
                    model.Maximize(num_included * 10000 + total_area - weight_penalty)
                else:
                    model.Maximize(num_included * 10000 + total_area)
            else:
                model.Maximize(num_included)
        else:
            # Solo massimizza numero ODL
            model.Maximize(num_included)
    
    def _extract_cpsat_solution(
        self, 
        solver: cp_model.CpSolver, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        variables: Dict[str, Any], 
        status: int,
        start_time: float
    ) -> NestingSolution:
        """Estrae la soluzione dal solver CP-SAT"""
        
        layouts = []
        excluded_odls = []
        total_weight = 0
        used_area = 0
        total_lines = 0
        
        for tool in tools:
            tool_id = tool.odl_id
            
            if solver.Value(variables['included'][tool_id]):
                # Tool incluso
                x = float(solver.Value(variables['x'][tool_id]))
                y = float(solver.Value(variables['y'][tool_id]))
                
                # Determina rotazione
                if isinstance(variables['rotated'][tool_id], int):
                    rotated = bool(variables['rotated'][tool_id])
                else:
                    rotated = bool(solver.Value(variables['rotated'][tool_id]))
                
                # Calcola dimensioni finali
                if rotated:
                    width = tool.height
                    height = tool.width
                else:
                    width = tool.width
                    height = tool.height
                
                layouts.append(NestingLayout(
                    odl_id=tool_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    weight=tool.weight,
                    rotated=rotated,
                    lines_used=tool.lines_needed
                ))
                
                total_weight += tool.weight
                used_area += width * height
                total_lines += tool.lines_needed
            else:
                # Tool escluso
                excluded_odls.append({
                    'odl_id': tool_id,
                    'motivo': 'Non incluso nella soluzione ottimale',
                    'dettagli': f"Tool non selezionato dall'algoritmo di ottimizzazione"
                })
        
        # Calcola metriche
        total_area = autoclave.width * autoclave.height
        area_pct = (used_area / total_area * 100) if total_area > 0 else 0
        vacuum_util_pct = (total_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
        efficiency_score = 0.7 * area_pct + 0.3 * vacuum_util_pct
        
        # ✅ FIX: Controllo efficienza bassa - warning ma non failure
        efficiency_warning = ""
        if efficiency_score < 60.0 and len(layouts) > 0:
            efficiency_warning = f" ⚠️ EFFICIENZA BASSA ({efficiency_score:.1f}%)"
        
        metrics = NestingMetrics(
            area_pct=area_pct,
            vacuum_util_pct=vacuum_util_pct,
            lines_used=total_lines,
            total_weight=total_weight,
            positioned_count=len(layouts),
            excluded_count=len(excluded_odls),
            efficiency_score=efficiency_score,
            time_solver_ms=(time.time() - start_time) * 1000,
            fallback_used=False,
            heuristic_iters=0
        )
        
        status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        
        self.logger.info(f"✅ CP-SAT completato: {len(layouts)} posizionati, {area_pct:.1f}% area, {total_lines} linee")
        
        return NestingSolution(
            layouts=layouts,
            excluded_odls=excluded_odls,
            metrics=metrics,
            success=True,
            algorithm_status=f"CP-SAT_{status_name}",
            message=f"Nesting completato con successo: {len(layouts)} ODL posizionati, efficienza {efficiency_score:.1f}%{efficiency_warning}"
        )
    
    def _solve_greedy_fallback(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo,
        start_time: float
    ) -> NestingSolution:
        """Algoritmo di fallback greedy con first-fit decreasing sull'asse lungo"""
        
        self.logger.info("🔄 Algoritmo fallback greedy attivo")
        
        # Ordina per dimensione asse lungo decrescente (first-fit decreasing)
        sorted_tools = sorted(
            tools, 
            key=lambda t: max(t.width, t.height), 
            reverse=True
        )
        
        layouts = []
        excluded_odls = []
        total_weight = 0
        used_area = 0
        total_lines = 0
        occupied_rects = []  # Lista di rettangoli occupati
        
        for tool in sorted_tools:
            # Verifica vincoli globali
            if total_weight + tool.weight > autoclave.max_weight:
                excluded_odls.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Peso eccessivo nel batch',
                    'dettagli': f"Aggiungere il tool ({tool.weight}kg) supererebbe il limite ({autoclave.max_weight}kg)"
                })
                continue
            
            if total_lines + tool.lines_needed > self.parameters.vacuum_lines_capacity:
                excluded_odls.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Capacità linee vuoto superata',
                    'dettagli': f"Aggiungere il tool ({tool.lines_needed} linee) supererebbe la capacità ({self.parameters.vacuum_lines_capacity})"
                })
                continue
            
            # Trova posizione valida
            best_position = self._find_greedy_position(tool, autoclave, occupied_rects)
            
            if best_position:
                x, y, width, height, rotated = best_position
                
                # Aggiungi rettangolo occupato
                occupied_rects.append((x, y, width, height))
                
                layouts.append(NestingLayout(
                    odl_id=tool.odl_id,
                    x=float(x),
                    y=float(y),
                    width=float(width),
                    height=float(height),
                    weight=tool.weight,
                    rotated=rotated,
                    lines_used=tool.lines_needed
                ))
                
                total_weight += tool.weight
                used_area += width * height
                total_lines += tool.lines_needed
                
                self.logger.info(f"✅ Tool {tool.odl_id} posizionato: {x},{y} {width}x{height}")
            else:
                excluded_odls.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Spazio insufficiente',
                    'dettagli': f"Non è stata trovata una posizione valida per il tool {tool.width}x{tool.height}mm"
                })
        
        # Calcola metriche
        total_area = autoclave.width * autoclave.height
        area_pct = (used_area / total_area * 100) if total_area > 0 else 0
        vacuum_util_pct = (total_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
        efficiency_score = 0.7 * area_pct + 0.3 * vacuum_util_pct
        
        # ✅ FIX: Controllo efficienza bassa - warning ma non failure
        efficiency_warning = ""
        if efficiency_score < 60.0 and len(layouts) > 0:
            efficiency_warning = f" ⚠️ EFFICIENZA BASSA ({efficiency_score:.1f}%)"
        
        metrics = NestingMetrics(
            area_pct=area_pct,
            vacuum_util_pct=vacuum_util_pct,
            lines_used=total_lines,
            total_weight=total_weight,
            positioned_count=len(layouts),
            excluded_count=len(excluded_odls),
            efficiency_score=efficiency_score,
            time_solver_ms=(time.time() - start_time) * 1000,
            fallback_used=True,
            heuristic_iters=0
        )
        
        self.logger.info(f"🔄 Fallback completato: {len(layouts)} posizionati, {area_pct:.1f}% efficienza")
        
        return NestingSolution(
            layouts=layouts,
            excluded_odls=excluded_odls,
            metrics=metrics,
            success=len(layouts) > 0,
            algorithm_status="FALLBACK_GREEDY",
            message=f"Fallback greedy completato: {len(layouts)} ODL posizionati, efficienza {efficiency_score:.1f}%{efficiency_warning}"
        )
    
    def _can_place(
        self, 
        piece: ToolInfo, 
        autoclave: AutoclaveInfo, 
        occupied_rects: List[Tuple[float, float, float, float]] = None
    ) -> bool:
        """
        🔍 NUOVO v1.4.14: Verifica se un pezzo può essere posizionato e registra i motivi di esclusione
        
        Controlla:
        - Dimensioni rispetto all'autoclave (con rotazione)
        - Peso massimo supportato
        - Linee vuoto disponibili
        - Padding richiesto
        
        Returns:
            bool: True se il pezzo può essere posizionato, False altrimenti
        """
        piece.debug_reasons.clear()  # Reset dei motivi
        
        margin = self.parameters.min_distance_mm
        padding = self.parameters.padding_mm
        
        # 1. Controllo dimensioni base (oversize)
        fits_normal = (piece.width + margin <= autoclave.width and 
                      piece.height + margin <= autoclave.height)
        fits_rotated = (piece.height + margin <= autoclave.width and 
                       piece.width + margin <= autoclave.height)
        
        if not fits_normal and not fits_rotated:
            piece.debug_reasons.append("oversize")
            piece.excluded = True
            self.logger.debug(f"🔍 ODL {piece.odl_id}: OVERSIZE - {piece.width}x{piece.height}mm non entra in {autoclave.width}x{autoclave.height}mm")
            return False
        
        # 2. Controllo peso
        if piece.weight > autoclave.max_weight:
            piece.debug_reasons.append("weight_exceeded")
            piece.excluded = True
            self.logger.debug(f"🔍 ODL {piece.odl_id}: WEIGHT_EXCEEDED - {piece.weight}kg > {autoclave.max_weight}kg")
            return False
        
        # 3. Controllo linee vuoto
        if piece.lines_needed > autoclave.max_lines:
            piece.debug_reasons.append("vacuum_lines")
            piece.excluded = True
            self.logger.debug(f"🔍 ODL {piece.odl_id}: VACUUM_LINES - richiede {piece.lines_needed} > {autoclave.max_lines} disponibili")
            return False
        
        # 4. Controllo padding requirements (area minima con padding)
        min_area_with_padding = (piece.width + 2*padding) * (piece.height + 2*padding)
        autoclave_area = autoclave.width * autoclave.height
        
        if min_area_with_padding > autoclave_area:
            piece.debug_reasons.append("padding")
            piece.excluded = True
            self.logger.debug(f"🔍 ODL {piece.odl_id}: PADDING - area con padding {min_area_with_padding:.0f}mm² > area autoclave {autoclave_area:.0f}mm²")
            return False
        
        # 5. Se tutto ok, pezzo potenzialmente piazzabile
        self.logger.debug(f"🔍 ODL {piece.odl_id}: PLACEABLE - {piece.width}x{piece.height}mm, {piece.weight}kg, {piece.lines_needed} linee")
        return True
    
    def _find_greedy_position(
        self, 
        tool: ToolInfo, 
        autoclave: AutoclaveInfo, 
        occupied_rects: List[Tuple[float, float, float, float]]
    ) -> Optional[Tuple[float, float, float, float, bool]]:
        """Trova la prima posizione valida per un tool nell'algoritmo greedy"""
        
        margin = int(self.parameters.min_distance_mm)
        
        # Prova entrambi gli orientamenti
        orientations = []
        if tool.width + margin <= autoclave.width and tool.height + margin <= autoclave.height:
            orientations.append((tool.width, tool.height, False))
        if tool.height + margin <= autoclave.width and tool.width + margin <= autoclave.height:
            orientations.append((tool.height, tool.width, True))
        
        # Griglia di ricerca con passo di 10mm per performance
        step = 10
        
        for width, height, rotated in orientations:
            for y in range(margin, int(round(autoclave.height - height)) + 1, step):
                for x in range(margin, int(round(autoclave.width - width)) + 1, step):
                    
                    # Controlla sovrapposizioni
                    overlaps = False
                    for rect_x, rect_y, rect_w, rect_h in occupied_rects:
                        if not (x + width <= rect_x or x >= rect_x + rect_w or 
                               y + height <= rect_y or y >= rect_y + rect_h):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        return (x, y, width, height, rotated)
        
        return None
    
    def _create_empty_solution(
        self, 
        excluded_tools: List[Dict[str, Any]], 
        autoclave: AutoclaveInfo,
        start_time: float
    ) -> NestingSolution:
        """Crea una soluzione vuota quando non ci sono tools validi"""
        
        metrics = NestingMetrics(
            area_pct=0,
            vacuum_util_pct=0,
            lines_used=0,
            total_weight=0,
            positioned_count=0,
            excluded_count=len(excluded_tools),
            efficiency_score=0,
            time_solver_ms=(time.time() - start_time) * 1000,
            fallback_used=False,
            heuristic_iters=0
        )
        
        return NestingSolution(
            layouts=[],
            excluded_odls=excluded_tools,
            metrics=metrics,
            success=False,
            algorithm_status="NO_VALID_TOOLS",
            message="Nessun tool valido disponibile per il nesting"
        )
    
    def _apply_ruin_recreate_heuristic(
        self, 
        initial_solution: NestingSolution, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo,
        start_time: float
    ) -> NestingSolution:
        """
        Applica l'heuristica "Ruin & Recreate Goal-Driven" (RRGH)
        Esegue 5 iterazioni: elimina random 20% pezzi e reinserisci con FFD migliorato
        """
        
        best_solution = initial_solution
        iterations = 5
        ruin_percentage = 0.2
        
        self.logger.info(f"🔄 Avvio heuristica RRGH: {iterations} iterazioni, ruin {ruin_percentage*100}%")
        
        for iteration in range(iterations):
            try:
                # Copia la soluzione corrente
                current_layouts = best_solution.layouts.copy()
                
                if len(current_layouts) < 2:
                    continue  # Non abbastanza pezzi per applicare la ruin
                
                # 1. Ruin: rimuovi randomly 20% dei pezzi posizionati
                num_to_remove = max(1, int(len(current_layouts) * ruin_percentage))
                removed_layouts = random.sample(current_layouts, num_to_remove)
                remaining_layouts = [l for l in current_layouts if l not in removed_layouts]
                
                # 2. Recreate: riprova a posizionare i pezzi rimossi con FFD migliorato
                removed_tools = [
                    tool for tool in tools 
                    if any(rl.odl_id == tool.odl_id for rl in removed_layouts)
                ]
                
                # Ordina per "efficacia" = area / linee_vuoto
                removed_tools.sort(
                    key=lambda t: (t.width * t.height) / max(1, t.lines_needed), 
                    reverse=True
                )
                
                # Calcola rettangoli occupati dai pezzi rimanenti
                occupied_rects = [
                    (l.x, l.y, l.width, l.height) for l in remaining_layouts
                ]
                
                # Riprova a posizionare i pezzi rimossi
                new_layouts = remaining_layouts.copy()
                current_weight = sum(l.weight for l in remaining_layouts)
                current_lines = sum(l.lines_used for l in remaining_layouts)
                current_area = sum(l.width * l.height for l in remaining_layouts)
                
                for tool in removed_tools:
                    # Verifica vincoli globali
                    if current_weight + tool.weight > autoclave.max_weight:
                        continue
                    if current_lines + tool.lines_needed > self.parameters.vacuum_lines_capacity:
                        continue
                    
                    # Cerca posizione con FFD migliorato (padding più piccolo)
                    best_pos = self._find_enhanced_position(tool, autoclave, occupied_rects)
                    
                    if best_pos:
                        x, y, width, height, rotated = best_pos
                        
                        new_layout = NestingLayout(
                            odl_id=tool.odl_id,
                            x=x,
                            y=y,
                            width=width,
                            height=height,
                            weight=tool.weight,
                            rotated=rotated,
                            lines_used=tool.lines_needed
                        )
                        
                        new_layouts.append(new_layout)
                        occupied_rects.append((x, y, width, height))
                        current_weight += tool.weight
                        current_lines += tool.lines_needed
                        current_area += width * height
                
                # 3. Valuta se la nuova soluzione è migliore
                total_area = autoclave.width * autoclave.height
                area_pct = (current_area / total_area * 100) if total_area > 0 else 0
                vacuum_util_pct = (current_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
                new_efficiency = 0.7 * area_pct + 0.3 * vacuum_util_pct
                
                if new_efficiency > best_solution.metrics.efficiency_score:
                    # Accetta la nuova soluzione
                    metrics = NestingMetrics(
                        area_pct=area_pct,
                        vacuum_util_pct=vacuum_util_pct,
                        lines_used=current_lines,
                        total_weight=current_weight,
                        positioned_count=len(new_layouts),
                        excluded_count=len(tools) - len(new_layouts),
                        efficiency_score=new_efficiency,
                        time_solver_ms=(time.time() - start_time) * 1000,
                        fallback_used=best_solution.metrics.fallback_used,
                        heuristic_iters=iteration + 1
                    )
                    
                    # Calcola ODL esclusi
                    positioned_ids = {l.odl_id for l in new_layouts}
                    excluded_odls = [
                        {
                            'odl_id': tool.odl_id,
                            'motivo': 'Escluso dopo heuristica RRGH',
                            'dettagli': f"Tool non riposizionato durante miglioramento iterativo"
                        }
                        for tool in tools if tool.odl_id not in positioned_ids
                    ]
                    
                    best_solution = NestingSolution(
                        layouts=new_layouts,
                        excluded_odls=excluded_odls,
                        metrics=metrics,
                        success=True,
                        algorithm_status=f"{best_solution.algorithm_status}_RRGH",
                        message=f"Heuristica RRGH migliorata: {new_efficiency:.1f}% efficienza"
                    )
                    
                    self.logger.info(f"  ✅ Iterazione {iteration+1}: miglioramento {new_efficiency:.1f}%")
                else:
                    self.logger.info(f"  ⚖️ Iterazione {iteration+1}: nessun miglioramento")
                    
            except Exception as e:
                self.logger.warning(f"  ⚠️ Errore iterazione {iteration+1}: {str(e)}")
                continue
        
        return best_solution
    
    def _find_enhanced_position(
        self, 
        tool: ToolInfo, 
        autoclave: AutoclaveInfo, 
        occupied_rects: List[Tuple[float, float, float, float]]
    ) -> Optional[Tuple[float, float, float, float, bool]]:
        """
        Trova posizione ottimale con FFD migliorato e padding ridotto per heuristica
        """
        
        # Usa padding ridotto per migliorare placement
        margin = int(max(5, self.parameters.min_distance_mm // 2))
        
        # Prova entrambi gli orientamenti
        orientations = []
        if tool.width + margin <= autoclave.width and tool.height + margin <= autoclave.height:
            orientations.append((tool.width, tool.height, False))
        if tool.height + margin <= autoclave.width and tool.width + margin <= autoclave.height:
            orientations.append((tool.height, tool.width, True))
        
        # Griglia più fine per heuristica
        step = 5
        
        for width, height, rotated in orientations:
            for y in range(margin, int(round(autoclave.height - height)) + 1, step):
                for x in range(margin, int(round(autoclave.width - width)) + 1, step):
                    
                    # Controlla sovrapposizioni
                    overlaps = False
                    for rect_x, rect_y, rect_w, rect_h in occupied_rects:
                        if not (x + width <= rect_x or x >= rect_x + rect_w or 
                               y + height <= rect_y or y >= rect_y + rect_h):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        # NUOVO: Vincolo pezzi pesanti nella metà inferiore
                        if tool.weight > self.parameters.heavy_piece_threshold_kg:
                            half_height = autoclave.height / 2
                            if y < half_height:
                                continue  # Pezzo pesante deve stare nella metà inferiore
                        
                        return (x, y, width, height, rotated)
        
        return None 

    def _collect_exclusion_reasons(
        self, 
        solution: NestingSolution, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo
    ) -> NestingSolution:
        """
        🔍 NUOVO v1.4.14: Raccoglie e analizza i motivi di esclusione dettagliati
        
        Analizza tutti i pezzi e aggiorna la solution con motivi dettagliati di esclusione.
        Usa il metodo _can_place per diagnostica approfondita.
        """
        positioned_ids = {layout.odl_id for layout in solution.layouts}
        
        # Analizza tutti i pezzi non posizionati
        for tool in tools:
            if tool.odl_id not in positioned_ids:
                # Usa _can_place per diagnostica dettagliata
                self._can_place(tool, autoclave)
                
                # Se il pezzo non ha motivi di esclusione (teoricamente posizionabile)
                # ma non è stato piazzato, aggiungi motivo "placement_failed"
                if not tool.debug_reasons:
                    tool.debug_reasons.append("placement_failed")
                    tool.excluded = True
                
                # Cerca se già presente negli esclusi
                found_exclusion = None
                for exc in solution.excluded_odls:
                    if exc.get('odl_id') == tool.odl_id:
                        found_exclusion = exc
                        break
                
                # Aggiorna o aggiungi esclusione con motivi dettagliati
                detailed_reasons = ', '.join(tool.debug_reasons)
                if found_exclusion:
                    found_exclusion['motivi_dettagliati'] = detailed_reasons
                    found_exclusion['debug_reasons'] = tool.debug_reasons.copy()
                else:
                    solution.excluded_odls.append({
                        'odl_id': tool.odl_id,
                        'motivo': detailed_reasons or 'Motivo sconosciuto',
                        'motivi_dettagliati': detailed_reasons,
                        'debug_reasons': tool.debug_reasons.copy(),
                        'dettagli': f"Tool {tool.width}x{tool.height}mm, {tool.weight}kg, {tool.lines_needed} linee"
                    })
                
                self.logger.debug(f"🔍 ODL {tool.odl_id} escluso: {detailed_reasons}")
        
        # Log riassuntivo
        excluded_summary = {}
        for tool in tools:
            if tool.excluded and tool.debug_reasons:
                for reason in tool.debug_reasons:
                    excluded_summary[reason] = excluded_summary.get(reason, 0) + 1
        
        if excluded_summary:
            self.logger.info(f"🔍 RIASSUNTO ESCLUSIONI: {excluded_summary}")
        
        return solution 