"""
Servizio per la gestione del nesting automatico degli ODL nelle autoclavi.
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.nesting_result import NestingResult
from nesting_optimizer.auto_nesting import compute_nesting, NestingResult as OptimizationResult
from nesting_optimizer.two_level_nesting import compute_two_level_nesting, TwoLevelNestingResult
from schemas.nesting import NestingResultSchema, NestingPreviewSchema, AutoclavePreviewInfo, ODLPreviewInfo
from schemas.nesting import AutoclaveNestingInfo, ODLNestingInfo, NestingODLStatus
import random
import re
import logging

# Configura il logger
logger = logging.getLogger(__name__)

def extract_ciclo_cura_from_note(note: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Estrae le informazioni del ciclo di cura dalle note del nesting
    
    Args:
        note: Stringa delle note del nesting
        
    Returns:
        Tupla (ciclo_cura_id, ciclo_cura_nome)
    """
    if not note:
        return None, None
    
    try:
        # Pattern per estrarre: "Ciclo di cura: Nome (ID: 123)"
        pattern = r"Ciclo di cura: (.+?) \(ID: (\d+)\)"
        match = re.search(pattern, note)
        
        if match:
            nome = match.group(1)
            ciclo_id = int(match.group(2))
            return ciclo_id, nome
        
        return None, None
    except Exception:
        return None, None

def get_all_nesting_results(db: Session) -> List[NestingResult]:
    """
    Recupera tutti i risultati di nesting dal database con le loro relazioni
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista di oggetti NestingResult
    """
    return db.query(NestingResult).options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    ).order_by(NestingResult.created_at.desc()).all()

def generate_color_for_odl(odl_id: int) -> str:
    """
    Genera un colore consistente per un ODL basato sul suo ID
    """
    colors = [
        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
        "#06B6D4", "#84CC16", "#F97316", "#EC4899", "#6366F1"
    ]
    return colors[odl_id % len(colors)]

async def get_nesting_preview(
    db: Session, 
    parametri: Optional['NestingParameters'] = None
) -> NestingPreviewSchema:
    """
    Genera un'anteprima del nesting senza salvarlo nel database
    
    Args:
        db: Sessione del database
        parametri: Parametri regolabili per il nesting (opzionale)
        
    Returns:
        Schema NestingPreviewSchema con l'anteprima del nesting
    """
    # Recupera tutti gli ODL in stato "Attesa Cura" filtrati e validati
    odl_list = await get_odl_attesa_cura_filtered(db)
    
    # Recupera tutte le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Se non ci sono ODL o autoclavi, restituisci un risultato vuoto
    if not odl_list or not autoclavi:
        return NestingPreviewSchema(
            success=False,
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            autoclavi=[],
            odl_esclusi=[]
        )
    
    # Esegui l'algoritmo di nesting con parametri personalizzati
    result = compute_nesting(db, odl_list, autoclavi, parametri)
    
    # Prepara le informazioni sulle autoclavi per la preview
    autoclavi_preview = []
    
    for autoclave in autoclavi:
        # Verifica se questa autoclave è stata utilizzata nel nesting
        if autoclave.id in result.assegnamenti:
            # Recupera le statistiche per questa autoclave
            stats = result.statistiche_autoclavi.get(autoclave.id, {})
            ciclo_info = result.cicli_cura_autoclavi.get(autoclave.id, {})
            
            # Prepara la lista degli ODL inclusi con le loro informazioni
            odl_inclusi = []
            for odl_id in result.assegnamenti[autoclave.id]:
                odl = db.query(ODL).options(
                    joinedload(ODL.parte).joinedload(Parte.catalogo)
                ).filter(ODL.id == odl_id).first()
                
                if odl and odl.parte and odl.parte.catalogo:
                    catalogo = odl.parte.catalogo
                    odl_inclusi.append(ODLPreviewInfo(
                        id=odl.id,
                        part_number=catalogo.part_number,
                        descrizione=odl.parte.descrizione_breve,
                        area_cm2=catalogo.area_cm2,
                        num_valvole=odl.parte.num_valvole_richieste,
                        priorita=odl.priorita,
                        color=generate_color_for_odl(odl.id)
                    ))
            
            # Calcola l'area totale dell'autoclave in cm²
            area_totale_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
            
            autoclavi_preview.append(AutoclavePreviewInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                codice=autoclave.codice,
                lunghezza=autoclave.lunghezza,
                larghezza_piano=autoclave.larghezza_piano,
                area_totale_cm2=area_totale_cm2,
                area_utilizzata_cm2=float(stats.get("area_utilizzata", 0.0)),
                valvole_totali=autoclave.num_linee_vuoto,
                valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
                odl_inclusi=odl_inclusi,
                ciclo_cura_id=ciclo_info.get("id"),
                ciclo_cura_nome=ciclo_info.get("nome")
            ))
    
    # Prepara la lista degli ODL esclusi
    odl_esclusi = []
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        # Recupera l'ODL dal database
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo)
        ).filter(ODL.id == odl_id).first()
        
        if odl:
            parte = odl.parte
            catalogo = parte.catalogo if parte else None
            
            odl_esclusi.append({
                "id": odl.id,
                "part_number": catalogo.part_number if catalogo else "N/A",
                "descrizione": parte.descrizione_breve if parte else "Sconosciuta",
                "motivo": motivo,
                "priorita": odl.priorita,
                "num_valvole": parte.num_valvole_richieste if parte else 0
            })
    
    # Restituisci l'anteprima con i parametri utilizzati
    return NestingPreviewSchema(
        success=True,
        message=f"Anteprima generata: {len([odl for autoclave in autoclavi_preview for odl in autoclave.odl_inclusi])} ODL pianificati, {len(odl_esclusi)} esclusi",
        autoclavi=autoclavi_preview,
        odl_esclusi=odl_esclusi,
        parametri_utilizzati=parametri
    )

async def run_automatic_nesting(db: Session) -> NestingResultSchema:
    """
    ✅ SEZIONE 1 - AUTOMAZIONE NESTING
    Esegue l'algoritmo di nesting automatico ottimizzato che:
    - Recupera tutti gli ODL in stato "ATTESA CURA"
    - Raggruppa per ciclo compatibile
    - Cerca autoclavi disponibili (stato = LIBERA/DISPONIBILE)
    - Seleziona autoclavi in base a capacità, superficie e carico massimo
    - Crea un nesting per ogni gruppo assegnabile
    - Al salvataggio: autoclave passa a "IN USO", nesting resta "SOSPESO"
    
    Args:
        db: Sessione del database
        
    Returns:
        Schema NestingResult con i risultati dell'ottimizzazione
    """
    # ✅ STEP 1: Recupera tutti gli ODL in stato "Attesa Cura" filtrati e validati
    odl_list = await get_odl_attesa_cura_filtered(db)
    
    # ✅ STEP 2: Recupera tutte le autoclavi DISPONIBILI (stato = DISPONIBILE)
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Se non ci sono ODL o autoclavi, restituisci un risultato vuoto
    if not odl_list or not autoclavi:
        return NestingResultSchema(
            success=False,
            message="Nessun ODL in attesa o nessuna autoclave disponibile per l'assegnazione automatica",
            autoclavi=[],
            odl_pianificati=[],
            odl_non_pianificabili=[]
        )
    
    # ✅ STEP 3: Raggruppa ODL per ciclo compatibile
    # Analizza le note degli ODL per identificare cicli di cura compatibili
    cicli_compatibili = {}
    odl_senza_ciclo = []
    
    for odl in odl_list:
        # Estrai informazioni sul ciclo dalle note o dalla parte
        ciclo_id, ciclo_nome = extract_ciclo_cura_from_note(odl.note or "")
        
        # Se non trovato nelle note, usa un ciclo standard basato sul materiale/tipo parte
        if not ciclo_id and odl.parte:
            # Logica semplificata: raggruppa per tipo di materiale o caratteristiche simili
            ciclo_key = f"standard_{odl.parte.id % 3}"  # Simula 3 cicli standard
            ciclo_nome = f"Ciclo Standard {ciclo_key[-1]}"
        else:
            ciclo_key = f"ciclo_{ciclo_id}" if ciclo_id else "senza_ciclo"
        
        if ciclo_key == "senza_ciclo":
            odl_senza_ciclo.append(odl)
        else:
            if ciclo_key not in cicli_compatibili:
                cicli_compatibili[ciclo_key] = {
                    'nome': ciclo_nome,
                    'odl_list': [],
                    'id': ciclo_id
                }
            cicli_compatibili[ciclo_key]['odl_list'].append(odl)
    
    # ✅ STEP 4: Per ogni gruppo di ciclo compatibile, cerca autoclavi disponibili
    autoclavi_assegnate = []
    odl_pianificati = []
    odl_non_pianificabili = []
    nesting_results = []
    
    for ciclo_key, ciclo_data in cicli_compatibili.items():
        odl_gruppo = ciclo_data['odl_list']
        ciclo_nome = ciclo_data['nome']
        ciclo_id = ciclo_data['id']
        
        if not odl_gruppo:
            continue
        
        # ✅ STEP 5: Seleziona autoclave ottimale per questo gruppo
        autoclave_ottimale = None
        migliore_score = -1
        
        for autoclave in autoclavi:
            # Salta autoclavi già assegnate
            if autoclave.id in autoclavi_assegnate:
                continue
            
            # ✅ Calcola capacità disponibile
            area_totale_cm2 = autoclave.area_piano
            valvole_totali = autoclave.num_linee_vuoto
            carico_max_kg = autoclave.max_load_kg or 1000.0
            
            # Calcola requisiti del gruppo ODL
            area_richiesta = sum(
                (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) / 100 
                for odl in odl_gruppo 
                if odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano
            )
            valvole_richieste = sum(
                odl.parte.num_valvole_richieste 
                for odl in odl_gruppo 
                if odl.parte and odl.parte.num_valvole_richieste
            )
            peso_stimato_kg = len(odl_gruppo) * 10.0  # Stima 10kg per ODL
            
            # ✅ Verifica vincoli di capacità
            if (area_richiesta > area_totale_cm2 or 
                valvole_richieste > valvole_totali or 
                peso_stimato_kg > carico_max_kg):
                continue
            
            # ✅ Calcola score di ottimizzazione (efficienza utilizzo)
            efficienza_area = (area_richiesta / area_totale_cm2) * 100
            efficienza_valvole = (valvole_richieste / valvole_totali) * 100
            efficienza_peso = (peso_stimato_kg / carico_max_kg) * 100
            
            # Score combinato (preferisce utilizzo bilanciato)
            score = (efficienza_area + efficienza_valvole + efficienza_peso) / 3
            
            if score > migliore_score:
                migliore_score = score
                autoclave_ottimale = autoclave
        
        # ✅ STEP 6: Se trovata autoclave ottimale, crea nesting
        if autoclave_ottimale:
            # Marca autoclave come assegnata
            autoclavi_assegnate.append(autoclave_ottimale.id)
            
            # ✅ SEZIONE 1: Aggiorna lo stato dell'autoclave a "IN_USO"
            autoclave_ottimale.stato = StatoAutoclaveEnum.IN_USO
            db.add(autoclave_ottimale)
            
            # Calcola statistiche finali
            area_utilizzata = sum(
                (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) / 100 
                for odl in odl_gruppo 
                if odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano
            )
            valvole_utilizzate = sum(
                odl.parte.num_valvole_richieste 
                for odl in odl_gruppo 
                if odl.parte and odl.parte.num_valvole_richieste
            )
            peso_totale = len(odl_gruppo) * 10.0
            
            # ✅ Prepara note complete con informazioni ciclo
            note_complete = (
                f"Nesting automatico - Ciclo di cura: {ciclo_nome} (ID: {ciclo_id or 'N/A'})\n"
                f"Efficienza area: {(area_utilizzata / autoclave_ottimale.area_piano) * 100:.1f}%\n"
                f"Efficienza valvole: {(valvole_utilizzate / autoclave_ottimale.num_linee_vuoto) * 100:.1f}%\n"
                f"Peso stimato: {peso_totale:.1f}kg\n"
                f"ODL assegnati: {len(odl_gruppo)}"
            )
            
            # ✅ Crea record NestingResult con stato "In sospeso"
            nesting_record = NestingResult(
                autoclave_id=autoclave_ottimale.id,
                odl_ids=[odl.id for odl in odl_gruppo],
                odl_esclusi_ids=[],
                motivi_esclusione=[],
                stato="In sospeso",  # ✅ Nesting resta in stato SOSPESO
                area_utilizzata=float(area_utilizzata),
                area_totale=float(autoclave_ottimale.area_piano),
                valvole_utilizzate=int(valvole_utilizzate),
                valvole_totali=autoclave_ottimale.num_linee_vuoto,
                peso_totale_kg=peso_totale,
                note=note_complete,
                posizioni_tool=[]  # Sarà popolato dal sistema di ottimizzazione 2D
            )
            
            # Aggiungi gli ODL al nesting
            for odl in odl_gruppo:
                nesting_record.odl_list.append(odl)
            
            # Salva nel database
            db.add(nesting_record)
            nesting_results.append(nesting_record)
            
            # Aggiungi agli ODL pianificati
            for odl in odl_gruppo:
                odl_pianificati.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                    num_valvole=odl.parte.num_valvole_richieste if odl.parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.PIANIFICATO
                ))
        else:
            # ✅ Nessuna autoclave disponibile per questo gruppo
            for odl in odl_gruppo:
                odl_non_pianificabili.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=f"{odl.parte.descrizione_breve if odl.parte else 'Sconosciuta'} (Motivo: Nessuna autoclave disponibile per ciclo {ciclo_nome})",
                    num_valvole=odl.parte.num_valvole_richieste if odl.parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.NON_PIANIFICABILE
                ))
    
    # ✅ Gestisci ODL senza ciclo definito
    for odl in odl_senza_ciclo:
        odl_non_pianificabili.append(ODLNestingInfo(
            id=odl.id,
            parte_descrizione=f"{odl.parte.descrizione_breve if odl.parte else 'Sconosciuta'} (Motivo: Ciclo di cura non definito)",
            num_valvole=odl.parte.num_valvole_richieste if odl.parte else 0,
            priorita=odl.priorita,
            status=NestingODLStatus.NON_PIANIFICABILE
        ))
    
    # ✅ Commit delle modifiche al database
    db.commit()
    
    # ✅ Prepara informazioni sulle autoclavi utilizzate
    autoclavi_info = []
    for nesting in nesting_results:
        autoclave = nesting.autoclave
        autoclavi_info.append(AutoclaveNestingInfo(
            id=autoclave.id,
            nome=autoclave.nome,
            odl_assegnati=[odl.id for odl in nesting.odl_list],
            valvole_utilizzate=nesting.valvole_utilizzate,
            valvole_totali=nesting.valvole_totali,
            area_utilizzata=nesting.area_utilizzata,
            area_totale=nesting.area_totale,
            ciclo_cura_id=None,  # Sarà estratto dalle note se necessario
            ciclo_cura_nome=None
        ))
    
    # ✅ Restituisci il risultato ottimizzato
    return NestingResultSchema(
        success=True,
        message=f"Nesting automatico completato: {len(odl_pianificati)} ODL pianificati su {len(autoclavi_info)} autoclavi, {len(odl_non_pianificabili)} non pianificabili",
        autoclavi=autoclavi_info,
        odl_pianificati=odl_pianificati,
        odl_non_pianificabili=odl_non_pianificabili
    )

async def update_nesting_status(db: Session, nesting_id: int, nuovo_stato: str, note: str = None, ruolo_utente: str = None) -> NestingResult:
    """
    Aggiorna lo stato di un nesting e gestisce il cambio di stato degli ODL associati
    
    Args:
        db: Sessione del database
        nesting_id: ID del nesting da aggiornare
        nuovo_stato: Nuovo stato del nesting
        note: Note opzionali
        ruolo_utente: Ruolo dell'utente che sta effettuando l'operazione
        
    Returns:
        Il nesting aggiornato
        
    Raises:
        ValueError: Se il nesting non viene trovato o l'operazione non è permessa
    """
    # Recupera il nesting dal database
    nesting = db.query(NestingResult).options(
        joinedload(NestingResult.autoclave),
        joinedload(NestingResult.odl_list).joinedload(ODL.parte),
        joinedload(NestingResult.odl_list).joinedload(ODL.tool)
    ).filter(NestingResult.id == nesting_id).first()
    
    if not nesting:
        raise ValueError(f"Nesting con ID {nesting_id} non trovato")
    
    # Validazione dei permessi basata sul ruolo
    if ruolo_utente == "curing":
        # L'operatore Curing può solo confermare nesting in sospeso
        if nesting.stato != "In sospeso":
            raise ValueError("L'operatore Curing può confermare solo nesting in sospeso")
        if nuovo_stato not in ["Confermato", "Annullato"]:
            raise ValueError("L'operatore Curing può solo confermare o annullare nesting")
    elif ruolo_utente == "management":
        # Il management può modificare qualsiasi nesting non completato
        if nesting.stato == "Completato":
            raise ValueError("Non è possibile modificare nesting già completati")
    
    # Aggiorna lo stato del nesting
    stato_precedente = nesting.stato
    nesting.stato = nuovo_stato
    if note:
        nesting.note = note
    
    # Registra chi ha confermato il nesting
    if nuovo_stato == "Confermato" and ruolo_utente:
        nesting.confermato_da_ruolo = ruolo_utente
    
    # Gestione cambio stato degli ODL e dell'autoclave
    if nuovo_stato == "Confermato":
        # Quando il nesting viene confermato, gli ODL passano in "Cura"
        for odl in nesting.odl_list:
            if odl.status == "Attesa Cura":
                odl.status = "Cura"  # Cambia lo stato a "Cura" (In Autoclave)
                db.add(odl)
        
        # ✅ SEZIONE 4: Aggiorna lo stato dell'autoclave a "IN CURA"
        if nesting.autoclave:
            nesting.autoclave.stato = StatoAutoclaveEnum.IN_CURA
            db.add(nesting.autoclave)
    
    elif nuovo_stato == "Annullato":
        # Se il nesting viene annullato, riporta gli ODL in "Attesa Cura"
        for odl in nesting.odl_list:
            if odl.status == "Cura":
                odl.status = "Attesa Cura"  # Riporta in attesa
                db.add(odl)
        
        # ✅ SEZIONE 4: Riporta l'autoclave a "DISPONIBILE"
        if nesting.autoclave:
            nesting.autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
            db.add(nesting.autoclave)
    
    elif nuovo_stato == "Completato":
        # Quando il nesting è completato, gli ODL passano a "Finito"
        for odl in nesting.odl_list:
            if odl.status == "Cura":
                odl.status = "Finito"
                db.add(odl)
        
        # ✅ SEZIONE 4: Riporta l'autoclave a "DISPONIBILE" dopo il completamento
        if nesting.autoclave:
            nesting.autoclave.stato = StatoAutoclaveEnum.DISPONIBILE
            db.add(nesting.autoclave)
        
        # ✅ NUOVO: Genera automaticamente il report PDF per il nesting completato
        try:
            from services.nesting_report_generator import NestingReportGenerator
            report_generator = NestingReportGenerator(db)
            result = report_generator.generate_nesting_report(nesting.id)
            if result:
                file_path, report_record = result
                logger.info(f"✅ Report PDF generato automaticamente per nesting {nesting.id}: {file_path}")
            else:
                logger.warning(f"⚠️ Impossibile generare il report PDF per nesting {nesting.id}")
        except Exception as e:
            logger.error(f"❌ Errore durante la generazione automatica del report per nesting {nesting.id}: {e}")
            # Non blocchiamo il processo se la generazione del report fallisce
    
    # Salva le modifiche
    db.add(nesting)
    db.commit()
    db.refresh(nesting)
    
    return nesting 

async def save_nesting_draft(db: Session, nesting_data: dict) -> dict:
    """
    Salva una bozza di nesting senza modificare lo stato degli ODL
    
    Args:
        db: Sessione del database
        nesting_data: Dati del nesting da salvare come bozza
        
    Returns:
        Dizionario con il risultato del salvataggio
    """
    try:
        # Valida i dati in input
        if not nesting_data.get("autoclavi") or not isinstance(nesting_data["autoclavi"], list):
            return {
                "success": False,
                "message": "Dati autoclavi non validi",
                "draft_id": None
            }
        
        # Salva ogni autoclave come bozza separata
        draft_ids = []
        
        for autoclave_data in nesting_data["autoclavi"]:
            autoclave_id = autoclave_data.get("id")
            odl_ids = autoclave_data.get("odl_inclusi", [])
            
            if not autoclave_id or not odl_ids:
                continue
                
            # Trova l'autoclave
            autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
            if not autoclave:
                continue
            
            # Crea un record di bozza
            nesting_draft = NestingResult(
                autoclave_id=autoclave_id,
                odl_ids=[odl["id"] for odl in odl_ids],
                odl_esclusi_ids=nesting_data.get("odl_esclusi", []),
                motivi_esclusione=[],
                stato="Bozza",  # Stato speciale per le bozze
                area_utilizzata=float(autoclave_data.get("area_utilizzata_cm2", 0.0)),
                area_totale=float(autoclave_data.get("area_totale_cm2", 0.0)),
                valvole_utilizzate=int(autoclave_data.get("valvole_utilizzate", 0)),
                valvole_totali=autoclave.num_linee_vuoto,
                note="Bozza salvata automaticamente"
            )
            
            # Salva nel database
            db.add(nesting_draft)
            db.flush()  # Per ottenere l'ID
            draft_ids.append(nesting_draft.id)
        
        # Commit delle modifiche
        db.commit()
        
        return {
            "success": True,
            "message": f"Bozza salvata con successo ({len(draft_ids)} autoclavi)",
            "draft_ids": draft_ids
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Errore nel salvataggio della bozza: {str(e)}",
            "draft_ids": []
        }

async def load_nesting_draft(db: Session, draft_id: int) -> dict:
    """
    Carica una bozza di nesting salvata
    
    Args:
        db: Sessione del database
        draft_id: ID della bozza da caricare
        
    Returns:
        Dizionario con i dati della bozza
    """
    try:
        # Recupera la bozza dal database
        draft = db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte).joinedload(Parte.catalogo)
        ).filter(
            NestingResult.id == draft_id,
            NestingResult.stato == "Bozza"
        ).first()
        
        if not draft:
            return {
                "success": False,
                "message": "Bozza non trovata",
                "data": None
            }
        
        # Prepara i dati della bozza
        autoclave_data = {
            "id": draft.autoclave.id,
            "nome": draft.autoclave.nome,
            "codice": draft.autoclave.codice,
            "lunghezza": draft.autoclave.lunghezza,
            "larghezza_piano": draft.autoclave.larghezza_piano,
            "area_totale_cm2": draft.area_totale,
            "area_utilizzata_cm2": draft.area_utilizzata,
            "valvole_totali": draft.valvole_totali,
            "valvole_utilizzate": draft.valvole_utilizzate,
            "odl_inclusi": []
        }
        
        # Aggiungi gli ODL inclusi
        for odl in draft.odl_list:
            if odl.parte and odl.parte.catalogo:
                autoclave_data["odl_inclusi"].append({
                    "id": odl.id,
                    "part_number": odl.parte.catalogo.part_number,
                    "descrizione": odl.parte.descrizione_breve,
                    "area_cm2": odl.parte.catalogo.area_cm2,
                    "num_valvole": odl.parte.num_valvole_richieste,
                    "priorita": odl.priorita,
                    "color": generate_color_for_odl(odl.id)
                })
        
        return {
            "success": True,
            "message": "Bozza caricata con successo",
            "data": {
                "id": draft.id,
                "created_at": draft.created_at.isoformat(),
                "autoclave": autoclave_data,
                "odl_esclusi": draft.odl_esclusi_ids or []
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Errore nel caricamento della bozza: {str(e)}",
            "data": None
        }

async def get_odl_attesa_cura_filtered(db: Session) -> List[ODL]:
    """
    Recupera tutti gli ODL in stato "Attesa Cura" che possono essere inclusi nel nesting
    
    Args:
        db: Sessione del database
        
    Returns:
        Lista di ODL filtrati e validati
    """
    try:
        # Recupera tutti gli ODL in stato "Attesa Cura"
        odl_candidates = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.tool)
        ).filter(
            ODL.status == "Attesa Cura"
        ).all()
        
        # Filtra solo gli ODL validi per il nesting
        odl_validi = []
        
        for odl in odl_candidates:
            # Verifica che l'ODL non sia già in un nesting attivo
            existing_nesting = db.query(NestingResult).filter(
                NestingResult.odl_ids.contains([odl.id]),
                NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
            ).first()
            
            if existing_nesting:
                continue  # Salta questo ODL
            
            # ✅ VALIDAZIONE MIGLIORATA: Verifica che abbia tutti i dati necessari
            errori_validazione = []
            
            # Verifica tool assegnato
            if not odl.tool:
                errori_validazione.append("Tool non assegnato")
            
            # Verifica parte e catalogo
            if not odl.parte:
                errori_validazione.append("Parte non definita")
            elif not odl.parte.catalogo:
                errori_validazione.append("Catalogo parte non definito")
            else:
                # Verifica superficie
                if not odl.parte.catalogo.area_cm2 or odl.parte.catalogo.area_cm2 <= 0:
                    errori_validazione.append("Superficie non definita o zero")
            
            # Verifica valvole
            if not odl.parte or not odl.parte.num_valvole_richieste or odl.parte.num_valvole_richieste <= 0:
                errori_validazione.append("Numero valvole non definito")
            
            # Verifica ciclo di cura
            if not odl.parte or not hasattr(odl.parte, 'ciclo_cura') or not odl.parte.ciclo_cura:
                errori_validazione.append("Ciclo di cura non assegnato")
            
            # Se non ci sono errori, l'ODL è valido
            if not errori_validazione:
                odl_validi.append(odl)
            else:
                # Log degli errori per debugging
                logger.warning(f"❌ ODL #{odl.id} escluso dal nesting: {', '.join(errori_validazione)}")
        
        return odl_validi
        
    except Exception as e:
        print(f"Errore nel filtro ODL Attesa Cura: {str(e)}")
        return [] 

async def select_odl_and_autoclave_automatically(db: Session) -> Dict:
    """
    ✅ LOGICA SELEZIONE AUTOMATICA ODL + AUTOCLAVE
    
    Implementa la logica che seleziona automaticamente:
    - Gli ODL idonei da inserire nel nesting (stato ATTESA CURA)
    - L'autoclave più adatta per il carico
    
    Basandosi su:
    - Stato ODL: solo quelli in ATTESA CURA
    - Ciclo di cura compatibile
    - Capacità disponibile (area, peso)
    - Stato autoclave (DISPONIBILE)
    - Campo use_secondary_plane per aumentare capacità
    
    Args:
        db: Sessione del database
        
    Returns:
        Dict con:
        - success: bool
        - message: str
        - odl_groups: List[Dict] - Gruppi di ODL per ciclo di cura
        - selected_autoclave: Dict - Autoclave selezionata
        - selection_criteria: Dict - Criteri di selezione utilizzati
    """
    try:
        # ✅ STEP 1: Selezione ODL
        print("🔍 STEP 1: Recupero ODL in stato ATTESA CURA...")
        
        # Recupera tutti gli ODL in stato "Attesa Cura" con tutte le relazioni necessarie
        odl_candidates = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(ODL.tool)
        ).filter(
            ODL.status == "Attesa Cura"
        ).all()
        
        if not odl_candidates:
            return {
                "success": False,
                "message": "Nessun ODL trovato in stato 'Attesa Cura'",
                "odl_groups": [],
                "selected_autoclave": None,
                "selection_criteria": {}
            }
        
        print(f"📋 Trovati {len(odl_candidates)} ODL candidati")
        
        # ✅ STEP 2: Verifica tool associati e validità
        print("🔧 STEP 2: Verifica tool associati e validità...")
        
        odl_validi = []
        odl_esclusi = []
        
        for odl in odl_candidates:
            # Verifica che l'ODL non sia già in un nesting attivo
            existing_nesting = db.query(NestingResult).filter(
                NestingResult.odl_ids.contains([odl.id]),
                NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
            ).first()
            
            if existing_nesting:
                odl_esclusi.append({
                    "odl_id": odl.id,
                    "motivo": f"Già assegnato al nesting #{existing_nesting.id}"
                })
                continue
            
            # Verifica che abbia tool assegnato
            if not odl.tool:
                odl_esclusi.append({
                    "odl_id": odl.id,
                    "motivo": "Tool non assegnato"
                })
                continue
            
            # ✅ VALIDAZIONE MIGLIORATA: Verifica che abbia tutti i dati necessari
            errori_validazione = []
            
            # Verifica parte
            if not odl.parte:
                errori_validazione.append("Parte non definita")
            
            # Verifica tool e dimensioni
            if not odl.tool:
                errori_validazione.append("Tool non assegnato")
            else:
                # Verifica superficie del tool
                if not odl.tool.lunghezza_piano or not odl.tool.larghezza_piano or odl.tool.area <= 0:
                    errori_validazione.append("Dimensioni tool non definite o zero")
                
                # Verifica peso del tool (opzionale, può essere 0)
                if odl.tool.peso is None or odl.tool.peso < 0:
                    errori_validazione.append("Peso tool non valido")
            
            # Verifica valvole
            if not odl.parte or not odl.parte.num_valvole_richieste or odl.parte.num_valvole_richieste <= 0:
                errori_validazione.append("Numero valvole non definito")
            
            if errori_validazione:
                odl_esclusi.append({
                    "odl_id": odl.id,
                    "motivo": f"Dati incompleti: {', '.join(errori_validazione)}"
                })
                continue
            
            # Verifica che abbia un ciclo di cura assegnato
            if not odl.parte.ciclo_cura:
                odl_esclusi.append({
                    "odl_id": odl.id,
                    "motivo": "Ciclo di cura non assegnato"
                })
                continue
            
            # ODL valido
            odl_validi.append(odl)
        
        if not odl_validi:
            return {
                "success": False,
                "message": f"Nessun ODL valido trovato. {len(odl_esclusi)} ODL esclusi per vari motivi",
                "odl_groups": [],
                "selected_autoclave": None,
                "selection_criteria": {"odl_esclusi": odl_esclusi}
            }
        
        print(f"✅ {len(odl_validi)} ODL validi, {len(odl_esclusi)} esclusi")
        
        # ✅ STEP 3: Raggruppa ODL per ciclo di cura, priorità e scadenza
        print("📊 STEP 3: Raggruppamento ODL per ciclo di cura...")
        
        gruppi_ciclo = {}
        
        for odl in odl_validi:
            ciclo_id = odl.parte.ciclo_cura.id
            ciclo_nome = odl.parte.ciclo_cura.nome
            
            if ciclo_id not in gruppi_ciclo:
                gruppi_ciclo[ciclo_id] = {
                    "ciclo_id": ciclo_id,
                    "ciclo_nome": ciclo_nome,
                    "ciclo_cura": odl.parte.ciclo_cura,
                    "odl_list": []
                }
            
            gruppi_ciclo[ciclo_id]["odl_list"].append(odl)
        
        # Ordina gli ODL in ogni gruppo per priorità (decrescente) e poi per ID (crescente come proxy per scadenza)
        for gruppo in gruppi_ciclo.values():
            gruppo["odl_list"].sort(key=lambda x: (-x.priorita, x.id))
        
        print(f"📋 Creati {len(gruppi_ciclo)} gruppi per cicli di cura diversi")
        
        # ✅ STEP 4: Selezione autoclave
        print("🏭 STEP 4: Selezione autoclave disponibili...")
        
        # Recupera tutte le autoclavi disponibili
        autoclavi_disponibili = db.query(Autoclave).filter(
            Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        ).all()
        
        if not autoclavi_disponibili:
            return {
                "success": False,
                "message": "Nessuna autoclave disponibile",
                "odl_groups": list(gruppi_ciclo.values()),
                "selected_autoclave": None,
                "selection_criteria": {"odl_esclusi": odl_esclusi}
            }
        
        print(f"🏭 Trovate {len(autoclavi_disponibili)} autoclavi disponibili")
        
        # ✅ STEP 5: Valuta compatibilità e capacità per ogni gruppo
        print("⚖️ STEP 5: Valutazione compatibilità e capacità...")
        
        migliore_combinazione = None
        miglior_punteggio = -1
        
        for gruppo in gruppi_ciclo.values():
            ciclo_cura = gruppo["ciclo_cura"]
            odl_gruppo = gruppo["odl_list"]
            
            # Calcola requisiti totali del gruppo usando i tool
            area_totale_richiesta = sum(odl.tool.area for odl in odl_gruppo if odl.tool)
            valvole_totali_richieste = sum(odl.parte.num_valvole_richieste for odl in odl_gruppo)
            peso_totale_stimato = sum(getattr(odl.tool, 'peso', 0.5) for odl in odl_gruppo if odl.tool)  # Default 0.5kg se non specificato
            
            print(f"📊 Gruppo {ciclo_cura.nome}: {len(odl_gruppo)} ODL, {area_totale_richiesta:.1f}cm², {valvole_totali_richieste} valvole, {peso_totale_stimato:.1f}kg")
            
            # Valuta ogni autoclave per questo gruppo
            for autoclave in autoclavi_disponibili:
                # Verifica compatibilità tecnica con il ciclo di cura
                if (ciclo_cura.temperatura_max > autoclave.temperatura_max or
                    ciclo_cura.pressione_max > autoclave.pressione_max):
                    continue  # Autoclave non compatibile con questo ciclo
                
                # Calcola capacità autoclave
                area_piano_base = autoclave.area_piano  # Già in cm²
                area_disponibile = area_piano_base
                
                # Se supporta piano secondario e necessario, raddoppia l'area
                if autoclave.use_secondary_plane and area_totale_richiesta > area_piano_base:
                    area_disponibile = area_piano_base * 2
                    print(f"🔄 Autoclave {autoclave.nome}: attivato piano secondario (area: {area_disponibile:.1f}cm²)")
                
                # Verifica capacità
                if (area_totale_richiesta <= area_disponibile and
                    valvole_totali_richieste <= autoclave.num_linee_vuoto and
                    peso_totale_stimato <= autoclave.max_load_kg):
                    
                    # Calcola punteggio di utilizzo
                    utilizzo_area = (area_totale_richiesta / area_disponibile) * 100
                    utilizzo_valvole = (valvole_totali_richieste / autoclave.num_linee_vuoto) * 100
                    utilizzo_peso = (peso_totale_stimato / autoclave.max_load_kg) * 100
                    
                    # Conta carichi eseguiti oggi (simulato - in futuro da implementare con query reale)
                    carichi_oggi = db.query(NestingResult).filter(
                        NestingResult.autoclave_id == autoclave.id,
                        func.date(NestingResult.created_at) == func.current_date()
                    ).count()
                    
                    # Punteggio: favorisce alto utilizzo superficie ma penalizza autoclavi già molto usate
                    punteggio = utilizzo_area - (carichi_oggi * 10)  # Penalità per uso frequente
                    
                    print(f"📈 Autoclave {autoclave.nome}: utilizzo {utilizzo_area:.1f}% area, {utilizzo_valvole:.1f}% valvole, {utilizzo_peso:.1f}% peso, punteggio: {punteggio:.1f}")
                    
                    if punteggio > miglior_punteggio:
                        miglior_punteggio = punteggio
                        migliore_combinazione = {
                            "gruppo": gruppo,
                            "autoclave": autoclave,
                            "utilizzo_area": utilizzo_area,
                            "utilizzo_valvole": utilizzo_valvole,
                            "utilizzo_peso": utilizzo_peso,
                            "area_richiesta": area_totale_richiesta,
                            "area_disponibile": area_disponibile,
                            "valvole_richieste": valvole_totali_richieste,
                            "peso_richiesto": peso_totale_stimato,
                            "carichi_oggi": carichi_oggi,
                            "punteggio": punteggio,
                            "usa_piano_secondario": area_totale_richiesta > area_piano_base and autoclave.use_secondary_plane
                        }
        
        # ✅ STEP 6: Risultato finale
        if not migliore_combinazione:
            return {
                "success": False,
                "message": "Nessuna autoclave compatibile trovata per i gruppi di ODL disponibili",
                "odl_groups": list(gruppi_ciclo.values()),
                "selected_autoclave": None,
                "selection_criteria": {
                    "odl_esclusi": odl_esclusi,
                    "autoclavi_valutate": len(autoclavi_disponibili),
                    "gruppi_ciclo": len(gruppi_ciclo)
                }
            }
        
        # Prepara il risultato
        gruppo_selezionato = migliore_combinazione["gruppo"]
        autoclave_selezionata = migliore_combinazione["autoclave"]
        
        print(f"🎯 SELEZIONE COMPLETATA:")
        print(f"   📋 Gruppo: {gruppo_selezionato['ciclo_nome']} ({len(gruppo_selezionato['odl_list'])} ODL)")
        print(f"   🏭 Autoclave: {autoclave_selezionata.nome}")
        print(f"   📊 Utilizzo: {migliore_combinazione['utilizzo_area']:.1f}% area, {migliore_combinazione['utilizzo_valvole']:.1f}% valvole")
        
        return {
            "success": True,
            "message": f"Selezione automatica completata: {len(gruppo_selezionato['odl_list'])} ODL per autoclave {autoclave_selezionata.nome}",
            "odl_groups": [gruppo_selezionato],  # Solo il gruppo selezionato
            "selected_autoclave": {
                "id": autoclave_selezionata.id,
                "nome": autoclave_selezionata.nome,
                "codice": autoclave_selezionata.codice,
                "area_totale_cm2": migliore_combinazione["area_disponibile"],
                "valvole_totali": autoclave_selezionata.num_linee_vuoto,
                "max_load_kg": autoclave_selezionata.max_load_kg,
                "usa_piano_secondario": migliore_combinazione["usa_piano_secondario"]
            },
            "selection_criteria": {
                "utilizzo_area": migliore_combinazione["utilizzo_area"],
                "utilizzo_valvole": migliore_combinazione["utilizzo_valvole"],
                "utilizzo_peso": migliore_combinazione["utilizzo_peso"],
                "area_richiesta": migliore_combinazione["area_richiesta"],
                "valvole_richieste": migliore_combinazione["valvole_richieste"],
                "peso_richiesto": migliore_combinazione["peso_richiesto"],
                "carichi_oggi": migliore_combinazione["carichi_oggi"],
                "punteggio": migliore_combinazione["punteggio"],
                "odl_esclusi": odl_esclusi,
                "autoclavi_valutate": len(autoclavi_disponibili),
                "gruppi_ciclo_totali": len(gruppi_ciclo)
            }
        }
        
    except Exception as e:
        print(f"❌ Errore nella selezione automatica: {str(e)}")
        return {
            "success": False,
            "message": f"Errore durante la selezione automatica: {str(e)}",
            "odl_groups": [],
            "selected_autoclave": None,
            "selection_criteria": {}
        }

async def run_manual_nesting(db: Session, odl_ids: List[int], note: Optional[str] = None) -> NestingResultSchema:
    """
    Esegue il nesting manuale con gli ODL specificati
    
    Args:
        db: Sessione del database
        odl_ids: Lista degli ID degli ODL da includere nel nesting
        note: Note opzionali per il nesting
        
    Returns:
        Schema NestingResultSchema con i risultati dell'ottimizzazione
        
    Raises:
        ValueError: Se gli ODL non sono validi o già assegnati
    """
    # Valida che la lista non sia vuota
    if not odl_ids:
        raise ValueError("Deve essere selezionato almeno un ODL per creare il nesting")
    
    # Recupera gli ODL dal database
    odl_list = db.query(ODL).options(
        joinedload(ODL.parte).joinedload(Parte.catalogo),
        joinedload(ODL.tool)
    ).filter(ODL.id.in_(odl_ids)).all()
    
    # Verifica che tutti gli ODL siano stati trovati
    found_ids = {odl.id for odl in odl_list}
    missing_ids = set(odl_ids) - found_ids
    if missing_ids:
        raise ValueError(f"ODL non trovati: {', '.join(map(str, missing_ids))}")
    
    # Verifica che tutti gli ODL siano in stato "Attesa Cura"
    invalid_status_odl = [odl for odl in odl_list if odl.status != "Attesa Cura"]
    if invalid_status_odl:
        invalid_ids = [str(odl.id) for odl in invalid_status_odl]
        raise ValueError(f"Gli ODL {', '.join(invalid_ids)} non sono in stato 'Attesa Cura'")
    
    # Verifica che nessun ODL sia già assegnato a un nesting attivo
    for odl in odl_list:
        existing_nesting = db.query(NestingResult).filter(
            NestingResult.odl_ids.contains([odl.id]),
            NestingResult.stato.in_(["In attesa schedulazione", "Schedulato", "In corso"])
        ).first()
        
        if existing_nesting:
            raise ValueError(f"L'ODL {odl.id} è già assegnato al nesting #{existing_nesting.id}")
    
    # Verifica che tutti gli ODL abbiano i dati necessari per il nesting
    invalid_data_odl = []
    for odl in odl_list:
        # Verifica che l'ODL abbia tool, parte e dati necessari
        if not (odl.parte and 
                odl.tool and
                odl.tool.lunghezza_piano and 
                odl.tool.larghezza_piano and
                odl.tool.area > 0 and
                odl.parte.num_valvole_richieste and 
                odl.parte.num_valvole_richieste > 0):
            invalid_data_odl.append(odl)
    
    if invalid_data_odl:
        invalid_ids = [str(odl.id) for odl in invalid_data_odl]
        raise ValueError(f"Gli ODL {', '.join(invalid_ids)} non hanno dati sufficienti per il nesting (area o valvole mancanti)")
    
    # Recupera tutte le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    if not autoclavi:
        raise ValueError("Nessuna autoclave disponibile per il nesting")
    
    # Esegui l'algoritmo di nesting con gli ODL selezionati
    result = compute_nesting(db, odl_list, autoclavi)
    
    # Verifica che almeno alcuni ODL siano stati pianificati
    total_planned = sum(len(odl_ids) for odl_ids in result.assegnamenti.values())
    if total_planned == 0:
        raise ValueError("Nessun ODL può essere pianificato nelle autoclavi disponibili")
    
    # Aggiorna lo stato degli ODL nel database e salva i risultati
    odl_pianificati = []
    odl_non_pianificabili = []
    autoclavi_info = []
    
    # Salva il risultato nel database per ogni autoclave usata
    for autoclave_id, assigned_odl_ids in result.assegnamenti.items():
        if not assigned_odl_ids:
            continue
            
        # Trova l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
        if not autoclave:
            continue
        
        # ✅ SEZIONE 1: Aggiorna lo stato dell'autoclave a "IN USO" per nesting manuale
        autoclave.stato = StatoAutoclaveEnum.IN_USO
        db.add(autoclave)
        
        # Crea un nuovo record NestingResult
        stats = result.statistiche_autoclavi.get(autoclave_id, {})
        nesting_record = NestingResult(
            autoclave_id=autoclave_id,
            odl_ids=assigned_odl_ids,
            odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
            motivi_esclusione=result.odl_non_pianificabili,
            stato="In sospeso",  # ✅ Cambiato da "In attesa schedulazione" a "In sospeso" per uniformità
            area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
            area_totale=float(stats.get("area_totale", 0.0)),
            valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
            valvole_totali=autoclave.num_linee_vuoto,
            peso_totale_kg=sum(getattr(odl.tool, 'peso', 0.5) for odl in assigned_odl_ids if odl.tool),
            note=note or "Nesting manuale creato dal management"
        )
        
        # Salva nel database
        db.add(nesting_record)
        db.flush()  # Per ottenere l'ID
        
        # ✅ SEZIONE 1: Non cambiare lo stato degli ODL finché il nesting non viene confermato
        # Gli ODL rimangono in "Attesa Cura" finché il nesting non viene confermato dall'operatore Curing
        
        # Aggiungi alle informazioni di ritorno per ogni ODL assegnato
        for odl_id in assigned_odl_ids:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl:
                odl_pianificati.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                    num_valvole=odl.parte.num_valvole_richieste if odl.parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.PIANIFICATO
                ))
        
        # Aggiungi alle informazioni dell'autoclave
        autoclavi_info.append(AutoclaveNestingInfo(
            id=autoclave.id,
            nome=autoclave.nome,
            odl_assegnati=assigned_odl_ids,
            valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
            valvole_totali=autoclave.num_linee_vuoto,
            area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
            area_totale=float(stats.get("area_totale", 0.0))
        ))
    
    # Gestisci gli ODL non pianificabili
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            odl_non_pianificabili.append(ODLNestingInfo(
                id=odl.id,
                parte_descrizione=odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                num_valvole=odl.parte.num_valvole_richieste if odl.parte else 0,
                priorita=odl.priorita,
                status=NestingODLStatus.NON_PIANIFICABILE
            ))
    
    # Salva tutte le modifiche
    db.commit()
    
    # Restituisci il risultato
    return NestingResultSchema(
        success=True,
        message=f"Nesting manuale completato: {len(odl_pianificati)} ODL pianificati, {len(odl_non_pianificabili)} esclusi",
        autoclavi=autoclavi_info,
        odl_pianificati=odl_pianificati,
        odl_non_pianificabili=odl_non_pianificabili
    )

# ✅ NUOVO: Funzione per nesting su due piani
async def run_two_level_nesting(
    db: Session, 
    autoclave_id: int, 
    odl_ids: Optional[List[int]] = None,
    superficie_piano_2_max_cm2: Optional[float] = None,
    note: Optional[str] = None
) -> Dict:
    """
    Esegue il nesting ottimizzato su due piani per un'autoclave specifica
    
    Args:
        db: Sessione del database
        autoclave_id: ID dell'autoclave target
        odl_ids: Lista opzionale degli ID degli ODL da includere (se None, usa tutti gli ODL in attesa)
        superficie_piano_2_max_cm2: Superficie massima del piano 2 in cm²
        note: Note opzionali per il nesting
        
    Returns:
        Dizionario con i risultati del nesting su due piani
        
    Raises:
        ValueError: Se l'autoclave non è valida o gli ODL non sono disponibili
    """
    # Recupera l'autoclave
    autoclave = db.query(Autoclave).filter(
        Autoclave.id == autoclave_id,
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).first()
    
    if not autoclave:
        raise ValueError(f"Autoclave {autoclave_id} non trovata o non disponibile")
    
    # Verifica che l'autoclave abbia i dati necessari per il nesting su due piani
    if not autoclave.max_load_kg:
        raise ValueError(f"Autoclave {autoclave.nome} non ha il carico massimo configurato")
    
    # Recupera gli ODL da processare
    if odl_ids:
        # ODL specificati manualmente
        odl_list = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(ODL.tool)
        ).filter(ODL.id.in_(odl_ids)).all()
        
        # Verifica che tutti gli ODL siano stati trovati
        found_ids = {odl.id for odl in odl_list}
        missing_ids = set(odl_ids) - found_ids
        if missing_ids:
            raise ValueError(f"ODL non trovati: {', '.join(map(str, missing_ids))}")
    else:
        # Usa tutti gli ODL in attesa di cura
        odl_list = await get_odl_attesa_cura_filtered(db)
    
    if not odl_list:
        raise ValueError("Nessun ODL disponibile per il nesting")
    
    # Esegui l'algoritmo di nesting su due piani
    result = compute_two_level_nesting(
        db=db,
        odl_list=odl_list,
        autoclave=autoclave,
        superficie_piano_2_max_cm2=superficie_piano_2_max_cm2
    )
    
    # Verifica che il carico sia valido
    if not result.carico_valido:
        raise ValueError(f"Nesting non valido: {result.motivo_invalidita}")
    
    # Verifica che almeno alcuni ODL siano stati pianificati
    total_planned = len(result.piano_1) + len(result.piano_2)
    if total_planned == 0:
        raise ValueError("Nessun ODL può essere pianificato nell'autoclave selezionata")
    
    # Prepara le posizioni combinate per entrambi i piani
    posizioni_combinate = []
    posizioni_combinate.extend(result.posizioni_piano_1)
    posizioni_combinate.extend(result.posizioni_piano_2)
    
    # ✅ SEZIONE 1: Aggiorna lo stato dell'autoclave a "IN USO" per nesting su due piani
    autoclave.stato = StatoAutoclaveEnum.IN_USO
    db.add(autoclave)
    
    # Crea un nuovo record NestingResult nel database
    nesting_record = NestingResult(
        autoclave_id=autoclave_id,
        odl_ids=result.piano_1 + result.piano_2,
        odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
        motivi_esclusione=result.odl_non_pianificabili,
        stato="In sospeso",  # ✅ Cambiato da "In attesa schedulazione" a "In sospeso" per uniformità
        area_utilizzata=result.area_piano_1 + result.area_piano_2,
        area_totale=autoclave.area_piano,
        valvole_utilizzate=0,  # Da calcolare se necessario
        valvole_totali=autoclave.num_linee_vuoto,
        # ✅ NUOVO: Campi specifici per nesting su due piani
        peso_totale_kg=result.peso_totale,
        area_piano_1=result.area_piano_1,
        area_piano_2=result.area_piano_2,
        superficie_piano_2_max=superficie_piano_2_max_cm2,
        posizioni_tool=posizioni_combinate,
        note=note or f"Nesting automatico su due piani - Piano 1: {len(result.piano_1)} ODL, Piano 2: {len(result.piano_2)} ODL"
    )
    
    # Salva nel database
    db.add(nesting_record)
    db.flush()  # Per ottenere l'ID
    
    # ✅ SEZIONE 1: Non cambiare lo stato degli ODL finché il nesting non viene confermato
                # Gli ODL rimangono in "Attesa Cura" finché il nesting non viene confermato dall'operatore Curing
    odl_pianificati = []
    for odl_id in result.piano_1 + result.piano_2:
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            
            # Determina il piano assegnato
            piano_assegnato = 1 if odl_id in result.piano_1 else 2
            
            odl_pianificati.append({
                "id": odl.id,
                "parte_descrizione": odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                "tool_part_number": odl.tool.part_number_tool if odl.tool else "N/A",
                "tool_peso_kg": odl.tool.peso if odl.tool and odl.tool.peso else 0.0,
                "piano_assegnato": piano_assegnato,
                "priorita": odl.priorita,
                "status": "PIANIFICATO"
            })
    
    # Prepara la lista degli ODL non pianificabili
    odl_non_pianificabili = []
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            odl_non_pianificabili.append({
                "id": odl.id,
                "parte_descrizione": odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                "tool_part_number": odl.tool.part_number_tool if odl.tool else "N/A",
                "motivo": motivo,
                "priorita": odl.priorita,
                "status": "NON_PIANIFICABILE"
            })
    
    # Salva tutte le modifiche
    db.commit()
    
    # Restituisci il risultato dettagliato
    return {
        "success": True,
        "nesting_id": nesting_record.id,
        "message": f"Nesting su due piani completato: {len(result.piano_1)} ODL piano 1, {len(result.piano_2)} ODL piano 2, {len(result.odl_non_pianificabili)} esclusi",
        "autoclave": {
            "id": autoclave.id,
            "nome": autoclave.nome,
            "max_load_kg": autoclave.max_load_kg,
            "area_totale_cm2": autoclave.area_piano
        },
        "statistiche": {
            "peso_totale_kg": result.peso_totale,
            "peso_piano_1_kg": result.peso_piano_1,
            "peso_piano_2_kg": result.peso_piano_2,
            "area_piano_1_cm2": result.area_piano_1,
            "area_piano_2_cm2": result.area_piano_2,
            "superficie_piano_2_max_cm2": superficie_piano_2_max_cm2,
            "efficienza_piano_1": nesting_record.efficienza_piano_1,
            "efficienza_piano_2": nesting_record.efficienza_piano_2,
            "efficienza_totale": nesting_record.efficienza_totale,
            "carico_valido": result.carico_valido
        },
        "piano_1": {
            "odl_count": len(result.piano_1),
            "odl_ids": result.piano_1,
            "peso_kg": result.peso_piano_1,
            "area_cm2": result.area_piano_1,
            "posizioni": result.posizioni_piano_1
        },
        "piano_2": {
            "odl_count": len(result.piano_2),
            "odl_ids": result.piano_2,
            "peso_kg": result.peso_piano_2,
            "area_cm2": result.area_piano_2,
            "posizioni": result.posizioni_piano_2
        },
        "odl_pianificati": odl_pianificati,
        "odl_non_pianificabili": odl_non_pianificabili
    } 

async def generate_multi_nesting(db: Session) -> Dict:
    """
    ✅ PROMPT 14.3B.2 - AUTOMAZIONE NESTING SU AUTOCLAVI DISPONIBILI
    
    Implementa una funzione backend che, partendo dagli ODL in `ATTESA CURA`, 
    generi automaticamente uno o più nesting associati alle autoclavi disponibili, 
    ottimizzando l'utilizzo delle risorse (area, peso, valvole).
    
    LOGICA:
    1. Recupera tutti gli ODL in stato `ATTESA CURA` validi
    2. Recupera tutte le autoclavi in stato `DISPONIBILE`
    3. Per ogni autoclave disponibile:
       - Seleziona gruppo compatibile di ODL (area, peso, valvole)
       - Se `use_secondary_plane` è attivo, sfrutta anche il secondo piano
       - Assegna ODL al nesting
       - Crea oggetto `NestingResult` con stato `SOSPESO`
       - Aggiorna autoclave a `IN_USO`
       - Mantiene ODL in `ATTESA CURA` (cambieranno solo alla conferma)
    
    Args:
        db: Sessione del database
        
    Returns:
        Dizionario con i risultati dell'automazione multi-nesting
        
    Raises:
        ValueError: Se non ci sono ODL o autoclavi disponibili
    """
    logger.info("🚀 Avvio automazione nesting su autoclavi disponibili")
    
    # ✅ STEP 1: Recupera tutti gli ODL in stato "ATTESA CURA" validi
    odl_list = await get_odl_attesa_cura_filtered(db)
    
    if not odl_list:
        logger.warning("❌ Nessun ODL in stato ATTESA CURA trovato")
        return {
            "success": False,
            "message": "Nessun ODL in stato ATTESA CURA disponibile per il nesting automatico",
            "nesting_creati": [],
            "odl_pianificati": [],
            "odl_non_pianificabili": [],
            "autoclavi_utilizzate": []
        }
    
    logger.info(f"📋 Trovati {len(odl_list)} ODL in ATTESA CURA")
    
    # ✅ STEP 2: Recupera tutte le autoclavi in stato `DISPONIBILE`
    autoclavi_disponibili = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    if not autoclavi_disponibili:
        logger.warning("❌ Nessuna autoclave disponibile trovata")
        return {
            "success": False,
            "message": "Nessuna autoclave in stato DISPONIBILE per il nesting automatico",
            "nesting_creati": [],
            "odl_pianificati": [],
            "odl_non_pianificabili": [],
            "autoclavi_utilizzate": []
        }
    
    logger.info(f"🏭 Trovate {len(autoclavi_disponibili)} autoclavi DISPONIBILI")
    
    # ✅ STEP 3: Raggruppa ODL per ciclo di cura compatibile
    cicli_compatibili = {}
    odl_senza_ciclo = []
    
    for odl in odl_list:
        # Estrai informazioni sul ciclo dalle note o dalla parte
        ciclo_id, ciclo_nome = extract_ciclo_cura_from_note(odl.note or "")
        
        # Se non trovato nelle note, usa un ciclo standard basato sul materiale/tipo parte
        if not ciclo_id and odl.parte:
            # Logica semplificata: raggruppa per tipo di materiale o caratteristiche simili
            ciclo_key = f"standard_{odl.parte.id % 3}"  # Simula 3 cicli standard
            ciclo_nome = f"Ciclo Standard {ciclo_key[-1]}"
            ciclo_id = int(ciclo_key[-1])
        else:
            ciclo_key = f"ciclo_{ciclo_id}" if ciclo_id else "senza_ciclo"
        
        if ciclo_key == "senza_ciclo":
            odl_senza_ciclo.append(odl)
        else:
            if ciclo_key not in cicli_compatibili:
                cicli_compatibili[ciclo_key] = {
                    'nome': ciclo_nome,
                    'odl_list': [],
                    'id': ciclo_id
                }
            cicli_compatibili[ciclo_key]['odl_list'].append(odl)
    
    logger.info(f"🔄 Raggruppati ODL in {len(cicli_compatibili)} cicli compatibili, {len(odl_senza_ciclo)} senza ciclo")
    
    # ✅ STEP 4: Per ogni autoclave disponibile, cerca il miglior gruppo di ODL
    nesting_creati = []
    odl_pianificati = []
    odl_non_pianificabili = []
    autoclavi_utilizzate = []
    odl_assegnati_ids = set()  # Traccia ODL già assegnati per evitare duplicati
    
    for autoclave in autoclavi_disponibili:
        logger.info(f"🏭 Processando autoclave {autoclave.nome} (ID: {autoclave.id})")
        
        # Calcola capacità disponibile dell'autoclave
        area_totale_cm2 = autoclave.area_piano
        valvole_totali = autoclave.num_linee_vuoto or 0
        carico_max_kg = autoclave.max_load_kg or 1000.0
        use_secondary_plane = autoclave.use_secondary_plane or False
        
        # Se supporta secondo piano, raddoppia l'area disponibile
        if use_secondary_plane:
            area_totale_cm2 *= 2
            logger.info(f"✅ Autoclave {autoclave.nome} supporta secondo piano - Area totale: {area_totale_cm2:.1f} cm²")
        
        # ✅ STEP 5: Trova il miglior gruppo di ODL compatibili per questa autoclave
        miglior_gruppo = None
        miglior_score = -1
        miglior_ciclo_info = None
        
        for ciclo_key, ciclo_data in cicli_compatibili.items():
            odl_gruppo = [odl for odl in ciclo_data['odl_list'] if odl.id not in odl_assegnati_ids]
            
            if not odl_gruppo:
                continue  # Tutti gli ODL di questo ciclo sono già assegnati
            
            # Calcola requisiti del gruppo ODL
            area_richiesta = 0.0
            valvole_richieste = 0
            peso_stimato_kg = 0.0
            
            for odl in odl_gruppo:
                # Area del tool
                if odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano:
                    area_richiesta += (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) / 100
                
                # Valvole richieste
                if odl.parte and odl.parte.num_valvole_richieste:
                    valvole_richieste += odl.parte.num_valvole_richieste
                
                # Peso stimato (usa peso del tool se disponibile, altrimenti stima)
                if odl.tool and odl.tool.peso:
                    peso_stimato_kg += odl.tool.peso
                else:
                    peso_stimato_kg += 10.0  # Stima 10kg per ODL senza peso definito
            
            # ✅ Verifica vincoli di capacità
            if (area_richiesta > area_totale_cm2 or 
                valvole_richieste > valvole_totali or 
                peso_stimato_kg > carico_max_kg):
                logger.debug(f"❌ Gruppo {ciclo_key} non compatibile con {autoclave.nome}: "
                           f"area={area_richiesta:.1f}/{area_totale_cm2:.1f}, "
                           f"valvole={valvole_richieste}/{valvole_totali}, "
                           f"peso={peso_stimato_kg:.1f}/{carico_max_kg:.1f}")
                continue
            
            # ✅ Calcola score di ottimizzazione (efficienza utilizzo)
            efficienza_area = (area_richiesta / area_totale_cm2) * 100
            efficienza_valvole = (valvole_richieste / valvole_totali) * 100 if valvole_totali > 0 else 0
            efficienza_peso = (peso_stimato_kg / carico_max_kg) * 100
            
            # Score combinato (preferisce utilizzo bilanciato + numero di ODL)
            score = (efficienza_area + efficienza_valvole + efficienza_peso) / 3 + len(odl_gruppo) * 2
            
            logger.debug(f"📊 Gruppo {ciclo_key}: score={score:.1f}, "
                        f"efficienza_area={efficienza_area:.1f}%, "
                        f"efficienza_valvole={efficienza_valvole:.1f}%, "
                        f"efficienza_peso={efficienza_peso:.1f}%, "
                        f"ODL={len(odl_gruppo)}")
            
            if score > miglior_score:
                miglior_score = score
                miglior_gruppo = odl_gruppo
                miglior_ciclo_info = {
                    'key': ciclo_key,
                    'nome': ciclo_data['nome'],
                    'id': ciclo_data['id'],
                    'area_richiesta': area_richiesta,
                    'valvole_richieste': valvole_richieste,
                    'peso_stimato_kg': peso_stimato_kg
                }
        
        # ✅ STEP 6: Se trovato gruppo ottimale, crea nesting
        if miglior_gruppo and miglior_ciclo_info:
            logger.info(f"✅ Creando nesting per autoclave {autoclave.nome} con {len(miglior_gruppo)} ODL del {miglior_ciclo_info['nome']}")
            
            # ✅ Aggiorna lo stato dell'autoclave a "IN_USO"
            autoclave.stato = StatoAutoclaveEnum.IN_USO
            db.add(autoclave)
            
            # ✅ Prepara note complete con informazioni ciclo
            note_complete = (
                f"Nesting automatico multiplo - Ciclo di cura: {miglior_ciclo_info['nome']} (ID: {miglior_ciclo_info['id'] or 'N/A'})\n"
                f"Efficienza area: {(miglior_ciclo_info['area_richiesta'] / area_totale_cm2) * 100:.1f}%\n"
                f"Efficienza valvole: {(miglior_ciclo_info['valvole_richieste'] / valvole_totali) * 100:.1f}% ({miglior_ciclo_info['valvole_richieste']}/{valvole_totali})\n"
                f"Peso stimato: {miglior_ciclo_info['peso_stimato_kg']:.1f}kg / {carico_max_kg:.1f}kg\n"
                f"ODL assegnati: {len(miglior_gruppo)}\n"
                f"Secondo piano: {'Attivo' if use_secondary_plane else 'Non utilizzato'}"
            )
            
            # ✅ Crea record NestingResult con stato "SOSPESO"
            nesting_record = NestingResult(
                autoclave_id=autoclave.id,
                odl_ids=[odl.id for odl in miglior_gruppo],
                odl_esclusi_ids=[],
                motivi_esclusione=[],
                stato="In sospeso",  # ✅ Nesting resta in stato SOSPESO
                area_utilizzata=float(miglior_ciclo_info['area_richiesta']),
                area_totale=float(autoclave.area_piano),  # Area base (senza secondo piano)
                valvole_utilizzate=int(miglior_ciclo_info['valvole_richieste']),
                valvole_totali=valvole_totali,
                peso_totale_kg=miglior_ciclo_info['peso_stimato_kg'],
                area_piano_1=float(min(miglior_ciclo_info['area_richiesta'], autoclave.area_piano)),
                area_piano_2=float(max(0, miglior_ciclo_info['area_richiesta'] - autoclave.area_piano)) if use_secondary_plane else 0.0,
                superficie_piano_2_max=float(autoclave.area_piano) if use_secondary_plane else None,
                note=note_complete,
                posizioni_tool=[]  # Sarà popolato dal sistema di ottimizzazione 2D
            )
            
            # Aggiungi gli ODL al nesting (relazione many-to-many)
            for odl in miglior_gruppo:
                nesting_record.odl_list.append(odl)
                odl_assegnati_ids.add(odl.id)  # Marca come assegnato
            
            # Salva nel database
            db.add(nesting_record)
            db.flush()  # Per ottenere l'ID del nesting
            
            # Aggiungi ai risultati
            nesting_creati.append({
                "id": nesting_record.id,
                "autoclave_id": autoclave.id,
                "autoclave_nome": autoclave.nome,
                "odl_count": len(miglior_gruppo),
                "odl_ids": [odl.id for odl in miglior_gruppo],
                "ciclo_cura_nome": miglior_ciclo_info['nome'],
                "ciclo_cura_id": miglior_ciclo_info['id'],
                "area_utilizzata": miglior_ciclo_info['area_richiesta'],
                "area_totale": area_totale_cm2,
                "valvole_utilizzate": miglior_ciclo_info['valvole_richieste'],
                "valvole_totali": valvole_totali,
                "peso_kg": miglior_ciclo_info['peso_stimato_kg'],
                "use_secondary_plane": use_secondary_plane,
                "stato": "In sospeso"
            })
            
            # Aggiungi agli ODL pianificati
            for odl in miglior_gruppo:
                odl_pianificati.append({
                    "id": odl.id,
                    "parte_descrizione": odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                    "tool_part_number": odl.tool.part_number_tool if odl.tool else "N/A",
                    "priorita": odl.priorita,
                    "nesting_id": nesting_record.id,
                    "autoclave_nome": autoclave.nome,
                    "ciclo_cura": miglior_ciclo_info['nome'],
                    "status": "PIANIFICATO"
                })
            
            # Aggiungi autoclave utilizzata
            autoclavi_utilizzate.append({
                "id": autoclave.id,
                "nome": autoclave.nome,
                "codice": autoclave.codice,
                "stato_precedente": "DISPONIBILE",
                "stato_attuale": "IN_USO",
                "nesting_id": nesting_record.id,
                "odl_assegnati": len(miglior_gruppo)
            })
            
            logger.info(f"✅ Nesting creato con ID {nesting_record.id} per autoclave {autoclave.nome}")
        
        else:
            logger.info(f"❌ Nessun gruppo ODL compatibile trovato per autoclave {autoclave.nome}")
    
    # ✅ Gestisci ODL non pianificabili (quelli rimasti senza assegnazione)
    for odl in odl_list:
        if odl.id not in odl_assegnati_ids:
            motivo = "Nessuna autoclave disponibile compatibile con i requisiti dell'ODL"
            
            # Verifica motivo specifico
            if odl.tool and odl.tool.lunghezza_piano and odl.tool.larghezza_piano:
                area_odl = (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) / 100
                if area_odl > max(autoclave.area_piano for autoclave in autoclavi_disponibili):
                    motivo = "Area richiesta superiore alla capacità di tutte le autoclavi"
            
            if odl.parte and odl.parte.num_valvole_richieste:
                if odl.parte.num_valvole_richieste > max(autoclave.num_linee_vuoto or 0 for autoclave in autoclavi_disponibili):
                    motivo = "Numero valvole richieste superiore alla capacità di tutte le autoclavi"
            
            odl_non_pianificabili.append({
                "id": odl.id,
                "parte_descrizione": odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                "tool_part_number": odl.tool.part_number_tool if odl.tool else "N/A",
                "priorita": odl.priorita,
                "motivo": motivo,
                "status": "NON_PIANIFICABILE"
            })
    
    # ✅ Gestisci ODL senza ciclo definito
    for odl in odl_senza_ciclo:
        if odl.id not in odl_assegnati_ids:
            odl_non_pianificabili.append({
                "id": odl.id,
                "parte_descrizione": odl.parte.descrizione_breve if odl.parte else "Sconosciuta",
                "tool_part_number": odl.tool.part_number_tool if odl.tool else "N/A",
                "priorita": odl.priorita,
                "motivo": "Ciclo di cura non definito",
                "status": "NON_PIANIFICABILE"
            })
    
    # ✅ Commit delle modifiche al database
    db.commit()
    
    # ✅ Prepara messaggio di risultato
    if nesting_creati:
        message = (f"✅ Automazione nesting completata: "
                  f"{len(nesting_creati)} nesting creati su {len(autoclavi_utilizzate)} autoclavi, "
                  f"{len(odl_pianificati)} ODL pianificati, "
                  f"{len(odl_non_pianificabili)} ODL non pianificabili")
        success = True
    else:
        message = (f"❌ Nessun nesting creato: "
                  f"{len(odl_non_pianificabili)} ODL non pianificabili, "
                  f"verificare compatibilità con autoclavi disponibili")
        success = False
    
    logger.info(message)
    
    # ✅ Restituisci il risultato completo
    return {
        "success": success,
        "message": message,
        "nesting_creati": nesting_creati,
        "odl_pianificati": odl_pianificati,
        "odl_non_pianificabili": odl_non_pianificabili,
        "autoclavi_utilizzate": autoclavi_utilizzate,
        "statistiche": {
            "odl_totali": len(odl_list),
            "odl_pianificati": len(odl_pianificati),
            "odl_non_pianificabili": len(odl_non_pianificabili),
            "autoclavi_disponibili": len(autoclavi_disponibili),
            "autoclavi_utilizzate": len(autoclavi_utilizzate),
            "nesting_creati": len(nesting_creati),
            "cicli_compatibili": len(cicli_compatibili)
        }
    } 