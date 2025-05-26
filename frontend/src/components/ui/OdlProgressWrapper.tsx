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

  // Funzione per caricare i dati di progresso
  const loadProgressData = async () => {
    try {
      setError(null);
      const data = await odlApi.getProgress(odlId);
      setProgressData(data);
    } catch (err) {
      console.error('Errore nel caricamento dei dati di progresso:', err);
      setError(err instanceof Error ? err.message : 'Errore nel caricamento');
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
        <span className="text-sm text-red-700">{error}</span>
      </div>
    );
  }

  if (!progressData) {
    return (
      <div className={`flex items-center gap-2 p-4 bg-gray-50 border border-gray-200 rounded-lg ${className}`}>
        <AlertCircle className="h-4 w-4 text-gray-600" />
        <span className="text-sm text-gray-700">Nessun dato di progresso disponibile</span>
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