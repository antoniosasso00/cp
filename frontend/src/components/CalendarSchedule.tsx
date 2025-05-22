import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, momentLocalizer, Views, SlotInfo } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { it } from 'date-fns/locale';
import { 
  ScheduleEntry, 
  ScheduleEntryStatus, 
  CalendarEvent, 
  CalendarResource,
  ScheduleEntryCreateData,
  ScheduleEntryUpdateData
} from '@/lib/types/schedule';
import { scheduleApi } from '@/lib/api';
import { Autoclave } from '@/lib/api';
import { ODLResponse } from '@/lib/api';

// Localizzatore italiano per il calendario
const locales = {
  'it': it,
};

// Formato per date e orari
const dateFormat = 'yyyy-MM-dd';
const timeFormat = 'HH:mm';
const dateTimeFormat = 'yyyy-MM-dd HH:mm:ss';

// Funzioni per formattare date
const formatDate = (date: Date) => format(date, dateFormat);
const formatTime = (date: Date) => format(date, timeFormat);
const formatDateTime = (date: Date) => format(date, dateTimeFormat);

// Localizer per il calendario
const localizer = {
  format: (value: Date, formatString: string) => 
    format(value, formatString, { locale: locales['it'] }),
  parse: (value: string, formatString: string) => 
    parse(value, formatString, new Date(), { locale: locales['it'] }),
  startOfWeek: () => startOfWeek(new Date(), { locale: locales['it'] }),
  getDay: (date: Date) => getDay(date),
  locales: locales,
  firstDayOfWeek: 1, // Lunedì come primo giorno della settimana
};

// Interfaccia per le props del componente
interface CalendarScheduleProps {
  autoclavi: Autoclave[];
  odlList: ODLResponse[];
}

// Interfaccia per il form di creazione/modifica
interface ScheduleFormData {
  odl_id: number;
  autoclave_id: number;
  start_date: string;
  start_time: string;
  end_date: string;
  end_time: string;
  status: ScheduleEntryStatus;
  priority_override: boolean;
}

// Componente principale
const CalendarSchedule: React.FC<CalendarScheduleProps> = ({ autoclavi, odlList }) => {
  // State
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [resources, setResources] = useState<CalendarResource[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [formData, setFormData] = useState<ScheduleFormData>({
    odl_id: 0,
    autoclave_id: 0,
    start_date: formatDate(new Date()),
    start_time: '08:00',
    end_date: formatDate(new Date()),
    end_time: '17:00',
    status: ScheduleEntryStatus.MANUAL,
    priority_override: false,
  });
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Inizializza le risorse del calendario (autoclavi)
  useEffect(() => {
    setResources(autoclavi.map(autoclave => ({
      id: autoclave.id,
      title: autoclave.nome,
      autocode: autoclave.codice,
    })));
  }, [autoclavi]);

  // Carica gli eventi al cambio della data selezionata
  useEffect(() => {
    fetchSchedules();
  }, [selectedDate]);

  // Funzione per recuperare le schedulazioni dal server
  const fetchSchedules = async () => {
    try {
      setLoading(true);
      setError(null);
      const schedules = await scheduleApi.getAll({ include_done: false });
      
      // Converte le schedulazioni in eventi per il calendario
      const calendarEvents = schedules.map(schedule => ({
        id: schedule.id,
        title: `ODL #${schedule.odl_id}${schedule.status === ScheduleEntryStatus.MANUAL ? ' (M)' : ''}`,
        start: new Date(schedule.start_datetime),
        end: new Date(schedule.end_datetime),
        resourceId: schedule.autoclave_id,
        isManual: schedule.status === ScheduleEntryStatus.MANUAL,
        scheduleData: schedule
      }));
      
      setEvents(calendarEvents);
    } catch (err) {
      console.error('Errore nel caricamento delle schedulazioni:', err);
      setError('Impossibile caricare le schedulazioni. Riprova più tardi.');
    } finally {
      setLoading(false);
    }
  };

  // Handler per il clic su uno slot vuoto del calendario
  const handleSelectSlot = useCallback(
    (slotInfo: SlotInfo) => {
      // Resetta il form con i dati dello slot selezionato
      setFormData({
        odl_id: 0, // Da selezionare
        autoclave_id: slotInfo.resourceId ? Number(slotInfo.resourceId) : 0,
        start_date: formatDate(slotInfo.start),
        start_time: formatTime(slotInfo.start),
        end_date: formatDate(slotInfo.end),
        end_time: formatTime(slotInfo.end),
        status: ScheduleEntryStatus.MANUAL,
        priority_override: false,
      });
      setEditingScheduleId(null);
      setIsModalOpen(true);
    },
    []
  );

  // Handler per il clic su un evento esistente
  const handleSelectEvent = useCallback(
    (event: CalendarEvent) => {
      const { scheduleData } = event;
      setFormData({
        odl_id: scheduleData.odl_id,
        autoclave_id: scheduleData.autoclave_id,
        start_date: formatDate(new Date(scheduleData.start_datetime)),
        start_time: formatTime(new Date(scheduleData.start_datetime)),
        end_date: formatDate(new Date(scheduleData.end_datetime)),
        end_time: formatTime(new Date(scheduleData.end_datetime)),
        status: scheduleData.status,
        priority_override: scheduleData.priority_override,
      });
      setEditingScheduleId(scheduleData.id);
      setIsModalOpen(true);
    },
    []
  );

  // Handler per il cambio di data/view del calendario
  const handleNavigate = (date: Date) => {
    setSelectedDate(date);
  };

  // Handler per l'invio del form
  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Crea l'oggetto con i dati per l'API
      const startDateTime = `${formData.start_date} ${formData.start_time}:00`;
      const endDateTime = `${formData.end_date} ${formData.end_time}:00`;
      
      const scheduleData: ScheduleEntryCreateData = {
        odl_id: formData.odl_id,
        autoclave_id: formData.autoclave_id,
        start_datetime: startDateTime,
        end_datetime: endDateTime,
        status: formData.status,
        priority_override: formData.priority_override,
        created_by: 'UI-User', // Nome utente (in un'app reale verrebbe dal contesto di autenticazione)
      };
      
      if (editingScheduleId) {
        // Aggiornamento
        await scheduleApi.update(editingScheduleId, scheduleData);
      } else {
        // Creazione
        await scheduleApi.create(scheduleData);
      }
      
      // Chiudi il modale e ricarica gli eventi
      setIsModalOpen(false);
      fetchSchedules();
    } catch (err) {
      console.error('Errore durante il salvataggio della schedulazione:', err);
      setError('Impossibile salvare la schedulazione. Riprova più tardi.');
    }
  };

  // Handler per eliminare una schedulazione
  const handleDelete = async () => {
    if (!editingScheduleId) return;
    
    try {
      await scheduleApi.delete(editingScheduleId);
      setIsModalOpen(false);
      fetchSchedules();
    } catch (err) {
      console.error('Errore durante l\'eliminazione della schedulazione:', err);
      setError('Impossibile eliminare la schedulazione. Riprova più tardi.');
    }
  };

  // Handler per generare automaticamente le schedulazioni
  const handleAutoGenerate = async () => {
    try {
      const date = formatDate(selectedDate);
      await scheduleApi.autoGenerate(date);
      fetchSchedules();
    } catch (err) {
      console.error('Errore durante la generazione automatica:', err);
      setError('Impossibile generare automaticamente le schedulazioni. Riprova più tardi.');
    }
  };

  // Componente per il modale di creazione/modifica
  const ScheduleModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg w-full max-w-xl">
        <h2 className="text-2xl mb-4">
          {editingScheduleId ? 'Modifica Schedulazione' : 'Crea Nuova Schedulazione'}
        </h2>
        
        {error && <div className="bg-red-100 text-red-700 p-2 mb-4 rounded">{error}</div>}
        
        <form onSubmit={handleFormSubmit}>
          <div className="mb-4">
            <label className="block mb-1">ODL</label>
            <select 
              className="w-full p-2 border rounded"
              value={formData.odl_id}
              onChange={e => setFormData({...formData, odl_id: Number(e.target.value)})}
              required
            >
              <option value="">Seleziona un ODL</option>
              {odlList
                .filter(odl => odl.status === 'Attesa Cura')
                .map(odl => (
                  <option key={odl.id} value={odl.id}>
                    ODL #{odl.id} - {odl.parte.descrizione_breve}
                  </option>
                ))}
            </select>
          </div>
          
          <div className="mb-4">
            <label className="block mb-1">Autoclave</label>
            <select 
              className="w-full p-2 border rounded"
              value={formData.autoclave_id}
              onChange={e => setFormData({...formData, autoclave_id: Number(e.target.value)})}
              required
            >
              <option value="">Seleziona un'autoclave</option>
              {autoclavi.map(autoclave => (
                <option key={autoclave.id} value={autoclave.id}>
                  {autoclave.nome} ({autoclave.codice})
                </option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block mb-1">Data Inizio</label>
              <input 
                type="date" 
                className="w-full p-2 border rounded"
                value={formData.start_date}
                onChange={e => setFormData({...formData, start_date: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block mb-1">Ora Inizio</label>
              <input 
                type="time" 
                className="w-full p-2 border rounded"
                value={formData.start_time}
                onChange={e => setFormData({...formData, start_time: e.target.value})}
                required
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block mb-1">Data Fine</label>
              <input 
                type="date" 
                className="w-full p-2 border rounded"
                value={formData.end_date}
                onChange={e => setFormData({...formData, end_date: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block mb-1">Ora Fine</label>
              <input 
                type="time" 
                className="w-full p-2 border rounded"
                value={formData.end_time}
                onChange={e => setFormData({...formData, end_time: e.target.value})}
                required
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label className="flex items-center">
              <input 
                type="checkbox" 
                checked={formData.priority_override}
                onChange={e => setFormData({...formData, priority_override: e.target.checked})}
                className="mr-2"
              />
              Priorità sovrascritta manualmente
            </label>
          </div>
          
          <div className="flex justify-between">
            <div>
              <button 
                type="submit" 
                className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 mr-2"
              >
                {editingScheduleId ? 'Aggiorna' : 'Crea'}
              </button>
              <button 
                type="button" 
                onClick={() => setIsModalOpen(false)}
                className="bg-gray-300 py-2 px-4 rounded hover:bg-gray-400"
              >
                Annulla
              </button>
            </div>
            
            {editingScheduleId && (
              <button 
                type="button" 
                onClick={handleDelete}
                className="bg-red-500 text-white py-2 px-4 rounded hover:bg-red-600"
              >
                Elimina
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col">
      <div className="flex justify-between items-center p-4 bg-gray-100">
        <h1 className="text-2xl font-bold">Scheduling ODL per Autoclavi</h1>
        
        <div>
          <button 
            onClick={handleAutoGenerate}
            className="bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600 mr-2"
          >
            Auto-genera
          </button>
          <button 
            onClick={() => {
              setFormData({
                odl_id: 0,
                autoclave_id: 0,
                start_date: formatDate(selectedDate),
                start_time: '08:00',
                end_date: formatDate(selectedDate),
                end_time: '17:00',
                status: ScheduleEntryStatus.MANUAL,
                priority_override: false,
              });
              setEditingScheduleId(null);
              setIsModalOpen(true);
            }}
            className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
          >
            Nuova Schedulazione
          </button>
        </div>
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <p>Caricamento in corso...</p>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-red-500">{error}</p>
        </div>
      ) : (
        <div className="flex-1 p-4">
          <Calendar
            localizer={localizer as any}
            events={events}
            resources={resources}
            resourceIdAccessor="id"
            resourceTitleAccessor="title"
            startAccessor="start"
            endAccessor="end"
            views={[Views.DAY, Views.WEEK, Views.MONTH]}
            defaultView={Views.WEEK}
            step={60}
            defaultDate={selectedDate}
            selectable
            onSelectSlot={handleSelectSlot}
            onSelectEvent={handleSelectEvent}
            onNavigate={handleNavigate}
            eventPropGetter={(event: any) => ({
              style: {
                backgroundColor: event.isManual ? '#F59E0B' : '#3B82F6',
                borderColor: event.isManual ? '#D97706' : '#2563EB',
              },
            })}
            className="h-full"
          />
        </div>
      )}
      
      {isModalOpen && <ScheduleModal />}
    </div>
  );
};

export default CalendarSchedule; 