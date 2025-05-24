import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, dateFnsLocalizer, Views, SlotInfo } from 'react-big-calendar';
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
import { useTheme } from 'next-themes';

// Localizer ufficiale italiano per il calendario usando date-fns
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales: { it },
});

// Formato per date e orari
const dateFormat = 'yyyy-MM-dd';
const timeFormat = 'HH:mm';
const dateTimeFormat = 'yyyy-MM-dd HH:mm:ss';

// Funzioni per formattare date
const formatDate = (date: Date) => format(date, dateFormat);
const formatTime = (date: Date) => format(date, timeFormat);
const formatDateTime = (date: Date) => format(date, dateTimeFormat);

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

  // Funzione per recuperare le schedulazioni dal server
  const fetchSchedules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const schedules = await scheduleApi.getAll({ include_done: false });
      
      // Converte le schedulazioni in eventi per il calendario
      const calendarEvents = schedules.map(schedule => ({
        id: schedule.id,
        title: `${schedule.status === ScheduleEntryStatus.MANUAL ? '(M) ' : ''}${schedule.odl_id ? `Parte ${schedule.odl_id}` : 'ODL'}`,
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
  }, []);

  // Carica gli eventi al cambio della data selezionata
  useEffect(() => {
    fetchSchedules();
  }, [selectedDate, fetchSchedules]);

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
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg w-full max-w-xl border dark:border-gray-700">
        <h2 className="text-2xl mb-4 text-gray-900 dark:text-white">
          {editingScheduleId ? 'Modifica Schedulazione' : 'Crea Nuova Schedulazione'}
        </h2>
        
        {error && (
          <div className="bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 p-2 mb-4 rounded border dark:border-red-800">
            {error}
          </div>
        )}
        
        <form onSubmit={handleFormSubmit}>
          <div className="mb-4">
            <label className="block mb-1 text-gray-700 dark:text-gray-300">ODL</label>
            <select 
              className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              value={formData.odl_id}
              onChange={e => setFormData({...formData, odl_id: Number(e.target.value)})}
              required
            >
              <option value="">Seleziona un ODL</option>
              {odlList
                .filter(odl => odl.status === 'Attesa Cura')
                .map(odl => (
                  <option key={odl.id} value={odl.id}>
                    {odl.parte.descrizione_breve}
                  </option>
                ))}
            </select>
          </div>
          
          <div className="mb-4">
            <label className="block mb-1 text-gray-700 dark:text-gray-300">Autoclave</label>
            <select 
              className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
              <label className="block mb-1 text-gray-700 dark:text-gray-300">Data Inizio</label>
              <input 
                type="date" 
                className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                value={formData.start_date}
                onChange={e => setFormData({...formData, start_date: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block mb-1 text-gray-700 dark:text-gray-300">Ora Inizio</label>
              <input 
                type="time" 
                className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                value={formData.start_time}
                onChange={e => setFormData({...formData, start_time: e.target.value})}
                required
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block mb-1 text-gray-700 dark:text-gray-300">Data Fine</label>
              <input 
                type="date" 
                className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                value={formData.end_date}
                onChange={e => setFormData({...formData, end_date: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block mb-1 text-gray-700 dark:text-gray-300">Ora Fine</label>
              <input 
                type="time" 
                className="w-full p-2 border dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                value={formData.end_time}
                onChange={e => setFormData({...formData, end_time: e.target.value})}
                required
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label className="flex items-center text-gray-700 dark:text-gray-300">
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
                className="bg-blue-500 dark:bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-600 dark:hover:bg-blue-700 mr-2 transition-colors"
              >
                {editingScheduleId ? 'Aggiorna' : 'Crea'}
              </button>
              <button 
                type="button" 
                onClick={() => setIsModalOpen(false)}
                className="bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 py-2 px-4 rounded hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors"
              >
                Annulla
              </button>
            </div>
            
            {editingScheduleId && (
              <button 
                type="button" 
                onClick={handleDelete}
                className="bg-red-500 dark:bg-red-600 text-white py-2 px-4 rounded hover:bg-red-600 dark:hover:bg-red-700 transition-colors"
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
    <div className="h-screen flex flex-col dark:bg-gray-900">
      <div className="flex justify-between items-center p-4 bg-gray-100 dark:bg-gray-800 border-b dark:border-gray-700">
        <h1 className="text-2xl font-bold dark:text-white">Scheduling ODL per Autoclavi</h1>
        
        <div>
          <button 
            onClick={handleAutoGenerate}
            className="bg-green-500 dark:bg-green-600 text-white py-2 px-4 rounded hover:bg-green-600 dark:hover:bg-green-700 mr-2 transition-colors"
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
            className="bg-blue-500 dark:bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors"
          >
            Nuova Schedulazione
          </button>
        </div>
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center dark:text-white">
          <p>Caricamento in corso...</p>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-red-500 dark:text-red-400">{error}</p>
        </div>
      ) : (
        <div className="flex-1 p-4">
          <style jsx global>{`
            /* Stili personalizzati per il calendario in modalità dark */
            .dark .rbc-calendar {
              background-color: #1f2937;
              color: #f9fafb;
            }
            
            .dark .rbc-header {
              background-color: #374151;
              color: #f9fafb;
              border-bottom: 1px solid #4b5563;
            }
            
            .dark .rbc-month-view,
            .dark .rbc-time-view {
              background-color: #1f2937;
              border-color: #4b5563;
            }
            
            .dark .rbc-day-bg {
              background-color: #1f2937;
              border-color: #4b5563;
            }
            
            .dark .rbc-today {
              background-color: #065f46 !important;
            }
            
            .dark .rbc-event {
              background-color: #3b82f6;
              border-color: #2563eb;
              color: #ffffff;
            }
            
            .dark .rbc-selected {
              background-color: #1d4ed8;
            }
            
            .dark .rbc-time-slot {
              border-color: #4b5563;
            }
            
            .dark .rbc-time-header {
              background-color: #374151;
              border-color: #4b5563;
            }
            
            .dark .rbc-time-content {
              border-color: #4b5563;
            }
            
            .dark .rbc-allday-cell {
              background-color: #374151;
              border-color: #4b5563;
            }
            
            .dark .rbc-row-bg {
              border-color: #4b5563;
            }
            
            .dark .rbc-off-range-bg {
              background-color: #111827;
            }
            
            .dark .rbc-toolbar {
              background-color: #374151;
              color: #f9fafb;
            }
            
            .dark .rbc-toolbar button {
              background-color: #4b5563;
              color: #f9fafb;
              border: 1px solid #6b7280;
            }
            
            .dark .rbc-toolbar button:hover {
              background-color: #6b7280;
            }
            
            .dark .rbc-toolbar button.rbc-active {
              background-color: #3b82f6;
              color: #ffffff;
            }
            
            .dark .rbc-month-row {
              border-color: #4b5563;
            }
            
            .dark .rbc-date-cell {
              color: #f9fafb;
            }
            
            .dark .rbc-date-cell a {
              color: #f9fafb;
            }
            
            .dark .rbc-button-link {
              color: #f9fafb;
            }
          `}</style>
          <Calendar
            localizer={localizer}
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
                color: '#FFFFFF',
                fontWeight: '500'
              },
            })}
            className="h-full rbc-calendar"
          />
        </div>
      )}
      
      {isModalOpen && <ScheduleModal />}
    </div>
  );
};

export default CalendarSchedule; 