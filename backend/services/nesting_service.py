import logging
import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from models.odl import ODL
from models.tool import Tool
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.autoclave import Autoclave

# Configurazione logger
logger = logging.getLogger(__name__)

@dataclass
class ToolDimensions:
    """Classe per rappresentare le dimensioni di un tool"""
    width: float
    height: float
    weight: float
    ciclo_cura_id: Optional[int]
    
@dataclass
class NestingParameters:
    """Parametri per l'algoritmo di nesting"""
    padding_mm: int = 20
    min_distance_mm: int = 15
    priorita_area: bool = True
    
@dataclass
class ToolPosition:
    """Posizione di un tool sul piano"""
    odl_id: int
    x: float
    y: float
    width: float
    height: float
    peso: float
    rotated: bool = False  # Indica se il tool è ruotato di 90°
    
@dataclass
class NestingResult:
    """Risultato dell'algoritmo di nesting"""
    positioned_tools: List[ToolPosition]
    excluded_odls: List[Dict[str, Any]]
    total_weight: float
    used_area: float
    total_area: float
    efficiency: float
    success: bool
    algorithm_status: str

class NestingService:
    """Servizio per l'algoritmo di nesting 2D con OR-Tools"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_odl_data(self, db: Session, odl_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Recupera i dati necessari per gli ODL specificati
        """
        try:
            odl_data = []
            
            for odl_id in odl_ids:
                # Carica ODL con tutte le relazioni necessarie
                odl = db.query(ODL)\
                    .join(Tool)\
                    .join(Parte)\
                    .outerjoin(CicloCura)\
                    .filter(ODL.id == odl_id)\
                    .first()
                
                if not odl:
                    self.logger.warning(f"ODL {odl_id} non trovato")
                    continue
                    
                if not odl.tool:
                    self.logger.warning(f"ODL {odl_id} non ha un tool associato")
                    continue
                    
                odl_info = {
                    'odl_id': odl.id,
                    'tool_width': odl.tool.larghezza_piano or 0,
                    'tool_height': odl.tool.lunghezza_piano or 0,
                    'tool_weight': odl.tool.peso or 0,
                    'ciclo_cura_id': odl.parte.ciclo_cura_id if odl.parte else None,
                    'parte_descrizione': odl.parte.descrizione_breve if odl.parte else "N/A",
                    'tool_part_number': odl.tool.part_number_tool
                }
                
                odl_data.append(odl_info)
                
            self.logger.info(f"Caricati dati per {len(odl_data)} ODL su {len(odl_ids)} richiesti")
            return odl_data
            
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dati ODL: {str(e)}")
            raise
            
    def get_autoclave_data(self, db: Session, autoclave_id: int) -> Dict[str, Any]:
        """
        Recupera i dati dell'autoclave specificata
        """
        try:
            autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            
            if not autoclave:
                raise ValueError(f"Autoclave {autoclave_id} non trovata")
                
            return {
                'id': autoclave.id,
                'nome': autoclave.nome,
                'larghezza_piano': autoclave.larghezza_piano or 0,
                'lunghezza': autoclave.lunghezza or 0,
                'max_load_kg': autoclave.max_load_kg or 1000,
                'use_secondary_plane': autoclave.use_secondary_plane or False
            }
            
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dati autoclave: {str(e)}")
            raise
            
    def check_ciclo_cura_compatibility(self, odl_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Verifica la compatibilità dei cicli di cura tra gli ODL
        """
        try:
            # Raggruppa per ciclo di cura
            cicli_cura = {}
            for odl in odl_data:
                ciclo_id = odl['ciclo_cura_id']
                if ciclo_id not in cicli_cura:
                    cicli_cura[ciclo_id] = []
                cicli_cura[ciclo_id].append(odl)
            
            # Per ora, prendiamo il ciclo di cura più comune
            if None in cicli_cura:
                # ODL senza ciclo di cura - li escludiamo
                excluded = [
                    {
                        'odl_id': odl['odl_id'],
                        'motivo': 'Ciclo di cura non definito',
                        'dettagli': f"ODL {odl['odl_id']} non ha un ciclo di cura associato"
                    }
                    for odl in cicli_cura[None]
                ]
                del cicli_cura[None]
            else:
                excluded = []
            
            if not cicli_cura:
                return [], excluded
                
            # Trova il ciclo più comune
            ciclo_principale = max(cicli_cura.keys(), key=lambda k: len(cicli_cura[k]))
            compatible_odls = cicli_cura[ciclo_principale]
            
            # Gli ODL con cicli diversi vengono esclusi
            for ciclo_id, odls in cicli_cura.items():
                if ciclo_id != ciclo_principale:
                    excluded.extend([
                        {
                            'odl_id': odl['odl_id'],
                            'motivo': 'Ciclo di cura incompatibile',
                            'dettagli': f"ODL {odl['odl_id']} ha ciclo di cura {ciclo_id}, ma il batch usa ciclo {ciclo_principale}"
                        }
                        for odl in odls
                    ])
            
            self.logger.info(f"Compatibilità cicli: {len(compatible_odls)} ODL compatibili, {len(excluded)} esclusi")
            return compatible_odls, excluded
            
        except Exception as e:
            self.logger.error(f"Errore nella verifica compatibilità cicli: {str(e)}")
            raise
            
    def perform_nesting_2d(
        self, 
        odl_data: List[Dict[str, Any]], 
        autoclave_data: Dict[str, Any], 
        parameters: NestingParameters
    ) -> NestingResult:
        """
        Esegue l'algoritmo di nesting 2D utilizzando OR-Tools CP-SAT
        """
        try:
            # Dimensioni del piano autoclave
            plane_width = autoclave_data['larghezza_piano']
            plane_height = autoclave_data['lunghezza'] 
            max_weight = autoclave_data['max_load_kg']
            
            self.logger.info(f"Piano autoclave: {plane_width}x{plane_height}mm, peso max: {max_weight}kg")
            
            if not odl_data:
                return NestingResult(
                    positioned_tools=[],
                    excluded_odls=[],
                    total_weight=0,
                    used_area=0,
                    total_area=plane_width * plane_height,
                    efficiency=0,
                    success=True,
                    algorithm_status="Nessun ODL da posizionare"
                )
            
            # Pre-filtraggio migliorato: escludi ODL troppo grandi o pesanti
            valid_odls = []
            excluded_odls = []
            
            for odl in odl_data:
                tool_width = odl['tool_width']
                tool_height = odl['tool_height']
                tool_weight = odl['tool_weight']
                
                self.logger.info(f"🔍 Controllo ODL {odl['odl_id']}: Tool {tool_width}x{tool_height}mm, peso {tool_weight}kg")
                
                # Margini di sicurezza per il posizionamento
                margin = parameters.min_distance_mm
                
                # Verifica dimensioni con controllo più accurato
                # Orientamento normale: width x height
                fits_normal = (tool_width + margin <= plane_width and 
                              tool_height + margin <= plane_height)
                
                # Orientamento ruotato: height x width  
                fits_rotated = (tool_height + margin <= plane_width and 
                               tool_width + margin <= plane_height)
                
                self.logger.info(f"   Orientamento normale ({tool_width}x{tool_height} + {margin}mm): fits = {fits_normal}")
                self.logger.info(f"   Orientamento ruotato ({tool_height}x{tool_width} + {margin}mm): fits = {fits_rotated}")
                
                if not fits_normal and not fits_rotated:
                    excluded_odls.append({
                        'odl_id': odl['odl_id'],
                        'motivo': 'Dimensioni eccessive',
                        'dettagli': f"Tool {tool_width}x{tool_height}mm non entra nel piano {plane_width}x{plane_height}mm in nessun orientamento (margine {margin}mm)"
                    })
                    self.logger.warning(f"   ❌ ODL {odl['odl_id']} escluso per dimensioni")
                    continue
                    
                # Verifica peso
                if tool_weight > max_weight:
                    excluded_odls.append({
                        'odl_id': odl['odl_id'],
                        'motivo': 'Peso eccessivo',
                        'dettagli': f"Tool {tool_weight}kg supera il limite di {max_weight}kg"
                    })
                    self.logger.warning(f"   ❌ ODL {odl['odl_id']} escluso per peso")
                    continue
                    
                # Aggiungi informazioni su orientamenti possibili
                odl['fits_normal'] = fits_normal
                odl['fits_rotated'] = fits_rotated
                valid_odls.append(odl)
                
                orientation_info = []
                if fits_normal:
                    orientation_info.append("normale")
                if fits_rotated:
                    orientation_info.append("ruotato")
                
                self.logger.info(f"   ✅ ODL {odl['odl_id']} valido per orientamenti: {', '.join(orientation_info)}")
            
            if not valid_odls:
                return NestingResult(
                    positioned_tools=[],
                    excluded_odls=excluded_odls,
                    total_weight=0,
                    used_area=0,
                    total_area=plane_width * plane_height,
                    efficiency=0,
                    success=False,
                    algorithm_status="Nessun ODL può essere posizionato"
                )
            
            self.logger.info(f"📊 Pre-filtraggio completato: {len(valid_odls)} ODL validi, {len(excluded_odls)} esclusi")
            
            # Ordina per area decrescente (strategia greedy)
            valid_odls.sort(key=lambda x: x['tool_width'] * x['tool_height'], reverse=True)
            
            # Crea il modello CP-SAT
            model = cp_model.CpModel()
            
            # Variabili per posizioni (x, y) e rotazione di ogni tool
            positions = {}
            intervals_x = {}
            intervals_y = {}
            tool_included = {}
            tool_rotated = {}
            
            for i, odl in enumerate(valid_odls):
                odl_id = odl['odl_id']
                original_width = int(odl['tool_width'])
                original_height = int(odl['tool_height'])
                margin = parameters.min_distance_mm
                
                self.logger.info(f"🔧 Creazione variabili per ODL {odl_id}: {original_width}x{original_height}mm")
                
                # Variabile booleana per inclusione
                tool_included[odl_id] = model.NewBoolVar(f'included_{odl_id}')
                
                # Gestione rotazione migliorata
                if odl['fits_normal'] and odl['fits_rotated']:
                    # Entrambi gli orientamenti possibili - rotazione variabile
                    tool_rotated[odl_id] = model.NewBoolVar(f'rotated_{odl_id}')
                    self.logger.info(f"   Rotazione: VARIABILE (entrambi orientamenti possibili)")
                elif odl['fits_normal']:
                    # Solo orientamento normale possibile
                    tool_rotated[odl_id] = 0
                    self.logger.info(f"   Rotazione: FISSA normale (solo questo orientamento possibile)")
                else:
                    # Solo orientamento ruotato possibile
                    tool_rotated[odl_id] = 1
                    self.logger.info(f"   Rotazione: FISSA ruotata (solo questo orientamento possibile)")
                
                # Calcolo limiti di posizione più accurato
                if odl['fits_normal']:
                    # Spazio disponibile per orientamento normale
                    max_x_normal = int(plane_width - original_width - margin)
                    max_y_normal = int(plane_height - original_height - margin)
                    self.logger.info(f"   Normale: max_pos ({max_x_normal}, {max_y_normal})")
                else:
                    max_x_normal = margin  # Valore di fallback
                    max_y_normal = margin
                
                if odl['fits_rotated']:
                    # Spazio disponibile per orientamento ruotato
                    max_x_rotated = int(plane_width - original_height - margin)  # Nota: height diventa width
                    max_y_rotated = int(plane_height - original_width - margin)   # Nota: width diventa height
                    self.logger.info(f"   Ruotato: max_pos ({max_x_rotated}, {max_y_rotated})")
                else:
                    max_x_rotated = margin  # Valore di fallback
                    max_y_rotated = margin
                
                # Variabili di posizione
                x = model.NewIntVar(margin, int(plane_width - margin), f'x_{odl_id}')
                y = model.NewIntVar(margin, int(plane_height - margin), f'y_{odl_id}')
                
                # Vincoli di posizione basati sulla rotazione
                if isinstance(tool_rotated[odl_id], int):
                    # Rotazione fissa
                    if tool_rotated[odl_id] == 0:  # Non ruotato
                        if odl['fits_normal']:
                            model.Add(x <= max_x_normal).OnlyEnforceIf(tool_included[odl_id])
                            model.Add(y <= max_y_normal).OnlyEnforceIf(tool_included[odl_id])
                            width_var = original_width
                            height_var = original_height
                        else:
                            # Questo non dovrebbe mai accadere con la logica corretta
                            model.Add(tool_included[odl_id] == 0)  # Forza esclusione
                            width_var = original_width
                            height_var = original_height
                    else:  # Ruotato
                        if odl['fits_rotated']:
                            model.Add(x <= max_x_rotated).OnlyEnforceIf(tool_included[odl_id])
                            model.Add(y <= max_y_rotated).OnlyEnforceIf(tool_included[odl_id])
                            width_var = original_height  # Dimensioni scambiate
                            height_var = original_width
                        else:
                            # Questo non dovrebbe mai accadere con la logica corretta
                            model.Add(tool_included[odl_id] == 0)  # Forza esclusione
                            width_var = original_width
                            height_var = original_height
                else:
                    # Rotazione variabile - vincoli condizionali
                    
                    # Vincoli per orientamento normale (non ruotato)
                    if odl['fits_normal']:
                        model.Add(x <= max_x_normal).OnlyEnforceIf([tool_included[odl_id], tool_rotated[odl_id].Not()])
                        model.Add(y <= max_y_normal).OnlyEnforceIf([tool_included[odl_id], tool_rotated[odl_id].Not()])
                    
                    # Vincoli per orientamento ruotato
                    if odl['fits_rotated']:
                        model.Add(x <= max_x_rotated).OnlyEnforceIf([tool_included[odl_id], tool_rotated[odl_id]])
                        model.Add(y <= max_y_rotated).OnlyEnforceIf([tool_included[odl_id], tool_rotated[odl_id]])
                    
                    # Per gli intervalli, useremo le dimensioni massime per evitare sovrapposizioni
                    width_var = max(original_width, original_height)
                    height_var = max(original_width, original_height)
                
                self.logger.info(f"   Dimensioni intervallo: {width_var}x{height_var}mm")
                
                # Salva informazioni per il risultato finale
                positions[odl_id] = (x, y, width_var, height_var, original_width, original_height)
                
                # Intervalli per non sovrapposizione
                intervals_x[odl_id] = model.NewOptionalIntervalVar(
                    x, width_var, x + width_var, tool_included[odl_id], f'interval_x_{odl_id}'
                )
                intervals_y[odl_id] = model.NewOptionalIntervalVar(
                    y, height_var, y + height_var, tool_included[odl_id], f'interval_y_{odl_id}'
                )
            
            # Vincolo di non sovrapposizione 2D
            if len(intervals_x) > 0:
                model.AddNoOverlap2D(
                    list(intervals_x.values()),
                    list(intervals_y.values())
                )
                self.logger.info(f"🔒 Aggiunto vincolo di non sovrapposizione per {len(intervals_x)} tool")
            
            # Vincolo di peso massimo
            total_weight_var = model.NewIntVar(0, int(max_weight * 1000), 'total_weight')
            weight_terms = []
            for odl in valid_odls:
                odl_id = odl['odl_id']
                if odl_id in tool_included:
                    weight_terms.append(
                        tool_included[odl_id] * int(odl['tool_weight'] * 1000)
                    )
            
            if weight_terms:
                model.Add(total_weight_var == sum(weight_terms))
                model.Add(total_weight_var <= int(max_weight * 1000))
                self.logger.info(f"⚖️ Aggiunto vincolo di peso massimo: {max_weight}kg")
            
            # Funzione obiettivo CORRETTA
            # SEMPRE massimizza il numero di ODL inclusi come obiettivo primario
            num_included = sum(tool_included.values())
            
            if parameters.priorita_area:
                # Obiettivo: massimizza copertura del piano (area utilizzata)
                # Prima massimizza ODL, poi massimizza area utilizzata
                
                # Calcola l'area totale utilizzata dai tool posizionati
                total_used_area = model.NewIntVar(0, int(plane_width * plane_height), 'total_used_area')
                area_terms = []
                
                for odl in valid_odls:
                    odl_id = odl['odl_id']
                    if odl_id in tool_included:
                        # Area del tool (larghezza * altezza)
                        tool_area = int(odl['tool_width'] * odl['tool_height'])
                        area_terms.append(tool_included[odl_id] * tool_area)
                
                if area_terms:
                    model.Add(total_used_area == sum(area_terms))
                
                # Obiettivo combinato: massimizza ODL (peso 10000) + massimizza area utilizzata (peso 1)
                # Questo assicura che il numero di ODL sia sempre prioritario, ma con area massima
                model.Maximize(num_included * 10000 + total_used_area)
                self.logger.info("🎯 Obiettivo: Massimizza ODL (priorità) + massimizza copertura piano (secondario)")
            else:
                # Massimizza solo il numero di ODL inclusi
                model.Maximize(num_included)
                self.logger.info("🎯 Obiettivo: Massimizza numero ODL inclusi")
            
            # Risolvi il problema
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 30.0  # Timeout di 30 secondi
            
            self.logger.info(f"Avvio risoluzione CP-SAT per {len(valid_odls)} ODL")
            status = solver.Solve(model)
            
            # Elabora risultati
            positioned_tools = []
            final_excluded = excluded_odls.copy()
            total_weight = 0
            used_area = 0
            
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                for odl in valid_odls:
                    odl_id = odl['odl_id']
                    if odl_id in tool_included and solver.Value(tool_included[odl_id]):
                        x, y, w, h, w_orig, h_orig = positions[odl_id]
                        
                        # Determina se il tool è ruotato
                        is_rotated = False
                        if isinstance(tool_rotated[odl_id], int):
                            is_rotated = bool(tool_rotated[odl_id])
                        else:
                            is_rotated = bool(solver.Value(tool_rotated[odl_id]))
                        
                        # Calcola dimensioni finali in base alla rotazione
                        if is_rotated:
                            final_width = float(h_orig)  # Larghezza diventa altezza originale
                            final_height = float(w_orig)  # Altezza diventa larghezza originale
                        else:
                            final_width = float(w_orig)  # Dimensioni originali
                            final_height = float(h_orig)
                        
                        pos = ToolPosition(
                            odl_id=odl_id,
                            x=float(solver.Value(x)),
                            y=float(solver.Value(y)),
                            width=final_width,
                            height=final_height,
                            peso=float(odl['tool_weight']),
                            rotated=is_rotated
                        )
                        positioned_tools.append(pos)
                        total_weight += odl['tool_weight']
                        used_area += final_width * final_height
                    else:
                        final_excluded.append({
                            'odl_id': odl_id,
                            'motivo': 'Non ottimale per il nesting',
                            'dettagli': f"ODL {odl_id} non incluso nella soluzione ottimale"
                        })
                
                algorithm_status = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
                success = True
                
            else:
                # Nessuna soluzione trovata
                final_excluded.extend([
                    {
                        'odl_id': odl['odl_id'],
                        'motivo': 'Nessuna soluzione trovata',
                        'dettagli': f"L'algoritmo non è riuscito a trovare una configurazione valida"
                    }
                    for odl in valid_odls
                ])
                algorithm_status = "INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN"
                success = False
            
            total_area = plane_width * plane_height
            efficiency = (used_area / total_area * 100) if total_area > 0 else 0
            
            self.logger.info(f"Nesting completato: {len(positioned_tools)} ODL posizionati, {len(final_excluded)} esclusi")
            self.logger.info(f"Efficienza: {efficiency:.1f}%, Peso totale: {total_weight:.1f}kg")
            
            # Log info sulle rotazioni
            if positioned_tools:
                rotated_count = sum(1 for tool in positioned_tools if tool.rotated)
                self.logger.info(f"Tool ruotati: {rotated_count}/{len(positioned_tools)} ({rotated_count/len(positioned_tools)*100:.1f}%)")
            
            return NestingResult(
                positioned_tools=positioned_tools,
                excluded_odls=final_excluded,
                total_weight=total_weight,
                used_area=used_area,
                total_area=total_area,
                efficiency=efficiency,
                success=success,
                algorithm_status=algorithm_status
            )
            
        except Exception as e:
            self.logger.error(f"Errore nell'algoritmo di nesting: {str(e)}")
            raise
            
    def generate_nesting(
        self, 
        db: Session, 
        odl_ids: List[int], 
        autoclave_id: int, 
        parameters: NestingParameters
    ) -> NestingResult:
        """
        Metodo principale per generare un nesting completo
        """
        try:
            self.logger.info(f"Inizio generazione nesting per {len(odl_ids)} ODL su autoclave {autoclave_id}")
            
            # 1. Carica dati ODL
            odl_data = self.get_odl_data(db, odl_ids)
            if not odl_data:
                return NestingResult(
                    positioned_tools=[],
                    excluded_odls=[{'odl_id': odl_id, 'motivo': 'ODL non trovato', 'dettagli': 'ODL non esistente nel database'} for odl_id in odl_ids],
                    total_weight=0,
                    used_area=0,
                    total_area=0,
                    efficiency=0,
                    success=False,
                    algorithm_status="NO_DATA"
                )
            
            # 2. Carica dati autoclave
            autoclave_data = self.get_autoclave_data(db, autoclave_id)
            
            # 3. Verifica compatibilità cicli di cura
            compatible_odls, excluded_cicli = self.check_ciclo_cura_compatibility(odl_data)
            
            # 4. Esegui nesting 2D
            result = self.perform_nesting_2d(compatible_odls, autoclave_data, parameters)
            
            # 5. Aggiungi esclusioni per cicli incompatibili
            result.excluded_odls.extend(excluded_cicli)
            
            self.logger.info(f"Nesting completato con successo: {result.success}")
            return result
            
        except Exception as e:
            self.logger.error(f"Errore nella generazione nesting: {str(e)}")
            raise 