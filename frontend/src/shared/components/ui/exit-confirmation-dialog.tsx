import React from 'react'
import { AlertCircle, Clock, Save, Trash2 } from 'lucide-react'
import { Button } from './button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './dialog'
import { Badge } from './badge'

interface ExitConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  draftCount: number
  onConfirmExit: () => void
  onSaveAll?: () => void
  onDeleteAll?: () => void
  isProcessing?: boolean
}

export function ExitConfirmationDialog({
  open,
  onOpenChange,
  draftCount,
  onConfirmExit,
  onSaveAll,
  onDeleteAll,
  isProcessing = false
}: ExitConfirmationDialogProps) {
  if (draftCount === 0) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
              <AlertCircle className="h-6 w-6 text-amber-600" />
            </div>
            <div className="flex-1">
              <DialogTitle className="text-xl font-semibold">
                Conferma Uscita
              </DialogTitle>
              <DialogDescription className="text-base mt-1">
                Attenzione! Hai bozze non salvate che verranno perse.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {/* Draft Count Badge */}
          <div className="flex items-center justify-center">
            <Badge variant="outline" className="text-amber-600 border-amber-300 py-2 px-4">
              <Clock className="h-4 w-4 mr-2" />
              {draftCount} {draftCount === 1 ? 'bozza non salvata' : 'bozze non salvate'}
            </Badge>
          </div>

          {/* Warning Message */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex gap-3">
              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-amber-800">
                <p className="font-medium mb-1">Cosa succederà:</p>
                <ul className="space-y-1 text-amber-700">
                  <li>• Le bozze verranno eliminate automaticamente</li>
                  <li>• I dati di configurazione non salvati andranno persi</li>
                  <li>• Dovrai rigenerare i batch se necessario</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Action Options */}
          <div className="text-sm text-gray-600">
            <p className="font-medium mb-2">Opzioni disponibili:</p>
            <div className="space-y-2">
              {onSaveAll && (
                <div className="flex items-center gap-2 text-green-700">
                  <Save className="h-4 w-4" />
                  <span>Salva tutte le bozze prima di uscire</span>
                </div>
              )}
              {onDeleteAll && (
                <div className="flex items-center gap-2 text-red-700">
                  <Trash2 className="h-4 w-4" />
                  <span>Elimina tutte le bozze ed esci</span>
                </div>
              )}
              <div className="flex items-center gap-2 text-gray-700">
                <AlertCircle className="h-4 w-4" />
                <span>Annulla e torna alla gestione batch</span>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isProcessing}
            className="w-full sm:w-auto order-last sm:order-first"
          >
            Annulla
          </Button>
          
          <div className="flex gap-2 w-full sm:w-auto">
            {onSaveAll && (
              <Button
                onClick={onSaveAll}
                disabled={isProcessing}
                className="flex-1 sm:flex-none bg-green-600 hover:bg-green-700"
              >
                <Save className="h-4 w-4 mr-2" />
                Salva Tutto
              </Button>
            )}
            
            <Button
              variant="destructive"
              onClick={onConfirmExit}
              disabled={isProcessing}
              className="flex-1 sm:flex-none"
            >
              <AlertCircle className="h-4 w-4 mr-2" />
              Esci Comunque
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 