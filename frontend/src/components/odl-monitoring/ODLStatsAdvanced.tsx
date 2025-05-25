'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  TrendingDown,
  BarChart3,
  Timer,
  Target,
  Zap
} from 'lucide-react';

interface ODLStatsAdvanced {
  totale_odl: number;
  per_stato: Record<string, number>;
  in_ritardo: number;
  completati_oggi: number;
  media_tempo_completamento?: number;
  // Nuove metriche
  efficienza_produzione?: number;
  tempo_medio_per_stato?: Record<string, number>;
  trend_completamenti?: {
    oggi: number;
    ieri: number;
    settimana_scorsa: number;
  };
}

interface ODLStatsAdvancedProps {
  stats: ODLStatsAdvanced;
}

export function ODLStatsAdvanced({ stats }: ODLStatsAdvancedProps) {
  const formatTempo = (minuti?: number) => {
    if (!minuti) return 'N/A';
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return ore > 0 ? `${ore}h ${min}m` : `${min}m`;
  };

  const calcolaPercentualeCompletamento = () => {
    const completati = stats.per_stato['Finito'] || 0;
    return stats.totale_odl > 0 ? Math.round((completati / stats.totale_odl) * 100) : 0;
  };

  const calcolaPercentualeInRitardo = () => {
    return stats.totale_odl > 0 ? Math.round((stats.in_ritardo / stats.totale_odl) * 100) : 0;
  };

  const getStatoColor = (stato: string) => {
    const colors: Record<string, string> = {
      'Preparazione': 'bg-blue-500',
      'Laminazione': 'bg-yellow-500',
      'In Coda': 'bg-orange-500',
      'Attesa Cura': 'bg-purple-500',
      'Cura': 'bg-red-500',
      'Finito': 'bg-green-500'
    };
    return colors[stato] || 'bg-gray-500';
  };

  const calcolaTrendCompletamenti = () => {
    if (!stats.trend_completamenti) return null;
    
    const { oggi, ieri } = stats.trend_completamenti;
    const variazione = oggi - ieri;
    const percentuale = ieri > 0 ? Math.round((variazione / ieri) * 100) : 0;
    
    return {
      variazione,
      percentuale,
      isPositive: variazione >= 0
    };
  };

  const trend = calcolaTrendCompletamenti();
  const percentualeCompletamento = calcolaPercentualeCompletamento();
  const percentualeRitardo = calcolaPercentualeInRitardo();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Statistiche principali */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">ODL Totali</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totale_odl}</div>
          <div className="flex items-center space-x-2 mt-2">
            <Progress value={percentualeCompletamento} className="flex-1" />
            <span className="text-xs text-muted-foreground">
              {percentualeCompletamento}% completati
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Completati Oggi</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.completati_oggi}</div>
          {trend && (
            <div className={`flex items-center space-x-1 mt-2 text-xs ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {trend.isPositive ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span>
                {trend.isPositive ? '+' : ''}{trend.variazione} ({trend.percentuale}%) vs ieri
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">In Ritardo</CardTitle>
          <AlertTriangle className="h-4 w-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">{stats.in_ritardo}</div>
          <div className="flex items-center space-x-2 mt-2">
            <Progress value={percentualeRitardo} className="flex-1" />
            <span className="text-xs text-muted-foreground">
              {percentualeRitardo}% del totale
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Tempo Medio</CardTitle>
          <Timer className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatTempo(stats.media_tempo_completamento)}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Tempo medio di completamento
          </p>
        </CardContent>
      </Card>

      {/* Distribuzione per stato */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Distribuzione per Stato
          </CardTitle>
          <CardDescription>
            Numero di ODL per ogni stato del processo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(stats.per_stato).map(([stato, count]) => {
              const percentuale = stats.totale_odl > 0 ? Math.round((count / stats.totale_odl) * 100) : 0;
              
              return (
                <div key={stato} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getStatoColor(stato)}`}></div>
                    <span className="text-sm font-medium">{stato}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-24">
                      <Progress value={percentuale} className="h-2" />
                    </div>
                    <Badge variant="outline" className="min-w-[60px] justify-center">
                      {count}
                    </Badge>
                    <span className="text-xs text-muted-foreground min-w-[40px]">
                      {percentuale}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Metriche di performance */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Metriche di Performance
          </CardTitle>
          <CardDescription>
            Indicatori di efficienza e produttività
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {/* Efficienza produzione */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Efficienza Produzione</span>
                <Zap className="h-4 w-4 text-yellow-500" />
              </div>
              <div className="text-2xl font-bold">
                {stats.efficienza_produzione ? `${stats.efficienza_produzione}%` : 'N/A'}
              </div>
              <Progress value={stats.efficienza_produzione || 0} className="h-2" />
            </div>

            {/* Tempo medio per stato critico */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tempo in Cura</span>
                <Clock className="h-4 w-4 text-red-500" />
              </div>
              <div className="text-2xl font-bold">
                {formatTempo(stats.tempo_medio_per_stato?.['Cura'])}
              </div>
              <p className="text-xs text-muted-foreground">
                Tempo medio nel ciclo di cura
              </p>
            </div>
          </div>

          {/* Tempi medi per stato */}
          {stats.tempo_medio_per_stato && (
            <div className="mt-6">
              <h4 className="text-sm font-medium mb-3">Tempi Medi per Stato</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(stats.tempo_medio_per_stato).map(([stato, tempo]) => (
                  <div key={stato} className="flex justify-between p-2 bg-gray-50 rounded">
                    <span>{stato}:</span>
                    <span className="font-medium">{formatTempo(tempo)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 