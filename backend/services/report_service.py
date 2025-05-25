"""
Servizio per la generazione di report PDF completo e scalabile.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, between, or_
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

from models.nesting_result import NestingResult
from models.odl import ODL
from models.autoclave import Autoclave
from models.parte import Parte
from models.tempo_fase import TempoFase
from models.schedule_entry import ScheduleEntry
from models.report import Report, ReportTypeEnum

class ReportService:
    """Servizio per la generazione di report PDF"""
    
    def __init__(self, db: Session):
        """
        Inizializza il servizio report.
        
        Args:
            db: Sessione del database
        """
        self.db = db
        self.reports_dir = "reports/generated"
        
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
    
    def _get_sections_for_report_type(self, report_type: ReportTypeEnum, custom_sections: List[str]) -> List[str]:
        """
        Determina quali sezioni includere in base al tipo di report.
        
        Args:
            report_type: Tipo di report
            custom_sections: Sezioni personalizzate richieste
            
        Returns:
            Lista delle sezioni da includere
        """
        # Sezioni predefinite per ogni tipo di report
        default_sections = {
            ReportTypeEnum.PRODUZIONE: ["header", "odl", "tempi"],
            ReportTypeEnum.QUALITA: ["header", "odl", "nesting"],
            ReportTypeEnum.TEMPI: ["header", "tempi"],
            ReportTypeEnum.NESTING: ["header", "nesting"],
            ReportTypeEnum.COMPLETO: ["header", "nesting", "odl", "tempi"]
        }
        
        # Usa le sezioni predefinite o quelle personalizzate
        if custom_sections:
            sections = ["header"] + custom_sections
        else:
            sections = default_sections.get(report_type, ["header", "nesting"])
        
        return list(set(sections))  # Rimuove duplicati
    
    def _save_report_to_db(
        self, 
        filename: str, 
        file_path: str, 
        report_type: ReportTypeEnum,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        include_sections: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> Report:
        """
        Salva i metadati del report nel database.
        
        Args:
            filename: Nome del file
            file_path: Percorso completo del file
            report_type: Tipo di report
            period_start: Data di inizio del periodo
            period_end: Data di fine del periodo
            include_sections: Sezioni incluse nel report
            user_id: ID dell'utente per cui è stato generato
            
        Returns:
            Oggetto Report salvato
        """
        # Calcola la dimensione del file
        file_size = None
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        # Crea il record nel database
        report = Report(
            filename=filename,
            file_path=file_path,
            report_type=report_type,
            generated_for_user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            include_sections=",".join(include_sections) if include_sections else None,
            file_size_bytes=file_size
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report
    
    def get_reports_with_filters(
        self,
        report_type: Optional[ReportTypeEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        odl_filter: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Report]:
        """
        Recupera i report dal database con filtri.
        
        Args:
            report_type: Filtra per tipo di report
            start_date: Data di inizio per il filtro
            end_date: Data di fine per il filtro
            odl_filter: Filtro per ODL o PN (non implementato in questa versione)
            user_id: Filtra per utente
            limit: Numero massimo di risultati
            offset: Offset per la paginazione
            
        Returns:
            Lista di report filtrati
        """
        query = self.db.query(Report)
        
        # Applica filtri
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        if start_date:
            query = query.filter(Report.created_at >= start_date)
        
        if end_date:
            query = query.filter(Report.created_at <= end_date)
        
        if user_id:
            query = query.filter(Report.generated_for_user_id == user_id)
        
        # Ordina per data di creazione (più recente prima)
        query = query.order_by(Report.created_at.desc())
        
        # Applica paginazione
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    def _get_nesting_data(self, start_date: datetime, end_date: datetime, odl_filter: Optional[str] = None) -> List[NestingResult]:
        """
        Recupera i dati di nesting per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            odl_filter: Filtro opzionale per ODL o PN
            
        Returns:
            Lista di risultati nesting
        """
        query = (
            self.db.query(NestingResult)
            .options(
                joinedload(NestingResult.autoclave),
                joinedload(NestingResult.odl_list).joinedload(ODL.parte),
                joinedload(NestingResult.odl_list).joinedload(ODL.tool)
            )
            .filter(
                between(NestingResult.created_at, start_date, end_date)
            )
        )
        
        # Applica filtro ODL se specificato
        if odl_filter:
            query = query.join(NestingResult.odl_list).join(ODL.parte).filter(
                or_(
                    ODL.id.like(f"%{odl_filter}%"),
                    Parte.part_number.like(f"%{odl_filter}%")
                )
            )
        
        return query.order_by(NestingResult.created_at.desc()).all()
    
    def _get_odl_data(self, start_date: datetime, end_date: datetime, odl_filter: Optional[str] = None) -> List[ODL]:
        """
        Recupera i dati ODL per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            odl_filter: Filtro opzionale per ODL o PN
            
        Returns:
            Lista di ODL
        """
        query = (
            self.db.query(ODL)
            .options(
                joinedload(ODL.parte),
                joinedload(ODL.tool)
            )
            .filter(
                between(ODL.created_at, start_date, end_date)
            )
        )
        
        # Applica filtro ODL se specificato
        if odl_filter:
            query = query.join(ODL.parte).filter(
                or_(
                    ODL.id.like(f"%{odl_filter}%"),
                    Parte.part_number.like(f"%{odl_filter}%")
                )
            )
        
        return query.order_by(ODL.created_at.desc()).all()
    
    def _get_tempo_fasi_data(self, start_date: datetime, end_date: datetime, odl_filter: Optional[str] = None) -> List[TempoFase]:
        """
        Recupera i dati dei tempi fase per il periodo specificato.
        
        Args:
            start_date: Data di inizio
            end_date: Data di fine
            odl_filter: Filtro opzionale per ODL o PN
            
        Returns:
            Lista di tempi fase
        """
        query = (
            self.db.query(TempoFase)
            .options(
                joinedload(TempoFase.odl).joinedload(ODL.parte)
            )
            .filter(
                between(TempoFase.updated_at, start_date, end_date)
            )
        )
        
        # Applica filtro ODL se specificato
        if odl_filter:
            query = query.join(TempoFase.odl).join(ODL.parte).filter(
                or_(
                    TempoFase.odl_id.like(f"%{odl_filter}%"),
                    Parte.part_number.like(f"%{odl_filter}%")
                )
            )
        
        return query.order_by(TempoFase.updated_at.desc()).all()
    
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
    
    async def generate_report(
        self, 
        report_type: ReportTypeEnum,
        range_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_sections: Optional[List[str]] = None,
        odl_filter: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Tuple[str, Report]:
        """
        Genera un report PDF per il periodo specificato.
        
        Args:
            report_type: Tipo di report da generare
            range_type: Tipo di periodo ('giorno', 'settimana', 'mese')
            start_date: Data di inizio personalizzata
            end_date: Data di fine personalizzata
            include_sections: Sezioni opzionali da includere
            odl_filter: Filtro per ODL o PN specifico
            user_id: ID dell'utente per cui generare il report
            
        Returns:
            Tupla con path del file PDF generato e oggetto Report salvato
        """
        # Determina l'intervallo di date
        if start_date and end_date:
            period_start, period_end = start_date, end_date
        elif range_type:
            period_start, period_end = self._get_date_range(range_type)
        else:
            # Default: giorno corrente
            period_start, period_end = self._get_date_range("giorno")
        
        # Genera il nome del file univoco
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"report_{report_type.value}_{timestamp}.pdf"
        file_path = f"{self.reports_dir}/{filename}"
        
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
        
        title = f"Report Manta Group - {report_type.value.capitalize()}"
        story.append(Paragraph(title, title_style))
        
        # Sottotitolo con periodo
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=20,
            alignment=1
        )
        
        period_text = f"Periodo: {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"
        story.append(Paragraph(period_text, subtitle_style))
        
        story.append(Spacer(1, 20))
        
        # Determina quali sezioni includere in base al tipo di report
        sections_to_include = self._get_sections_for_report_type(report_type, include_sections or [])
        
        section_counter = 1
        
        # SEZIONE NESTING (sempre inclusa per alcuni tipi)
        if "nesting" in sections_to_include:
            story.append(Paragraph(f"{section_counter}. Riepilogo Nesting", styles['Heading2']))
            section_counter += 1
            
            nesting_data = self._get_nesting_data(period_start, period_end, odl_filter)
            
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
                story.append(Paragraph(f"{section_counter-1}.1 Layout Visivo Autoclavi", styles['Heading3']))
                layout_drawing = self._create_nesting_layout_drawing(nesting_data)
                story.append(layout_drawing)
                story.append(Spacer(1, 20))
                
            else:
                story.append(Paragraph("Nessun dato di nesting trovato per il periodo specificato.", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # SEZIONE ODL (se richiesta)
        if "odl" in sections_to_include:
            story.append(Paragraph(f"{section_counter}. Dettaglio ODL", styles['Heading2']))
            section_counter += 1
            
            odl_data = self._get_odl_data(period_start, period_end, odl_filter)
            
            if odl_data:
                odl_table_data = [['ID ODL', 'Parte', 'Tool', 'Priorità', 'Status', 'Data Creazione']]
                
                for odl in odl_data:
                    odl_table_data.append([
                        str(odl.id),
                        odl.parte.descrizione_breve if odl.parte else "N/A",
                        odl.tool.codice if odl.tool else "N/A",
                        str(odl.priorita),
                        odl.status,
                        odl.created_at.strftime('%d/%m/%Y')
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
        
        # SEZIONE TEMPI (se richiesta)
        if "tempi" in sections_to_include:
            story.append(Paragraph(f"{section_counter}. Tempi Fase", styles['Heading2']))
            section_counter += 1
            
            tempi_data = self._get_tempo_fasi_data(period_start, period_end, odl_filter)
            
            if tempi_data:
                tempi_table_data = [['Parte', 'Ciclo Cura', 'Tempo (min)', 'Tipo Fase', 'Data Aggiornamento']]
                
                for tempo in tempi_data:
                    tempi_table_data.append([
                        tempo.odl.parte.descrizione_breve if tempo.odl and tempo.odl.parte else "N/A",
                        tempo.fase,
                        str(tempo.durata_minuti) if tempo.durata_minuti else "In corso",
                        "Fase produzione",
                        tempo.updated_at.strftime('%d/%m/%Y')
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
        
        footer_text = f"Report generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} - Manta Group v1.0.0"
        story.append(Paragraph(footer_text, footer_style))
        
        # Genera il PDF
        doc.build(story)
        
        # Salva i metadati nel database
        report_record = self._save_report_to_db(
            filename=filename,
            file_path=file_path,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            include_sections=include_sections,
            user_id=user_id
        )
        
        return file_path, report_record 