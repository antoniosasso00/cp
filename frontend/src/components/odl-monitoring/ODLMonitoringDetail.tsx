'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowLeft,
  Clock,
  Calendar,
  Cpu,
  Package,
  AlertCircle,
  Loader2,
  Activity,
  Settings,
  Flame,
  CheckCircle,
  Plus,
  Grid,
  User,
  FileText
} from 'lucide-react';
import { ODLTimelineEnhanced } from './ODLTimelineEnhanced';

interface ODLLog {
  id: number;
  evento: string;
  stato_precedente?: string;
  stato_nuovo: string;
  descrizione?: string;
  responsabile?: string; // Campo legacy mantenuto per compatibilità dati esistenti
  timestamp: string;
  nesting_stato?: string;
  autoclave_nome?: string;
}

interface ODLMonitoringDetail {
  id: number;
  parte_id: number;
  tool_id: number;
  priorita: number;
  status: string;
  note?: string;
  motivo_blocco?: string;
  created_at: string;
  updated_at: string;
  parte_nome: string;
  parte_categoria?: string;
  tool_nome: string;
  nesting_id?: number;
  nesting_stato?: string;
  nesting_created_at?: string;
  autoclave_id?: number;
  autoclave_nome?: string;
  ciclo_cura_id?: number;
  ciclo_cura_nome?: string;
  schedule_entry_id?: number;
  schedule_start?: string;
  schedule_end?: string;
  schedule_status?: string;
  logs: ODLLog[];
  tempo_in_stato_corrente?: number;
  tempo_totale_produzione?: number;
}

interface ODLMonitoringDetailProps {
  odlId: number;
  onBack: () => void;
}

export function ODLMonitoringDetail({ odlId, onBack }: ODLMonitoringDetailProps) {
  const [odlDetail, setOdlDetail] = useState<ODLMonitoringDetail | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOdlDetail = async () => {
    try {
      const response = await fetch(`/api/v1/odl-monitoring/monitoring/${odlId}`);
      if (!response.ok) throw new Error('Errore nel caricamento dei dettagli ODL');
      const data = await response.json();
      setOdlDetail(data);
    } catch (err) {
      console.error('Errore nel caricamento dei dettagli ODL:', err);
      setError('Errore nel caricamento dei dettagli ODL');
    }
  };

  const fetchTimeline = async () => {
    try {
      const response = await fetch(`/api/v1/odl-monitoring/monitoring/${odlId}/timeline`);
      if (!response.ok) throw new Error('Errore nel caricamento della timeline');
      const data = await response.json();
      setTimeline(data.timeline || []);
    } catch (err) {
      console.error('Errore nel caricamento della timeline:', err);
      // Non bloccare l'interfaccia se la timeline non si carica
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([fetchOdlDetail(), fetchTimeline()]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [odlId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTempo = (minuti?: number) => {
    if (!minuti) return 'N/A';
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return ore > 0 ? `${ore}h ${min}m` : `${min}m`;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'Preparazione': 'bg-blue-100 text-blue-800',
      'Laminazione': 'bg-yellow-100 text-yellow-800',
      'In Coda': 'bg-orange-100 text-orange-800',
      'Attesa Cura': 'bg-purple-100 text-purple-800',
      'Cura': 'bg-red-100 text-red-800',
      'Finito': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getEventIcon = (evento: string, color: string) => {
    const iconClass = `h-4 w-4 text-${color}-500`;
    
    if (evento.includes('creato')) return <Plus className={iconClass} />;
    if (evento.includes('nesting')) return <Grid className={iconClass} />;
    if (evento.includes('cura')) return <Flame className={iconClass} />;
    if (evento.includes('finito')) return <CheckCircle className={iconClass} />;
    if (evento.includes('bloccato')) return <AlertCircle className={iconClass} />;
    
    return <Clock className={iconClass} />;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
        </div>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Caricamento dettagli ODL...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !odlDetail) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
        </div>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Errore nel caricamento</h3>
              <p className="text-gray-600">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">ODL #{odlDetail.id}</h1>
            <p className="text-gray-600">Dettagli completi e tracciabilità</p>
          </div>
        </div>
        <Badge className={getStatusColor(odlDetail.status)}>
          {odlDetail.status}
        </Badge>
      </div>

      {/* Informazioni principali */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Parte</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{odlDetail.parte_nome}</div>
            {odlDetail.parte_categoria && (
              <p className="text-xs text-muted-foreground">
                Categoria: {odlDetail.parte_categoria}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tool</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{odlDetail.tool_nome}</div>
            <p className="text-xs text-muted-foreground">
              Priorità: {odlDetail.priorita}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tempo nello Stato</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatTempo(odlDetail.tempo_in_stato_corrente)}
            </div>
            <p className="text-xs text-muted-foreground">
              Stato corrente: {odlDetail.status}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tempo Totale</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatTempo(odlDetail.tempo_totale_produzione)}
            </div>
            <p className="text-xs text-muted-foreground">
              Dalla creazione
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs per dettagli */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Panoramica</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="logs">Log Dettagliati</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Informazioni processo */}
            <Card>
              <CardHeader>
                <CardTitle>Informazioni Processo</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {odlDetail.autoclave_nome && (
                  <div>
                    <span className="font-medium text-gray-600">Autoclave:</span>
                    <p className="text-gray-900">{odlDetail.autoclave_nome}</p>
                  </div>
                )}
                
                {odlDetail.nesting_stato && (
                  <div>
                    <span className="font-medium text-gray-600">Stato Nesting:</span>
                    <p className="text-gray-900">{odlDetail.nesting_stato}</p>
                  </div>
                )}
                
                {odlDetail.ciclo_cura_nome && (
                  <div>
                    <span className="font-medium text-gray-600">Ciclo di Cura:</span>
                    <p className="text-gray-900">{odlDetail.ciclo_cura_nome}</p>
                  </div>
                )}
                
                {odlDetail.schedule_status && (
                  <div>
                    <span className="font-medium text-gray-600">Stato Schedulazione:</span>
                    <p className="text-gray-900">{odlDetail.schedule_status}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Informazioni temporali */}
            <Card>
              <CardHeader>
                <CardTitle>Informazioni Temporali</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="font-medium text-gray-600">Creato:</span>
                  <p className="text-gray-900">{formatDate(odlDetail.created_at)}</p>
                </div>
                
                <div>
                  <span className="font-medium text-gray-600">Ultimo Aggiornamento:</span>
                  <p className="text-gray-900">{formatDate(odlDetail.updated_at)}</p>
                </div>
                
                {odlDetail.schedule_start && (
                  <div>
                    <span className="font-medium text-gray-600">Inizio Schedulazione:</span>
                    <p className="text-gray-900">{formatDate(odlDetail.schedule_start)}</p>
                  </div>
                )}
                
                {odlDetail.schedule_end && (
                  <div>
                    <span className="font-medium text-gray-600">Fine Schedulazione:</span>
                    <p className="text-gray-900">{formatDate(odlDetail.schedule_end)}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Note e blocchi */}
          {(odlDetail.note || odlDetail.motivo_blocco) && (
            <Card>
              <CardHeader>
                <CardTitle>Note e Informazioni Aggiuntive</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {odlDetail.note && (
                  <div>
                    <span className="font-medium text-gray-600">Note:</span>
                    <p className="text-gray-900">{odlDetail.note}</p>
                  </div>
                )}
                
                {odlDetail.motivo_blocco && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-5 w-5 text-red-500" />
                      <span className="font-medium text-red-800">Motivo Blocco:</span>
                    </div>
                    <p className="text-red-700 mt-1">{odlDetail.motivo_blocco}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <ODLTimelineEnhanced 
            logs={Array.isArray(odlDetail.logs) ? odlDetail.logs : []} 
            currentStatus={odlDetail.status || 'Unknown'}
          />
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Dettagliati</CardTitle>
              <CardDescription>
                Tutti i log di avanzamento dell'ODL con informazioni complete
              </CardDescription>
            </CardHeader>
            <CardContent>
              {Array.isArray(odlDetail.logs) && odlDetail.logs.length > 0 ? (
                <div className="space-y-4">
                  {odlDetail.logs.map((log) => (
                    <div key={log.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{log.evento}</Badge>
                          {log.stato_precedente && (
                            <span className="text-sm text-gray-500">
                              {log.stato_precedente} → {log.stato_nuovo}
                            </span>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">
                          {formatDate(log.timestamp)}
                        </span>
                      </div>
                      
                      {log.descrizione && (
                        <p className="text-sm text-gray-700 mb-2">{log.descrizione}</p>
                      )}
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        {log.responsabile && (
                          <span>Responsabile: {log.responsabile}</span>
                        )}
                        {log.autoclave_nome && (
                          <span>Autoclave: {log.autoclave_nome}</span>
                        )}
                        {log.nesting_stato && (
                          <span>Nesting: {log.nesting_stato}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  Nessun log disponibile
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 