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
  Package,
  PlayCircle,
  Settings,
  Info,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { odlApi } from '@/lib/api';

// Tipi per lo stato dell'ODL
type ODLStatus = 'Preparazione' | 'Laminazione' | 'In Coda' | 'Attesa Cura' | 'Cura' | 'Finito';

interface ODLStatusInfo {
  status: ODLStatus;
  label: string;
  description: string;
  color: string;
  icon: React.ComponentType<{ className?: string }>;
  canTransitionTo: ODLStatus[];
}

// Configurazione stati ODL
const ODL_STATUS_CONFIG: Record<ODLStatus, ODLStatusInfo> = {
  'Preparazione': {
    status: 'Preparazione',
    label: 'Preparazione',
    description: 'ODL in fase di preparazione iniziale',
    color: 'bg-gray-100 text-gray-800 border-gray-300',
    icon: Settings,
    canTransitionTo: ['Laminazione']
  },
  'Laminazione': {
    status: 'Laminazione',
    label: 'Laminazione',
    description: 'ODL in fase di laminazione',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: Package,
    canTransitionTo: ['In Coda']
  },
  'In Coda': {
    status: 'In Coda',
    label: 'In Coda',
    description: 'ODL in coda per la cura',
    color: 'bg-purple-100 text-purple-800 border-purple-300',
    icon: Clock,
    canTransitionTo: ['Attesa Cura']
  },
  'Attesa Cura': {
    status: 'Attesa Cura',
    label: 'Attesa Cura',
    description: 'ODL pronto per il caricamento in autoclave',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    icon: Clock,
    canTransitionTo: ['Cura']
  },
  'Cura': {
    status: 'Cura',
    label: 'Cura',
    description: 'ODL in fase di cura nell\'autoclave',
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: PlayCircle,
    canTransitionTo: ['Finito']
  },
  'Finito': {
    status: 'Finito',
    label: 'Finito',
    description: 'ODL completato con successo',
    color: 'bg-green-100 text-green-800 border-green-300',
    icon: CheckCircle,
    canTransitionTo: []
  }
};

interface ODLInfo {
  id: number;
  status: ODLStatus;
  parte: {
    part_number: string;
    descrizione_breve: string;
  };
  tool: {
    part_number_tool: string;
    descrizione?: string;
  };
  priorita: number;
  note?: string;
}

interface ODLStatusSwitchProps {
  /** Lista degli ODL da gestire */
  odlList: ODLInfo[];
  /** Callback chiamato quando lo stato di un ODL cambia */
  onStatusChanged?: (odlId: number, newStatus: ODLStatus) => void;
  /** Informazioni utente per audit */
  userInfo?: {
    userId: string;
    userRole: string;
  };
  /** Modalità read-only per visualizzazione */
  readOnly?: boolean;
  /** Mostra tutti gli ODL o solo quelli modificabili */
  showAll?: boolean;
}

export default function ODLStatusSwitch({
  odlList,
  onStatusChanged,
  userInfo = { userId: 'utente_frontend', userRole: 'Curing' },
  readOnly = false,
  showAll = true
}: ODLStatusSwitchProps) {
  
  const [loadingOdl, setLoadingOdl] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedOdl, setExpandedOdl] = useState<Set<number>>(new Set());
  const [confirmationOdl, setConfirmationOdl] = useState<{
    odlId: number;
    newStatus: ODLStatus;
  } | null>(null);

  // Filtra ODL se necessario
  const filteredOdlList = showAll 
    ? odlList 
    : odlList.filter(odl => ODL_STATUS_CONFIG[odl.status].canTransitionTo.length > 0);

  // Funzione per gestire il cambio di stato di un ODL
  const handleODLStatusChange = async (odlId: number, newStatus: ODLStatus) => {
    const odl = odlList.find(o => o.id === odlId);
    if (!odl) return;

    const currentConfig = ODL_STATUS_CONFIG[odl.status];
    
    // Verifica se la transizione è consentita
    if (!currentConfig.canTransitionTo.includes(newStatus)) {
      setError(`Transizione da ${currentConfig.label} a ${ODL_STATUS_CONFIG[newStatus].label} non consentita per ODL ${odlId}`);
      return;
    }

    setLoadingOdl(odlId);
    setError(null);

    try {
      console.log(`🔄 Aggiornando ODL ${odlId} da ${odl.status} a ${newStatus}...`);
      
      await odlApi.updateStatus(
        odlId,
        newStatus
      );

      console.log(`✅ ODL ${odlId} aggiornato a stato: ${newStatus}`);

      // Notifica il parent component
      if (onStatusChanged) {
        onStatusChanged(odlId, newStatus);
      }

      setConfirmationOdl(null);

    } catch (err: any) {
      console.error(`❌ Errore nel cambio stato ODL ${odlId}:`, err);
      setError(err.message || 'Errore durante il cambio di stato');
    } finally {
      setLoadingOdl(null);
    }
  };

  // Funzione per aprire la conferma
  const requestODLStatusChange = (odlId: number, newStatus: ODLStatus) => {
    setConfirmationOdl({ odlId, newStatus });
    setError(null);
  };

  // Funzione per annullare la conferma
  const cancelODLStatusChange = () => {
    setConfirmationOdl(null);
    setError(null);
  };

  // Funzione per espandere/comprimere un ODL
  const toggleODLExpansion = (odlId: number) => {
    const newExpanded = new Set(expandedOdl);
    if (newExpanded.has(odlId)) {
      newExpanded.delete(odlId);
    } else {
      newExpanded.add(odlId);
    }
    setExpandedOdl(newExpanded);
  };

  // Raggruppa ODL per stato
  const groupedOdlByStatus = filteredOdlList.reduce((acc, odl) => {
    if (!acc[odl.status]) {
      acc[odl.status] = [];
    }
    acc[odl.status].push(odl);
    return acc;
  }, {} as Record<ODLStatus, ODLInfo[]>);

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Package className="h-5 w-5" />
          Controllo Stato ODL ({filteredOdlList.length} ODL)
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Errori Globali */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Nessun ODL */}
        {filteredOdlList.length === 0 && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              {showAll 
                ? 'Nessun ODL presente nel batch' 
                : 'Nessun ODL con azioni disponibili'
              }
            </AlertDescription>
          </Alert>
        )}

        {/* Lista ODL raggruppati per stato */}
        {Object.entries(groupedOdlByStatus).map(([status, odls]) => {
          const statusConfig = ODL_STATUS_CONFIG[status as ODLStatus];
          const StatusIcon = statusConfig.icon;

          return (
            <div key={status} className="border rounded-lg overflow-hidden">
              {/* Header Gruppo */}
              <div className="bg-gray-50 p-3 border-b">
                <div className="flex items-center gap-2">
                  <StatusIcon className="h-4 w-4" />
                  <Badge className={`${statusConfig.color} px-2 py-1`}>
                    {statusConfig.label}
                  </Badge>
                  <span className="text-sm text-gray-600">({odls.length} ODL)</span>
                </div>
              </div>

              {/* Lista ODL in questo stato */}
              <div className="divide-y">
                {odls.map(odl => {
                  const isExpanded = expandedOdl.has(odl.id);
                  const isLoading = loadingOdl === odl.id;
                  const canTransition = statusConfig.canTransitionTo.length > 0;

                  return (
                    <div key={odl.id} className="p-3">
                      {/* Header ODL */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleODLExpansion(odl.id)}
                            className="p-0 h-auto"
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                          
                          <div>
                            <div className="font-medium">ODL #{odl.id}</div>
                            <div className="text-sm text-gray-600">
                              {odl.parte.part_number} - {odl.parte.descrizione_breve}
                            </div>
                          </div>
                        </div>

                        {/* Priorità */}
                        <Badge variant="outline" className="text-xs">
                          Priorità {odl.priorita}
                        </Badge>
                      </div>

                      {/* Dettagli Espansi */}
                      {isExpanded && (
                        <div className="mt-3 space-y-3 pl-7">
                          {/* Informazioni Tool */}
                          <div className="text-sm">
                            <div className="font-medium mb-1">Tool:</div>
                            <div className="text-gray-600">
                              {odl.tool.part_number_tool}
                              {odl.tool.descrizione && ` - ${odl.tool.descrizione}`}
                            </div>
                          </div>

                          {/* Note */}
                          {odl.note && (
                            <div className="text-sm">
                              <div className="font-medium mb-1">Note:</div>
                              <div className="text-gray-600">{odl.note}</div>
                            </div>
                          )}

                          {/* Azioni di Transizione */}
                          {!readOnly && canTransition && (
                            <div className="space-y-2">
                              <div className="font-medium text-sm">Azioni Disponibili:</div>
                              
                              {statusConfig.canTransitionTo.map(nextStatus => {
                                const nextConfig = ODL_STATUS_CONFIG[nextStatus];
                                const NextIcon = nextConfig.icon;
                                
                                return (
                                  <div key={nextStatus} className="flex items-center justify-between p-2 border rounded">
                                    <div className="flex items-center gap-2">
                                      <NextIcon className="h-4 w-4 text-gray-600" />
                                      <span className="text-sm">{nextConfig.label}</span>
                                    </div>
                                    
                                    <Button 
                                      onClick={() => requestODLStatusChange(odl.id, nextStatus)}
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

                          {/* Read-Only Message */}
                          {readOnly && (
                            <Alert>
                              <Info className="h-4 w-4" />
                              <AlertDescription className="text-sm">
                                Visualizzazione in sola lettura
                              </AlertDescription>
                            </Alert>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Modal di Conferma */}
        {confirmationOdl && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md mx-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Conferma Cambio Stato ODL
                </CardTitle>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {(() => {
                  const odl = odlList.find(o => o.id === confirmationOdl.odlId);
                  const currentConfig = odl ? ODL_STATUS_CONFIG[odl.status] : null;
                  const newConfig = ODL_STATUS_CONFIG[confirmationOdl.newStatus];
                  
                  return (
                    <>
                      <div className="text-sm">
                        Vuoi cambiare lo stato dell'ODL #{confirmationOdl.odlId} da{' '}
                        {currentConfig && (
                          <Badge className={currentConfig.color}>{currentConfig.label}</Badge>
                        )}
                        {' '}a{' '}
                        <Badge className={newConfig.color}>{newConfig.label}</Badge>
                        ?
                      </div>

                      {odl && (
                        <div className="text-sm bg-gray-50 p-2 rounded">
                          <div><strong>Part Number:</strong> {odl.parte.part_number}</div>
                          <div><strong>Descrizione:</strong> {odl.parte.descrizione_breve}</div>
                        </div>
                      )}

                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription className="text-sm">
                          {newConfig.description}
                        </AlertDescription>
                      </Alert>

                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          onClick={cancelODLStatusChange}
                          disabled={loadingOdl !== null}
                        >
                          Annulla
                        </Button>
                        <Button
                          onClick={() => handleODLStatusChange(confirmationOdl.odlId, confirmationOdl.newStatus)}
                          disabled={loadingOdl !== null}
                        >
                          {loadingOdl !== null ? (
                            <Loader2 className="h-4 w-4 animate-spin mr-1" />
                          ) : (
                            <CheckCircle className="h-4 w-4 mr-1" />
                          )}
                          Conferma
                        </Button>
                      </div>
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 