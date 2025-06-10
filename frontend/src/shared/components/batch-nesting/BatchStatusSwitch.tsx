'use client';

import React, { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Lock, Info, CheckCircle, AlertTriangle } from 'lucide-react';
import { batchNestingApi } from '@/lib/api';
import { 
  useBatchStatus, 
  BatchStatus,
  BATCH_STATUS_CONFIG,
  getAvailableTransitions 
} from '@/shared/hooks/useBatchStatus';

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
  
  const [showConfirmation, setShowConfirmation] = useState<BatchStatus | null>(null);
  
  // Usa la state machine centralizzata
  const batchStatus = useBatchStatus(batchId, currentStatus);
  
  // Ottieni le transizioni valide per l'utente corrente
  const validTransitions = getAvailableTransitions(batchStatus.state).filter(
    nextStatus => batchStatus.canTransition(nextStatus, userInfo.userRole)
  );

  // Funzione per gestire il cambio di stato
  const handleStatusChange = async (newStatus: BatchStatus) => {
    // Verifica se la transizione è consentita
    if (!batchStatus.canTransition(newStatus, userInfo.userRole)) {
      return;
    }

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

        case 'loaded':
          console.log(`📦 Caricando batch ${batchId}...`);
          updatedBatch = await batchNestingApi.carica(
            batchId,
            userInfo.userId,
            userInfo.userRole
          );
          break;

        case 'cured':
          console.log(`🔥 Avviando cura batch ${batchId}...`);
          updatedBatch = await batchNestingApi.avviaCura(
            batchId,
            userInfo.userId,
            userInfo.userRole
          );
          break;

        case 'terminato':
          console.log(`🏁 Terminando batch ${batchId}...`);
          updatedBatch = await batchNestingApi.termina(
            batchId,
            userInfo.userId,
            userInfo.userRole
          );
          break;

        default:
          throw new Error(`Azione non implementata per stato: ${newStatus}`);
      }

      console.log(`✅ Batch ${batchId} aggiornato a stato: ${newStatus}`);
      
      // Usa la state machine per la transizione
      await batchStatus.transition(newStatus, userInfo.userRole);

      // Notifica il parent component
      if (onStatusChanged) {
        onStatusChanged(newStatus);
      }

      setShowConfirmation(null);

    } catch (err: any) {
      console.error(`❌ Errore nel cambio stato batch ${batchId}:`, err);
      // L'errore viene gestito dalla state machine
    }
  };

  // Funzione per aprire la conferma
  const requestStatusChange = (newStatus: BatchStatus) => {
    setShowConfirmation(newStatus);
    batchStatus.clearError();
  };

  // Funzione per annullare la conferma
  const cancelStatusChange = () => {
    setShowConfirmation(null);
    batchStatus.clearError();
  };

  // Ottieni configurazione dello stato corrente
  const currentStatusInfo = batchStatus.statusInfo;
  const CurrentIcon = currentStatusInfo.icon;

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <CurrentIcon className="h-6 w-6" />
          Gestione Stato Batch: {batchName || batchId}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Stato Corrente */}
        <div className="flex items-center justify-between p-4 rounded-lg border">
          <div className="flex items-center gap-3">
            <CurrentIcon className="h-8 w-8 text-gray-600" />
            <div>
              <div className="font-semibold text-lg">{currentStatusInfo.label}</div>
              <div className="text-sm text-gray-600">{currentStatusInfo.description}</div>
            </div>
          </div>
          
          <Badge 
            className={`${currentStatusInfo.color.bg} ${currentStatusInfo.color.text} ${currentStatusInfo.color.border} border`}
          >
            {currentStatusInfo.label}
          </Badge>
        </div>

        {/* Informazioni Batch */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-sm">
            <span className="font-medium">ODL inclusi:</span> {odlCount}
          </div>
          <div className="text-sm">
            <span className="font-medium">Peso totale:</span> {totalWeight} kg
          </div>
        </div>

        {/* Errori dalla State Machine */}
        {batchStatus.error && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {batchStatus.error}
            </AlertDescription>
          </Alert>
        )}

        {/* Transizione in corso */}
        {batchStatus.isTransitioning && (
          <Alert>
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertDescription>
              Aggiornamento stato in corso...
            </AlertDescription>
          </Alert>
        )}

        {/* Dialogo di Conferma */}
        {showConfirmation && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-3">
                <p>
                  Confermare la transizione a: <strong>{BATCH_STATUS_CONFIG[showConfirmation].label}</strong>?
                </p>
                <p className="text-sm text-gray-600">
                  {BATCH_STATUS_CONFIG[showConfirmation].description}
                </p>
                <div className="flex gap-2">
                  <Button 
                    onClick={() => handleStatusChange(showConfirmation)}
                    disabled={batchStatus.isTransitioning}
                    size="sm"
                  >
                    {batchStatus.isTransitioning ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-1" />
                    )}
                    Conferma
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={cancelStatusChange}
                    disabled={batchStatus.isTransitioning}
                    size="sm"
                  >
                    Annulla
                  </Button>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Azioni Disponibili */}
        {!readOnly && validTransitions.length > 0 && (
          <div className="space-y-3">
            <span className="text-sm font-medium text-gray-700">Azioni Disponibili:</span>
            
            {validTransitions.map((nextStatus: BatchStatus) => {
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
                    disabled={batchStatus.isTransitioning}
                    variant="outline"
                    size="sm"
                  >
                    {batchStatus.isTransitioning ? (
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
        {validTransitions.length === 0 && !readOnly && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Batch in stato finale. Nessuna azione aggiuntiva disponibile.
            </AlertDescription>
          </Alert>
        )}

        {/* Informazioni Ultima Transizione */}
        {batchStatus.lastTransition && (
          <div className="text-xs text-gray-500 p-2 bg-gray-50 rounded">
            Ultima transizione: {batchStatus.lastTransition.label}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 