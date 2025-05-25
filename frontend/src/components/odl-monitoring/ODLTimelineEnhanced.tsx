'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Clock, 
  Calendar, 
  CheckCircle, 
  AlertCircle, 
  Play, 
  Pause, 
  Settings, 
  Flame,
  Package,
  Grid,
  User,
  ArrowRight
} from 'lucide-react';

interface TimelineEvent {
  id: number;
  evento: string;
  stato_precedente?: string;
  stato_nuovo: string;
  descrizione?: string;
  responsabile?: string;
  timestamp: string;
  nesting_stato?: string;
  autoclave_nome?: string;
  nesting_id?: number;
  autoclave_id?: number;
}

interface ODLTimelineEnhancedProps {
  logs: TimelineEvent[];
  currentStatus: string;
}

export function ODLTimelineEnhanced({ logs, currentStatus }: ODLTimelineEnhancedProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      }),
      time: date.toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit'
      })
    };
  };

  const getEventIcon = (evento: string, isCompleted: boolean) => {
    const iconClass = `h-5 w-5 ${isCompleted ? 'text-green-600' : 'text-blue-600'}`;
    
    switch (evento) {
      case 'creato':
        return <Package className={iconClass} />;
      case 'assegnato_nesting':
        return <Grid className={iconClass} />;
      case 'avvio_cura':
        return <Flame className={iconClass} />;
      case 'finito':
        return <CheckCircle className={iconClass} />;
      case 'bloccato':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'sbloccato':
        return <Play className={iconClass} />;
      default:
        return <Clock className={iconClass} />;
    }
  };

  const getEventColor = (evento: string, isCompleted: boolean) => {
    if (!isCompleted) return 'bg-blue-100 border-blue-300';
    
    switch (evento) {
      case 'creato':
        return 'bg-green-100 border-green-300';
      case 'assegnato_nesting':
        return 'bg-purple-100 border-purple-300';
      case 'avvio_cura':
        return 'bg-orange-100 border-orange-300';
      case 'finito':
        return 'bg-green-100 border-green-300';
      case 'bloccato':
        return 'bg-red-100 border-red-300';
      default:
        return 'bg-gray-100 border-gray-300';
    }
  };

  const getEventTitle = (evento: string) => {
    const titles: Record<string, string> = {
      'creato': 'ODL Creato',
      'assegnato_nesting': 'Assegnato a Nesting',
      'avvio_cura': 'Avvio Ciclo di Cura',
      'finito': 'ODL Completato',
      'bloccato': 'ODL Bloccato',
      'sbloccato': 'ODL Sbloccato',
      'priorita_modificata': 'Priorità Modificata',
      'note_aggiornate': 'Note Aggiornate'
    };
    return titles[evento] || evento.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const isEventCompleted = (index: number) => {
    return index < logs.length - 1 || currentStatus === 'Finito';
  };

  const calculateDuration = (currentIndex: number) => {
    if (currentIndex === logs.length - 1) return null;
    
    const current = new Date(logs[currentIndex].timestamp);
    const next = new Date(logs[currentIndex + 1].timestamp);
    const diffMs = next.getTime() - current.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`;
    }
    return `${diffMinutes}m`;
  };

  if (logs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Timeline Eventi</CardTitle>
          <CardDescription>
            Cronologia degli eventi dell'ODL
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Nessun evento registrato</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Timeline Eventi
        </CardTitle>
        <CardDescription>
          Cronologia dettagliata degli eventi dell'ODL con durate
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Linea verticale */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>
          
          <div className="space-y-6">
            {logs.map((log, index) => {
              const isCompleted = isEventCompleted(index);
              const duration = calculateDuration(index);
              const { date, time } = formatDate(log.timestamp);
              
              return (
                <div key={log.id} className="relative flex items-start space-x-4">
                  {/* Icona evento */}
                  <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 ${getEventColor(log.evento, isCompleted)}`}>
                    {getEventIcon(log.evento, isCompleted)}
                  </div>
                  
                  {/* Contenuto evento */}
                  <div className="flex-1 min-w-0 pb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {getEventTitle(log.evento)}
                      </h3>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{time}</p>
                        <p className="text-xs text-gray-500">{date}</p>
                      </div>
                    </div>
                    
                    {/* Cambio di stato */}
                    {log.stato_precedente && (
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          {log.stato_precedente}
                        </Badge>
                        <ArrowRight className="h-3 w-3 text-gray-400" />
                        <Badge variant="default" className="text-xs">
                          {log.stato_nuovo}
                        </Badge>
                      </div>
                    )}
                    
                    {/* Descrizione */}
                    {log.descrizione && (
                      <p className="text-sm text-gray-600 mb-3">{log.descrizione}</p>
                    )}
                    
                    {/* Informazioni aggiuntive */}
                    <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                      {log.responsabile && (
                        <div className="flex items-center space-x-1">
                          <User className="h-3 w-3" />
                          <span>{log.responsabile}</span>
                        </div>
                      )}
                      
                      {log.autoclave_nome && (
                        <div className="flex items-center space-x-1">
                          <Settings className="h-3 w-3" />
                          <span>Autoclave: {log.autoclave_nome}</span>
                        </div>
                      )}
                      
                      {log.nesting_id && (
                        <div className="flex items-center space-x-1">
                          <Grid className="h-3 w-3" />
                          <span>Nesting #{log.nesting_id}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Durata fino al prossimo evento */}
                    {duration && (
                      <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                        <p className="text-xs text-blue-700">
                          <Clock className="h-3 w-3 inline mr-1" />
                          Durata: {duration}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 