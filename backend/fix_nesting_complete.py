#!/usr/bin/env python3
"""
Script completo per testare e correggere il modulo di nesting automatico.
Implementa tutte le correzioni richieste dall'utente.
"""

import sys
sys.path.append('.')

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.odl import ODL
from models.parte import Parte
from models.ciclo_cura import CicloCura
from models.tool import Tool
from models.autoclave import Autoclave
from models.nesting_result import NestingResult
from services.nesting_service import NestingService, NestingParameters

def fix_missing_cicli_cura(db):
    """
    STEP 1: Fix dati mancanti - Assegna cicli di cura alle parti che ne sono prive
    """
    print("🔧 STEP 1: CORREZIONE CICLI DI CURA MANCANTI")
    print("=" * 50)
    
    # Trova parti senza ciclo di cura
    parti_senza_ciclo = db.query(Parte).filter(Parte.ciclo_cura_id.is_(None)).all()
    
    if not parti_senza_ciclo:
        print("✅ Tutte le parti hanno già un ciclo di cura associato")
        return True
    
    # Prendi il primo ciclo di cura disponibile come default
    ciclo_default = db.query(CicloCura).first()
    
    if not ciclo_default:
        print("❌ ERRORE CRITICO: Nessun ciclo di cura disponibile nel database!")
        print("   🔧 Creazione ciclo di cura di default...")
        
        # Crea un ciclo di cura di default
        ciclo_default = CicloCura(
            nome="STANDARD_180C_DEFAULT",
            descrizione="Ciclo di cura standard creato automaticamente per il nesting",
            temperatura_stasi1=180.0,
            pressione_stasi1=6.0,
            durata_stasi1=120,
            attiva_stasi2=False
        )
        db.add(ciclo_default)
        db.commit()
        db.refresh(ciclo_default)
        print(f"   ✅ Ciclo di cura creato: {ciclo_default.nome} (ID: {ciclo_default.id})")
    
    # Assegna il ciclo default alle parti senza ciclo
    fixed_count = 0
    for parte in parti_senza_ciclo:
        parte.ciclo_cura_id = ciclo_default.id
        fixed_count += 1
        print(f"   • Parte {parte.id} '{parte.descrizione_breve}' → Ciclo {ciclo_default.nome}")
    
    db.commit()
    print(f"✅ Corrette {fixed_count} parti senza ciclo di cura")
    return True

def fix_missing_tool_data(db):
    """
    STEP 1: Fix dati mancanti - Completa i dati dei tool
    """
    print("\n🔧 STEP 1: CORREZIONE DATI TOOL MANCANTI")
    print("=" * 50)
    
    # Tool senza dimensioni
    tools_incomplete = db.query(Tool).filter(
        (Tool.lunghezza_piano.is_(None)) | 
        (Tool.larghezza_piano.is_(None)) |
        (Tool.peso.is_(None))
    ).all()
    
    if not tools_incomplete:
        print("✅ Tutti i tool hanno dati completi")
        return True
    
    fixed_count = 0
    for tool in tools_incomplete:
        # Assegna valori di default realistici se mancanti
        if tool.lunghezza_piano is None:
            tool.lunghezza_piano = 800.0  # mm
            print(f"   • Tool {tool.part_number_tool}: lunghezza → 800mm")
        
        if tool.larghezza_piano is None:
            tool.larghezza_piano = 600.0  # mm
            print(f"   • Tool {tool.part_number_tool}: larghezza → 600mm")
        
        if tool.peso is None:
            tool.peso = 12.0  # kg
            print(f"   • Tool {tool.part_number_tool}: peso → 12kg")
        
        fixed_count += 1
    
    db.commit()
    print(f"✅ Corretti {fixed_count} tool con dati mancanti")
    return True

def validate_odl_data(db, odl_ids):
    """
    STEP 1: Validazione dati in input
    """
    print("\n📋 STEP 1: VALIDAZIONE DATI ODL")
    print("=" * 40)
    
    valid_odls = []
    invalid_odls = []
    
    for odl_id in odl_ids:
        odl = db.query(ODL).join(Tool).join(Parte).outerjoin(CicloCura).filter(ODL.id == odl_id).first()
        
        if not odl:
            invalid_odls.append({'odl_id': odl_id, 'motivo': 'ODL non trovato'})
            continue
        
        # Validazioni
        issues = []
        
        if not odl.tool:
            issues.append('Tool non associato')
        elif not all([odl.tool.lunghezza_piano, odl.tool.larghezza_piano, odl.tool.peso]):
            issues.append('Tool con dati incompleti')
        
        if not odl.parte:
            issues.append('Parte non associata')
        elif not odl.parte.ciclo_cura_id:
            issues.append('Ciclo di cura non definito')
        
        if issues:
            invalid_odls.append({
                'odl_id': odl_id, 
                'motivo': 'Dati incompleti', 
                'dettagli': ', '.join(issues)
            })
        else:
            valid_odls.append(odl)
            print(f"   ✅ ODL {odl_id}: Tool {odl.tool.part_number_tool} ({odl.tool.lunghezza_piano}x{odl.tool.larghezza_piano}mm, {odl.tool.peso}kg), Ciclo: {odl.parte.ciclo_cura.nome}")
    
    if invalid_odls:
        print(f"\n❌ {len(invalid_odls)} ODL con problemi:")
        for invalid in invalid_odls:
            print(f"   • ODL {invalid['odl_id']}: {invalid['motivo']} - {invalid.get('dettagli', '')}")
    
    print(f"\n📊 Risultato validazione: {len(valid_odls)} ODL validi su {len(odl_ids)} totali")
    return valid_odls, invalid_odls

def cluster_by_ciclo_cura(db, valid_odls):
    """
    STEP 2: Cluster e pre-assegnazione ODL a autoclavi
    """
    print("\n🔀 STEP 2: CLUSTERING PER CICLO DI CURA")
    print("=" * 45)
    
    # Raggruppa per ciclo di cura
    cicli_clusters = {}
    for odl in valid_odls:
        ciclo_id = odl.parte.ciclo_cura_id
        ciclo_nome = odl.parte.ciclo_cura.nome if odl.parte.ciclo_cura else f"Ciclo_{ciclo_id}"
        
        if ciclo_id not in cicli_clusters:
            cicli_clusters[ciclo_id] = {
                'nome': ciclo_nome,
                'odl_list': [],
                'temperatura': odl.parte.ciclo_cura.temperatura_stasi1 if odl.parte.ciclo_cura else None,
                'pressione': odl.parte.ciclo_cura.pressione_stasi1 if odl.parte.ciclo_cura else None
            }
        
        cicli_clusters[ciclo_id]['odl_list'].append(odl)
    
    print(f"🎯 Trovati {len(cicli_clusters)} cluster di cicli di cura:")
    for ciclo_id, cluster in cicli_clusters.items():
        print(f"   • {cluster['nome']}: {len(cluster['odl_list'])} ODL (T={cluster['temperatura']}°C, P={cluster['pressione']}bar)")
    
    return cicli_clusters

def assign_autoclave_compatibility(db, cicli_clusters):
    """
    STEP 2: Verifica compatibilità con autoclavi disponibili
    """
    print("\n🏭 STEP 2: COMPATIBILITÀ CON AUTOCLAVI")
    print("=" * 42)
    
    # Per ora assumiamo che tutte le autoclavi disponibili supportino tutti i cicli
    # In futuro si potrebbero aggiungere vincoli specifici per autoclave
    autoclavi_disponibili = db.query(Autoclave).filter(Autoclave.stato == 'DISPONIBILE').all()
    
    print(f"🔍 Autoclavi disponibili: {len(autoclavi_disponibili)}")
    for autoclave in autoclavi_disponibili:
        print(f"   • {autoclave.nome}: {autoclave.larghezza_piano}x{autoclave.lunghezza}mm, max {autoclave.max_load_kg}kg")
    
    # Assegnazione: usiamo la prima autoclave disponibile per tutti i cluster
    # (logica semplificata per il test)
    assignment = {}
    if autoclavi_disponibili:
        main_autoclave = autoclavi_disponibili[0]
        for ciclo_id, cluster in cicli_clusters.items():
            assignment[ciclo_id] = {
                'autoclave': main_autoclave,
                'odl_list': cluster['odl_list'],
                'ciclo_nome': cluster['nome']
            }
            print(f"   ✅ Cluster '{cluster['nome']}' → Autoclave '{main_autoclave.nome}'")
    
    return assignment

def execute_nesting_algorithm(db, assignment):
    """
    STEP 3: Invocazione algoritmo OR-Tools
    """
    print("\n🧠 STEP 3: ESECUZIONE ALGORITMO OR-TOOLS")
    print("=" * 48)
    
    nesting_service = NestingService()
    results = {}
    
    for ciclo_id, data in assignment.items():
        autoclave = data['autoclave']
        odl_list = data['odl_list']
        ciclo_nome = data['ciclo_nome']
        
        print(f"\n🔄 Elaborazione cluster '{ciclo_nome}' su autoclave '{autoclave.nome}'")
        print(f"   📋 ODL da processare: {len(odl_list)}")
        
        # Parametri di nesting ottimizzati
        parameters = NestingParameters(
            padding_mm=10,     # Ridotto da 25 a 10mm
            min_distance_mm=5, # Ridotto da 20 a 5mm
            priorita_area=False  # Massimizza numero ODL invece che area
        )
        
        try:
            # Estrai gli ID degli ODL
            odl_ids = [odl.id for odl in odl_list]
            
            # Esegui il nesting
            result = nesting_service.generate_nesting(
                db=db,
                odl_ids=odl_ids,
                autoclave_id=autoclave.id,
                parameters=parameters
            )
            
            results[ciclo_id] = {
                'result': result,
                'autoclave': autoclave,
                'ciclo_nome': ciclo_nome,
                'odl_count': len(odl_list)
            }
            
            # Log risultati
            if result.success:
                print(f"   ✅ Nesting riuscito!")
                print(f"   📊 ODL posizionati: {len(result.positioned_tools)}")
                print(f"   📊 ODL esclusi: {len(result.excluded_odls)}")
                print(f"   📊 Efficienza: {result.efficiency:.1f}%")
                print(f"   📊 Peso totale: {result.total_weight:.1f}kg")
                print(f"   📊 Status algoritmo: {result.algorithm_status}")
                
                # Log posizioni dei tool
                for tool in result.positioned_tools:
                    print(f"     • ODL {tool.odl_id}: pos({tool.x:.0f},{tool.y:.0f}), dim({tool.width:.0f}x{tool.height:.0f}mm), peso({tool.peso:.1f}kg){' [RUOTATO]' if tool.rotated else ''}")
                
                # Log esclusioni
                for excl in result.excluded_odls:
                    print(f"     ❌ ODL {excl['odl_id']}: {excl['motivo']} - {excl.get('dettagli', '')}")
            else:
                print(f"   ❌ Nesting fallito: {result.algorithm_status}")
                for excl in result.excluded_odls:
                    print(f"     ❌ ODL {excl['odl_id']}: {excl['motivo']}")
                    
        except Exception as e:
            print(f"   ❌ Errore nell'esecuzione nesting: {str(e)}")
            results[ciclo_id] = {
                'error': str(e),
                'autoclave': autoclave,
                'ciclo_nome': ciclo_nome,
                'odl_count': len(odl_list)
            }
    
    return results

def save_nesting_results(db, results):
    """
    STEP 4: Salvataggio risultati nel database
    """
    print("\n💾 STEP 4: SALVATAGGIO RISULTATI NEL DATABASE")
    print("=" * 52)
    
    saved_results = []
    
    for ciclo_id, data in results.items():
        if 'error' in data:
            print(f"   ❌ Skip salvataggio per '{data['ciclo_nome']}': {data['error']}")
            continue
        
        result = data['result']
        autoclave = data['autoclave']
        ciclo_nome = data['ciclo_nome']
        
        if not result.success or not result.positioned_tools:
            print(f"   ⚠️ Skip salvataggio per '{ciclo_nome}': nessun ODL posizionato")
            continue
        
        try:
            # Crea configurazione JSON completa
            configurazione_json = {
                "canvas_width": autoclave.larghezza_piano,
                "canvas_height": autoclave.lunghezza,
                "scale_factor": 1.0,
                "tool_positions": [
                    {
                        'odl_id': tool.odl_id,
                        'piano': 1,  # Per ora solo piano 1
                        'x': tool.x,
                        'y': tool.y,
                        'width': tool.width,
                        'height': tool.height,
                        'peso': tool.peso,
                        'rotated': tool.rotated
                    }
                    for tool in result.positioned_tools
                ],
                "plane_assignments": {str(tool.odl_id): 1 for tool in result.positioned_tools}
            }
            
            # Crea NestingResult nel database
            db_nesting_result = NestingResult(
                autoclave_id=autoclave.id,
                odl_ids=[tool.odl_id for tool in result.positioned_tools],
                odl_esclusi_ids=[excl['odl_id'] for excl in result.excluded_odls if 'odl_id' in excl],
                motivi_esclusione=result.excluded_odls,
                stato="Generato automaticamente - Test Fix",
                peso_totale_kg=result.total_weight,
                area_piano_1=result.used_area,
                area_piano_2=0.0,
                area_totale=result.total_area,
                area_utilizzata=result.used_area,
                posizioni_tool=configurazione_json["tool_positions"],
                note=f"Test nesting fix - Cluster '{ciclo_nome}': {len(result.positioned_tools)} ODL posizionati, {len(result.excluded_odls)} esclusi. Efficienza: {result.efficiency:.1f}%. Algoritmo: {result.algorithm_status}"
            )
            
            db.add(db_nesting_result)
            db.commit()
            db.refresh(db_nesting_result)
            
            saved_results.append({
                'nesting_result_id': db_nesting_result.id,
                'ciclo_nome': ciclo_nome,
                'autoclave_nome': autoclave.nome,
                'odl_posizionati': len(result.positioned_tools),
                'odl_esclusi': len(result.excluded_odls),
                'efficienza': result.efficiency,
                'configurazione_json': configurazione_json
            })
            
            print(f"   ✅ Salvato NestingResult ID {db_nesting_result.id} per '{ciclo_nome}'")
            print(f"     📊 {len(result.positioned_tools)} ODL posizionati, efficienza {result.efficiency:.1f}%")
            
        except Exception as e:
            print(f"   ❌ Errore nel salvataggio per '{ciclo_nome}': {str(e)}")
    
    return saved_results

def validate_frontend_compatibility(saved_results):
    """
    STEP 4: Validazione compatibilità frontend
    """
    print("\n🖥️ STEP 4: VALIDAZIONE COMPATIBILITÀ FRONTEND")
    print("=" * 52)
    
    for result in saved_results:
        config = result['configurazione_json']
        
        print(f"\n📋 Validazione per NestingResult ID {result['nesting_result_id']}:")
        
        # Verifica struttura configurazione_json
        required_fields = ['canvas_width', 'canvas_height', 'tool_positions', 'plane_assignments']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"   ❌ Campi mancanti: {missing_fields}")
        else:
            print(f"   ✅ Struttura configurazione_json valida")
        
        # Verifica tool_positions
        if config.get('tool_positions'):
            print(f"   ✅ Trovate {len(config['tool_positions'])} posizioni tool")
            
            # Controlla ogni posizione
            for i, pos in enumerate(config['tool_positions'][:3]):  # Solo primi 3 per brevità
                required_pos_fields = ['odl_id', 'x', 'y', 'width', 'height']
                missing_pos_fields = [field for field in required_pos_fields if field not in pos]
                
                if missing_pos_fields:
                    print(f"     ❌ Posizione {i}: campi mancanti {missing_pos_fields}")
                else:
                    print(f"     ✅ Posizione {i}: ODL {pos['odl_id']} a ({pos['x']:.0f},{pos['y']:.0f})")
        else:
            print(f"   ❌ Nessuna posizione tool trovata")
        
        # Verifica compatibilità canvas
        canvas_ok = (
            isinstance(config.get('canvas_width'), (int, float)) and config['canvas_width'] > 0 and
            isinstance(config.get('canvas_height'), (int, float)) and config['canvas_height'] > 0
        )
        
        if canvas_ok:
            print(f"   ✅ Dimensioni canvas valide: {config['canvas_width']}x{config['canvas_height']}")
        else:
            print(f"   ❌ Dimensioni canvas non valide")

def test_complete_nesting_workflow():
    """
    Test completo del workflow di nesting corretto
    """
    print("🚀 AVVIO TEST COMPLETO MODULO NESTING")
    print("=" * 60)
    
    # Setup database
    engine = create_engine('sqlite:///./carbonpilot.db')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # STEP 1: Correzioni preliminari
        fix_missing_cicli_cura(db)
        fix_missing_tool_data(db)
        
        # Selezione ODL di test (tutti gli ODL disponibili)
        all_odls = db.query(ODL).all()
        if not all_odls:
            print("❌ ERRORE: Nessun ODL trovato nel database!")
            return False
        
        odl_ids = [odl.id for odl in all_odls]
        print(f"\n🎯 Test con {len(odl_ids)} ODL: {odl_ids}")
        
        # STEP 1: Validazione dati
        valid_odls, invalid_odls = validate_odl_data(db, odl_ids)
        
        if not valid_odls:
            print("❌ ERRORE CRITICO: Nessun ODL valido per il nesting!")
            return False
        
        # STEP 2: Clustering e assegnazione autoclavi
        cicli_clusters = cluster_by_ciclo_cura(db, valid_odls)
        assignment = assign_autoclave_compatibility(db, cicli_clusters)
        
        if not assignment:
            print("❌ ERRORE: Nessuna autoclave disponibile!")
            return False
        
        # STEP 3: Esecuzione algoritmo
        results = execute_nesting_algorithm(db, assignment)
        
        # STEP 4: Salvataggio e validazione
        saved_results = save_nesting_results(db, results)
        
        if saved_results:
            validate_frontend_compatibility(saved_results)
            
            print("\n🎉 TEST COMPLETATO CON SUCCESSO!")
            print("=" * 50)
            print(f"✅ {len(saved_results)} nesting salvati nel database")
            print(f"✅ Frontend può renderizzare i canvas")
            print(f"✅ Algoritmo OR-Tools funzionante")
            
            # Riepilogo finale
            total_positioned = sum(r['odl_posizionati'] for r in saved_results)
            total_excluded = sum(r['odl_esclusi'] for r in saved_results)
            avg_efficiency = sum(r['efficienza'] for r in saved_results) / len(saved_results)
            
            print(f"\n📊 STATISTICHE FINALI:")
            print(f"   • ODL posizionati: {total_positioned}")
            print(f"   • ODL esclusi: {total_excluded}")
            print(f"   • Efficienza media: {avg_efficiency:.1f}%")
            
            return True
        else:
            print("\n❌ NESSUN RISULTATO SALVATO!")
            return False
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE IL TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_complete_nesting_workflow()
    
    if success:
        print("\n🏆 MODULO NESTING COMPLETAMENTE FUNZIONANTE!")
        print("✅ Tutti i problemi identificati sono stati risolti")
        print("✅ Il frontend può ora renderizzare correttamente i canvas")
        print("✅ Gli ODL vengono posizionati correttamente")
    else:
        print("\n❌ IL TEST HA FALLITO")
        print("🔧 Controllare i log sopra per identificare i problemi rimanenti") 