'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Clock, 
  PlayCircle, 
  CheckCircle, 
  Search, 
  Filter,
  Loader2,
  Eye,
  Package,
  Cpu,
  Info,
  Plus,
  Edit,
  Trash2,
  Settings,
  MoreVertical
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  batchNestingApi, 
  BatchNestingList, 
  BatchNestingResponse
} from '@/lib/api';
import BatchStatusSwitch from './BatchStatusSwitch';
import BatchCRUD from './BatchCRUD';
import { useRouter } from 'next/navigation';
import { useStandardToast } from '@/shared/hooks/use-standard-toast';

import { 
  BATCH_STATUS_COLORS,
  BATCH_STATUS_ICONS
} from '@/shared/lib/constants';
import type { BatchStatus } from '@/shared/types';

// Configurazione icone e colori per stati batch (usando costanti centralizzate)
const STATUS_ICONS = BATCH_STATUS_ICONS;
const STATUS_COLORS = BATCH_STATUS_COLORS;

interface BatchListWithControlsProps {
  /** Titolo del componente */
  title?: string;
  /** Mostra solo batch modificabili */
  editableOnly?: boolean;
  /** Stato iniziale del filtro */
  initialStatusFilter?: 'sospeso' | 'confermato' | 'terminato' | '';
  /** Callback quando un batch viene aggiornato */
  onBatchUpdated?: (batchId: string, newData: any) => void;
  /** Informazioni utente per audit */
  userInfo?: {
    userId: string;
    userRole: string;
  };
}

export default function BatchListWithControls({
  title = 'Batch Nesting',
  editableOnly = false,
  initialStatusFilter = '',
  onBatchUpdated,
  userInfo = { userId: 'utente_frontend', userRole: 'Curing' }
}: BatchListWithControlsProps) {

  const router = useRouter();
  const { toast } = useStandardToast();
  
  // States
  const [batches, setBatches] = useState<BatchNestingList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedBatch, setExpandedBatch] = useState<string | null>(null);
  
  // Filtri
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>(initialStatusFilter);
  const [autoclaveFilter, setAutoclaveFilter] = useState<string>('');

  // ✅ NUOVI STATI PER CRUD
  const [selectedBatch, setSelectedBatch] = useState<BatchNestingResponse | null>(null);
  const [crudMode, setCrudMode] = useState<'create' | 'edit' | 'view' | null>(null);
  const [showCrudDialog, setShowCrudDialog] = useState(false);
  const [deletingBatchId, setDeletingBatchId] = useState<string | null>(null);

  // Carica la lista dei batch
  const loadBatches = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters: any = {
        limit: 50
      };

      if (statusFilter && statusFilter !== '') {
        filters.stato = statusFilter;
      }

      if (autoclaveFilter && autoclaveFilter !== '') {
        filters.autoclave_id = parseInt(autoclaveFilter);
      }

      if (searchTerm.trim()) {
        filters.nome = searchTerm.trim();
      }

      const batchList = await batchNestingApi.getAll(filters);
      
      // Filtra solo batch modificabili se richiesto
      const filteredBatches = editableOnly 
        ? batchList.filter(batch => batch.stato === 'sospeso' || batch.stato === 'confermato')
        : batchList;

      setBatches(filteredBatches);
      console.log(`📦 Caricati ${filteredBatches.length} batch`);

    } catch (err: any) {
      console.error('❌ Errore nel caricamento batch:', err);
      setError(err.message || 'Errore nel caricamento dei batch');
    } finally {
      setLoading(false);
    }
  };

  // Carica i batch all'avvio e quando cambiano i filtri
  useEffect(() => {
    loadBatches();
  }, [searchTerm, statusFilter, autoclaveFilter, editableOnly]);

  // Gestisce il cambio di status di un batch
  const handleBatchStatusChanged = async (batchId: string, newStatus: string) => {
    // Aggiorna la lista locale
    setBatches(prevBatches => 
      prevBatches.map(batch => 
        batch.id === batchId 
          ? { ...batch, stato: newStatus as any }
          : batch
      )
    );

    // Notifica il parent se disponibile
    if (onBatchUpdated) {
      onBatchUpdated(batchId, { stato: newStatus });
    }

    // Ricarica la lista per aggiornare eventuali altri dati
    setTimeout(() => {
      loadBatches();
    }, 1000);
  };

  // Espande/comprime i dettagli di un batch
  const toggleBatchExpansion = (batchId: string) => {
    setExpandedBatch(expandedBatch === batchId ? null : batchId);
  };

  // Naviga ai dettagli del batch
  const viewBatchDetails = (batchId: string) => {
    router.push(`/nesting/result/${batchId}`);
  };

  // ✅ NUOVE FUNZIONI CRUD
  
  // Apre il dialog per creare un nuovo batch
  const openCreateBatch = () => {
    setSelectedBatch(null);
    setCrudMode('create');
    setShowCrudDialog(true);
  };

  // Apre il dialog per modificare un batch
  const openEditBatch = async (batchId: string) => {
    try {
      setLoading(true);
      const batch = await batchNestingApi.getOne(batchId);
      setSelectedBatch(batch);
      setCrudMode('edit');
      setShowCrudDialog(true);
    } catch (err: any) {
      console.error('❌ Errore nel caricamento batch per modifica:', err);
      toast({
        title: "❌ Errore",
        description: "Impossibile caricare il batch per la modifica",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Apre il dialog per visualizzare i dettagli di un batch
  const openViewBatch = async (batchId: string) => {
    try {
      setLoading(true);
      const batch = await batchNestingApi.getOne(batchId);
      setSelectedBatch(batch);
      setCrudMode('view');
      setShowCrudDialog(true);
    } catch (err: any) {
      console.error('❌ Errore nel caricamento batch per visualizzazione:', err);
      toast({
        title: "❌ Errore",
        description: "Impossibile caricare i dettagli del batch",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Elimina un batch
  const deleteBatch = async (batchId: string, batchName?: string) => {
    if (!window.confirm(`Sei sicuro di voler eliminare il batch "${batchName || batchId}"?`)) {
      return;
    }

    try {
      setDeletingBatchId(batchId);
      await batchNestingApi.delete(batchId);
      
      toast({
        title: "✅ Batch eliminato",
        description: `Batch "${batchName || batchId}" eliminato con successo`,
      });

      // Ricarica la lista
      loadBatches();
      
    } catch (err: any) {
      console.error('❌ Errore nell\'eliminazione batch:', err);
      toast({
        title: "❌ Errore",
        description: err.message || "Errore durante l'eliminazione del batch",
        variant: "destructive",
      });
    } finally {
      setDeletingBatchId(null);
    }
  };

  // Callback quando un batch viene salvato tramite CRUD
  const handleBatchSaved = (batch: BatchNestingResponse) => {
    console.log(`✅ Batch ${crudMode === 'create' ? 'creato' : 'aggiornato'}:`, batch);
    
    // Chiudi dialog
    setShowCrudDialog(false);
    setSelectedBatch(null);
    setCrudMode(null);
    
    // Ricarica la lista
    loadBatches();
    
    // Notifica il parent se disponibile
    if (onBatchUpdated) {
      onBatchUpdated(batch.id, batch);
    }
  };

  // Callback quando viene annullata l'operazione CRUD
  const handleCrudCancel = () => {
    setShowCrudDialog(false);
    setSelectedBatch(null);
    setCrudMode(null);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          {title} ({batches.length})
        </CardTitle>
        <div className="flex justify-between items-center mt-2">
          <div className="text-sm text-gray-600">
            Gestisci i batch di nesting con controlli avanzati
          </div>
          <Button onClick={openCreateBatch} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Nuovo Batch
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filtri */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Ricerca per nome */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Cerca per nome batch..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filtro per stato */}
          <Select value={statusFilter || "all"} onValueChange={(value) => setStatusFilter(value === "all" ? "" : value)}>
            <SelectTrigger>
              <SelectValue placeholder="Tutti gli stati" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti gli stati</SelectItem>
              <SelectItem value="sospeso">In Sospeso</SelectItem>
              <SelectItem value="confermato">Confermato</SelectItem>
              <SelectItem value="terminato">Terminato</SelectItem>
            </SelectContent>
          </Select>

          {/* Filtro per autoclave */}
          <Input
            placeholder="Filtro ID Autoclave..."
            value={autoclaveFilter}
            onChange={(e) => setAutoclaveFilter(e.target.value)}
            type="number"
          />
        </div>

        {/* Stato Loading */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Caricamento batch...</span>
          </div>
        )}

        {/* Errori */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Lista Vuota */}
        {!loading && batches.length === 0 && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              {editableOnly 
                ? 'Nessun batch modificabile trovato con i filtri attuali'
                : 'Nessun batch trovato con i filtri attuali'
              }
            </AlertDescription>
          </Alert>
        )}

        {/* Lista Batch */}
        {!loading && batches.length > 0 && (
          <div className="space-y-4">
            {batches.map(batch => {
              const isExpanded = expandedBatch === batch.id;
              const StatusIcon = STATUS_ICONS[batch.stato];
              const statusColor = STATUS_COLORS[batch.stato];

              return (
                <Card key={batch.id} className="border-l-4 border-l-blue-500">
                  <CardContent className="p-4">
                    {/* Header Batch */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <StatusIcon className="h-5 w-5 text-gray-600" />
                        <div>
                          <div className="font-medium">
                            {batch.nome || `Batch ${batch.id.slice(0, 8)}...`}
                          </div>
                          <div className="text-sm text-gray-600">
                            ID: {batch.id.slice(0, 12)}...
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge className={`${statusColor} px-2 py-1`}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {batch.stato.charAt(0).toUpperCase() + batch.stato.slice(1)}
                        </Badge>
                        
                        {/* ✅ NUOVO: Menu dropdown per azioni CRUD */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuLabel>Azioni Batch</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            
                            <DropdownMenuItem onClick={() => openViewBatch(batch.id)}>
                              <Eye className="h-4 w-4 mr-2" />
                              Visualizza Dettagli
                            </DropdownMenuItem>
                            
                            <DropdownMenuItem onClick={() => viewBatchDetails(batch.id)}>
                              <Package className="h-4 w-4 mr-2" />
                              Canvas Nesting
                            </DropdownMenuItem>
                            
                            {/* Modifica solo se in stato sospeso */}
                            {batch.stato === 'sospeso' && (
                              <DropdownMenuItem onClick={() => openEditBatch(batch.id)}>
                                <Edit className="h-4 w-4 mr-2" />
                                Modifica
                              </DropdownMenuItem>
                            )}
                            
                            <DropdownMenuSeparator />
                            
                            {/* Elimina solo se in stato sospeso */}
                            {batch.stato === 'sospeso' && (
                              <DropdownMenuItem 
                                onClick={() => deleteBatch(batch.id, batch.nome)}
                                className="text-red-600 focus:text-red-600"
                                disabled={deletingBatchId === batch.id}
                              >
                                {deletingBatchId === batch.id ? (
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                ) : (
                                  <Trash2 className="h-4 w-4 mr-2" />
                                )}
                                Elimina
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleBatchExpansion(batch.id)}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Statistiche Rapide */}
                    <div className="grid grid-cols-3 gap-4 text-sm text-gray-600 mb-3">
                      <div>
                        <strong>Nesting:</strong> {batch.numero_nesting}
                      </div>
                      <div>
                        <strong>Peso:</strong> {batch.peso_totale_kg.toFixed(1)} kg
                      </div>
                      <div>
                        <strong>Creato:</strong> {new Date(batch.created_at).toLocaleDateString('it-IT')}
                      </div>
                    </div>

                    {/* Controlli Status Espansi */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t">
                        <BatchStatusSwitch
                          batchId={batch.id}
                          currentStatus={batch.stato as any}
                          batchName={batch.nome}
                          odlCount={batch.numero_nesting}
                          totalWeight={batch.peso_totale_kg}
                          onStatusChanged={(newStatus) => handleBatchStatusChanged(batch.id, newStatus)}
                          userInfo={userInfo}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Pulsante Ricarica */}
        <div className="flex justify-center">
          <Button 
            variant="outline" 
            onClick={loadBatches}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Filter className="h-4 w-4 mr-2" />
            )}
            Ricarica Lista
          </Button>
        </div>
      </CardContent>

      {/* ✅ NUOVO: Dialog CRUD per batch */}
      {crudMode && (
        <BatchCRUD
          mode={crudMode}
          editBatch={selectedBatch}
          onSaved={handleBatchSaved}
          onCancel={handleCrudCancel}
          userInfo={userInfo}
          isDialog={true}
          isOpen={showCrudDialog}
          onOpenChange={setShowCrudDialog}
        />
      )}
    </Card>
  );
} 