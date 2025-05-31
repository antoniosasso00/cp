"""
Service per la gestione del layout visuale del nesting con orientamento automatico.
Gestisce il calcolo delle posizioni dei tool, l'orientamento ottimale e le quote dimensionali.
"""

import logging
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from models.nesting_result import NestingResult
from models.odl import ODL
from models.tool import Tool
from models.autoclave import Autoclave
from schemas.nesting import (
    NestingLayoutData, MultiNestingLayoutData, ToolPosition, 
    OrientationCalculationRequest, OrientationCalculationResponse,
    ODLLayoutInfo, AutoclaveLayoutInfo, ToolDetailInfo, ParteDetailInfo
)
import math

logger = logging.getLogger(__name__)

class NestingLayoutService:
    """Service per la gestione del layout visuale del nesting"""
    
    @staticmethod
    def calculate_optimal_orientation(
        tool_length: float, 
        tool_width: float, 
        autoclave_length: float, 
        autoclave_width: float
    ) -> Dict:
        """
        Calcola l'orientamento ottimale per un tool in un'autoclave.
        
        Args:
            tool_length: Lunghezza del tool in mm
            tool_width: Larghezza del tool in mm  
            autoclave_length: Lunghezza dell'autoclave in mm
            autoclave_width: Larghezza dell'autoclave in mm
            
        Returns:
            Dict con informazioni sull'orientamento ottimale
        """
        try:
            # Calcola efficienza per orientamento normale
            normal_efficiency = min(
                tool_length / autoclave_length,
                tool_width / autoclave_width
            )
            
            # Calcola efficienza per orientamento ruotato
            rotated_efficiency = min(
                tool_width / autoclave_length,
                tool_length / autoclave_width
            )
            
            # Determina se ruotare
            should_rotate = rotated_efficiency > normal_efficiency
            improvement = rotated_efficiency - normal_efficiency if should_rotate else 0
            
            return {
                "should_rotate": should_rotate,
                "normal_efficiency": round(normal_efficiency, 4),
                "rotated_efficiency": round(rotated_efficiency, 4),
                "improvement_percentage": round(improvement * 100, 2),
                "recommended_orientation": "ruotato" if should_rotate else "normale"
            }
            
        except Exception as e:
            logger.error(f"Errore nel calcolo orientamento: {e}")
            return {
                "should_rotate": False,
                "normal_efficiency": 0.0,
                "rotated_efficiency": 0.0,
                "improvement_percentage": 0.0,
                "recommended_orientation": "normale"
            }
    
    @staticmethod
    def calculate_tool_positions(
        nesting: NestingResult,
        padding_mm: float = 10.0,
        borda_mm: float = 20.0,
        rotazione_abilitata: bool = True
    ) -> List[ToolPosition]:
        """
        Calcola le posizioni ottimali dei tool nel nesting.
        Priorità: usa posizioni salvate -> posizioni da algoritmo -> layout automatico fallback
        
        Args:
            nesting: Risultato del nesting
            padding_mm: Spaziatura tra tool in mm
            borda_mm: Bordo dall'autoclave in mm
            rotazione_abilitata: Se abilitare la rotazione automatica
            
        Returns:
            Lista delle posizioni calcolate
        """
        try:
            positions = []
            
            # PRIORITÀ 1: Se abbiamo posizioni già salvate nel database, usale
            if nesting.posizioni_tool:
                logger.debug(f"Caricamento posizioni salvate per nesting {nesting.id}")
                for pos_data in nesting.posizioni_tool:
                    if isinstance(pos_data, dict):
                        # Valida i campi richiesti
                        required_fields = ['odl_id', 'x', 'y', 'width', 'height']
                        if all(field in pos_data for field in required_fields):
                            positions.append(ToolPosition(**pos_data))
                        else:
                            logger.warning(f"Posizione tool incompleta nel nesting {nesting.id}: {pos_data}")
                
                if positions:
                    logger.info(f"Caricate {len(positions)} posizioni salvate per nesting {nesting.id}")
                    return positions
                else:
                    logger.warning(f"Posizioni salvate non valide per nesting {nesting.id}, procedo con calcolo automatico")
            
            # PRIORITÀ 2: Se il nesting ha metadati dell'algoritmo, usa quelli
            if hasattr(nesting, 'note') and nesting.note:
                try:
                    import json
                    # Cerca se nelle note ci sono i dati dell'algoritmo
                    note_lines = nesting.note.split('\n')
                    for line in note_lines:
                        if line.strip().startswith('{') and 'tool_positions' in line:
                            algorithm_data = json.loads(line.strip())
                            if 'tool_positions' in algorithm_data:
                                logger.debug(f"Caricamento posizioni da algoritmo per nesting {nesting.id}")
                                for pos_data in algorithm_data['tool_positions']:
                                    positions.append(ToolPosition(**pos_data))
                                
                                if positions:
                                    logger.info(f"Caricate {len(positions)} posizioni da algoritmo per nesting {nesting.id}")
                                    return positions
                except (json.JSONDecodeError, KeyError):
                    logger.debug(f"Metadati algoritmo non trovati o non validi per nesting {nesting.id}")
            
            # PRIORITÀ 3: Layout automatico fallback
            logger.debug(f"Calcolo layout automatico fallback per nesting {nesting.id}")
            autoclave = nesting.autoclave
            if not autoclave:
                logger.error(f"Autoclave non trovata per nesting {nesting.id}")
                return positions
                
            # Area disponibile considerando i bordi
            available_width = autoclave.lunghezza - (2 * borda_mm)
            available_height = autoclave.larghezza_piano - (2 * borda_mm)
            
            if available_width <= 0 or available_height <= 0:
                logger.error(f"Dimensioni disponibili non valide per autoclave {autoclave.id}: {available_width}x{available_height}mm")
                return positions
            
            # Layout automatico con orientamento ottimale
            current_x = borda_mm
            current_y = borda_mm
            row_height = 0
            
            logger.debug(f"Area disponibile: {available_width}x{available_height}mm con bordo {borda_mm}mm")
            
            for odl in nesting.odl_list:
                if not odl.tool:
                    logger.warning(f"ODL {odl.id} non ha tool associato, saltato")
                    continue
                    
                tool = odl.tool
                
                # Usa dimensioni reali del tool
                base_width = tool.lunghezza_piano or 100.0  # Default se non specificato
                base_height = tool.larghezza_piano or 100.0  # Default se non specificato
                
                # Calcola orientamento ottimale se abilitato
                orientation_info = NestingLayoutService.calculate_optimal_orientation(
                    base_width,
                    base_height,
                    autoclave.lunghezza,
                    autoclave.larghezza_piano
                ) if rotazione_abilitata else {"should_rotate": False}
                
                is_rotated = orientation_info.get("should_rotate", False)
                
                # Dimensioni effettive considerando rotazione
                tool_width = base_height if is_rotated else base_width
                tool_height = base_width if is_rotated else base_height
                
                # Verifica se c'è spazio nella riga corrente
                if current_x + tool_width > autoclave.lunghezza - borda_mm and current_x > borda_mm:
                    # Vai alla riga successiva
                    current_x = borda_mm
                    current_y += row_height + padding_mm
                    row_height = 0
                    logger.debug(f"Tool ODL {odl.id}: nuova riga, posizione ({current_x}, {current_y})")
                
                # Verifica se c'è spazio verticale
                if current_y + tool_height > autoclave.larghezza_piano - borda_mm:
                    # Non c'è più spazio, ferma il posizionamento
                    logger.warning(f"Spazio verticale insufficiente per ODL {odl.id} nel nesting {nesting.id} "
                                 f"(richiesto: {current_y + tool_height}mm, disponibile: {autoclave.larghezza_piano - borda_mm}mm)")
                    break
                
                # Crea posizione
                position = ToolPosition(
                    odl_id=odl.id,
                    x=current_x,
                    y=current_y,
                    width=tool_width,
                    height=tool_height,
                    rotated=is_rotated,
                    piano=1  # Default piano 1 per layout automatico
                )
                
                positions.append(position)
                logger.debug(f"Tool ODL {odl.id} posizionato a ({current_x:.1f}, {current_y:.1f}) - {tool_width:.1f}x{tool_height:.1f}mm" +
                           (" (ruotato)" if is_rotated else ""))
                
                # Aggiorna posizione per il prossimo tool
                current_x += tool_width + padding_mm
                row_height = max(row_height, tool_height)
            
            logger.info(f"Layout automatico completato per nesting {nesting.id}: {len(positions)} tool posizionati")
            return positions
            
        except Exception as e:
            logger.error(f"Errore nel calcolo posizioni tool per nesting {nesting.id}: {e}")
            return []
    
    @staticmethod
    def convert_nesting_to_layout_data(
        nesting: NestingResult,
        padding_mm: float = 10.0,
        borda_mm: float = 20.0,
        rotazione_abilitata: bool = True
    ) -> NestingLayoutData:
        """
        Converte un NestingResult in NestingLayoutData per il frontend.
        
        Args:
            nesting: Risultato del nesting
            padding_mm: Spaziatura tra tool
            borda_mm: Bordo dall'autoclave
            rotazione_abilitata: Se abilitare rotazione
            
        Returns:
            Dati del nesting per il layout visuale
        """
        try:
            # Converti autoclave
            autoclave_data = AutoclaveLayoutInfo(
                id=nesting.autoclave.id,
                nome=nesting.autoclave.nome,
                codice=nesting.autoclave.codice,
                lunghezza=nesting.autoclave.lunghezza,
                larghezza_piano=nesting.autoclave.larghezza_piano,
                temperatura_max=nesting.autoclave.temperatura_max,
                num_linee_vuoto=nesting.autoclave.num_linee_vuoto
            )
            
            # Converti ODL
            odl_data = []
            logger.info(f"🔧 DEBUG: Convertendo {len(nesting.odl_list)} ODL per nesting {nesting.id}")
            
            for i, odl in enumerate(nesting.odl_list):
                logger.info(f"🔧 DEBUG: ODL {i+1}: ID={odl.id}, tool={odl.tool is not None}, parte={odl.parte is not None}")
                
                if odl.tool and odl.parte:
                    logger.info(f"🔧 DEBUG: Processando ODL {odl.id} - tool: {odl.tool.part_number_tool}, parte: {odl.parte.part_number}")
                    
                    # Dati tool
                    tool_data = ToolDetailInfo(
                        id=odl.tool.id,
                        part_number_tool=odl.tool.part_number_tool,
                        descrizione=odl.tool.descrizione,
                        lunghezza_piano=odl.tool.lunghezza_piano,
                        larghezza_piano=odl.tool.larghezza_piano,
                        peso=getattr(odl.tool, 'peso', None),
                        materiale=getattr(odl.tool, 'materiale', None),
                        orientamento_preferito=getattr(odl.tool, 'orientamento_preferito', None)
                    )
                    
                    # Dati parte
                    parte_data = ParteDetailInfo(
                        id=odl.parte.id,
                        part_number=odl.parte.part_number,
                        descrizione_breve=odl.parte.descrizione_breve,
                        num_valvole_richieste=odl.parte.num_valvole_richieste,
                        area_cm2=getattr(odl.parte, 'area_cm2', None)
                    )
                    
                    # ODL completo
                    odl_layout = ODLLayoutInfo(
                        id=odl.id,
                        priorita=odl.priorita,
                        parte=parte_data,
                        tool=tool_data
                    )
                    
                    odl_data.append(odl_layout)
                    logger.info(f"✅ DEBUG: ODL {odl.id} aggiunto a odl_data")
                else:
                    logger.warning(f"⚠️ DEBUG: ODL {odl.id} saltato - tool: {odl.tool is not None}, parte: {odl.parte is not None}")
            
            logger.info(f"🔧 DEBUG: Totale ODL processati: {len(odl_data)}")
            
            # Calcola posizioni tool
            posizioni_tool = NestingLayoutService.calculate_tool_positions(
                nesting, padding_mm, borda_mm, rotazione_abilitata
            )
            
            # Estrai nome ciclo di cura dalle note
            ciclo_cura_nome = None
            if nesting.note:
                # Cerca pattern "Ciclo: Nome Ciclo" nelle note
                import re
                match = re.search(r'Ciclo:\s*([^,\n]+)', nesting.note)
                if match:
                    ciclo_cura_nome = match.group(1).strip()
            
            # Crea oggetto layout
            layout_data = NestingLayoutData(
                id=nesting.id,
                autoclave=autoclave_data,
                odl_list=odl_data,
                posizioni_tool=posizioni_tool,
                area_utilizzata=nesting.area_utilizzata or 0.0,
                area_totale=nesting.area_totale or 0.0,
                valvole_utilizzate=nesting.valvole_utilizzate or 0,
                valvole_totali=nesting.valvole_totali or 0,
                stato=nesting.stato.value if hasattr(nesting.stato, 'value') else str(nesting.stato),
                ciclo_cura_nome=ciclo_cura_nome,
                created_at=nesting.created_at,
                note=nesting.note,
                padding_mm=padding_mm,
                borda_mm=borda_mm,
                rotazione_abilitata=rotazione_abilitata
            )
            
            return layout_data
            
        except Exception as e:
            logger.error(f"Errore nella conversione nesting {nesting.id} a layout data: {e}")
            raise
    
    @staticmethod
    def get_nesting_layout_data(db: Session, nesting_id: int) -> Optional[NestingLayoutData]:
        """
        Recupera i dati di layout per un nesting specifico.
        
        Args:
            db: Sessione database
            nesting_id: ID del nesting
            
        Returns:
            Dati del layout o None se non trovato
        """
        try:
            nesting = db.query(NestingResult).options(
                joinedload(NestingResult.autoclave),
                joinedload(NestingResult.odl_list).joinedload(ODL.tool),
                joinedload(NestingResult.odl_list).joinedload(ODL.parte)
            ).filter(NestingResult.id == nesting_id).first()
            
            if not nesting:
                return None
                
            return NestingLayoutService.convert_nesting_to_layout_data(nesting)
            
        except Exception as e:
            logger.error(f"Errore nel recupero layout data per nesting {nesting_id}: {e}")
            return None
    
    @staticmethod
    def get_multi_nesting_layout_data(
        db: Session, 
        limit: Optional[int] = None,
        stato_filtro: Optional[str] = None
    ) -> MultiNestingLayoutData:
        """
        Recupera i dati di layout per più nesting.
        
        Args:
            db: Sessione database
            limit: Limite numero nesting
            stato_filtro: Filtro per stato
            
        Returns:
            Dati multi-nesting per il layout
        """
        try:
            # Query base
            query = db.query(NestingResult).options(
                joinedload(NestingResult.autoclave),
                joinedload(NestingResult.odl_list).joinedload(ODL.tool),
                joinedload(NestingResult.odl_list).joinedload(ODL.parte)
            )
            
            # Applica filtri
            if stato_filtro:
                query = query.filter(NestingResult.stato == stato_filtro)
            
            # Ordina per data creazione (più recenti prima)
            query = query.order_by(NestingResult.created_at.desc())
            
            # Applica limite
            if limit:
                query = query.limit(limit)
            
            nesting_results = query.all()
            
            # Converti a layout data
            nesting_layout_list = []
            for nesting in nesting_results:
                try:
                    layout_data = NestingLayoutService.convert_nesting_to_layout_data(nesting)
                    nesting_layout_list.append(layout_data)
                except Exception as e:
                    logger.error(f"Errore conversione nesting {nesting.id}: {e}")
                    continue
            
            # Calcola statistiche globali
            statistiche = NestingLayoutService.calculate_global_statistics(nesting_layout_list)
            
            return MultiNestingLayoutData(
                nesting_list=nesting_layout_list,
                statistiche_globali=statistiche
            )
            
        except Exception as e:
            logger.error(f"Errore nel recupero multi-nesting layout data: {e}")
            return MultiNestingLayoutData(nesting_list=[], statistiche_globali={})
    
    @staticmethod
    def calculate_global_statistics(nesting_list: List[NestingLayoutData]) -> Dict:
        """
        Calcola statistiche globali per una lista di nesting.
        
        Args:
            nesting_list: Lista dei nesting
            
        Returns:
            Dizionario con statistiche aggregate
        """
        try:
            if not nesting_list:
                return {}
            
            total_nesting = len(nesting_list)
            total_odl = sum(len(n.odl_list) for n in nesting_list)
            total_valvole = sum(n.valvole_utilizzate for n in nesting_list)
            
            # Calcola utilizzo medio area
            area_utilizations = []
            for n in nesting_list:
                if n.area_totale > 0:
                    utilization = (n.area_utilizzata / n.area_totale) * 100
                    area_utilizations.append(utilization)
            
            avg_area_utilization = sum(area_utilizations) / len(area_utilizations) if area_utilizations else 0
            
            # Conta nesting per stato
            nesting_by_status = {}
            for n in nesting_list:
                stato = n.stato
                nesting_by_status[stato] = nesting_by_status.get(stato, 0) + 1
            
            # Conta tool ruotati
            total_tools_rotated = 0
            for n in nesting_list:
                total_tools_rotated += sum(1 for pos in n.posizioni_tool if pos.rotated)
            
            return {
                "total_nesting": total_nesting,
                "total_odl": total_odl,
                "total_valvole": total_valvole,
                "avg_area_utilization": round(avg_area_utilization, 1),
                "nesting_by_status": nesting_by_status,
                "total_tools_rotated": total_tools_rotated,
                "autoclavi_utilizzate": len(set(n.autoclave.id for n in nesting_list))
            }
            
        except Exception as e:
            logger.error(f"Errore nel calcolo statistiche globali: {e}")
            return {} 