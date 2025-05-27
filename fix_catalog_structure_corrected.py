#!/usr/bin/env python3
"""
🔧 CORREZIONE STRUTTURA CATALOGO (VERSIONE CORRETTA)
====================================================

Script per correggere la struttura del catalogo adattato alla struttura reale del database:
- Verifica che l'area venga calcolata dai tools collegati
- Corregge dati inconsistenti
- Adattato alla struttura DB esistente

Autore: Sistema CarbonPilot
Data: 2025-01-27
"""

import os
import sys
import logging
from datetime import datetime

# Aggiungi il path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import SessionLocal, engine

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CatalogStructureFixerCorrected:
    """Classe per correggere la struttura del catalogo (versione corretta)"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def analizza_struttura_attuale(self):
        """
        🔍 ANALISI STRUTTURA ATTUALE
        Analizza la struttura attuale del catalogo e identifica problemi
        """
        logger.info("🔍 Analisi struttura attuale del catalogo...")
        
        # Verifica colonne esistenti nella tabella cataloghi
        result = self.db.execute(text("PRAGMA table_info(cataloghi)"))
        colonne = result.fetchall()
        
        logger.info("📋 Colonne attuali nella tabella cataloghi:")
        colonne_problematiche = []
        
        for colonna in colonne:
            nome_colonna = colonna[1]  # Il nome è nel secondo elemento
            tipo_colonna = colonna[2]  # Il tipo è nel terzo elemento
            logger.info(f"   • {nome_colonna}: {tipo_colonna}")
            
            # Identifica colonne problematiche
            if nome_colonna.lower() in ['altezza', 'area_cm2', 'areacm2', 'lunghezza', 'larghezza']:
                colonne_problematiche.append(nome_colonna)
        
        if colonne_problematiche:
            logger.warning(f"⚠️ Colonne problematiche trovate: {colonne_problematiche}")
        else:
            logger.info("✅ Nessuna colonna problematica trovata nel catalogo")
        
        return colonne_problematiche
    
    def verifica_relazioni_catalogo_tool(self):
        """
        🔗 VERIFICA RELAZIONI CATALOGO-TOOL
        Verifica che ogni catalogo abbia tools associati con dimensioni valide
        """
        logger.info("🔗 Verifica relazioni catalogo-tool...")
        
        # Query per trovare cataloghi senza tools associati
        query_cataloghi_senza_tools = text("""
            SELECT c.part_number, c.descrizione 
            FROM cataloghi c
            LEFT JOIN parti p ON c.part_number = p.part_number
            LEFT JOIN parte_tool_association pta ON p.id = pta.parte_id
            LEFT JOIN tools t ON pta.tool_id = t.id
            WHERE t.id IS NULL
        """)
        
        result = self.db.execute(query_cataloghi_senza_tools)
        cataloghi_senza_tools = result.fetchall()
        
        if cataloghi_senza_tools:
            logger.warning(f"⚠️ Trovati {len(cataloghi_senza_tools)} cataloghi senza tools associati:")
            for catalogo in cataloghi_senza_tools:
                logger.warning(f"   • {catalogo[0]}: {catalogo[1]}")
        
        # Query per trovare tools senza dimensioni valide (solo larghezza_piano disponibile)
        query_tools_senza_dimensioni = text("""
            SELECT part_number_tool, larghezza_piano
            FROM tools
            WHERE larghezza_piano IS NULL OR larghezza_piano <= 0
        """)
        
        result = self.db.execute(query_tools_senza_dimensioni)
        tools_senza_dimensioni = result.fetchall()
        
        if tools_senza_dimensioni:
            logger.warning(f"⚠️ Trovati {len(tools_senza_dimensioni)} tools senza dimensioni valide:")
            for tool in tools_senza_dimensioni:
                logger.warning(f"   • {tool[0]}: larghezza={tool[1]}")
        
        # Verifica calcolo area per ogni catalogo (usando solo larghezza_piano)
        logger.info("📐 Verifica calcolo area per cataloghi:")
        
        query_area_cataloghi = text("""
            SELECT c.part_number, c.descrizione, t.larghezza_piano
            FROM cataloghi c
            LEFT JOIN parti p ON c.part_number = p.part_number
            LEFT JOIN parte_tool_association pta ON p.id = pta.parte_id
            LEFT JOIN tools t ON pta.tool_id = t.id
        """)
        
        result = self.db.execute(query_area_cataloghi)
        cataloghi_con_tools = result.fetchall()
        
        for catalogo in cataloghi_con_tools:
            part_number = catalogo[0]
            larghezza = catalogo[2]
            
            if larghezza:
                # Assumiamo lunghezza = larghezza per semplicità (dato che non abbiamo lunghezza_piano)
                area_stimata = (larghezza * larghezza) / 100  # Conversione da mm² a cm²
                logger.info(f"   • {part_number}: Area stimata = {area_stimata:.2f} cm² (larghezza: {larghezza}mm)")
            else:
                logger.warning(f"   ⚠️ {part_number}: Nessuna dimensione disponibile")
        
        return len(cataloghi_senza_tools), len(tools_senza_dimensioni)
    
    def correggi_dati_inconsistenti(self):
        """
        🔧 CORREZIONE DATI INCONSISTENTI
        Corregge dati inconsistenti nel database
        """
        logger.info("🔧 Correzione dati inconsistenti...")
        
        correzioni_effettuate = 0
        
        # 1. Correggi tools con dimensioni nulle o negative
        query_tools_da_correggere = text("""
            SELECT id, part_number_tool, larghezza_piano
            FROM tools
            WHERE larghezza_piano IS NULL OR larghezza_piano <= 0
        """)
        
        result = self.db.execute(query_tools_da_correggere)
        tools_da_correggere = result.fetchall()
        
        for tool in tools_da_correggere:
            tool_id = tool[0]
            part_number_tool = tool[1]
            larghezza_attuale = tool[2]
            
            logger.info(f"   🔧 Correzione tool {part_number_tool}")
            
            # Assegna dimensioni di default se mancanti
            nuova_larghezza = 200.0  # 20cm default
            
            update_query = text("""
                UPDATE tools 
                SET larghezza_piano = :nuova_larghezza
                WHERE id = :tool_id
            """)
            
            self.db.execute(update_query, {
                "nuova_larghezza": nuova_larghezza,
                "tool_id": tool_id
            })
            
            logger.info(f"     • Larghezza impostata a {nuova_larghezza}mm")
            correzioni_effettuate += 1
        
        # 2. Verifica e correggi relazioni parte-tool mancanti
        query_parti_senza_tools = text("""
            SELECT p.id, p.part_number
            FROM parti p
            LEFT JOIN parte_tool_association pta ON p.id = pta.parte_id
            WHERE pta.tool_id IS NULL
        """)
        
        result = self.db.execute(query_parti_senza_tools)
        parti_senza_tools = result.fetchall()
        
        for parte in parti_senza_tools:
            parte_id = parte[0]
            part_number = parte[1]
            
            # Cerca un tool con part_number simile
            query_tool_corrispondente = text("""
                SELECT id FROM tools 
                WHERE part_number_tool LIKE :pattern
                LIMIT 1
            """)
            
            result = self.db.execute(query_tool_corrispondente, {
                "pattern": f"%{part_number}%"
            })
            tool_corrispondente = result.fetchone()
            
            if tool_corrispondente:
                tool_id = tool_corrispondente[0]
                
                # Inserisci associazione
                insert_query = text("""
                    INSERT INTO parte_tool_association (parte_id, tool_id)
                    VALUES (:parte_id, :tool_id)
                """)
                
                try:
                    self.db.execute(insert_query, {
                        "parte_id": parte_id,
                        "tool_id": tool_id
                    })
                    
                    logger.info(f"   🔗 Collegamento parte {part_number} a tool {tool_id}")
                    correzioni_effettuate += 1
                    
                except Exception as e:
                    logger.warning(f"   ⚠️ Errore collegamento {part_number}: {str(e)}")
        
        if correzioni_effettuate > 0:
            self.db.commit()
            logger.info(f"✅ Effettuate {correzioni_effettuate} correzioni")
        else:
            logger.info("✅ Nessuna correzione necessaria")
        
        return correzioni_effettuate
    
    def testa_calcolo_area(self):
        """
        🧪 TEST CALCOLO AREA
        Testa il calcolo dell'area per tutti i cataloghi
        """
        logger.info("🧪 Test calcolo area cataloghi...")
        
        query_cataloghi_con_tools = text("""
            SELECT c.part_number, c.descrizione, t.larghezza_piano, t.part_number_tool
            FROM cataloghi c
            LEFT JOIN parti p ON c.part_number = p.part_number
            LEFT JOIN parte_tool_association pta ON p.id = pta.parte_id
            LEFT JOIN tools t ON pta.tool_id = t.id
        """)
        
        result = self.db.execute(query_cataloghi_con_tools)
        cataloghi = result.fetchall()
        
        risultati_test = []
        
        for catalogo in cataloghi:
            part_number = catalogo[0]
            descrizione = catalogo[1]
            larghezza = catalogo[2]
            tool_part_number = catalogo[3]
            
            try:
                if larghezza and larghezza > 0:
                    # Calcolo area stimata (assumendo forma quadrata)
                    area_stimata = (larghezza * larghezza) / 100  # mm² -> cm²
                    
                    risultato = {
                        "part_number": part_number,
                        "area_calcolata": area_stimata,
                        "larghezza_tool": larghezza,
                        "tool_associato": tool_part_number,
                        "corretto": True
                    }
                    
                    logger.info(f"   ✅ {part_number}: {area_stimata:.2f} cm² (larghezza: {larghezza}mm)")
                else:
                    risultato = {
                        "part_number": part_number,
                        "area_calcolata": 0,
                        "larghezza_tool": larghezza,
                        "tool_associato": tool_part_number,
                        "corretto": False
                    }
                    
                    logger.warning(f"   ⚠️ {part_number}: Nessuna dimensione valida")
                
                risultati_test.append(risultato)
                
            except Exception as e:
                logger.error(f"   ❌ Errore calcolo area per {part_number}: {str(e)}")
                risultati_test.append({
                    "part_number": part_number,
                    "errore": str(e),
                    "corretto": False
                })
        
        # Statistiche finali
        corretti = sum(1 for r in risultati_test if r.get("corretto", False))
        totali = len(risultati_test)
        
        logger.info(f"📊 Risultati test: {corretti}/{totali} cataloghi con calcolo area corretto")
        
        return risultati_test
    
    def genera_report_correzioni(self):
        """
        📊 GENERAZIONE REPORT CORREZIONI
        Genera un report dettagliato delle correzioni effettuate
        """
        logger.info("📊 Generazione report correzioni...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"catalog_structure_fix_report_corrected_{timestamp}.txt"
        
        with open(nome_file, 'w', encoding='utf-8') as f:
            f.write("🔧 REPORT CORREZIONE STRUTTURA CATALOGO (CORRETTA)\n")
            f.write("=" * 55 + "\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Analisi struttura
            f.write("📋 ANALISI STRUTTURA:\n")
            colonne_problematiche = self.analizza_struttura_attuale()
            if colonne_problematiche:
                f.write(f"Colonne problematiche: {colonne_problematiche}\n")
            else:
                f.write("Nessuna colonna problematica trovata\n")
            f.write("\n")
            
            # Verifica relazioni
            f.write("🔗 VERIFICA RELAZIONI:\n")
            cataloghi_senza_tools, tools_senza_dimensioni = self.verifica_relazioni_catalogo_tool()
            f.write(f"Cataloghi senza tools: {cataloghi_senza_tools}\n")
            f.write(f"Tools senza dimensioni valide: {tools_senza_dimensioni}\n\n")
            
            # Test calcolo area
            f.write("🧪 TEST CALCOLO AREA:\n")
            risultati_test = self.testa_calcolo_area()
            corretti = sum(1 for r in risultati_test if r.get("corretto", False))
            f.write(f"Cataloghi con calcolo corretto: {corretti}/{len(risultati_test)}\n\n")
            
            # Dettagli per cataloghi con problemi
            problematici = [r for r in risultati_test if not r.get("corretto", False)]
            if problematici:
                f.write("❌ CATALOGHI CON PROBLEMI:\n")
                for r in problematici:
                    f.write(f"- {r['part_number']}: {r.get('errore', 'Calcolo area errato')}\n")
            
            f.write("\n📝 NOTE:\n")
            f.write("- Il calcolo area è basato solo su larghezza_piano (assumendo forma quadrata)\n")
            f.write("- La struttura DB attuale non include lunghezza_piano nei tools\n")
            f.write("- Per calcoli più precisi, aggiungere colonna lunghezza_piano\n")
            
        logger.info(f"📊 Report salvato in: {nome_file}")
        return nome_file
    
    def esegui_correzione_completa(self):
        """
        🚀 ESECUZIONE CORREZIONE COMPLETA
        Metodo principale che coordina tutte le correzioni
        """
        logger.info("🚀 Inizio correzione completa struttura catalogo (versione corretta)...")
        
        try:
            # 1. Analisi struttura attuale
            colonne_problematiche = self.analizza_struttura_attuale()
            
            # 2. Verifica relazioni
            self.verifica_relazioni_catalogo_tool()
            
            # 3. Correzione dati inconsistenti
            correzioni = self.correggi_dati_inconsistenti()
            
            # 4. Test calcolo area
            self.testa_calcolo_area()
            
            # 5. Generazione report
            nome_report = self.genera_report_correzioni()
            
            logger.info("🎯 Correzione struttura catalogo completata!")
            logger.info(f"📄 Report salvato in: {nome_report}")
            
            return nome_report
            
        except Exception as e:
            logger.error(f"❌ Errore durante correzione: {str(e)}")
            self.db.rollback()
            raise

def main():
    """Funzione principale per eseguire la correzione"""
    print("🔧 CORREZIONE STRUTTURA CATALOGO (VERSIONE CORRETTA)")
    print("=" * 55)
    
    with CatalogStructureFixerCorrected() as fixer:
        nome_report = fixer.esegui_correzione_completa()
        print(f"\n📄 Report correzioni salvato in: {nome_report}")

if __name__ == "__main__":
    main() 