'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/ui/use-toast'
import { nestingApi, NestingResponse } from '@/lib/api'
import { useUserRole } from '@/hooks/useUserRole'
import { 
  MoreHorizontal, 
  CheckCircle, 
  XCircle, 
  Package, 
  Edit,
  Loader2,
  Trash2
} from 'lucide-react'

interface NestingActionsProps {
  nesting: NestingResponse
  onUpdate: () => void
}

export function NestingActions({ nesting, onUpdate }: NestingActionsProps) {
  const { role } = useUserRole()
  const { toast } = useToast()
  
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedAction, setSelectedAction] = useState<{
    type: 'confirm' | 'complete' | 'cancel' | 'confirm_pending' | 'delete_pending'
    title: string
    description: string
    newState?: string
  } | null>(null)
  const [note, setNote] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Determina le azioni disponibili in base al ruolo e allo stato del nesting
  const getAvailableActions = () => {
    if (role === 'Curing') {
      // L'operatore Curing può solo confermare o eliminare nesting in sospeso
      if (nesting.stato === 'In sospeso') {
        return [
          {
            type: 'confirm_pending' as const,
            title: 'Conferma Nesting',
            description: 'Conferma il nesting e avvia il processo di cura',
            icon: CheckCircle,
            color: 'text-green-600'
          },
          {
            type: 'delete_pending' as const,
            title: 'Elimina',
            description: 'Elimina il nesting e rilascia gli ODL',
            icon: Trash2,
            color: 'text-red-600'
          }
        ]
      }
      return []
    } else if (role === 'Management') {
      // Il management può modificare qualsiasi nesting non completato
      if (nesting.stato === 'In sospeso' || nesting.stato === 'SOSPESO') {
        return [
          {
            type: 'confirm' as const,
            title: 'Conferma Nesting',
            description: 'Conferma questo nesting per la produzione',
            newState: 'Confermato',
            icon: CheckCircle,
            color: 'text-blue-600'
          },
          {
            type: 'complete' as const,
            title: 'Completa Nesting',
            description: 'Segna questo nesting come completato',
            newState: 'Completato',
            icon: Package,
            color: 'text-green-600'
          },
          {
            type: 'cancel' as const,
            title: 'Annulla Nesting',
            description: 'Annulla questo nesting e riporta gli ODL in attesa',
            newState: 'Annullato',
            icon: XCircle,
            color: 'text-red-600'
          }
        ]
      }
    }
    return []
  }

  const availableActions = getAvailableActions()

  const handleActionClick = (action: typeof availableActions[0]) => {
    setSelectedAction({
      type: action.type,
      title: action.title,
      description: action.description,
      newState: 'newState' in action ? action.newState : undefined
    })
    setNote('')
    setIsDialogOpen(true)
  }

  const handleConfirmAction = async () => {
    if (!selectedAction) return

    setIsLoading(true)
    try {
      // Gestione delle nuove azioni specifiche per nesting in sospeso
      if (selectedAction.type === 'confirm_pending') {
        await nestingApi.confirmPending(nesting.id)
        toast({
          title: 'Nesting Confermato',
          description: `Nesting #${nesting.id} confermato con successo. Il processo di cura è iniziato.`,
        })
      } else if (selectedAction.type === 'delete_pending') {
        await nestingApi.deletePending(nesting.id)
        toast({
          title: 'Nesting Eliminato',
          description: `Nesting #${nesting.id} eliminato con successo. Gli ODL sono tornati in attesa di cura.`,
        })
      } else if (selectedAction.newState) {
        // Gestione delle azioni tradizionali
        await nestingApi.updateStatus(
          nesting.id, 
          selectedAction.newState, 
          note || undefined,
          role || undefined
        )
        toast({
          title: 'Azione completata',
          description: `Nesting #${nesting.id} aggiornato a "${selectedAction.newState}"`,
        })
      }

      onUpdate()
      setIsDialogOpen(false)
      setSelectedAction(null)
      setNote('')
    } catch (error) {
      console.error('Errore nell\'operazione sul nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile completare l\'operazione. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Se non ci sono azioni disponibili, non mostrare il menu
  if (availableActions.length === 0) {
    return null
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
            <span className="sr-only">Azioni nesting #{nesting.id}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {availableActions.map((action, index) => {
            const IconComponent = action.icon
            return (
              <DropdownMenuItem
                key={action.type}
                onClick={() => handleActionClick(action)}
                className={`${action.color} cursor-pointer`}
              >
                <IconComponent className="h-4 w-4 mr-2" />
                {action.title}
              </DropdownMenuItem>
            )
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedAction?.title}</DialogTitle>
            <DialogDescription>
              {selectedAction?.description}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Note (opzionale)
              </label>
              <Textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Aggiungi note per questa azione..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsDialogOpen(false)}
              disabled={isLoading}
            >
              Annulla
            </Button>
            <Button 
              onClick={handleConfirmAction}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Aggiornamento...
                </>
              ) : (
                'Conferma'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
} 