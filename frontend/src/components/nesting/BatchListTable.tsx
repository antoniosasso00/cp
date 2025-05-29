'use client';

import React from 'react';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreHorizontal, 
  Eye, 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  Trash2,
  Calendar,
  Users,
  Weight,
  TrendingUp
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { it } from 'date-fns/locale';

interface Batch {
  id: number;
  nome: string;
  descrizione: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  peso_totale_kg: number;
  efficienza_media: number;
  created_at: string;
  creato_da_ruolo: string;
}

interface BatchListTableProps {
  batches: Batch[];
  onViewDetails: (batchId: number) => void;
  onUpdateStatus: (batchId: number, newStatus: string) => void;
  onDelete: (batchId: number) => void;
  getStatusBadgeVariant: (status: string) => 'default' | 'secondary' | 'destructive' | 'outline';
}

export function BatchListTable({
  batches,
  onViewDetails,
  onUpdateStatus,
  onDelete,
  getStatusBadgeVariant
}: BatchListTableProps) {

  /**
   * Formatta la data in formato relativo (es. "2 ore fa")
   */
  const formatRelativeDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { 
        addSuffix: true, 
        locale: it 
      });
    } catch (error) {
      return 'Data non valida';
    }
  };

  /**
   * Ottiene le azioni disponibili per un batch in base al suo stato
   */
  const getAvailableActions = (batch: Batch) => {
    const actions = [];

    // Visualizza dettagli sempre disponibile
    actions.push({
      label: 'Visualizza Dettagli',
      icon: Eye,
      action: () => onViewDetails(batch.id),
      variant: 'default' as const
    });

    // Azioni basate sullo stato
    switch (batch.stato) {
      case 'Pianificazione':
        actions.push({
          label: 'Avvia Batch',
          icon: Play,
          action: () => onUpdateStatus(batch.id, 'In Esecuzione'),
          variant: 'default' as const
        });
        actions.push({
          label: 'Elimina',
          icon: Trash2,
          action: () => onDelete(batch.id),
          variant: 'destructive' as const
        });
        break;
      
      case 'Pronto':
        actions.push({
          label: 'Avvia Esecuzione',
          icon: Play,
          action: () => onUpdateStatus(batch.id, 'In Esecuzione'),
          variant: 'default' as const
        });
        actions.push({
          label: 'Annulla',
          icon: XCircle,
          action: () => onUpdateStatus(batch.id, 'Annullato'),
          variant: 'destructive' as const
        });
        break;
      
      case 'In Esecuzione':
        actions.push({
          label: 'Pausa',
          icon: Pause,
          action: () => onUpdateStatus(batch.id, 'Pronto'),
          variant: 'default' as const
        });
        actions.push({
          label: 'Completa',
          icon: CheckCircle,
          action: () => onUpdateStatus(batch.id, 'Completato'),
          variant: 'default' as const
        });
        break;
      
      case 'Completato':
      case 'Annullato':
        actions.push({
          label: 'Elimina',
          icon: Trash2,
          action: () => onDelete(batch.id),
          variant: 'destructive' as const
        });
        break;
    }

    return actions;
  };

  if (batches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Users className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Nessun Batch Trovato</h3>
        <p className="text-muted-foreground">
          Non ci sono batch di nesting salvati. Crea il primo batch utilizzando la funzione di preview.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Statistiche rapide */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Totale Batch</span>
          </div>
          <p className="text-2xl font-bold">{batches.length}</p>
        </div>
        
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <Play className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium">In Esecuzione</span>
          </div>
          <p className="text-2xl font-bold text-green-600">
            {batches.filter(b => b.stato === 'In Esecuzione').length}
          </p>
        </div>
        
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium">Completati</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">
            {batches.filter(b => b.stato === 'Completato').length}
          </p>
        </div>
        
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium">Efficienza Media</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">
            {batches.length > 0 
              ? Math.round(batches.reduce((acc, b) => acc + b.efficienza_media, 0) / batches.length)
              : 0
            }%
          </p>
        </div>
      </div>

      {/* Tabella dei batch */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome Batch</TableHead>
              <TableHead>Stato</TableHead>
              <TableHead className="text-center">Autoclavi</TableHead>
              <TableHead className="text-center">ODL</TableHead>
              <TableHead className="text-center">Peso (kg)</TableHead>
              <TableHead className="text-center">Efficienza</TableHead>
              <TableHead className="text-center">Creato</TableHead>
              <TableHead className="text-center">Ruolo</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {batches.map((batch) => (
              <TableRow key={batch.id} className="hover:bg-muted/50">
                <TableCell>
                  <div>
                    <p className="font-medium">{batch.nome}</p>
                    {batch.descrizione && (
                      <p className="text-sm text-muted-foreground truncate max-w-xs">
                        {batch.descrizione}
                      </p>
                    )}
                  </div>
                </TableCell>
                
                <TableCell>
                  <Badge variant={getStatusBadgeVariant(batch.stato)}>
                    {batch.stato}
                  </Badge>
                </TableCell>
                
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{batch.numero_autoclavi}</span>
                  </div>
                </TableCell>
                
                <TableCell className="text-center">
                  <span className="font-medium">{batch.numero_odl_totali}</span>
                </TableCell>
                
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <Weight className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">
                      {batch.peso_totale_kg.toFixed(1)}
                    </span>
                  </div>
                </TableCell>
                
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">
                      {batch.efficienza_media.toFixed(1)}%
                    </span>
                  </div>
                </TableCell>
                
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      {formatRelativeDate(batch.created_at)}
                    </span>
                  </div>
                </TableCell>
                
                <TableCell className="text-center">
                  <Badge variant="outline" className="text-xs">
                    {batch.creato_da_ruolo}
                  </Badge>
                </TableCell>
                
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Apri menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Azioni</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {getAvailableActions(batch).map((action, index) => (
                        <DropdownMenuItem
                          key={index}
                          onClick={action.action}
                          className={action.variant === 'destructive' ? 'text-destructive' : ''}
                        >
                          <action.icon className="mr-2 h-4 w-4" />
                          {action.label}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
} 