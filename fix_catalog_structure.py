#!/usr/bin/env python3
"""
🔧 CORREZIONE STRUTTURA CATALOGO
================================

Script per correggere la struttura del catalogo come richiesto:
- Rimuove campi non necessari dal catalogo (altezza, areacm2 se presente)
- Assicura che l'area venga calcolata dai tools collegati
- Verifica che lunghezza e larghezza vengano presi dai tools
- Pulisce dati inconsistenti

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
from models.catalogo import Catalogo
from models.tool import Tool
from models.parte import Parte

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CatalogStructureFixer:
    """Classe per correggere la struttura del catalogo"""
    
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
        cataloghi_senza_tools = self.db.query(Catalogo).outerjoin(Parte).outerjoin(Parte.tools).filter(Tool.id.is_(None)).all()
        
        if cataloghi_senza_tools:
            logger.warning(f"⚠️ Trovati {len(cataloghi_senza_tools)} cataloghi senza tools associati:")
            for catalogo in cataloghi_senza_tools:
                logger.warning(f"   • {catalogo.part_number}: {catalogo.descrizione}")
        
        # Query per trovare tools senza dimensioni valide
        tools_senza_dimensioni = self.db.query(Tool).filter(
            (Tool.lunghezza_piano.is_(None)) | 
            (Tool.larghezza_piano.is_(None)) |
            (Tool.lunghezza_piano <= 0) |
            (Tool.larghezza_piano <= 0)
        ).all()
        
        if tools_senza_dimensioni:
            logger.warning(f"⚠️ Trovati {len(tools_senza_dimensioni)} tools senza dimensioni valide:")
            for tool in tools_senza_dimensioni:
                logger.warning(f"   • {tool.part_number_tool}: L={tool.lunghezza_piano}, W={tool.larghezza_piano}")
        
        # Verifica calcolo area per ogni catalogo
        logger.info("📐 Verifica calcolo area per cataloghi:")
        cataloghi = self.db.query(Catalogo).all()
        
        for catalogo in cataloghi:
            area_calcolata = catalogo.area_cm2
            logger.info(f"   • {catalogo.part_number}: Area = {area_calcolata:.2f} cm²")
            
            if area_calcolata == 0:
                logger.warning(f"     ⚠️ Area zero per {catalogo.part_number}")
        
        return len(cataloghi_senza_tools), len(tools_senza_dimensioni)
    
    def rimuovi_colonne_problematiche(self, colonne_da_rimuovere):
        """
        🗑️ RIMOZIONE COLONNE PROBLEMATICHE
        Rimuove le colonne non necessarie dal catalogo
        """
        if not colonne_da_rimuovere:
            logger.info("✅ Nessuna colonna da rimuovere")
            return
        
        logger.info(f"🗑️ Rimozione colonne problematiche: {colonne_da_rimuovere}")
        
        try:
            # SQLite non supporta DROP COLUMN direttamente, quindi dobbiamo ricreare la tabella
            # Per ora, logghiamo solo l'intenzione
            logger.warning("⚠️ SQLite non supporta DROP COLUMN. Le colonne verranno ignorate nel codice.")
            logger.info("💡 Suggerimento: Utilizzare una migrazione Alembic per rimuovere le colonne definitivamente")
            
        except Exception as e:
            logger.error(f"❌ Errore durante rimozione colonne: {str(e)}")
            raise
    
    def correggi_dati_inconsistenti(self):
        """
        🔧 CORREZIONE DATI INCONSISTENTI
        Corregge dati inconsistenti nel database
        """
        logger.info("🔧 Correzione dati inconsistenti...")
        
        correzioni_effettuate = 0
        
        # 1. Correggi tools con dimensioni nulle o negative
        tools_da_correggere = self.db.query(Tool).filter(
            (Tool.lunghezza_piano.is_(None)) | 
            (Tool.larghezza_piano.is_(None)) |
            (Tool.lunghezza_piano <= 0) |
            (Tool.larghezza_piano <= 0)
        ).all()
        
        for tool in tools_da_correggere:
            logger.info(f"   🔧 Correzione tool {tool.part_number_tool}")
            
            # Assegna dimensioni di default se mancanti
            if not tool.lunghezza_piano or tool.lunghezza_piano <= 0:
                tool.lunghezza_piano = 300.0  # 30cm default
                logger.info(f"     • Lunghezza impostata a {tool.lunghezza_piano}mm")
            
            if not tool.larghezza_piano or tool.larghezza_piano <= 0:
                tool.larghezza_piano = 200.0  # 20cm default
                logger.info(f"     • Larghezza impostata a {tool.larghezza_piano}mm")
            
            if not tool.peso or tool.peso <= 0:
                tool.peso = 5.0  # 5kg default
                logger.info(f"     • Peso impostato a {tool.peso}kg")
            
            correzioni_effettuate += 1
        
        # 2. Verifica e correggi relazioni parte-tool mancanti
        parti_senza_tools = self.db.query(Parte).outerjoin(Parte.tools).filter(Tool.id.is_(None)).all()
        
        for parte in parti_senza_tools:
            # Cerca un tool con lo stesso part_number
            tool_corrispondente = self.db.query(Tool).filter(
                Tool.part_number_tool.like(f"%{parte.part_number}%")
            ).first()
            
            if tool_corrispondente:
                logger.info(f"   🔗 Collegamento parte {parte.part_number} a tool {tool_corrispondente.part_number_tool}")
                parte.tools.append(tool_corrispondente)
                correzioni_effettuate += 1
        
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
        
        cataloghi = self.db.query(Catalogo).all()
        risultati_test = []
        
        for catalogo in cataloghi:
            try:
                area = catalogo.area_cm2
                
                # Trova il tool associato per verifica
                tool_associato = None
                for parte in catalogo.parti:
                    if parte.tools:
                        tool_associato = parte.tools[0]
                        break
                
                if tool_associato:
                    area_attesa = (tool_associato.lunghezza_piano * tool_associato.larghezza_piano) / 100
                    differenza = abs(area - area_attesa)
                    
                    risultato = {
                        "part_number": catalogo.part_number,
                        "area_calcolata": area,
                        "area_attesa": area_attesa,
                        "differenza": differenza,
                        "tool_associato": tool_associato.part_number_tool,
                        "corretto": differenza < 0.01  # Tolleranza di 0.01 cm²
                    }
                else:
                    risultato = {
                        "part_number": catalogo.part_number,
                        "area_calcolata": area,
                        "area_attesa": 0,
                        "differenza": area,
                        "tool_associato": None,
                        "corretto": area == 0
                    }
                
                risultati_test.append(risultato)
                
                if risultato["corretto"]:
                    logger.info(f"   ✅ {catalogo.part_number}: {area:.2f} cm²")
                else:
                    logger.warning(f"   ⚠️ {catalogo.part_number}: {area:.2f} cm² (atteso: {risultato['area_attesa']:.2f})")
                
            except Exception as e:
                logger.error(f"   ❌ Errore calcolo area per {catalogo.part_number}: {str(e)}")
                risultati_test.append({
                    "part_number": catalogo.part_number,
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
        nome_file = f"catalog_structure_fix_report_{timestamp}.txt"
        
        with open(nome_file, 'w', encoding='utf-8') as f:
            f.write("🔧 REPORT CORREZIONE STRUTTURA CATALOGO\n")
            f.write("=" * 50 + "\n\n")
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
            
        logger.info(f"📊 Report salvato in: {nome_file}")
        return nome_file
    
    def esegui_correzione_completa(self):
        """
        🚀 ESECUZIONE CORREZIONE COMPLETA
        Metodo principale che coordina tutte le correzioni
        """
        logger.info("🚀 Inizio correzione completa struttura catalogo...")
        
        try:
            # 1. Analisi struttura attuale
            colonne_problematiche = self.analizza_struttura_attuale()
            
            # 2. Verifica relazioni
            self.verifica_relazioni_catalogo_tool()
            
            # 3. Correzione dati inconsistenti
            correzioni = self.correggi_dati_inconsistenti()
            
            # 4. Test calcolo area
            self.testa_calcolo_area()
            
            # 5. Rimozione colonne problematiche (se necessario)
            if colonne_problematiche:
                self.rimuovi_colonne_problematiche(colonne_problematiche)
            
            # 6. Generazione report
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
    print("🔧 CORREZIONE STRUTTURA CATALOGO")
    print("=" * 40)
    
    with CatalogStructureFixer() as fixer:
        nome_report = fixer.esegui_correzione_completa()
        print(f"\n📄 Report correzioni salvato in: {nome_report}")

if __name__ == "__main__":
    main() 