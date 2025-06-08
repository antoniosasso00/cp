import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, dateFnsLocalizer, Views, SlotInfo } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { it } from 'date-fns/locale';
import { 
  ScheduleEntry, 
  ScheduleEntryStatus, 
  ScheduleEntryType,
  CalendarEvent, 
  CalendarResource,
  ScheduleOperatorActionData
} from '@/lib/types/schedule';
import { SCHEDULE_STATUS_COLORS, SCHEDULE_STATUS_LABELS } from '@/shared/lib/constants';
import { scheduleApi } from '@/lib/api';
import { Autoclave, ODLResponse } from '@/lib/api';
import { useTheme } from 'next-themes';
import ScheduleForm from './ScheduleForm';
import RecurringScheduleForm from './RecurringScheduleForm';
import { showSuccess, showError, showOperationResult } from '@/shared/services/toast-service';

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

// Funzioni per formattare date
const formatDate = (date: Date) => format(date, dateFormat);
const formatTime = (date: Date) => format(date, timeFormat);

// Interfaccia per le props del componente
interface CalendarScheduleProps {
  autoclavi: Autoclave[];
  odlList: ODLResponse[];
}

// Componente principale
const CalendarSchedule: React.FC<CalendarScheduleProps> = ({ autoclavi, odlList }) => {
  const { theme } = useTheme();
  
  // State
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [resources, setResources] = useState<CalendarResource[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [showScheduleForm, setShowScheduleForm] = useState<boolean>(false);
  const [showRecurringForm, setShowRecurringForm] = useState<boolean>(false);
  const [selectedSlot, setSelectedSlot] = useState<SlotInfo | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

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
      const calendarEvents: CalendarEvent[] = schedules.map(schedule => {
        const title = getEventTitle(schedule);
        const isPriority = Boolean(schedule.odl?.priorita && schedule.odl.priorita >= 8);
        
        return {
          id: schedule.id,
          title,
          start: new Date(schedule.start_datetime),
          end: schedule.end_datetime ? new Date(schedule.end_datetime) : new Date(schedule.start_datetime),
          resourceId: schedule.autoclave_id,
          isManual: schedule.status === ScheduleEntryStatus.MANUAL,
          isPriority,
          isRecurring: schedule.is_recurring,
          scheduleType: schedule.schedule_type,
          status: schedule.status,
          scheduleData: schedule
        };
      });
      
      setEvents(calendarEvents);
    } catch (err) {
      console.error('Errore nel caricamento delle schedulazioni:', err);
      setError('Impossibile caricare le schedulazioni. Riprova più tardi.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Funzione per generare il titolo dell'evento
  const getEventTitle = (schedule: ScheduleEntry): string => {
    let title = '';
    
    // Prefisso per il tipo
    switch (schedule.schedule_type) {
      case ScheduleEntryType.ODL_SPECIFICO:
        title = schedule.odl ? `ODL #${schedule.odl.id}` : 'ODL';
        break;
      case ScheduleEntryType.CATEGORIA:
        title = `Cat: ${schedule.categoria}`;
        break;
      case ScheduleEntryType.SOTTO_CATEGORIA:
        title = `Sub: ${schedule.sotto_categoria}`;
        break;
      case ScheduleEntryType.RICORRENTE:
        title = `Ric: ${schedule.categoria || schedule.sotto_categoria}`;
        break;
    }
    
    // Aggiungi badge di priorità
    if (schedule.odl?.priorita && schedule.odl.priorita >= 8) {
      title = `🔥 ${title}`;
    }
    
    // Aggiungi stato
    switch (schedule.status) {
      case ScheduleEntryStatus.PREVISIONALE:
        title = `📋 ${title}`;
        break;
      case ScheduleEntryStatus.IN_ATTESA:
        title = `⏳ ${title}`;
        break;
      case ScheduleEntryStatus.IN_CORSO:
        title = `🔄 ${title}`;
        break;
      case ScheduleEntryStatus.POSTICIPATO:
        title = `⏸️ ${title}`;
        break;
    }
    
    return title;
  };

  // Carica gli eventi al cambio della data selezionata
  useEffect(() => {
    fetchSchedules();
  }, [selectedDate, fetchSchedules]);

  // Handler per il clic su uno slot vuoto del calendario
  const handleSelectSlot = useCallback(
    (slotInfo: SlotInfo) => {
      setSelectedSlot(slotInfo);
      setSelectedEvent(null);
      setShowScheduleForm(true);
    },
    []
  );

  // Handler per il clic su un evento esistente
  const handleSelectEvent = useCallback(
    (event: CalendarEvent) => {
      setSelectedEvent(event);
      setSelectedSlot(null);
      // Non apriamo automaticamente il form, mostriamo solo il tooltip/azioni
    },
    []
  );

  // Handler per il cambio di data/view del calendario
  const handleNavigate = (date: Date) => {
    setSelectedDate(date);
  };

  // Handler per eliminare una schedulazione
  const handleDelete = async (scheduleId: number) => {
    try {
      await scheduleApi.delete(scheduleId);
      setSelectedEvent(null);
      fetchSchedules();
      showOperationResult('success', {
        operation: 'Eliminazione',
        entity: 'schedulazione'
      });
    } catch (err) {
      console.error('Errore durante l\'eliminazione della schedulazione:', err);
      showOperationResult('error', {
        operation: 'Eliminazione',
        entity: 'schedulazione'
      });
    }
  };

  // Handler per generare automaticamente le schedulazioni
  const handleAutoGenerate = async () => {
    try {
      const date = formatDate(selectedDate);
      const result = await scheduleApi.autoGenerate(date);
      fetchSchedules();
      showSuccess('Generazione Automatica Completata', `${result.count} schedulazioni generate automaticamente`);
    } catch (err) {
      console.error('Errore durante la generazione automatica:', err);
      showError('Errore Generazione Automatica', 'Impossibile generare le schedulazioni automaticamente');
    }
  };

  // Handler per azioni dell'operatore
  const handleOperatorAction = async (scheduleId: number, action: ScheduleOperatorActionData) => {
    try {
      setActionLoading(scheduleId);
      await scheduleApi.executeAction(scheduleId, action);
      fetchSchedules();
      setSelectedEvent(null);
      
      let message = '';
      switch (action.action) {
        case 'avvia':
          message = 'Schedulazione avviata con successo';
          break;
        case 'posticipa':
          message = 'Schedulazione posticipata con successo';
          break;
        case 'completa':
          message = 'Schedulazione completata con successo';
          break;
      }
      showSuccess('Azione Completata', message);
    } catch (err) {
      console.error('Errore durante l\'azione dell\'operatore:', err);
      showError('Errore Azione Operatore', 'Impossibile eseguire l\'azione richiesta');
    } finally {
      setActionLoading(null);
    }
  };

  // Rimosso: ora usiamo il servizio standardizzato

  // Componente per il tooltip/azioni dell'evento
  const EventTooltip = ({ event }: { event: CalendarEvent }) => {
    const schedule = event.scheduleData;
    const canStart = schedule.status === ScheduleEntryStatus.IN_ATTESA || schedule.status === ScheduleEntryStatus.SCHEDULED;
    const canPostpone = schedule.status !== ScheduleEntryStatus.DONE && schedule.status !== ScheduleEntryStatus.IN_CORSO;
    const canComplete = schedule.status === ScheduleEntryStatus.IN_CORSO;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedEvent(null)}>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4 border dark:border-gray-700" onClick={e => e.stopPropagation()}>
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Dettagli Schedulazione
            </h3>
            <button 
              onClick={() => setSelectedEvent(null)}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-3 mb-6">
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Tipo: </span>
              <span className="text-gray-900 dark:text-white">{schedule.schedule_type}</span>
            </div>
            
            {schedule.odl && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">ODL: </span>
                <span className="text-gray-900 dark:text-white">#{schedule.odl.id} (Priorità: {schedule.odl.priorita})</span>
              </div>
            )}
            
            {schedule.categoria && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Categoria: </span>
                <span className="text-gray-900 dark:text-white">{schedule.categoria}</span>
              </div>
            )}
            
            {schedule.sotto_categoria && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Sotto-categoria: </span>
                <span className="text-gray-900 dark:text-white">{schedule.sotto_categoria}</span>
              </div>
            )}
            
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Autoclave: </span>
              <span className="text-gray-900 dark:text-white">{schedule.autoclave.nome}</span>
            </div>
            
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Stato: </span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(schedule.status)}`}>
                {getStatusLabel(schedule.status)}
              </span>
            </div>
            
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">Inizio: </span>
              <span className="text-gray-900 dark:text-white">{format(new Date(schedule.start_datetime), 'dd/MM/yyyy HH:mm')}</span>
            </div>
            
            {schedule.end_datetime && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Fine stimata: </span>
                <span className="text-gray-900 dark:text-white">{format(new Date(schedule.end_datetime), 'dd/MM/yyyy HH:mm')}</span>
              </div>
            )}
            
            {schedule.estimated_duration_minutes && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Durata stimata: </span>
                <span className="text-gray-900 dark:text-white">{Math.floor(schedule.estimated_duration_minutes / 60)}h {schedule.estimated_duration_minutes % 60}m</span>
              </div>
            )}
            
            {schedule.note && (
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Note: </span>
                <span className="text-gray-900 dark:text-white">{schedule.note}</span>
              </div>
            )}
          </div>
          
          <div className="flex flex-wrap gap-2">
            {canStart && (
              <button
                onClick={() => handleOperatorAction(schedule.id, { action: 'avvia' })}
                disabled={actionLoading === schedule.id}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                {actionLoading === schedule.id ? '...' : '▶️ Avvia'}
              </button>
            )}
            
            {canPostpone && (
              <button
                onClick={() => {
                  const newDateTime = prompt('Nuova data e ora (YYYY-MM-DD HH:MM):');
                  if (newDateTime) {
                    handleOperatorAction(schedule.id, { 
                      action: 'posticipa', 
                      new_datetime: newDateTime + ':00'
                    });
                  }
                }}
                disabled={actionLoading === schedule.id}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                ⏸️ Posticipa
              </button>
            )}
            
            {canComplete && (
              <button
                onClick={() => handleOperatorAction(schedule.id, { action: 'completa' })}
                disabled={actionLoading === schedule.id}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                ✅ Completa
              </button>
            )}
            
            <button
              onClick={() => handleDelete(schedule.id)}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm font-medium"
            >
              🗑️ Elimina
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Funzioni helper per gli stati (usando costanti centralizzate)
  const getStatusColor = (status: ScheduleEntryStatus): string => {
    // Converti l'enum in stringa per usare le costanti centralizzate
    const statusString = status.toString();
    return SCHEDULE_STATUS_COLORS[statusString as keyof typeof SCHEDULE_STATUS_COLORS] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
  };

  const getStatusLabel = (status: ScheduleEntryStatus): string => {
    // Converti l'enum in stringa per usare le costanti centralizzate
    const statusString = status.toString();
    return SCHEDULE_STATUS_LABELS[statusString as keyof typeof SCHEDULE_STATUS_LABELS] || statusString;
  };

  return (
    <div className="h-screen flex flex-col dark:bg-gray-900">
      <div className="flex justify-between items-center p-4 bg-gray-100 dark:bg-gray-800 border-b dark:border-gray-700">
        <h1 className="text-2xl font-bold dark:text-white">📅 Scheduling Avanzato</h1>
        
        <div className="flex gap-2">
          <button 
            onClick={handleAutoGenerate}
            className="bg-green-500 dark:bg-green-600 text-white py-2 px-4 rounded hover:bg-green-600 dark:hover:bg-green-700 transition-colors text-sm"
          >
            🤖 Auto-genera
          </button>
          <button 
            onClick={() => setShowRecurringForm(true)}
            className="bg-purple-500 dark:bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-600 dark:hover:bg-purple-700 transition-colors text-sm"
          >
            🔄 Ricorrente
          </button>
          <button 
            onClick={() => setShowScheduleForm(true)}
            className="bg-blue-500 dark:bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors text-sm"
          >
            ➕ Nuova
          </button>
        </div>
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center dark:text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p>Caricamento schedulazioni...</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-500 dark:text-red-400 mb-4">{error}</p>
            <button 
              onClick={fetchSchedules}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Riprova
            </button>
          </div>
        </div>
      ) : events.length === 0 ? (
        <div className="flex-1 flex items-center justify-center dark:text-white">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400 mb-4">📅 Nessun evento pianificato</p>
            <p className="text-sm text-gray-400 dark:text-gray-500">Clicca su "Nuova" per creare una schedulazione</p>
          </div>
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
            eventPropGetter={(event: CalendarEvent) => {
              let backgroundColor = '#3B82F6'; // Default blue
              
              // Colori basati sul tipo
              switch (event.scheduleType) {
                case ScheduleEntryType.CATEGORIA:
                  backgroundColor = '#8B5CF6'; // Purple
                  break;
                case ScheduleEntryType.SOTTO_CATEGORIA:
                  backgroundColor = '#06B6D4'; // Cyan
                  break;
                case ScheduleEntryType.RICORRENTE:
                  backgroundColor = '#10B981'; // Green
                  break;
              }
              
              // Colori basati sullo stato
              switch (event.status) {
                case ScheduleEntryStatus.PREVISIONALE:
                  backgroundColor = '#6B7280'; // Gray
                  break;
                case ScheduleEntryStatus.IN_ATTESA:
                  backgroundColor = '#F59E0B'; // Yellow
                  break;
                case ScheduleEntryStatus.IN_CORSO:
                  backgroundColor = '#3B82F6'; // Blue
                  break;
                case ScheduleEntryStatus.POSTICIPATO:
                  backgroundColor = '#F97316'; // Orange
                  break;
                case ScheduleEntryStatus.DONE:
                  backgroundColor = '#10B981'; // Green
                  break;
              }
              
              // Priorità alta
              if (event.isPriority) {
                backgroundColor = '#DC2626'; // Red for high priority
              }
              
              return {
                style: {
                  backgroundColor,
                  borderColor: backgroundColor,
                  color: '#FFFFFF',
                  fontWeight: event.isPriority ? 'bold' : '500',
                  border: event.isPriority ? '2px solid #FEF3C7' : undefined
                },
              };
            }}
            className="h-full rbc-calendar"
          />
        </div>
      )}
      
      {/* Form per nuova schedulazione */}
      {showScheduleForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-h-[90vh] overflow-y-auto">
            <ScheduleForm
              autoclavi={autoclavi}
              odlList={odlList}
              onScheduleCreated={() => {
                setShowScheduleForm(false);
                fetchSchedules();
              }}
              onCancel={() => setShowScheduleForm(false)}
              initialData={selectedSlot ? {
                date: selectedSlot.start,
                autoclave_id: selectedSlot.resourceId ? Number(selectedSlot.resourceId) : undefined
              } : undefined}
            />
          </div>
        </div>
      )}
      
      {/* Form per schedulazione ricorrente */}
      {showRecurringForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-h-[90vh] overflow-y-auto">
            <RecurringScheduleForm
              autoclavi={autoclavi}
              onSchedulesCreated={() => {
                setShowRecurringForm(false);
                fetchSchedules();
              }}
              onCancel={() => setShowRecurringForm(false)}
            />
          </div>
        </div>
      )}
      
      {/* Tooltip per evento selezionato */}
      {selectedEvent && <EventTooltip event={selectedEvent} />}
    </div>
  );
};

export default CalendarSchedule; 