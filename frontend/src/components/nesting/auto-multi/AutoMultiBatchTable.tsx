"use client";

import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  AlertCircle, 
  CheckCircle2, 
  Loader2, 
  Play,
  Square,
  Clock,
  Zap,
  BarChart3,
  Package,
  Weight,
  Calendar,
  Settings
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';

interface BatchAutomatico {
  id: number;
  nome: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  peso_totale_kg: number;
  efficienza_media: number;
  data_inizio_pianificata: string | null;
  autoclavi: Array<{
    id: number;
    nome: string;
    efficienza: number;
    stato_nesting: string;
  }>;
  created_at: string;
}

interface AutoMultiBatchTableProps {
  batches: BatchAutomatico[];
  onRefresh: () => void;
  onTerminateBatch: (batchId: number) => void;
  onCreateNew: () => void;
}

export function AutoMultiBatchTable({ 
  batches, 
  onRefresh, 
  onTerminateBatch, 
  onCreateNew 
}: AutoMultiBatchTableProps) {
  const [terminandoBatch, setTerminandoBatch] = useState<number | null>(null);

  // Filtra i batch per stato
  const batchInSospeso = batches.filter(b => b.stato === 'Pronto');
  const batchInEsecuzione = batches.filter(b => b.stato === 'In Esecuzione');
  const batchCompletati = batches.filter(b => b.stato === 'Completato');

  // Handler per terminare un batch
  const handleTerminateBatch = async (batchId: number) => {
    setTerminandoBatch(batchId);
    try {
      await onTerminateBatch(batchId);
    } finally {
      setTerminandoBatch(null);
    }
  };

  // Funzione per ottenere il colore del badge in base al stato
  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'Pronto':
        return 'default';
      case 'In Esecuzione':
        return 'secondary';
      case 'Completato':
        return 'outline';
      default:
        return 'outline';
    }
  };

  // Funzione per formattare la data
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Componente per la riga della tabella
  const BatchRow: React.FC<{ batch: BatchAutomatico }> = ({ batch }) => (
    <TableRow>
      <TableCell>
        <div className="space-y-1">
          <div className="font-medium">{batch.nome}</div>
          <div className="text-xs text-muted-foreground">
            ID: {batch.id}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={getStatoBadgeVariant(batch.stato)}>
          {batch.stato}
        </Badge>
      </TableCell>
      <TableCell className="text-center">
        <div className="flex items-center justify-center gap-1">
          <Package className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{batch.numero_autoclavi}</span>
        </div>
      </TableCell>
      <TableCell className="text-center">
        <div className="flex items-center justify-center gap-1">
          <Settings className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{batch.numero_odl_totali}</span>
        </div>
      </TableCell>
      <TableCell className="text-center">
        <div className="flex items-center justify-center gap-1">
          <Weight className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{batch.peso_totale_kg.toFixed(1)} kg</span>
        </div>
      </TableCell>
      <TableCell className="text-center">
        <div className="flex items-center gap-2">
          <Progress value={batch.efficienza_media} className="flex-1 h-2" />
          <span className="text-sm font-medium w-12">
            {batch.efficienza_media.toFixed(0)}%
          </span>
        </div>
      </TableCell>
      <TableCell className="text-center text-sm">
        {formatDate(batch.data_inizio_pianificata)}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          {batch.stato === 'Pronto' || batch.stato === 'In Esecuzione' ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleTerminateBatch(batch.id)}
              disabled={terminandoBatch === batch.id}
            >
              {terminandoBatch === batch.id ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Terminando...
                </>
              ) : (
                <>
                  <Square className="h-4 w-4 mr-1" />
                  Termina
                </>
              )}
            </Button>
          ) : (
            <Badge variant="outline" className="text-green-600">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Completato
            </Badge>
          )}
        </div>
      </TableCell>
    </TableRow>
  );

  return (
    <div className="space-y-6">
      {/* Header con statistiche */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">In Sospeso</p>
                <p className="text-2xl font-bold text-blue-600">{batchInSospeso.length}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">In Esecuzione</p>
                <p className="text-2xl font-bold text-orange-600">{batchInEsecuzione.length}</p>
              </div>
              <Play className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completati</p>
                <p className="text-2xl font-bold text-green-600">{batchCompletati.length}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Totali</p>
                <p className="text-2xl font-bold">{batches.length}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Azioni principali */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Batch Nesting Automatico</h2>
          <p className="text-muted-foreground">
            Gestisci i batch di nesting automatico multi-autoclave
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRefresh}>
            <Loader2 className="h-4 w-4 mr-2" />
            Aggiorna
          </Button>
          <Button onClick={onCreateNew} className="bg-blue-600 hover:bg-blue-700">
            <Zap className="h-4 w-4 mr-2" />
            Nuovo Nesting Automatico
          </Button>
        </div>
      </div>

      {/* Tabella dei batch */}
      {batches.length === 0 ? (
        <Card>
          <CardContent className="p-8">
            <div className="text-center">
              <Zap className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium mb-2">Nessun batch automatico</h3>
              <p className="text-muted-foreground mb-4">
                Non ci sono batch di nesting automatico. Crea il primo batch per iniziare.
              </p>
              <Button onClick={onCreateNew} className="bg-blue-600 hover:bg-blue-700">
                <Zap className="h-4 w-4 mr-2" />
                Crea Primo Batch
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Batch Attivi e Completati</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome Batch</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead className="text-center">Autoclavi</TableHead>
                  <TableHead className="text-center">ODL</TableHead>
                  <TableHead className="text-center">Peso</TableHead>
                  <TableHead className="text-center">Efficienza</TableHead>
                  <TableHead className="text-center">Data Inizio</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.map((batch) => (
                  <BatchRow key={batch.id} batch={batch} />
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Dettagli autoclavi per batch attivi */}
      {(batchInSospeso.length > 0 || batchInEsecuzione.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Dettagli Autoclavi Attive</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[...batchInSospeso, ...batchInEsecuzione].map((batch) => (
                <div key={batch.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{batch.nome}</h4>
                      <Badge variant={getStatoBadgeVariant(batch.stato)}>
                        {batch.stato}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {batch.autoclavi.length} autoclavi
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {batch.autoclavi.map((autoclave) => (
                      <div key={autoclave.id} className="bg-gray-50 rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{autoclave.nome}</span>
                          <Badge variant="outline">
                            {autoclave.stato_nesting}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Progress value={autoclave.efficienza} className="flex-1 h-2" />
                          <span className="text-xs font-medium">
                            {autoclave.efficienza.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Informazioni aggiuntive */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Nota:</strong> I batch in stato "Pronto" sono pronti per iniziare la cura. 
          I batch "In Esecuzione" sono attualmente in corso. Usa il pulsante "Termina" per 
          completare un ciclo di cura e liberare le autoclavi.
        </AlertDescription>
      </Alert>
    </div>
  );
} 