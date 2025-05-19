import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import status

from api.database import get_db, Base
from models.catalogo import Catalogo
from main import app

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_db.db"

# Test database setup
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sovrascrive la dipendenza del database
async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Fix per pytest
pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def setup_database():
    """
    Ricrea il database di test prima di ogni test
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def db_session():
    """
    Fornisce una sessione di database per i test
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
async def sample_catalogo(db_session):
    """
    Crea un elemento di catalogo di esempio nel database
    """
    catalogo = Catalogo(
        part_number="PN12345",
        descrizione="Pezzo di test",
        categoria="Test",
        attivo=True,
        note="Note di test"
    )
    db_session.add(catalogo)
    db_session.commit()
    db_session.refresh(catalogo)
    return catalogo

async def test_create_catalogo(client: AsyncClient):
    """Test creazione catalogo"""
    catalogo_data = {
        "part_number": "PN54321",
        "descrizione": "Nuovo pezzo di test",
        "categoria": "Test",
        "attivo": True,
        "note": "Note di test per nuovo pezzo"
    }
    
    response = await client.post("/api/catalogo/", json=catalogo_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["part_number"] == catalogo_data["part_number"]
    assert data["descrizione"] == catalogo_data["descrizione"]
    assert "created_at" in data

async def test_get_catalogo(client: AsyncClient, sample_catalogo):
    """Test recupero catalogo per part_number"""
    response = await client.get(f"/api/catalogo/{sample_catalogo.part_number}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["part_number"] == sample_catalogo.part_number
    assert data["descrizione"] == sample_catalogo.descrizione

async def test_get_catalogo_not_found(client: AsyncClient):
    """Test recupero catalogo non esistente"""
    response = await client.get("/api/catalogo/PN-NON-ESISTENTE")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_update_catalogo(client: AsyncClient, sample_catalogo):
    """Test aggiornamento catalogo"""
    update_data = {
        "descrizione": "Descrizione aggiornata",
        "attivo": False
    }
    
    response = await client.put(f"/api/catalogo/{sample_catalogo.part_number}", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["part_number"] == sample_catalogo.part_number
    assert data["descrizione"] == update_data["descrizione"]
    assert data["attivo"] == update_data["attivo"]

async def test_delete_catalogo(client: AsyncClient, sample_catalogo, db_session):
    """Test eliminazione catalogo"""
    response = await client.delete(f"/api/catalogo/{sample_catalogo.part_number}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verifica che sia stato effettivamente eliminato
    db_catalogo = db_session.query(Catalogo).filter(Catalogo.part_number == sample_catalogo.part_number).first()
    assert db_catalogo is None 