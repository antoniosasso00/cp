'use client';

import React, { useState, useEffect } from 'react';
import { OdlProgressBar, ODLProgressData } from './OdlProgressBar';
import { OdlTimelineModal } from './OdlTimelineModal';
import { odlApi } from '@/lib/api';
import { AlertCircle, Loader2 } from 'lucide-react';

interface OdlProgressWrapperProps {
  odlId: number;
  showDetails?: boolean;
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // in secondi
}

export function OdlProgressWrapper({ 
  odlId, 
  showDetails = true, 
  className = '',
  autoRefresh = false,
  refreshInterval = 30
}: OdlProgressWrapperProps) {
  const [progressData, setProgressData] = useState<ODLProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timelineOpen, setTimelineOpen] = useState(false);

  // ✅ CORREZIONE: Funzione per caricare i dati di progresso REALI
  const loadProgressData = async () => {
    try {
      setError(null);
      
      console.log(`📊 Caricamento dati progresso per ODL ${odlId}...`);
      
      // 🎯 CORREZIONE: Usa l'endpoint corretto per i dati di progresso reali
      // invece dell'endpoint tempo-fasi che non esiste nel formato aspettato
      const progressData = await odlApi.getProgress(odlId);
      
      console.log(`📊 Dati progresso ricevuti per ODL ${odlId}:`, {
        hasTimeline: progressData.has_timeline_data,
        timestamps: progressData.timestamps?.length || 0,
        status: progressData.status,
        dataType: progressData.has_timeline_data ? 'REALI (da timeline stati)' : 'STIMATI (da fallback)'
      });
      
      setProgressData(progressData);
      
    } catch (err) {
      console.error('❌ Errore nel caricamento dei dati di progresso:', err);
      
      // 🛡️ FALLBACK ROBUSTO: Se l'endpoint principale fallisce, 
      // proviamo a ottenere almeno i dati base dell'ODL
      try {
        console.log(`🔄 Tentativo fallback per ODL ${odlId}...`);
        const odlData = await odlApi.getOne(odlId);
        
        // Crea dati di progresso minimi usando i dati base dell'ODL
        const fallbackProgressData: ODLProgressData = {
          id: odlData.id,
          status: odlData.status,
          created_at: odlData.created_at,
          updated_at: odlData.updated_at,
          timestamps: [], // Nessun timestamp disponibile
          tempo_totale_stimato: undefined,
          has_timeline_data: false
        };
        
        setProgressData(fallbackProgressData);
        console.log(`✅ Usati dati fallback per ODL ${odlId}`);
        
      } catch (fallbackErr) {
        console.error('❌ Anche il fallback è fallito:', fallbackErr);
        setError(
          err instanceof Error 
            ? `Errore caricamento: ${err.message}` 
            : 'Errore di comunicazione con il server'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // Effetto per il caricamento iniziale
  useEffect(() => {
    loadProgressData();
  }, [odlId]);

  // Effetto per l'auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadProgressData();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, odlId]);

  // Gestione apertura timeline
  const handleTimelineClick = () => {
    setTimelineOpen(true);
  };

  // Rendering degli stati di caricamento ed errore
  if (loading) {
    return (
      <div className={`flex items-center justify-center p-4 ${className}`}>
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">Caricamento progresso...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg ${className}`}>
        <AlertCircle className="h-4 w-4 text-red-600" />
        <div className="flex-1">
          <span className="text-sm text-red-700 font-medium">Errore nel caricamento dei dati di progresso</span>
          <p className="text-xs text-red-600 mt-1">{error}</p>
          <button 
            onClick={loadProgressData}
            className="text-xs text-red-600 underline hover:text-red-800 mt-1"
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!progressData) {
    return (
      <div className={`flex items-center gap-2 p-4 bg-amber-50 border border-amber-200 rounded-lg ${className}`}>
        <AlertCircle className="h-4 w-4 text-amber-600" />
        <div className="flex-1">
          <span className="text-sm text-amber-700 font-medium">Dati di progresso non disponibili</span>
          <p className="text-xs text-amber-600 mt-1">
            I dati temporali per questo ODL non sono ancora stati registrati o sono incompleti.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <OdlProgressBar
        odl={progressData}
        showDetails={showDetails}
        className={className}
        onTimelineClick={handleTimelineClick}
      />
      
      <OdlTimelineModal
        odlId={odlId}
        isOpen={timelineOpen}
        onOpenChange={setTimelineOpen}
      />
    </>
  );
} 