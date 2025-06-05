'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { 
  Clock, 
  Download, 
  Calendar, 
  User, 
  Activity, 
  AlertCircle,
  CheckCircle,
  Loader2,
  FileText,
  TrendingUp,
  BarChart3
} from 'lucide-react';

// Tipi per i log degli ODL
export interface ODLLogEntry {
  id: number;
  evento: string;
  stato_precedente?: string;
  stato_nuovo: string;
  descrizione?: string;
  responsabile?: string; // Campo legacy mantenuto per compatibilità dati esistenti
  timestamp: string;
  nesting_stato?: string;
  autoclave_nome?: string;
  nesting_id?: number;
  autoclave_id?: number;
  schedule_entry_id?: number;
}

// Tipi per le statistiche temporali
export interface ODLTimelineStats {
  durata_totale_minuti: number;
  durata_per_stato: Record<string, number>;
  tempo_medio_per_transizione: Record<string, number>;
  numero_transizioni: number;
  efficienza_stimata?: number;
}

// Tipi per i dati completi della timeline
export interface ODLTimelineData {
  odl_id: number;
  parte_nome: string;
  tool_nome: string;
  status_corrente: string;
  created_at: string;
  updated_at: string;
  logs: ODLLogEntry[];
  statistiche: ODLTimelineStats;
}

interface OdlTimelineModalProps {
  odlId: number;
  trigger?: React.ReactNode;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function OdlTimelineModal({ 
  odlId, 
  trigger, 
  isOpen, 
  onOpenChange 
}: OdlTimelineModalProps) {
  const [timelineData, setTimelineData] = useState<ODLTimelineData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // Fetch dei dati della timeline
  const fetchTimelineData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Chiamata API per ottenere i dati completi della timeline
      const response = await fetch(`/api/odl-monitoring/monitoring/${odlId}/timeline`);
      if (!response.ok) {
        throw new Error('Errore nel caricamento della timeline');
      }
      
      const data = await response.json();
      setTimelineData(data);
    } catch (err) {
      console.error('Errore nel caricamento della timeline:', err);
      setError(err instanceof Error ? err.message : 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  // Effetto per caricare i dati quando il modal si apre
  useEffect(() => {
    if (isOpen && odlId) {
      fetchTimelineData();
    }
  }, [isOpen, odlId]);

  // Formattazione delle date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Formattazione della durata
  const formatDurata = (minuti: number): string => {
    if (minuti < 60) {
      return `${minuti}m`;
    }
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    if (ore >= 24) {
      const giorni = Math.floor(ore / 24);
      const oreRimanenti = ore % 24;
      return `${giorni}g ${oreRimanenti}h ${min}m`;
    }
    return min > 0 ? `${ore}h ${min}m` : `${ore}h`;
  };

  // Calcola la durata tra due timestamp
  const calcolaDurata = (inizio: string, fine?: string): number => {
    const dataInizio = new Date(inizio);
    const dataFine = fine ? new Date(fine) : new Date();
    return Math.floor((dataFine.getTime() - dataInizio.getTime()) / (1000 * 60));
  };

  // Ottieni l'icona per il tipo di evento
  const getEventIcon = (evento: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'creato': <CheckCircle className="h-4 w-4 text-green-600" />,
      'assegnato_nesting': <Activity className="h-4 w-4 text-blue-600" />,
      'caricato_autoclave': <Activity className="h-4 w-4 text-orange-600" />,
      'avvio_cura': <Activity className="h-4 w-4 text-red-600" />,
      'completato_cura': <CheckCircle className="h-4 w-4 text-green-600" />,
      'finito': <CheckCircle className="h-4 w-4 text-green-600" />,
      'bloccato': <AlertCircle className="h-4 w-4 text-red-600" />,
      'sbloccato': <CheckCircle className="h-4 w-4 text-green-600" />,
      'priorita_modificata': <TrendingUp className="h-4 w-4 text-purple-600" />,
      'note_aggiornate': <FileText className="h-4 w-4 text-gray-600" />
    };
    
    return iconMap[evento] || <Activity className="h-4 w-4 text-gray-600" />;
  };

  // Esportazione in CSV
  const exportToCSV = async () => {
    if (!timelineData) return;
    
    setExporting(true);
    try {
      const csvContent = generateCSVContent(timelineData);
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      
      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `ODL_${odlId}_timeline_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error('Errore nell\'esportazione CSV:', err);
    } finally {
      setExporting(false);
    }
  };

  // Genera il contenuto CSV
  const generateCSVContent = (data: ODLTimelineData): string => {
    const headers = [
      'Timestamp',
      'Evento',
      'Stato Precedente',
      'Stato Nuovo',
      'Durata (minuti)',
      'Responsabile',
      'Autoclave',
      'Nesting',
      'Descrizione'
    ];

    const rows = data.logs.map((log, index) => {
      const nextLog = data.logs[index + 1];
      const durata = nextLog ? calcolaDurata(log.timestamp, nextLog.timestamp) : 0;
      
      return [
        formatDate(log.timestamp),
        log.evento,
        log.stato_precedente || '',
        log.stato_nuovo,
        durata.toString(),
        log.responsabile || '',
        log.autoclave_nome || '',
        log.nesting_stato || '',
        log.descrizione || ''
      ];
    });

    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  };

  const modalContent = (
    <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Storico Temporale ODL #{odlId}
        </DialogTitle>
        <DialogDescription>
          Timeline completa con durate, eventi e statistiche dettagliate
        </DialogDescription>
      </DialogHeader>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Caricamento timeline...</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {timelineData && (
        <div className="space-y-6">
          {/* Header con informazioni generali */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {timelineData.parte_nome}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={exportToCSV}
                    disabled={exporting}
                  >
                    {exporting ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Download className="h-4 w-4 mr-2" />
                    )}
                    Esporta CSV
                  </Button>
                </div>
              </CardTitle>
              <CardDescription>
                Tool: {timelineData.tool_nome} • Stato: {timelineData.status_corrente}
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Statistiche riassuntive */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistiche Temporali
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatDurata(timelineData.statistiche.durata_totale_minuti)}
                  </div>
                  <div className="text-sm text-gray-600">Durata Totale</div>
                </div>
                
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-900">
                    {timelineData.statistiche.numero_transizioni}
                  </div>
                  <div className="text-sm text-blue-600">Transizioni</div>
                </div>
                
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-900">
                    {timelineData.statistiche.efficienza_stimata ? 
                      `${timelineData.statistiche.efficienza_stimata}%` : 'N/A'}
                  </div>
                  <div className="text-sm text-green-600">Efficienza</div>
                </div>
                
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-900">
                    {Object.keys(timelineData.statistiche.durata_per_stato).length}
                  </div>
                  <div className="text-sm text-purple-600">Stati Attraversati</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline degli eventi */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline Eventi</CardTitle>
              <CardDescription>
                Cronologia completa con durate e dettagli
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {timelineData.logs.map((log, index) => {
                  const nextLog = timelineData.logs[index + 1];
                  const durata = nextLog ? calcolaDurata(log.timestamp, nextLog.timestamp) : null;
                  const isLast = index === timelineData.logs.length - 1;
                  
                  return (
                    <div key={log.id} className="relative">
                      {/* Linea di connessione */}
                      {!isLast && (
                        <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-300" />
                      )}
                      
                      <div className="flex items-start gap-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                        {/* Icona evento */}
                        <div className="flex-shrink-0 w-12 h-12 bg-white border-2 border-gray-300 rounded-full flex items-center justify-center">
                          {getEventIcon(log.evento)}
                        </div>
                        
                        {/* Contenuto evento */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{log.evento}</Badge>
                              {log.stato_precedente && (
                                <span className="text-sm text-gray-600">
                                  {log.stato_precedente} → {log.stato_nuovo}
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-500">
                              {formatDate(log.timestamp)}
                            </div>
                          </div>
                          
                          {log.descrizione && (
                            <p className="text-sm text-gray-700 mb-2">{log.descrizione}</p>
                          )}
                          
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            {log.responsabile && (
                              <span className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {log.responsabile}
                              </span>
                            )}
                            {log.autoclave_nome && (
                              <span className="flex items-center gap-1">
                                <Activity className="h-3 w-3" />
                                {log.autoclave_nome}
                              </span>
                            )}
                            {durata !== null && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                Durata: {formatDurata(durata)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Durate per stato */}
          <Card>
            <CardHeader>
              <CardTitle>Durate per Stato</CardTitle>
              <CardDescription>
                Tempo trascorso in ogni stato del processo
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(timelineData.statistiche.durata_per_stato).map(([stato, durata]) => (
                  <div key={stato} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium">{stato}</span>
                    <Badge variant="secondary">{formatDurata(durata)}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </DialogContent>
  );

  if (trigger) {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogTrigger asChild>
          {trigger}
        </DialogTrigger>
        {modalContent}
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      {modalContent}
    </Dialog>
  );
} 