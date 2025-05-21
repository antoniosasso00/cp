-- Script per aggiungere tabelle nesting al database
-- Da eseguire manualmente per risolvere errori di migrazione

-- 1. Tabella nesting_params
CREATE TABLE IF NOT EXISTS nesting_params (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    peso_valvole FLOAT NOT NULL DEFAULT 1.0,
    peso_area FLOAT NOT NULL DEFAULT 1.0,
    peso_priorita FLOAT NOT NULL DEFAULT 1.0,
    spazio_minimo_mm FLOAT NOT NULL DEFAULT 50.0,
    attivo BOOLEAN NOT NULL DEFAULT FALSE,
    descrizione TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_nesting_params_id ON nesting_params (id);

-- 2. Tabella nesting_results
CREATE TABLE IF NOT EXISTS nesting_results (
    id SERIAL PRIMARY KEY,
    codice VARCHAR(50) NOT NULL UNIQUE,
    autoclave_id INTEGER NOT NULL REFERENCES autoclavi (id),
    confermato BOOLEAN NOT NULL DEFAULT FALSE,
    data_conferma TIMESTAMP WITH TIME ZONE,
    area_totale_mm2 FLOAT NOT NULL,
    area_utilizzata_mm2 FLOAT NOT NULL,
    efficienza_area FLOAT NOT NULL,
    valvole_totali INTEGER NOT NULL,
    valvole_utilizzate INTEGER NOT NULL,
    layout JSONB NOT NULL,
    odl_ids JSONB NOT NULL,
    generato_manualmente BOOLEAN NOT NULL DEFAULT FALSE,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT fk_autoclave FOREIGN KEY (autoclave_id) REFERENCES autoclavi (id)
);

CREATE INDEX IF NOT EXISTS ix_nesting_results_id ON nesting_results (id);

-- 3. Inserisci un set di parametri default
INSERT INTO nesting_params (nome, peso_valvole, peso_area, peso_priorita, spazio_minimo_mm, attivo, descrizione)
VALUES ('Configurazione Default', 2.0, 3.0, 5.0, 30.0, TRUE, 'Configurazione predefinita del sistema')
ON CONFLICT (nome) DO NOTHING; 