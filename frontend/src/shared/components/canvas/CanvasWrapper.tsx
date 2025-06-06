'use client';

import React, { useState, useEffect, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

// ✅ SOLUZIONE DEFINITIVA: Import dinamico sicuro di tutto react-konva
let KonvaComponents: any = null;

// Componente di loading personalizzato
const CanvasLoadingPlaceholder: React.FC<{ width?: number; height?: number }> = ({ 
  width = 800, 
  height = 600 
}) => (
  <div 
    className="flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg"
    style={{ width, height }}
  >
    <div className="text-center space-y-3">
      <Loader2 className="h-10 w-10 text-blue-500 mx-auto animate-spin" />
      <div>
        <p className="text-sm font-medium text-gray-700">Caricamento Canvas</p>
        <p className="text-xs text-gray-500">Inizializzazione React-Konva...</p>
      </div>
    </div>
  </div>
);

// ✅ Hook per verificare il mounting client-side
const useClientMount = () => {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  return mounted;
};

// ✅ Hook per caricare react-konva in modo sicuro
const useKonvaLoader = () => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useClientMount();

  useEffect(() => {
    if (!mounted) return;
    
    let isMounted = true;
    
    const loadKonva = async () => {
      try {
        if (typeof window === 'undefined') return;
        
        // Carica react-konva solo se siamo nel browser
        const konvaModule = await import('react-konva');
        
        if (isMounted) {
          KonvaComponents = {
            Stage: konvaModule.Stage,
            Layer: konvaModule.Layer,
            Rect: konvaModule.Rect,
            Text: konvaModule.Text,
            Group: konvaModule.Group,
            Line: konvaModule.Line,
            Circle: konvaModule.Circle
          };
          setLoaded(true);
        }
      } catch (err) {
        console.error('Errore nel caricamento di react-konva:', err);
        if (isMounted) {
          setError('Impossibile caricare react-konva');
        }
      }
    };

    // Delay per assicurarsi che il DOM sia pronto
    const timer = setTimeout(loadKonva, 100);
    
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [mounted]);

  return { loaded: loaded && mounted, error };
};

// ✅ Componenti wrapper sicuri per react-konva
const SafeStage: React.FC<any> = ({ children, ...props }) => {
  if (!KonvaComponents?.Stage) return null;
  return React.createElement(KonvaComponents.Stage, props, children);
};

const SafeLayer: React.FC<any> = ({ children, ...props }) => {
  if (!KonvaComponents?.Layer) return null;
  return React.createElement(KonvaComponents.Layer, props, children);
};

const SafeRect: React.FC<any> = (props) => {
  if (!KonvaComponents?.Rect) return null;
  return React.createElement(KonvaComponents.Rect, props);
};

const SafeText: React.FC<any> = (props) => {
  if (!KonvaComponents?.Text) return null;
  return React.createElement(KonvaComponents.Text, props);
};

const SafeGroup: React.FC<any> = ({ children, ...props }) => {
  if (!KonvaComponents?.Group) return null;
  return React.createElement(KonvaComponents.Group, props, children);
};

const SafeLine: React.FC<any> = (props) => {
  if (!KonvaComponents?.Line) return null;
  return React.createElement(KonvaComponents.Line, props);
};

const SafeCircle: React.FC<any> = (props) => {
  if (!KonvaComponents?.Circle) return null;
  return React.createElement(KonvaComponents.Circle, props);
};

// ✅ Wrapper principale per Canvas React-Konva
interface CanvasWrapperProps {
  width: number;
  height: number;
  children: ReactNode;
  className?: string;
  scaleX?: number;
  scaleY?: number;
  x?: number;
  y?: number;
  draggable?: boolean;
  onDragStart?: () => void;
  onDragEnd?: (e: any) => void;
  onMouseMove?: (e: any) => void;
  onMouseLeave?: () => void;
  loadingDelay?: number;
}

const CanvasWrapper = React.forwardRef<any, CanvasWrapperProps>(({
  width,
  height,
  children,
  className = "",
  scaleX = 1,
  scaleY = 1,
  x = 0,
  y = 0,
  draggable = false,
  onDragStart,
  onDragEnd,
  onMouseMove,
  onMouseLeave
}, ref) => {
  const { loaded, error } = useKonvaLoader();
  
  if (error) {
    return (
      <div className={className}>
        <div 
          className="flex items-center justify-center bg-red-50 border border-red-200 rounded-lg"
          style={{ width, height }}
        >
          <div className="text-center space-y-2">
            <div className="text-red-600 font-medium">Errore Canvas</div>
            <div className="text-red-500 text-sm">{error}</div>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              Ricarica Pagina
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  if (!loaded) {
    return (
      <div className={className}>
        <CanvasLoadingPlaceholder width={width} height={height} />
      </div>
    );
  }
  
  return (
    <div className={className}>
      <SafeStage
        ref={ref}
        width={width}
        height={height}
        scaleX={scaleX}
        scaleY={scaleY}
        x={x}
        y={y}
        draggable={draggable}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        onMouseMove={onMouseMove}
        onMouseLeave={onMouseLeave}
      >
        {children}
      </SafeStage>
    </div>
  );
});

CanvasWrapper.displayName = 'CanvasWrapper';

// ✅ Export di tutti i componenti sicuri
export {
  CanvasWrapper,
  SafeLayer as Layer,
  SafeRect as Rect,
  SafeText as Text,
  SafeGroup as Group,
  SafeLine as Line,
  SafeCircle as Circle,
  CanvasLoadingPlaceholder,
  useClientMount,
  useKonvaLoader
};

export default CanvasWrapper; 