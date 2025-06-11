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
import { Badge } from '@/shared/components/ui/badge'
import { 
  AlertTriangle, 
  Save,
  LogOut,
  Loader2,
  Clock,
  Package,
  FileX
} from 'lucide-react'

interface DraftBatch {
  id: string
  nome: string
  autoclave?: {
    nome: string
    codice: string
  }
  autoclave_id?: number | null
  metrics?: {
    efficiency_percentage: number
    positioned_tools: number
  }
}

interface ExitPageDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  draftBatches: DraftBatch[]
  isSaving: boolean
  onSaveAndExit: () => void
  onExitWithoutSaving: () => void
  onStayOnPage: () => void
}

export function ExitPageDialog({
  open,
  onOpenChange,
  draftBatches,
  isSaving,
  onSaveAndExit,
  onExitWithoutSaving,
  onStayOnPage
}: ExitPageDialogProps) {
  const draftCount = draftBatches.length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
            Uscita dalla Pagina
          </DialogTitle>
          <DialogDescription>
            Hai {draftCount} bozz{draftCount === 1 ? 'a' : 'e'} non salvat{draftCount === 1 ? 'a' : 'e'} che {draftCount === 1 ? 'andrà persa' : 'andranno perse'} se esci dalla pagina.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Avviso principale */}
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <FileX className="h-4 w-4 text-amber-600" />
              <p className="text-sm font-medium text-amber-800">
                Attenzione: Bozze non salvate
              </p>
            </div>
            <p className="text-sm text-amber-700">
              Uscendo da questa pagina, tutte le bozze generate andranno perse definitivamente.
            </p>
          </div>

          {/* Lista bozze a rischio */}
          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Package className="h-4 w-4" />
              Bozze a rischio ({draftCount}):
            </h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {draftBatches.map((batch) => (
                <div key={batch.id} className="flex items-center justify-between text-sm bg-white p-2 rounded border">
                  <div>
                    <p className="font-mono text-xs text-muted-foreground">{batch.nome}</p>
                    <p className="text-xs text-muted-foreground">
                      {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge variant="outline" className="text-xs">
                      <Clock className="h-3 w-3 mr-1" />
                      Draft
                    </Badge>
                    {batch.metrics && (
                      <Badge variant="secondary" className="text-xs">
                        {batch.metrics.efficiency_percentage.toFixed(1)}%
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Opzioni */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 mb-2">
              <strong>Opzioni disponibili:</strong>
            </p>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• <strong>Salva e Esci:</strong> Promuove tutte le bozze a "Sospeso" e poi esce</li>
              <li>• <strong>Rimani:</strong> Rimane nella pagina per gestire le bozze</li>
              <li>• <strong>Esci Senza Salvare:</strong> Elimina le bozze ed esce dalla pagina</li>
            </ul>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button 
            variant="outline" 
            onClick={onStayOnPage}
            disabled={isSaving}
          >
            Rimani
          </Button>
          
          <Button 
            variant="destructive"
            onClick={onExitWithoutSaving}
            disabled={isSaving}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Esci Senza Salvare
          </Button>
          
          <Button 
            onClick={onSaveAndExit}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Salvataggio...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Salva e Esci
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 