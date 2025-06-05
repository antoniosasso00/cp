import React, { useState, useEffect } from 'react';
import { scheduleApi, catalogApi } from '@/lib/api';
import { 
  ScheduleEntryCreateData, 
  ScheduleEntryType, 
  ScheduleEntryStatus,
  ProductionTimeEstimate 
} from '@/lib/types/schedule';
import { Autoclave, ODLResponse, CatalogoResponse } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useTheme } from 'next-themes';

interface ScheduleFormProps {
  autoclavi: Autoclave[];
  odlList: ODLResponse[];
  onScheduleCreated: () => void;
  onCancel: () => void;
  initialData?: {
    date?: Date;
    autoclave_id?: number;
  };
}

interface FormData {
  schedule_type: ScheduleEntryType;
  odl_id?: number;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  start_date: string;
  start_time: string;
  end_date?: string;
  end_time?: string;
  note?: string;
}

const ScheduleForm: React.FC<ScheduleFormProps> = ({
  autoclavi,
  odlList,
  onScheduleCreated,
  onCancel,
  initialData
}) => {
  const { theme } = useTheme();
  const [formData, setFormData] = useState<FormData>({
    schedule_type: ScheduleEntryType.ODL_SPECIFICO,
    autoclave_id: initialData?.autoclave_id || 0,
    start_date: initialData?.date ? 
      initialData.date.toISOString().split('T')[0] : 
      new Date().toISOString().split('T')[0],
    start_time: '08:00',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [estimatedEndTime, setEstimatedEndTime] = useState<string | null>(null);
  const [categorieList, setCategorieList] = useState<string[]>([]);
  const [sottoCategorieList, setSottoCategorieList] = useState<string[]>([]);

  // Carica le categorie e sotto-categorie dal catalogo
  useEffect(() => {
    const loadCatalogData = async () => {
      try {
        const catalogo = await catalogApi.fetchCatalogItems();
        
        const categorie = Array.from(new Set(catalogo
          .map(item => item.categoria)
          .filter(Boolean))) as string[];
        
        const sottoCategorie = Array.from(new Set(catalogo
          .map(item => item.sotto_categoria)
          .filter(Boolean))) as string[];
        
        setCategorieList(categorie);
        setSottoCategorieList(sottoCategorie);
      } catch (err) {
        console.error('Errore nel caricamento del catalogo:', err);
      }
    };

    loadCatalogData();
  }, []);

  // Calcola il tempo di fine stimato quando cambiano i dati rilevanti
  useEffect(() => {
    const calculateEstimatedEndTime = async () => {
      if (!formData.start_date || !formData.start_time) return;

      let part_number: string | undefined;
      let categoria: string | undefined;
      let sotto_categoria: string | undefined;

      // Determina i parametri per la stima basati sul tipo di schedulazione
      if (formData.schedule_type === ScheduleEntryType.ODL_SPECIFICO && formData.odl_id) {
        const odl = odlList.find(o => o.id === formData.odl_id);
        if (odl?.parte) {
          part_number = odl.parte.part_number;
          // Qui dovresti recuperare categoria e sotto_categoria dal catalogo
          // Per ora usiamo i valori del form se disponibili
          categoria = formData.categoria;
          sotto_categoria = formData.sotto_categoria;
        }
      } else if (formData.schedule_type === ScheduleEntryType.CATEGORIA) {
        categoria = formData.categoria;
      } else if (formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA) {
        sotto_categoria = formData.sotto_categoria;
      }

      if (part_number || categoria || sotto_categoria) {
        try {
          const estimate = await scheduleApi.estimateProductionTime({
            part_number,
            categoria,
            sotto_categoria
          });

          if (estimate.disponibile && estimate.tempo_stimato_minuti) {
            const startDateTime = new Date(`${formData.start_date}T${formData.start_time}`);
            const endDateTime = new Date(startDateTime.getTime() + estimate.tempo_stimato_minuti * 60000);
            
            setFormData(prev => ({
              ...prev,
              end_date: endDateTime.toISOString().split('T')[0],
              end_time: endDateTime.toTimeString().slice(0, 5)
            }));
            
            setEstimatedEndTime(`${Math.floor(estimate.tempo_stimato_minuti / 60)}h ${estimate.tempo_stimato_minuti % 60}m`);
          } else {
            setEstimatedEndTime(null);
            setFormData(prev => ({
              ...prev,
              end_date: undefined,
              end_time: undefined
            }));
          }
        } catch (err) {
          console.error('Errore nella stima del tempo:', err);
          setEstimatedEndTime(null);
        }
      }
    };

    calculateEstimatedEndTime();
  }, [formData.schedule_type, formData.odl_id, formData.categoria, formData.sotto_categoria, formData.start_date, formData.start_time, odlList]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Valida i dati del form
      if (!formData.autoclave_id) {
        throw new Error('Seleziona un\'autoclave');
      }

      if (formData.schedule_type === ScheduleEntryType.ODL_SPECIFICO && !formData.odl_id) {
        throw new Error('Seleziona un ODL per la schedulazione specifica');
      }

      if (formData.schedule_type === ScheduleEntryType.CATEGORIA && !formData.categoria) {
        throw new Error('Seleziona una categoria');
      }

      if (formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA && !formData.sotto_categoria) {
        throw new Error('Seleziona una sotto-categoria');
      }

      // Prepara i dati per l'API
      const scheduleData: ScheduleEntryCreateData = {
        schedule_type: formData.schedule_type,
        autoclave_id: formData.autoclave_id,
        start_datetime: `${formData.start_date} ${formData.start_time}:00`,
        status: ScheduleEntryStatus.MANUAL,
        created_by: 'UI-User',
        note: formData.note
      };

      // Aggiungi campi specifici basati sul tipo
      if (formData.schedule_type === ScheduleEntryType.ODL_SPECIFICO) {
        scheduleData.odl_id = formData.odl_id;
      } else if (formData.schedule_type === ScheduleEntryType.CATEGORIA) {
        scheduleData.categoria = formData.categoria;
      } else if (formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA) {
        scheduleData.sotto_categoria = formData.sotto_categoria;
      }

      // Aggiungi tempo di fine se calcolato
      if (formData.end_date && formData.end_time) {
        scheduleData.end_datetime = `${formData.end_date} ${formData.end_time}:00`;
      }

      await scheduleApi.create(scheduleData);
      onScheduleCreated();
    } catch (err: any) {
      setError(err.message || 'Errore durante la creazione della schedulazione');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl font-bold">
          🗓️ Nuova Schedulazione
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Tipo di Schedulazione */}
          <div>
            <Label className="block text-sm font-medium mb-2">
              Tipo di Schedulazione
            </Label>
            <Select
              value={formData.schedule_type}
              onValueChange={(value) => handleFieldChange('schedule_type', value as ScheduleEntryType)}
              required
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleziona tipo di schedulazione" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ScheduleEntryType.ODL_SPECIFICO}>ODL Specifico</SelectItem>
                <SelectItem value={ScheduleEntryType.CATEGORIA}>Categoria</SelectItem>
                <SelectItem value={ScheduleEntryType.SOTTO_CATEGORIA}>Sotto-categoria</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Selezione ODL (solo per tipo ODL_SPECIFICO) */}
          {formData.schedule_type === ScheduleEntryType.ODL_SPECIFICO && (
            <div>
              <Label className="block text-sm font-medium mb-2">
                ODL
              </Label>
              <Select
                value={formData.odl_id?.toString() || ''}
                onValueChange={(value) => handleFieldChange('odl_id', value ? Number(value) : undefined)}
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona un ODL" />
                </SelectTrigger>
                <SelectContent>
                  {odlList
                    .filter(odl => odl.status === 'Attesa Cura' && odl.id && odl.parte)
                    .length > 0 ? (
                    odlList
                      .filter(odl => odl.status === 'Attesa Cura' && odl.id && odl.parte)
                      .map(odl => (
                        <SelectItem key={odl.id} value={odl.id.toString()}>
                          ODL #{odl.id} - {odl.parte.descrizione_breve} (Priorità: {odl.priorita})
                        </SelectItem>
                      ))
                  ) : (
                    <SelectItem value="no-odl" disabled>
                      Nessun ODL disponibile in Attesa Cura
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Selezione Categoria (solo per tipo CATEGORIA) */}
          {formData.schedule_type === ScheduleEntryType.CATEGORIA && (
            <div>
              <Label className="block text-sm font-medium mb-2">
                Categoria
              </Label>
              <Select
                value={formData.categoria || ''}
                onValueChange={(value) => handleFieldChange('categoria', value)}
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona una categoria" />
                </SelectTrigger>
                <SelectContent>
                  {categorieList && categorieList.length > 0 ? (
                    categorieList
                      .filter(categoria => categoria && categoria.trim())
                      .map(categoria => (
                        <SelectItem key={categoria} value={categoria}>
                          {categoria}
                        </SelectItem>
                      ))
                  ) : (
                    <SelectItem value="no-categoria" disabled>
                      Nessuna categoria disponibile
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Selezione Sotto-categoria (solo per tipo SOTTO_CATEGORIA) */}
          {formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA && (
            <div>
              <Label className="block text-sm font-medium mb-2">
                Sotto-categoria
              </Label>
              <Select
                value={formData.sotto_categoria || ''}
                onValueChange={(value) => handleFieldChange('sotto_categoria', value)}
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona una sotto-categoria" />
                </SelectTrigger>
                <SelectContent>
                  {sottoCategorieList && sottoCategorieList.length > 0 ? (
                    sottoCategorieList
                      .filter(sottoCategoria => sottoCategoria && sottoCategoria.trim())
                      .map(sottoCategoria => (
                        <SelectItem key={sottoCategoria} value={sottoCategoria}>
                          {sottoCategoria}
                        </SelectItem>
                      ))
                  ) : (
                    <SelectItem value="no-sottocategoria" disabled>
                      Nessuna sotto-categoria disponibile
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Selezione Autoclave */}
          <div>
            <Label className="block text-sm font-medium mb-2">
              Autoclave
            </Label>
            <Select
              value={formData.autoclave_id?.toString() || ''}
              onValueChange={(value) => handleFieldChange('autoclave_id', value ? Number(value) : 0)}
              required
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleziona un'autoclave" />
              </SelectTrigger>
              <SelectContent>
                {autoclavi
                  .filter(autoclave => autoclave.stato === 'DISPONIBILE' && autoclave.id && autoclave.nome)
                  .length > 0 ? (
                  autoclavi
                    .filter(autoclave => autoclave.stato === 'DISPONIBILE' && autoclave.id && autoclave.nome)
                    .map(autoclave => (
                      <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                        {autoclave.nome} ({autoclave.codice})
                      </SelectItem>
                    ))
                ) : (
                  <SelectItem value="no-autoclave" disabled>
                    Nessuna autoclave disponibile
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          {/* Data e Ora di Inizio */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Data di Inizio
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => handleFieldChange('start_date', e.target.value)}
                className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Ora di Inizio
              </label>
              <input
                type="time"
                value={formData.start_time}
                onChange={(e) => handleFieldChange('start_time', e.target.value)}
                className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                required
              />
            </div>
          </div>

          {/* Data e Ora di Fine (se calcolate automaticamente) */}
          {(formData.end_date && formData.end_time) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Data di Fine (Stimata)
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => handleFieldChange('end_date', e.target.value)}
                  className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 bg-green-50 dark:bg-green-900/20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Ora di Fine (Stimata)
                </label>
                <input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) => handleFieldChange('end_time', e.target.value)}
                  className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 bg-green-50 dark:bg-green-900/20"
                />
              </div>
            </div>
          )}

          {/* Indicatore tempo stimato */}
          {estimatedEndTime && (
            <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-md">
              <p className="text-sm text-green-700 dark:text-green-300">
                ⏱️ Tempo stimato di produzione: <strong>{estimatedEndTime}</strong>
                <br />
                <span className="text-xs">Basato sui dati storici di produzione</span>
              </p>
            </div>
          )}

          {/* Note */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Note (opzionale)
            </label>
            <textarea
              value={formData.note || ''}
              onChange={(e) => handleFieldChange('note', e.target.value)}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
              rows={3}
              placeholder="Aggiungi note aggiuntive..."
            />
          </div>

          {/* Pulsanti */}
          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={loading}
            >
              Annulla
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Creazione...' : 'Crea Schedulazione'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default ScheduleForm; 