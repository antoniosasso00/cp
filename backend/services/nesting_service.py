"""
🔧 SERVIZIO NESTING UNIFICATO
=============================

Servizio consolidato per il nesting 2D con OR-Tools che include:
1. Algoritmi di nesting avanzati (OR-Tools + fallback greedy)
2. Validazioni estese del sistema
3. Gestione robustezza e fallback automatico
4. Creazione automatica batch nel database
5. Error handling avanzato

Consolidato da NestingService + RobustNestingService
Autore: CarbonPilot Development Team
Data: 2025-06-05
"""

import logging
import json
import uuid
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.odl import ODL
from models.tool import Tool
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum

# 🚀 AEROSPACE: Import del solver ottimizzato
from services.nesting.solver import NestingModel, NestingParameters as AerospaceParameters, ToolInfo, AutoclaveInfo

# Configurazione logger
logger = logging.getLogger(__name__)

@dataclass
class NestingParameters:
    """Parametri per il nesting ottimizzato"""
    padding_mm: float = 10  # Padding aggiuntivo attorno ai pezzi
    min_distance_mm: float = 15  # Distanza minima tra i pezzi
    vacuum_lines_capacity: int = 20  # Capacità massima linee di vuoto (default per compatibilità)
    use_fallback: bool = True  # Usa fallback greedy se CP-SAT fallisce
    allow_heuristic: bool = True  # Usa euristiche avanzate
    timeout_override: Optional[int] = None  # Override del timeout predefinito
    
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
    lines_used: int = 1  # Numero di linee vuoto utilizzate
    
@dataclass
class NestingResult:
    """Risultato dell'algoritmo di nesting"""
    positioned_tools: List[ToolPosition]
    excluded_odls: List[Dict[str, Any]]
    total_weight: float
    used_area: float
    total_area: float
    area_pct: float  # Percentuale area utilizzata
    lines_used: int  # Totale linee vuoto utilizzate
    efficiency: float
    success: bool
    algorithm_status: str

def fallback_greedy_nesting(
    odl_data: List[Dict[str, Any]], 
    autoclave_data: Dict[str, Any], 
    parameters: NestingParameters
) -> NestingResult:
    """
    Algoritmo di fallback greedy con first-fit decreasing sull'asse lungo
    """
    logger.info("🔄 Attivazione algoritmo fallback greedy")
    
    # ✅ FIX CRITICO: Dimensioni del piano autoclave CORRETTE
    plane_width = autoclave_data['lunghezza']          # Larghezza = lunghezza autoclave
    plane_height = autoclave_data['larghezza_piano']   # Altezza = larghezza piano
    max_weight = autoclave_data['max_load_kg']
    
    # Ordina per dimensione asse lungo decrescente (first-fit decreasing)
    sorted_odls = sorted(
        odl_data, 
        key=lambda x: max(x['tool_width'], x['tool_height']), 
        reverse=True
    )
    
    positioned_tools = []
    excluded_odls = []
    total_weight = 0
    used_area = 0
    total_lines_used = 0
    
    # Lista di rettangoli occupati per controllo sovrapposizioni
    occupied_rects = []
    
    for odl in sorted_odls:
        tool_width = odl['tool_width']
        tool_height = odl['tool_height']
        tool_weight = odl['tool_weight']
        odl_id = odl['odl_id']
        
        # Numero di linee vuoto per questo tool
        tool_lines = odl.get('lines_needed', 1)
        
        # Verifica vincoli globali
        if total_weight + tool_weight > max_weight:
            excluded_odls.append({
                'odl_id': odl_id,
                'motivo': 'Peso eccessivo nel batch',
                'dettagli': f"Aggiungere il tool ({tool_weight}kg) supererebbe il limite di peso ({max_weight}kg)"
            })
            continue
            
        if total_lines_used + tool_lines > parameters.vacuum_lines_capacity:
            excluded_odls.append({
                'odl_id': odl_id,
                'motivo': 'Capacità linee vuoto superata',
                'dettagli': f"Aggiungere il tool ({tool_lines} linee) supererebbe la capacità ({parameters.vacuum_lines_capacity} linee)"
            })
            continue
        
        # Trova la prima posizione valida
        best_position = None
        
        # Prova entrambi gli orientamenti
        orientations = []
        if tool_width + parameters.min_distance_mm <= plane_width and tool_height + parameters.min_distance_mm <= plane_height:
            orientations.append((tool_width, tool_height, False))
        if tool_height + parameters.min_distance_mm <= plane_width and tool_width + parameters.min_distance_mm <= plane_height:
            orientations.append((tool_height, tool_width, True))
            
        for width, height, rotated in orientations:
            # Griglia di posizioni possibili
            for y in range(parameters.min_distance_mm, int(plane_height - height) + 1, 10):
                for x in range(parameters.min_distance_mm, int(plane_width - width) + 1, 10):
                    
                    # Controlla sovrapposizioni con tool già posizionati
                    overlaps = False
                    for rect in occupied_rects:
                        if not (x + width <= rect[0] or x >= rect[0] + rect[2] or 
                               y + height <= rect[1] or y >= rect[1] + rect[3]):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        best_position = (x, y, width, height, rotated)
                        break
                        
                if best_position:
                    break
            if best_position:
                break
        
        if best_position:
            x, y, width, height, rotated = best_position
            
            # Aggiungi il rettangolo occupato
            occupied_rects.append((x, y, width, height))
            
            positioned_tools.append(ToolPosition(
                odl_id=odl_id,
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                peso=float(tool_weight),
                rotated=rotated,
                lines_used=tool_lines
            ))
            
            total_weight += tool_weight
            used_area += width * height
            total_lines_used += tool_lines
            
            logger.info(f"✅ Tool {odl_id} posizionato: {x},{y} {width}x{height} (ruotato: {rotated})")
        else:
            excluded_odls.append({
                'odl_id': odl_id,
                'motivo': 'Spazio insufficiente',
                'dettagli': f"Non è stata trovata una posizione valida per il tool {tool_width}x{tool_height}mm"
            })
            logger.info(f"❌ Tool {odl_id} escluso: spazio insufficiente")
    
    total_area = plane_width * plane_height
    efficiency = (used_area / total_area * 100) if total_area > 0 else 0
    area_pct = efficiency
    
    logger.info(f"🔄 Fallback greedy completato: {len(positioned_tools)} tool posizionati, efficienza {efficiency:.1f}%")
    
    return NestingResult(
        positioned_tools=positioned_tools,
        excluded_odls=excluded_odls,
        total_weight=total_weight,
        used_area=used_area,
        total_area=total_area,
        area_pct=area_pct,
        lines_used=total_lines_used,
        efficiency=efficiency,
        success=len(positioned_tools) > 0,
        algorithm_status="FALLBACK_GREEDY"
    )

class NestingService:
    """Servizio unificato per il nesting 2D con robustezza e gestione avanzata"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fallback_strategies = {
            'NO_ODL_AVAILABLE': self._handle_no_odl,
            'NO_AUTOCLAVE_AVAILABLE': self._handle_no_autoclave,
            'ALGORITHM_FAILED': self._handle_algorithm_failure,
            'POSITIONING_FAILED': self._handle_positioning_failure,
            'DATA_CORRUPTION': self._handle_data_corruption
        }
    
    def validate_system_prerequisites(self, db: Session) -> Dict[str, Any]:
        """Valida i prerequisiti del sistema per il nesting"""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 1. Verifica ODL disponibili
            odl_attesa_cura = db.query(ODL).filter(ODL.status == 'Attesa Cura').count()
            validation_result['statistics']['odl_attesa_cura'] = odl_attesa_cura
            
            if odl_attesa_cura == 0:
                validation_result['valid'] = False
                validation_result['issues'].append({
                    'type': 'NO_ODL_AVAILABLE',
                    'message': 'Nessun ODL in stato "Attesa Cura"',
                    'severity': 'CRITICAL'
                })
            elif odl_attesa_cura < 2:
                validation_result['warnings'].append({
                    'type': 'LOW_ODL_COUNT',
                    'message': f'Solo {odl_attesa_cura} ODL disponibili - efficienza ridotta',
                    'severity': 'WARNING'
                })
            
            # 2. Verifica autoclavi disponibili
            autoclavi_disponibili = db.query(Autoclave).filter(
                Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
            ).count()
            validation_result['statistics']['autoclavi_disponibili'] = autoclavi_disponibili
            
            if autoclavi_disponibili == 0:
                validation_result['valid'] = False
                validation_result['issues'].append({
                    'type': 'NO_AUTOCLAVE_AVAILABLE',
                    'message': 'Nessuna autoclave disponibile',
                    'severity': 'CRITICAL'
                })
            
            # 3. Verifica integrità dati ODL
            odl_con_problemi = db.query(ODL).filter(
                (ODL.parte_id == None) | (ODL.tool_id == None)
            ).count()
            
            if odl_con_problemi > 0:
                validation_result['warnings'].append({
                    'type': 'DATA_INTEGRITY',
                    'message': f'{odl_con_problemi} ODL con dati mancanti',
                    'severity': 'WARNING'
                })
            
            # 4. Verifica tool con dimensioni
            tools_senza_dimensioni = db.query(Tool).filter(
                (Tool.larghezza_piano == None) | (Tool.lunghezza_piano == None)
            ).count()
            
            if tools_senza_dimensioni > 0:
                validation_result['warnings'].append({
                    'type': 'MISSING_DIMENSIONS',
                    'message': f'{tools_senza_dimensioni} tool senza dimensioni',
                    'severity': 'WARNING'
                })
            
            logger.info(f"Validazione prerequisiti completata: {validation_result['valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Errore durante validazione prerequisiti: {str(e)}")
            validation_result['valid'] = False
            validation_result['issues'].append({
                'type': 'VALIDATION_ERROR',
                'message': f'Errore di validazione: {str(e)}',
                'severity': 'CRITICAL'
            })
            return validation_result
    
    def fix_system_issues(self, db: Session, validation_result: Dict[str, Any]) -> bool:
        """Tenta di risolvere automaticamente i problemi identificati"""
        fixed_issues = []
        
        try:
            for issue in validation_result.get('issues', []):
                issue_type = issue['type']
                
                if issue_type == 'NO_AUTOCLAVE_AVAILABLE':
                    # Aggiorna autoclavi non guaste a disponibili
                    updated = db.query(Autoclave).filter(
                        Autoclave.stato != StatoAutoclaveEnum.GUASTO
                    ).update({
                        'stato': StatoAutoclaveEnum.DISPONIBILE,
                        'updated_at': func.now()
                    })
                    
                    if updated > 0:
                        fixed_issues.append(f"Aggiornate {updated} autoclavi a disponibili")
                        logger.info(f"Auto-fix: {updated} autoclavi rese disponibili")
                
                elif issue_type == 'NO_ODL_AVAILABLE':
                    # Log per debug - in produzione potresti voler creare ODL test
                    logger.warning("Nessun ODL disponibile - richiede intervento manuale")
            
            if fixed_issues:
                db.commit()
                logger.info(f"Issues risolti automaticamente: {fixed_issues}")
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore durante auto-fix: {str(e)}")
            return False
    
    def generate_robust_nesting(
        self, 
        db: Session, 
        odl_ids: List[int], 
        autoclave_ids: List[int], 
        parameters: NestingParameters
    ) -> Dict[str, Any]:
        """Genera un nesting robusto con gestione errori avanzata"""
        
        result = {
            'success': False,
            'batch_id': '',
            'message': '',
            'positioned_tools': [],
            'excluded_odls': [],
            'efficiency': 0.0,
            'total_weight': 0.0,
            'algorithm_status': 'STARTING',
            'validation_report': None,
            'fixes_applied': []
        }
        
        try:
            # 1. Validazione prerequisiti
            logger.info("🔍 Validazione prerequisiti sistema...")
            validation = self.validate_system_prerequisites(db)
            result['validation_report'] = validation
            
            # 2. Tentativo di fix automatico se necessario
            if not validation['valid']:
                logger.info("⚙️ Tentativo risoluzione automatica problemi...")
                if self.fix_system_issues(db, validation):
                    result['fixes_applied'].append("Auto-fix applicato con successo")
                    # Re-validazione dopo fix
                    validation = self.validate_system_prerequisites(db)
                    result['validation_report'] = validation
            
            # 3. Se ancora non valido, usa strategia fallback
            if not validation['valid']:
                logger.warning("⚠️ Sistema non valido - applicazione strategia fallback")
                return self._apply_fallback_strategy(db, validation, result)
            
            # 4. Validazione input
            validated_odl_ids = self._validate_odl_list(db, odl_ids)
            validated_autoclave_ids = self._validate_autoclave_list(db, autoclave_ids)
            
            if not validated_odl_ids:
                result['message'] = "Nessun ODL valido fornito"
                result['algorithm_status'] = 'NO_VALID_ODL'
                return result
                
            if not validated_autoclave_ids:
                result['message'] = "Nessuna autoclave valida fornita"
                result['algorithm_status'] = 'NO_VALID_AUTOCLAVE'
                return result
            
            # 5. Esecuzione nesting per ogni autoclave
            best_result = None
            best_efficiency = 0
            best_autoclave_id = None
            
            for autoclave_id in validated_autoclave_ids:
                logger.info(f"🚀 Tentativo nesting su autoclave {autoclave_id}")
                
                nesting_result = self.generate_nesting(
                    db, validated_odl_ids, autoclave_id, parameters
                )
                
                if nesting_result.success and nesting_result.efficiency > best_efficiency:
                    best_result = nesting_result
                    best_efficiency = nesting_result.efficiency
                    best_autoclave_id = autoclave_id
                    logger.info(f"✅ Miglior risultato trovato: {best_efficiency:.1f}% su autoclave {autoclave_id}")
            
            # 6. Gestione risultato
            if best_result and best_result.success:
                # Crea batch nel database
                batch_id = self._create_robust_batch(db, best_result, best_autoclave_id, parameters)
                
                if batch_id:
                    result.update({
                        'success': True,
                        'batch_id': batch_id,
                        'message': f'Nesting completato con successo su autoclave {best_autoclave_id}',
                        'positioned_tools': [
                            {
                                'odl_id': tool.odl_id,
                                'x': tool.x,
                                'y': tool.y,
                                'width': tool.width,
                                'height': tool.height,
                                'peso': tool.peso,
                                'rotated': tool.rotated,
                                'lines_used': tool.lines_used
                            } for tool in best_result.positioned_tools
                        ],
                        'excluded_odls': best_result.excluded_odls,
                        'efficiency': best_result.efficiency,
                        'total_weight': best_result.total_weight,
                        'algorithm_status': best_result.algorithm_status
                    })
                else:
                    result['message'] = "Errore nella creazione del batch"
                    result['algorithm_status'] = 'BATCH_CREATION_FAILED'
            else:
                result['message'] = "Nessun nesting valido trovato per le autoclavi fornite"
                result['algorithm_status'] = 'NO_VALID_SOLUTION'
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nel nesting robusto: {str(e)}")
            result.update({
                'message': f'Errore imprevisto: {str(e)}',
                'algorithm_status': 'UNEXPECTED_ERROR'
            })
            return result

    def get_odl_data(self, db: Session, odl_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Recupera i dati necessari per gli ODL specificati
        """
        try:
            odl_data = []
            logger.info(f"Caricamento dati per ODL: {odl_ids}")
            
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
                    'tool_part_number': odl.tool.part_number_tool,
                    'lines_needed': getattr(odl.parte, 'num_valvole_richieste', 1) if odl.parte else 1  # Nuovo: linee vuoto richieste
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
                'num_linee_vuoto': getattr(autoclave, 'num_linee_vuoto', 10)  # Nuovo: numero linee vuoto disponibili
            }
            
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dati autoclave: {str(e)}")
            raise
            
    def check_ciclo_cura_compatibility(self, odl_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        🔄 MIGLIORATO: Verifica la compatibilità dei cicli di cura tra gli ODL
        Ora supporta cicli di cura compatibili invece di richiedere cicli identici
        """
        try:
            # Raggruppa per ciclo di cura
            cicli_cura = {}
            odl_senza_ciclo = []
            
            for odl in odl_data:
                ciclo_id = odl['ciclo_cura_id']
                if ciclo_id is None:
                    odl_senza_ciclo.append(odl)
                else:
                    if ciclo_id not in cicli_cura:
                        cicli_cura[ciclo_id] = []
                    cicli_cura[ciclo_id].append(odl)
            
            # 🔄 NUOVO: Logica di compatibilità cicli di cura
            compatible_groups = self._find_compatible_cure_cycles(cicli_cura)
            
            if not compatible_groups:
                # Se non ci sono gruppi compatibili, usa il ciclo più comune
                if cicli_cura:
                    ciclo_principale = max(cicli_cura.keys(), key=lambda k: len(cicli_cura[k]))
                    compatible_odls = cicli_cura[ciclo_principale]
                    
                    # Escludi tutti gli altri cicli
                    excluded = []
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
                else:
                    compatible_odls = []
                    excluded = []
            else:
                # Usa il gruppo compatibile più grande
                best_group = max(compatible_groups, key=lambda g: sum(len(cicli_cura[cid]) for cid in g))
                compatible_odls = []
                for ciclo_id in best_group:
                    compatible_odls.extend(cicli_cura[ciclo_id])
                
                # Escludi cicli non compatibili
                excluded = []
                for ciclo_id, odls in cicli_cura.items():
                    if ciclo_id not in best_group:
                        excluded.extend([
                            {
                                'odl_id': odl['odl_id'],
                                'motivo': 'Ciclo di cura incompatibile con gruppo selezionato',
                                'dettagli': f"ODL {odl['odl_id']} ha ciclo di cura {ciclo_id}, incompatibile con gruppo {best_group}"
                            }
                            for odl in odls
                        ])
            
            # Gestisci ODL senza ciclo di cura
            if odl_senza_ciclo:
                excluded.extend([
                    {
                        'odl_id': odl['odl_id'],
                        'motivo': 'Ciclo di cura non definito',
                        'dettagli': f"ODL {odl['odl_id']} non ha un ciclo di cura associato"
                    }
                    for odl in odl_senza_ciclo
                ])
            
            self.logger.info(f"🔄 Compatibilità cicli: {len(compatible_odls)} ODL compatibili, {len(excluded)} esclusi")
            if compatible_groups:
                self.logger.info(f"🔄 Gruppo cicli compatibili selezionato: {best_group}")
            
            return compatible_odls, excluded
            
        except Exception as e:
            self.logger.error(f"Errore nella verifica compatibilità cicli: {str(e)}")
            raise
    
    def _find_compatible_cure_cycles(self, cicli_cura: Dict[int, List]) -> List[List[int]]:
        """
        🔄 ENHANCED: Trova gruppi di cicli di cura compatibili basati su parametri reali
        
        Args:
            cicli_cura: Dizionario {ciclo_id: [odl_list]}
            
        Returns:
            Lista di gruppi di cicli compatibili [[ciclo1, ciclo2], [ciclo3], ...]
        """
        try:
            if not cicli_cura:
                return []
                
            # Ottieni i dettagli dei cicli di cura dal database
            from models.ciclo_cura import CicloCura
            from sqlalchemy.orm import sessionmaker
            from database import engine
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                ciclo_details = {}
                for ciclo_id in cicli_cura.keys():
                    if ciclo_id is not None:
                        ciclo = session.query(CicloCura).filter(CicloCura.id == ciclo_id).first()
                        if ciclo:
                            ciclo_details[ciclo_id] = {
                                'temperatura': ciclo.temperatura,
                                'tempo_minuti': ciclo.tempo_minuti,
                                'pressione': ciclo.pressione,
                                'nome': ciclo.nome
                            }
                
                # Implementa logica di compatibilità avanzata
                compatible_groups = []
                processed_cycles = set()
                
                for ciclo_id, ciclo_info in ciclo_details.items():
                    if ciclo_id in processed_cycles:
                        continue
                        
                    # Crea un nuovo gruppo con questo ciclo
                    current_group = [ciclo_id]
                    processed_cycles.add(ciclo_id)
                    
                    # Trova cicli compatibili con questo
                    for other_ciclo_id, other_info in ciclo_details.items():
                        if other_ciclo_id in processed_cycles:
                            continue
                            
                        # Verifica compatibilità
                        if self._are_cycles_compatible(ciclo_info, other_info):
                            current_group.append(other_ciclo_id)
                            processed_cycles.add(other_ciclo_id)
                            self.logger.info(f"🔄 Cicli compatibili: {ciclo_info['nome']} + {other_info['nome']}")
                    
                    compatible_groups.append(current_group)
                
                # Aggiungi cicli None come gruppo separato se esistono
                if None in cicli_cura:
                    compatible_groups.append([None])
                
                self.logger.info(f"🔄 Gruppi cicli compatibili trovati: {len(compatible_groups)}")
                for i, group in enumerate(compatible_groups):
                    group_names = []
                    for cid in group:
                        if cid is None:
                            group_names.append("Non definito")
                        elif cid in ciclo_details:
                            group_names.append(ciclo_details[cid]['nome'])
                        else:
                            group_names.append(f"ID:{cid}")
                    self.logger.info(f"🔄 Gruppo {i+1}: {group_names}")
                
                return compatible_groups
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Errore nella ricerca cicli compatibili: {str(e)}")
            # Fallback: ogni ciclo forma il proprio gruppo
            return [[ciclo_id] for ciclo_id in cicli_cura.keys()]
    
    def _are_cycles_compatible(self, cycle1: Dict, cycle2: Dict) -> bool:
        """
        🔄 NUOVO: Verifica se due cicli di cura sono compatibili
        
        Args:
            cycle1, cycle2: Dizionari con temperatura, tempo_minuti, pressione
            
        Returns:
            True se i cicli sono compatibili
        """
        try:
            # Tolleranze per compatibilità
            TEMP_TOLERANCE = 10  # ±10°C
            TIME_TOLERANCE_PCT = 0.20  # ±20% del tempo
            PRESSURE_TOLERANCE = 0.1  # ±0.1 bar
            
            # Verifica temperatura
            if cycle1['temperatura'] and cycle2['temperatura']:
                temp_diff = abs(cycle1['temperatura'] - cycle2['temperatura'])
                if temp_diff > TEMP_TOLERANCE:
                    return False
            
            # Verifica tempo (tolleranza percentuale)
            if cycle1['tempo_minuti'] and cycle2['tempo_minuti']:
                time1, time2 = cycle1['tempo_minuti'], cycle2['tempo_minuti']
                max_time = max(time1, time2)
                time_diff_pct = abs(time1 - time2) / max_time
                if time_diff_pct > TIME_TOLERANCE_PCT:
                    return False
            
            # Verifica pressione
            if cycle1['pressione'] and cycle2['pressione']:
                pressure_diff = abs(cycle1['pressione'] - cycle2['pressione'])
                if pressure_diff > PRESSURE_TOLERANCE:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore nella verifica compatibilità cicli: {str(e)}")
            return False

    def perform_nesting_2d(
        self, 
        odl_data: List[Dict[str, Any]], 
        autoclave_data: Dict[str, Any], 
        parameters: NestingParameters
    ) -> NestingResult:
        """
        🚀 AEROSPACE GRADE: Esegue nesting 2D utilizzando l'algoritmo ottimizzato aerospace
        Sostituisce completamente il vecchio algoritmo per raggiungere efficienze 80-90%
        """
        try:
            # ✅ FIX CRITICO: Dimensioni del piano autoclave CORRETTE
            plane_width = autoclave_data['lunghezza']          # Larghezza = lunghezza autoclave
            plane_height = autoclave_data['larghezza_piano']   # Altezza = larghezza piano
            max_weight = autoclave_data['max_load_kg']
            max_lines = parameters.vacuum_lines_capacity
            
            self.logger.info(f"🚀 AEROSPACE NESTING: Piano {plane_width}x{plane_height}mm, peso max: {max_weight}kg")
            
            if not odl_data:
                return NestingResult(
                    positioned_tools=[],
                    excluded_odls=[],
                    total_weight=0,
                    used_area=0,
                    total_area=plane_width * plane_height,
                    area_pct=0,
                    lines_used=0,
                    efficiency=0,
                    success=True,
                    algorithm_status="Nessun ODL da posizionare"
                )
            
            # 🚀 AEROSPACE: Conversione ai parametri ottimizzati
            aerospace_params = AerospaceParameters(
                padding_mm=0.5,  # Ultra-aggressive 0.5mm vs old 1mm
                min_distance_mm=0.5,  # Ultra-aggressive 0.5mm vs old 1mm
                vacuum_lines_capacity=max_lines,
                use_fallback=True,
                allow_heuristic=True,
                timeout_override=None,
                heavy_piece_threshold_kg=50.0,
                # 🚀 AEROSPACE OPTIMIZATION PARAMETERS:
                use_multithread=True,  # 8 CP-SAT workers vs single-thread
                num_search_workers=8,  # Multi-threading for better convergence
                use_grasp_heuristic=True,  # GRASP global optimization
                compactness_weight=0.10,  # 10% compactness weight
                balance_weight=0.05,  # 5% balance weight
                area_weight=0.85,  # 85% area weight (vs 80% old)
                max_iterations_grasp=5  # GRASP iterations
            )
            
            # 🚀 AEROSPACE: Conversione tool data
            aerospace_tools = []
            for odl in odl_data:
                tool = ToolInfo(
                    odl_id=odl['odl_id'],
                    width=float(odl['tool_width']),
                    height=float(odl['tool_height']),
                    weight=float(odl['tool_weight']),
                    lines_needed=odl.get('lines_needed', 1),
                    ciclo_cura_id=odl.get('ciclo_cura_id'),
                    priority=1
                )
                aerospace_tools.append(tool)
            
            # 🚀 AEROSPACE: Conversione autoclave data
            aerospace_autoclave = AutoclaveInfo(
                id=autoclave_data['id'],
                width=float(plane_width),
                height=float(plane_height),
                max_weight=float(max_weight),
                max_lines=max_lines
            )
            
            # 🚀 AEROSPACE: Inizializza il solver ottimizzato
            aerospace_solver = NestingModel(aerospace_params)
            
            self.logger.info(f"🚀 AEROSPACE: Avvio solver ottimizzato con {len(aerospace_tools)} tools")
            self.logger.info(f"🚀 PARAMETRI: padding=0.5mm, multithread=8, GRASP=ON, timeout=min(300s, 10s×{len(aerospace_tools)})")
            
            # 🚀 AEROSPACE: Risoluzione con algoritmo ottimizzato
            aerospace_solution = aerospace_solver.solve(aerospace_tools, aerospace_autoclave)
            
            # 🚀 AEROSPACE: Conversione risultati al formato legacy
            positioned_tools = []
            for layout in aerospace_solution.layouts:
                tool_pos = ToolPosition(
                    odl_id=layout.odl_id,
                    x=layout.x,
                    y=layout.y,
                    width=layout.width,
                    height=layout.height,
                    peso=layout.weight,
                    rotated=layout.rotated,
                    lines_used=layout.lines_used
                )
                positioned_tools.append(tool_pos)
            
            # 🚀 AEROSPACE: Conversione metriche
            total_area = plane_width * plane_height
            used_area = sum(tool.width * tool.height for tool in positioned_tools)
            efficiency = aerospace_solution.metrics.efficiency_score
            
            # 🚀 AEROSPACE: Log risultati con comparazione
            self.logger.info(f"🚀 AEROSPACE RISULTATO: {len(positioned_tools)} ODL posizionati")
            self.logger.info(f"🚀 EFFICIENZA: {efficiency:.1f}% (Target aerospace: 80-90%)")
            self.logger.info(f"🚀 AREA: {aerospace_solution.metrics.area_pct:.1f}% utilizzata")
            self.logger.info(f"🚀 VACUUM: {aerospace_solution.metrics.vacuum_util_pct:.1f}% linee usate")
            self.logger.info(f"🚀 ROTAZIONI: {aerospace_solution.metrics.rotation_used}")
            self.logger.info(f"🚀 ALGORITMO: {aerospace_solution.algorithm_status}")
            self.logger.info(f"🚀 TEMPO: {aerospace_solution.metrics.time_solver_ms:.0f}ms")
            
            if aerospace_solution.metrics.fallback_used:
                self.logger.warning("🚀 FALLBACK: Utilizzato algoritmo greedy avanzato")
            
            if aerospace_solution.metrics.heuristic_iters > 0:
                self.logger.info(f"🚀 HEURISTIC: {aerospace_solution.metrics.heuristic_iters} iterazioni di miglioramento")
            
            # ⚠️ WARNING se efficienza è sotto standard aerospace
            if efficiency < 60.0:
                self.logger.warning(f"⚠️ EFFICIENZA SOTTO STANDARD: {efficiency:.1f}% < 60% (verificare dati input)")
            elif efficiency < 80.0:
                self.logger.warning(f"⚠️ EFFICIENZA MIGLIORABILE: {efficiency:.1f}% < 80% target aerospace")
            else:
                self.logger.info(f"✅ EFFICIENZA AEROSPACE: {efficiency:.1f}% >= 80% target")
            
            return NestingResult(
                positioned_tools=positioned_tools,
                excluded_odls=aerospace_solution.excluded_odls,
                total_weight=aerospace_solution.metrics.total_weight,
                used_area=used_area,
                total_area=total_area,
                area_pct=aerospace_solution.metrics.area_pct,
                lines_used=aerospace_solution.metrics.lines_used,
                efficiency=efficiency,
                success=aerospace_solution.success,
                algorithm_status=f"AEROSPACE_{aerospace_solution.algorithm_status}"
            )
            
        except Exception as e:
            self.logger.error(f"🚀 AEROSPACE ERROR: {str(e)}")
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
                    area_pct=0,
                    lines_used=0,
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
    
    def _validate_odl_list(self, db: Session, odl_ids: List[int]) -> List[int]:
        """Valida la lista di ODL e restituisce solo quelli validi"""
        try:
            valid_odls = db.query(ODL).filter(
                ODL.id.in_(odl_ids),
                ODL.status == 'Attesa Cura'
            ).all()
            
            valid_ids = [odl.id for odl in valid_odls]
            logger.info(f"ODL validati: {len(valid_ids)}/{len(odl_ids)} - IDs: {valid_ids}")
            return valid_ids
            
        except Exception as e:
            logger.error(f"Errore validazione ODL: {str(e)}")
            return []
    
    def _validate_autoclave_list(self, db: Session, autoclave_ids: List[int]) -> List[int]:
        """Valida la lista di autoclavi e restituisce solo quelle valide"""
        try:
            valid_autoclavi = db.query(Autoclave).filter(
                Autoclave.id.in_(autoclave_ids),
                Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
            ).all()
            
            valid_ids = [autoclave.id for autoclave in valid_autoclavi]
            logger.info(f"Autoclavi validate: {len(valid_ids)}/{len(autoclave_ids)}")
            return valid_ids
            
        except Exception as e:
            logger.error(f"Errore validazione autoclavi: {str(e)}")
            return []
    
    def _create_robust_batch(
        self, 
        db: Session, 
        nesting_result: NestingResult, 
        autoclave_id: int,
        parameters: NestingParameters
    ) -> Optional[str]:
        """Crea un batch robusto nel database"""
        try:
            autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            if not autoclave:
                logger.error(f"Autoclave {autoclave_id} non trovata")
                return None
            
            # Genera nome univoco per il batch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_name = f"Robust Nesting {autoclave.nome} {timestamp}"
            
            # Prepara posizioni tool per JSON
            tool_positions = []
            for tool in nesting_result.positioned_tools:
                tool_positions.append({
                    'odl_id': tool.odl_id,
                    'x': float(tool.x),
                    'y': float(tool.y),
                    'width': float(tool.width),
                    'height': float(tool.height),
                    'peso': float(tool.peso),
                    'rotated': bool(tool.rotated),
                    'lines_used': int(tool.lines_used)
                })
            
            configurazione_json = {
                # ✅ DIMENSIONI CORRETTE (fix precedente)
                'canvas_width': float(autoclave.lunghezza or 3000),        # Width = lunghezza autoclave
                'canvas_height': float(autoclave.larghezza_piano or 2000), # Height = larghezza piano
                'tool_positions': tool_positions,
                'plane_assignments': {str(tool.odl_id): 1 for tool in nesting_result.positioned_tools},
                'autoclave_mm': [
                    float(autoclave.lunghezza or 3000),        # Larghezza autoclave in mm
                    float(autoclave.larghezza_piano or 2000)   # Altezza autoclave in mm
                ],
                'bounding_px': [
                    800,  # Larghezza container canvas in px (default)
                    600   # Altezza container canvas in px (default)
                ]
            }
            
            # Parametri completi
            parametri = {
                'padding_mm': float(parameters.padding_mm),
                'min_distance_mm': float(parameters.min_distance_mm),
                'use_fallback': bool(parameters.use_fallback),
                'allow_heuristic': bool(parameters.allow_heuristic),
                'timeout_override': parameters.timeout_override,
                'accorpamento_odl': False,
                'use_secondary_plane': False,
                'max_weight_per_plane_kg': None
            }
            
            # Crea batch nel database con i campi corretti
            new_batch = BatchNesting(
                nome=batch_name,
                autoclave_id=autoclave_id,
                odl_ids=[tool.odl_id for tool in nesting_result.positioned_tools],
                configurazione_json=configurazione_json,
                parametri=parametri,
                numero_nesting=len(nesting_result.positioned_tools),
                peso_totale_kg=int(nesting_result.total_weight),
                area_totale_utilizzata=int(nesting_result.used_area / 100),  # Converte da mm² a cm²
                valvole_totali_utilizzate=int(nesting_result.lines_used),
                efficiency=float(nesting_result.efficiency),
                stato=StatoBatchNestingEnum.SOSPESO.value,  # Usa il valore string dell'enum
                creato_da_utente='SYSTEM_ROBUST',
                creato_da_ruolo='SYSTEM'
            )
            
            db.add(new_batch)
            db.commit()
            db.refresh(new_batch)
            
            logger.info(f"✅ Batch robusto creato: {new_batch.id}")
            return str(new_batch.id)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore creazione batch robusto: {str(e)}")
            return None
    
    def _apply_fallback_strategy(
        self, 
        db: Session, 
        validation_result: Dict[str, Any], 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Applica strategie di fallback per problemi critici"""
        try:
            for issue in validation_result.get('issues', []):
                issue_type = issue['type']
                if issue_type in self.fallback_strategies:
                    handler = self.fallback_strategies[issue_type]
                    result = handler(db, issue, result)
                    break
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'applicazione strategia fallback: {str(e)}")
            result.update({
                'message': f'Errore strategia fallback: {str(e)}',
                'algorithm_status': 'FALLBACK_ERROR'
            })
            return result
    
    def _handle_no_odl(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il caso di nessun ODL disponibile"""
        result.update({
            'message': 'Nessun ODL in attesa di cura disponibile per il nesting',
            'algorithm_status': 'NO_ODL_AVAILABLE'
        })
        return result
    
    def _handle_no_autoclave(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il caso di nessuna autoclave disponibile"""
        result.update({
            'message': 'Nessuna autoclave disponibile per il nesting',
            'algorithm_status': 'NO_AUTOCLAVE_AVAILABLE'
        })
        return result
    
    def _handle_algorithm_failure(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il fallimento dell'algoritmo principale"""
        result.update({
            'message': 'Algoritmo di nesting principale fallito - usare parametri meno restrittivi',
            'algorithm_status': 'ALGORITHM_FAILED'
        })
        return result
    
    def _handle_positioning_failure(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il fallimento del posizionamento tool"""
        result.update({
            'message': 'Impossibile posizionare tool nell\'autoclave - verificare dimensioni',
            'algorithm_status': 'POSITIONING_FAILED'
        })
        return result
    
    def _handle_data_corruption(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce la corruzione dei dati"""
        result.update({
            'message': 'Dati ODL o autoclave corrotti - verificare integrità database',
            'algorithm_status': 'DATA_CORRUPTION'
        })
        return result 
