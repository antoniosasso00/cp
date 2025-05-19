# tools/describe_models.py

import os
import sys
import inspect as pyinspect
from sqlalchemy import inspect as sa_inspect
import importlib
from pathlib import Path
from sqlalchemy.orm import DeclarativeMeta, RelationshipProperty
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, Boolean, Float, DateTime, Text

# Imposta il path del progetto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

MODELS_PATH = ROOT_DIR / "backend" / "models"
MODULE_PREFIX = "backend.models"

print("\n📘 MODEL STRUCTURE ANALYSIS:\n")

for file in MODELS_PATH.glob("*.py"):
    if file.name in {"__init__.py", "base.py"}:
        continue

    module_name = f"{MODULE_PREFIX}.{file.stem}"
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        print(f"❌ Errore import {module_name}: {e}")
        continue

    for name, obj in pyinspect.getmembers(module):
        if pyinspect.isclass(obj) and hasattr(obj, "__table__"):
            print(f"📦 {name} (tabella: {obj.__tablename__})")

            for col in obj.__table__.columns:
                col_desc = f" ├─ {col.name}: {col.type}"
                flags = []
                if col.primary_key:
                    flags.append("PK")
                if col.foreign_keys:
                    fk = list(col.foreign_keys)[0]
                    flags.append(f"FK → {fk.column.table.name}.{fk.column.name}")
                if not col.nullable:
                    flags.append("NOT NULL")
                if col.index:
                    flags.append("INDEX")
                if col.unique:
                    flags.append("UNIQUE")
                if col.default:
                    flags.append("default")
                if flags:
                    col_desc += " [" + ", ".join(flags) + "]"
                print(col_desc)

            mapper = sa_inspect(obj)
            for rel in mapper.relationships:
                rel_line = f" └─ relationship: {rel.key} → {rel.mapper.class_.__name__}"
                if rel.back_populates:
                    rel_line += f" (back_populates='{rel.back_populates}')"
                print(rel_line)

            print("")