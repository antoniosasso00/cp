#!/usr/bin/env python3
"""
🧠 Script per stampare un riassunto completo dello schema del database
Scansiona tutti i modelli SQLAlchemy e mostra:
- Nome del modello e tabella
- Campi con tipo, nullabilità e vincoli
- Foreign Keys e relazioni
- Enum e valori possibili

Uso: python tools/print_schema_summary.py
"""

import sys
import os
import inspect
from typing import Dict, List, Any
from sqlalchemy import Column, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

# Aggiungi il path del backend per importare i modelli
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

print(f"🔍 Tentativo di importazione modelli da: {backend_path}")

try:
    # Importa tutti i modelli uno per uno per debug migliore
    from models.base import Base
    print("✅ Importato Base")
    
    from models.catalogo import Catalogo
    from models.parte import Parte
    from models.tool import Tool
    from models.autoclave import Autoclave, StatoAutoclaveEnum
    from models.ciclo_cura import CicloCura
    from models.odl import ODL
    from models.odl_log import ODLLog
    from models.state_log import StateLog
    from models.tempo_fase import TempoFase
    from models.nesting_result import NestingResult
    from models.schedule_entry import ScheduleEntry, ScheduleEntryStatus, ScheduleEntryType
    from models.tempo_produzione import TempoProduzione
    from models.report import Report, ReportTypeEnum
    from models.system_log import SystemLog, LogLevel, EventType, UserRole
    
    print("✅ Tutti i modelli importati con successo")
    
except ImportError as e:
    print(f"❌ Errore nell'importazione dei modelli: {e}")
    print(f"Path backend: {backend_path}")
    print(f"Directory corrente: {os.getcwd()}")
    print("Assicurati di essere nella directory root del progetto")
    sys.exit(1)

def get_column_type_info(column: Column) -> str:
    """Estrae informazioni dettagliate sul tipo di una colonna"""
    col_type = column.type
    type_info = []
    
    # Tipo base
    if isinstance(col_type, String):
        if hasattr(col_type, 'length') and col_type.length:
            type_info.append(f"String({col_type.length})")
        else:
            type_info.append("String")
    elif isinstance(col_type, Integer):
        type_info.append("Integer")
    elif isinstance(col_type, Float):
        type_info.append("Float")
    elif isinstance(col_type, Boolean):
        type_info.append("Boolean")
    elif isinstance(col_type, DateTime):
        type_info.append("DateTime")
    elif isinstance(col_type, Text):
        type_info.append("Text")
    elif isinstance(col_type, (Enum, PgEnum)):
        # Per gli enum, mostra anche i valori possibili
        if hasattr(col_type, 'enum_class'):
            enum_values = [e.value for e in col_type.enum_class]
            type_info.append(f"Enum({', '.join(enum_values)})")
        elif hasattr(col_type, 'enums'):
            # Per enum SQLAlchemy standard
            type_info.append(f"Enum({', '.join(col_type.enums)})")
        else:
            type_info.append("Enum")
    else:
        type_info.append(str(col_type))
    
    # Vincoli aggiuntivi
    if column.primary_key:
        type_info.append("PK")
    if column.unique:
        type_info.append("UNIQUE")
    if column.index:
        type_info.append("INDEX")
    if not column.nullable:
        type_info.append("NOT NULL")
    if column.default is not None:
        if hasattr(column.default, 'arg'):
            type_info.append(f"DEFAULT={column.default.arg}")
        else:
            type_info.append("DEFAULT")
    
    return " | ".join(type_info)

def get_foreign_keys(column: Column) -> List[str]:
    """Estrae informazioni sui foreign keys di una colonna"""
    fks = []
    for fk in column.foreign_keys:
        fks.append(f"FK -> {fk.column}")
    return fks

def get_model_relationships(model_class) -> Dict[str, str]:
    """Estrae le relazioni del modello"""
    relationships = {}
    
    # Cerca gli attributi di tipo relationship
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
            # È una relationship
            related_model = attr.property.mapper.class_.__name__
            
            # Determina il tipo di relazione
            if hasattr(attr.property, 'back_populates'):
                rel_type = "bidirectional"
            elif hasattr(attr.property, 'backref'):
                rel_type = "backref"
            else:
                rel_type = "one-way"
            
            # Determina la cardinalità
            if hasattr(attr.property, 'uselist') and not attr.property.uselist:
                cardinality = "one-to-one"
            else:
                cardinality = "one-to-many"
            
            relationships[attr_name] = f"{cardinality} -> {related_model} ({rel_type})"
    
    return relationships

def print_model_summary(model_class) -> None:
    """Stampa il riassunto di un singolo modello"""
    print(f"\n📄 Modello: {model_class.__name__}")
    print(f"   Tabella: {model_class.__tablename__}")
    
    # Ottieni tutte le colonne
    columns = []
    if hasattr(model_class, '__table__'):
        for column in model_class.__table__.columns:
            columns.append(column)
    
    # Ordina le colonne: prima PK, poi FK, poi il resto
    def column_sort_key(col):
        if col.primary_key:
            return (0, col.name)
        elif col.foreign_keys:
            return (1, col.name)
        else:
            return (2, col.name)
    
    columns.sort(key=column_sort_key)
    
    # Stampa le colonne
    print("   📋 Campi:")
    for column in columns:
        type_info = get_column_type_info(column)
        fks = get_foreign_keys(column)
        
        line = f"      • {column.name}: {type_info}"
        if fks:
            line += f" | {' | '.join(fks)}"
        
        # Aggiungi documentazione se presente
        if hasattr(column, 'doc') and column.doc:
            line += f"\n        📝 {column.doc}"
        
        print(line)
    
    # Stampa le relazioni
    relationships = get_model_relationships(model_class)
    if relationships:
        print("   🔗 Relazioni:")
        for rel_name, rel_info in sorted(relationships.items()):
            print(f"      • {rel_name}: {rel_info}")

def main():
    """Funzione principale che scansiona tutti i modelli e stampa il riassunto"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stampa riassunto schema database CarbonPilot")
    parser.add_argument("--output", "-o", help="Salva output in file invece di stampare")
    parser.add_argument("--compact", "-c", action="store_true", help="Output compatto senza emoji")
    args = parser.parse_args()
    
    # Redirect output se richiesto
    original_stdout = sys.stdout
    if args.output:
        sys.stdout = open(args.output, 'w', encoding='utf-8')
    
    try:
        if args.compact:
            print("RIASSUNTO SCHEMA DATABASE - CarbonPilot")
            print("=" * 60)
        else:
            print("🧠 RIASSUNTO SCHEMA DATABASE - CarbonPilot")
            print("=" * 60)
        
        # Trova tutti i modelli che ereditano da Base
        models = []
        
        # Cerca nei moduli importati
        current_module = sys.modules[__name__]
        for name in dir(current_module):
            obj = getattr(current_module, name)
            if (inspect.isclass(obj) and 
                hasattr(obj, '__tablename__') and 
                issubclass(obj, Base) and 
                obj != Base):
                models.append(obj)
        
        # Ordina i modelli alfabeticamente
        models.sort(key=lambda x: x.__name__)
        
        if args.compact:
            print(f"\nTrovati {len(models)} modelli:")
        else:
            print(f"\n🔍 Trovati {len(models)} modelli:")
        for model in models:
            print(f"   • {model.__name__}")
        
        print("\n" + "=" * 60)
        
        # Stampa il dettaglio di ogni modello
        for model in models:
            print_model_summary(model)
        
        print("\n" + "=" * 60)
        if args.compact:
            print("Riassunto completato!")
            print(f"Totale modelli analizzati: {len(models)}")
        else:
            print("✅ Riassunto completato!")
            print(f"📊 Totale modelli analizzati: {len(models)}")
    
    finally:
        # Ripristina stdout se era stato reindirizzato
        if args.output:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"✅ Riassunto salvato in: {args.output}")

if __name__ == "__main__":
    main() 