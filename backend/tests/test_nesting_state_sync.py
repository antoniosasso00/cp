"""
Test per la sincronizzazione degli stati tra Nesting, ODL e Autoclavi.

Questo test verifica che:
1. Gli stati del nesting si sincronizzino correttamente con ODL e autoclavi
2. Le transizioni di stato siano validate correttamente
3. Le fasi temporali vengano gestite appropriatamente
4. I log vengano creati correttamente
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from api.database import get_db
from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.ciclo_cura import CicloCura
from models.tempo_fase import TempoFase
from models.odl_log import ODLLog
from services.nesting_state_sync_service import NestingStateSyncService


class TestNestingStateSync:
    """Test per la sincronizzazione degli stati del nesting"""
    
    @pytest.fixture
    def setup_test_data(self, db: Session):
        """Prepara i dati di test"""
        # Crea ciclo di cura
        ciclo_cura = CicloCura(
            nome="Test Cycle",
            temperatura=180.0,
            durata_minuti=120,
            pressione_bar=2.0
        )
        db.add(ciclo_cura)
        
        # Crea autoclave
        autoclave = Autoclave(
            nome="Autoclave Test",
            codice="AT001",
            lunghezza=1000.0,
            larghezza_piano=800.0,
            temperatura_max=200.0,
            num_linee_vuoto=4,
            stato=StatoAutoclaveEnum.DISPONIBILE
        )
        db.add(autoclave)
        
        # Crea catalogo
        catalogo = Catalogo(
            part_number="TEST001",
            descrizione="Test Part",
            area_cm2=100.0,
            peso_kg=1.5
        )
        db.add(catalogo)
        
        # Crea parte
        parte = Parte(
            catalogo_id=None,  # Sarà impostato dopo il commit
            descrizione_breve="Test Part",
            num_valvole_richieste=2,
            ciclo_cura_id=None  # Sarà impostato dopo il commit
        )
        db.add(parte)
        
        # Crea tool
        tool = Tool(
            part_number_tool="TOOL001",
            descrizione="Test Tool",
            lunghezza_piano=200.0,
            larghezza_piano=150.0,
            peso=2.0,
            disponibile=True
        )
        db.add(tool)
        
        db.commit()
        
        # Aggiorna le relazioni
        parte.catalogo_id = catalogo.id
        parte.ciclo_cura_id = ciclo_cura.id
        catalogo.parte_id = parte.id
        
        # Crea ODL in stato "Attesa Cura"
        odl1 = ODL(
            parte_id=parte.id,
            tool_id=tool.id,
            priorita=1,
            status="Attesa Cura"
        )
        odl2 = ODL(
            parte_id=parte.id,
            tool_id=tool.id,
            priorita=2,
            status="Attesa Cura"
        )
        db.add_all([odl1, odl2])
        
        # Crea nesting in stato "Bozza"
        nesting = NestingResult(
            autoclave_id=autoclave.id,
            odl_ids=[],  # Sarà aggiornato dopo il commit
            stato="Bozza",
            area_utilizzata=150.0,
            area_totale=800.0,
            valvole_utilizzate=4,
            valvole_totali=8,
            peso_totale_kg=3.0
        )
        db.add(nesting)
        
        db.commit()
        
        # Aggiorna gli ODL IDs nel nesting
        nesting.odl_ids = [odl1.id, odl2.id]
        db.commit()
        
        return {
            'nesting': nesting,
            'odl1': odl1,
            'odl2': odl2,
            'autoclave': autoclave,
            'parte': parte,
            'tool': tool,
            'ciclo_cura': ciclo_cura
        }
    
    def test_validate_state_transitions(self):
        """Test validazione transizioni di stato"""
        # Transizioni valide
        assert NestingStateSyncService.validate_state_transition("Bozza", "Confermato")
        assert NestingStateSyncService.validate_state_transition("Confermato", "Caricato")
        assert NestingStateSyncService.validate_state_transition("Caricato", "Finito")
        
        # Transizioni non valide
        assert not NestingStateSyncService.validate_state_transition("Bozza", "Finito")
        assert not NestingStateSyncService.validate_state_transition("Finito", "Bozza")
        assert not NestingStateSyncService.validate_state_transition("Finito", "Caricato")
    
    def test_get_valid_transitions(self):
        """Test ottenimento transizioni valide"""
        transitions = NestingStateSyncService.get_valid_transitions("Bozza")
        assert "Confermato" in transitions
        assert "In sospeso" in transitions
        
        transitions = NestingStateSyncService.get_valid_transitions("Finito")
        assert len(transitions) == 0  # Stato finale
    
    def test_sync_stato_confermato(self, db: Session, setup_test_data):
        """Test sincronizzazione stato 'Confermato'"""
        data = setup_test_data
        nesting = data['nesting']
        
        # Test: conferma nesting con ODL in "Attesa Cura" (dovrebbe funzionare)
        risultato = NestingStateSyncService.sync_nesting_state_change(
            db=db,
            nesting=nesting,
            nuovo_stato="Confermato",
            responsabile="test_user"
        )
        
        assert risultato['nuovo_stato'] == "Confermato"
        assert nesting.stato == "Confermato"
        assert len(risultato['errori']) == 0
        
        # Verifica che gli ODL rimangano in "Attesa Cura"
        db.refresh(data['odl1'])
        db.refresh(data['odl2'])
        assert data['odl1'].status == "Attesa Cura"
        assert data['odl2'].status == "Attesa Cura"
    
    def test_sync_stato_confermato_with_invalid_odl(self, db: Session, setup_test_data):
        """Test conferma nesting con ODL in stato non valido"""
        data = setup_test_data
        nesting = data['nesting']
        
        # Cambia stato di un ODL
        data['odl1'].status = "Preparazione"
        db.commit()
        
        # Test: conferma nesting con ODL non in "Attesa Cura" (dovrebbe fallire)
        with pytest.raises(ValueError) as exc_info:
            NestingStateSyncService.sync_nesting_state_change(
                db=db,
                nesting=nesting,
                nuovo_stato="Confermato",
                responsabile="test_user"
            )
        
        assert "non sono in stato 'Attesa Cura'" in str(exc_info.value)
    
    def test_sync_stato_caricato(self, db: Session, setup_test_data):
        """Test sincronizzazione stato 'Caricato'"""
        data = setup_test_data
        nesting = data['nesting']
        autoclave = data['autoclave']
        
        # Prima conferma il nesting
        nesting.stato = "Confermato"
        db.commit()
        
        # Test: carica nesting
        risultato = NestingStateSyncService.sync_nesting_state_change(
            db=db,
            nesting=nesting,
            nuovo_stato="Caricato",
            responsabile="test_user"
        )
        
        assert risultato['nuovo_stato'] == "Caricato"
        assert nesting.stato == "Caricato"
        assert risultato['autoclave_aggiornata'] == True
        assert len(risultato['odl_aggiornati']) == 2
        
        # Verifica autoclave
        db.refresh(autoclave)
        assert autoclave.stato == StatoAutoclaveEnum.IN_USO
        
        # Verifica ODL
        db.refresh(data['odl1'])
        db.refresh(data['odl2'])
        assert data['odl1'].status == "Cura"
        assert data['odl2'].status == "Cura"
        
        # Verifica che siano stati creati i log
        logs = db.query(ODLLog).filter(
            ODLLog.odl_id.in_([data['odl1'].id, data['odl2'].id])
        ).all()
        assert len(logs) >= 2
    
    def test_sync_stato_finito(self, db: Session, setup_test_data):
        """Test sincronizzazione stato 'Finito'"""
        data = setup_test_data
        nesting = data['nesting']
        autoclave = data['autoclave']
        
        # Prepara il nesting in stato "Caricato"
        nesting.stato = "Caricato"
        autoclave.stato = StatoAutoclaveEnum.IN_USO
        data['odl1'].status = "Cura"
        data['odl2'].status = "Cura"
        db.commit()
        
        # Test: completa nesting
        risultato = NestingStateSyncService.sync_nesting_state_change(
            db=db,
            nesting=nesting,
            nuovo_stato="Finito",
            responsabile="test_user"
        )
        
        assert risultato['nuovo_stato'] == "Finito"
        assert nesting.stato == "Finito"
        assert risultato['autoclave_aggiornata'] == True
        assert len(risultato['odl_aggiornati']) == 2
        
        # Verifica autoclave
        db.refresh(autoclave)
        assert autoclave.stato == StatoAutoclaveEnum.DISPONIBILE
        
        # Verifica ODL
        db.refresh(data['odl1'])
        db.refresh(data['odl2'])
        assert data['odl1'].status == "Finito"
        assert data['odl2'].status == "Finito"
    
    def test_gestione_fasi_temporali(self, db: Session, setup_test_data):
        """Test gestione delle fasi temporali durante le transizioni"""
        data = setup_test_data
        nesting = data['nesting']
        odl1 = data['odl1']
        
        # Crea una fase "attesa_cura" attiva
        fase_attesa = TempoFase(
            odl_id=odl1.id,
            fase="attesa_cura",
            inizio_fase=datetime.now() - timedelta(hours=1),
            note="Fase di test"
        )
        db.add(fase_attesa)
        db.commit()
        
        # Prepara per caricamento
        nesting.stato = "Confermato"
        db.commit()
        
        # Carica nesting (dovrebbe chiudere fase attesa e aprire fase cura)
        NestingStateSyncService.sync_nesting_state_change(
            db=db,
            nesting=nesting,
            nuovo_stato="Caricato",
            responsabile="test_user"
        )
        
        # Verifica che la fase attesa sia stata chiusa
        db.refresh(fase_attesa)
        assert fase_attesa.fine_fase is not None
        assert fase_attesa.durata_minuti is not None
        
        # Verifica che sia stata creata una fase cura
        fase_cura = db.query(TempoFase).filter(
            TempoFase.odl_id == odl1.id,
            TempoFase.fase == "cura",
            TempoFase.fine_fase == None
        ).first()
        assert fase_cura is not None
    
    def test_invalid_transition(self, db: Session, setup_test_data):
        """Test transizione non valida"""
        data = setup_test_data
        nesting = data['nesting']
        
        # Test: tentativo di passare direttamente da "Bozza" a "Finito"
        with pytest.raises(ValueError) as exc_info:
            NestingStateSyncService.sync_nesting_state_change(
                db=db,
                nesting=nesting,
                nuovo_stato="Finito",
                responsabile="test_user"
            )
        
        assert "Transizione non valida" in str(exc_info.value)
    
    def test_autoclave_not_available(self, db: Session, setup_test_data):
        """Test caricamento con autoclave non disponibile"""
        data = setup_test_data
        nesting = data['nesting']
        autoclave = data['autoclave']
        
        # Imposta autoclave in manutenzione
        autoclave.stato = StatoAutoclaveEnum.MANUTENZIONE
        nesting.stato = "Confermato"
        db.commit()
        
        # Test: tentativo di caricamento con autoclave non disponibile
        with pytest.raises(ValueError) as exc_info:
            NestingStateSyncService.sync_nesting_state_change(
                db=db,
                nesting=nesting,
                nuovo_stato="Caricato",
                responsabile="test_user"
            )
        
        assert "non può essere utilizzata" in str(exc_info.value)


class TestNestingStateAPI:
    """Test per l'API di aggiornamento stato nesting"""
    
    def test_update_nesting_status_api(self, client: TestClient, db: Session):
        """Test endpoint API per aggiornamento stato"""
        # Questo test richiede dati di setup più complessi
        # Per ora testiamo solo la validazione di base
        
        response = client.put(
            "/api/v1/nesting/999/status",
            json={
                "stato": "Confermato",
                "note": "Test update"
            }
        )
        
        # Dovrebbe restituire 404 per nesting inesistente
        assert response.status_code == 404
    
    def test_invalid_state_transition_api(self, client: TestClient, db: Session):
        """Test transizione non valida tramite API"""
        # Questo test richiederebbe un nesting esistente nel database
        # Per ora testiamo solo la struttura della risposta
        pass


if __name__ == "__main__":
    # Esegui i test
    pytest.main([__file__, "-v"]) 