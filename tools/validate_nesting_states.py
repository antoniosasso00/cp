#!/usr/bin/env python3
"""
Script di validazione per verificare la coerenza degli stati del nesting

Questo script verifica:
1. Coerenza tra stati nesting e stati ODL
2. Coerenza tra stati nesting e stati autoclavi
3. Integrità dei dati (parametri, relazioni)
4. Possibili inconsistenze da correggere

Uso:
    python tools/validate_nesting_states.py [--fix] [--verbose]
    
    --fix: Corregge automaticamente le inconsistenze trovate
    --verbose: Output dettagliato
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from models.db import get_database_url
import logging
from typing import Dict, List, Tuple
import argparse

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NestingStateValidator:
    """Validatore per la coerenza degli stati del nesting"""
    
    def __init__(self, db: Session, verbose: bool = False, fix_issues: bool = False):
        self.db = db
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.issues = []
        self.fixes_applied = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log con controllo verbosità"""
        if self.verbose or level in ["WARNING", "ERROR"]:
            getattr(logger, level.lower())(message)
    
    def add_issue(self, issue_type: str, description: str, severity: str = "WARNING"):
        """Aggiunge un'issue alla lista"""
        issue = {
            "type": issue_type,
            "description": description,
            "severity": severity
        }
        self.issues.append(issue)
        self.log(f"🔍 {severity}: {description}", severity)
    
    def add_fix(self, fix_description: str):
        """Registra una correzione applicata"""
        self.fixes_applied.append(fix_description)
        self.log(f"🔧 FIX: {fix_description}", "INFO")
    
    def validate_nesting_states(self) -> bool:
        """
        Valida la coerenza degli stati del nesting
        
        Returns:
            True se tutti i controlli passano, False altrimenti
        """
        self.log("🔍 Validazione stati nesting...")
        
        try:
            # Usa query SQL diretta per evitare problemi con relazioni
            result = self.db.execute(text("SELECT id, stato, padding_mm, borda_mm, rotazione_abilitata FROM nesting_results"))
            nesting_results = result.fetchall()
            
            if not nesting_results:
                self.log("ℹ️ Nessun nesting trovato nel database")
                return True
            
            self.log(f"📊 Trovati {len(nesting_results)} nesting da validare")
            
            all_valid = True
            
            for row in nesting_results:
                nesting_id = row.id
                stato = row.stato
                padding_mm = row.padding_mm
                borda_mm = row.borda_mm
                rotazione_abilitata = row.rotazione_abilitata
                
                # Valida stato
                valid_states = ["bozza", "in_sospeso", "confermato", "annullato", "completato"]
                if stato not in valid_states:
                    self.add_issue(
                        "INVALID_STATE",
                        f"Nesting #{nesting_id}: stato '{stato}' non è valido",
                        "ERROR"
                    )
                    all_valid = False
                    
                    if self.fix_issues:
                        # Prova a mappare al nuovo formato
                        state_mapping = {
                            "In sospeso": "in_sospeso",
                            "Confermato": "confermato",
                            "Completato": "completato",
                            "Annullato": "annullato",
                            "Bozza": "bozza"
                        }
                        
                        new_state = state_mapping.get(str(stato), "in_sospeso")
                        self.db.execute(text("UPDATE nesting_results SET stato = :new_state WHERE id = :id"), 
                                      {"new_state": new_state, "id": nesting_id})
                        self.add_fix(f"Nesting #{nesting_id}: stato aggiornato a {new_state}")
                
                # Valida parametri personalizzabili
                if padding_mm is None or padding_mm < 0:
                    self.add_issue(
                        "INVALID_PADDING",
                        f"Nesting #{nesting_id}: padding_mm non valido ({padding_mm})",
                        "WARNING"
                    )
                    if self.fix_issues:
                        self.db.execute(text("UPDATE nesting_results SET padding_mm = 10.0 WHERE id = :id"), 
                                      {"id": nesting_id})
                        self.add_fix(f"Nesting #{nesting_id}: padding_mm impostato a 10.0")
                
                if borda_mm is None or borda_mm < 0:
                    self.add_issue(
                        "INVALID_BORDA",
                        f"Nesting #{nesting_id}: borda_mm non valido ({borda_mm})",
                        "WARNING"
                    )
                    if self.fix_issues:
                        self.db.execute(text("UPDATE nesting_results SET borda_mm = 20.0 WHERE id = :id"), 
                                      {"id": nesting_id})
                        self.add_fix(f"Nesting #{nesting_id}: borda_mm impostato a 20.0")
                
                if rotazione_abilitata is None:
                    self.add_issue(
                        "INVALID_ROTATION",
                        f"Nesting #{nesting_id}: rotazione_abilitata non impostato",
                        "WARNING"
                    )
                    if self.fix_issues:
                        self.db.execute(text("UPDATE nesting_results SET rotazione_abilitata = 1 WHERE id = :id"), 
                                      {"id": nesting_id})
                        self.add_fix(f"Nesting #{nesting_id}: rotazione_abilitata impostato a True")
            
            return all_valid
            
        except Exception as e:
            self.log(f"❌ Errore nella validazione stati: {e}", "ERROR")
            return False
    
    def validate_odl_nesting_consistency(self) -> bool:
        """
        Valida la coerenza tra stati nesting e stati ODL
        
        Returns:
            True se coerente, False altrimenti
        """
        self.log("🔍 Validazione coerenza ODL-Nesting...")
        
        try:
            # Query per nesting attivi
            result = self.db.execute(text("""
                SELECT id, stato, odl_ids, autoclave_id 
                FROM nesting_results 
                WHERE stato IN ('in_sospeso', 'confermato')
            """))
            active_nestings = result.fetchall()
            
            all_valid = True
            
            for row in active_nestings:
                nesting_id = row.id
                stato = row.stato
                odl_ids = row.odl_ids
                
                if odl_ids:
                    # Verifica che gli ODL esistano
                    for odl_id in odl_ids:
                        odl_result = self.db.execute(text("SELECT id, status FROM odl WHERE id = :id"), {"id": odl_id})
                        odl_row = odl_result.fetchone()
                        
                        if not odl_row:
                            self.add_issue(
                                "MISSING_ODL",
                                f"Nesting #{nesting_id}: ODL #{odl_id} non trovato",
                                "ERROR"
                            )
                            all_valid = False
                            continue
                        
                        # Verifica coerenza stato
                        odl_status = odl_row.status
                        if stato == "in_sospeso" and odl_status != "Attesa Cura":
                            self.add_issue(
                                "ODL_STATE_MISMATCH",
                                f"Nesting #{nesting_id} IN_SOSPESO ma ODL #{odl_id} in stato '{odl_status}'",
                                "WARNING"
                            )
                            if self.fix_issues:
                                self.db.execute(text("UPDATE odl SET status = 'Attesa Cura' WHERE id = :id"), 
                                              {"id": odl_id})
                                self.add_fix(f"ODL #{odl_id}: stato ripristinato a 'Attesa Cura'")
                        
                        elif stato == "confermato" and odl_status != "Cura":
                            self.add_issue(
                                "ODL_STATE_MISMATCH",
                                f"Nesting #{nesting_id} CONFERMATO ma ODL #{odl_id} in stato '{odl_status}'",
                                "WARNING"
                            )
                            if self.fix_issues:
                                self.db.execute(text("UPDATE odl SET status = 'Cura' WHERE id = :id"), 
                                              {"id": odl_id})
                                self.add_fix(f"ODL #{odl_id}: stato aggiornato a 'Cura'")
            
            return all_valid
            
        except Exception as e:
            self.log(f"❌ Errore nella validazione ODL: {e}", "ERROR")
            return False
    
    def validate_autoclave_availability(self) -> bool:
        """
        Valida la coerenza tra stati nesting e disponibilità autoclavi
        
        Returns:
            True se coerente, False altrimenti
        """
        self.log("🔍 Validazione disponibilità autoclavi...")
        
        try:
            # Query per nesting attivi e relative autoclavi
            result = self.db.execute(text("""
                SELECT nr.id as nesting_id, nr.stato, nr.autoclave_id, a.nome, a.stato as autoclave_stato
                FROM nesting_results nr
                LEFT JOIN autoclavi a ON nr.autoclave_id = a.id
                WHERE nr.stato IN ('in_sospeso', 'confermato')
            """))
            active_nestings = result.fetchall()
            
            all_valid = True
            
            for row in active_nestings:
                nesting_id = row.nesting_id
                autoclave_id = row.autoclave_id
                autoclave_nome = row.nome
                autoclave_stato = row.autoclave_stato
                
                if not autoclave_nome:
                    self.add_issue(
                        "MISSING_AUTOCLAVE",
                        f"Nesting #{nesting_id}: Autoclave #{autoclave_id} non trovata",
                        "ERROR"
                    )
                    all_valid = False
                    continue
                
                # Verifica stato autoclave
                if autoclave_stato != "IN_USO":
                    self.add_issue(
                        "AUTOCLAVE_STATE_MISMATCH",
                        f"Nesting #{nesting_id} attivo ma autoclave {autoclave_nome} in stato '{autoclave_stato}'",
                        "WARNING"
                    )
                    if self.fix_issues:
                        self.db.execute(text("UPDATE autoclavi SET stato = 'IN_USO' WHERE id = :id"), 
                                      {"id": autoclave_id})
                        self.add_fix(f"Autoclave {autoclave_nome}: stato aggiornato a 'IN_USO'")
            
            # Verifica autoclavi libere con nesting attivi
            result = self.db.execute(text("""
                SELECT a.id, a.nome, COUNT(nr.id) as active_nestings
                FROM autoclavi a
                LEFT JOIN nesting_results nr ON a.id = nr.autoclave_id 
                    AND nr.stato IN ('in_sospeso', 'confermato')
                WHERE a.stato = 'DISPONIBILE'
                GROUP BY a.id, a.nome
                HAVING COUNT(nr.id) > 0
            """))
            
            for row in result:
                autoclave_id = row.id
                autoclave_nome = row.nome
                active_count = row.active_nestings
                
                self.add_issue(
                    "AUTOCLAVE_FREE_WITH_ACTIVE_NESTING",
                    f"Autoclave {autoclave_nome} DISPONIBILE ma ha {active_count} nesting attivi",
                    "WARNING"
                )
                if self.fix_issues:
                    self.db.execute(text("UPDATE autoclavi SET stato = 'IN_USO' WHERE id = :id"), 
                                  {"id": autoclave_id})
                    self.add_fix(f"Autoclave {autoclave_nome}: stato corretto a 'IN_USO'")
            
            return all_valid
            
        except Exception as e:
            self.log(f"❌ Errore nella validazione autoclavi: {e}", "ERROR")
            return False
    
    def validate_data_integrity(self) -> bool:
        """
        Valida l'integrità generale dei dati
        
        Returns:
            True se integri, False altrimenti
        """
        self.log("🔍 Validazione integrità dati...")
        
        try:
            all_valid = True
            
            # Verifica nesting senza ODL
            result = self.db.execute(text("""
                SELECT id, stato 
                FROM nesting_results 
                WHERE odl_ids IS NULL OR odl_ids = '[]'
            """))
            
            for row in result:
                nesting_id = row.id
                stato = row.stato
                
                self.add_issue(
                    "EMPTY_NESTING",
                    f"Nesting #{nesting_id}: nessun ODL associato",
                    "WARNING"
                )
                if self.fix_issues and stato != "annullato":
                    self.db.execute(text("UPDATE nesting_results SET stato = 'annullato' WHERE id = :id"), 
                                  {"id": nesting_id})
                    self.add_fix(f"Nesting #{nesting_id}: stato impostato a 'annullato' (nessun ODL)")
            
            # Verifica nesting con autoclave inesistente
            result = self.db.execute(text("""
                SELECT nr.id, nr.autoclave_id
                FROM nesting_results nr
                LEFT JOIN autoclavi a ON nr.autoclave_id = a.id
                WHERE a.id IS NULL AND nr.autoclave_id IS NOT NULL
            """))
            
            for row in result:
                nesting_id = row.id
                autoclave_id = row.autoclave_id
                
                self.add_issue(
                    "ORPHAN_NESTING",
                    f"Nesting #{nesting_id}: autoclave #{autoclave_id} non esiste",
                    "ERROR"
                )
                all_valid = False
            
            # Verifica parametri fuori range
            result = self.db.execute(text("""
                SELECT id, padding_mm, borda_mm
                FROM nesting_results 
                WHERE padding_mm < 0 OR padding_mm > 100 
                   OR borda_mm < 0 OR borda_mm > 200
            """))
            
            for row in result:
                nesting_id = row.id
                padding_mm = row.padding_mm
                borda_mm = row.borda_mm
                
                self.add_issue(
                    "INVALID_PARAMETERS",
                    f"Nesting #{nesting_id}: parametri fuori range (padding: {padding_mm}, borda: {borda_mm})",
                    "WARNING"
                )
                if self.fix_issues:
                    updates = []
                    if padding_mm < 0 or padding_mm > 100:
                        updates.append("padding_mm = 10.0")
                    if borda_mm < 0 or borda_mm > 200:
                        updates.append("borda_mm = 20.0")
                    
                    if updates:
                        self.db.execute(text(f"UPDATE nesting_results SET {', '.join(updates)} WHERE id = :id"), 
                                      {"id": nesting_id})
                        self.add_fix(f"Nesting #{nesting_id}: parametri corretti")
            
            return all_valid
            
        except Exception as e:
            self.log(f"❌ Errore nella validazione integrità: {e}", "ERROR")
            return False
    
    def run_full_validation(self) -> Dict:
        """
        Esegue la validazione completa
        
        Returns:
            Dizionario con i risultati della validazione
        """
        self.log("🚀 Avvio validazione completa stati nesting...")
        
        results = {
            "nesting_states": self.validate_nesting_states(),
            "odl_consistency": self.validate_odl_nesting_consistency(),
            "autoclave_availability": self.validate_autoclave_availability(),
            "data_integrity": self.validate_data_integrity()
        }
        
        # Applica le correzioni se richiesto
        if self.fix_issues and self.fixes_applied:
            try:
                self.db.commit()
                self.log(f"✅ Applicate {len(self.fixes_applied)} correzioni")
            except Exception as e:
                self.db.rollback()
                self.log(f"❌ Errore nell'applicazione delle correzioni: {e}", "ERROR")
        
        # Riassunto
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i["severity"] == "ERROR"])
        warnings = len([i for i in self.issues if i["severity"] == "WARNING"])
        
        self.log(f"📊 Validazione completata:")
        self.log(f"   - Issues totali: {total_issues}")
        self.log(f"   - Errori critici: {critical_issues}")
        self.log(f"   - Avvisi: {warnings}")
        self.log(f"   - Correzioni applicate: {len(self.fixes_applied)}")
        
        results.update({
            "summary": {
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "fixes_applied": len(self.fixes_applied),
                "overall_valid": all(results.values()) and critical_issues == 0
            },
            "issues": self.issues,
            "fixes": self.fixes_applied
        })
        
        return results

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description="Valida la coerenza degli stati del nesting")
    parser.add_argument("--fix", action="store_true", help="Corregge automaticamente le inconsistenze")
    parser.add_argument("--verbose", action="store_true", help="Output dettagliato")
    
    args = parser.parse_args()
    
    # Connessione al database
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            validator = NestingStateValidator(db, args.verbose, args.fix)
            results = validator.run_full_validation()
            
            # Exit code basato sui risultati
            if results["summary"]["critical_issues"] > 0:
                sys.exit(1)  # Errori critici
            elif results["summary"]["warnings"] > 0:
                sys.exit(2)  # Solo avvisi
            else:
                sys.exit(0)  # Tutto OK
                
    except Exception as e:
        logger.error(f"❌ Errore durante la validazione: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main() 