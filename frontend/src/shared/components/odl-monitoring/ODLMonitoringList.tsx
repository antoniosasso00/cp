'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Eye,
  Clock,
  Calendar,
  Cpu,
  Package,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { OdlProgressWrapper } from '@/components/ui/OdlProgressWrapper';

interface ODLMonitoringSummary {
  id: number;
  parte_nome: string;
  tool_nome: string;
  status: string;
  priorita: number;
  created_at: string;
  updated_at: string;
  nesting_stato?: string;
  autoclave_nome?: string;
  ultimo_evento?: string;
  ultimo_evento_timestamp?: string;
  tempo_in_stato_corrente?: number;
}

interface ODLMonitoringListProps {
  odlList: ODLMonitoringSummary[];
  loading: boolean;
  error: string | null;
  onSelectOdl: (id: number) => void;
  formatTempo: (minuti?: number) => string;
  getStatusColor: (status: string) => string;
}

export function ODLMonitoringList({ 
  odlList, 
  loading, 
  error, 
  onSelectOdl, 
  formatTempo, 
  getStatusColor 
}: ODLMonitoringListProps) {
  
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

  const getPriorityColor = (priorita: number) => {
    if (priorita >= 5) return 'bg-red-100 text-red-800 border-red-200';
    if (priorita >= 3) return 'bg-orange-100 text-orange-800 border-orange-200';
    if (priorita >= 2) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getEventIcon = (evento?: string) => {
    if (!evento) return <Clock className="h-4 w-4" />;
    
    if (evento.includes('creato')) return <Package className="h-4 w-4 text-blue-500" />;
    if (evento.includes('nesting')) return <Cpu className="h-4 w-4 text-purple-500" />;
    if (evento.includes('cura')) return <AlertCircle className="h-4 w-4 text-orange-500" />;
    if (evento.includes('finito')) return <Clock className="h-4 w-4 text-green-500" />;
    
    return <Clock className="h-4 w-4 text-gray-500" />;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Caricamento ODL in corso...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Errore nel caricamento</h3>
            <p className="text-gray-600">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (odlList.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Nessun ODL trovato</h3>
            <p className="text-gray-600">Non ci sono ODL che corrispondono ai filtri selezionati.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Lista ODL ({odlList.length})
        </CardTitle>
        <CardDescription>
          Ordini di lavorazione con informazioni di monitoraggio in tempo reale
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {odlList.map((odl) => (
            <div
              key={odl.id}
              className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                {/* Informazioni principali */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center space-x-3">
                    <span className="font-semibold text-lg">ODL #{odl.id}</span>
                    <Badge className={getStatusColor(odl.status)}>
                      {odl.status}
                    </Badge>
                    <Badge 
                      variant="outline" 
                      className={getPriorityColor(odl.priorita)}
                    >
                      Priorità {odl.priorita}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Parte:</span>
                      <p className="text-gray-900">{odl.parte_nome}</p>
                    </div>
                    
                    <div>
                      <span className="font-medium text-gray-600">Tool:</span>
                      <p className="text-gray-900">{odl.tool_nome}</p>
                    </div>
                    
                    {odl.autoclave_nome && (
                      <div>
                        <span className="font-medium text-gray-600">Autoclave:</span>
                        <p className="text-gray-900">{odl.autoclave_nome}</p>
                      </div>
                    )}
                    
                    {odl.nesting_stato && (
                      <div>
                        <span className="font-medium text-gray-600">Nesting:</span>
                        <p className="text-gray-900">{odl.nesting_stato}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Azioni */}
                <div className="flex flex-col items-end space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectOdl(odl.id)}
                    className="flex items-center gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    Dettagli
                  </Button>
                </div>
              </div>

              {/* Barra di progresso temporale */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Progresso Temporale:</span>
                    <span className="text-xs text-gray-500">
                      Creato: {formatDate(odl.created_at)}
                    </span>
                  </div>
                  
                  <OdlProgressWrapper 
                    odlId={odl.id}
                    showDetails={false}
                    className="mb-2"
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-gray-400" />
                      <div>
                        <span className="font-medium text-gray-600">Tempo nello stato:</span>
                        <p className="text-gray-900">{formatTempo(odl.tempo_in_stato_corrente)}</p>
                      </div>
                    </div>
                    
                    {odl.ultimo_evento && (
                      <div className="flex items-center space-x-2">
                        {getEventIcon(odl.ultimo_evento)}
                        <div>
                          <span className="font-medium text-gray-600">Ultimo evento:</span>
                          <p className="text-gray-900 capitalize">{odl.ultimo_evento.replace('_', ' ')}</p>
                          {odl.ultimo_evento_timestamp && (
                            <p className="text-xs text-gray-500">
                              {formatDate(odl.ultimo_evento_timestamp)}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Indicatore di ritardo */}
              {odl.tempo_in_stato_corrente && odl.tempo_in_stato_corrente > 1440 && (
                <div className="mt-2 flex items-center space-x-2 text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    ODL in ritardo (oltre 24h nello stesso stato)
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
} 