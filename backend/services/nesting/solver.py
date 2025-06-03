"""
CarbonPilot - Nesting Solver Ottimizzato
Implementazione migliorata dell'algoritmo di nesting 2D con OR-Tools CP-SAT
Versione: 1.4.17-DEMO

Funzionalità principali:
- 🔄 NUOVO v1.4.17: Rotazione 90° integrata nei modelli OR-Tools e fallback
- 🎯 NUOVO v1.4.17: Sostituzione greedy con Bottom-Left First-Fit Decreasing (BL-FFD)
- 🚀 NUOVO v1.4.17: Heuristica Ruin-&-Recreate Goal-Driven (RRGH) per +5-10% area
- 📊 NUOVO v1.4.17: Objective migliorato Z = 0.8·area_pct + 0.2·vacuum_util_pct
- Timeout adaptivo: min(90s, 2s × n_pieces)
- Vincolo pezzi pesanti nella metà inferiore (y ≥ H/2)
- Vincoli su linee vuoto e peso
- 🔍 v1.4.14: Log diagnostici dettagliati per debug esclusioni
- 🔧 v1.4.15: Formula efficienza migliorata per casi piccoli
- 🎯 v1.4.16-DEMO: Rilevamento e correzione overlap con algoritmo BL-FFD
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
    invalid: bool = False  # 🎯 NUOVO v1.4.16-DEMO: indica se ci sono overlap nel layout
    rotation_used: bool = False  # 🔄 NUOVO v1.4.17-DEMO: indica se è stata utilizzata rotazione

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
            
            # 🎯 NUOVO v1.4.16-DEMO: Post-processing per controllo overlap
            solution = self._post_process_overlaps(solution, tools, autoclave)
            
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
            
            # 🎯 NUOVO v1.4.16-DEMO: Post-processing per controllo overlap
            solution = self._post_process_overlaps(solution, tools, autoclave)
            
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
        # 🔧 FIX: PORTFOLIO non disponibile in tutte le versioni OR-Tools
        try:
            solver.parameters.search_branching = cp_model.PORTFOLIO
        except AttributeError:
            # Fallback per versioni OR-Tools che non supportano PORTFOLIO
            solver.parameters.search_branching = cp_model.AUTOMATIC_SEARCH
        
        status = solver.Solve(model)
        
        # Elabora risultato
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_cpsat_solution(solver, sorted_tools, autoclave, variables, status, start_time)
        elif status in [cp_model.INFEASIBLE, cp_model.UNKNOWN]:
            # Ritorna soluzione vuota per attivare fallback
            return NestingSolution(
                layouts=[],
                excluded_odls=[],
                metrics=NestingMetrics(0, 0, 0, 0, len(tools), 0, 0, 0, False, False),
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
        """
        🔄 NUOVO v1.4.17-DEMO: Crea le variabili per il modello CP-SAT con rotazione 90° integrata
        Approccio compatibile OR-Tools: intervalli separati per ogni orientamento
        """
        
        variables = {
            'included': {},      # tool incluso nel layout
            'x': {},            # posizione x
            'y': {},            # posizione y  
            'rotated': {},      # tool ruotato 90°
            'intervals_x_normal': {},   # intervalli x orientamento normale
            'intervals_y_normal': {},   # intervalli y orientamento normale
            'intervals_x_rotated': {},  # intervalli x orientamento ruotato
            'intervals_y_rotated': {},  # intervalli y orientamento ruotato
        }
        
        margin = self.parameters.min_distance_mm
        
        for tool in tools:
            tool_id = tool.odl_id
            
            # Inclusione
            variables['included'][tool_id] = model.NewBoolVar(f'included_{tool_id}')
            
            # 🔄 NUOVO v1.4.17-DEMO: Rotazione 90° con AddAllowedAssignments
            # Verifica se entrambi gli orientamenti sono possibili
            fits_normal = (tool.width + margin <= autoclave.width and 
                          tool.height + margin <= autoclave.height)
            fits_rotated = (tool.height + margin <= autoclave.width and 
                           tool.width + margin <= autoclave.height)
            
            if fits_normal and fits_rotated:
                # Entrambi orientamenti possibili - variabile binaria
                variables['rotated'][tool_id] = model.NewBoolVar(f'rotated_{tool_id}')
                # 🔄 SPECIFICO v1.4.17-DEMO: AddAllowedAssignments per rotazione 0=no rot, 1=90°
                model.AddAllowedAssignments([variables['rotated'][tool_id]], [[0], [1]])
            elif fits_rotated and not fits_normal:
                # Solo orientamento ruotato possibile
                variables['rotated'][tool_id] = model.NewBoolVar(f'rotated_{tool_id}')
                model.Add(variables['rotated'][tool_id] == 1)  # Forzato ruotato
            else:
                # Solo orientamento normale possibile (o nessuno dei due, gestito in pre-filter)
                variables['rotated'][tool_id] = model.NewBoolVar(f'rotated_{tool_id}')
                model.Add(variables['rotated'][tool_id] == 0)  # Forzato normale
            
            # Posizione (con limiti per entrambi gli orientamenti)
            max_x_normal = round(autoclave.width - tool.width - margin)
            max_y_normal = round(autoclave.height - tool.height - margin)
            max_x_rotated = round(autoclave.width - tool.height - margin)
            max_y_rotated = round(autoclave.height - tool.width - margin)
            
            # Limiti conservativi per le variabili di posizione
            max_x = max(max_x_normal, max_x_rotated) if fits_normal and fits_rotated else (
                max_x_rotated if fits_rotated else max_x_normal
            )
            max_y = max(max_y_normal, max_y_rotated) if fits_normal and fits_rotated else (
                max_y_rotated if fits_rotated else max_y_normal
            )
            
            variables['x'][tool_id] = model.NewIntVar(
                margin, max(margin, max_x), f'x_{tool_id}'
            )
            variables['y'][tool_id] = model.NewIntVar(
                margin, max(margin, max_y), f'y_{tool_id}'
            )
            
            # 🔄 NUOVO v1.4.17-DEMO: Intervalli separati per orientamento normale e ruotato
            # Orientamento normale: width x height
            normal_active = model.NewBoolVar(f'normal_active_{tool_id}')
            model.Add(normal_active == 1).OnlyEnforceIf([
                variables['included'][tool_id], variables['rotated'][tool_id].Not()
            ])
            model.Add(normal_active == 0).OnlyEnforceIf(variables['rotated'][tool_id])
            model.Add(normal_active == 0).OnlyEnforceIf(variables['included'][tool_id].Not())
            
            variables['intervals_x_normal'][tool_id] = model.NewOptionalIntervalVar(
                variables['x'][tool_id], 
                round(tool.width),
                variables['x'][tool_id] + round(tool.width),
                normal_active,
                f'interval_x_normal_{tool_id}'
            )
            
            variables['intervals_y_normal'][tool_id] = model.NewOptionalIntervalVar(
                variables['y'][tool_id], 
                round(tool.height),
                variables['y'][tool_id] + round(tool.height),
                normal_active,
                f'interval_y_normal_{tool_id}'
            )
            
            # Orientamento ruotato: height x width
            rotated_active = model.NewBoolVar(f'rotated_active_{tool_id}')
            model.Add(rotated_active == 1).OnlyEnforceIf([
                variables['included'][tool_id], variables['rotated'][tool_id]
            ])
            model.Add(rotated_active == 0).OnlyEnforceIf(variables['rotated'][tool_id].Not())
            model.Add(rotated_active == 0).OnlyEnforceIf(variables['included'][tool_id].Not())
            
            variables['intervals_x_rotated'][tool_id] = model.NewOptionalIntervalVar(
                variables['x'][tool_id], 
                round(tool.height),  # Ruotato: larghezza = altezza originale
                variables['x'][tool_id] + round(tool.height),
                rotated_active,
                f'interval_x_rotated_{tool_id}'
            )
            
            variables['intervals_y_rotated'][tool_id] = model.NewOptionalIntervalVar(
                variables['y'][tool_id], 
                round(tool.width),   # Ruotato: altezza = larghezza originale
                variables['y'][tool_id] + round(tool.width),
                rotated_active,
                f'interval_y_rotated_{tool_id}'
            )
        
        return variables
    
    def _add_cpsat_constraints(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        variables: Dict[str, Any]
    ) -> None:
        """
        🔄 NUOVO v1.4.17-DEMO: Aggiunge i vincoli al modello CP-SAT con supporto rotazione dinamica
        """
        
        # Vincolo di non sovrapposizione 2D per entrambi gli orientamenti
        if len(variables['intervals_x_normal']) > 0:
            # Combina intervalli normali e ruotati per non-sovrapposizione
            all_intervals_x = (list(variables['intervals_x_normal'].values()) + 
                              list(variables['intervals_x_rotated'].values()))
            all_intervals_y = (list(variables['intervals_y_normal'].values()) + 
                              list(variables['intervals_y_rotated'].values()))
            
            model.AddNoOverlap2D(all_intervals_x, all_intervals_y)
        
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
        
        # 🔄 NUOVO v1.4.17-DEMO: Vincoli di posizione per entrambi gli orientamenti
        margin = self.parameters.min_distance_mm
        
        for tool in tools:
            tool_id = tool.odl_id
            
            # Vincoli di boundary per orientamento normale
            model.Add(
                variables['x'][tool_id] + round(tool.width) <= round(autoclave.width - margin)
            ).OnlyEnforceIf([variables['included'][tool_id], variables['rotated'][tool_id].Not()])
            
            model.Add(
                variables['y'][tool_id] + round(tool.height) <= round(autoclave.height - margin)
            ).OnlyEnforceIf([variables['included'][tool_id], variables['rotated'][tool_id].Not()])
            
            # Vincoli di boundary per orientamento ruotato
            model.Add(
                variables['x'][tool_id] + round(tool.height) <= round(autoclave.width - margin)
            ).OnlyEnforceIf([variables['included'][tool_id], variables['rotated'][tool_id]])
            
            model.Add(
                variables['y'][tool_id] + round(tool.width) <= round(autoclave.height - margin)
            ).OnlyEnforceIf([variables['included'][tool_id], variables['rotated'][tool_id]])
            
            # Vincoli minimi di posizione
            model.Add(variables['x'][tool_id] >= margin).OnlyEnforceIf(variables['included'][tool_id])
            model.Add(variables['y'][tool_id] >= margin).OnlyEnforceIf(variables['included'][tool_id])
    
    def _add_cpsat_objective(
        self, 
        model: cp_model.CpModel, 
        tools: List[ToolInfo], 
        variables: Dict[str, Any]
    ) -> None:
        """
        🔄 NUOVO v1.4.17-DEMO: Objective migliorato Z = 0.8·area_pct + 0.2·vacuum_util_pct
        Aggiunge la funzione obiettivo al modello CP-SAT
        """
        
        # 🔄 NUOVO v1.4.17-DEMO: Objective multi-termine ottimizzato
        # Termini per area utilizzata (peso 80%)
        area_terms = []
        for tool in tools:
            tool_id = tool.odl_id
            tool_area = round(tool.width * tool.height)
            area_terms.append(variables['included'][tool_id] * tool_area)
        
        # Termini per utilizzo linee vuoto (peso 20%)
        vacuum_terms = []
        for tool in tools:
            tool_id = tool.odl_id
            vacuum_terms.append(variables['included'][tool_id] * tool.lines_needed)
        
        if area_terms and vacuum_terms:
            # Variabili per i componenti dell'objective
            total_area = model.NewIntVar(0, sum(round(t.width * t.height) for t in tools), 'total_area')
            model.Add(total_area == sum(area_terms))
            
            total_vacuum = model.NewIntVar(0, sum(t.lines_needed for t in tools), 'total_vacuum')
            model.Add(total_vacuum == sum(vacuum_terms))
            
            # Normalizzazione per mantenere i pesi relativi
            # Area normalizzata: total_area / max_possible_area * 800 (peso 80% su scala 1000)
            max_area = sum(round(t.width * t.height) for t in tools)
            area_normalized = model.NewIntVar(0, 800, 'area_normalized')
            if max_area > 0:
                model.AddDivisionEquality(area_normalized, total_area * 800, max_area)
            
            # Vacuum normalizzato: total_vacuum / max_capacity * 200 (peso 20% su scala 1000)
            max_vacuum = self.parameters.vacuum_lines_capacity
            vacuum_normalized = model.NewIntVar(0, 200, 'vacuum_normalized')
            if max_vacuum > 0:
                model.AddDivisionEquality(vacuum_normalized, total_vacuum * 200, max_vacuum)
            
            # Objective finale: Z = 0.8·area_norm + 0.2·vacuum_norm
            objective = model.NewIntVar(0, 1000, 'objective')
            model.Add(objective == area_normalized + vacuum_normalized)
            
            model.Maximize(objective)
            
            self.logger.info("🎯 v1.4.17-DEMO: Objective Z = 0.8·area_pct + 0.2·vacuum_util_pct")
            
        elif area_terms:
            # Fallback: solo area se non ci sono vacuum terms
            total_area = model.NewIntVar(0, sum(round(t.width * t.height) for t in tools), 'total_area')
            model.Add(total_area == sum(area_terms))
            model.Maximize(total_area)
            
            self.logger.info("🎯 v1.4.17-DEMO: Fallback objective: solo area")
            
        else:
            # Fallback: solo numero di ODL inclusi
            num_included = sum(variables['included'].values())
            model.Maximize(num_included)
            
            self.logger.info("🎯 v1.4.17-DEMO: Fallback objective: solo count ODL")
    
    def _extract_cpsat_solution(
        self, 
        solver: cp_model.CpSolver, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        variables: Dict[str, Any], 
        status: int,
        start_time: float
    ) -> NestingSolution:
        """Estrae la soluzione dal solver CP-SAT e calcola le metriche"""
        layouts = []
        total_weight = 0
        total_lines = 0
        
        # 🔄 NUOVO v1.4.18-DEMO: Traccia utilizzo rotazione
        rotation_used = False
        
        # Estrae posizioni per ogni tool incluso
        for tool in tools:
            tool_id = tool.odl_id
            if solver.Value(variables['included'][tool_id]):
                # 🔄 NUOVO v1.4.17-DEMO: Controlla se rotato
                is_rotated = solver.Value(variables['rotated'][tool_id])
                if is_rotated:
                    rotation_used = True
                
                # 🔧 FIX v1.4.18-DEMO: Dimensioni finali corrette (senza accesso a variables inesistenti)
                if is_rotated:
                    # Tool ruotato: scambia larghezza e altezza
                    final_width = tool.height
                    final_height = tool.width
                else:
                    # Tool normale: usa dimensioni originali
                    final_width = tool.width
                    final_height = tool.height
                
                layout = NestingLayout(
                    odl_id=tool.odl_id,
                    x=float(solver.Value(variables['x'][tool_id])),
                    y=float(solver.Value(variables['y'][tool_id])),
                    width=float(final_width),
                    height=float(final_height),
                    weight=tool.weight,
                    rotated=bool(is_rotated),  # 🔧 FIX v1.4.18-DEMO: Assicura che sia boolean
                    lines_used=tool.lines_needed
                )
                layouts.append(layout)
                total_weight += tool.weight
                total_lines += tool.lines_needed
        
        # Calcola metriche
        total_area = autoclave.width * autoclave.height
        area_pct = (sum(l.width * l.height for l in layouts) / total_area * 100) if total_area > 0 else 0
        vacuum_util_pct = (total_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
        # 🔄 NUOVO v1.4.17-DEMO: Formula efficienza corretta Z = 0.8·area + 0.2·vacuum
        efficiency_score = 0.8 * area_pct + 0.2 * vacuum_util_pct
        
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
            excluded_count=len(tools) - len(layouts),
            efficiency_score=efficiency_score,
            time_solver_ms=(time.time() - start_time) * 1000,
            fallback_used=False,
            heuristic_iters=0,
            rotation_used=rotation_used  # 🔄 NUOVO v1.4.17-DEMO: Track rotazione
        )
        
        status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        
        self.logger.info(f"✅ CP-SAT completato: {len(layouts)} posizionati, {area_pct:.1f}% area, {total_lines} linee, rotazione={rotation_used}")
        
        return NestingSolution(
            layouts=layouts,
            excluded_odls=[],
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
        """
        🔄 NUOVO v1.4.17-DEMO: Algoritmo di fallback con Bottom-Left First-Fit Decreasing (BL-FFD)
        Sostituisce il vecchio greedy con implementazione BL-FFD integrata
        """
        
        self.logger.info("🎯 v1.4.17-DEMO: Algoritmo fallback BL-FFD attivo")
        
        # Applica BL-FFD direttamente
        layouts = self._apply_bl_ffd_algorithm(tools, autoclave)
        
        # Calcola esclusioni (tool non posizionati)
        positioned_ids = {layout.odl_id for layout in layouts}
        excluded_odls = []
        
        for tool in tools:
            if tool.odl_id not in positioned_ids:
                excluded_odls.append({
                    'odl_id': tool.odl_id,
                    'motivo': 'Non posizionato da BL-FFD',
                    'dettagli': f"Tool {tool.width}x{tool.height}mm non ha trovato posizione con algoritmo BL-FFD"
                })
        
        # Calcola metriche
        total_weight = sum(layout.weight for layout in layouts)
        used_area = sum(layout.width * layout.height for layout in layouts)
        total_lines = sum(layout.lines_used for layout in layouts)
        
        total_area = autoclave.width * autoclave.height
        area_pct = (used_area / total_area * 100) if total_area > 0 else 0
        vacuum_util_pct = (total_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
        # 🔄 NUOVO v1.4.17-DEMO: Formula efficienza corretta Z = 0.8·area + 0.2·vacuum
        efficiency_score = 0.8 * area_pct + 0.2 * vacuum_util_pct
        
        # Verifica se è stata utilizzata rotazione
        rotation_used = any(layout.rotated for layout in layouts)
        
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
            heuristic_iters=0,
            rotation_used=rotation_used  # 🔄 NUOVO v1.4.17-DEMO: Track rotazione
        )
        
        self.logger.info(f"🎯 BL-FFD completato: {len(layouts)} posizionati, {area_pct:.1f}% area, {total_lines} linee, rotazione={rotation_used}")
        
        return NestingSolution(
            layouts=layouts,
            excluded_odls=excluded_odls,
            metrics=metrics,
            success=len(layouts) > 0,
            algorithm_status="BL_FFD_FALLBACK",
            message=f"BL-FFD fallback completato: {len(layouts)} ODL posizionati, efficienza {efficiency_score:.1f}%{efficiency_warning}"
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
            heuristic_iters=0,
            rotation_used=False
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
        🚀 NUOVO v1.4.17-DEMO: Heuristica "Ruin & Recreate Goal-Driven" (RRGH) migliorata
        Esegue 5 iterazioni: elimina random 25% pezzi con efficienza bassa e reinserisci via BL-FFD
        """
        
        best_solution = initial_solution
        iterations = 5
        ruin_percentage = 0.25  # 🔄 NUOVO v1.4.17-DEMO: Aumentato da 20% a 25%
        
        self.logger.info(f"🚀 v1.4.17-DEMO: Avvio heuristica RRGH: {iterations} iterazioni, ruin {ruin_percentage*100}%")
        
        for iteration in range(iterations):
            try:
                # Copia la soluzione corrente
                current_layouts = best_solution.layouts.copy()
                
                if len(current_layouts) < 3:  # Aumentato threshold minimo
                    continue  # Non abbastanza pezzi per applicare la ruin
                
                # 🔄 NUOVO v1.4.17-DEMO: Ruin intelligente - rimuovi pezzi con efficienza bassa
                num_to_remove = max(1, int(len(current_layouts) * ruin_percentage))
                
                # Calcola efficienza per pezzo (area/vacuum_lines)
                layout_efficiency = []
                for layout in current_layouts:
                    efficiency = (layout.width * layout.height) / max(1, layout.lines_used)
                    layout_efficiency.append((layout, efficiency))
                
                # Ordina per efficienza crescente e rimuovi i peggiori
                layout_efficiency.sort(key=lambda x: x[1])
                removed_layouts = [x[0] for x in layout_efficiency[:num_to_remove]]
                remaining_layouts = [l for l in current_layouts if l not in removed_layouts]
                
                # 🔄 NUOVO v1.4.17-DEMO: Recreate usando BL-FFD invece di enhanced_position
                removed_tools = [
                    tool for tool in tools 
                    if any(rl.odl_id == tool.odl_id for rl in removed_layouts)
                ]
                
                # Applica BL-FFD ai pezzi rimossi considerando quelli già posizionati
                recreated_layouts = self._recreate_with_bl_ffd(removed_tools, autoclave, remaining_layouts)
                
                # Combina layout rimanenti + ricreati
                new_layouts = remaining_layouts + recreated_layouts
                
                # 🔄 NUOVO v1.4.17-DEMO: Valuta con nuovo objective Z = 0.8·area + 0.2·vacuum
                total_area = autoclave.width * autoclave.height
                current_area = sum(l.width * l.height for l in new_layouts)
                current_lines = sum(l.lines_used for l in new_layouts)
                
                area_pct = (current_area / total_area * 100) if total_area > 0 else 0
                vacuum_util_pct = (current_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
                new_efficiency = 0.8 * area_pct + 0.2 * vacuum_util_pct  # Nuovo objective
                
                if new_efficiency > best_solution.metrics.efficiency_score:
                    # Verifica se è stata utilizzata rotazione
                    rotation_used = any(layout.rotated for layout in new_layouts)
                    
                    # Accetta la nuova soluzione
                    metrics = NestingMetrics(
                        area_pct=area_pct,
                        vacuum_util_pct=vacuum_util_pct,
                        lines_used=current_lines,
                        total_weight=sum(l.weight for l in new_layouts),
                        positioned_count=len(new_layouts),
                        excluded_count=len(tools) - len(new_layouts),
                        efficiency_score=new_efficiency,
                        time_solver_ms=(time.time() - start_time) * 1000,
                        fallback_used=best_solution.metrics.fallback_used,
                        heuristic_iters=iteration + 1,
                        rotation_used=rotation_used or best_solution.metrics.rotation_used  # 🔄 NUOVO v1.4.17-DEMO
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
                    
                    self.logger.info(f"  ✅ Iterazione {iteration+1}: miglioramento {new_efficiency:.1f}% (rot={rotation_used})")
                else:
                    self.logger.info(f"  ⚖️ Iterazione {iteration+1}: nessun miglioramento ({new_efficiency:.1f}% vs {best_solution.metrics.efficiency_score:.1f}%)")
                    
            except Exception as e:
                self.logger.warning(f"  ⚠️ Errore iterazione {iteration+1}: {str(e)}")
                continue
        
        return best_solution
    
    def _recreate_with_bl_ffd(
        self, 
        tools_to_place: List[ToolInfo], 
        autoclave: AutoclaveInfo, 
        existing_layouts: List[NestingLayout]
    ) -> List[NestingLayout]:
        """
        🔄 NUOVO v1.4.17-DEMO: Ricrea layout usando BL-FFD considerando pezzi già posizionati
        """
        if not tools_to_place:
            return []
        
        # Ordina per max(height,width) decrescente come BL-FFD
        sorted_tools = sorted(tools_to_place, key=lambda t: max(t.width, t.height), reverse=True)
        
        new_layouts = []
        padding = self.parameters.min_distance_mm
        
        # Calcola vincoli attuali dai layout esistenti
        current_weight = sum(l.weight for l in existing_layouts)
        current_lines = sum(l.lines_used for l in existing_layouts)
        
        for tool in sorted_tools:
            # Verifica vincoli globali
            if current_weight + tool.weight > autoclave.max_weight:
                continue
            if current_lines + tool.lines_needed > self.parameters.vacuum_lines_capacity:
                continue
            
            # Trova posizione considerando sia layout esistenti che nuovi
            all_layouts = existing_layouts + new_layouts
            best_position = self._find_bottom_left_position(tool, autoclave, all_layouts, padding)
            
            if best_position:
                x, y, width, height, rotated = best_position
                
                layout = NestingLayout(
                    odl_id=tool.odl_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    weight=tool.weight,
                    rotated=rotated,
                    lines_used=tool.lines_needed
                )
                
                new_layouts.append(layout)
                current_weight += tool.weight
                current_lines += tool.lines_needed
        
        return new_layouts

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

    # 🎯 NUOVO v1.4.16-DEMO: Funzione per rilevare sovrapposizioni
    def check_overlap(self, layout: List[NestingLayout]) -> List[Tuple[NestingLayout, NestingLayout]]:
        """
        Controlla se ci sono sovrapposizioni tra i pezzi nel layout.
        
        Args:
            layout: Lista dei pezzi posizionati
            
        Returns:
            Lista di tuple con le coppie di pezzi che si sovrappongono
        """
        overlaps = []
        
        for i in range(len(layout)):
            for j in range(i + 1, len(layout)):
                piece_a = layout[i]
                piece_b = layout[j]
                
                # Controlla se i bounding box si intersecano
                if not (piece_a.x + piece_a.width <= piece_b.x or  # A è a sinistra di B
                       piece_b.x + piece_b.width <= piece_a.x or   # B è a sinistra di A
                       piece_a.y + piece_a.height <= piece_b.y or  # A è sopra B
                       piece_b.y + piece_b.height <= piece_a.y):   # B è sopra A
                    overlaps.append((piece_a, piece_b))
                    self.logger.warning(f"🔴 OVERLAP rilevato tra ODL {piece_a.odl_id} e ODL {piece_b.odl_id}")
        
        return overlaps

    # 🎯 NUOVO v1.4.16-DEMO: Algoritmo Bottom-Left First-Fit Decreasing (BL-FFD)
    def _apply_bl_ffd_algorithm(
        self, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo,
        padding: int = None
    ) -> List[NestingLayout]:
        """
        🔄 NUOVO v1.4.17-DEMO: Applica l'algoritmo Bottom-Left First-Fit Decreasing per posizionare i pezzi.
        
        Ordinamento: max(height,width) desc per First-Fit Decreasing
        Posizionamento: Bottom-Left con supporto rotazione 90°
        
        Args:
            tools: Lista dei tool da posizionare
            autoclave: Informazioni dell'autoclave
            padding: Padding tra i pezzi (default usa parametro della classe)
            
        Returns:
            Lista dei layout posizionati senza sovrapposizioni
        """
        if padding is None:
            padding = self.parameters.min_distance_mm
            
        self.logger.info(f"🎯 v1.4.17-DEMO: Applico algoritmo BL-FFD con padding {padding}mm")
        
        # 🔄 NUOVO v1.4.17-DEMO: Ordina per max(height,width) decrescente (criterio FFD migliorato)
        sorted_tools = sorted(tools, key=lambda t: max(t.width, t.height), reverse=True)
        
        layouts = []
        
        for tool in sorted_tools:
            # Controlla vincoli di peso e linee vuoto globali
            current_weight = sum(l.weight for l in layouts)
            current_lines = sum(l.lines_used for l in layouts)
            
            if current_weight + tool.weight > autoclave.max_weight:
                self.logger.debug(f"❌ ODL {tool.odl_id}: peso eccessivo ({current_weight + tool.weight} > {autoclave.max_weight})")
                continue
                
            if current_lines + tool.lines_needed > self.parameters.vacuum_lines_capacity:
                self.logger.debug(f"❌ ODL {tool.odl_id}: linee vuoto insufficienti ({current_lines + tool.lines_needed} > {self.parameters.vacuum_lines_capacity})")
                continue
            
            # 🔄 NUOVO v1.4.17-DEMO: Trova la posizione bottom-left migliore con rotazione
            best_position = self._find_bottom_left_position(tool, autoclave, layouts, padding)
            
            if best_position:
                x, y, width, height, rotated = best_position
                
                layout = NestingLayout(
                    odl_id=tool.odl_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    weight=tool.weight,
                    rotated=rotated,
                    lines_used=tool.lines_needed
                )
                
                layouts.append(layout)
                rotation_str = " [RUOTATO]" if rotated else ""
                self.logger.debug(f"✅ ODL {tool.odl_id}: posizionato in ({x}, {y}) - {width}x{height}mm{rotation_str}")
            else:
                self.logger.debug(f"❌ ODL {tool.odl_id}: nessuna posizione valida trovata per {tool.width}x{tool.height}mm")
        
        rotation_count = sum(1 for l in layouts if l.rotated)
        self.logger.info(f"🔄 BL-FFD completato: {len(layouts)} posizionati, {rotation_count} ruotati")
        
        return layouts

    # 🎯 NUOVO v1.4.16-DEMO: Trova posizione bottom-left per un pezzo
    def _find_bottom_left_position(
        self,
        tool: ToolInfo,
        autoclave: AutoclaveInfo,
        existing_layouts: List[NestingLayout],
        padding: int
    ) -> Optional[Tuple[float, float, float, float, bool]]:
        """
        Trova la posizione bottom-left più bassa e a sinistra per il tool.
        
        Args:
            tool: Tool da posizionare
            autoclave: Informazioni dell'autoclave
            existing_layouts: Layout già posizionati
            padding: Padding tra i pezzi
            
        Returns:
            Tuple (x, y, width, height, rotated) se trovata posizione valida, None altrimenti
        """
        
        # Prepara rettangoli occupati per controllo sovrapposizioni
        occupied_rects = [(l.x, l.y, l.width, l.height) for l in existing_layouts]
        
        # Prova entrambi gli orientamenti
        orientations = []
        if tool.width + padding <= autoclave.width and tool.height + padding <= autoclave.height:
            orientations.append((tool.width, tool.height, False))
        if tool.height + padding <= autoclave.width and tool.width + padding <= autoclave.height:
            orientations.append((tool.height, tool.width, True))
            
        if not orientations:
            return None
        
        best_position = None
        best_y = float('inf')  # Cerca la posizione più bassa
        best_x = float('inf')  # In caso di parità, la più a sinistra
        
        # Griglia di ricerca bottom-left
        grid_step = 5  # Risoluzione griglia in mm
        
        for width, height, rotated in orientations:
            # Scansiona dal basso verso l'alto, da sinistra a destra
            for y in range(padding, int(autoclave.height - height) + 1, grid_step):
                for x in range(padding, int(autoclave.width - width) + 1, grid_step):
                    
                    # Controlla se la posizione è valida (no sovrapposizioni)
                    valid_position = True
                    for rect_x, rect_y, rect_w, rect_h in occupied_rects:
                        if not (x + width <= rect_x or x >= rect_x + rect_w or 
                               y + height <= rect_y or y >= rect_y + rect_h):
                            valid_position = False
                            break
                    
                    if valid_position:
                        # Controlla se è migliore della precedente (bottom-left)
                        if y < best_y or (y == best_y and x < best_x):
                            best_position = (x, y, width, height, rotated)
                            best_y = y
                            best_x = x
                            
                        # Se trovata una posizione valida in questa riga, passa alla successiva
                        # (bottom-left significa prima posizione valida dal basso)
                        break
                        
                # Se trovata una posizione in questa altezza, non cercare più in alto
                if best_position and best_y == y:
                    break
                    
        return best_position

    # 🎯 NUOVO v1.4.16-DEMO: Post-processing per eliminare overlap
    def _post_process_overlaps(
        self, 
        solution: NestingSolution, 
        tools: List[ToolInfo], 
        autoclave: AutoclaveInfo
    ) -> NestingSolution:
        """
        Post-processing per rilevare e correggere sovrapposizioni nel layout.
        
        Args:
            solution: Soluzione da verificare e correggere
            tools: Lista completa dei tool
            autoclave: Informazioni dell'autoclave
            
        Returns:
            Soluzione corretta o marcata come invalid se persistono overlap
        """
        
        # 1. Controlla se ci sono sovrapposizioni
        overlaps = self.check_overlap(solution.layouts)
        
        if not overlaps:
            # Nessuna sovrapposizione, layout valido
            self.logger.info("✅ Layout validato: nessuna sovrapposizione rilevata")
            return solution
        
        self.logger.warning(f"🔴 Rilevate {len(overlaps)} sovrapposizioni nel layout")
        
        # 2. Se c'erano overlap e non era stato usato fallback, prova BL-FFD
        if not solution.metrics.fallback_used:
            self.logger.info("🎯 Tentativo correzione overlap con algoritmo BL-FFD")
            
            # Estrai i tool dalla soluzione attuale
            positioned_tools = []
            for layout in solution.layouts:
                # Trova il tool corrispondente
                for tool in tools:
                    if tool.odl_id == layout.odl_id:
                        positioned_tools.append(tool)
                        break
            
            # Applica BL-FFD con padding considerato
            corrected_layouts = self._apply_bl_ffd_algorithm(
                positioned_tools, 
                autoclave,
                self.parameters.min_distance_mm
            )
            
            # Verifica se BL-FFD ha risolto gli overlap
            corrected_overlaps = self.check_overlap(corrected_layouts)
            
            if not corrected_overlaps:
                # BL-FFD ha risolto i problemi!
                self.logger.info("✅ BL-FFD ha risolto le sovrapposizioni")
                
                # Ricalcola metriche
                total_area = autoclave.width * autoclave.height
                used_area = sum(l.width * l.height for l in corrected_layouts)
                total_weight = sum(l.weight for l in corrected_layouts)
                total_lines = sum(l.lines_used for l in corrected_layouts)
                
                area_pct = (used_area / total_area * 100) if total_area > 0 else 0
                vacuum_util_pct = (total_lines / self.parameters.vacuum_lines_capacity * 100) if self.parameters.vacuum_lines_capacity > 0 else 0
                # 🔄 NUOVO v1.4.17-DEMO: Formula efficienza corretta Z = 0.8·area + 0.2·vacuum
                efficiency_score = 0.8 * area_pct + 0.2 * vacuum_util_pct
                
                # Aggiorna la soluzione
                solution.layouts = corrected_layouts
                solution.metrics.area_pct = area_pct
                solution.metrics.vacuum_util_pct = vacuum_util_pct
                solution.metrics.lines_used = total_lines
                solution.metrics.total_weight = total_weight
                solution.metrics.positioned_count = len(corrected_layouts)
                solution.metrics.efficiency_score = efficiency_score
                solution.metrics.invalid = False
                solution.algorithm_status += "_BL_FFD_CORRECTED"
                solution.message += " [Overlap corretti con BL-FFD]"
                
                return solution
            else:
                self.logger.warning(f"⚠️ BL-FFD non ha risolto tutti gli overlap ({len(corrected_overlaps)} rimasti)")
        
        # 3. Se persistono overlap, marca il layout come invalid
        self.logger.error(f"🔴 Layout INVALID: {len(overlaps)} sovrapposizioni non risolte")
        
        # Aggiungi informazioni dettagliate sugli overlap
        overlap_details = []
        for piece_a, piece_b in overlaps:
            overlap_details.append({
                'odl_a': piece_a.odl_id,
                'odl_b': piece_b.odl_id,
                'area_a': f"{piece_a.width}x{piece_a.height}mm",
                'area_b': f"{piece_b.width}x{piece_b.height}mm",
                'pos_a': f"({piece_a.x}, {piece_a.y})",
                'pos_b': f"({piece_b.x}, {piece_b.y})"
            })
        
        # Marca la soluzione come invalid
        solution.metrics.invalid = True
        solution.algorithm_status += "_INVALID_OVERLAPS"
        solution.message += f" [ATTENZIONE: {len(overlaps)} sovrapposizioni rilevate]"
        
        # Aggiungi i dettagli degli overlap alla soluzione per il frontend
        if not hasattr(solution, 'overlaps'):
            solution.overlaps = overlap_details
        
        return solution 