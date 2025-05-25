'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  AlertTriangle, 
  Clock, 
  AlertCircle,
  Bell,
  X,
  ExternalLink,
  Zap
} from 'lucide-react';

interface ODLAlert {
  id: number;
  odl_id: number;
  tipo: 'ritardo' | 'blocco' | 'warning' | 'critico';
  titolo: string;
  descrizione: string;
  timestamp: string;
  parte_nome?: string;
  tool_nome?: string;
  tempo_in_stato?: number;
  azione_suggerita?: string;
}

interface ODLAlertsPanelProps {
  alerts: ODLAlert[];
  onDismissAlert?: (alertId: number) => void;
  onViewODL?: (odlId: number) => void;
}

export function ODLAlertsPanel({ alerts, onDismissAlert, onViewODL }: ODLAlertsPanelProps) {
  const formatTempo = (minuti?: number) => {
    if (!minuti) return 'N/A';
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return ore > 0 ? `${ore}h ${min}m` : `${min}m`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAlertIcon = (tipo: string) => {
    switch (tipo) {
      case 'critico':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'ritardo':
        return <Clock className="h-5 w-5 text-orange-500" />;
      case 'blocco':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <Bell className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAlertColor = (tipo: string) => {
    switch (tipo) {
      case 'critico':
        return 'border-red-200 bg-red-50';
      case 'ritardo':
        return 'border-orange-200 bg-orange-50';
      case 'blocco':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getAlertBadgeColor = (tipo: string) => {
    switch (tipo) {
      case 'critico':
        return 'bg-red-100 text-red-800';
      case 'ritardo':
        return 'bg-orange-100 text-orange-800';
      case 'blocco':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityOrder = (tipo: string) => {
    switch (tipo) {
      case 'critico': return 1;
      case 'blocco': return 2;
      case 'ritardo': return 3;
      case 'warning': return 4;
      default: return 5;
    }
  };

  // Ordina gli alert per priorità
  const sortedAlerts = [...alerts].sort((a, b) => 
    getPriorityOrder(a.tipo) - getPriorityOrder(b.tipo)
  );

  if (alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-green-500" />
            Alert e Notifiche
          </CardTitle>
          <CardDescription>
            Monitoraggio problemi e situazioni critiche
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4">
              <Bell className="h-8 w-8 text-green-500" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Tutto OK!</h3>
            <p className="text-gray-600">Nessun alert attivo al momento</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Alert e Notifiche
            <Badge variant="destructive" className="ml-2">
              {alerts.length}
            </Badge>
          </div>
          <Button variant="outline" size="sm">
            <Bell className="h-4 w-4 mr-2" />
            Gestisci Tutti
          </Button>
        </CardTitle>
        <CardDescription>
          Situazioni che richiedono attenzione immediata
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedAlerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`border rounded-lg p-4 ${getAlertColor(alert.tipo)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  {getAlertIcon(alert.tipo)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="text-sm font-semibold text-gray-900">
                        {alert.titolo}
                      </h4>
                      <Badge className={getAlertBadgeColor(alert.tipo)}>
                        {alert.tipo.toUpperCase()}
                      </Badge>
                    </div>
                    
                    <p className="text-sm text-gray-700 mb-2">
                      {alert.descrizione}
                    </p>
                    
                    {/* Informazioni ODL */}
                    <div className="flex flex-wrap gap-4 text-xs text-gray-600 mb-2">
                      <span>ODL #{alert.odl_id}</span>
                      {alert.parte_nome && <span>Parte: {alert.parte_nome}</span>}
                      {alert.tool_nome && <span>Tool: {alert.tool_nome}</span>}
                      {alert.tempo_in_stato && (
                        <span>Tempo: {formatTempo(alert.tempo_in_stato)}</span>
                      )}
                    </div>
                    
                    {/* Azione suggerita */}
                    {alert.azione_suggerita && (
                      <div className="flex items-center space-x-1 text-xs text-blue-700 bg-blue-100 rounded px-2 py-1 mb-2">
                        <Zap className="h-3 w-3" />
                        <span>{alert.azione_suggerita}</span>
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500">
                      {formatDate(alert.timestamp)}
                    </p>
                  </div>
                </div>
                
                {/* Azioni */}
                <div className="flex items-center space-x-2 ml-4">
                  {onViewODL && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewODL(alert.odl_id)}
                      className="flex items-center space-x-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>Vedi ODL</span>
                    </Button>
                  )}
                  
                  {onDismissAlert && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDismissAlert(alert.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Riepilogo */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Riepilogo Alert</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            {['critico', 'blocco', 'ritardo', 'warning'].map((tipo) => {
              const count = alerts.filter(a => a.tipo === tipo).length;
              return (
                <div key={tipo} className="flex items-center space-x-2">
                  {getAlertIcon(tipo)}
                  <span className="capitalize">{tipo}: {count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 