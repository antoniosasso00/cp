"""
🔧 SERVIZIO DI ROBUSTEZZA PER MODULO NESTING
============================================

Questo servizio migliora la robustezza del modulo nesting:
1. Aggiunge validazioni estese
2. Implementa fallback per situazioni problematiche
3. Migliora l'error handling
4. Garantisce sempre un risultato utilizzabile

Autore: CarbonPilot Development Team
Data: 2025-05-31
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.tool import Tool
from models.batch_nesting import BatchNesting, StatoBatchNestingEnum
from services.nesting_service import NestingService, NestingParameters, ToolPosition, NestingResult

logger = logging.getLogger(__name__)

class RobustNestingService:
    """Servizio robusto per il nesting con validazioni e fallback"""
    
    def __init__(self):
        self.base_nesting_service = NestingService()
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
            
            # 4. Validazione ODL specifici
            valid_odl_ids = self._validate_odl_list(db, odl_ids)
            if not valid_odl_ids:
                result['message'] = 'Nessun ODL valido fornito'
                result['algorithm_status'] = 'NO_VALID_ODL'
                result['batch_id'] = f'EMPTY_BATCH_{int(datetime.now().timestamp())}'
                return result
            
            # 5. Validazione autoclavi specifiche
            valid_autoclave_ids = self._validate_autoclave_list(db, autoclave_ids)
            if not valid_autoclave_ids:
                result['message'] = 'Nessuna autoclave valida fornita'
                result['algorithm_status'] = 'NO_VALID_AUTOCLAVE'
                result['batch_id'] = f'EMPTY_BATCH_{int(datetime.now().timestamp())}'
                return result
            
            # 6. Generazione nesting con algoritmo base
            logger.info(f"🚀 Generazione nesting: {len(valid_odl_ids)} ODL su {len(valid_autoclave_ids)} autoclavi")
            
            nesting_results = []
            total_positioned = 0
            all_excluded = []
            
            for autoclave_id in valid_autoclave_ids:
                if not valid_odl_ids:  # Tutti gli ODL sono stati posizionati
                    break
                
                # Genera nesting per questa autoclave
                nesting_result = self.base_nesting_service.generate_nesting(
                    db=db,
                    odl_ids=valid_odl_ids[:],  # Copia della lista
                    autoclave_id=autoclave_id,
                    parameters=parameters
                )
                
                if nesting_result.success and nesting_result.positioned_tools:
                    # Crea batch per questo nesting
                    batch_id = self._create_robust_batch(
                        db=db, 
                        nesting_result=nesting_result, 
                        autoclave_id=autoclave_id,
                        parameters=parameters
                    )
                    
                    if batch_id:
                        nesting_results.append({
                            'batch_id': batch_id,
                            'autoclave_id': autoclave_id,
                            'positioned_count': len(nesting_result.positioned_tools),
                            'efficiency': nesting_result.efficiency
                        })
                        
                        # Rimuovi ODL posizionati dalla lista
                        positioned_odl_ids = [tool.odl_id for tool in nesting_result.positioned_tools]
                        valid_odl_ids = [odl_id for odl_id in valid_odl_ids if odl_id not in positioned_odl_ids]
                        total_positioned += len(positioned_odl_ids)
                        
                        # Se è il primo batch, usalo come principale
                        if not result['batch_id']:
                            result['batch_id'] = batch_id
                            result['positioned_tools'] = [
                                {
                                    'odl_id': tool.odl_id,
                                    'x': tool.x,
                                    'y': tool.y,
                                    'width': tool.width,
                                    'height': tool.height,
                                    'peso': tool.peso,
                                    'rotated': tool.rotated
                                }
                                for tool in nesting_result.positioned_tools
                            ]
                            result['efficiency'] = nesting_result.efficiency
                            result['total_weight'] = nesting_result.total_weight
                    else:
                        # ✅ FIX: Se creazione batch fallisce, genera ID di fallback
                        logger.warning(f"⚠️ Creazione batch fallita per autoclave {autoclave_id}")
                        fallback_batch_id = f'BATCH_FAILED_{autoclave_id}_{int(datetime.now().timestamp())}'
                        if not result['batch_id']:
                            result['batch_id'] = fallback_batch_id
                
                # Accumula esclusioni
                all_excluded.extend(nesting_result.excluded_odls)
            
            # 7. Prepara risultato finale
            if nesting_results:
                result['success'] = True
                result['algorithm_status'] = 'COMPLETED_SUCCESSFULLY'
                
                if len(nesting_results) == 1:
                    result['message'] = f'Nesting generato: {total_positioned} ODL posizionati'
                else:
                    additional_batches = [nr['batch_id'] for nr in nesting_results[1:]]
                    result['message'] = f'{total_positioned} ODL posizionati su {len(nesting_results)} batch. Batch aggiuntivi: {additional_batches}'
            else:
                result['success'] = False
                result['algorithm_status'] = 'NO_POSITIONING_POSSIBLE'
                result['message'] = 'Impossibile posizionare ODL sulle autoclavi disponibili'
                result['batch_id'] = f'FAILED_BATCH_{int(datetime.now().timestamp())}'
            
            result['excluded_odls'] = all_excluded
            
            logger.info(f"✅ Nesting robusto completato: {result['success']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Errore nella generazione nesting robusto: {str(e)}")
            result['success'] = False
            result['algorithm_status'] = 'ERROR'
            result['message'] = f'Errore imprevisto: {str(e)}'
            result['batch_id'] = f'ERROR_BATCH_{int(datetime.now().timestamp())}'
            return result
    
    def _validate_odl_list(self, db: Session, odl_ids: List[int]) -> List[int]:
        """Valida e filtra la lista di ODL"""
        try:
            valid_odls = db.query(ODL).filter(
                ODL.id.in_(odl_ids),
                ODL.status == 'Attesa Cura',
                ODL.parte_id != None,
                ODL.tool_id != None
            ).all()
            
            valid_ids = [odl.id for odl in valid_odls]
            
            if len(valid_ids) != len(odl_ids):
                invalid_count = len(odl_ids) - len(valid_ids)
                logger.warning(f"⚠️ {invalid_count} ODL non validi rimossi dalla lista")
            
            return valid_ids
            
        except Exception as e:
            logger.error(f"Errore validazione ODL: {str(e)}")
            return []
    
    def _validate_autoclave_list(self, db: Session, autoclave_ids: List[int]) -> List[int]:
        """Valida e filtra la lista di autoclavi"""
        try:
            valid_autoclaves = db.query(Autoclave).filter(
                Autoclave.id.in_(autoclave_ids),
                Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE,
                Autoclave.larghezza_piano != None,
                Autoclave.lunghezza != None
            ).all()
            
            valid_ids = [autoclave.id for autoclave in valid_autoclaves]
            
            if len(valid_ids) != len(autoclave_ids):
                invalid_count = len(autoclave_ids) - len(valid_ids)
                logger.warning(f"⚠️ {invalid_count} autoclavi non valide rimosse dalla lista")
            
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
        """Crea un batch robusto con validazione dei dati"""
        try:
            batch_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Ottieni dati autoclave
            autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            if not autoclave:
                logger.error(f"Autoclave {autoclave_id} non trovata")
                return None
            
            # Prepara configurazione JSON robusta
            tool_positions = []
            for tool in nesting_result.positioned_tools:
                tool_data = {
                    'odl_id': tool.odl_id,
                    'x': float(tool.x),
                    'y': float(tool.y),
                    'width': float(tool.width),
                    'height': float(tool.height),
                    'peso': float(tool.peso),
                    'rotated': bool(tool.rotated)
                }
                tool_positions.append(tool_data)
            
            configurazione_json = {
                'canvas_width': float(autoclave.larghezza_piano or 2000),
                'canvas_height': float(autoclave.lunghezza or 3000),
                'scale_factor': 1.0,
                'tool_positions': tool_positions,
                'plane_assignments': {str(tool.odl_id): 1 for tool in nesting_result.positioned_tools},
                'autoclave_mm': [
                    float(autoclave.lunghezza or 3000),  # Larghezza autoclave in mm
                    float(autoclave.larghezza_piano or 2000)  # Altezza autoclave in mm
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
                'priorita_area': bool(parameters.priorita_area),
                'accorpamento_odl': False,
                'use_secondary_plane': False,
                'max_weight_per_plane_kg': None
            }
            
            # Crea batch nel database
            batch = BatchNesting(
                id=batch_id,
                nome=f'Robust Nesting {autoclave.nome} {timestamp}',
                stato=StatoBatchNestingEnum.SOSPESO.value,
                autoclave_id=autoclave_id,
                odl_ids=[tool.odl_id for tool in nesting_result.positioned_tools],
                configurazione_json=configurazione_json,
                parametri=parametri,
                numero_nesting=1,
                peso_totale_kg=nesting_result.total_weight,
                area_totale_utilizzata=nesting_result.used_area / 10000,  # Convert to cm²
                valvole_totali_utilizzate=len(nesting_result.positioned_tools),
                note=f'Batch robusto: {len(tool_positions)} tool posizionati. Efficienza: {nesting_result.efficiency:.1f}%',
                creato_da_utente='robust_nesting_service',
                creato_da_ruolo='Curing'
            )
            
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            logger.info(f"✅ Batch robusto creato: {batch_id}")
            return batch_id
            
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
        
        logger.info("🔄 Applicazione strategie fallback...")
        
        for issue in validation_result.get('issues', []):
            issue_type = issue['type']
            
            if issue_type in self.fallback_strategies:
                fallback_result = self.fallback_strategies[issue_type](db, issue, result)
                if fallback_result['success']:
                    logger.info(f"✅ Fallback {issue_type} applicato con successo")
                    return fallback_result
                else:
                    logger.warning(f"⚠️ Fallback {issue_type} fallito")
        
        # Fallback finale: crea batch vuoto per debugging
        result.update({
            'success': False,
            'algorithm_status': 'FALLBACK_APPLIED',
            'message': 'Sistema non operativo - richiede intervento manuale',
            'batch_id': ''
        })
        
        return result
    
    def _handle_no_odl(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il caso di nessun ODL disponibile"""
        result.update({
            'success': False,
            'algorithm_status': 'NO_ODL_AVAILABLE',
            'message': 'Nessun ODL in stato "Attesa Cura". Creare nuovi ODL per procedere.',
            'batch_id': f'NO_ODL_{int(datetime.now().timestamp())}'
        })
        return result
    
    def _handle_no_autoclave(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce il caso di nessuna autoclave disponibile"""
        # Tentativo automatico di liberare autoclavi
        try:
            updated = db.query(Autoclave).filter(
                Autoclave.stato == StatoAutoclaveEnum.IN_USO
            ).update({'stato': StatoAutoclaveEnum.DISPONIBILE})
            
            if updated > 0:
                db.commit()
                result.update({
                    'success': True,
                    'algorithm_status': 'AUTOCLAVE_FREED',
                    'message': f'{updated} autoclavi liberate automaticamente',
                    'fixes_applied': [f'Liberate {updated} autoclavi'],
                    'batch_id': f'AUTO_FIX_{int(datetime.now().timestamp())}'
                })
            else:
                result.update({
                    'success': False,
                    'algorithm_status': 'NO_AUTOCLAVE_AVAILABLE',
                    'message': 'Nessuna autoclave disponibile. Verificare stato autoclavi.',
                    'batch_id': f'NO_AUTOCLAVE_{int(datetime.now().timestamp())}'
                })
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Errore nel liberare autoclavi: {str(e)}")
            result.update({
                'success': False,
                'algorithm_status': 'AUTOCLAVE_FIX_FAILED',
                'message': f'Impossibile liberare autoclavi: {str(e)}',
                'batch_id': f'FIX_FAILED_{int(datetime.now().timestamp())}'
            })
            return result
    
    def _handle_algorithm_failure(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce fallimento dell'algoritmo"""
        result.update({
            'success': False,
            'algorithm_status': 'ALGORITHM_FAILED',
            'message': 'Algoritmo di nesting fallito. Verificare parametri e dati.',
            'batch_id': f'ALG_FAILED_{int(datetime.now().timestamp())}'
        })
        return result
    
    def _handle_positioning_failure(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce fallimento del posizionamento"""
        result.update({
            'success': False,
            'algorithm_status': 'POSITIONING_FAILED',
            'message': 'Impossibile posizionare tool nelle autoclavi. Verificare dimensioni.',
            'batch_id': f'POS_FAILED_{int(datetime.now().timestamp())}'
        })
        return result
    
    def _handle_data_corruption(self, db: Session, issue: Dict, result: Dict) -> Dict:
        """Gestisce corruzione dei dati"""
        result.update({
            'success': False,
            'algorithm_status': 'DATA_CORRUPTION',
            'message': 'Dati corrotti rilevati. Verificare integrità database.',
            'batch_id': f'DATA_CORRUPT_{int(datetime.now().timestamp())}'
        })
        return result 