'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Tool, ParteResponse, ODLResponse, ODLCreate, ODLUpdate, odlApi, toolsApi, partsApi } from '@/lib/api'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Loader2, AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { FormField, FormSelect, FormWrapper, SelectOption } from '@/shared/components/form'
import { odlSchema, ODLFormValues, odlDefaultValues, statusOptions } from '../schema'

type ODLModalProps = {
  isOpen: boolean
  onClose: () => void
  item: ODLResponse | null
  onSuccess: () => void
}

const ODLModal = ({ isOpen, onClose, item, onSuccess }: ODLModalProps) => {
  const { toast } = useStandardToast()
  const [tools, setTools] = useState<Tool[]>([])
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [filteredTools, setFilteredTools] = useState<Tool[]>([])
  const [selectedParte, setSelectedParte] = useState<ParteResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
  const form = useForm<ODLFormValues>({
    resolver: zodResolver(odlSchema),
    defaultValues: odlDefaultValues,
  })

  useEffect(() => {
    if (isOpen) {
      loadDependencies()
      
      // Se stiamo modificando, prendiamo i dati esistenti
      if (item) {
        form.reset({
          numero_odl: item.numero_odl,
          parte_id: item.parte_id,
          tool_id: item.tool_id,
          priorita: item.priorita,
          status: item.status,
          note: item.note || ""
        })
      } else {
        // Reset form per nuova creazione
        form.reset(odlDefaultValues)
        setSelectedParte(null)
        setFilteredTools([])
      }
    }
  }, [isOpen, item, form])

  // Aggiorna i tool filtrati quando cambia la parte selezionata
  useEffect(() => {
    const parteId = form.watch('parte_id')
    if (parteId && parti.length > 0) {
      const parte = parti.find(p => p.id === parteId)
      setSelectedParte(parte || null)
      
      if (parte) {
        // Filtra i tool associati alla parte selezionata
        const parteTools = parte.tools || []
        const toolIds = parteTools.map(t => t.id)
        const filtered = tools.filter(tool => toolIds.includes(tool.id))
        setFilteredTools(filtered)
        
        // Se il tool attualmente selezionato non è nella lista filtrata, lo resettiamo
        const currentToolId = form.watch('tool_id')
        if (currentToolId && currentToolId !== 0 && !toolIds.includes(currentToolId)) {
          form.setValue('tool_id', 0)
        }
        
        // ✅ AUTO-SELEZIONE: Se c'è solo un tool disponibile, selezionalo automaticamente
        if (filtered.length === 1 && (currentToolId === 0 || !currentToolId)) {
          form.setValue('tool_id', filtered[0].id)
        }
      } else {
        setFilteredTools([])
      }
    } else {
      setFilteredTools([])
      setSelectedParte(null)
    }
  }, [form.watch('parte_id'), parti, tools, form])

  const loadDependencies = async () => {
    try {
      setIsLoading(true)
      const [toolsData, partiData] = await Promise.all([
        toolsApi.fetchTools(),
        partsApi.fetchParts()
      ])
      setTools(toolsData)
      setParti(partiData)
    } catch (error) {
      console.error('Errore nel caricamento delle dipendenze:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati necessari. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const onSubmit = async (data: ODLFormValues) => {
    try {
      setIsSaving(true)
      
      if (item) {
        // Aggiornamento
        await odlApi.updateODL(item.id, data)
        toast({
          variant: 'success',
          title: 'ODL aggiornato',
          description: `ODL #${item.id} aggiornato con successo.`,
        })
      } else {
        // Creazione
        await odlApi.createODL(data as ODLCreate)
        toast({
          variant: 'success',
          title: 'ODL creato',
          description: 'Nuovo ODL creato con successo.',
        })
      }
      
      onSuccess()
      onClose()
    } catch (error) {
      console.error('Errore nel salvataggio dell\'ODL:', error)
      
      // Gestione errore 409 per numero ODL duplicato
      if (error instanceof Error && error.message.includes('409')) {
        toast({
          variant: 'destructive',
          title: 'Numero ODL già presente',
          description: 'Il numero ODL inserito è già utilizzato. Inserisci un valore diverso.',
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore',
          description: 'Impossibile salvare l\'ODL. Verifica i dati e riprova.',
        })
      }
    } finally {
      setIsSaving(false)
    }
  }

  // ✅ FIX: Funzione "Salva e Nuovo" - reset form e mantiene dialog aperto
  const handleSaveAndNew = async (data: ODLFormValues) => {
    try {
      setIsSaving(true)
      
      // Solo in modalità creazione (non aggiornamento)
      await odlApi.createODL(data as ODLCreate)
      
      // Reset del form PRIMA del toast per evitare interferenze
      form.reset(odlDefaultValues)
      
      toast({
        variant: 'success',
        title: 'Creato e pronto per il prossimo',
        description: `ODL ${data.numero_odl} creato con successo. Form resettato per un nuovo inserimento.`,
      })
      
      // Focus immediato sul primo campo
      setTimeout(() => {
        const numeroOdlInput = document.querySelector('input[name="numero_odl"]') as HTMLInputElement
        if (numeroOdlInput) {
          numeroOdlInput.focus()
        }
      }, 50)
      
      // NON chiamare onSuccess() o onClose() per mantenere il dialog aperto
      
    } catch (error) {
      console.error('Errore nel salvataggio dell\'ODL:', error)
      
      // Gestione errore 409 per numero ODL duplicato
      if (error instanceof Error && error.message.includes('409')) {
        toast({
          variant: 'destructive',
          title: 'Numero ODL già presente',
          description: 'Il numero ODL inserito è già utilizzato. Inserisci un valore diverso.',
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore',
          description: 'Impossibile salvare l\'ODL. Verifica i dati e riprova.',
        })
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleCreateNewTool = () => {
    window.open('/dashboard/tools/new', '_blank')
  }

  const handleCreateNewPart = () => {
    window.open('/dashboard/parts/new', '_blank')
  }

  // Prepara le opzioni per i select
  const partiOptions: SelectOption[] = parti
    .filter(parte => parte?.id && parte?.part_number)
    .map(parte => ({
      value: parte.id,
      label: `${parte.part_number} - ${parte.descrizione_breve}`
    }))

  const toolOptions: SelectOption[] = filteredTools
    .filter(tool => tool?.id && tool?.part_number_tool)
    .map(tool => ({
      value: tool.id,
      label: `${tool.part_number_tool}${tool.descrizione ? ` - ${tool.descrizione}` : ''}`
    }))

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {item 
              ? `Modifica ODL - ${item.parte.part_number}` 
              : 'Crea nuovo ODL'
            }
          </DialogTitle>
          <DialogDescription>
            {item 
              ? `Modifica i dettagli dell'ordine di lavoro per ${item.parte.descrizione_breve}` 
              : 'Inserisci i dettagli per creare un nuovo ordine di lavoro'}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Caricamento in corso...</span>
          </div>
        ) : (
          <FormWrapper
            form={form}
            onSubmit={onSubmit}
            isLoading={isSaving}
            submitText={item ? "Aggiorna ODL" : "Crea ODL"}
            showCancel={true}
            onCancel={onClose}
            cardClassName="border-0 shadow-none"
            headerClassName="hidden"
            showSaveAndNew={!item}
            onSaveAndNew={handleSaveAndNew}
            saveAndNewText="Salva e Nuovo"
          >
            <FormField
              label="Numero ODL"
              name="numero_odl"
              type="text"
              value={form.watch('numero_odl')}
              onChange={(value) => form.setValue('numero_odl', value as string)}
              placeholder="es. 2024001"
              required
              error={form.formState.errors.numero_odl?.message}
              description="Numero identificativo univoco dell'ODL"
            />

            <FormSelect
              label="Parte"
              name="parte_id"
              value={form.watch('parte_id')}
              onChange={(value) => form.setValue('parte_id', value as number)}
              options={partiOptions}
              placeholder="Seleziona una parte"
              required
              error={form.formState.errors.parte_id?.message}
              emptyMessage="Nessuna parte disponibile"
            />

            {partiOptions.length === 0 && (
              <div className="flex justify-end">
                <Button 
                  type="button"
                  variant="outline" 
                  size="sm" 
                  onClick={handleCreateNewPart}
                >
                  + Crea nuova parte
                </Button>
              </div>
            )}

            {/* Descrizione della parte selezionata */}
            {selectedParte && (
              <div className="p-3 bg-muted rounded-md">
                <p className="text-sm font-medium">Descrizione parte:</p>
                <p className="text-sm text-muted-foreground">{selectedParte.descrizione_breve}</p>
              </div>
            )}

            <FormSelect
              label="Tool"
              name="tool_id"
              value={form.watch('tool_id')}
              onChange={(value) => form.setValue('tool_id', value as number)}
              options={toolOptions}
              placeholder="Seleziona un tool"
              required
              disabled={!form.watch('parte_id') || toolOptions.length === 0}
              error={form.formState.errors.tool_id?.message}
              emptyMessage={
                form.watch('parte_id') && form.watch('parte_id') > 0 
                  ? "Nessun tool disponibile per questa parte" 
                  : "Seleziona prima una parte"
              }
            />

            {selectedParte && toolOptions.length === 0 && (
              <>
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Nessun tool associato alla parte selezionata
                  </AlertDescription>
                </Alert>
                <div className="flex justify-end">
                  <Button 
                    type="button"
                    variant="outline" 
                    size="sm" 
                    onClick={handleCreateNewTool}
                  >
                    + Crea nuovo tool
                  </Button>
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <FormField
                label="Priorità"
                name="priorita"
                type="number"
                value={form.watch('priorita')}
                onChange={(value) => form.setValue('priorita', value as number)}
                min={1}
                max={10}
                required
                error={form.formState.errors.priorita?.message}
                description="Da 1 (bassa) a 10 (alta)"
              />

              <FormSelect
                label="Stato"
                name="status"
                value={form.watch('status')}
                onChange={(value) => form.setValue('status', value as any)}
                options={statusOptions}
                required
                error={form.formState.errors.status?.message}
              />
            </div>

            <FormField
              label="Note"
              name="note"
              type="textarea"
              value={form.watch('note')}
              onChange={(value) => form.setValue('note', value as string)}
              placeholder="Note aggiuntive (opzionale)"
              rows={3}
              error={form.formState.errors.note?.message}
            />
          </FormWrapper>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default ODLModal 