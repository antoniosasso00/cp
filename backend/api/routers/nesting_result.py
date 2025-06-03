"""
Nesting Result Router - API per gestione risultati nesting
Versione: v1.4.19-DEMO

Endpoint per:
- Generazione SVG ground-truth con coordinate precise
- Validazione e confronto coordinate
- Debug sistema di rendering
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from api.database import get_db
from models.nesting_result import NestingResult
from models.batch_nesting import BatchNesting
from models.autoclave import Autoclave

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/nesting",
    tags=["Nesting Results v1.4.19"],
    responses={404: {"description": "Nesting result non trovato"}}
)

@router.get("/{nesting_id}/svg", response_class=Response)
def get_nesting_svg_ground_truth(
    nesting_id: int,
    db: Session = Depends(get_db)
):
    """
    🎯 ENDPOINT SVG GROUND-TRUTH v1.4.19-DEMO
    ========================================
    
    Genera SVG con coordinate esatte in mm dei tool posizionati.
    Utilizzato per confronto visivo con rendering Konva.
    
    **Coordinate SVG**: Base matematica precisa dal solver
    **Unità**: millimetri (mm)
    **Stile**: AutoCAD-like con stroke precisi
    
    Returns:
        SVG: Documento SVG con rettangoli tool e autoclave
    """
    logger.info(f"🎯 Generazione SVG ground-truth per nesting {nesting_id}")
    
    # Recupera il nesting result
    nesting = db.query(NestingResult).filter(
        NestingResult.id == nesting_id
    ).first()
    
    if not nesting:
        raise HTTPException(
            status_code=404, 
            detail=f"Nesting result {nesting_id} non trovato"
        )
    
    # Recupera autoclave associata
    autoclave = db.query(Autoclave).filter(
        Autoclave.id == nesting.autoclave_id
    ).first()
    
    if not autoclave:
        raise HTTPException(
            status_code=404,
            detail=f"Autoclave {nesting.autoclave_id} non trovata"
        )
    
    # Estrae le posizioni dei tool dal JSON
    tool_positions = nesting.posizioni_tool or []
    
    if not tool_positions:
        logger.warning(f"🔍 Nesting {nesting_id}: nessuna posizione tool trovata")
    
    # Dimensioni autoclave in mm
    autoclave_width = float(autoclave.lunghezza or 1000)
    autoclave_height = float(autoclave.larghezza_piano or 800)
    
    logger.info(f"🔍 Autoclave dimensioni: {autoclave_width}x{autoclave_height}mm")
    logger.info(f"🔍 Tool positions trovate: {len(tool_positions)}")
    
    # Genera SVG
    svg_content = _generate_svg_ground_truth(
        tool_positions=tool_positions,
        autoclave_width=autoclave_width,
        autoclave_height=autoclave_height,
        autoclave_name=autoclave.nome or f"Autoclave {autoclave.id}"
    )
    
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=300",  # Cache per 5 minuti
            "Content-Disposition": f"inline; filename=nesting_{nesting_id}_ground_truth.svg"
        }
    )

@router.get("/batch/{batch_id}/svg", response_class=Response)
def get_batch_svg_ground_truth(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    🎯 ENDPOINT SVG GROUND-TRUTH PER BATCH v1.4.19-DEMO
    =================================================
    
    Trova il NestingResult associato al BatchNesting e genera SVG con coordinate precise.
    Questo endpoint risolve il mapping batch_id -> nesting_id automaticamente.
    
    Args:
        batch_id: ID del BatchNesting
        
    Returns:
        SVG: Documento SVG con rettangoli tool e autoclave
    """
    logger.info(f"🎯 Generazione SVG ground-truth per batch {batch_id}")
    
    # Trova il batch
    batch = db.query(BatchNesting).filter(
        BatchNesting.id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=404,
            detail=f"Batch {batch_id} non trovato"
        )
    
    # Estrae tool positions dalla configurazione del batch
    configurazione = batch.configurazione_json or {}
    tool_positions = configurazione.get('tool_positions', [])
    
    if not tool_positions:
        logger.warning(f"🔍 Batch {batch_id}: nessuna posizione tool nella configurazione")
        # Genera SVG vuoto con solo autoclave
        tool_positions = []
    
    # Recupera autoclave associata
    autoclave = db.query(Autoclave).filter(
        Autoclave.id == batch.autoclave_id
    ).first()
    
    if not autoclave:
        raise HTTPException(
            status_code=404,
            detail=f"Autoclave {batch.autoclave_id} non trovata per batch {batch_id}"
        )
    
    # Dimensioni autoclave in mm
    autoclave_width = float(autoclave.lunghezza or 1000)
    autoclave_height = float(autoclave.larghezza_piano or 800)
    
    logger.info(f"🔍 Batch {batch_id}: Autoclave {autoclave.nome} ({autoclave_width}x{autoclave_height}mm)")
    logger.info(f"🔍 Tool positions trovate: {len(tool_positions)}")
    
    # Genera SVG
    svg_content = _generate_svg_ground_truth(
        tool_positions=tool_positions,
        autoclave_width=autoclave_width,
        autoclave_height=autoclave_height,
        autoclave_name=f"{autoclave.nome} - Batch {batch.nome or batch_id[:8]}"
    )
    
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=300",  # Cache per 5 minuti
            "Content-Disposition": f"inline; filename=batch_{batch_id[:8]}_ground_truth.svg"
        }
    )

def _generate_svg_ground_truth(
    tool_positions: List[Dict[str, Any]],
    autoclave_width: float,
    autoclave_height: float,
    autoclave_name: str
) -> str:
    """
    Genera SVG ground-truth con coordinate precise dei tool.
    
    Args:
        tool_positions: Lista posizioni tool dal database
        autoclave_width: Larghezza autoclave in mm
        autoclave_height: Altezza autoclave in mm
        autoclave_name: Nome autoclave per il titolo
    
    Returns:
        str: Contenuto SVG completo
    """
    
    # Header SVG con dimensioni in mm
    svg_parts = [
        f'<svg width="{autoclave_width}" height="{autoclave_height}" ',
        f'viewBox="0 0 {autoclave_width} {autoclave_height}" ',
        'xmlns="http://www.w3.org/2000/svg">',
        '',
        f'<!-- SVG Ground-Truth: {autoclave_name} -->',
        f'<!-- Dimensioni: {autoclave_width}x{autoclave_height}mm -->',
        f'<!-- Tool count: {len(tool_positions)} -->',
        '',
        '<defs>',
        '  <style>',
        '    .autoclave { fill: none; stroke: #0af; stroke-width: 2; stroke-dasharray: 5,5; }',
        '    .tool { fill: rgba(0,100,255,0.3); stroke: #00f; stroke-width: 1.5; }',
        '    .tool-rotated { fill: rgba(255,100,0,0.3); stroke: #f80; stroke-width: 1.5; }',
        '    .tool-text { font-family: Arial, sans-serif; font-size: 12px; fill: #333; }',
        '    .title { font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #000; }',
        '  </style>',
        '</defs>',
        '',
        f'<!-- Titolo -->',
        f'<text x="10" y="25" class="title">{autoclave_name} - Ground Truth</text>',
        '',
        '<!-- Bordo autoclave -->',
        f'<rect x="0" y="0" width="{autoclave_width}" height="{autoclave_height}" class="autoclave" />',
        ''
    ]
    
    # Aggiunge i rettangoli dei tool
    for i, tool in enumerate(tool_positions):
        try:
            # Estrae coordinate (assicura che siano float)
            x = float(tool.get('x', 0))
            y = float(tool.get('y', 0))
            width = float(tool.get('width', 50))
            height = float(tool.get('height', 50))
            odl_id = tool.get('odl_id', i)
            rotated = bool(tool.get('rotated', False))
            
            # Classe CSS based su rotazione
            css_class = 'tool-rotated' if rotated else 'tool'
            
            # Commento descrittivo
            rotation_text = " (RUOTATO)" if rotated else ""
            svg_parts.append(f'  <!-- Tool ODL {odl_id}: {width}x{height}mm at ({x},{y}){rotation_text} -->')
            
            # Rettangolo tool
            svg_parts.append(
                f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" class="{css_class}" />'
            )
            
            # Etichetta con ODL ID
            text_x = x + width/2
            text_y = y + height/2 + 4  # Centrato verticalmente
            svg_parts.append(
                f'  <text x="{text_x}" y="{text_y}" class="tool-text" text-anchor="middle">ODL {odl_id}</text>'
            )
            
        except (ValueError, KeyError) as e:
            logger.warning(f"🔍 Errore parsing tool position {i}: {e}")
            continue
    
    # Chiusura SVG
    svg_parts.extend([
        '',
        '<!-- Griglia di riferimento (ogni 100mm) -->',
        '<g stroke="#ccc" stroke-width="0.5" opacity="0.5">',
    ])
    
    # Griglia verticale ogni 100mm
    for x in range(0, int(autoclave_width) + 1, 100):
        svg_parts.append(f'  <line x1="{x}" y1="0" x2="{x}" y2="{autoclave_height}" />')
    
    # Griglia orizzontale ogni 100mm
    for y in range(0, int(autoclave_height) + 1, 100):
        svg_parts.append(f'  <line x1="0" y1="{y}" x2="{autoclave_width}" y2="{y}" />')
    
    svg_parts.extend([
        '</g>',
        '',
        '<!-- Marker origine -->',
        '<polygon points="0,0 15,10 10,15" fill="#666" />',
        '',
        '</svg>'
    ])
    
    return '\n'.join(svg_parts) 