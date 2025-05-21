'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AutoclaveLayout, ODLLayout } from '@/lib/types/nesting';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2, ZoomIn, ZoomOut, Maximize2, Info, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

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
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [scale, setScale] = useState(1);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [hoveredOdl, setHoveredOdl] = useState<ODLLayout | null>(null);
    const [renderProgress, setRenderProgress] = useState(0);
    
    // Costanti per il rendering
    const PADDING = 40;
    const BASE_SCALE = 0.1; // 1mm = 0.1px (fattore di scala base)
    
    // Funzioni di zoom
    const handleZoomIn = () => {
        setScale(prev => Math.min(prev * 1.2, 3));
    };
    
    const handleZoomOut = () => {
        setScale(prev => Math.max(prev / 1.2, 0.5));
    };
    
    const handleResetZoom = () => {
        setScale(1);
        setOffset({ x: 0, y: 0 });
    };
    
    // Gestione del pan
    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    };
    
    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging) return;
        
        const newX = e.clientX - dragStart.x;
        const newY = e.clientY - dragStart.y;
        setOffset({ x: newX, y: newY });
        
        // Aggiorna hoveredOdl durante il movimento
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - PADDING - offset.x) / (BASE_SCALE * scale);
        const y = (e.clientY - rect.top - PADDING - offset.y) / (BASE_SCALE * scale);
        
        const hovered = layout.odl_layout.find(odl => 
            x >= odl.x && 
            x <= odl.x + odl.lunghezza && 
            y >= odl.y && 
            y <= odl.y + odl.larghezza
        );
        
        setHoveredOdl(hovered || null);
    };
    
    const handleMouseUp = () => {
        setIsDragging(false);
    };

    // Gestione errori di rendering
    const handleRenderError = (error: Error) => {
        console.error('Errore di rendering:', error);
        setError(`Errore durante il rendering del layout: ${error.message}`);
        setIsLoading(false);
    };

    // Effetto per il rendering del layout
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            handleRenderError(new Error('Impossibile ottenere il contesto 2D del canvas'));
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            setRenderProgress(0);
            
            // Ricava le dimensioni dell'autoclave (approssimative)
            const autoWidth = Math.sqrt(layout.area_totale_mm2 / 2);
            const autoLength = autoWidth * 2;
            
            // Configurazione canvas
            const width = autoLength * BASE_SCALE * scale + PADDING * 2;
            const height = autoWidth * BASE_SCALE * scale + PADDING * 2;
            
            // Imposta le dimensioni del canvas
            canvas.width = width;
            canvas.height = height;
            setRenderProgress(20);
            
            // Pulisci il canvas
            ctx.clearRect(0, 0, width, height);
            setRenderProgress(40);
            
            // Applica trasformazioni per zoom e pan
            ctx.save();
            ctx.translate(offset.x, offset.y);
            ctx.scale(scale, scale);
            setRenderProgress(60);
            
            // Disegna il contorno dell'autoclave
            ctx.fillStyle = '#f0f0f0';
            ctx.strokeStyle = '#888';
            ctx.lineWidth = 2 / scale;
            ctx.fillRect(PADDING, PADDING, autoLength * BASE_SCALE, autoWidth * BASE_SCALE);
            ctx.strokeRect(PADDING, PADDING, autoLength * BASE_SCALE, autoWidth * BASE_SCALE);
            setRenderProgress(80);
            
            // Disegna i tool
            layout.odl_layout.forEach((odl, index) => {
                const x = odl.x * BASE_SCALE + PADDING;
                const y = odl.y * BASE_SCALE + PADDING;
                const w = odl.lunghezza * BASE_SCALE;
                const h = odl.larghezza * BASE_SCALE;
                
                // Determina il colore in base all'ODL
                ctx.fillStyle = getColorForOdl(odl.odl_id);
                
                // Se questo ODL è selezionato o hovered, aggiungi effetti
                if (selectedOdlId === odl.odl_id) {
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 3 / scale;
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                    ctx.shadowBlur = 5 / scale;
                } else if (hoveredOdl?.odl_id === odl.odl_id) {
                    ctx.strokeStyle = '#666';
                    ctx.lineWidth = 2 / scale;
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
                    ctx.shadowBlur = 3 / scale;
                } else {
                    ctx.strokeStyle = '#444';
                    ctx.lineWidth = 1 / scale;
                    ctx.shadowBlur = 0;
                }
                
                // Disegna il rettangolo dell'ODL
                ctx.fillRect(x, y, w, h);
                ctx.strokeRect(x, y, w, h);
                
                // Aggiungi testo con ID dell'ODL e codice tool se c'è spazio
                if (w > 40 && h > 20) {
                    ctx.fillStyle = '#000';
                    ctx.font = `${12 / scale}px Arial`;
                    ctx.fillText(`ODL: ${odl.odl_id}`, x + 5 / scale, y + 15 / scale);
                    ctx.fillText(`${odl.tool_codice}`, x + 5 / scale, y + 30 / scale);
                }

                // Aggiorna il progresso
                setRenderProgress(80 + (index / layout.odl_layout.length) * 20);
            });
            
            ctx.restore();
            setRenderProgress(100);
            setIsLoading(false);
        } catch (err) {
            handleRenderError(err instanceof Error ? err : new Error('Errore sconosciuto durante il rendering'));
        }
    }, [layout, scale, offset, selectedOdlId, hoveredOdl]);
    
    if (isLoading) {
        return (
            <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-4 mt-4">
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 mt-4">
                <div className="text-red-700">
                    <p className="font-medium">Errore di visualizzazione</p>
                    <p className="text-sm">{error}</p>
                </div>
            </div>
        );
    }
    
    return (
        <div className="relative" ref={containerRef}>
            {/* Controlli zoom */}
            <div className="absolute top-4 right-4 z-10 flex gap-2">
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={handleZoomIn}
                                disabled={scale >= 3}
                            >
                                <ZoomIn className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Ingrandisci</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={handleZoomOut}
                                disabled={scale <= 0.5}
                            >
                                <ZoomOut className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Riduci</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={handleResetZoom}
                            >
                                <Maximize2 className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Ripristina zoom</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </div>

            {/* Canvas e overlay di caricamento/errore */}
            <div className="relative">
                <canvas
                    ref={canvasRef}
                    className={`w-full h-full border rounded-lg ${
                        isDragging ? 'cursor-grabbing' : 'cursor-grab'
                    }`}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={() => setIsDragging(false)}
                    onMouseLeave={() => setIsDragging(false)}
                />

                {/* Overlay di caricamento */}
                {isLoading && (
                    <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center rounded-lg">
                        <Loader2 className="h-8 w-8 animate-spin mb-2" />
                        <div className="text-sm text-gray-600">
                            Rendering in corso... {renderProgress}%
                        </div>
                        <div className="w-48 h-2 bg-gray-200 rounded-full mt-2">
                            <div
                                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                                style={{ width: `${renderProgress}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Overlay di errore */}
                {error && (
                    <div className="absolute inset-0 bg-red-50 border border-red-200 rounded-lg flex flex-col items-center justify-center p-4">
                        <AlertCircle className="h-8 w-8 text-red-500 mb-2" />
                        <div className="text-sm text-red-600 text-center">
                            {error}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            className="mt-4"
                            onClick={() => {
                                setError(null);
                                setIsLoading(true);
                            }}
                        >
                            Riprova
                        </Button>
                    </div>
                )}

                {/* Tooltip per ODL hover */}
                {hoveredOdl && (
                    <div className="absolute bg-white border rounded-lg shadow-lg p-2 text-sm">
                        <div className="font-medium">ODL: {hoveredOdl.odl_id}</div>
                        <div>Tool: {hoveredOdl.tool_codice}</div>
                        <div>Dimensioni: {hoveredOdl.lunghezza} × {hoveredOdl.larghezza} mm</div>
                        <div>Posizione: ({hoveredOdl.x}, {hoveredOdl.y})</div>
                    </div>
                )}
            </div>

            {/* Legenda */}
            <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    <span>Trascina per spostare, usa i controlli per lo zoom</span>
                </div>
                <div>
                    Efficienza: {(layout.efficienza_area * 100).toFixed(1)}%
                </div>
            </div>
        </div>
    );
};

export default NestingVisualizer; 