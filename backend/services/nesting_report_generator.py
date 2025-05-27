"""
🧠 Generatore di Report PDF per Nesting Completati
Questo modulo si occupa di generare automaticamente un report PDF dettagliato
quando un nesting passa da ATTIVO a COMPLETATO.

Il report include:
- Informazioni del nesting (ID, data, autoclave)
- Lista degli ODL e PN associati
- Dettagli dei tool (dimensioni, peso, materiale)
- Ciclo di cura utilizzato
- Piano/i utilizzati
- Stato finale del processo
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte
from models.tool import Tool
from models.ciclo_cura import CicloCura
from models.report import Report, ReportTypeEnum

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NestingReportGenerator:
    """Generatore di report PDF per nesting completati"""
    
    def __init__(self, db: Session):
        """
        Inizializza il generatore di report.
        
        Args:
            db: Sessione del database
        """
        self.db = db
        self.reports_dir = "reports/generated"
        
        # Crea la directory dei report se non esiste
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Stili per il PDF
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura gli stili personalizzati per il PDF"""
        # Titolo principale
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Centrato
        ))
        
        # Sottotitolo
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkgreen
        ))
        
        # Testo normale con spaziatura
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        # Testo per tabelle
        self.styles.add(ParagraphStyle(
            name='TableText',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11
        ))
    
    def generate_nesting_report(self, nesting_id: int) -> Optional[Tuple[str, Report]]:
        """
        Genera un report PDF per un nesting completato.
        
        Args:
            nesting_id: ID del nesting per cui generare il report
            
        Returns:
            Tupla con (percorso_file, record_report) o None in caso di errore
        """
        try:
            # Carica il nesting con tutte le relazioni necessarie
            nesting = self._load_nesting_data(nesting_id)
            if not nesting:
                logger.error(f"Nesting {nesting_id} non trovato")
                return None
            
            # Verifica che il nesting sia completato
            if nesting.stato != "Completato":
                logger.warning(f"Nesting {nesting_id} non è completato (stato: {nesting.stato})")
                return None
            
            # Verifica che non esista già un report
            if nesting.report_id:
                logger.info(f"Report già esistente per nesting {nesting_id}")
                existing_report = self.db.query(Report).filter(Report.id == nesting.report_id).first()
                if existing_report and os.path.exists(existing_report.file_path):
                    return existing_report.file_path, existing_report
            
            # Genera il nome del file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nesting_report_{nesting_id}_{timestamp}.pdf"
            file_path = os.path.join(self.reports_dir, filename)
            
            # Genera il PDF
            self._create_pdf_report(nesting, file_path)
            
            # Salva il record nel database
            report_record = self._save_report_record(nesting, filename, file_path)
            
            # Collega il report al nesting
            nesting.report_id = report_record.id
            self.db.commit()
            
            logger.info(f"✅ Report generato con successo: {file_path}")
            return file_path, report_record
            
        except Exception as e:
            logger.error(f"❌ Errore durante la generazione del report per nesting {nesting_id}: {e}")
            self.db.rollback()
            return None
    
    def _load_nesting_data(self, nesting_id: int) -> Optional[NestingResult]:
        """Carica i dati del nesting con tutte le relazioni necessarie"""
        return self.db.query(NestingResult).options(
            joinedload(NestingResult.autoclave),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte).joinedload(Parte.catalogo),
            joinedload(NestingResult.odl_list).joinedload(ODL.parte).joinedload(Parte.ciclo_cura),
            joinedload(NestingResult.odl_list).joinedload(ODL.tool)
        ).filter(NestingResult.id == nesting_id).first()
    
    def _create_pdf_report(self, nesting: NestingResult, file_path: str):
        """Crea il file PDF del report"""
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Contenuto del report
        story = []
        
        # Header del report
        story.extend(self._create_header(nesting))
        story.append(Spacer(1, 20))
        
        # Informazioni generali del nesting
        story.extend(self._create_nesting_info_section(nesting))
        story.append(Spacer(1, 20))
        
        # Informazioni autoclave
        story.extend(self._create_autoclave_info_section(nesting))
        story.append(Spacer(1, 20))
        
        # Lista ODL e PN
        story.extend(self._create_odl_section(nesting))
        story.append(Spacer(1, 20))
        
        # Dettagli tool
        story.extend(self._create_tool_section(nesting))
        story.append(Spacer(1, 20))
        
        # Ciclo di cura
        story.extend(self._create_cycle_section(nesting))
        story.append(Spacer(1, 20))
        
        # Utilizzo piani
        story.extend(self._create_planes_section(nesting))
        story.append(Spacer(1, 20))
        
        # Stato finale
        story.extend(self._create_status_section(nesting))
        
        # Genera il PDF
        doc.build(story)
    
    def _create_header(self, nesting: NestingResult) -> List:
        """Crea l'header del report"""
        elements = []
        
        # Titolo principale
        title = Paragraph(
            f"📄 REPORT NESTING COMPLETATO",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Sottotitolo con ID e data
        subtitle = Paragraph(
            f"Nesting ID: {nesting.id} | Data: {nesting.created_at.strftime('%d/%m/%Y %H:%M')}",
            self.styles['CustomSubtitle']
        )
        elements.append(subtitle)
        
        return elements
    
    def _create_nesting_info_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con le informazioni generali del nesting"""
        elements = []
        
        elements.append(Paragraph("🔍 INFORMAZIONI GENERALI", self.styles['CustomSubtitle']))
        
        # Tabella con le informazioni principali
        data = [
            ['Campo', 'Valore'],
            ['ID Nesting', str(nesting.id)],
            ['Data Creazione', nesting.created_at.strftime('%d/%m/%Y %H:%M:%S')],
            ['Stato', nesting.stato],
            ['Confermato da', nesting.confermato_da_ruolo or 'N/A'],
            ['Peso Totale', f"{nesting.peso_totale_kg:.2f} kg"],
            ['Note', nesting.note or 'Nessuna nota']
        ]
        
        table = Table(data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        return elements
    
    def _create_autoclave_info_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con le informazioni dell'autoclave"""
        elements = []
        
        elements.append(Paragraph("🏭 AUTOCLAVE UTILIZZATA", self.styles['CustomSubtitle']))
        
        autoclave = nesting.autoclave
        if autoclave:
            data = [
                ['Campo', 'Valore'],
                ['Nome', autoclave.nome],
                ['Codice', autoclave.codice],
                ['Dimensioni', f"{autoclave.lunghezza} x {autoclave.larghezza_piano} cm"],
                ['Area Totale', f"{autoclave.lunghezza * autoclave.larghezza_piano:.0f} cm²"],
                ['Linee Vuoto', str(autoclave.num_linee_vuoto)],
                ['Stato', autoclave.stato.value if autoclave.stato else 'N/A']
            ]
        else:
            data = [
                ['Campo', 'Valore'],
                ['Autoclave', 'Informazioni non disponibili']
            ]
        
        table = Table(data, colWidths=[4*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        return elements
    
    def _create_odl_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con la lista degli ODL"""
        elements = []
        
        elements.append(Paragraph("📋 ODL INCLUSI NEL NESTING", self.styles['CustomSubtitle']))
        
        if not nesting.odl_list:
            elements.append(Paragraph("Nessun ODL trovato", self.styles['CustomNormal']))
            return elements
        
        # Header della tabella
        data = [['ODL ID', 'Part Number', 'Descrizione', 'Priorità', 'Stato']]
        
        # Aggiungi i dati degli ODL
        for odl in nesting.odl_list:
            part_number = 'N/A'
            descrizione = 'N/A'
            
            if odl.parte and odl.parte.catalogo:
                part_number = odl.parte.catalogo.part_number
                descrizione = odl.parte.descrizione_breve or 'N/A'
            
            data.append([
                str(odl.id),
                part_number,
                descrizione[:40] + '...' if len(descrizione) > 40 else descrizione,
                str(odl.priorita),
                odl.status
            ])
        
        table = Table(data, colWidths=[2*cm, 3*cm, 6*cm, 2*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(table)
        return elements
    
    def _create_tool_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con i dettagli dei tool"""
        elements = []
        
        elements.append(Paragraph("🔧 DETTAGLI TOOL", self.styles['CustomSubtitle']))
        
        # Raccogli i tool unici
        tools = []
        for odl in nesting.odl_list:
            if odl.tool and odl.tool not in tools:
                tools.append(odl.tool)
        
        if not tools:
            elements.append(Paragraph("Nessun tool associato", self.styles['CustomNormal']))
            return elements
        
        # Header della tabella
        data = [['Codice Tool', 'Dimensioni (cm)', 'Peso (kg)', 'Materiale', 'Note']]
        
        # Aggiungi i dati dei tool
        for tool in tools:
            dimensioni = f"{tool.lunghezza}x{tool.larghezza}x{tool.altezza}" if all([tool.lunghezza, tool.larghezza, tool.altezza]) else 'N/A'
            peso = f"{tool.peso:.2f}" if tool.peso else 'N/A'
            materiale = tool.materiale or 'N/A'
            note = (tool.note[:30] + '...') if tool.note and len(tool.note) > 30 else (tool.note or 'N/A')
            
            data.append([
                tool.codice,
                dimensioni,
                peso,
                materiale,
                note
            ])
        
        table = Table(data, colWidths=[3*cm, 3*cm, 2*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(table)
        return elements
    
    def _create_cycle_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con le informazioni del ciclo di cura"""
        elements = []
        
        elements.append(Paragraph("⚙️ CICLO DI CURA", self.styles['CustomSubtitle']))
        
        # Raccogli i cicli di cura unici
        cicli = set()
        for odl in nesting.odl_list:
            if odl.parte and odl.parte.ciclo_cura:
                cicli.add(odl.parte.ciclo_cura)
        
        if not cicli:
            elements.append(Paragraph("Nessun ciclo di cura definito", self.styles['CustomNormal']))
            return elements
        
        for ciclo in cicli:
            data = [
                ['Parametro', 'Valore'],
                ['Nome Ciclo', ciclo.nome],
                ['Temperatura', f"{ciclo.temperatura}°C" if ciclo.temperatura else 'N/A'],
                ['Durata', f"{ciclo.durata_minuti} min" if ciclo.durata_minuti else 'N/A'],
                ['Pressione', f"{ciclo.pressione} bar" if ciclo.pressione else 'N/A'],
                ['Descrizione', ciclo.descrizione or 'N/A']
            ]
            
            table = Table(data, colWidths=[4*cm, 10*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_planes_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con l'utilizzo dei piani"""
        elements = []
        
        elements.append(Paragraph("📐 UTILIZZO PIANI", self.styles['CustomSubtitle']))
        
        data = [
            ['Piano', 'Area Utilizzata (cm²)', 'Efficienza (%)'],
            ['Piano 1', f"{nesting.area_piano_1:.2f}", f"{nesting.efficienza_piano_1:.1f}%"],
            ['Piano 2', f"{nesting.area_piano_2:.2f}", f"{nesting.efficienza_piano_2:.1f}%"],
            ['TOTALE', f"{nesting.area_piano_1 + nesting.area_piano_2:.2f}", f"{nesting.efficienza_totale:.1f}%"]
        ]
        
        table = Table(data, colWidths=[4*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.mistyrose),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightcoral),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        return elements
    
    def _create_status_section(self, nesting: NestingResult) -> List:
        """Crea la sezione con lo stato finale"""
        elements = []
        
        elements.append(Paragraph("✅ STATO FINALE", self.styles['CustomSubtitle']))
        
        # Per ora usiamo un placeholder per lo stato
        stato_finale = "✅ Riuscito" if nesting.stato == "Completato" else "⚠️ Fallito"
        
        status_text = Paragraph(
            f"<b>Stato del processo:</b> {stato_finale}<br/>"
            f"<b>Data completamento:</b> {nesting.updated_at.strftime('%d/%m/%Y %H:%M:%S')}<br/>"
            f"<b>Report generato il:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            self.styles['CustomNormal']
        )
        
        elements.append(status_text)
        return elements
    
    def _save_report_record(self, nesting: NestingResult, filename: str, file_path: str) -> Report:
        """Salva il record del report nel database"""
        # Calcola la dimensione del file
        file_size = None
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        # Crea il record nel database
        report = Report(
            filename=filename,
            file_path=file_path,
            report_type=ReportTypeEnum.NESTING,
            generated_for_user_id=None,  # Per ora nullable
            period_start=nesting.created_at,
            period_end=nesting.updated_at,
            include_sections="header,nesting,odl,tool,cycle,planes,status",
            file_size_bytes=file_size
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report 