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
  Loader2
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
    type: 'confirm' | 'complete' | 'cancel'
    title: string
    description: string
    newState: string
  } | null>(null)
  const [note, setNote] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Determina le azioni disponibili in base al ruolo e allo stato
  const getAvailableActions = () => {
    const actions = []

    if (role === 'AUTOCLAVISTA') {
      // L'autoclavista può solo confermare o annullare nesting in sospeso
      if (nesting.stato === 'In sospeso') {
        actions.push({
          type: 'confirm' as const,
          title: 'Conferma Carico',
          description: 'Conferma che il carico è stato inserito nell\'autoclave',
          newState: 'Confermato',
          icon: CheckCircle,
          color: 'text-blue-600'
        })
        actions.push({
          type: 'cancel' as const,
          title: 'Annulla Nesting',
          description: 'Annulla questo nesting e riporta gli ODL in attesa',
          newState: 'Annullato',
          icon: XCircle,
          color: 'text-red-600'
        })
      }
    } else if (role === 'RESPONSABILE') {
      // Il responsabile può modificare qualsiasi nesting non completato
      if (nesting.stato === 'In sospeso') {
        actions.push({
          type: 'confirm' as const,
          title: 'Conferma Nesting',
          description: 'Conferma questo nesting per la produzione',
          newState: 'Confermato',
          icon: CheckCircle,
          color: 'text-blue-600'
        })
      }
      
      if (nesting.stato === 'Confermato') {
        actions.push({
          type: 'complete' as const,
          title: 'Completa Nesting',
          description: 'Segna questo nesting come completato',
          newState: 'Completato',
          icon: Package,
          color: 'text-green-600'
        })
      }
      
      if (nesting.stato !== 'Completato') {
        actions.push({
          type: 'cancel' as const,
          title: 'Annulla Nesting',
          description: 'Annulla questo nesting e riporta gli ODL in attesa',
          newState: 'Annullato',
          icon: XCircle,
          color: 'text-red-600'
        })
      }
    }

    return actions
  }

  const availableActions = getAvailableActions()

  const handleActionClick = (action: typeof availableActions[0]) => {
    setSelectedAction({
      type: action.type,
      title: action.title,
      description: action.description,
      newState: action.newState
    })
    setNote('')
    setIsDialogOpen(true)
  }

  const handleConfirmAction = async () => {
    if (!selectedAction) return

    setIsLoading(true)
    try {
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

      onUpdate()
      setIsDialogOpen(false)
      setSelectedAction(null)
      setNote('')
    } catch (error) {
      console.error('Errore nell\'aggiornamento del nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile aggiornare il nesting. Riprova più tardi.',
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