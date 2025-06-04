#!/usr/bin/env python3
"""
CarbonPilot Schema Summary Tool
Analizza automaticamente tutti i modelli SQLAlchemy e gli schemi Pydantic del progetto.
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, get_type_hints
from datetime import datetime

# Aggiungi il percorso backend al PYTHONPATH
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from sqlalchemy.ext.declarative import DeclarativeMeta
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy import Column
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo
except ImportError as e:
    print(f"❌ Errore import: {e}")
    print("Assicurati di essere nell'ambiente virtuale corretto")
    sys.exit(1)

def is_sqlalchemy_model(obj) -> bool:
    """Verifica se un oggetto è un modello SQLAlchemy"""
    try:
        # Controlla se ha __tablename__ (caratteristica dei modelli SQLAlchemy)
        if not hasattr(obj, '__tablename__'):
            return False
        
        # Controlla se è una classe
        if not inspect.isclass(obj):
            return False
            
        # Controlla se ha attributi Column di SQLAlchemy
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):
                attr = getattr(obj, attr_name)
                if isinstance(attr, Column):
                    return True
                    
        # Controlla se ha il metaclass corretto
        if hasattr(obj, '__mro__'):
            for base in obj.__mro__:
                if hasattr(base, 'registry') or str(type(base)).find('DeclarativeMeta') != -1:
                    return True
                    
        return False
    except Exception:
        return False

def analyze_sqlalchemy_column(column: Column) -> Dict[str, Any]:
    """Analizza una colonna SQLAlchemy e restituisce le sue proprietà"""
    info = {
        'name': getattr(column, 'name', 'unknown'),
        'type': str(column.type),
        'nullable': getattr(column, 'nullable', True),
        'primary_key': getattr(column, 'primary_key', False),
        'foreign_keys': [],
        'default': None,
        'doc': getattr(column, 'doc', None)
    }
    
    # Analizza foreign keys
    if hasattr(column, 'foreign_keys') and column.foreign_keys:
        info['foreign_keys'] = [str(fk) for fk in column.foreign_keys]
    
    # Analizza default
    if hasattr(column, 'default') and column.default is not None:
        try:
            if hasattr(column.default, 'arg'):
                info['default'] = str(column.default.arg)
            else:
                info['default'] = str(column.default)
        except:
            info['default'] = 'complex_default'
    
    return info

def analyze_sqlalchemy_model(model_class) -> Dict[str, Any]:
    """Analizza un modello SQLAlchemy e restituisce le sue informazioni"""
    info = {
        'name': model_class.__name__,
        'table_name': getattr(model_class, '__tablename__', 'unknown'),
        'columns': {},
        'relationships': {},
        'doc': inspect.getdoc(model_class) or ''
    }
    
    # Analizza le colonne
    for attr_name in dir(model_class):
        if not attr_name.startswith('_'):
            attr = getattr(model_class, attr_name)
            if isinstance(attr, Column):
                info['columns'][attr_name] = analyze_sqlalchemy_column(attr)
    
    # Analizza le relazioni
    if hasattr(model_class, '__mapper__'):
        try:
            for rel_name, relationship in model_class.__mapper__.relationships.items():
                info['relationships'][rel_name] = {
                    'target': str(relationship.mapper.class_.__name__),
                    'back_populates': getattr(relationship, 'back_populates', None),
                    'foreign_keys': [str(fk) for fk in relationship.local_columns] if hasattr(relationship, 'local_columns') else []
                }
        except Exception as e:
            info['relationships']['_error'] = f"Errore analisi relazioni: {str(e)}"
    
    return info

def analyze_pydantic_model(model_class) -> Dict[str, Any]:
    """Analizza un modello Pydantic e restituisce le sue informazioni"""
    info = {
        'name': model_class.__name__,
        'fields': {},
        'doc': inspect.getdoc(model_class) or ''
    }
    
    # Analizza i campi usando model_fields (Pydantic v2)
    if hasattr(model_class, 'model_fields'):
        for field_name, field_info in model_class.model_fields.items():
            field_data = {
                'type': str(field_info.annotation) if hasattr(field_info, 'annotation') else 'unknown',
                'required': field_info.is_required() if hasattr(field_info, 'is_required') else True,
                'default': None,
                'description': None
            }
            
            # Gestisci default
            if hasattr(field_info, 'default') and field_info.default is not None:
                try:
                    field_data['default'] = str(field_info.default)
                except:
                    field_data['default'] = 'complex_default'
            
            # Gestisci descrizione
            if hasattr(field_info, 'description') and field_info.description:
                field_data['description'] = field_info.description
            
            info['fields'][field_name] = field_data
    
    return info

def scan_directory_for_models(directory: Path, is_sqlalchemy: bool = True) -> List[Dict[str, Any]]:
    """Scansiona una directory per trovare modelli SQLAlchemy o Pydantic"""
    models = []
    
    if not directory.exists():
        print(f"⚠️  Directory non trovata: {directory}")
        return models
    
    print(f"🔍 Scansionando {directory}...")
    
    for py_file in directory.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        try:
            # Costruisci il nome del modulo
            relative_path = py_file.relative_to(directory.parent)
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            print(f"   📄 Analizzando {module_name}")
            
            # Importa il modulo
            module = importlib.import_module(module_name)
            
            # Cerca classi nel modulo
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Salta classi importate da altri moduli
                if obj.__module__ != module.__name__:
                    continue
                
                if is_sqlalchemy and is_sqlalchemy_model(obj):
                    print(f"   ✅ Trovato modello SQLAlchemy: {name}")
                    models.append(analyze_sqlalchemy_model(obj))
                elif not is_sqlalchemy and issubclass(obj, BaseModel) and obj != BaseModel:
                    print(f"   ✅ Trovato schema Pydantic: {name}")
                    models.append(analyze_pydantic_model(obj))
                    
        except Exception as e:
            print(f"   ❌ Errore nell'analisi di {py_file.name}: {str(e)}")
            continue
    
    return models

def format_sqlalchemy_output(models: List[Dict[str, Any]]) -> str:
    """Formatta l'output per i modelli SQLAlchemy"""
    if not models:
        return "❌ Nessun modello SQLAlchemy trovato\n"
    
    output = f"📊 MODELLI SQLALCHEMY ({len(models)} trovati)\n"
    output += "=" * 50 + "\n\n"
    
    for model in models:
        output += f"🏗️  {model['name']} (tabella: {model['table_name']})\n"
        if model['doc']:
            output += f"   📝 {model['doc']}\n"
        
        # Colonne
        if model['columns']:
            output += f"   📋 Colonne ({len(model['columns'])}):\n"
            for col_name, col_info in model['columns'].items():
                flags = []
                if col_info['primary_key']:
                    flags.append("PK")
                if not col_info['nullable']:
                    flags.append("NOT NULL")
                if col_info['foreign_keys']:
                    flags.append("FK")
                if col_info['default']:
                    flags.append(f"default={col_info['default']}")
                
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                output += f"      • {col_name}: {col_info['type']}{flag_str}\n"
                
                if col_info['doc']:
                    output += f"        💬 {col_info['doc']}\n"
        
        # Relazioni
        if model['relationships']:
            output += f"   🔗 Relazioni ({len(model['relationships'])}):\n"
            for rel_name, rel_info in model['relationships'].items():
                if rel_name != '_error':
                    back_pop = f" (back_populates: {rel_info['back_populates']})" if rel_info['back_populates'] else ""
                    output += f"      • {rel_name} → {rel_info['target']}{back_pop}\n"
        
        output += "\n"
    
    return output

def format_pydantic_output(schemas: List[Dict[str, Any]]) -> str:
    """Formatta l'output per gli schemi Pydantic"""
    if not schemas:
        return "❌ Nessuno schema Pydantic trovato\n"
    
    output = f"📋 SCHEMI PYDANTIC ({len(schemas)} trovati)\n"
    output += "=" * 50 + "\n\n"
    
    for schema in schemas:
        output += f"📄 {schema['name']}\n"
        if schema['doc']:
            output += f"   📝 {schema['doc']}\n"
        
        if schema['fields']:
            output += f"   🏷️  Campi ({len(schema['fields'])}):\n"
            for field_name, field_info in schema['fields'].items():
                req_str = "obbligatorio" if field_info['required'] else "opzionale"
                default_str = f", default={field_info['default']}" if field_info['default'] else ""
                
                output += f"      • {field_name}: {field_info['type']} ({req_str}{default_str})\n"
                
                if field_info['description']:
                    output += f"        💬 {field_info['description']}\n"
        
        output += "\n"
    
    return output

def generate_summary() -> str:
    """Genera il riassunto completo di tutti i modelli e schemi"""
    print("🚀 Avvio analisi schema CarbonPilot...")
    
    # Percorsi
    backend_dir = Path(__file__).parent.parent / "backend"
    models_dir = backend_dir / "models"
    schemas_dir = backend_dir / "schemas"
    
    print(f"📁 Directory backend: {backend_dir}")
    print(f"📁 Directory modelli: {models_dir}")
    print(f"📁 Directory schemi: {schemas_dir}")
    
    # Analizza modelli SQLAlchemy
    print("\n" + "="*60)
    print("🔍 ANALISI MODELLI SQLALCHEMY")
    print("="*60)
    sqlalchemy_models = scan_directory_for_models(models_dir, is_sqlalchemy=True)
    
    # Analizza schemi Pydantic
    print("\n" + "="*60)
    print("🔍 ANALISI SCHEMI PYDANTIC")
    print("="*60)
    pydantic_schemas = scan_directory_for_models(schemas_dir, is_sqlalchemy=False)
    
    # Genera output
    output = f"# CarbonPilot - Schema Summary\n"
    output += f"Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Statistiche
    output += f"📊 STATISTICHE\n"
    output += f"=" * 20 + "\n"
    output += f"• Modelli SQLAlchemy: {len(sqlalchemy_models)}\n"
    output += f"• Schemi Pydantic: {len(pydantic_schemas)}\n"
    output += f"• Totale componenti: {len(sqlalchemy_models) + len(pydantic_schemas)}\n\n"
    
    # Dettagli
    output += format_sqlalchemy_output(sqlalchemy_models)
    output += format_pydantic_output(pydantic_schemas)
    
    return output

def main():
    """Funzione principale"""
    try:
        summary = generate_summary()
        
        print("\n" + "="*60)
        print("📋 RIASSUNTO FINALE")
        print("="*60)
        print(summary)
        
        # Salva su file
        output_file = Path(__file__).parent / "schema_summary.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"\n💾 Riassunto salvato in: {output_file}")
        
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 