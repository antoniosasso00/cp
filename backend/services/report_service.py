"""
Servizio per la generazione di report PDF.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, between
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF

from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte
from models.tempo_fase import TempoFase
from models.schedule_entry import ScheduleEntry

class ReportService:
    """Servizio per la generazione di report PDF"""
    
    def __init__(self, db: Session):
        """
        Inizializza il servizio report.
        
        Args:
            db: Sessione del database
        """
        self.db = db
        self.reports_dir = "/app/reports"
        
        # Crea la directory dei report se non esiste
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _get_date_range(self, range_type: str) -> tuple[datetime, datetime]:
        """
        Calcola l'intervallo di date basato sul tipo di range.
        
        Args:
            range_type: Tipo di periodo ('giorno', 'settimana', 'mese')
            
        Returns:
            Tupla con data inizio e fine
        """
        today = datetime.now()
        
        if range_type == "giorno":
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif range_type == "settimana":
            # Inizio settimana (lunedì)
            days_since_monday = today.weekday()
            start_date = (today - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = start_date + timedelta(days=7)
        elif range_type == "mese":
            # Primo giorno del mese corrente
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Primo giorno del mese successivo
            if today.month == 12:
                end_date = start_date.replace(year=today.year + 1, month=1)
            else:
                end_date = start_date.replace(month=today.month + 1)
        else:
            raise ValueError(f"Range type non supportato: {range_type}")
        
        return start_date, end_date
    
    def _get_nesting_data(self, start_date: datetime, end_date: datetime) -> List[NestingResult]:
        """
        Recupera i dati di nesting per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            Lista di risultati nesting
        """
        return (
            self.db.query(NestingResult)
            .options(
                joinedload(NestingResult.autoclave),
                joinedload(NestingResult.odl_list).joinedload(ODL.parte),
                joinedload(NestingResult.odl_list).joinedload(ODL.tool)
            )
            .filter(
                between(NestingResult.created_at, start_date, end_date)
            )
            .order_by(NestingResult.created_at.desc())
            .all()
        )
    
    def _get_odl_data(self, start_date: datetime, end_date: datetime) -> List[ODL]:
        """
        Recupera i dati ODL per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            Lista di ODL
        """
        return (
            self.db.query(ODL)
            .options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            )
            .filter(
                between(ODL.data_creazione, start_date, end_date)
            )
            .order_by(ODL.data_creazione.desc())
            .all()
        )
    
    def _get_tempo_fasi_data(self, start_date: datetime, end_date: datetime) -> List[TempoFase]:
        """
        Recupera i dati dei tempi fase per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            
        Returns:
            Lista di tempi fase
        """
        return (
            self.db.query(TempoFase)
            .options(
                joinedload(TempoFase.parte),
                joinedload(TempoFase.ciclo_cura)
            )
            .filter(
                between(TempoFase.data_aggiornamento, start_date, end_date)
            )
            .order_by(TempoFase.data_aggiornamento.desc())
            .all()
        )
    
    def _create_nesting_layout_drawing(self, nesting_results: List[NestingResult]) -> Drawing:
        """
        Crea un disegno SVG del layout nesting.
        
        Args:
            nesting_results: Lista dei risultati nesting
            
        Returns:
            Drawing object per reportlab
        """
        drawing = Drawing(400, 300)
        
        # Disegna un layout semplice delle autoclavi
        y_offset = 250
        x_offset = 50
        
        for i, nesting in enumerate(nesting_results[:4]):  # Max 4 autoclavi per pagina
            # Disegna rettangolo autoclave
            autoclave_width = 80
            autoclave_height = 40
            
            # Colore in base all'utilizzo
            usage_ratio = nesting.area_utilizzata / max(nesting.area_totale, 1)
            if usage_ratio > 0.8:
                color = colors.red
            elif usage_ratio > 0.6:
                color = colors.orange
            elif usage_ratio > 0.3:
                color = colors.yellow
            else:
                color = colors.lightgreen
            
            # Disegna autoclave
            rect = Rect(
                x_offset + (i % 2) * 150,
                y_offset - (i // 2) * 100,
                autoclave_width,
                autoclave_height,
                fillColor=color,
                strokeColor=colors.black
            )
            drawing.add(rect)
            
            # Aggiungi testo con nome autoclave
            from reportlab.graphics.shapes import String
            text = String(
                x_offset + (i % 2) * 150 + 5,
                y_offset - (i // 2) * 100 + 45,
                f"{nesting.autoclave.nome}",
                fontSize=8
            )
            drawing.add(text)
            
            # Aggiungi info utilizzo
            usage_text = String(
                x_offset + (i % 2) * 150 + 5,
                y_offset - (i // 2) * 100 + 25,
                f"ODL: {len(nesting.odl_list)}",
                fontSize=6
            )
            drawing.add(usage_text)
            
            area_text = String(
                x_offset + (i % 2) * 150 + 5,
                y_offset - (i // 2) * 100 + 15,
                f"Area: {nesting.area_utilizzata:.1f}/{nesting.area_totale:.1f}",
                fontSize=6
            )
            drawing.add(area_text)
        
        return drawing
    
    async def generate_report(self, range_type: str, include_sections: List[str]) -> str:
        """
        Genera un report PDF per il periodo specificato.
        
        Args:
            range_type: Tipo di periodo ('giorno', 'settimana', 'mese')
            include_sections: Sezioni opzionali da includere
            
        Returns:
            Path del file PDF generato
        """
        # Calcola l'intervallo di date
        start_date, end_date = self._get_date_range(range_type)
        
        # Genera il nome del file
        date_str = start_date.strftime("%Y-%m-%d")
        filename = f"report_{range_type}_{date_str}.pdf"
        file_path = os.path.join(self.reports_dir, filename)
        
        # Crea il documento PDF
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Titolo del report
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1  # Centrato
        )
        
        title = f"Report CarbonPilot - {range_type.capitalize()}"
        story.append(Paragraph(title, title_style))
        
        # Sottotitolo con periodo
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=20,
            alignment=1
        )
        
        period_text = f"Periodo: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        story.append(Paragraph(period_text, subtitle_style))
        
        story.append(Spacer(1, 20))
        
        # SEZIONE 1: Riepilogo Nesting
        story.append(Paragraph("1. Riepilogo Nesting", styles['Heading2']))
        
        nesting_data = self._get_nesting_data(start_date, end_date)
        
        if nesting_data:
            # Tabella riassuntiva nesting
            nesting_table_data = [['Autoclave', 'ODL Assegnati', 'Area Utilizzata', 'Valvole Utilizzate', 'Data']]
            
            for nesting in nesting_data:
                nesting_table_data.append([
                    nesting.autoclave.nome,
                    str(len(nesting.odl_list)),
                    f"{nesting.area_utilizzata:.2f}/{nesting.area_totale:.2f} m²",
                    f"{nesting.valvole_utilizzate}/{nesting.valvole_totali}",
                    nesting.created_at.strftime('%d/%m/%Y %H:%M')
                ])
            
            nesting_table = Table(nesting_table_data)
            nesting_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(nesting_table)
            story.append(Spacer(1, 20))
            
            # Layout grafico nesting
            story.append(Paragraph("1.1 Layout Visivo Autoclavi", styles['Heading3']))
            layout_drawing = self._create_nesting_layout_drawing(nesting_data)
            story.append(layout_drawing)
            story.append(Spacer(1, 20))
            
        else:
            story.append(Paragraph("Nessun dato di nesting trovato per il periodo specificato.", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # SEZIONE 2: ODL (se richiesta)
        if "odl" in include_sections:
            story.append(Paragraph("2. Dettaglio ODL", styles['Heading2']))
            
            odl_data = self._get_odl_data(start_date, end_date)
            
            if odl_data:
                odl_table_data = [['ID ODL', 'Parte', 'Tool', 'Priorità', 'Status', 'Data Creazione']]
                
                for odl in odl_data:
                    odl_table_data.append([
                        str(odl.id),
                        odl.parte.descrizione_breve if odl.parte else "N/A",
                        odl.tool.codice if odl.tool else "N/A",
                        str(odl.priorita),
                        odl.status,
                        odl.data_creazione.strftime('%d/%m/%Y')
                    ])
                
                odl_table = Table(odl_table_data)
                odl_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(odl_table)
                story.append(Spacer(1, 20))
            else:
                story.append(Paragraph("Nessun ODL trovato per il periodo specificato.", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # SEZIONE 3: Tempi Fase (se richiesta)
        if "tempi" in include_sections:
            story.append(Paragraph("3. Tempi Fase", styles['Heading2']))
            
            tempi_data = self._get_tempo_fasi_data(start_date, end_date)
            
            if tempi_data:
                tempi_table_data = [['Parte', 'Ciclo Cura', 'Tempo (min)', 'Tipo Fase', 'Data Aggiornamento']]
                
                for tempo in tempi_data:
                    tempi_table_data.append([
                        tempo.parte.descrizione_breve if tempo.parte else "N/A",
                        tempo.ciclo_cura.descrizione if tempo.ciclo_cura else "N/A",
                        str(tempo.tempo_minuti),
                        tempo.tipo_fase,
                        tempo.data_aggiornamento.strftime('%d/%m/%Y')
                    ])
                
                tempi_table = Table(tempi_table_data)
                tempi_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(tempi_table)
                story.append(Spacer(1, 20))
            else:
                story.append(Paragraph("Nessun dato sui tempi fase trovato per il periodo specificato.", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            textColor=colors.grey
        )
        
        footer_text = f"Report generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} - CarbonPilot v0.9.0"
        story.append(Paragraph(footer_text, footer_style))
        
        # Genera il PDF
        doc.build(story)
        
        return file_path 