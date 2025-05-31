"""
Router per la gestione delle operazioni di nesting.

Questo modulo contiene gli endpoint per:
- Ottenere la lista dei nesting esistenti
- Creare nuovi nesting
- Generare nesting automatico
- Preview del nesting
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import os
import logging
import json

# Configurazione logger
logger = logging.getLogger(__name__)

from api.database import get_db
from schemas.nesting import (
    NestingRead, NestingCreate, AutomaticNestingRequest, AutomaticNestingResponse,
    NestingPreviewRequest, NestingPreviewResponse, NestingDetailResponse,
    NestingStatusUpdate, AutoclaveSelectionSchema, ODLNestingInfo, AutoclaveNestingInfo, ODLGroupPreview,
    NestingParameters, NestingParametersResponse, AutomaticNestingRequestWithParams,
    NestingLayoutResponse, MultiNestingLayoutResponse, OrientationCalculationRequest,
    OrientationCalculationResponse, NestingToolsResponse, NestingToolInfo, ToolPosition,
    EnhancedNestingRequest, EnhancedNestingPreviewResponse, ODLNestingInfoEnhanced,
    AutoclaveNestingInfoEnhanced
)
from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.catalogo import Catalogo
from nesting_optimizer.auto_nesting import generate_automatic_nesting, NestingOptimizer
# ✅ NUOVO: Import dell'algoritmo migliorato
from nesting_optimizer.enhanced_nesting import compute_enhanced_nesting, NestingConstraints
from sqlalchemy.orm import joinedload
from services.nesting_layout_service import NestingLayoutService
from fastapi.responses import FileResponse
from services.nesting_report_generator import NestingReportGenerator
from models.report import Report
from services.nesting_state_sync_service import NestingStateSyncService

# Creo il router con prefisso e tag per l'organizzazione
router = APIRouter(
    tags=["nesting"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[NestingRead])
async def get_nesting_list(db: Session = Depends(get_db)):
    """
    Endpoint GET per ottenere la lista di tutti i nesting dal database.
    
    Returns:
        List[NestingRead]: Lista dei nesting esistenti dal database
    """
    try:
        # ✅ DATI REALI: Carica i nesting dal database con join eager per ottimizzare le query
        nesting_results = db.query(NestingResult)\
            .options(joinedload(NestingResult.autoclave))\
            .options(joinedload(NestingResult.odl_list))\
            .all()
        
        # Converte i risultati in formato NestingRead
        nesting_list = []
        for result in nesting_results:
            # ✅ CICLO CURA REALE: Estrae il ciclo cura dal primo ODL se disponibile
            ciclo_cura = None
            if result.odl_list and len(result.odl_list) > 0:
                first_odl = result.odl_list[0]
                if first_odl.parte and first_odl.parte.ciclo_cura:
                    ciclo_cura = first_odl.parte.ciclo_cura.nome
            
            # ✅ MOTIVI ESCLUSIONE REALI: Converte da JSON se presente
            motivi_esclusione = []
            if result.motivi_esclusione:
                if isinstance(result.motivi_esclusione, str):
                    try:
                        motivi_esclusione = json.loads(result.motivi_esclusione)
                    except:
                        motivi_esclusione = [result.motivi_esclusione]
                elif isinstance(result.motivi_esclusione, list):
                    motivi_esclusione = result.motivi_esclusione
            
            nesting_data = NestingRead(
                id=str(result.id),
                created_at=result.created_at,
                stato=result.stato,
                note=result.note,
                # ✅ CAMPI AGGIUNTIVI: Tutti i campi reali dal database
                autoclave_id=result.autoclave_id,
                autoclave_nome=result.autoclave.nome if result.autoclave else None,
                ciclo_cura=ciclo_cura,  # ✅ REALE invece di None
                odl_inclusi=len(result.odl_list) if result.odl_list else 0,
                odl_esclusi=len(result.odl_esclusi_ids) if result.odl_esclusi_ids else 0,
                efficienza=result.efficienza_totale,  # Usa la proprietà calcolata
                area_utilizzata=result.area_utilizzata,
                area_totale=result.area_totale,
                peso_totale=result.peso_totale_kg,
                valvole_utilizzate=result.valvole_utilizzate,
                valvole_totali=result.valvole_totali,
                motivi_esclusione=motivi_esclusione
            )
            nesting_list.append(nesting_data)
        
        logger.info(f"✅ Caricati {len(nesting_list)} nesting dal database con dati completi")
        return nesting_list
        
    except Exception as e:
        logger.error(f"❌ Errore nel caricamento nesting: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nel caricamento dei nesting: {str(e)}")


@router.post("/", response_model=NestingRead)
async def create_nesting(nesting_data: NestingCreate, db: Session = Depends(get_db)):
    """
    Endpoint POST per creare un nuovo nesting nel database con dati reali.
    
    Args:
        nesting_data (NestingCreate): Dati del nesting da creare
        
    Returns:
        NestingRead: Il nesting creato con tutti i campi popolati
    """
    try:
        # ✅ NUOVO: Crea un nesting con dati reali
        
        # 1. Valida autoclave se specificata
        autoclave = None
        if nesting_data.autoclave_id:
            autoclave = db.query(Autoclave).filter(Autoclave.id == nesting_data.autoclave_id).first()
            if not autoclave:
                raise HTTPException(status_code=404, detail=f"Autoclave con ID {nesting_data.autoclave_id} non trovata")
            if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
                raise HTTPException(status_code=400, detail=f"Autoclave {autoclave.nome} non è disponibile (stato: {autoclave.stato.value})")
        
        # 2. Valida e carica ODL se specificati
        odl_list = []
        if nesting_data.odl_ids:
            odl_query = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
                joinedload(ODL.tool)
            ).filter(ODL.id.in_(nesting_data.odl_ids))
            
            odl_list = odl_query.all()
            if len(odl_list) != len(nesting_data.odl_ids):
                found_ids = [odl.id for odl in odl_list]
                missing_ids = [odl_id for odl_id in nesting_data.odl_ids if odl_id not in found_ids]
                raise HTTPException(status_code=404, detail=f"ODL non trovati: {missing_ids}")
            
            # Verifica che gli ODL siano in stato corretto
            invalid_odl = [odl for odl in odl_list if odl.status != "Attesa Cura"]
            if invalid_odl:
                invalid_ids = [str(odl.id) for odl in invalid_odl]
                raise HTTPException(status_code=400, detail=f"ODL non in stato 'Attesa Cura': {invalid_ids}")
        
        # 3. Calcola statistiche reali
        area_utilizzata = 0.0
        area_totale = 0.0
        peso_totale_kg = 0.0
        valvole_utilizzate = 0
        valvole_totali = 0
        ciclo_cura = None
        
        if autoclave:
            area_totale = autoclave.area_piano
            valvole_totali = autoclave.num_linee_vuoto
        
        if odl_list:
            # Calcola peso e area dai tool
            for odl in odl_list:
                if odl.tool:
                    peso_totale_kg += odl.tool.peso or 0.0
                    # Area del tool = larghezza * lunghezza (convertita in cm²)
                    if odl.tool.larghezza_piano and odl.tool.lunghezza_piano:
                        tool_area = (odl.tool.larghezza_piano * odl.tool.lunghezza_piano) / 100
                        area_utilizzata += tool_area
                
                # Conta valvole richieste
                if odl.parte and odl.parte.num_valvole_richieste:
                    valvole_utilizzate += odl.parte.num_valvole_richieste
            
            # Estrae ciclo cura dal primo ODL
            first_odl = odl_list[0]
            if first_odl.parte and first_odl.parte.ciclo_cura:
                ciclo_cura = first_odl.parte.ciclo_cura.nome
        
        # 4. Crea il nesting nel database
        new_nesting = NestingResult(
            note=nesting_data.note or "Nesting creato via API",
            stato="bozza",
            autoclave_id=nesting_data.autoclave_id,
            odl_ids=nesting_data.odl_ids or [],
            area_utilizzata=area_utilizzata,
            area_totale=area_totale,
            peso_totale_kg=peso_totale_kg,
            valvole_utilizzate=valvole_utilizzate,
            valvole_totali=valvole_totali
        )
        
        db.add(new_nesting)
        db.flush()  # Per ottenere l'ID senza commit
        
        # 5. Associa gli ODL tramite la relazione many-to-many
        if odl_list:
            new_nesting.odl_list.extend(odl_list)
        
        db.commit()
        db.refresh(new_nesting)
        
        # 6. Prepara la risposta con tutti i dati reali
        response = NestingRead(
            id=str(new_nesting.id),
            created_at=new_nesting.created_at,
            stato=new_nesting.stato,
            note=new_nesting.note,
            autoclave_id=new_nesting.autoclave_id,
            autoclave_nome=autoclave.nome if autoclave else None,
            ciclo_cura=ciclo_cura,
            odl_inclusi=len(odl_list),
            odl_esclusi=0,
            efficienza=(area_utilizzata / area_totale * 100) if area_totale > 0 else 0.0,
            area_utilizzata=area_utilizzata,
            area_totale=area_totale,
            peso_totale=peso_totale_kg,
            valvole_utilizzate=valvole_utilizzate,
            valvole_totali=valvole_totali,
            motivi_esclusione=[]
        )
        
        logger.info(f"✅ Nesting creato con dati reali: ID={new_nesting.id}, "
                   f"Autoclave={autoclave.nome if autoclave else 'None'}, "
                   f"ODL={len(odl_list)}, Efficienza={response.efficienza:.1f}%")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Errore nella creazione nesting: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nella creazione del nesting: {str(e)}")


@router.post("/{nesting_id}/select-autoclave")
async def select_autoclave_for_nesting(
    nesting_id: int, 
    data: AutoclaveSelectionSchema, 
    db: Session = Depends(get_db)
):
    """
    Assegna un'autoclave a un nesting esistente.
    Questo è il primo step obbligatorio del flusso nesting manuale.
    
    Args:
        nesting_id: ID del nesting da aggiornare
        data: Schema contenente l'ID dell'autoclave da assegnare
        db: Sessione del database
        
    Returns:
        Dict con success e message
    """
    try:
        # 1. Trova il nesting
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(status_code=404, detail="Nesting non trovato")
        
        # 2. Verifica che il nesting sia in stato bozza
        if nesting.stato not in ["bozza", "In sospeso"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Non è possibile modificare l'autoclave per un nesting in stato '{nesting.stato}'"
            )
        
        # 3. Valida l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == data.autoclave_id).first()
        if not autoclave:
            raise HTTPException(status_code=404, detail=f"Autoclave con ID {data.autoclave_id} non trovata")
        
        # 4. Verifica che l'autoclave sia disponibile
        if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
            raise HTTPException(
                status_code=400, 
                detail=f"Autoclave '{autoclave.nome}' non è disponibile (stato: {autoclave.stato.value})"
            )
        
        # 5. Aggiorna il nesting
        nesting.autoclave_id = data.autoclave_id
        nesting.updated_at = datetime.utcnow()
        
        # 6. Aggiorna statistiche dell'autoclave se non erano presenti
        if nesting.area_totale == 0:
            nesting.area_totale = autoclave.area_piano
            nesting.valvole_totali = autoclave.num_linee_vuoto
        
        db.commit()
        
        logger.info(f"✅ Autoclave '{autoclave.nome}' (ID: {autoclave.id}) assegnata al nesting {nesting_id}")
        
        return {
            "success": True, 
            "message": f"Autoclave '{autoclave.nome}' assegnata con successo",
            "autoclave_id": autoclave.id,
            "autoclave_nome": autoclave.nome
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Errore nell'assegnazione autoclave al nesting {nesting_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'assegnazione dell'autoclave: {str(e)}")


@router.post("/automatic", response_model=AutomaticNestingResponse)
async def generate_automatic_nesting_endpoint(
    request: AutomaticNestingRequestWithParams = AutomaticNestingRequestWithParams(),
    db: Session = Depends(get_db)
):
    """
    Genera automaticamente il nesting ottimale per tutti gli ODL in attesa.
    Supporta parametri personalizzati per l'algoritmo di ottimizzazione.
    
    Args:
        request: Parametri per la generazione automatica inclusi i parametri dell'algoritmo
        db: Sessione del database
        
    Returns:
        AutomaticNestingResponse: Risultato della generazione automatica
    """
    try:
        # Verifica se esistono già nesting in bozza e se non è forzata la rigenerazione
        if not request.force_regenerate:
            existing_drafts = db.query(NestingResult).filter(
                NestingResult.stato == "Bozza"
            ).count()
            
            if existing_drafts > 0:
                return AutomaticNestingResponse(
                    success=False,
                    message=f"Esistono già {existing_drafts} nesting in bozza. Usa force_regenerate=true per sovrascrivere.",
                    nesting_results=[],
                    summary={"existing_drafts": existing_drafts}
                )
        
        # Prepara i parametri per l'algoritmo
        parameters_dict = None
        if request.parameters:
            parameters_dict = request.parameters.dict()
        
        # Genera il nesting automatico con i parametri
        result = generate_automatic_nesting(db, parameters_dict)
        
        return AutomaticNestingResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la generazione automatica: {str(e)}")


@router.get("/parameters", response_model=NestingParametersResponse)
async def get_nesting_parameters():
    """
    Ottiene i parametri di default per l'algoritmo di nesting.
    
    Returns:
        NestingParametersResponse: Parametri di default
    """
    try:
        default_params = NestingParameters()
        
        return NestingParametersResponse(
            success=True,
            message="Parametri di default recuperati con successo",
            parameters=default_params
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero dei parametri: {str(e)}")


@router.post("/parameters/validate", response_model=NestingParametersResponse)
async def validate_nesting_parameters(parameters: NestingParameters):
    """
    Valida i parametri forniti per l'algoritmo di nesting.
    
    Args:
        parameters: Parametri da validare
        
    Returns:
        NestingParametersResponse: Conferma della validazione
    """
    try:
        # I parametri sono già validati da Pydantic, quindi se arriviamo qui sono validi
        return NestingParametersResponse(
            success=True,
            message="Parametri validati con successo",
            parameters=parameters
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parametri non validi: {str(e)}")


@router.post("/preview-with-parameters", response_model=NestingPreviewResponse)
async def get_nesting_preview_with_parameters(
    parameters: NestingParameters,
    db: Session = Depends(get_db)
):
    """
    Ottiene una preview degli ODL disponibili per il nesting con parametri personalizzati.
    
    Args:
        parameters: Parametri personalizzati per l'algoritmo
        db: Sessione del database
        
    Returns:
        NestingPreviewResponse: Preview degli ODL e autoclavi disponibili
    """
    try:
        from nesting_optimizer.auto_nesting import NestingOptimizer, NestingParameters as AlgoParams
        
        # Converte i parametri Pydantic in parametri dell'algoritmo
        algo_params = AlgoParams(
            distanza_minima_tool_cm=parameters.distanza_minima_tool_cm,
            padding_bordo_autoclave_cm=parameters.padding_bordo_autoclave_cm,
            margine_sicurezza_peso_percent=parameters.margine_sicurezza_peso_percent,
            priorita_minima=parameters.priorita_minima,
            efficienza_minima_percent=parameters.efficienza_minima_percent
        )
        
        optimizer = NestingOptimizer(db, algo_params)
        
        # Recupera i gruppi di ODL compatibili con i parametri
        odl_groups = optimizer.get_compatible_odl_groups()
        
        # Recupera le autoclavi disponibili
        available_autoclaves = optimizer.get_available_autoclaves()
        
        # Converte in formato di risposta
        preview_groups = []
        total_odl = 0
        
        for ciclo_key, odl_list in odl_groups.items():
            total_odl += len(odl_list)
            
            # Calcola statistiche del gruppo con i parametri personalizzati
            total_area = 0.0
            total_weight = 0.0
            odl_info_list = []
            
            for odl in odl_list:
                # Calcola dimensioni dal tool
                width = odl.tool.larghezza_piano if odl.tool else 0
                length = odl.tool.lunghezza_piano if odl.tool else 0
                weight = odl.tool.peso if odl.tool else 0
                area = (width * length) / 100  # cm²
                
                total_area += area
                total_weight += weight
                
                odl_info = ODLNestingInfo(
                    id=odl.id,
                    parte_codice=odl.parte.part_number if odl.parte else None,
                    tool_nome=odl.tool.part_number_tool if odl.tool else None,
                    priorita=odl.priorita,
                    dimensioni={
                        "larghezza": width,
                        "lunghezza": length,
                        "peso": weight
                    },
                    ciclo_cura=ciclo_key,
                    status=odl.status
                )
                odl_info_list.append(odl_info)
            
            # Trova autoclavi compatibili per questo gruppo con i parametri
            compatible_autoclaves = []
            for autoclave in available_autoclaves:
                if optimizer.can_fit_in_autoclave(odl_list, autoclave):
                    effective_area = optimizer.calculate_effective_autoclave_area(autoclave)
                    autoclave_info = AutoclaveNestingInfo(
                        id=autoclave.id,
                        nome=autoclave.nome,
                        area_piano=effective_area,  # Mostra l'area effettiva
                        max_load_kg=autoclave.max_load_kg,
                        stato=autoclave.stato.value
                    )
                    compatible_autoclaves.append(autoclave_info)
            
            group_preview = ODLGroupPreview(
                ciclo_cura=ciclo_key,
                odl_list=odl_info_list,
                total_area=round(total_area, 2),
                total_weight=round(total_weight, 2),
                compatible_autoclaves=compatible_autoclaves
            )
            preview_groups.append(group_preview)
        
        # Converte le autoclavi disponibili con aree effettive
        autoclave_info_list = []
        for autoclave in available_autoclaves:
            effective_area = optimizer.calculate_effective_autoclave_area(autoclave)
            autoclave_info = AutoclaveNestingInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                area_piano=effective_area,
                max_load_kg=autoclave.max_load_kg,
                stato=autoclave.stato.value
            )
            autoclave_info_list.append(autoclave_info)
        
        return NestingPreviewResponse(
            success=True,
            message=f"Preview generata con parametri personalizzati: {total_odl} ODL trovati",
            odl_groups=preview_groups,
            available_autoclaves=autoclave_info_list,
            total_odl_pending=total_odl
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la generazione della preview: {str(e)}")


@router.get("/preview", response_model=NestingPreviewResponse)
async def get_nesting_preview(
    request: NestingPreviewRequest = NestingPreviewRequest(),
    db: Session = Depends(get_db)
):
    """
    Genera una preview del nesting automatico mostrando i gruppi di ODL
    raggruppati per ciclo di cura e le autoclavi disponibili.
    
    Args:
        request: Parametri della richiesta di preview
        db: Sessione del database
        
    Returns:
        NestingPreviewResponse: Preview dei gruppi ODL e autoclavi disponibili
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 INIZIO PREVIEW NESTING")
        
        # Crea l'optimizer con parametri di default dell'algoritmo
        from nesting_optimizer.auto_nesting import NestingParameters as AlgoParams
        parameters = AlgoParams(priorita_minima=1)
        optimizer = NestingOptimizer(db, parameters)
        logger.info("✅ NestingOptimizer creato")
        
        # Ottieni i gruppi di ODL compatibili
        logger.info("📋 Recupero gruppi ODL compatibili...")
        odl_groups = optimizer.get_compatible_odl_groups()
        logger.info(f"   Gruppi trovati: {len(odl_groups)}")
        
        # Ottieni le autoclavi disponibili
        logger.info("🏭 Recupero autoclavi disponibili...")
        available_autoclaves = optimizer.get_available_autoclaves()
        logger.info(f"   Autoclavi disponibili: {len(available_autoclaves)}")
        
        preview_groups = []
        total_odl = 0
        
        logger.info("🔄 Processamento gruppi ODL...")
        for ciclo_key, odl_list in odl_groups.items():
            logger.info(f"   Processando gruppo {ciclo_key} con {len(odl_list)} ODL")
            
            odl_info_list = []
            total_area = 0
            total_weight = 0
            
            for i, odl in enumerate(odl_list):
                try:
                    logger.info(f"     Processando ODL {odl.id} ({i+1}/{len(odl_list)})")
                    
                    # Calcola dimensioni dal tool
                    width = odl.tool.larghezza_piano if odl.tool else 0
                    length = odl.tool.lunghezza_piano if odl.tool else 0
                    weight = odl.tool.peso if odl.tool else 0
                    area = (width * length) / 100  # cm²
                    
                    logger.info(f"       Dimensioni: {width}x{length}, peso: {weight}")
                    
                    odl_info = ODLNestingInfo(
                        id=odl.id,
                        parte_codice=odl.parte.part_number if odl.parte else None,
                        tool_nome=odl.tool.part_number_tool if odl.tool else None,
                        priorita=odl.priorita,
                        dimensioni={
                            "larghezza": width,
                            "lunghezza": length,
                            "peso": weight
                        },
                        ciclo_cura=ciclo_key,
                        status=odl.status
                    )
                    
                    odl_info_list.append(odl_info)
                    total_area += area
                    total_weight += weight
                    total_odl += 1
                    
                    logger.info(f"       ✅ ODL {odl.id} processato correttamente")
                    
                except Exception as e:
                    logger.error(f"       ❌ Errore processando ODL {odl.id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # Trova autoclavi compatibili per questo ciclo
            compatible_autoclaves = []
            for autoclave in available_autoclaves:
                # Logica di compatibilità semplificata per ora
                compatible_autoclaves.append(AutoclaveNestingInfo(
                    id=autoclave.id,
                    nome=autoclave.nome,
                    area_piano=autoclave.area_piano,
                    max_load_kg=autoclave.max_load_kg,
                    stato=autoclave.stato.value
                ))
            
            if odl_info_list:
                group_preview = ODLGroupPreview(
                    ciclo_cura=ciclo_key,
                    odl_list=odl_info_list,
                    total_area=round(total_area, 2),
                    total_weight=round(total_weight, 2),
                    compatible_autoclaves=compatible_autoclaves
                )
                preview_groups.append(group_preview)
                logger.info(f"   ✅ Gruppo {ciclo_key} aggiunto con {len(odl_info_list)} ODL")
        
        # Converte le autoclavi disponibili
        logger.info("🏭 Processamento autoclavi...")
        autoclave_info_list = []
        for autoclave in available_autoclaves:
            try:
                autoclave_info = AutoclaveNestingInfo(
                    id=autoclave.id,
                    nome=autoclave.nome,
                    area_piano=autoclave.area_piano,
                    max_load_kg=autoclave.max_load_kg,
                    stato=autoclave.stato.value
                )
                autoclave_info_list.append(autoclave_info)
                logger.info(f"   ✅ Autoclave {autoclave.nome} processata")
            except Exception as e:
                logger.error(f"   ❌ Errore processando autoclave {autoclave.nome}: {e}")
        
        logger.info(f"📊 RISULTATO FINALE: {len(preview_groups)} gruppi, {len(autoclave_info_list)} autoclavi, {total_odl} ODL")
        
        return NestingPreviewResponse(
            success=True,
            message=f"Preview generata per {len(preview_groups)} gruppi di ODL",
            odl_groups=preview_groups,
            available_autoclaves=autoclave_info_list,
            total_odl_pending=total_odl
        )
        
    except Exception as e:
        logger.error(f"💥 ERRORE GENERALE PREVIEW: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Errore durante la generazione della preview: {str(e)}")


@router.get("/active", response_model=List[NestingDetailResponse])
async def get_active_nesting(db: Session = Depends(get_db)):
    """
    Ottiene tutti i nesting attualmente attivi (caricati) nelle autoclavi.
    
    Un nesting è considerato attivo se:
    - Ha stato "Caricato"
    - L'autoclave associata è in stato "IN_USO"
    - Contiene ODL in stato "Cura"
    
    Returns:
        List[NestingDetailResponse]: Lista dei nesting attivi
    """
    try:
        # Recupera tutti i nesting in stato "Caricato"
        active_nesting = db.query(NestingResult).filter(
            NestingResult.stato == "Caricato"
        ).order_by(NestingResult.created_at.desc()).all()
        
        response_list = []
        
        for nesting in active_nesting:
            # Recupera l'autoclave associata
            autoclave = db.query(Autoclave).filter(Autoclave.id == nesting.autoclave_id).first()
            if not autoclave:
                continue
            
            # Recupera gli ODL inclusi
            odl_inclusi = []
            if nesting.odl_ids:
                odl_query = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).filter(ODL.id.in_(nesting.odl_ids))
                odl_inclusi = odl_query.all()
            
            # Recupera gli ODL esclusi
            odl_esclusi = []
            if nesting.odl_esclusi_ids:
                odl_esclusi_query = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).filter(ODL.id.in_(nesting.odl_esclusi_ids))
                odl_esclusi = odl_esclusi_query.all()
            
            # Costruisci la risposta per questo nesting
            nesting_response = NestingDetailResponse(
                id=nesting.id,
                autoclave=AutoclaveNestingInfo(
                    id=autoclave.id,
                    nome=autoclave.nome,
                    area_piano=autoclave.lunghezza * autoclave.larghezza_piano / 100,
                    max_load_kg=autoclave.max_load_kg,
                    stato=autoclave.stato.value
                ),
                odl_inclusi=[
                    ODLNestingInfo(
                        id=odl.id,
                        parte_codice=odl.parte.part_number if odl.parte else None,
                        tool_nome=odl.tool.part_number_tool if odl.tool else None,
                        priorita=odl.priorita,
                        dimensioni={
                            "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                            "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                            "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                        },
                        ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                        status=odl.status
                    ) for odl in odl_inclusi
                ],
                odl_esclusi=[
                    ODLNestingInfo(
                        id=odl.id,
                        parte_codice=odl.parte.part_number if odl.parte else None,
                        tool_nome=odl.tool.part_number_tool if odl.tool else None,
                        priorita=odl.priorita,
                        dimensioni={
                            "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                            "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                            "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                        },
                        ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                        status=odl.status
                    ) for odl in odl_esclusi
                ],
                motivi_esclusione=nesting.motivi_esclusione or [],
                statistiche={
                    "area_utilizzata": nesting.area_utilizzata,
                    "area_totale": nesting.area_totale,
                    "efficienza": (nesting.area_utilizzata / nesting.area_totale * 100) if nesting.area_totale > 0 else 0,
                    "peso_totale": nesting.peso_totale_kg,
                    "valvole_utilizzate": nesting.valvole_utilizzate,
                    "valvole_totali": nesting.valvole_totali
                },
                stato=nesting.stato,
                note=nesting.note,
                created_at=nesting.created_at
            )
            
            response_list.append(nesting_response)
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero dei nesting attivi: {str(e)}")


@router.get("/{nesting_id}", response_model=NestingDetailResponse)
async def get_nesting_details(nesting_id: int, db: Session = Depends(get_db)):
    """
    Ottiene i dettagli completi di un nesting specifico.
    
    Args:
        nesting_id: ID del nesting da recuperare
        db: Sessione del database
        
    Returns:
        NestingDetailResponse: Dettagli completi del nesting
    """
    try:
        # Recupera il nesting result
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(status_code=404, detail="Nesting non trovato")
        
        # Recupera l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == nesting.autoclave_id).first()
        if not autoclave:
            raise HTTPException(status_code=404, detail="Autoclave non trovata")
        
        # Recupera gli ODL inclusi
        odl_inclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids)).all()
        
        # Recupera gli ODL esclusi
        odl_esclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_esclusi_ids)).all()
        
        optimizer = NestingOptimizer(db)
        
        # Converte gli ODL inclusi
        odl_inclusi_info = []
        for odl in odl_inclusi:
            width = odl.tool.larghezza_piano if odl.tool else 0
            length = odl.tool.lunghezza_piano if odl.tool else 0
            weight = odl.tool.peso if odl.tool else 0
            odl_info = ODLNestingInfo(
                id=odl.id,
                parte_codice=odl.parte.part_number if odl.parte else None,
                tool_nome=odl.tool.part_number_tool if odl.tool else None,
                priorita=odl.priorita,
                dimensioni={
                    "larghezza": width,
                    "lunghezza": length,
                    "peso": weight
                },
                ciclo_cura=f"{odl.parte.catalogo.categoria}_{odl.parte.catalogo.sotto_categoria}" if odl.parte and odl.parte.catalogo else None,
                status=odl.status
            )
            odl_inclusi_info.append(odl_info)
        
        # Converte gli ODL esclusi
        odl_esclusi_info = []
        for odl in odl_esclusi:
            width = odl.tool.larghezza_piano if odl.tool else 0
            length = odl.tool.lunghezza_piano if odl.tool else 0
            weight = odl.tool.peso if odl.tool else 0
            odl_info = ODLNestingInfo(
                id=odl.id,
                parte_codice=odl.parte.part_number if odl.parte else None,
                tool_nome=odl.tool.part_number_tool if odl.tool else None,
                priorita=odl.priorita,
                dimensioni={
                    "larghezza": width,
                    "lunghezza": length,
                    "peso": weight
                },
                ciclo_cura=f"{odl.parte.catalogo.categoria}_{odl.parte.catalogo.sotto_categoria}" if odl.parte and odl.parte.catalogo else None,
                status=odl.status
            )
            odl_esclusi_info.append(odl_info)
        
        # Informazioni autoclave
        autoclave_info = AutoclaveNestingInfo(
            id=autoclave.id,
            nome=autoclave.nome,
            area_piano=autoclave.area_piano,
            max_load_kg=autoclave.max_load_kg,
            stato=autoclave.stato.value
        )
        
        # Statistiche
        statistiche = {
            "area_utilizzata": nesting.area_utilizzata,
            "area_totale": nesting.area_totale,
            "efficienza": nesting.efficienza_totale,
            "peso_totale": nesting.peso_totale_kg,
            "valvole_utilizzate": nesting.valvole_utilizzate,
            "valvole_totali": nesting.valvole_totali
        }
        
        return NestingDetailResponse(
            id=nesting.id,
            autoclave=autoclave_info,
            odl_inclusi=odl_inclusi_info,
            odl_esclusi=odl_esclusi_info,
            motivi_esclusione=nesting.motivi_esclusione or [],
            statistiche=statistiche,
            stato=nesting.stato,
            note=nesting.note,
            created_at=nesting.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero dei dettagli: {str(e)}")


@router.put("/{nesting_id}/status", response_model=NestingDetailResponse)
async def update_nesting_status(
    nesting_id: int, 
    status_update: NestingStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Aggiorna lo stato di un nesting specifico e sincronizza automaticamente
    gli stati degli ODL e dell'autoclave associata.
    
    🔄 SINCRONIZZAZIONE AUTOMATICA:
    - "Confermato" → ODL rimangono "Attesa Cura"
    - "Caricato" → ODL → "Cura", Autoclave → "IN_USO"  
    - "Finito" → ODL → "Finito", Autoclave → "DISPONIBILE"
    
    Args:
        nesting_id: ID del nesting da aggiornare
        status_update: Nuovi dati di stato
        db: Sessione del database
        
    Returns:
        NestingDetailResponse: Dettagli aggiornati del nesting
    """
    try:
        from services.nesting_state_sync_service import NestingStateSyncService
        from datetime import datetime
        
        # Recupera il nesting con tutte le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(status_code=404, detail="Nesting non trovato")
        
        stato_precedente = nesting.stato
        nuovo_stato = status_update.stato
        responsabile = status_update.confermato_da_ruolo or "sistema"
        
        # Validazione transizione usando il servizio
        if not NestingStateSyncService.validate_state_transition(stato_precedente, nuovo_stato):
            transizioni_valide = NestingStateSyncService.get_valid_transitions(stato_precedente)
            raise HTTPException(
                status_code=400,
                detail=f"Transizione non valida da '{stato_precedente}' a '{nuovo_stato}'. "
                       f"Transizioni permesse: {transizioni_valide}"
            )
        
        # Aggiungi note se fornite
        if status_update.note:
            note_esistenti = nesting.note or ""
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nota_aggiornamento = f"[{timestamp_str}] Stato aggiornato a '{nuovo_stato}': {status_update.note}"
            
            if note_esistenti:
                nesting.note = f"{note_esistenti}\n{nota_aggiornamento}"
            else:
                nesting.note = nota_aggiornamento
        
        # 🔄 SINCRONIZZAZIONE AUTOMATICA usando il servizio dedicato
        risultato_sync = NestingStateSyncService.sync_nesting_state_change(
            db=db,
            nesting=nesting,
            nuovo_stato=nuovo_stato,
            responsabile=responsabile,
            note=status_update.note
        )
        
        # Salva tutte le modifiche
        db.commit()
        db.refresh(nesting)
        
        # Log del risultato della sincronizzazione
        logger.info(f"✅ Nesting {nesting_id}: sincronizzazione completata")
        logger.info(f"   📊 ODL aggiornati: {len(risultato_sync.get('odl_aggiornati', []))}")
        logger.info(f"   🏭 Autoclave aggiornata: {risultato_sync.get('autoclave_aggiornata', False)}")
        logger.info(f"   ⏱️ Fasi temporali aggiornate: {len(risultato_sync.get('fasi_temporali_aggiornate', []))}")
        
        # Ritorna i dettagli aggiornati
        return await get_nesting_details(nesting_id, db)
        
    except HTTPException:
        raise
    except ValueError as e:
        # Errori di validazione dal servizio
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante l'aggiornamento stato nesting {nesting_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore durante l'aggiornamento dello stato: {str(e)}")


# ✅ NUOVO: Endpoint per la visualizzazione grafica del nesting
@router.get("/{nesting_id}/layout", response_model=NestingLayoutResponse)
async def get_nesting_layout(
    nesting_id: int,
    padding_mm: float = 10.0,
    borda_mm: float = 20.0,
    rotazione_abilitata: bool = True,
    db: Session = Depends(get_db)
):
    """
    Ottiene i dati per la visualizzazione grafica del layout di un nesting specifico.
    
    Args:
        nesting_id: ID del nesting
        padding_mm: Spaziatura tra tool in mm
        borda_mm: Bordo dall'autoclave in mm
        rotazione_abilitata: Se abilitare la rotazione automatica
        db: Sessione del database
        
    Returns:
        NestingLayoutResponse: Dati per la visualizzazione del layout
    """
    try:
        # Recupera il nesting con tutte le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(status_code=404, detail="Nesting non trovato")
        
        # Converte in dati di layout
        layout_data = NestingLayoutService.convert_nesting_to_layout_data(
            nesting, padding_mm, borda_mm, rotazione_abilitata
        )
        
        return NestingLayoutResponse(
            success=True,
            message=f"Layout del nesting {nesting_id} recuperato con successo",
            layout_data=layout_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero del layout: {str(e)}")


@router.get("/layouts/all", response_model=MultiNestingLayoutResponse)
async def get_all_nesting_layouts(
    limit: Optional[int] = None,
    stato_filtro: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Ottiene i dati di layout per tutti i nesting disponibili.
    
    Args:
        limit: Numero massimo di nesting da recuperare
        stato_filtro: Filtra per stato specifico
        db: Sessione del database
        
    Returns:
        MultiNestingLayoutResponse: Dati di layout per tutti i nesting
    """
    try:
        layout_data = NestingLayoutService.get_multi_nesting_layout_data(
            db, limit, stato_filtro
        )
        
        return MultiNestingLayoutResponse(
            success=True,
            message=f"Layout di {len(layout_data.nesting_list)} nesting recuperati con successo",
            layout_data=layout_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero dei layout: {str(e)}")


@router.post("/calculate-orientation", response_model=OrientationCalculationResponse)
async def calculate_tool_orientation(request: OrientationCalculationRequest):
    """
    Calcola l'orientamento ottimale per un tool in base alle dimensioni dell'autoclave.
    
    Args:
        request: Richiesta con dimensioni del tool e dell'autoclave
        
    Returns:
        OrientationCalculationResponse: Risultato del calcolo dell'orientamento
    """
    try:
        # Calcola l'efficienza per orientamento normale
        normal_efficiency = (request.tool_length * request.tool_width) / (request.autoclave_length * request.autoclave_width) * 100
        
        # Calcola l'efficienza per orientamento ruotato
        rotated_efficiency = (request.tool_width * request.tool_length) / (request.autoclave_length * request.autoclave_width) * 100
        
        # Determina se conviene ruotare
        should_rotate = rotated_efficiency > normal_efficiency
        improvement_percentage = abs(rotated_efficiency - normal_efficiency)
        
        return OrientationCalculationResponse(
            should_rotate=should_rotate,
            normal_efficiency=normal_efficiency,
            rotated_efficiency=rotated_efficiency,
            improvement_percentage=improvement_percentage,
            recommended_orientation="ruotato" if should_rotate else "normale"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel calcolo dell'orientamento: {str(e)}")


@router.post("/{nesting_id}/confirm", response_model=NestingDetailResponse)
async def confirm_nesting(
    nesting_id: int,
    confermato_da_ruolo: str = "operatore",
    note_conferma: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Conferma un nesting cambiando il suo stato a "in sospeso".
    
    Questo endpoint viene utilizzato per confermare un nesting che è stato generato
    automaticamente o creato manualmente, passandolo dallo stato "Bozza" a "In sospeso".
    
    Args:
        nesting_id: ID del nesting da confermare
        confermato_da_ruolo: Ruolo dell'utente che conferma (default: "operatore")
        note_conferma: Note aggiuntive per la conferma
        db: Sessione del database
        
    Returns:
        NestingDetailResponse: Dettagli del nesting confermato
    """
    try:
        # Recupera il nesting dal database
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(status_code=404, detail=f"Nesting con ID {nesting_id} non trovato")
        
        # Verifica che il nesting sia in uno stato confermabile
        if nesting.stato not in ["Bozza", "Creato"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Il nesting è nello stato '{nesting.stato}' e non può essere confermato. "
                       f"Solo i nesting in stato 'Bozza' o 'Creato' possono essere confermati."
            )
        
        # Aggiorna lo stato del nesting
        nesting.stato = "In sospeso"
        nesting.confermato_da_ruolo = confermato_da_ruolo
        
        # Aggiungi note di conferma se fornite
        if note_conferma:
            note_esistenti = nesting.note or ""
            timestamp_conferma = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nota_conferma = f"[{timestamp_conferma}] Confermato da {confermato_da_ruolo}: {note_conferma}"
            
            if note_esistenti:
                nesting.note = f"{note_esistenti}\n{nota_conferma}"
            else:
                nesting.note = nota_conferma
        
        # Salva le modifiche
        db.commit()
        db.refresh(nesting)
        
        # Prepara la risposta con i dettagli del nesting confermato
        # Recupera l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == nesting.autoclave_id).first()
        if not autoclave:
            raise HTTPException(status_code=500, detail="Autoclave associata non trovata")
        
        # Recupera gli ODL inclusi
        odl_inclusi = []
        if nesting.odl_ids:
            odl_query = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids))
            odl_inclusi = odl_query.all()
        
        # Recupera gli ODL esclusi
        odl_esclusi = []
        if nesting.odl_esclusi_ids:
            odl_esclusi_query = db.query(ODL).filter(ODL.id.in_(nesting.odl_esclusi_ids))
            odl_esclusi = odl_esclusi_query.all()
        
        # Costruisci la risposta
        response = NestingDetailResponse(
            id=nesting.id,
            autoclave=AutoclaveNestingInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                area_piano=autoclave.lunghezza * autoclave.larghezza_piano / 100,  # Converti in cm²
                max_load_kg=autoclave.max_load_kg,
                stato=autoclave.stato.value
            ),
            odl_inclusi=[
                ODLNestingInfo(
                    id=odl.id,
                    parte_codice=odl.parte.part_number if odl.parte else None,
                    tool_nome=odl.tool.part_number_tool if odl.tool else None,
                    priorita=odl.priorita,
                    dimensioni={
                        "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                        "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                        "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                    },
                    ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                    status=odl.status
                ) for odl in odl_inclusi
            ],
            odl_esclusi=[
                ODLNestingInfo(
                    id=odl.id,
                    parte_codice=odl.parte.part_number if odl.parte else None,
                    tool_nome=odl.tool.part_number_tool if odl.tool else None,
                    priorita=odl.priorita,
                    dimensioni={
                        "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                        "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                        "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                    },
                    ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                    status=odl.status
                ) for odl in odl_esclusi
            ],
            motivi_esclusione=nesting.motivi_esclusione or [],
            statistiche={
                "area_utilizzata": nesting.area_utilizzata,
                "area_totale": nesting.area_totale,
                "efficienza": (nesting.area_utilizzata / nesting.area_totale * 100) if nesting.area_totale > 0 else 0,
                "peso_totale": nesting.peso_totale_kg,
                "valvole_utilizzate": nesting.valvole_utilizzate,
                "valvole_totali": nesting.valvole_totali
            },
            stato=nesting.stato,
            note=nesting.note,
            created_at=nesting.created_at
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante la conferma del nesting: {str(e)}")


@router.post("/{nesting_id}/load", response_model=NestingDetailResponse)
async def load_nesting(
    nesting_id: int,
    caricato_da_ruolo: str = "curing",
    note_caricamento: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Carica un nesting nell'autoclave cambiando:
    - Stato del nesting a "Caricato"
    - Stato degli ODL inclusi a "Cura"
    - Stato dell'autoclave a "IN_USO"
    
    Questo endpoint viene utilizzato per avviare il processo di cura dopo che
    il nesting è stato confermato e gli ODL sono stati fisicamente caricati nell'autoclave.
    
    Args:
        nesting_id: ID del nesting da caricare
        caricato_da_ruolo: Ruolo dell'utente che carica (default: "curing")
        note_caricamento: Note aggiuntive per il caricamento
        db: Sessione del database
        
    Returns:
        NestingDetailResponse: Dettagli del nesting caricato
    """
    try:
        # from services.system_log_service import SystemLogService
        from services.state_tracking_service import StateTrackingService
        from models.system_log import UserRole
        from models.odl_log import ODLLog
        
        # Recupera il nesting dal database
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(status_code=404, detail=f"Nesting con ID {nesting_id} non trovato")
        
        # Verifica che il nesting sia in uno stato caricabile
        if nesting.stato not in ["In sospeso", "Confermato"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Il nesting è nello stato '{nesting.stato}' e non può essere caricato. "
                       f"Solo i nesting in stato 'In sospeso' o 'Confermato' possono essere caricati."
            )
        
        # Recupera l'autoclave associata
        autoclave = db.query(Autoclave).filter(Autoclave.id == nesting.autoclave_id).first()
        if not autoclave:
            raise HTTPException(status_code=500, detail="Autoclave associata non trovata")
        
        # Verifica che l'autoclave sia disponibile
        if autoclave.stato != StatoAutoclaveEnum.DISPONIBILE:
            raise HTTPException(
                status_code=400,
                detail=f"L'autoclave '{autoclave.nome}' è nello stato '{autoclave.stato.value}' e non può essere utilizzata. "
                       f"Solo le autoclavi 'DISPONIBILI' possono essere caricate."
            )
        
        # Recupera gli ODL inclusi nel nesting
        if not nesting.odl_ids:
            raise HTTPException(status_code=400, detail="Il nesting non contiene ODL da caricare")
        
        odl_inclusi = db.query(ODL).filter(ODL.id.in_(nesting.odl_ids)).all()
        
        # Verifica che tutti gli ODL siano in stato "Attesa Cura"
        odl_non_pronti = [odl for odl in odl_inclusi if odl.status != "Attesa Cura"]
        if odl_non_pronti:
            odl_ids_non_pronti = [str(odl.id) for odl in odl_non_pronti]
            raise HTTPException(
                status_code=400,
                detail=f"Gli ODL {', '.join(odl_ids_non_pronti)} non sono in stato 'Attesa Cura' e non possono essere caricati"
            )
        
        timestamp_caricamento = datetime.now()
        
        # 1. Aggiorna lo stato del nesting
        nesting.stato = "Caricato"
        
        # Aggiungi note di caricamento se fornite
        if note_caricamento:
            note_esistenti = nesting.note or ""
            timestamp_str = timestamp_caricamento.strftime("%Y-%m-%d %H:%M:%S")
            nota_caricamento = f"[{timestamp_str}] Caricato da {caricato_da_ruolo}: {note_caricamento}"
            
            if note_esistenti:
                nesting.note = f"{note_esistenti}\n{nota_caricamento}"
            else:
                nesting.note = nota_caricamento
        
        # 2. Aggiorna lo stato dell'autoclave a "IN_USO"
        stato_precedente_autoclave = autoclave.stato
        autoclave.stato = StatoAutoclaveEnum.IN_USO
        
        # 3. Aggiorna lo stato di tutti gli ODL inclusi a "Cura"
        odl_aggiornati = []
        for odl in odl_inclusi:
            stato_precedente_odl = odl.status
            odl.status = "Cura"
            odl.previous_status = stato_precedente_odl
            
            # Registra il cambio di stato dell'ODL
            StateTrackingService.registra_cambio_stato(
                db=db,
                odl_id=odl.id,
                stato_precedente=stato_precedente_odl,
                stato_nuovo="Cura",
                responsabile=caricato_da_ruolo,
                ruolo_responsabile="curing",
                note=f"ODL caricato in autoclave {autoclave.nome} tramite nesting {nesting_id}"
            )
            
            # Crea un log specifico per il caricamento
            odl_log = ODLLog(
                odl_id=odl.id,
                evento="caricato_autoclave",
                stato_precedente=stato_precedente_odl,
                stato_nuovo="Cura",
                descrizione=f"ODL caricato in autoclave {autoclave.nome} tramite nesting {nesting_id}",
                responsabile=caricato_da_ruolo,
                nesting_id=nesting_id,
                autoclave_id=autoclave.id
            )
            db.add(odl_log)
            
            # Gestione delle fasi temporali
            from models.tempo_fase import TempoFase
            
            # Chiudi la fase "attesa_cura" se attiva
            fase_attesa = db.query(TempoFase).filter(
                TempoFase.odl_id == odl.id,
                TempoFase.fase == "attesa_cura",
                TempoFase.fine_fase == None
            ).first()
            
            if fase_attesa:
                durata = int((timestamp_caricamento - fase_attesa.inizio_fase).total_seconds() / 60)
                fase_attesa.fine_fase = timestamp_caricamento
                fase_attesa.durata_minuti = durata
                fase_attesa.note = f"{fase_attesa.note or ''} - Fase completata con caricamento in autoclave"
            
            # Apri la fase "cura"
            nuova_fase_cura = TempoFase(
                odl_id=odl.id,
                fase="cura",
                inizio_fase=timestamp_caricamento,
                note=f"Fase cura iniziata con caricamento in autoclave {autoclave.nome}"
            )
            db.add(nuova_fase_cura)
            
            odl_aggiornati.append(odl)
        
        # Salva tutte le modifiche
        db.commit()
        db.refresh(nesting)
        db.refresh(autoclave)
        
        # Prepara la risposta con i dettagli aggiornati
        response = NestingDetailResponse(
            id=nesting.id,
            autoclave=AutoclaveNestingInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                area_piano=autoclave.lunghezza * autoclave.larghezza_piano / 100,
                max_load_kg=autoclave.max_load_kg,
                stato=autoclave.stato.value
            ),
            odl_inclusi=[
                ODLNestingInfo(
                    id=odl.id,
                    parte_codice=odl.parte.part_number if odl.parte else None,
                    tool_nome=odl.tool.part_number_tool if odl.tool else None,
                    priorita=odl.priorita,
                    dimensioni={
                        "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                        "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                        "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                    },
                    ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                    status=odl.status
                ) for odl in odl_aggiornati
            ],
            odl_esclusi=[],  # Gli esclusi rimangono invariati
            motivi_esclusione=nesting.motivi_esclusione or [],
            statistiche={
                "area_utilizzata": nesting.area_utilizzata,
                "area_totale": nesting.area_totale,
                "efficienza": (nesting.area_utilizzata / nesting.area_totale * 100) if nesting.area_totale > 0 else 0,
                "peso_totale": nesting.peso_totale_kg,
                "valvole_utilizzate": nesting.valvole_utilizzate,
                "valvole_totali": nesting.valvole_totali
            },
            stato=nesting.stato,
            note=nesting.note,
            created_at=nesting.created_at
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore durante il caricamento del nesting: {str(e)}")


@router.post("/{nesting_id}/generate-report")
async def generate_nesting_report(
    nesting_id: int,
    force_regenerate: bool = Query(False, description="Forza la rigenerazione anche se esiste già un report"),
    db: Session = Depends(get_db)
):
    """
    Genera un report PDF per un nesting specifico.
    
    Questo endpoint crea un report PDF dettagliato che include:
    - Informazioni generali del nesting (ID, data, stato)
    - Dettagli dell'autoclave utilizzata
    - Lista degli ODL inclusi con Part Number e descrizioni
    - Informazioni sui tool utilizzati (dimensioni, peso, materiale)
    - Cicli di cura applicati
    - Statistiche di utilizzo dei piani
    - Layout visivo del nesting
    - Tempi previsti e effettivi
    
    Args:
        nesting_id: ID del nesting per cui generare il report
        force_regenerate: Se True, rigenera il report anche se esiste già
        db: Sessione del database
        
    Returns:
        Informazioni sul report generato con possibilità di download
    """
    try:
        from services.nesting_report_generator import NestingReportGenerator
        from models.report import Report
        
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=404, 
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Controlla se esiste già un report
        if nesting.report_id and not force_regenerate:
            existing_report = db.query(Report).filter(Report.id == nesting.report_id).first()
            if existing_report and os.path.exists(existing_report.file_path):
                return {
                    "success": True,
                    "message": "Report già esistente per questo nesting",
                    "report_id": existing_report.id,
                    "filename": existing_report.filename,
                    "file_path": existing_report.file_path,
                    "created_at": existing_report.created_at,
                    "download_url": f"/api/reports/nesting/{nesting_id}/download"
                }
        
        # Inizializza il generatore di report
        report_generator = NestingReportGenerator(db)
        
        # Genera il report PDF
        result = report_generator.generate_nesting_report(nesting_id)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Errore durante la generazione del report"
            )
        
        file_path, report_record = result
        
        return {
            "success": True,
            "message": f"Report PDF generato con successo per il nesting {nesting_id}",
            "report_id": report_record.id,
            "filename": report_record.filename,
            "file_path": file_path,
            "file_size_bytes": report_record.file_size_bytes,
            "created_at": report_record.created_at,
            "download_url": f"/api/reports/nesting/{nesting_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante la generazione del report: {str(e)}"
        )


@router.post("/auto-multiple", response_model=AutomaticNestingResponse)
async def generate_auto_multiple_nesting(
    request: AutomaticNestingRequestWithParams = AutomaticNestingRequestWithParams(),
    db: Session = Depends(get_db)
):
    """
    Endpoint fallback per il nesting automatico multiplo.
    
    Questo endpoint è un placeholder per la funzionalità multi-nesting.
    Attualmente reindirizza al sistema multi-nesting esistente.
    
    Args:
        request: Parametri per la generazione automatica
        db: Sessione del database
        
    Returns:
        AutomaticNestingResponse: Risultato della generazione automatica
    """
    try:
        logger.info("🔄 Fallback: auto-multiple reindirizzato a multi-nesting API")
        
        # Questo è un fallback che reindirizza al sistema multi-nesting
        return AutomaticNestingResponse(
            success=False,
            message="⚠️ Endpoint auto-multiple non ancora implementato. Utilizza /api/multi-nesting/preview-batch",
            nesting_results=[],
            summary={
                "note": "Fallback attivo",
                "endpoint_alternativo": "/api/multi-nesting/preview-batch",
                "componente_frontend": "MultiBatchNesting.tsx disponibile",
                "stato": "Da implementare nel backend"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Errore nel fallback auto-multiple: {e}")
        raise HTTPException(
            status_code=501, 
            detail=f"Endpoint auto-multiple non implementato. Usa multi-nesting API. Errore: {str(e)}"
        )


@router.post("/{nesting_id}/regenerate")
async def regenerate_nesting(
    nesting_id: int,
    force_regenerate: bool = Query(True, description="Forza la rigenerazione del nesting"),
    db: Session = Depends(get_db)
):
    """
    Rigenera un nesting esistente con gli stessi parametri.
    
    Questo endpoint permette di rigenerare un nesting esistente, mantenendo
    gli stessi ODL e parametri di ottimizzazione, ma ricalcolando il layout
    e le posizioni ottimali dei tool.
    
    Args:
        nesting_id: ID del nesting da rigenerare
        force_regenerate: Se True, procede con la rigenerazione indipendentemente dallo stato
        db: Sessione del database
        
    Returns:
        Informazioni sulla rigenerazione effettuata
    """
    try:
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=404, 
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Verifica che il nesting sia in uno stato rigenerabile
        stati_rigenerabili = ["Bozza", "bozza", "Errore", "errore"]
        if nesting.stato not in stati_rigenerabili and not force_regenerate:
            raise HTTPException(
                status_code=400,
                detail=f"Impossibile rigenerare nesting nello stato '{nesting.stato}'. "
                      f"Stati consentiti: {stati_rigenerabili}. Usa force_regenerate=true per forzare."
            )
        
        # Ottieni gli ODL associati al nesting originale
        odl_inclusi = nesting.odl_list  # Usa la relazione many-to-many
        
        if not odl_inclusi:
            raise HTTPException(
                status_code=400,
                detail="Nessun ODL associato al nesting. Impossibile rigenerare."
            )
        
        # Salva l'autoclave originale per mantenere la stessa configurazione
        autoclave_originale = nesting.autoclave
        if not autoclave_originale:
            raise HTTPException(
                status_code=400,
                detail="Autoclave originale non trovata. Impossibile rigenerare."
            )
        
        # Reset degli ODL: riportali in stato "Attesa Cura"
        for odl in odl_inclusi:
            if odl.status in ["Cura", "Finito"]:
                # Per ODL già avanzati, mantieni lo stato se force_regenerate=False
                if not force_regenerate:
                    continue
            
            # Reset dello stato dell'ODL
            odl.status = "Attesa Cura"
            # Rimuovi dalla relazione many-to-many temporaneamente
            nesting.odl_list.remove(odl)
        
        # Reset dello stato dell'autoclave se necessario
        if autoclave_originale.stato == "IN_USO" and force_regenerate:
            autoclave_originale.stato = "DISPONIBILE"
        
        # Rigenera il nesting utilizzando l'algoritmo di ottimizzazione
        try:
            from nesting_optimizer.auto_nesting import NestingOptimizer
            
            optimizer = NestingOptimizer(db)
            
            # Prepara i parametri per la rigenerazione
            odl_da_processare = [odl.id for odl in odl_inclusi]
            
            # Chiama l'algoritmo di ottimizzazione per gli ODL specifici
            nuovo_risultato = optimizer.optimize_for_autoclave(
                autoclave_id=autoclave_originale.id,
                odl_ids=odl_da_processare,
                force_regenerate=True
            )
            
            if not nuovo_risultato:
                raise HTTPException(
                    status_code=500,
                    detail="Algoritmo di ottimizzazione non è riuscito a rigenerare il nesting"
                )
            
            # Aggiorna il nesting esistente con i nuovi risultati
            nesting.stato = "Bozza"  # Reset allo stato bozza
            nesting.area_utilizzata = nuovo_risultato.get('area_utilizzata', nesting.area_utilizzata)
            nesting.area_totale = nuovo_risultato.get('area_totale', nesting.area_totale)
            nesting.peso_totale_kg = nuovo_risultato.get('peso_totale', nesting.peso_totale_kg)
            nesting.valvole_utilizzate = nuovo_risultato.get('valvole_utilizzate', nesting.valvole_utilizzate)
            nesting.valvole_totali = nuovo_risultato.get('valvole_totali', nesting.valvole_totali)
            nesting.note = f"{nesting.note or ''} - Rigenerato il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Ricollega gli ODL al nesting rigenerato
            for odl in odl_inclusi:
                nesting.odl_list.append(odl)
            
        except Exception as opt_error:
            # In caso di errore nell'ottimizzazione, usa una strategia di fallback
            logger.warning(f"⚠️ Errore nell'ottimizzazione, uso fallback: {opt_error}")
            
            # Fallback: mantieni la configurazione esistente ma reset lo stato
            nesting.stato = "Bozza"
            nesting.note = f"{nesting.note or ''} - Rigenerato (fallback) il {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Ricollega gli ODL
            for odl in odl_inclusi:
                nesting.odl_list.append(odl)
                odl.status = "Attesa Cura"
        
        # Salva tutte le modifiche
        db.commit()
        db.refresh(nesting)
        
        logger.info(f"✅ Nesting {nesting_id} rigenerato con successo")
        
        return {
            "success": True,
            "message": f"Nesting {nesting_id} rigenerato con successo",
            "nesting_id": nesting_id,
            "stato": nesting.stato,
            "odl_count": len(odl_inclusi),
            "autoclave": autoclave_originale.nome,
            "efficienza": nesting.efficienza,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante la rigenerazione del nesting {nesting_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante la rigenerazione del nesting: {str(e)}"
        )


@router.delete("/{nesting_id}")
async def delete_nesting(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina definitivamente un nesting dal database.
    
    Questo endpoint rimuove completamente un nesting e tutte le sue
    associazioni, liberando gli ODL collegati e ripristinando lo stato
    dell'autoclave se necessario.
    
    ATTENZIONE: Questa operazione è irreversibile!
    
    Args:
        nesting_id: ID del nesting da eliminare
        db: Sessione del database
        
    Returns:
        Conferma dell'eliminazione avvenuta
    """
    try:
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(
                status_code=404, 
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Verifica che il nesting sia in uno stato eliminabile
        stati_eliminabili = ["Bozza", "bozza", "Errore", "errore"]
        if nesting.stato not in stati_eliminabili:
            raise HTTPException(
                status_code=400,
                detail=f"Impossibile eliminare nesting nello stato '{nesting.stato}'. "
                      f"Solo i nesting negli stati {stati_eliminabili} possono essere eliminati. "
                      f"Per nesting in altri stati, contatta l'amministratore."
            )
        
        # Ottieni informazioni sul nesting prima dell'eliminazione (per il log)
        autoclave_nome = nesting.autoclave.nome if nesting.autoclave else "Non specificata"
        stato_originale = nesting.stato
        note_originali = nesting.note
        
        # Libera gli ODL associati al nesting
        odl_collegati = nesting.odl_list  # Usa la relazione many-to-many
        
        odl_liberati = []
        for odl in odl_collegati:
            # Reset dello stato dell'ODL a "Attesa Cura"
            stato_precedente = odl.status
            odl.status = "Attesa Cura"
            # Rimuovi l'associazione al nesting tramite la relazione many-to-many
            nesting.odl_list.remove(odl)
            
            odl_liberati.append({
                "id": odl.id,
                "parte": odl.parte.part_number if odl.parte else "N/A",
                "tool": odl.tool.part_number_tool if odl.tool else "N/A",
                "stato_precedente": stato_precedente,
                "stato_nuovo": "Attesa Cura"
            })
        
        # Libera l'autoclave se era associata e in uso per questo nesting
        autoclave = nesting.autoclave
        if autoclave and autoclave.stato == "IN_USO":
            # Verifica se questa autoclave ha altri nesting attivi
            altri_nesting_attivi = db.query(NestingResult).filter(
                NestingResult.autoclave_id == autoclave.id,
                NestingResult.id != nesting_id,
                NestingResult.stato.in_(["Cura", "cura", "Caricato", "caricato"])
            ).count()
            
            if altri_nesting_attivi == 0:
                # Nessun altro nesting attivo, libera l'autoclave
                autoclave.stato = "DISPONIBILE"
                logger.info(f"🔓 Autoclave {autoclave.nome} liberata dopo eliminazione nesting {nesting_id}")
        
        # Gestione dei report associati (se presenti)
        if nesting.report_id:
            try:
                from models.report import Report
                report = db.query(Report).filter(Report.id == nesting.report_id).first()
                if report:
                    # Rimuovi il file fisico se esiste
                    if os.path.exists(report.file_path):
                        os.remove(report.file_path)
                        logger.info(f"🗑️ File report rimosso: {report.file_path}")
                    
                    # Elimina il record del report
                    db.delete(report)
                    logger.info(f"🗑️ Report {report.id} eliminato dal database")
            except Exception as report_error:
                logger.warning(f"⚠️ Errore nella rimozione del report: {report_error}")
                # Non bloccare l'eliminazione del nesting per errori del report
        
        # Elimina il nesting dal database
        db.delete(nesting)
        
        # Commit di tutte le modifiche
        db.commit()
        
        logger.info(f"🗑️ Nesting {nesting_id} eliminato definitivamente")
        
        return {
            "success": True,
            "message": f"Nesting {nesting_id} eliminato definitivamente",
            "nesting_eliminato": {
                "id": nesting_id,
                "stato_originale": stato_originale,
                "autoclave": autoclave_nome,
                "note_originali": note_originali
            },
            "odl_liberati": odl_liberati,
            "autoclave_liberata": autoclave.nome if autoclave and autoclave.stato == "DISPONIBILE" else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante l'eliminazione del nesting {nesting_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante l'eliminazione del nesting: {str(e)}"
        ) 


@router.get("/{nesting_id}/tools", response_model=NestingToolsResponse)
async def get_nesting_tools(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Recupera la lista dettagliata dei tool inclusi in un nesting specifico.
    
    Questo endpoint supporta lo Step 2 semplificato del nesting manuale,
    fornendo tutte le informazioni sui tool derivati dagli ODL associati.
    
    Args:
        nesting_id: ID del nesting di cui recuperare i tool
        db: Sessione del database
        
    Returns:
        NestingToolsResponse: Lista dettagliata dei tool con statistiche
    """
    try:
        # Recupera il nesting con tutte le relazioni
        nesting = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte)
        ).filter(NestingResult.id == nesting_id).first()
        
        if not nesting:
            raise HTTPException(
                status_code=404, 
                detail=f"Nesting con ID {nesting_id} non trovato"
            )
        
        # Verifica che il nesting abbia ODL associati
        if not nesting.odl_list:
            return NestingToolsResponse(
                success=True,
                message="Nessun ODL associato al nesting",
                nesting_id=nesting_id,
                autoclave_nome=nesting.autoclave.nome if nesting.autoclave else None,
                tools=[],
                statistiche_tools={
                    "totale_tools": 0,
                    "peso_totale": 0.0,
                    "area_totale": 0.0,
                    "tools_disponibili": 0,
                    "tools_non_disponibili": 0
                }
            )
        
        # Costruisce la lista dei tool
        tools_info = []
        peso_totale = 0.0
        area_totale = 0.0
        tools_disponibili = 0
        tools_non_disponibili = 0
        
        for odl in nesting.odl_list:
            if not odl.tool:
                logger.warning(f"ODL {odl.id} non ha un tool associato")
                continue
            
            tool = odl.tool
            
            # Calcola area del tool
            area_tool = (tool.lunghezza_piano * tool.larghezza_piano) / 100  # da mm² a cm²
            peso_tool = tool.peso or 0.0
            
            tool_info = NestingToolInfo(
                id=tool.id,
                part_number_tool=tool.part_number_tool,
                descrizione=tool.descrizione,
                dimensioni={
                    "larghezza": tool.larghezza_piano,
                    "lunghezza": tool.lunghezza_piano
                },
                peso=peso_tool,
                materiale=tool.materiale,
                disponibile=tool.disponibile,
                area_cm2=round(area_tool, 2),
                odl_id=odl.id,
                parte_codice=odl.parte.part_number if odl.parte else "N/A",
                priorita=odl.priorita
            )
            
            tools_info.append(tool_info)
            
            # Aggiorna statistiche
            peso_totale += peso_tool
            area_totale += area_tool
            
            if tool.disponibile:
                tools_disponibili += 1
            else:
                tools_non_disponibili += 1
        
        # Statistiche finali
        statistiche = {
            "totale_tools": len(tools_info),
            "peso_totale": round(peso_totale, 2),
            "area_totale": round(area_totale, 2),
            "tools_disponibili": tools_disponibili,
            "tools_non_disponibili": tools_non_disponibili,
            "efficienza_area": round((area_totale / nesting.area_totale * 100), 2) if nesting.area_totale > 0 else 0.0
        }
        
        return NestingToolsResponse(
            success=True,
            message=f"Recuperati {len(tools_info)} tool per il nesting {nesting_id}",
            nesting_id=nesting_id,
            autoclave_nome=nesting.autoclave.nome if nesting.autoclave else None,
            tools=tools_info,
            statistiche_tools=statistiche
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore durante il recupero dei tool per il nesting {nesting_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante il recupero dei tool: {str(e)}"
        )


@router.put("/{nesting_id}/layout/positions")
async def save_tool_positions(
    nesting_id: int,
    positions: List[ToolPosition],
    db: Session = Depends(get_db)
):
    """
    Salva le posizioni aggiornate dei tool nel nesting dopo drag and drop.
    
    Args:
        nesting_id: ID del nesting
        positions: Lista delle nuove posizioni dei tool
        db: Sessione database
        
    Returns:
        Conferma del salvataggio con statistiche aggiornate
    """
    try:
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(status_code=404, detail=f"Nesting con ID {nesting_id} non trovato")
        
        # Verifica che sia modificabile
        if nesting.stato in ["confermato", "in_autoclave", "completato"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Impossibile modificare le posizioni: nesting in stato '{nesting.stato}'"
            )
        
        # Valida le posizioni
        if not positions:
            raise HTTPException(status_code=400, detail="Lista posizioni non può essere vuota")
        
        # Verifica che tutti gli ODL appartengano al nesting
        nesting_odl_ids = set(nesting.odl_ids or [])
        position_odl_ids = set(pos.odl_id for pos in positions)
        
        if not position_odl_ids.issubset(nesting_odl_ids):
            invalid_ids = position_odl_ids - nesting_odl_ids
            raise HTTPException(
                status_code=400, 
                detail=f"ODL non appartenenti al nesting: {list(invalid_ids)}"
            )
        
        # Converte posizioni in formato JSON
        positions_json = []
        area_piano_1 = 0.0
        area_piano_2 = 0.0
        
        for pos in positions:
            # Calcola area utilizzata per piano
            tool_area = pos.width * pos.height / 100  # Converte mm² in cm²
            if pos.piano == 1:
                area_piano_1 += tool_area
            elif pos.piano == 2:
                area_piano_2 += tool_area
            
            positions_json.append({
                "odl_id": pos.odl_id,
                "x": pos.x,
                "y": pos.y,
                "width": pos.width,
                "height": pos.height,
                "rotated": pos.rotated,
                "piano": pos.piano
            })
        
        # Aggiorna il nesting
        nesting.posizioni_tool = positions_json
        nesting.area_piano_1 = area_piano_1
        nesting.area_piano_2 = area_piano_2
        nesting.area_utilizzata = area_piano_1 + area_piano_2
        
        # Ricalcola efficienza totale
        area_totale_disponibile = nesting.area_totale + (nesting.superficie_piano_2_max or 0)
        if area_totale_disponibile > 0:
            efficienza_totale = (nesting.area_utilizzata / area_totale_disponibile) * 100
        else:
            efficienza_totale = 0.0
        
        db.commit()
        
        logger.info(f"✅ Posizioni aggiornate per nesting {nesting_id}: {len(positions)} tool posizionati")
        
        return {
            "success": True,
            "message": f"Posizioni salvate con successo per {len(positions)} tool",
            "nesting_id": nesting_id,
            "statistiche": {
                "tools_posizionati": len(positions),
                "area_piano_1": round(area_piano_1, 2),
                "area_piano_2": round(area_piano_2, 2),
                "area_totale_utilizzata": round(nesting.area_utilizzata, 2),
                "efficienza_totale": round(efficienza_totale, 2)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore nel salvataggio posizioni per nesting {nesting_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.get("/{nesting_id}/layout/positions")
async def get_tool_positions(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Recupera le posizioni salvate dei tool nel nesting.
    
    Args:
        nesting_id: ID del nesting
        db: Sessione database
        
    Returns:
        Lista delle posizioni salvate
    """
    try:
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(status_code=404, detail=f"Nesting con ID {nesting_id} non trovato")
        
        # Recupera posizioni salvate o calcola layout automatico
        if nesting.posizioni_tool:
            positions = []
            for pos_data in nesting.posizioni_tool:
                positions.append(ToolPosition(**pos_data))
        else:
            # Genera layout automatico se non ci sono posizioni salvate
            positions = NestingLayoutService.calculate_tool_positions(nesting)
        
        return {
            "success": True,
            "message": f"Posizioni recuperate per {len(positions)} tool",
            "nesting_id": nesting_id,
            "positions": positions,
            "has_custom_positions": bool(nesting.posizioni_tool)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore nel recupero posizioni per nesting {nesting_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/{nesting_id}/layout/reset")
async def reset_tool_positions(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    Resetta le posizioni dei tool al layout automatico.
    
    Args:
        nesting_id: ID del nesting
        db: Sessione database
        
    Returns:
        Nuove posizioni calcolate automaticamente
    """
    try:
        # Verifica che il nesting esista
        nesting = db.query(NestingResult).filter(NestingResult.id == nesting_id).first()
        if not nesting:
            raise HTTPException(status_code=404, detail=f"Nesting con ID {nesting_id} non trovato")
        
        # Verifica che sia modificabile
        if nesting.stato in ["confermato", "in_autoclave", "completato"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Impossibile resettare le posizioni: nesting in stato '{nesting.stato}'"
            )
        
        # Cancella posizioni personalizzate
        nesting.posizioni_tool = []
        
        # Ricalcola layout automatico
        new_positions = NestingLayoutService.calculate_tool_positions(nesting)
        
        # Salva le nuove posizioni
        if new_positions:
            positions_json = []
            area_piano_1 = 0.0
            area_piano_2 = 0.0
            
            for pos in new_positions:
                tool_area = pos.width * pos.height / 100
                if pos.piano == 1:
                    area_piano_1 += tool_area
                elif pos.piano == 2:
                    area_piano_2 += tool_area
                
                positions_json.append({
                    "odl_id": pos.odl_id,
                    "x": pos.x,
                    "y": pos.y,
                    "width": pos.width,
                    "height": pos.height,
                    "rotated": pos.rotated,
                    "piano": pos.piano
                })
            
            nesting.posizioni_tool = positions_json
            nesting.area_piano_1 = area_piano_1
            nesting.area_piano_2 = area_piano_2
            nesting.area_utilizzata = area_piano_1 + area_piano_2
        
        db.commit()
        
        logger.info(f"✅ Layout resettato per nesting {nesting_id}: {len(new_positions)} tool riposizionati")
        
        return {
            "success": True,
            "message": f"Layout resettato con successo: {len(new_positions)} tool riposizionati automaticamente",
            "nesting_id": nesting_id,
            "positions": new_positions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore nel reset posizioni per nesting {nesting_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


# ✅ NUOVO: Endpoint per nesting migliorato con vincoli completi
@router.post("/enhanced-preview")
async def get_enhanced_nesting_preview(
    request: EnhancedNestingRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint per generare una preview del nesting utilizzando l'algoritmo migliorato.
    
    Considera tutti i vincoli:
    - Compatibilità cicli di cura
    - Dimensioni reali dei tool con rotazioni
    - Valvole richieste vs disponibili
    - Numero di linee del vuoto
    - Posizionamento geometrico preciso
    - Gestione completa degli ODL esclusi con motivi dettagliati
    
    Args:
        request: Richiesta con ODL IDs, autoclave ID e vincoli opzionali
        
    Returns:
        EnhancedNestingPreviewResponse: Preview dettagliata del nesting con posizioni precise
    """
    try:
        logger.info(f"🔧 Generazione preview nesting migliorato per {len(request.odl_ids)} ODL in autoclave {request.autoclave_id}")
        
        # Valida input
        if not request.odl_ids:
            raise HTTPException(status_code=400, detail="Lista ODL vuota")
        
        # Verifica che l'autoclave esista
        autoclave = db.query(Autoclave).filter(Autoclave.id == request.autoclave_id).first()
        if not autoclave:
            raise HTTPException(status_code=404, detail=f"Autoclave con ID {request.autoclave_id} non trovata")
        
        # Verifica che gli ODL esistano
        odl_list = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(ODL.id.in_(request.odl_ids)).all()
        
        if len(odl_list) != len(request.odl_ids):
            found_ids = [odl.id for odl in odl_list]
            missing_ids = [odl_id for odl_id in request.odl_ids if odl_id not in found_ids]
            raise HTTPException(status_code=404, detail=f"ODL non trovati: {missing_ids}")
        
        # Esegui il nesting migliorato
        result = compute_enhanced_nesting(
            db=db,
            odl_ids=request.odl_ids,
            autoclave_id=request.autoclave_id,
            constraints=request.constraints
        )
        
        if not result['success']:
            # Se il nesting fallisce, restituisci comunque una preview con tutti gli ODL esclusi
            logger.warning(f"⚠️ Nesting migliorato fallito: {result.get('error', 'Errore sconosciuto')}")
            
            # Prepara dati per ODL esclusi
            excluded_odl_info = []
            for i, odl in enumerate(odl_list):
                exclusion_reason = result.get('exclusion_reasons', [])[i] if i < len(result.get('exclusion_reasons', [])) else result.get('error', 'Motivo sconosciuto')
                
                excluded_odl_info.append(ODLNestingInfoEnhanced(
                    id=odl.id,
                    parte_nome=odl.parte.descrizione_breve if odl.parte else "Parte sconosciuta",
                    tool_nome=odl.tool.part_number_tool if odl.tool else "Tool sconosciuto",
                    priorita=odl.priorita,
                    peso_kg=odl.tool.peso if odl.tool else 0.0,
                    area_cm2=(odl.tool.lunghezza_piano * odl.tool.larghezza_piano / 100) if (odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano) else 0.0,
                    valvole_richieste=odl.parte.num_valvole_richieste if odl.parte else 0,
                    ciclo_cura=odl.parte.ciclo_cura.nome if (odl.parte and odl.parte.ciclo_cura) else "Sconosciuto",
                    motivo_esclusione=exclusion_reason
                ))
            
            return EnhancedNestingPreviewResponse(
                success=False,
                message=f"Nesting non possibile: {result.get('error', 'Errore sconosciuto')}",
                autoclave=AutoclaveNestingInfoEnhanced(
                    id=autoclave.id,
                    nome=autoclave.nome,
                    area_piano=autoclave.area_piano or 0.0,
                    capacita_peso=autoclave.max_load_kg or 0.0,
                    num_linee_vuoto=autoclave.num_linee_vuoto or 0,
                    stato=autoclave.stato.value if autoclave.stato else "Sconosciuto"
                ),
                odl_inclusi=[],
                odl_esclusi=excluded_odl_info,
                statistiche={
                    "odl_totali": len(odl_list),
                    "odl_inclusi": 0,
                    "odl_esclusi": len(odl_list),
                    "efficienza_percent": 0.0,
                    "peso_totale_kg": 0.0,
                    "peso_massimo_kg": autoclave.max_load_kg or 0.0,
                    "valvole_utilizzate": 0,
                    "valvole_totali": autoclave.num_linee_vuoto or 0,
                    "area_utilizzata_cm2": 0.0,
                    "area_totale_cm2": autoclave.area_piano or 0.0
                },
                tool_positions=[],
                effective_dimensions=result.get('effective_dimensions', {}),
                constraints_used=request.constraints or {}
            )
        
        # Nesting riuscito - prepara la risposta
        selected_odl = result['selected_odl']
        excluded_odl = result['excluded_odl']
        exclusion_reasons = result['exclusion_reasons']
        
        # Prepara informazioni ODL inclusi
        included_odl_info = []
        for odl in selected_odl:
            included_odl_info.append(ODLNestingInfoEnhanced(
                id=odl.id,
                parte_nome=odl.parte.descrizione_breve if odl.parte else "Parte sconosciuta",
                tool_nome=odl.tool.part_number_tool if odl.tool else "Tool sconosciuto",
                priorita=odl.priorita,
                peso_kg=odl.tool.peso if odl.tool else 0.0,
                area_cm2=(odl.tool.lunghezza_piano * odl.tool.larghezza_piano / 100) if (odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano) else 0.0,
                valvole_richieste=odl.parte.num_valvole_richieste if odl.parte else 0,
                ciclo_cura=odl.parte.ciclo_cura.nome if (odl.parte and odl.parte.ciclo_cura) else "Sconosciuto",
                motivo_esclusione=None
            ))
        
        # Prepara informazioni ODL esclusi
        excluded_odl_info = []
        for i, odl in enumerate(excluded_odl):
            exclusion_reason = exclusion_reasons[i] if i < len(exclusion_reasons) else "Motivo sconosciuto"
            
            excluded_odl_info.append(ODLNestingInfoEnhanced(
                id=odl.id,
                parte_nome=odl.parte.descrizione_breve if odl.parte else "Parte sconosciuta",
                tool_nome=odl.tool.part_number_tool if odl.tool else "Tool sconosciuto",
                priorita=odl.priorita,
                peso_kg=odl.tool.peso if odl.tool else 0.0,
                area_cm2=(odl.tool.lunghezza_piano * odl.tool.larghezza_piano / 100) if (odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano) else 0.0,
                valvole_richieste=odl.parte.num_valvole_richieste if odl.parte else 0,
                ciclo_cura=odl.parte.ciclo_cura.nome if (odl.parte and odl.parte.ciclo_cura) else "Sconosciuto",
                motivo_esclusione=exclusion_reason
            ))
        
        # Converti posizioni tool
        tool_positions = []
        for pos_dict in result['tool_positions']:
            tool_positions.append(ToolPosition(
                odl_id=pos_dict['odl_id'],
                x=pos_dict['x'],
                y=pos_dict['y'],
                width=pos_dict['width'],
                height=pos_dict['height'],
                rotated=pos_dict.get('rotated', False),
                piano=pos_dict.get('piano', 1)
            ))
        
        # Calcola statistiche
        statistiche = {
            "odl_totali": len(odl_list),
            "odl_inclusi": len(selected_odl),
            "odl_esclusi": len(excluded_odl),
            "efficienza_percent": result.get('overall_efficiency', 0.0),
            "efficienza_geometrica_percent": result.get('geometric_efficiency', 0.0),
            "peso_totale_kg": result.get('total_weight', 0.0),
            "peso_massimo_kg": result.get('max_weight_with_margin', 0.0),
            "valvole_utilizzate": result.get('total_valvole', 0),
            "valvole_totali": result.get('max_valvole', 0),
            "area_utilizzata_cm2": sum(pos.width * pos.height for pos in tool_positions) / 100,  # Converti mm² in cm²
            "area_totale_cm2": autoclave.area_piano or 0.0,
            "cycles_found": result.get('cycles_found', [])
        }
        
        response = EnhancedNestingPreviewResponse(
            success=True,
            message=f"Preview nesting migliorato generata con successo: {len(selected_odl)} ODL inclusi, {len(excluded_odl)} esclusi",
            autoclave=AutoclaveNestingInfoEnhanced(
                id=autoclave.id,
                nome=autoclave.nome,
                area_piano=autoclave.area_piano or 0.0,
                capacita_peso=autoclave.max_load_kg or 0.0,
                num_linee_vuoto=autoclave.num_linee_vuoto or 0,
                stato=autoclave.stato.value if autoclave.stato else "Sconosciuto"
            ),
            odl_inclusi=included_odl_info,
            odl_esclusi=excluded_odl_info,
            statistiche=statistiche,
            tool_positions=tool_positions,
            effective_dimensions=result.get('effective_dimensions', {}),
            constraints_used=result.get('nesting_constraints').__dict__ if result.get('nesting_constraints') else {}
        )
        
        logger.info(f"✅ Preview nesting migliorato generata: {len(selected_odl)} inclusi, {len(excluded_odl)} esclusi, efficienza {result.get('overall_efficiency', 0):.1f}%")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Errore nella generazione preview nesting migliorato: {e}")
        raise HTTPException(status_code=500, detail=f"Errore nella generazione preview migliorato: {str(e)}")


@router.get("/active", response_model=List[NestingDetailResponse])
async def get_active_nesting(db: Session = Depends(get_db)):
    """
    Ottiene tutti i nesting attualmente attivi (caricati) nelle autoclavi.
    
    Un nesting è considerato attivo se:
    - Ha stato "Caricato"
    - L'autoclave associata è in stato "IN_USO"
    - Contiene ODL in stato "Cura"
    
    Returns:
        List[NestingDetailResponse]: Lista dei nesting attivi
    """
    try:
        # Recupera tutti i nesting in stato "Caricato"
        active_nesting = db.query(NestingResult).filter(
            NestingResult.stato == "Caricato"
        ).order_by(NestingResult.created_at.desc()).all()
        
        response_list = []
        
        for nesting in active_nesting:
            # Recupera l'autoclave associata
            autoclave = db.query(Autoclave).filter(Autoclave.id == nesting.autoclave_id).first()
            if not autoclave:
                continue
            
            # Recupera gli ODL inclusi
            odl_inclusi = []
            if nesting.odl_ids:
                odl_query = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).filter(ODL.id.in_(nesting.odl_ids))
                odl_inclusi = odl_query.all()
            
            # Recupera gli ODL esclusi
            odl_esclusi = []
            if nesting.odl_esclusi_ids:
                odl_esclusi_query = db.query(ODL).options(
                    joinedload(ODL.parte),
                    joinedload(ODL.tool)
                ).filter(ODL.id.in_(nesting.odl_esclusi_ids))
                odl_esclusi = odl_esclusi_query.all()
            
            # Costruisci la risposta per questo nesting
            nesting_response = NestingDetailResponse(
                id=nesting.id,
                autoclave=AutoclaveNestingInfo(
                    id=autoclave.id,
                    nome=autoclave.nome,
                    area_piano=autoclave.lunghezza * autoclave.larghezza_piano / 100,
                    max_load_kg=autoclave.max_load_kg,
                    stato=autoclave.stato.value
                ),
                odl_inclusi=[
                    ODLNestingInfo(
                        id=odl.id,
                        parte_codice=odl.parte.part_number if odl.parte else None,
                        tool_nome=odl.tool.part_number_tool if odl.tool else None,
                        priorita=odl.priorita,
                        dimensioni={
                            "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                            "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                            "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                        },
                        ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                        status=odl.status
                    ) for odl in odl_inclusi
                ],
                odl_esclusi=[
                    ODLNestingInfo(
                        id=odl.id,
                        parte_codice=odl.parte.part_number if odl.parte else None,
                        tool_nome=odl.tool.part_number_tool if odl.tool else None,
                        priorita=odl.priorita,
                        dimensioni={
                            "larghezza": odl.tool.larghezza_piano if odl.tool else 0,
                            "lunghezza": odl.tool.lunghezza_piano if odl.tool else 0,
                            "peso": odl.tool.peso if odl.tool and odl.tool.peso else 0
                        },
                        ciclo_cura=odl.parte.ciclo_cura.nome if odl.parte and odl.parte.ciclo_cura else None,
                        status=odl.status
                    ) for odl in odl_esclusi
                ],
                motivi_esclusione=nesting.motivi_esclusione or [],
                statistiche={
                    "area_utilizzata": nesting.area_utilizzata,
                    "area_totale": nesting.area_totale,
                    "efficienza": (nesting.area_utilizzata / nesting.area_totale * 100) if nesting.area_totale > 0 else 0,
                    "peso_totale": nesting.peso_totale_kg,
                    "valvole_utilizzate": nesting.valvole_utilizzate,
                    "valvole_totali": nesting.valvole_totali
                },
                stato=nesting.stato,
                note=nesting.note,
                created_at=nesting.created_at
            )
            
            response_list.append(nesting_response)
        
        return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero dei nesting attivi: {str(e)}")