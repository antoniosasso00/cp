import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/components/ui/dialog'
import { Button } from '@/shared/components/ui/button'
import { 
  AlertCircle, 
  CheckCircle,
  Loader2,
  Save,
  Trash2,
  Clock,
  Package
} from 'lucide-react'

interface BatchData {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: {
    nome: string
    codice: string
    lunghezza: number
    larghezza_piano: number
  }
  configurazione_json?: any
  metrics?: {
    efficiency_percentage: number
    total_weight_kg: number
    positioned_tools: number
    excluded_tools: number
  }
  created_at: string
  updated_at: string
}

interface DraftActionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  batch: BatchData | null
  action: 'save' | 'delete' | null
  isProcessing: boolean
  onConfirm: () => void
}

export function DraftActionDialog({
  open,
  onOpenChange,
  batch,
  action,
  isProcessing,
  onConfirm
}: DraftActionDialogProps) {
  if (!batch || !action) return null

  const isSaveAction = action === 'save'
  const isDeleteAction = action === 'delete'

  const getActionInfo = () => {
    if (isSaveAction) {
      return {
        title: 'Salva Bozza',
        description: `Stai per salvare la bozza "${batch.nome}" e promuoverla a stato "Sospeso".`,
        icon: <Save className="h-5 w-5 text-green-600" />,
        buttonText: 'Salva Bozza',
        buttonVariant: 'default' as const,
        buttonIcon: <CheckCircle className="mr-2 h-4 w-4" />,
        infoText: 'La bozza sarà promossa a "Sospeso" e sarà disponibile per la conferma.',
        infoClass: 'bg-green-50 border-green-200 text-green-800'
      }
    } else {
      return {
        title: 'Elimina Bozza',
        description: `Stai per eliminare definitivamente la bozza "${batch.nome}".`,
        icon: <AlertCircle className="h-5 w-5 text-red-600" />,
        buttonText: 'Elimina Bozza',
        buttonVariant: 'destructive' as const,
        buttonIcon: <Trash2 className="mr-2 h-4 w-4" />,
        infoText: 'Questa operazione è irreversibile. La bozza sarà eliminata permanentemente.',
        infoClass: 'bg-red-50 border-red-200 text-red-800'
      }
    }
  }

  const actionInfo = getActionInfo()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {actionInfo.icon}
            {actionInfo.title}
          </DialogTitle>
          <DialogDescription>
            {actionInfo.description}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Dettagli Batch */}
          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Package className="h-4 w-4" />
              Dettagli Batch:
            </h4>
            <div className="space-y-1 text-sm">
              <p><strong>Nome:</strong> {batch.nome}</p>
              <p><strong>Autoclave:</strong> {batch.autoclave?.nome || `ID ${batch.autoclave_id}`}</p>
              <p>
                <strong>Dimensioni Piano:</strong>{' '}
                {batch.autoclave ? 
                  `${batch.autoclave.lunghezza} × ${batch.autoclave.larghezza_piano} mm` : 
                  'Non disponibili'
                }
              </p>
              {batch.metrics && (
                <>
                  <p><strong>Efficienza:</strong> {batch.metrics.efficiency_percentage.toFixed(1)}%</p>
                  <p><strong>Tool Posizionati:</strong> {batch.metrics.positioned_tools}</p>
                  <p><strong>Peso Totale:</strong> {batch.metrics.total_weight_kg.toFixed(1)} kg</p>
                </>
              )}
            </div>
          </div>
          
          {/* Info Operazione */}
          <div className={`p-4 rounded-lg border ${actionInfo.infoClass}`}>
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4" />
              <p className="text-sm font-medium">
                {isSaveAction ? 'Promozione batch' : 'Attenzione: Operazione irreversibile'}
              </p>
            </div>
            <p className="text-sm">
              {actionInfo.infoText}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={isProcessing}
          >
            Annulla
          </Button>
          <Button 
            variant={actionInfo.buttonVariant}
            onClick={onConfirm}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {isSaveAction ? 'Salvataggio...' : 'Eliminazione...'}
              </>
            ) : (
              <>
                {actionInfo.buttonIcon}
                {actionInfo.buttonText}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 