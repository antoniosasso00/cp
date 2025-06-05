'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  Filter,
  Search,
  RefreshCw
} from 'lucide-react';
import { ODLMonitoringStats } from './ODLMonitoringStats';
import { ODLMonitoringList } from './ODLMonitoringList';
import { ODLMonitoringDetail } from './ODLMonitoringDetail';
import { ODLAlertsPanel } from './ODLAlertsPanel';
import { odlApi } from '@/lib/api';

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

interface ODLStats {
  totale_odl: number;
  per_stato: Record<string, number>;
  in_ritardo: number;
  completati_oggi: number;
  media_tempo_completamento?: number;
}

export function ODLMonitoringDashboard() {
  const [stats, setStats] = useState<ODLStats | null>(null);
  const [odlList, setOdlList] = useState<ODLMonitoringSummary[]>([]);
  const [selectedOdlId, setSelectedOdlId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  
  // Filtri
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [prioritaMin, setPrioritaMin] = useState<string>('');
  const [soloAttivi, setSoloAttivi] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Paginazione
  const [currentPage, setCurrentPage] = useState(0);
  const [limit] = useState(20);

  const fetchStats = async () => {
    try {
      const data = await odlApi.fetchODLMonitoringStats();
      setStats(data);
    } catch (err) {
      console.error('Errore nel caricamento delle statistiche:', err);
      setError('Errore nel caricamento delle statistiche');
    }
  };

  const fetchOdlList = async () => {
    try {
      const params = {
        skip: currentPage * limit,
        limit: limit,
        solo_attivi: soloAttivi,
        ...(statusFilter && { status_filter: statusFilter }),
        ...(prioritaMin && { priorita_min: parseInt(prioritaMin) })
      };
      
      const data = await odlApi.fetchODLMonitoringList(params);
      
      // Filtra per termine di ricerca se presente
      let filteredData = data;
      if (searchTerm) {
        filteredData = data.filter((odl: ODLMonitoringSummary) =>
          (odl.parte_nome && odl.parte_nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (odl.tool_nome && odl.tool_nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (odl.id && odl.id.toString().includes(searchTerm))
        );
      }
      
      setOdlList(filteredData);
      
      // Genera alert basati sui dati ODL
      generateAlerts(filteredData);
    } catch (err) {
      console.error('Errore nel caricamento della lista ODL:', err);
      setError('Errore nel caricamento della lista ODL');
    }
  };

  const generateAlerts = (odlData: ODLMonitoringSummary[]) => {
    const newAlerts: any[] = [];
    
    odlData.forEach((odl) => {
      // Alert per ODL in ritardo (più di 24 ore nello stesso stato)
      if (odl.tempo_in_stato_corrente && odl.tempo_in_stato_corrente > 1440) {
        newAlerts.push({
          id: `ritardo_${odl.id}`,
          odl_id: odl.id,
          tipo: 'ritardo',
          titolo: `ODL #${odl.id} in ritardo`,
          descrizione: `L'ODL è nello stato "${odl.status}" da più di 24 ore`,
          timestamp: new Date().toISOString(),
          parte_nome: odl.parte_nome,
          tool_nome: odl.tool_nome,
          tempo_in_stato: odl.tempo_in_stato_corrente,
          azione_suggerita: 'Verificare lo stato del processo e sbloccare se necessario'
        });
      }
      
      // Alert per ODL bloccati
      if (odl.status === 'Preparazione' && odl.tempo_in_stato_corrente && odl.tempo_in_stato_corrente > 480) {
        newAlerts.push({
          id: `blocco_${odl.id}`,
          odl_id: odl.id,
          tipo: 'blocco',
          titolo: `ODL #${odl.id} bloccato in preparazione`,
          descrizione: `L'ODL è in preparazione da più di 8 ore`,
          timestamp: new Date().toISOString(),
          parte_nome: odl.parte_nome,
          tool_nome: odl.tool_nome,
          tempo_in_stato: odl.tempo_in_stato_corrente,
          azione_suggerita: 'Verificare disponibilità tool e risorse'
        });
      }
      
      // Alert per ODL ad alta priorità in attesa
      if (odl.priorita >= 4 && odl.status === 'Attesa Cura') {
        newAlerts.push({
          id: `priorita_${odl.id}`,
          odl_id: odl.id,
          tipo: 'warning',
          titolo: `ODL #${odl.id} alta priorità in attesa`,
          descrizione: `ODL con priorità ${odl.priorita} in attesa di cura`,
          timestamp: new Date().toISOString(),
          parte_nome: odl.parte_nome,
          tool_nome: odl.tool_nome,
          azione_suggerita: 'Considerare prioritizzazione nella schedulazione'
        });
      }
    });
    
    setAlerts(newAlerts);
  };

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([fetchStats(), fetchOdlList()]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [currentPage, statusFilter, prioritaMin, soloAttivi]);

  useEffect(() => {
    // Debounce per la ricerca
    const timer = setTimeout(() => {
      if (searchTerm !== undefined) {
        fetchOdlList();
      }
    }, 300);
    
    return () => clearTimeout(timer);
  }, [searchTerm]);

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

  const formatTempo = (minuti?: number) => {
    if (!minuti) return 'N/A';
    const ore = Math.floor(minuti / 60);
    const min = minuti % 60;
    return ore > 0 ? `${ore}h ${min}m` : `${min}m`;
  };

  if (selectedOdlId) {
    return (
      <ODLMonitoringDetail 
        odlId={selectedOdlId} 
        onBack={() => setSelectedOdlId(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoraggio ODL</h1>
          <p className="text-gray-600">Tracciabilità completa degli Ordini di Lavorazione</p>
        </div>
        <Button onClick={refreshData} disabled={loading} className="flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      {/* Statistiche */}
      {stats && <ODLMonitoringStats stats={stats} />}

      {/* Alert Panel */}
      {alerts.length > 0 && (
        <ODLAlertsPanel 
          alerts={alerts}
          onViewODL={setSelectedOdlId}
          onDismissAlert={(alertId) => {
            setAlerts(prev => prev.filter(alert => alert.id !== alertId));
          }}
        />
      )}

      {/* Filtri */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri e Ricerca
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Cerca per parte, tool o ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select 
              value={statusFilter || 'all'} 
              onValueChange={(value) => {
                console.log('🔍 Select Status - Value received:', value, 'Type:', typeof value);
                setStatusFilter(value === 'all' ? '' : value);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filtra per stato" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti gli stati</SelectItem>
                <SelectItem value="Preparazione">Preparazione</SelectItem>
                <SelectItem value="Laminazione">Laminazione</SelectItem>
                <SelectItem value="In Coda">In Coda</SelectItem>
                <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                <SelectItem value="Cura">Cura</SelectItem>
                <SelectItem value="Finito">Finito</SelectItem>
              </SelectContent>
            </Select>
            
            <Select 
              value={prioritaMin || 'all'} 
              onValueChange={(value) => {
                console.log('🔍 Select Priority - Value received:', value, 'Type:', typeof value);
                setPrioritaMin(value === 'all' ? '' : value);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Priorità minima" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutte le priorità</SelectItem>
                <SelectItem value="1">Priorità ≥ 1</SelectItem>
                <SelectItem value="2">Priorità ≥ 2</SelectItem>
                <SelectItem value="3">Priorità ≥ 3</SelectItem>
                <SelectItem value="4">Priorità ≥ 4</SelectItem>
                <SelectItem value="5">Priorità ≥ 5</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="solo-attivi"
                checked={soloAttivi}
                onChange={(e) => setSoloAttivi(e.target.checked)}
                className="rounded border-gray-300"
              />
              <label htmlFor="solo-attivi" className="text-sm font-medium">
                Solo ODL attivi
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista ODL */}
      <ODLMonitoringList 
        odlList={odlList}
        loading={loading}
        error={error}
        onSelectOdl={setSelectedOdlId}
        formatTempo={formatTempo}
        getStatusColor={getStatusColor}
      />

      {/* Paginazione */}
      <div className="flex justify-center space-x-2">
        <Button
          variant="outline"
          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0 || loading}
        >
          Precedente
        </Button>
        <span className="flex items-center px-4 py-2 text-sm text-gray-600">
          Pagina {currentPage + 1}
        </span>
        <Button
          variant="outline"
          onClick={() => setCurrentPage(currentPage + 1)}
          disabled={odlList.length < limit || loading}
        >
          Successiva
        </Button>
      </div>
    </div>
  );
} 