'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Activity, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  BarChart3
} from 'lucide-react';

interface ODLStats {
  totale_odl: number;
  per_stato: Record<string, number>;
  in_ritardo: number;
  completati_oggi: number;
  media_tempo_completamento?: number;
}

interface ODLMonitoringStatsProps {
  stats: ODLStats;
}

export function ODLMonitoringStats({ stats }: ODLMonitoringStatsProps) {
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'Preparazione': 'bg-blue-500',
      'Laminazione': 'bg-yellow-500',
      'In Coda': 'bg-orange-500',
      'Attesa Cura': 'bg-purple-500',
      'Cura': 'bg-red-500',
      'Finito': 'bg-green-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const formatTempo = (ore?: number) => {
    if (!ore) return 'N/A';
    return `${ore.toFixed(1)}h`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Totale ODL */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Totale ODL</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totale_odl}</div>
          <p className="text-xs text-muted-foreground">
            Ordini di lavorazione attivi
          </p>
        </CardContent>
      </Card>

      {/* ODL in Ritardo */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">In Ritardo</CardTitle>
          <AlertTriangle className="h-4 w-4 text-red-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{stats.in_ritardo}</div>
          <p className="text-xs text-muted-foreground">
            ODL oltre le 24h nello stesso stato
          </p>
        </CardContent>
      </Card>

      {/* Completati Oggi */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Completati Oggi</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.completati_oggi}</div>
          <p className="text-xs text-muted-foreground">
            ODL finiti nelle ultime 24h
          </p>
        </CardContent>
      </Card>

      {/* Tempo Medio Completamento */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Tempo Medio</CardTitle>
          <Clock className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {formatTempo(stats.media_tempo_completamento)}
          </div>
          <p className="text-xs text-muted-foreground">
            Tempo medio di completamento
          </p>
        </CardContent>
      </Card>

      {/* Distribuzione per Stato */}
      <Card className="md:col-span-2 lg:col-span-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Distribuzione per Stato
          </CardTitle>
          <CardDescription>
            Numero di ODL per ogni stato del processo produttivo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Barra di progresso visuale */}
            <div className="flex h-8 rounded-lg overflow-hidden bg-gray-100">
              {Object.entries(stats.per_stato).map(([stato, count]) => {
                const percentage = (count / stats.totale_odl) * 100;
                return (
                  <div
                    key={stato}
                    className={`${getStatusColor(stato)} flex items-center justify-center text-white text-xs font-medium`}
                    style={{ width: `${percentage}%` }}
                    title={`${stato}: ${count} ODL (${percentage.toFixed(1)}%)`}
                  >
                    {percentage > 10 && count}
                  </div>
                );
              })}
            </div>

            {/* Legenda con dettagli */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(stats.per_stato).map(([stato, count]) => {
                const percentage = (count / stats.totale_odl) * 100;
                return (
                  <div key={stato} className="flex items-center space-x-2">
                    <div 
                      className={`w-3 h-3 rounded-full ${getStatusColor(stato)}`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {stato}
                      </p>
                      <p className="text-xs text-gray-500">
                        {count} ({percentage.toFixed(1)}%)
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 