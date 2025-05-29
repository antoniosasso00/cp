"""
Servizio per la gestione del nesting multiplo con batch e assegnazione di autoclavi.

Questo servizio si occupa di:
- Raggruppare ODL compatibili per ciclo di cura
- Assegnare automaticamente le autoclavi disponibili
- Creare batch di nesting ottimizzati
- Gestire preview e conferma dei batch
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import logging

# Importazioni dei modelli
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.nesting_result import NestingResult
from models.nesting_batch import NestingBatch
from models.tool import Tool
from models.parte import Parte
from models.catalogo import Catalogo
from models.ciclo_cura import CicloCura

# Importazioni dei servizi
from nesting_optimizer.auto_nesting import NestingOptimizer, NestingParameters

# Configurazione logging
logger = logging.getLogger(__name__)


class MultiNestingService:
    """
    Servizio per la gestione del nesting multiplo con batch e assegnazione di autoclavi.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def raggruppa_odl_per_ciclo_cura(self, priorita_minima: int = 1) -> Dict[str, List[ODL]]:
        """
        Raggruppa gli ODL in attesa per ciclo di cura compatibile.
        
        Args:
            priorita_minima: Priorità minima degli ODL da considerare
            
        Returns:
            Dict[str, List[ODL]]: Dizionario con chiave il ciclo di cura e valore la lista degli ODL
        """
        logger.info(f"Raggruppamento ODL per ciclo di cura con priorità >= {priorita_minima}")
        
        # Recupera tutti gli ODL in stato "In Coda" con priorità >= priorità minima
        query = self.db.query(ODL).filter(
            ODL.status == "In Coda",
            ODL.priorita >= priorita_minima
        ).join(ODL.parte).join(Parte.catalogo)
        
        odl_in_coda = query.all()
        logger.info(f"Trovati {len(odl_in_coda)} ODL in coda")
        
        # Raggruppa per ciclo di cura
        groups = {}
        for odl in odl_in_coda:
            if odl.parte and odl.parte.catalogo:
                # Crea una chiave basata su categoria e sotto_categoria
                ciclo_key = f"{odl.parte.catalogo.categoria}_{odl.parte.catalogo.sotto_categoria}"
                if ciclo_key not in groups:
                    groups[ciclo_key] = []
                groups[ciclo_key].append(odl)
        
        logger.info(f"Creati {len(groups)} gruppi di ODL compatibili")
        for ciclo_key, odl_list in groups.items():
            logger.debug(f"Gruppo {ciclo_key}: {len(odl_list)} ODL")
        
        return groups
    
    def get_autoclavi_disponibili(self) -> List[Autoclave]:
        """
        Recupera tutte le autoclavi disponibili per il nesting.
        
        Returns:
            List[Autoclave]: Lista delle autoclavi disponibili ordinate per capacità
        """
        autoclaves = self.db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).order_by(Autoclave.area_piano.desc()).all()
        
        logger.info(f"Trovate {len(autoclaves)} autoclavi disponibili")
        return autoclaves
    
    def calcola_assegnazione_autoclavi(
        self, 
        gruppi_odl: Dict[str, List[ODL]], 
        autoclavi: List[Autoclave],
        parametri_nesting: Optional[Dict] = None
    ) -> Dict[str, List[Dict]]:
        """
        Calcola l'assegnazione ottimale degli ODL alle autoclavi per ogni gruppo.
        
        Args:
            gruppi_odl: Gruppi di ODL per ciclo di cura
            autoclavi: Lista delle autoclavi disponibili
            parametri_nesting: Parametri per l'ottimizzazione del nesting
            
        Returns:
            Dict[str, List[Dict]]: Assegnazioni per ogni gruppo di ciclo di cura
        """
        logger.info("Calcolo assegnazione autoclavi per gruppi ODL")
        
        assegnazioni = {}
        parametri = NestingParameters.from_dict(parametri_nesting or {})
        
        for ciclo_key, odl_list in gruppi_odl.items():
            logger.info(f"Processando gruppo {ciclo_key} con {len(odl_list)} ODL")
            
            # Ordina gli ODL per priorità decrescente
            odl_ordinati = sorted(odl_list, key=lambda x: x.priorita, reverse=True)
            
            # Calcola assegnazioni per questo gruppo
            assegnazioni_gruppo = self._assegna_odl_a_autoclavi(
                odl_ordinati, autoclavi, parametri
            )
            
            assegnazioni[ciclo_key] = assegnazioni_gruppo
            
            # Log delle assegnazioni
            for i, assegnazione in enumerate(assegnazioni_gruppo):
                autoclave_nome = assegnazione['autoclave']['nome']
                num_odl = len(assegnazione['odl_assegnati'])
                efficienza = assegnazione['efficienza']
                logger.info(f"  Autoclave {autoclave_nome}: {num_odl} ODL, efficienza {efficienza:.1f}%")
        
        return assegnazioni
    
    def _assegna_odl_a_autoclavi(
        self, 
        odl_list: List[ODL], 
        autoclavi: List[Autoclave],
        parametri: NestingParameters
    ) -> List[Dict]:
        """
        Assegna una lista di ODL alle autoclavi disponibili usando l'algoritmo di nesting.
        
        Args:
            odl_list: Lista degli ODL da assegnare
            autoclavi: Lista delle autoclavi disponibili
            parametri: Parametri per l'ottimizzazione
            
        Returns:
            List[Dict]: Lista delle assegnazioni con dettagli
        """
        assegnazioni = []
        odl_rimanenti = odl_list.copy()
        autoclavi_utilizzate = set()
        
        while odl_rimanenti and len(autoclavi_utilizzate) < len(autoclavi):
            # Trova la migliore autoclave per gli ODL rimanenti
            migliore_assegnazione = None
            migliore_efficienza = 0
            
            for autoclave in autoclavi:
                if autoclave.id in autoclavi_utilizzate:
                    continue
                
                # Testa il nesting con questa autoclave
                optimizer = NestingOptimizer(self.db, parametri)
                risultato = optimizer.optimize_single_plane_nesting(odl_rimanenti, autoclave)
                
                if risultato and risultato.get('efficienza', 0) > migliore_efficienza:
                    migliore_efficienza = risultato['efficienza']
                    migliore_assegnazione = {
                        'autoclave': {
                            'id': autoclave.id,
                            'nome': autoclave.nome,
                            'area_piano': autoclave.area_piano,
                            'capacita_peso': autoclave.capacita_peso
                        },
                        'odl_assegnati': risultato['odl_inclusi'],
                        'odl_esclusi': risultato['odl_esclusi'],
                        'efficienza': risultato['efficienza'],
                        'peso_totale': risultato['peso_totale'],
                        'area_utilizzata': risultato['area_utilizzata'],
                        'posizioni_tool': risultato.get('posizioni_tool', [])
                    }
            
            # Se abbiamo trovato una buona assegnazione, la aggiungiamo
            if migliore_assegnazione and migliore_efficienza >= parametri.efficienza_minima_percent:
                assegnazioni.append(migliore_assegnazione)
                autoclavi_utilizzate.add(migliore_assegnazione['autoclave']['id'])
                
                # Rimuovi gli ODL assegnati dalla lista rimanente
                odl_assegnati_ids = [odl.id for odl in migliore_assegnazione['odl_assegnati']]
                odl_rimanenti = [odl for odl in odl_rimanenti if odl.id not in odl_assegnati_ids]
                
                logger.debug(f"Assegnata autoclave {migliore_assegnazione['autoclave']['nome']}, "
                           f"rimangono {len(odl_rimanenti)} ODL")
            else:
                # Nessuna autoclave può ospitare gli ODL rimanenti con efficienza sufficiente
                logger.warning(f"Impossibile assegnare {len(odl_rimanenti)} ODL rimanenti "
                             f"con efficienza >= {parametri.efficienza_minima_percent}%")
                break
        
        return assegnazioni
    
    def crea_batch_preview(
        self, 
        parametri_nesting: Optional[Dict] = None,
        priorita_minima: int = 1,
        nome_batch: Optional[str] = None
    ) -> Dict:
        """
        Crea un preview del batch di nesting multiplo senza salvare nel database.
        
        Args:
            parametri_nesting: Parametri per l'ottimizzazione del nesting
            priorita_minima: Priorità minima degli ODL da considerare
            nome_batch: Nome del batch (se non specificato, viene generato automaticamente)
            
        Returns:
            Dict: Preview del batch con tutte le assegnazioni
        """
        logger.info("Creazione preview batch nesting multiplo")
        
        # Raggruppa ODL per ciclo di cura
        gruppi_odl = self.raggruppa_odl_per_ciclo_cura(priorita_minima)
        
        if not gruppi_odl:
            return {
                'success': False,
                'message': 'Nessun ODL in coda trovato con la priorità specificata',
                'batch_preview': None
            }
        
        # Recupera autoclavi disponibili
        autoclavi = self.get_autoclavi_disponibili()
        
        if not autoclavi:
            return {
                'success': False,
                'message': 'Nessuna autoclave disponibile per il nesting',
                'batch_preview': None
            }
        
        # Calcola assegnazioni
        assegnazioni = self.calcola_assegnazione_autoclavi(gruppi_odl, autoclavi, parametri_nesting)
        
        # Calcola statistiche aggregate
        statistiche = self._calcola_statistiche_batch(assegnazioni)
        
        # Genera nome batch se non specificato
        if not nome_batch:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            nome_batch = f"Batch_Auto_{timestamp}"
        
        batch_preview = {
            'nome': nome_batch,
            'descrizione': f"Batch automatico generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            'gruppi_ciclo_cura': list(gruppi_odl.keys()),
            'assegnazioni': assegnazioni,
            'statistiche': statistiche,
            'parametri_nesting': parametri_nesting or {},
            'autoclavi_disponibili': len(autoclavi),
            'autoclavi_utilizzate': statistiche['numero_autoclavi'],
            'odl_totali': statistiche['numero_odl_totali'],
            'odl_assegnati': statistiche['numero_odl_assegnati'],
            'odl_non_assegnati': statistiche['numero_odl_non_assegnati'],
            'efficienza_media': statistiche['efficienza_media']
        }
        
        return {
            'success': True,
            'message': f'Preview batch creato con successo: {statistiche["numero_autoclavi"]} autoclavi, {statistiche["numero_odl_assegnati"]} ODL assegnati',
            'batch_preview': batch_preview
        }
    
    def _calcola_statistiche_batch(self, assegnazioni: Dict[str, List[Dict]]) -> Dict:
        """
        Calcola le statistiche aggregate per un batch.
        
        Args:
            assegnazioni: Assegnazioni per ogni gruppo di ciclo di cura
            
        Returns:
            Dict: Statistiche aggregate del batch
        """
        numero_autoclavi = 0
        numero_odl_assegnati = 0
        numero_odl_non_assegnati = 0
        peso_totale = 0.0
        area_totale_utilizzata = 0.0
        efficienze = []
        
        autoclavi_utilizzate = set()
        
        for ciclo_key, assegnazioni_gruppo in assegnazioni.items():
            for assegnazione in assegnazioni_gruppo:
                autoclave_id = assegnazione['autoclave']['id']
                autoclavi_utilizzate.add(autoclave_id)
                
                numero_odl_assegnati += len(assegnazione['odl_assegnati'])
                numero_odl_non_assegnati += len(assegnazione['odl_esclusi'])
                peso_totale += assegnazione['peso_totale']
                area_totale_utilizzata += assegnazione['area_utilizzata']
                efficienze.append(assegnazione['efficienza'])
        
        numero_autoclavi = len(autoclavi_utilizzate)
        efficienza_media = sum(efficienze) / len(efficienze) if efficienze else 0.0
        numero_odl_totali = numero_odl_assegnati + numero_odl_non_assegnati
        
        return {
            'numero_autoclavi': numero_autoclavi,
            'numero_odl_totali': numero_odl_totali,
            'numero_odl_assegnati': numero_odl_assegnati,
            'numero_odl_non_assegnati': numero_odl_non_assegnati,
            'peso_totale_kg': peso_totale,
            'area_totale_utilizzata': area_totale_utilizzata,
            'efficienza_media': efficienza_media
        }
    
    def salva_batch(
        self, 
        batch_preview: Dict, 
        creato_da_ruolo: Optional[str] = None
    ) -> NestingBatch:
        """
        Salva un batch di nesting nel database basandosi sul preview.
        
        Args:
            batch_preview: Preview del batch da salvare
            creato_da_ruolo: Ruolo dell'utente che crea il batch
            
        Returns:
            NestingBatch: Il batch salvato nel database
        """
        logger.info(f"Salvataggio batch: {batch_preview['nome']}")
        
        try:
            # Crea il batch
            batch = NestingBatch(
                nome=batch_preview['nome'],
                descrizione=batch_preview['descrizione'],
                stato="Pronto",
                parametri_nesting=batch_preview['parametri_nesting'],
                creato_da_ruolo=creato_da_ruolo,
                numero_autoclavi=batch_preview['statistiche']['numero_autoclavi'],
                numero_odl_totali=batch_preview['statistiche']['numero_odl_totali'],
                peso_totale_kg=batch_preview['statistiche']['peso_totale_kg'],
                area_totale_utilizzata=batch_preview['statistiche']['area_totale_utilizzata'],
                efficienza_media=batch_preview['statistiche']['efficienza_media']
            )
            
            self.db.add(batch)
            self.db.flush()  # Per ottenere l'ID del batch
            
            # Crea i NestingResult per ogni assegnazione
            for ciclo_key, assegnazioni_gruppo in batch_preview['assegnazioni'].items():
                for assegnazione in assegnazioni_gruppo:
                    nesting_result = NestingResult(
                        batch_id=batch.id,
                        autoclave_id=assegnazione['autoclave']['id'],
                        odl_ids=[odl.id for odl in assegnazione['odl_assegnati']],
                        odl_esclusi_ids=[odl.id for odl in assegnazione['odl_esclusi']],
                        stato="Pronto",
                        peso_totale_kg=assegnazione['peso_totale'],
                        area_utilizzata=assegnazione['area_utilizzata'],
                        posizioni_tool=assegnazione['posizioni_tool']
                    )
                    
                    # Associa gli ODL al nesting result
                    nesting_result.odl_list = assegnazione['odl_assegnati']
                    
                    self.db.add(nesting_result)
            
            self.db.commit()
            logger.info(f"Batch {batch.nome} salvato con successo (ID: {batch.id})")
            
            return batch
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Errore nel salvataggio del batch: {str(e)}")
            raise
    
    def get_batch_list(self, stato: Optional[str] = None) -> List[NestingBatch]:
        """
        Recupera la lista dei batch di nesting.
        
        Args:
            stato: Filtro per stato del batch (opzionale)
            
        Returns:
            List[NestingBatch]: Lista dei batch
        """
        query = self.db.query(NestingBatch)
        
        if stato:
            query = query.filter(NestingBatch.stato == stato)
        
        return query.order_by(NestingBatch.created_at.desc()).all()
    
    def get_batch_dettagli(self, batch_id: int) -> Optional[Dict]:
        """
        Recupera i dettagli completi di un batch.
        
        Args:
            batch_id: ID del batch
            
        Returns:
            Dict: Dettagli completi del batch o None se non trovato
        """
        batch = self.db.query(NestingBatch).filter(NestingBatch.id == batch_id).first()
        
        if not batch:
            return None
        
        # Raggruppa i nesting results per autoclave
        nesting_per_autoclave = {}
        for nr in batch.nesting_results:
            autoclave_nome = nr.autoclave.nome if nr.autoclave else "Sconosciuta"
            if autoclave_nome not in nesting_per_autoclave:
                nesting_per_autoclave[autoclave_nome] = []
            nesting_per_autoclave[autoclave_nome].append({
                'id': nr.id,
                'odl_count': len(nr.odl_list),
                'peso_kg': nr.peso_totale_kg,
                'area_utilizzata': nr.area_utilizzata,
                'efficienza': nr.efficienza_totale,
                'stato': nr.stato
            })
        
        return {
            'batch': {
                'id': batch.id,
                'nome': batch.nome,
                'descrizione': batch.descrizione,
                'stato': batch.stato,
                'numero_autoclavi': batch.numero_autoclavi,
                'numero_odl_totali': batch.numero_odl_totali,
                'peso_totale_kg': batch.peso_totale_kg,
                'efficienza_media': batch.efficienza_media,
                'created_at': batch.created_at,
                'creato_da_ruolo': batch.creato_da_ruolo
            },
            'nesting_per_autoclave': nesting_per_autoclave,
            'odl_totali': [
                {
                    'id': odl.id,
                    'parte_nome': odl.parte.nome if odl.parte else "Sconosciuta",
                    'tool_nome': odl.tool.nome if odl.tool else "Sconosciuto",
                    'priorita': odl.priorita,
                    'status': odl.status
                }
                for odl in batch.odl_totali
            ]
        } 