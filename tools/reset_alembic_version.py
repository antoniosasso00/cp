from sqlalchemy import create_engine, text

# Aggiorna la stringa se usi credenziali diverse
engine = create_engine("postgresql://postgres:postgres@localhost:5432/carbonpilot")

with engine.connect() as conn:
    print("🔄 Eliminazione versione Alembic corrente...")
    conn.execute(text("DELETE FROM alembic_version;"))
    conn.commit()
    print("✅ Tabella 'alembic_version' ripulita.")
