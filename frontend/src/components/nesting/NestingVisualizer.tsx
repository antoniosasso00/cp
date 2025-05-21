'use client';

import React, { useEffect, useRef } from 'react';
import { AutoclaveLayout, ODLLayout } from '@/lib/types/nesting';

interface NestingVisualizerProps {
    layout: AutoclaveLayout;
    onSelect?: (odlId: number) => void;
    selectedOdlId?: number;
}

// Generiamo colori casuali ma riproducibili basati sull'ID dell'ODL
const getColorForOdl = (odlId: number): string => {
    // Generiamo un hash dall'ID
    const hash = odlId * 137;
    // Generiamo colori vivaci ma non troppo chiari
    const h = hash % 360;
    const s = 60 + (hash % 30);
    const l = 45 + (hash % 20);
    return `hsl(${h}, ${s}%, ${l}%)`;
};

// Funzione di utility per formattare mm² in m²
const formatArea = (area: number): string => {
    return (area / 1000000).toFixed(2);
};

const NestingVisualizer: React.FC<NestingVisualizerProps> = ({ 
    layout, 
    onSelect, 
    selectedOdlId 
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    
    // Costanti per il rendering
    const PADDING = 40;
    const SCALE = 0.1; // 1mm = 0.1px (fattore di scala)
    
    // Disegna il layout dell'autoclave
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        // Ricava le dimensioni dell'autoclave (approssimative)
        const autoWidth = Math.sqrt(layout.area_totale_mm2 / 2);
        const autoLength = autoWidth * 2;
        
        // Configurazione canvas
        const width = autoLength * SCALE + PADDING * 2;
        const height = autoWidth * SCALE + PADDING * 2;
        
        // Imposta le dimensioni del canvas
        canvas.width = width;
        canvas.height = height;
        
        // Pulisci il canvas
        ctx.clearRect(0, 0, width, height);
        
        // Disegna il contorno dell'autoclave
        ctx.fillStyle = '#f0f0f0';
        ctx.strokeStyle = '#888';
        ctx.lineWidth = 2;
        ctx.fillRect(PADDING, PADDING, autoLength * SCALE, autoWidth * SCALE);
        ctx.strokeRect(PADDING, PADDING, autoLength * SCALE, autoWidth * SCALE);
        
        // Disegna i tool
        layout.odl_layout.forEach(odl => {
            const x = odl.x * SCALE + PADDING;
            const y = odl.y * SCALE + PADDING;
            const w = odl.lunghezza * SCALE;
            const h = odl.larghezza * SCALE;
            
            // Determina il colore in base all'ODL
            ctx.fillStyle = getColorForOdl(odl.odl_id);
            
            // Se questo ODL è selezionato, aggiungi un bordo più spesso
            if (selectedOdlId === odl.odl_id) {
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 3;
            } else {
                ctx.strokeStyle = '#444';
                ctx.lineWidth = 1;
            }
            
            // Disegna il rettangolo dell'ODL
            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);
            
            // Aggiungi testo con ID dell'ODL e codice tool se c'è spazio
            if (w > 40 && h > 20) {
                ctx.fillStyle = '#000';
                ctx.font = '10px Arial';
                ctx.fillText(`ODL: ${odl.odl_id}`, x + 5, y + 15);
                ctx.fillText(`${odl.tool_codice}`, x + 5, y + 30);
            }
        });
        
        // Aggiungi gestione click se è fornita la funzione onSelect
        if (onSelect) {
            canvas.onclick = (e) => {
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left - PADDING;
                const y = e.clientY - rect.top - PADDING;
                const clickedX = x / SCALE;
                const clickedY = y / SCALE;
                
                // Trova l'ODL cliccato
                for (const odl of layout.odl_layout) {
                    if (
                        clickedX >= odl.x && 
                        clickedX <= odl.x + odl.lunghezza && 
                        clickedY >= odl.y && 
                        clickedY <= odl.y + odl.larghezza
                    ) {
                        onSelect(odl.odl_id);
                        return;
                    }
                }
                
                // Se nessun ODL è stato cliccato, deseleziona
                onSelect(-1);
            };
        }
    }, [layout, onSelect, selectedOdlId]);
    
    return (
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-4 mt-4" ref={containerRef}>
            <h3 className="text-lg font-semibold mb-2">{layout.autoclave_nome}</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                    <div className="flex justify-between">
                        <span className="font-medium">Efficienza area:</span>
                        <span>{(layout.efficienza_area * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="font-medium">Area utilizzata:</span>
                        <span>{formatArea(layout.area_utilizzata_mm2)} m² / {formatArea(layout.area_totale_mm2)} m²</span>
                    </div>
                </div>
                <div>
                    <div className="flex justify-between">
                        <span className="font-medium">Valvole utilizzate:</span>
                        <span>{layout.valvole_utilizzate} / {layout.valvole_totali}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="font-medium">ODL caricati:</span>
                        <span>{layout.odl_layout.length}</span>
                    </div>
                </div>
            </div>
            
            <div className="overflow-auto border rounded">
                <canvas 
                    ref={canvasRef} 
                    className="mx-auto"
                    style={{ cursor: onSelect ? 'pointer' : 'default' }}
                />
            </div>
            
            <div className="mt-4">
                <h4 className="font-medium mb-2">ODL nel layout:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {layout.odl_layout.map(odl => (
                        <div 
                            key={odl.odl_id}
                            className={`p-2 rounded border ${selectedOdlId === odl.odl_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
                            onClick={() => onSelect && onSelect(odl.odl_id)}
                            style={{ cursor: onSelect ? 'pointer' : 'default' }}
                        >
                            <div className="flex items-center">
                                <div 
                                    className="w-4 h-4 mr-2 rounded-sm" 
                                    style={{ backgroundColor: getColorForOdl(odl.odl_id) }}
                                />
                                <div>
                                    <div className="font-medium">{odl.parte_nome}</div>
                                    <div className="text-xs">
                                        Tool: {odl.tool_codice} | 
                                        ODL: {odl.odl_id} | 
                                        Priorità: {odl.priorita} | 
                                        Valvole: {odl.valvole_utilizzate}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default NestingVisualizer; 