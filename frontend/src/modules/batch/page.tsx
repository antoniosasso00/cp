'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Eye, 
  Trash2, 
  Plus, 
  RefreshCw, 
  Filter,
  AlertCircle,
  CheckCircle,
  Clock,
  Package,
  Zap
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

// Tipi TypeScript
interface BatchNesting {
  id: string;
  nome: string | null;
  stato: 'draft' | 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato';
  autoclave_id: number;
  numero_nesting: number;
  peso_totale_kg: number;
  efficiency: number;
  created_at: string;
  updated_at: string;
}

interface BatchListResponse {
  batches: BatchNesting[];
  total: number;
}

export default function BatchListPage() {
  const router = useRouter();
  const [batches, setBatches] = useState<BatchNesting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [limit] = useState(20);

  // Funzione per caricare i batch
  const loadBatches = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        skip: (page * limit).toString(),
        limit: limit.toString(),
      });

      if (searchTerm) {
        params.append('nome', searchTerm);
      }

      if (statusFilter !== 'all') {
        params.append('stato', statusFilter);
      }

      const response = await fetch(`/api/v1/batch_nesting/?${params}`);
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }

      const data = await response.json();
      setBatches(data);
    } catch (err) {
      console.error('Errore nel caricamento dei batch:', err);
      setError(err instanceof Error ? err.message : 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  // Carica i batch al mount e quando cambiano i filtri
  useEffect(() => {
    loadBatches();
  }, [page, searchTerm, statusFilter]);

  // Funzione per eliminare un batch
  const handleDelete = async (batchId: string) => {
    if (!confirm('Sei sicuro di voler eliminare questo batch? Questa operazione è irreversibile.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/batch_nesting/${batchId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Errore nell'eliminazione: ${response.status}`);
      }

      // Ricarica la lista
      await loadBatches();
    } catch (err) {
      console.error('Errore nell\'eliminazione del batch:', err);
      alert('Errore nell\'eliminazione del batch: ' + (err instanceof Error ? err.message : 'Errore sconosciuto'));
    }
  };

  // Funzione per ottenere l'icona dello stato
  const getStatusIcon = (stato: string) => {
    switch (stato) {
      case 'draft':
        return <Clock className="w-4 h-4" />;
      case 'sospeso':
        return <AlertCircle className="w-4 h-4" />;
      case 'confermato':
        return <CheckCircle className="w-4 h-4" />;
      case 'loaded':
        return <Package className="w-4 h-4" />;
      case 'cured':
        return <Zap className="w-4 h-4" />;
      case 'terminato':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  // Funzione per ottenere il colore del badge dello stato
  const getStatusColor = (stato: string) => {
    switch (stato) {
      case 'draft':
        return 'bg-gray-500';
      case 'sospeso':
        return 'bg-yellow-500';
      case 'confermato':
        return 'bg-blue-500';
      case 'loaded':
        return 'bg-purple-500';
      case 'cured':
        return 'bg-green-500';
      case 'terminato':
        return 'bg-green-600';
      default:
        return 'bg-gray-500';
    }
  };

  // Funzione per ottenere il colore del badge di efficienza
  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 80) return 'bg-green-500';
    if (efficiency >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  // Funzione per formattare la data
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestione Batch</h1>
          <p className="text-gray-600 mt-1">
            Gestisci i batch di nesting per la produzione
          </p>
        </div>
        <Button 
          onClick={() => router.push('/batch/new')}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuovo Batch
        </Button>
      </div>

      {/* Filtri */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filtri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <Input
                placeholder="Cerca per nome batch..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filtra per stato" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli stati</SelectItem>
                  <SelectItem value="draft">Bozza</SelectItem>
                  <SelectItem value="sospeso">In attesa</SelectItem>
                  <SelectItem value="confermato">Confermato</SelectItem>
                  <SelectItem value="loaded">Caricato</SelectItem>
                  <SelectItem value="cured">Curato</SelectItem>
                  <SelectItem value="terminato">Terminato</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button 
              variant="outline" 
              onClick={loadBatches}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Aggiorna
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Messaggio di errore */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Errore nel caricamento dei batch: {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Tabella dei batch */}
      <Card>
        <CardHeader>
          <CardTitle>Lista Batch ({batches.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin mr-2" />
              Caricamento batch...
            </div>
          ) : batches.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Nessun batch trovato</p>
              <p className="text-sm">Crea il tuo primo batch per iniziare</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Codice</TableHead>
                  <TableHead>Efficienza</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Autoclave</TableHead>
                  <TableHead>ODL</TableHead>
                  <TableHead>Peso (kg)</TableHead>
                  <TableHead>Creato</TableHead>
                  <TableHead className="text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell className="font-medium">
                      {batch.nome || `Batch-${batch.id.slice(0, 8)}`}
                    </TableCell>
                    <TableCell>
                      <Badge className={`${getEfficiencyColor(batch.efficiency)} text-white`}>
                        {batch.efficiency.toFixed(1)}%
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={`${getStatusColor(batch.stato)} text-white flex items-center gap-1 w-fit`}>
                        {getStatusIcon(batch.stato)}
                        {batch.stato}
                      </Badge>
                    </TableCell>
                    <TableCell>#{batch.autoclave_id}</TableCell>
                    <TableCell>{batch.numero_nesting}</TableCell>
                    <TableCell>{batch.peso_totale_kg.toFixed(1)}</TableCell>
                    <TableCell className="text-sm text-gray-600">
                      {formatDate(batch.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/batch/${batch.id}`)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(batch.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          disabled={batch.stato !== 'sospeso' && batch.stato !== 'draft'}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 