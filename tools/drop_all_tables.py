# tools/drop_all_tables.py
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/carbonpilot")

with engine.connect() as conn:
    print("⚠️ Eliminazione TUTTE le tabelle...")
    conn.execute(text("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """))
    conn.commit()
    print("✅ Tutte le tabelle eliminate.")
