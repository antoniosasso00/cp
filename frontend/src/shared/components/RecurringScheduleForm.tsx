import React, { useState, useEffect } from 'react';
import { scheduleApi, catalogoApi } from '@/lib/api';
import { 
  RecurringScheduleCreateData, 
  ScheduleEntryType 
} from '@/lib/types/schedule';
import { Autoclave } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

interface RecurringScheduleFormProps {
  autoclavi: Autoclave[];
  onSchedulesCreated: () => void;
  onCancel: () => void;
}

interface FormData {
  schedule_type: ScheduleEntryType;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  pieces_per_month: number;
  start_date: string;
  end_date: string;
}

const RecurringScheduleForm: React.FC<RecurringScheduleFormProps> = ({
  autoclavi,
  onSchedulesCreated,
  onCancel
}) => {
  const [formData, setFormData] = useState<FormData>({
    schedule_type: ScheduleEntryType.CATEGORIA,
    autoclave_id: 0,
    pieces_per_month: 10,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // +30 giorni
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categorieList, setCategorieList] = useState<string[]>([]);
  const [sottoCategorieList, setSottoCategorieList] = useState<string[]>([]);
  const [previewInfo, setPreviewInfo] = useState<{
    workingDays: number;
    piecesPerDay: number;
  } | null>(null);

  // Carica le categorie e sotto-categorie dal catalogo
  useEffect(() => {
    const loadCatalogData = async () => {
      try {
        const catalogo = await catalogoApi.getAll();
        
        const categorieSet = new Set(catalogo
          .map(item => item.categoria)
          .filter(Boolean));
        const categorie = Array.from(categorieSet) as string[];
        
        const sottoCategorieSet = new Set(catalogo
          .map(item => item.sotto_categoria)
          .filter(Boolean));
        const sottoCategorie = Array.from(sottoCategorieSet) as string[];
        
        setCategorieList(categorie);
        setSottoCategorieList(sottoCategorie);
      } catch (err) {
        console.error('Errore nel caricamento del catalogo:', err);
      }
    };

    loadCatalogData();
  }, []);

  // Calcola l'anteprima della distribuzione
  useEffect(() => {
    if (formData.start_date && formData.end_date && formData.pieces_per_month > 0) {
      const startDate = new Date(formData.start_date);
      const endDate = new Date(formData.end_date);
      
      let workingDays = 0;
      const currentDate = new Date(startDate);
      
      while (currentDate <= endDate) {
        // Conta solo i giorni feriali (lunedì-venerdì)
        if (currentDate.getDay() >= 1 && currentDate.getDay() <= 5) {
          workingDays++;
        }
        currentDate.setDate(currentDate.getDate() + 1);
      }
      
      const piecesPerDay = workingDays > 0 ? formData.pieces_per_month / workingDays : 0;
      
      setPreviewInfo({
        workingDays,
        piecesPerDay: Math.round(piecesPerDay * 10) / 10
      });
    } else {
      setPreviewInfo(null);
    }
  }, [formData.start_date, formData.end_date, formData.pieces_per_month]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Valida i dati del form
      if (!formData.autoclave_id) {
        throw new Error('Seleziona un\'autoclave');
      }

      if (formData.schedule_type === ScheduleEntryType.CATEGORIA && !formData.categoria) {
        throw new Error('Seleziona una categoria');
      }

      if (formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA && !formData.sotto_categoria) {
        throw new Error('Seleziona una sotto-categoria');
      }

      if (formData.pieces_per_month <= 0) {
        throw new Error('Il numero di pezzi al mese deve essere maggiore di 0');
      }

      if (new Date(formData.start_date) >= new Date(formData.end_date)) {
        throw new Error('La data di fine deve essere successiva alla data di inizio');
      }

      // Prepara i dati per l'API
      const recurringData: RecurringScheduleCreateData = {
        schedule_type: formData.schedule_type,
        autoclave_id: formData.autoclave_id,
        pieces_per_month: formData.pieces_per_month,
        start_date: formData.start_date,
        end_date: formData.end_date,
        created_by: 'UI-User'
      };

      // Aggiungi campi specifici basati sul tipo
      if (formData.schedule_type === ScheduleEntryType.CATEGORIA) {
        recurringData.categoria = formData.categoria;
      } else if (formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA) {
        recurringData.sotto_categoria = formData.sotto_categoria;
      }

      const createdSchedules = await scheduleApi.createRecurring(recurringData);
      
      // Mostra messaggio di successo
      alert(`✅ Creazione completata! ${createdSchedules.length} schedulazioni create per il periodo selezionato.`);
      
      onSchedulesCreated();
    } catch (err: any) {
      setError(err.message || 'Errore durante la creazione delle schedulazioni ricorrenti');
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
          🔄 Schedulazione Ricorrente per Frequenza
        </CardTitle>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Crea automaticamente schedulazioni distribuite nel tempo basate sulla frequenza produttiva
        </p>
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
                <SelectItem value={ScheduleEntryType.CATEGORIA}>Categoria</SelectItem>
                <SelectItem value={ScheduleEntryType.SOTTO_CATEGORIA}>Sotto-categoria</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500 mt-1">
              Le schedulazioni ricorrenti sono disponibili solo per categoria o sotto-categoria
            </p>
          </div>

          {/* Selezione Categoria */}
          {formData.schedule_type === ScheduleEntryType.CATEGORIA && (
            <div>
              <Label className="block text-sm font-medium mb-2">
                Categoria
              </Label>
              <Select
                value={formData.categoria || 'none'}
                onValueChange={(value) => handleFieldChange('categoria', value === 'none' ? '' : value)}
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona una categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Seleziona una categoria</SelectItem>
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

          {/* Selezione Sotto-categoria */}
          {(formData.schedule_type === ScheduleEntryType.CATEGORIA || formData.schedule_type === ScheduleEntryType.SOTTO_CATEGORIA) && (
            <div>
              <Label className="block text-sm font-medium mb-2">
                Sotto-categoria
              </Label>
              <Select
                value={formData.sotto_categoria || 'none'}
                onValueChange={(value) => handleFieldChange('sotto_categoria', value === 'none' ? '' : value)}
                required
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleziona una sotto-categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Seleziona una sotto-categoria</SelectItem>
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
              value={formData.autoclave_id?.toString() || 'none'}
              onValueChange={(value) => handleFieldChange('autoclave_id', value === 'none' ? 0 : Number(value))}
              required
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleziona un'autoclave" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Seleziona un'autoclave</SelectItem>
                {autoclavi && autoclavi.length > 0 ? (
                  autoclavi
                    .filter(autoclave => autoclave.stato === 'DISPONIBILE')
                    .length > 0 ? (
                      autoclavi
                        .filter(autoclave => autoclave.stato === 'DISPONIBILE')
                        .map(autoclave => (
                          <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                            {autoclave.nome} ({autoclave.codice})
                          </SelectItem>
                        ))
                    ) : (
                      <SelectItem value="no-autoclave-disponibile" disabled>
                        Nessuna autoclave disponibile
                      </SelectItem>
                    )
                ) : (
                  <SelectItem value="no-autoclave" disabled>
                    Nessuna autoclave configurata
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>

          {/* Numero di pezzi al mese */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Numero di pezzi da produrre al mese
            </label>
            <input
              type="number"
              min="1"
              max="1000"
              value={formData.pieces_per_month}
              onChange={(e) => handleFieldChange('pieces_per_month', Number(e.target.value))}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Il sistema distribuirà automaticamente la produzione sui giorni lavorativi
            </p>
          </div>

          {/* Periodo */}
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
                Data di Fine
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => handleFieldChange('end_date', e.target.value)}
                className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600"
                required
              />
            </div>
          </div>

          {/* Anteprima della distribuzione */}
          {previewInfo && (
            <div className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-md">
              <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                📊 Anteprima Distribuzione
              </h4>
              <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <p>• <strong>Giorni lavorativi nel periodo:</strong> {previewInfo.workingDays}</p>
                <p>• <strong>Pezzi per giorno lavorativo:</strong> ~{previewInfo.piecesPerDay}</p>
                <p>• <strong>Schedulazioni che verranno create:</strong> {previewInfo.workingDays}</p>
              </div>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                ℹ️ Le schedulazioni saranno create solo per i giorni feriali (lunedì-venerdì)
              </p>
            </div>
          )}

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
              disabled={loading || !previewInfo}
              className="bg-green-600 hover:bg-green-700"
            >
              {loading ? 'Creazione...' : `Crea ${previewInfo?.workingDays || 0} Schedulazioni`}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default RecurringScheduleForm; 