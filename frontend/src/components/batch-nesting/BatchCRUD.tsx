'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Save, 
  X, 
  Package,
  Clock,
  PlayCircle,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Settings,
  Calendar
} from 'lucide-react';
import { 
  batchNestingApi, 
  autoclaveApi,
  odlApi,
  BatchNestingResponse, 
  BatchNestingCreate,
  BatchNestingUpdate,
  Autoclave,
  ODLResponse
} from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

// Tipi per le props del componente
interface BatchCRUDProps {
  /** Titolo del componente */
  title?: string;
  /** Batch da modificare (per modalità edit) */
  editBatch?: BatchNestingResponse | null;
  /** Callback quando viene salvato un batch */
  onSaved?: (batch: BatchNestingResponse) => void;
  /** Callback quando viene cancellata l'operazione */
  onCancel?: () => void;
  /** Modalità del componente */
  mode?: 'create' | 'edit' | 'view';
  /** Informazioni utente */
  userInfo?: {
    userId: string;
    userRole: string;
  };
  /** Se true, mostra come dialog */
  isDialog?: boolean;
  /** Controllo apertura dialog */
  isOpen?: boolean;
  /** Callback per chiusura dialog */
  onOpenChange?: (open: boolean) => void;
}

// Componente principale
const BatchCRUD: React.FC<BatchCRUDProps> = ({
  title,
  editBatch,
  onSaved,
  onCancel,
  mode = 'create',
  userInfo = { userId: 'utente_frontend', userRole: 'Curing' },
  isDialog = false,
  isOpen = false,
  onOpenChange
}) => {
  const { toast } = useToast();

  // Stati per il form
  const [formData, setFormData] = useState<BatchNestingCreate>({
    nome: '',
    stato: 'sospeso',
    autoclave_id: 0,
    odl_ids: [],
    note: '',
    creato_da_utente: userInfo.userId,
    creato_da_ruolo: userInfo.userRole
  });

  // Stati per dati aggiuntivi
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([]);
  const [odlDisponibili, setOdlDisponibili] = useState<ODLResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Carica dati quando cambia la modalità o il batch da modificare
  useEffect(() => {
    loadInitialData();
    
    if (mode === 'edit' && editBatch) {
      setFormData({
        nome: editBatch.nome || '',
        stato: editBatch.stato,
        autoclave_id: editBatch.autoclave_id,
        odl_ids: editBatch.odl_ids,
        note: editBatch.note || '',
        creato_da_utente: editBatch.creato_da_utente,
        creato_da_ruolo: editBatch.creato_da_ruolo
      });
    }
  }, [mode, editBatch]);

  // Carica dati iniziali (autoclavi e ODL)
  const loadInitialData = async () => {
    try {
      setLoadingData(true);
      setError(null);

      // Carica autoclavi disponibili
      const autoclaveList = await autoclaveApi.getAll();
      setAutoclavi(autoclaveList.filter(a => a.stato === 'DISPONIBILE'));

      // Carica ODL in attesa di cura
      const odlList = await odlApi.getAll({ 
        status: 'Attesa Cura'
      });
      setOdlDisponibili(odlList);

    } catch (err: any) {
      console.error('❌ Errore caricamento dati:', err);
      setError(err.message || 'Errore nel caricamento dei dati');
    } finally {
      setLoadingData(false);
    }
  };

  // Gestisce i cambiamenti nei campi del form
  const handleFieldChange = (field: keyof BatchNestingCreate, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setError(null);
  };

  // Gestisce la selezione/deselezione degli ODL
  const handleOdlToggle = (odlId: number) => {
    setFormData(prev => ({
      ...prev,
      odl_ids: prev.odl_ids.includes(odlId)
        ? prev.odl_ids.filter(id => id !== odlId)
        : [...prev.odl_ids, odlId]
    }));
  };

  // Valida il form
  const validateForm = (): string | null => {
    if (!formData.nome?.trim()) {
      return 'Il nome del batch è obbligatorio';
    }
    if (!formData.autoclave_id) {
      return 'Seleziona un\'autoclave';
    }
    if (formData.odl_ids.length === 0) {
      return 'Seleziona almeno un ODL';
    }
    return null;
  };

  // Salva il batch (create o update)
  const handleSave = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let savedBatch: BatchNestingResponse;

      if (mode === 'create') {
        console.log('🆕 Creando nuovo batch:', formData);
        savedBatch = await batchNestingApi.create(formData);
        toast({
          title: "✅ Batch creato!",
          description: `Batch "${savedBatch.nome}" creato con successo`,
        });
      } else if (mode === 'edit' && editBatch) {
        console.log('✏️ Aggiornando batch:', editBatch.id, formData);
        const updateData: BatchNestingUpdate = {
          nome: formData.nome,
          odl_ids: formData.odl_ids,
          note: formData.note
        };
        savedBatch = await batchNestingApi.update(editBatch.id, updateData);
        toast({
          title: "✅ Batch aggiornato!",
          description: `Batch "${savedBatch.nome}" aggiornato con successo`,
        });
      } else {
        throw new Error('Modalità non supportata');
      }

      // Notifica il parent
      if (onSaved) {
        onSaved(savedBatch);
      }

      // Chiudi dialog se applicabile
      if (isDialog && onOpenChange) {
        onOpenChange(false);
      }

    } catch (err: any) {
      console.error('❌ Errore nel salvataggio:', err);
      const errorMessage = err.message || 'Errore durante il salvataggio';
      setError(errorMessage);
      toast({
        title: "❌ Errore",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Gestisce la cancellazione
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    if (isDialog && onOpenChange) {
      onOpenChange(false);
    }
  };

  // Renderizza icona stato
  const getStatusIcon = (stato: string) => {
    switch (stato) {
      case 'sospeso': return <Clock className="h-4 w-4" />;
      case 'confermato': return <PlayCircle className="h-4 w-4" />;
      case 'terminato': return <CheckCircle className="h-4 w-4" />;
      default: return <Package className="h-4 w-4" />;
    }
  };

  // Renderizza badge stato
  const getStatusBadge = (stato: string) => {
    const configs = {
      sospeso: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      confermato: 'bg-green-100 text-green-800 border-green-300',
      terminato: 'bg-blue-100 text-blue-800 border-blue-300'
    };
    
    return (
      <Badge className={configs[stato as keyof typeof configs] || 'bg-gray-100 text-gray-800'}>
        {getStatusIcon(stato)}
        <span className="ml-1 capitalize">{stato}</span>
      </Badge>
    );
  };

  // Contenuto del form
  const formContent = (
    <div className="space-y-6">
      {/* Errore generale */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading iniziale */}
      {loadingData && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Caricamento dati...</span>
        </div>
      )}

      {!loadingData && (
        <>
          {/* Informazioni base */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nome batch */}
            <div className="space-y-2">
              <Label htmlFor="nome">Nome Batch *</Label>
              <Input
                id="nome"
                placeholder="Es. Batch_Autoclave1_20250101"
                value={formData.nome}
                onChange={(e) => handleFieldChange('nome', e.target.value)}
                disabled={mode === 'view'}
              />
            </div>

            {/* Stato (solo in visualizzazione/modifica) */}
            {(mode === 'view' || mode === 'edit') && editBatch && (
              <div className="space-y-2">
                <Label>Stato Attuale</Label>
                <div className="flex items-center">
                  {getStatusBadge(editBatch.stato)}
                </div>
              </div>
            )}
          </div>

          {/* Autoclave */}
          <div className="space-y-2">
            <Label htmlFor="autoclave">Autoclave *</Label>
            <Select
              value={formData.autoclave_id?.toString() || ''}
              onValueChange={(value) => handleFieldChange('autoclave_id', parseInt(value))}
              disabled={mode === 'view'}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona un'autoclave..." />
              </SelectTrigger>
              <SelectContent>
                {autoclavi.map((autoclave) => (
                  <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                    {autoclave.nome} ({autoclave.codice}) - {autoclave.lunghezza}x{autoclave.larghezza_piano}mm
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Selezione ODL */}
          <div className="space-y-3">
            <Label>ODL da includere nel batch *</Label>
            <div className="max-h-48 overflow-y-auto border rounded-md p-3">
              {odlDisponibili.length === 0 ? (
                <div className="text-center text-gray-500 py-4">
                  Nessun ODL in attesa di cura disponibile
                </div>
              ) : (
                <div className="space-y-2">
                  {odlDisponibili.map((odl) => (
                    <div 
                      key={odl.id} 
                      className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors ${
                        formData.odl_ids.includes(odl.id) 
                          ? 'bg-blue-50 border-blue-300' 
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => mode !== 'view' && handleOdlToggle(odl.id)}
                    >
                      <div className="flex-1">
                        <div className="font-medium">ODL #{odl.id}</div>
                        <div className="text-sm text-gray-600">
                          {odl.parte.part_number} - {odl.parte.descrizione_breve}
                        </div>
                        <div className="text-xs text-gray-500">
                          Tool: {odl.tool.part_number_tool}
                        </div>
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.odl_ids.includes(odl.id)}
                          onChange={() => mode !== 'view' && handleOdlToggle(odl.id)}
                          disabled={mode === 'view'}
                          className="h-4 w-4 text-blue-600"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="text-sm text-gray-600">
              {formData.odl_ids.length} ODL selezionati
            </div>
          </div>

          {/* Note */}
          <div className="space-y-2">
            <Label htmlFor="note">Note</Label>
            <Textarea
              id="note"
              placeholder="Note aggiuntive sul batch..."
              value={formData.note}
              onChange={(e) => handleFieldChange('note', e.target.value)}
              disabled={mode === 'view'}
              rows={3}
            />
          </div>

          {/* Informazioni aggiuntive (solo in view/edit) */}
          {(mode === 'view' || mode === 'edit') && editBatch && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {editBatch.numero_nesting}
                </div>
                <div className="text-sm text-gray-600">Nesting</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {editBatch.peso_totale_kg.toFixed(1)} kg
                </div>
                <div className="text-sm text-gray-600">Peso Totale</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {editBatch.valvole_totali_utilizzate}
                </div>
                <div className="text-sm text-gray-600">Valvole</div>
              </div>
            </div>
          )}

          {/* Date (solo in view/edit) */}
          {(mode === 'view' || mode === 'edit') && editBatch && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="flex items-center text-sm text-gray-600">
                <Calendar className="h-4 w-4 mr-2" />
                <span>Creato: {new Date(editBatch.created_at).toLocaleString('it-IT')}</span>
              </div>
              {editBatch.data_conferma && (
                <div className="flex items-center text-sm text-gray-600">
                  <PlayCircle className="h-4 w-4 mr-2" />
                  <span>Confermato: {new Date(editBatch.data_conferma).toLocaleString('it-IT')}</span>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );

  // Pulsanti azione
  const actionButtons = mode !== 'view' && !loadingData && (
    <div className="flex gap-2">
      <Button onClick={handleCancel} variant="outline" disabled={loading}>
        <X className="h-4 w-4 mr-2" />
        Annulla
      </Button>
      <Button onClick={handleSave} disabled={loading}>
        {loading ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Save className="h-4 w-4 mr-2" />
        )}
        {mode === 'create' ? 'Crea Batch' : 'Salva Modifiche'}
      </Button>
    </div>
  );

  // Titolo dinamico
  const dynamicTitle = title || {
    create: 'Crea Nuovo Batch',
    edit: `Modifica Batch: ${editBatch?.nome || 'N/A'}`,
    view: `Dettagli Batch: ${editBatch?.nome || 'N/A'}`
  }[mode];

  // Se è un dialog, renderizza all'interno del Dialog
  if (isDialog) {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              {dynamicTitle}
            </DialogTitle>
            <DialogDescription>
              {mode === 'create' && 'Crea un nuovo batch selezionando autoclave e ODL'}
              {mode === 'edit' && 'Modifica le informazioni del batch'}
              {mode === 'view' && 'Visualizza i dettagli completi del batch'}
            </DialogDescription>
          </DialogHeader>
          
          {formContent}
          
          {actionButtons && (
            <DialogFooter>
              {actionButtons}
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    );
  }

  // Renderizza come Card normale
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          {dynamicTitle}
        </CardTitle>
        <CardDescription>
          {mode === 'create' && 'Crea un nuovo batch selezionando autoclave e ODL'}
          {mode === 'edit' && 'Modifica le informazioni del batch'}
          {mode === 'view' && 'Visualizza i dettagli completi del batch'}
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {formContent}
        
        {actionButtons && (
          <div className="mt-6 flex justify-end">
            {actionButtons}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BatchCRUD; 