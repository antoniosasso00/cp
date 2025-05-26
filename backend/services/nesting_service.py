"""
Servizio per la gestione del nesting automatico degli ODL nelle autoclavi.
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.nesting_result import NestingResult
from nesting_optimizer.auto_nesting import compute_nesting, NestingResult as OptimizationResult
from nesting_optimizer.two_level_nesting import compute_two_level_nesting, TwoLevelNestingResult
from schemas.nesting import NestingResultSchema, NestingPreviewSchema, AutoclavePreviewInfo, ODLPreviewInfo
from schemas.nesting import AutoclaveNestingInfo, ODLNestingInfo, NestingODLStatus
import random
import re

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

async def get_nesting_preview(db: Session) -> NestingPreviewSchema:
    """
    Genera un'anteprima del nesting senza salvarlo nel database
    
    Args:
        db: Sessione del database
        
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
    
    # Esegui l'algoritmo di nesting
    result = compute_nesting(db, odl_list, autoclavi)
    
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
    
    # Restituisci l'anteprima
    return NestingPreviewSchema(
        success=True,
        message=f"Anteprima generata: {len([odl for autoclave in autoclavi_preview for odl in autoclave.odl_inclusi])} ODL pianificati, {len(odl_esclusi)} esclusi",
        autoclavi=autoclavi_preview,
        odl_esclusi=odl_esclusi
    )

async def run_automatic_nesting(db: Session) -> NestingResultSchema:
    """
    Esegue l'algoritmo di nesting automatico per ottimizzare il posizionamento 
    degli ODL nelle autoclavi disponibili.
    
    Args:
        db: Sessione del database
        
    Returns:
        Schema NestingResult con i risultati dell'ottimizzazione
    """
    # Recupera tutti gli ODL in stato "Attesa Cura" filtrati e validati
    odl_list = await get_odl_attesa_cura_filtered(db)
    
    # Recupera tutte le autoclavi disponibili
    autoclavi = db.query(Autoclave).filter(
        Autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
    ).all()
    
    # Se non ci sono ODL o autoclavi, restituisci un risultato vuoto
    if not odl_list or not autoclavi:
        return NestingResultSchema(
            success=False,
            message="Nessun ODL in attesa o nessuna autoclave disponibile",
            autoclavi=[],
            odl_pianificati=[],
            odl_non_pianificabili=[]
        )
    
    # Esegui l'algoritmo di nesting
    result = compute_nesting(db, odl_list, autoclavi)
    
    # Aggiorna lo stato degli ODL nel database
    odl_pianificati = []
    odl_non_pianificabili = []
    
    # Salva il risultato nel database per ogni autoclave usata
    for autoclave_id, odl_ids in result.assegnamenti.items():
        if not odl_ids:
            continue
            
        # Trova l'autoclave
        autoclave = db.query(Autoclave).filter(Autoclave.id == autoclave_id).first()
        
        # Crea un nuovo record NestingResult
        stats = result.statistiche_autoclavi.get(autoclave_id, {})
        ciclo_info = result.cicli_cura_autoclavi.get(autoclave_id, {})
        
        # Prepara le note con informazioni sul ciclo di cura e statistiche
        efficienza_area = stats.get("efficienza_area", 0)
        efficienza_valvole = stats.get("efficienza_valvole", 0)
        note_ciclo = (f"Ciclo di cura: {ciclo_info.get('nome', 'Sconosciuto')} (ID: {ciclo_info.get('id', 'N/A')})\n"
                     f"Efficienza area: {efficienza_area:.1f}% | Efficienza valvole: {efficienza_valvole:.1f}%\n"
                     f"ODL posizionati: {stats.get('odl_posizionati', 0)}")
        
        # ✅ NUOVO: Recupera le posizioni 2D dei tool
        posizioni_tool = result.posizioni_tool.get(autoclave_id, [])
        
        nesting_record = NestingResult(
            autoclave_id=autoclave_id,
            odl_ids=odl_ids,
            odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
            motivi_esclusione=result.odl_non_pianificabili,
            stato="In sospeso",
            area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
            area_totale=float(stats.get("area_totale", 0.0)),
            valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
            valvole_totali=autoclave.num_linee_vuoto if autoclave else 0,
            note=note_ciclo,
            posizioni_tool=posizioni_tool  # ✅ NUOVO: Salva le posizioni 2D
        )
        
        # Aggiungi gli ODL al nesting
        for odl_id in odl_ids:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl:
                nesting_record.odl_list.append(odl)
        
        # Salva nel database
        db.add(nesting_record)
    
    # Aggiorna gli ODL pianificati
    for autoclave_id, odl_ids in result.assegnamenti.items():
        for odl_id in odl_ids:
            # Recupera l'ODL dal database
            odl = db.query(ODL).options(
                joinedload(ODL.parte).joinedload(Parte.catalogo)
            ).filter(ODL.id == odl_id).first()
            if odl:
                # Manteniamo lo stato "Attesa Cura" finché non viene schedulato
                
                # Recupera le informazioni sulla parte
                parte = odl.parte
                catalogo = parte.catalogo if parte else None
                
                # Aggiungi all'elenco degli ODL pianificati
                odl_pianificati.append(ODLNestingInfo(
                    id=odl.id,
                    parte_descrizione=parte.descrizione_breve if parte else "Sconosciuta",
                    num_valvole=parte.num_valvole_richieste if parte else 0,
                    priorita=odl.priorita,
                    status=NestingODLStatus.PIANIFICATO
                ))
    
    # Aggiorna gli ODL non pianificabili
    for item in result.odl_non_pianificabili:
        odl_id = item["odl_id"]
        motivo = item["motivo"]
        
        # Recupera l'ODL dal database
        odl = db.query(ODL).options(
            joinedload(ODL.parte).joinedload(Parte.catalogo)
        ).filter(ODL.id == odl_id).first()
        if odl:
            # Manteniamo lo stato "Attesa Cura"
            
            # Recupera le informazioni sulla parte
            parte = odl.parte
            
            # Aggiungi all'elenco degli ODL non pianificabili
            odl_non_pianificabili.append(ODLNestingInfo(
                id=odl.id,
                parte_descrizione=f"{parte.descrizione_breve if parte else 'Sconosciuta'} (Motivo: {motivo})",
                num_valvole=parte.num_valvole_richieste if parte else 0,
                priorita=odl.priorita,
                status=NestingODLStatus.NON_PIANIFICABILE
            ))
    
    # Commit delle modifiche al database
    db.commit()
    
    # Prepara le informazioni sulle autoclavi
    autoclavi_info = []
    for autoclave in autoclavi:
        # Verifica se questa autoclave è stata utilizzata nel nesting
        if autoclave.id in result.assegnamenti:
            # Recupera le statistiche per questa autoclave
            stats = result.statistiche_autoclavi.get(autoclave.id, {})
            
            ciclo_info = result.cicli_cura_autoclavi.get(autoclave.id, {})
            
            autoclavi_info.append(AutoclaveNestingInfo(
                id=autoclave.id,
                nome=autoclave.nome,
                odl_assegnati=result.assegnamenti[autoclave.id],
                valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
                valvole_totali=autoclave.num_linee_vuoto,
                area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
                area_totale=float(stats.get("area_totale", 0.0)),
                ciclo_cura_id=ciclo_info.get("id"),
                ciclo_cura_nome=ciclo_info.get("nome")
            ))
    
    # Restituisci il risultato
    return NestingResultSchema(
        success=True,
        message=f"Nesting completato: {len(odl_pianificati)} ODL pianificati, {len(odl_non_pianificabili)} non pianificabili",
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
    if ruolo_utente == "AUTOCLAVISTA":
        # L'autoclavista può solo confermare nesting in sospeso
        if nesting.stato != "In sospeso":
            raise ValueError("L'autoclavista può confermare solo nesting in sospeso")
        if nuovo_stato not in ["Confermato", "Annullato"]:
            raise ValueError("L'autoclavista può solo confermare o annullare nesting")
    elif ruolo_utente == "RESPONSABILE":
        # Il responsabile può modificare qualsiasi nesting non completato
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
    
    # Gestione cambio stato degli ODL
    if nuovo_stato == "Confermato":
        # Quando il nesting viene confermato, gli ODL passano in "Cura"
        for odl in nesting.odl_list:
            if odl.status == "Attesa Cura":
                odl.status = "Cura"  # Cambia lo stato a "Cura" (In Autoclave)
                db.add(odl)
    
    elif nuovo_stato == "Annullato":
        # Se il nesting viene annullato, riporta gli ODL in "Attesa Cura"
        for odl in nesting.odl_list:
            if odl.status == "Cura":
                odl.status = "Attesa Cura"  # Riporta in attesa
                db.add(odl)
    
    elif nuovo_stato == "Completato":
        # Quando il nesting è completato, gli ODL passano a "Finito"
        for odl in nesting.odl_list:
            if odl.status == "Cura":
                odl.status = "Finito"
                db.add(odl)
    
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
            
            # Verifica che abbia tutti i dati necessari
            if (odl.parte and 
                odl.parte.catalogo and 
                odl.parte.catalogo.area_cm2 and 
                odl.parte.catalogo.area_cm2 > 0 and
                odl.parte.num_valvole_richieste and 
                odl.parte.num_valvole_richieste > 0):
                
                odl_validi.append(odl)
        
        return odl_validi
        
    except Exception as e:
        print(f"Errore nel filtro ODL Attesa Cura: {str(e)}")
        return [] 

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
        if not (odl.parte and 
                odl.parte.catalogo and 
                odl.parte.catalogo.area_cm2 and 
                odl.parte.catalogo.area_cm2 > 0 and
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
        
        # Crea un nuovo record NestingResult
        stats = result.statistiche_autoclavi.get(autoclave_id, {})
        nesting_record = NestingResult(
            autoclave_id=autoclave_id,
            odl_ids=assigned_odl_ids,
            odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
            motivi_esclusione=result.odl_non_pianificabili,
            stato="In attesa schedulazione",
            area_utilizzata=float(stats.get("area_utilizzata", 0.0)),
            area_totale=float(stats.get("area_totale", 0.0)),
            valvole_utilizzate=int(stats.get("valvole_utilizzate", 0)),
            valvole_totali=autoclave.num_linee_vuoto,
            note=note or "Nesting manuale creato dal responsabile"
        )
        
        # Salva nel database
        db.add(nesting_record)
        db.flush()  # Per ottenere l'ID
        
        # Aggiorna lo stato degli ODL assegnati
        for odl_id in assigned_odl_ids:
            odl = db.query(ODL).filter(ODL.id == odl_id).first()
            if odl:
                odl.status = "Cura"
                db.add(odl)
                
                # Aggiungi alle informazioni di ritorno
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
    
    # Crea un nuovo record NestingResult nel database
    nesting_record = NestingResult(
        autoclave_id=autoclave_id,
        odl_ids=result.piano_1 + result.piano_2,
        odl_esclusi_ids=[item["odl_id"] for item in result.odl_non_pianificabili],
        motivi_esclusione=result.odl_non_pianificabili,
        stato="In attesa schedulazione",
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
    
    # Aggiorna lo stato degli ODL pianificati
    odl_pianificati = []
    for odl_id in result.piano_1 + result.piano_2:
        odl = db.query(ODL).filter(ODL.id == odl_id).first()
        if odl:
            odl.status = "Cura"
            db.add(odl)
            
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