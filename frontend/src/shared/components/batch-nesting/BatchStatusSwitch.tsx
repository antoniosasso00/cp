'use client';

import React, { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Loader2, 
  Lock, 
  PlayCircle,
  StopCircle,
  Info
} from 'lucide-react';
import { batchNestingApi } from '@/lib/api';

// Tipi per lo stato del batch
type BatchStatus = 'sospeso' | 'confermato' | 'terminato';

interface BatchStatusInfo {
  status: BatchStatus;
  label: string;
  description: string;
  color: string;
  icon: React.ComponentType<{ className?: string }>;
  canTransitionTo: BatchStatus[];
}

// Configurazione stati batch
const BATCH_STATUS_CONFIG: Record<BatchStatus, BatchStatusInfo> = {
  sospeso: {
    status: 'sospeso',
    label: 'In Sospeso',
    description: 'Batch generato, in attesa di conferma per avviare il ciclo di cura',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: Clock,
    canTransitionTo: ['confermato']
  },
  confermato: {
    status: 'confermato', 
    label: 'Confermato',
    description: 'Batch confermato, ciclo di cura avviato. ODL in stato "Cura"',
    color: 'bg-green-100 text-green-800 border-green-300',
    icon: PlayCircle,
    canTransitionTo: ['terminato']
  },
  terminato: {
    status: 'terminato',
    label: 'Terminato', 
    description: 'Ciclo di cura completato. ODL in stato "Finito"',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: CheckCircle,
    canTransitionTo: []
  }
};

interface BatchStatusSwitchProps {
  /** ID univoco del batch */
  batchId: string;
  /** Stato attuale del batch */
  currentStatus: BatchStatus;
  /** Nome del batch per visualizzazione */
  batchName?: string;
  /** Numero di ODL nel batch */
  odlCount?: number;
  /** Peso totale del batch in kg */
  totalWeight?: number;
  /** Callback chiamato quando lo stato cambia con successo */
  onStatusChanged?: (newStatus: BatchStatus) => void;
  /** Informazioni utente per audit */
  userInfo?: {
    userId: string;
    userRole: string;
  };
  /** Modalità read-only per visualizzazione */
  readOnly?: boolean;
}

export default function BatchStatusSwitch({
  batchId,
  currentStatus,
  batchName,
  odlCount = 0,
  totalWeight = 0,
  onStatusChanged,
  userInfo = { userId: 'utente_frontend', userRole: 'Curing' },
  readOnly = false
}: BatchStatusSwitchProps) {
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState<BatchStatus | null>(null);

  const currentConfig = BATCH_STATUS_CONFIG[currentStatus];

  // Funzione per gestire il cambio di stato
  const handleStatusChange = async (newStatus: BatchStatus) => {
    // Verifica se la transizione è consentita
    if (!currentConfig.canTransitionTo.includes(newStatus)) {
      setError(`Transizione da ${currentConfig.label} a ${BATCH_STATUS_CONFIG[newStatus].label} non consentita`);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let updatedBatch;

      // Esegui l'azione appropriata in base al nuovo stato
      switch (newStatus) {
        case 'confermato':
          console.log(`🚀 Confermando batch ${batchId}...`);
          updatedBatch = await batchNestingApi.conferma(
            batchId,
            userInfo.userId,
            userInfo.userRole
          );
          break;

        case 'terminato':
          console.log(`🏁 Terminando batch ${batchId}...`);
          updatedBatch = await batchNestingApi.chiudi(
            batchId,
            userInfo.userId,
            userInfo.userRole
          );
          break;

        default:
          throw new Error(`Azione non implementata per stato: ${newStatus}`);
      }

      console.log(`✅ Batch ${batchId} aggiornato a stato: ${newStatus}`);

      // Notifica il parent component
      if (onStatusChanged) {
        onStatusChanged(newStatus);
      }

      setShowConfirmation(null);

    } catch (err: any) {
      console.error(`❌ Errore nel cambio stato batch ${batchId}:`, err);
      setError(err.message || 'Errore durante il cambio di stato');
    } finally {
      setIsLoading(false);
    }
  };

  // Funzione per aprire la conferma
  const requestStatusChange = (newStatus: BatchStatus) => {
    setShowConfirmation(newStatus);
    setError(null);
  };

  // Funzione per annullare la conferma  
  const cancelStatusChange = () => {
    setShowConfirmation(null);
    setError(null);
  };

  const CurrentIcon = currentConfig.icon;

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <CurrentIcon className="h-5 w-5" />
          Controllo Stato Batch
          {batchName && (
            <span className="text-sm font-normal text-gray-600">({batchName})</span>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stato Attuale */}
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-700">Stato Attuale:</span>
            <Badge className={`${currentConfig.color} px-3 py-1`}>
              <CurrentIcon className="h-4 w-4 mr-1" />
              {currentConfig.label}
            </Badge>
          </div>
          
          {/* Statistiche Batch */}
          <div className="text-right text-sm text-gray-600">
            <div>ODL: {odlCount}</div>
            <div>Peso: {totalWeight.toFixed(1)} kg</div>
          </div>
        </div>

        {/* Descrizione Stato */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription className="text-sm">
            {currentConfig.description}
          </AlertDescription>
        </Alert>

        {/* Controlli di Transizione */}
        {!readOnly && currentConfig.canTransitionTo.length > 0 && (
          <div className="space-y-3">
            <span className="text-sm font-medium text-gray-700">Azioni Disponibili:</span>
            
            {currentConfig.canTransitionTo.map(nextStatus => {
              const nextConfig = BATCH_STATUS_CONFIG[nextStatus];
              const NextIcon = nextConfig.icon;
              
              return (
                <div key={nextStatus} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <NextIcon className="h-5 w-5 text-gray-600" />
                    <div>
                      <div className="font-medium">{nextConfig.label}</div>
                      <div className="text-sm text-gray-600">{nextConfig.description}</div>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => requestStatusChange(nextStatus)}
                    disabled={isLoading}
                    variant="outline"
                    size="sm"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <NextIcon className="h-4 w-4 mr-1" />
                        Avvia
                      </>
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        {/* Stato Read-Only */}
        {readOnly && (
          <Alert>
            <Lock className="h-4 w-4" />
            <AlertDescription>
              Visualizzazione in sola lettura. Le modifiche di stato non sono consentite.
            </AlertDescription>
          </Alert>
        )}

        {/* Stato Finale */}
        {currentConfig.canTransitionTo.length === 0 && !readOnly && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Batch completato. Non sono disponibili ulteriori azioni.
            </AlertDescription>
          </Alert>
        )}

        {/* Errori */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Modal di Conferma */}
        {showConfirmation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Conferma Cambio Stato
                </CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="text-sm">
                  Sei sicuro di voler cambiare lo stato del batch da{' '}
                  <Badge className={currentConfig.color}>{currentConfig.label}</Badge>
                  {' '}a{' '}
                  <Badge className={BATCH_STATUS_CONFIG[showConfirmation].color}>
                    {BATCH_STATUS_CONFIG[showConfirmation].label}
                  </Badge>
                  ?
                </div>

                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-sm">
                    {BATCH_STATUS_CONFIG[showConfirmation].description}
                  </AlertDescription>
                </Alert>

                <div className="flex gap-2 justify-end">
                  <Button
                    variant="outline"
                    onClick={cancelStatusChange}
                    disabled={isLoading}
                  >
                    Annulla
                  </Button>
                  <Button
                    onClick={() => handleStatusChange(showConfirmation)}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-1" />
                    )}
                    Conferma
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 