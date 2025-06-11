import React, { useState } from 'react';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { 
  CheckCircle, 
  Clock, 
  Flame, 
  CheckCircle2,
  User,
  Calendar
} from 'lucide-react';
import { useStandardToast } from '@/shared/hooks/use-standard-toast';
import { batchNestingApi } from '@/shared/lib/api';

// 🆕 STATI SEMPLIFICATI - Nuovo flusso industriale
type BatchStatus = 'draft' | 'sospeso' | 'in_cura' | 'terminato';

interface BatchStatusControlProps {
  batchId: string;
  currentStatus: BatchStatus;
  onStatusChange?: (newStatus: BatchStatus) => void;
  // Dati temporali per display
  dataConferma?: string;
  dataInizioCura?: string;
  dataFineCura?: string;
  durataCuraMinuti?: number;
  confermato_da_utente?: string;
  caricato_da_utente?: string;
  terminato_da_utente?: string;
}

// Configurazione degli stati nel nuovo flusso
const STATUS_CONFIG = {
  draft: {
    label: 'Bozza',
    color: 'bg-gray-100 text-gray-800',
    icon: Clock,
    description: 'Risultati generati, non confermati',
    nextAction: 'Conferma Batch',
    nextStatus: 'sospeso' as BatchStatus,
    endpoint: '/confirm'
  },
  sospeso: {
    label: 'Sospeso',
    color: 'bg-yellow-100 text-yellow-800',
    icon: Clock,
    description: 'Confermato dall\'operatore, pronto per caricamento',
    nextAction: 'Inizia Cura',
    nextStatus: 'in_cura' as BatchStatus,
    endpoint: '/start-cure'
  },
  in_cura: {
    label: 'In Cura',
    color: 'bg-red-100 text-red-800',
    icon: Flame,
    description: 'Autoclave caricata, cura in corso',
    nextAction: 'Termina Cura',
    nextStatus: 'terminato' as BatchStatus,
    endpoint: '/terminate'
  },
  terminato: {
    label: 'Completato',
    color: 'bg-green-100 text-green-800',
    icon: CheckCircle2,
    description: 'Cura completata, workflow chiuso',
    nextAction: null,
    nextStatus: null,
    endpoint: null
  }
} as const;

export function BatchStatusControl({
  batchId,
  currentStatus,
  onStatusChange,
  dataConferma,
  dataInizioCura,
  dataFineCura,
  durataCuraMinuti,
  confermato_da_utente,
  caricato_da_utente,
  terminato_da_utente
}: BatchStatusControlProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { success, error } = useStandardToast();

  const config = STATUS_CONFIG[currentStatus];
  const IconComponent = config.icon;

  const handleStatusChange = async () => {
    if (!config.nextStatus || !config.endpoint) return;

    setIsLoading(true);
    try {
      // Simulate user info (in production, get from auth context)
      const userId = 'ADMIN';
      const userRole = 'ADMIN';
      
      // Usa l'API centralizzata con i parametri corretti
      if (config.endpoint === '/confirm') {
        await batchNestingApi.conferma(batchId, userId, userRole);
      } else if (config.endpoint === '/start-cure') {
        await batchNestingApi.avviaCura(batchId, userId, userRole);
      } else if (config.endpoint === '/terminate') {
        await batchNestingApi.termina(batchId, userId, userRole);
      }
      
      success(`${config.nextAction} completata`, 'Operazione eseguita con successo');
      
      // Notifica il parent component del cambio di stato
      onStatusChange?.(config.nextStatus);
      
    } catch (err) {
      console.error('Errore nel cambio stato:', err);
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto';
      error(`Errore in ${config.nextAction}`, errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return null;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return hours > 0 ? `${hours}h ${remainingMinutes}m` : `${remainingMinutes}m`;
  };

  return (
    <div className="space-y-4">
      {/* Stato Attuale */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <IconComponent className="h-6 w-6 text-gray-600" />
          <div>
            <Badge className={config.color}>
              {config.label}
            </Badge>
            <p className="text-sm text-gray-600 mt-1">
              {config.description}
            </p>
          </div>
        </div>

        {/* Pulsante Azione */}
        {config.nextAction && (
          <Button
            onClick={handleStatusChange}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isLoading ? 'Elaborazione...' : config.nextAction}
          </Button>
        )}
      </div>

      {/* Timeline Informazioni */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
        {/* Conferma */}
        {(currentStatus !== 'draft') && (
          <div className="flex items-center space-x-2 text-sm">
            <CheckCircle className="h-4 w-4 text-blue-500" />
            <div>
              <div className="font-medium">Confermato</div>
              <div className="text-gray-500">
                {formatDate(dataConferma)}
              </div>
              {confermato_da_utente && (
                <div className="text-xs text-gray-400 flex items-center">
                  <User className="h-3 w-3 mr-1" />
                  {confermato_da_utente}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Inizio Cura */}
        {(['in_cura', 'terminato'].includes(currentStatus)) && (
          <div className="flex items-center space-x-2 text-sm">
            <Flame className="h-4 w-4 text-red-500" />
            <div>
              <div className="font-medium">Cura Iniziata</div>
              <div className="text-gray-500">
                {formatDate(dataInizioCura)}
              </div>
              {caricato_da_utente && (
                <div className="text-xs text-gray-400 flex items-center">
                  <User className="h-3 w-3 mr-1" />
                  {caricato_da_utente}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Fine Cura */}
        {currentStatus === 'terminato' && (
          <div className="flex items-center space-x-2 text-sm">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <div>
              <div className="font-medium">Cura Completata</div>
              <div className="text-gray-500">
                {formatDate(dataFineCura)}
              </div>
              {durataCuraMinuti && (
                <div className="text-xs text-blue-600 font-medium">
                  Durata: {formatDuration(durataCuraMinuti)}
                </div>
              )}
              {terminato_da_utente && (
                <div className="text-xs text-gray-400 flex items-center">
                  <User className="h-3 w-3 mr-1" />
                  {terminato_da_utente}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 