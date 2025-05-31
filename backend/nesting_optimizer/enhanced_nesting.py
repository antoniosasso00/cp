"""
Modulo per l'ottimizzazione avanzata del nesting degli ODL nelle autoclavi.

Implementa un algoritmo di nesting migliorato che considera:
- Compatibilità dei cicli di cura
- Dimensioni reali dei tool con rotazioni
- Valvole richieste vs disponibili
- Numero di linee del vuoto dell'autoclave
- Efficienza di utilizzo dello spazio
- Posizionamento geometrico preciso con coordinate x,y
- Gestione completa degli ODL esclusi con motivi dettagliati
"""

from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
import math
from dataclasses import dataclass
from enum import Enum

# Importazioni dei modelli
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.nesting_result import NestingResult
from models.tool import Tool
from models.parte import Parte
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura

# Configurazione logging
logger = logging.getLogger(__name__)


class ExclusionReason(Enum):
    """Motivi di esclusione degli ODL dal nesting"""
    CICLO_CURA_INCOMPATIBILE = "Ciclo di cura incompatibile"
    PESO_ECCESSIVO = "Peso eccessivo per l'autoclave"
    DIMENSIONI_ECCESSIVE = "Dimensioni tool eccessive per l'autoclave"
    SPAZIO_GEOMETRICO_INSUFFICIENTE = "Spazio geometrico insufficiente"
    VALVOLE_INSUFFICIENTI = "Valvole insufficienti nell'autoclave"
    TOOL_NON_TROVATO = "Tool non trovato o non valido"
    PARTE_NON_TROVATA = "Parte non trovata o non valida"
    CICLO_CURA_NON_TROVATO = "Ciclo di cura non trovato"
    EFFICIENZA_INSUFFICIENTE = "Efficienza complessiva insufficiente"


@dataclass
class ToolDimensions:
    """Dimensioni di un tool con informazioni aggiuntive"""
    width: float  # Larghezza in mm
    height: float  # Altezza in mm
    weight: float  # Peso in kg
    valvole_richieste: int  # Numero di valvole richieste
    can_rotate: bool = True  # Se il tool può essere ruotato
    
    @property
    def area_mm2(self) -> float:
        """Area in mm²"""
        return self.width * self.height
    
    @property
    def area_cm2(self) -> float:
        """Area in cm²"""
        return self.area_mm2 / 100


@dataclass
class ToolPlacement:
    """Posizionamento di un tool nel layout"""
    odl_id: int
    x: float  # Posizione x in mm
    y: float  # Posizione y in mm
    width: float  # Larghezza effettiva in mm
    height: float  # Altezza effettiva in mm
    rotated: bool = False  # Se il tool è ruotato
    piano: int = 1  # Piano dell'autoclave (1 o 2)
    
    def to_dict(self) -> Dict:
        """Converte in dizionario per il database"""
        return {
            'odl_id': self.odl_id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotated': self.rotated,
            'piano': self.piano
        }
    
    def overlaps_with(self, other: 'ToolPlacement') -> bool:
        """Verifica se questo tool si sovrappone con un altro"""
        if self.piano != other.piano:
            return False
        
        return not (
            self.x + self.width <= other.x or
            other.x + other.width <= self.x or
            self.y + self.height <= other.y or
            other.y + other.height <= self.y
        )
    
    @property
    def area_mm2(self) -> float:
        """Area occupata in mm²"""
        return self.width * self.height


@dataclass
class AutoclaveConstraints:
    """Vincoli di un'autoclave"""
    id: int
    nome: str
    lunghezza: float  # Lunghezza interna in mm
    larghezza_piano: float  # Larghezza piano in mm
    max_load_kg: float  # Carico massimo in kg
    num_linee_vuoto: int  # Numero di linee vuoto disponibili
    use_secondary_plane: bool = False  # Se può usare piano secondario
    superficie_piano_2_max: Optional[float] = None  # Superficie max piano 2 in cm²
    
    @property
    def area_piano_1_mm2(self) -> float:
        """Area piano 1 in mm²"""
        return self.lunghezza * self.larghezza_piano
    
    @property
    def area_piano_2_mm2(self) -> float:
        """Area piano 2 in mm²"""
        if not self.use_secondary_plane or not self.superficie_piano_2_max:
            return 0.0
        return self.superficie_piano_2_max * 100  # Converti cm² in mm²
    
    @property
    def area_totale_mm2(self) -> float:
        """Area totale disponibile in mm²"""
        return self.area_piano_1_mm2 + self.area_piano_2_mm2


@dataclass
class NestingConstraints:
    """Vincoli per l'algoritmo di nesting"""
    distanza_minima_tool_mm: float = 20.0  # Distanza minima tra tool in mm
    padding_bordo_mm: float = 15.0  # Padding dal bordo autoclave in mm
    margine_sicurezza_peso_percent: float = 10.0  # Margine di sicurezza peso
    efficienza_minima_percent: float = 60.0  # Efficienza minima richiesta
    priorita_minima: int = 1  # Priorità minima ODL
    separa_cicli_cura: bool = True  # Se separare ODL con cicli diversi
    abilita_rotazioni: bool = True  # Se abilitare rotazioni automatiche
    
    @property
    def effective_area_reduction_factor(self) -> float:
        """Fattore di riduzione area per padding"""
        return 1.0 - (2 * self.padding_bordo_mm / 1000) ** 2  # Approssimazione


class EnhancedBinPacker:
    """
    Algoritmo di bin packing avanzato per il posizionamento ottimale dei tool
    """
    
    def __init__(self, autoclave: AutoclaveConstraints, constraints: NestingConstraints):
        self.autoclave = autoclave
        self.constraints = constraints
        self.placements: List[ToolPlacement] = []
        
        # Calcola dimensioni effettive considerando i bordi
        self.effective_width = autoclave.lunghezza - (2 * constraints.padding_bordo_mm)
        self.effective_height = autoclave.larghezza_piano - (2 * constraints.padding_bordo_mm)
        
        logger.info(f"Inizializzato BinPacker per {autoclave.nome}: "
                   f"area effettiva {self.effective_width:.0f}x{self.effective_height:.0f}mm")
    
    def can_place_at_position(self, x: float, y: float, width: float, height: float, 
                             odl_id: int, piano: int = 1) -> bool:
        """Verifica se un tool può essere posizionato in una specifica posizione"""
        # Verifica confini del contenitore
        if x + width > self.effective_width or y + height > self.effective_height:
            return False
        
        # Verifica sovrapposizioni con altri tool
        temp_placement = ToolPlacement(odl_id, x, y, width, height, piano=piano)
        for placement in self.placements:
            if temp_placement.overlaps_with(placement):
                return False
        
        return True
    
    def find_best_position_with_rotation(self, tool_dims: ToolDimensions, odl_id: int, 
                                       piano: int = 1) -> Optional[Tuple[float, float, bool]]:
        """
        Trova la migliore posizione per un tool considerando rotazioni
        """
        best_position = None
        best_waste = float('inf')
        
        # Dimensioni con padding
        width_with_padding = tool_dims.width + self.constraints.distanza_minima_tool_mm
        height_with_padding = tool_dims.height + self.constraints.distanza_minima_tool_mm
        
        # Prova posizionamento normale
        positions_to_try = [(width_with_padding, height_with_padding, False)]
        
        # Prova posizionamento ruotato se abilitato e dimensioni diverse
        if (self.constraints.abilita_rotazioni and tool_dims.can_rotate and 
            tool_dims.width != tool_dims.height):
            positions_to_try.append((height_with_padding, width_with_padding, True))
        
        # Grid search ottimizzato
        step = 10  # Step di 10mm per bilanciare precisione e performance
        
        for width, height, rotated in positions_to_try:
            for y in range(0, int(self.effective_height - height) + 1, step):
                for x in range(0, int(self.effective_width - width) + 1, step):
                    if self.can_place_at_position(x, y, width, height, odl_id, piano):
                        # Calcola "waste" - preferisce bottom-left
                        waste = y * self.effective_width + x
                        
                        if waste < best_waste:
                            best_waste = waste
                            best_position = (x, y, rotated)
        
        return best_position
    
    def place_tool(self, tool_dims: ToolDimensions, odl_id: int, piano: int = 1) -> bool:
        """Posiziona un tool nel contenitore"""
        result = self.find_best_position_with_rotation(tool_dims, odl_id, piano)
        
        if result:
            x, y, rotated = result
            
            # Dimensioni finali (con rotazione se applicabile)
            if rotated:
                final_width = tool_dims.height + self.constraints.distanza_minima_tool_mm
                final_height = tool_dims.width + self.constraints.distanza_minima_tool_mm
            else:
                final_width = tool_dims.width + self.constraints.distanza_minima_tool_mm
                final_height = tool_dims.height + self.constraints.distanza_minima_tool_mm
            
            placement = ToolPlacement(
                odl_id=odl_id,
                x=x + self.constraints.padding_bordo_mm,  # Aggiungi offset bordo
                y=y + self.constraints.padding_bordo_mm,  # Aggiungi offset bordo
                width=final_width - self.constraints.distanza_minima_tool_mm,  # Rimuovi padding interno
                height=final_height - self.constraints.distanza_minima_tool_mm,  # Rimuovi padding interno
                rotated=rotated,
                piano=piano
            )
            
            self.placements.append(placement)
            logger.debug(f"Tool ODL {odl_id} posizionato a ({placement.x:.1f}, {placement.y:.1f}) - "
                        f"{placement.width:.1f}x{placement.height:.1f}mm" + 
                        (" (ruotato)" if rotated else ""))
            return True
        
        return False
    
    def calculate_efficiency(self) -> float:
        """Calcola l'efficienza di utilizzo dello spazio"""
        if not self.placements:
            return 0.0
        
        total_tool_area = sum(p.area_mm2 for p in self.placements)
        container_area = self.effective_width * self.effective_height
        
        return (total_tool_area / container_area) * 100 if container_area > 0 else 0.0
    
    def get_placements(self) -> List[ToolPlacement]:
        """Restituisce tutti i posizionamenti"""
        return self.placements.copy()


class EnhancedNestingOptimizer:
    """
    Ottimizzatore di nesting avanzato con vincoli completi
    """
    
    def __init__(self, db: Session, constraints: Optional[NestingConstraints] = None):
        self.db = db
        self.constraints = constraints or NestingConstraints()
        logger.info(f"EnhancedNestingOptimizer inizializzato con vincoli: "
                   f"distanza_tool={self.constraints.distanza_minima_tool_mm}mm, "
                   f"padding_bordo={self.constraints.padding_bordo_mm}mm, "
                   f"efficienza_min={self.constraints.efficienza_minima_percent}%")
    
    def extract_tool_dimensions(self, odl: ODL) -> Optional[ToolDimensions]:
        """Estrae le dimensioni del tool da un ODL"""
        try:
            if not odl.tool:
                logger.warning(f"ODL {odl.id}: Tool non trovato")
                return None
            
            if not odl.parte:
                logger.warning(f"ODL {odl.id}: Parte non trovata")
                return None
            
            # Dimensioni del tool
            width = odl.tool.lunghezza_piano or 100.0
            height = odl.tool.larghezza_piano or 100.0
            weight = odl.tool.peso or 1.0
            
            # Valvole richieste dalla parte
            valvole_richieste = odl.parte.num_valvole_richieste or 1
            
            return ToolDimensions(
                width=width,
                height=height,
                weight=weight,
                valvole_richieste=valvole_richieste,
                can_rotate=True  # Assumiamo che tutti i tool possano essere ruotati
            )
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione dimensioni ODL {odl.id}: {str(e)}")
            return None
    
    def check_cycle_compatibility(self, odl_list: List[ODL]) -> Tuple[bool, Set[str]]:
        """
        Verifica la compatibilità dei cicli di cura
        
        Returns:
            Tuple[bool, Set[str]]: (compatibili, set dei cicli trovati)
        """
        cicli_trovati = set()
        
        for odl in odl_list:
            if odl.parte and odl.parte.ciclo_cura:
                cicli_trovati.add(odl.parte.ciclo_cura.nome)
            else:
                cicli_trovati.add("SCONOSCIUTO")
        
        # Se separa_cicli_cura è True, accetta solo un ciclo
        if self.constraints.separa_cicli_cura:
            compatible = len(cicli_trovati) <= 1
        else:
            # Altrimenti, per ora accettiamo tutti (logica da migliorare)
            compatible = True
        
        return compatible, cicli_trovati
    
    def optimize_nesting(self, odl_list: List[ODL], autoclave: Autoclave) -> Dict:
        """
        Ottimizza il nesting per una lista di ODL e un'autoclave
        """
        logger.info(f"Inizio ottimizzazione nesting per {len(odl_list)} ODL in autoclave {autoclave.nome}")
        
        # Converti autoclave in vincoli
        autoclave_constraints = AutoclaveConstraints(
            id=autoclave.id,
            nome=autoclave.nome,
            lunghezza=autoclave.lunghezza,
            larghezza_piano=autoclave.larghezza_piano,
            max_load_kg=autoclave.max_load_kg or 1000.0,
            num_linee_vuoto=autoclave.num_linee_vuoto or 0,
            use_secondary_plane=autoclave.use_secondary_plane or False,
            superficie_piano_2_max=autoclave.superficie_piano_2_max
        )
        
        # Inizializza bin packer
        bin_packer = EnhancedBinPacker(autoclave_constraints, self.constraints)
        
        # Liste per risultati
        selected_odl = []
        excluded_odl = []
        exclusion_reasons = []
        
        # Statistiche
        total_weight = 0.0
        total_valvole = 0
        
        # Calcola peso massimo con margine di sicurezza
        max_weight = autoclave_constraints.max_load_kg * (
            1 - self.constraints.margine_sicurezza_peso_percent / 100
        )
        
        # Ordina ODL per priorità decrescente e poi per area decrescente
        sorted_odl = sorted(odl_list, key=lambda x: (
            -x.priorita,
            -((self.extract_tool_dimensions(x).area_mm2) if self.extract_tool_dimensions(x) else 0)
        ))
        
        # Verifica compatibilità cicli di cura
        cycles_compatible, cycles_found = self.check_cycle_compatibility(sorted_odl)
        if not cycles_compatible:
            return {
                'success': False,
                'error': f'Cicli di cura incompatibili: {", ".join(cycles_found)}',
                'selected_odl': [],
                'excluded_odl': sorted_odl,
                'exclusion_reasons': [f"Cicli di cura incompatibili: {', '.join(cycles_found)}"] * len(sorted_odl)
            }
        
        # Prova a posizionare ogni ODL
        for odl in sorted_odl:
            # Estrai dimensioni tool
            tool_dims = self.extract_tool_dimensions(odl)
            if not tool_dims:
                excluded_odl.append(odl)
                exclusion_reasons.append(f"ODL {odl.id}: {ExclusionReason.TOOL_NON_TROVATO.value}")
                continue
            
            # Verifica vincolo di peso
            if total_weight + tool_dims.weight > max_weight:
                excluded_odl.append(odl)
                exclusion_reasons.append(
                    f"ODL {odl.id}: {ExclusionReason.PESO_ECCESSIVO.value} "
                    f"(richiesto: {tool_dims.weight:.1f}kg, disponibile: {max_weight - total_weight:.1f}kg)"
                )
                continue
            
            # Verifica vincolo valvole
            if total_valvole + tool_dims.valvole_richieste > autoclave_constraints.num_linee_vuoto:
                excluded_odl.append(odl)
                exclusion_reasons.append(
                    f"ODL {odl.id}: {ExclusionReason.VALVOLE_INSUFFICIENTI.value} "
                    f"(richieste: {tool_dims.valvole_richieste}, disponibili: {autoclave_constraints.num_linee_vuoto - total_valvole})"
                )
                continue
            
            # Verifica dimensioni massime
            if (tool_dims.width > autoclave_constraints.lunghezza or 
                tool_dims.height > autoclave_constraints.larghezza_piano):
                excluded_odl.append(odl)
                exclusion_reasons.append(
                    f"ODL {odl.id}: {ExclusionReason.DIMENSIONI_ECCESSIVE.value} "
                    f"(tool: {tool_dims.width:.0f}x{tool_dims.height:.0f}mm, "
                    f"autoclave: {autoclave_constraints.lunghezza:.0f}x{autoclave_constraints.larghezza_piano:.0f}mm)"
                )
                continue
            
            # Prova a posizionare il tool
            if bin_packer.place_tool(tool_dims, odl.id, piano=1):
                selected_odl.append(odl)
                total_weight += tool_dims.weight
                total_valvole += tool_dims.valvole_richieste
                logger.debug(f"ODL {odl.id} posizionato con successo")
            else:
                excluded_odl.append(odl)
                exclusion_reasons.append(
                    f"ODL {odl.id}: {ExclusionReason.SPAZIO_GEOMETRICO_INSUFFICIENTE.value} "
                    f"({tool_dims.width:.0f}x{tool_dims.height:.0f}mm)"
                )
                logger.debug(f"ODL {odl.id} escluso per mancanza di spazio geometrico")
        
        # Calcola efficienza
        geometric_efficiency = bin_packer.calculate_efficiency()
        
        # Verifica efficienza minima
        if geometric_efficiency < self.constraints.efficienza_minima_percent:
            logger.info(f"Efficienza {geometric_efficiency:.1f}% inferiore al minimo {self.constraints.efficienza_minima_percent}%")
            return {
                'success': False,
                'error': f'Efficienza insufficiente: {geometric_efficiency:.1f}% < {self.constraints.efficienza_minima_percent}%',
                'selected_odl': [],
                'excluded_odl': sorted_odl,
                'exclusion_reasons': [f"Efficienza complessiva insufficiente: {geometric_efficiency:.1f}%"] * len(sorted_odl)
            }
        
        # Ottieni posizioni finali
        tool_positions = bin_packer.get_placements()
        
        # Calcola statistiche finali
        total_tool_area_mm2 = sum(pos.area_mm2 for pos in tool_positions)
        autoclave_area_mm2 = autoclave_constraints.area_piano_1_mm2
        overall_efficiency = (total_tool_area_mm2 / autoclave_area_mm2) * 100 if autoclave_area_mm2 > 0 else 0
        
        logger.info(f"Nesting completato: {len(selected_odl)} ODL posizionati, "
                   f"efficienza geometrica {geometric_efficiency:.1f}%, "
                   f"efficienza totale {overall_efficiency:.1f}%, "
                   f"peso {total_weight:.1f}/{max_weight:.1f}kg, "
                   f"valvole {total_valvole}/{autoclave_constraints.num_linee_vuoto}")
        
        return {
            'success': True,
            'selected_odl': selected_odl,
            'excluded_odl': excluded_odl,
            'exclusion_reasons': exclusion_reasons,
            'tool_positions': [pos.to_dict() for pos in tool_positions],
            'total_weight': total_weight,
            'max_weight_with_margin': max_weight,
            'total_valvole': total_valvole,
            'max_valvole': autoclave_constraints.num_linee_vuoto,
            'geometric_efficiency': geometric_efficiency,
            'overall_efficiency': overall_efficiency,
            'autoclave_constraints': autoclave_constraints,
            'nesting_constraints': self.constraints,
            'cycles_found': list(cycles_found),
            'effective_dimensions': {
                'width': bin_packer.effective_width,
                'height': bin_packer.effective_height,
                'border_padding_mm': self.constraints.padding_bordo_mm,
                'tool_padding_mm': self.constraints.distanza_minima_tool_mm
            }
        }


def compute_enhanced_nesting(
    db: Session, 
    odl_ids: List[int], 
    autoclave_id: int, 
    constraints: Optional[Dict] = None
) -> Dict:
    """
    Funzione principale per il calcolo del nesting migliorato
    
    Args:
        db: Sessione del database
        odl_ids: Lista degli ID degli ODL
        autoclave_id: ID dell'autoclave
        constraints: Vincoli opzionali per l'algoritmo
        
    Returns:
        Dict: Risultato del nesting con posizioni precise e vincoli rispettati
    """
    try:
        # Crea vincoli se forniti
        nesting_constraints = NestingConstraints()
        if constraints:
            for key, value in constraints.items():
                if hasattr(nesting_constraints, key):
                    setattr(nesting_constraints, key, value)
        
        # Inizializza ottimizzatore
        optimizer = EnhancedNestingOptimizer(db, nesting_constraints)
        
        # Recupera ODL e autoclave
        odl_list = db.query(ODL).filter(ODL.id.in_(odl_ids)).all()
        autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
        
        if not autoclave:
            return {
                'success': False,
                'error': 'Autoclave non trovata',
                'selected_odl': [],
                'excluded_odl': [],
                'exclusion_reasons': []
            }
        
        if not odl_list:
            return {
                'success': False,
                'error': 'Nessun ODL trovato',
                'selected_odl': [],
                'excluded_odl': [],
                'exclusion_reasons': []
            }
        
        # Esegui ottimizzazione
        result = optimizer.optimize_nesting(odl_list, autoclave)
        
        return result
        
    except Exception as e:
        logger.error(f"Errore nel calcolo nesting migliorato: {str(e)}")
        return {
            'success': False,
            'error': f'Errore interno: {str(e)}',
            'selected_odl': [],
            'excluded_odl': [],
            'exclusion_reasons': []
        } 