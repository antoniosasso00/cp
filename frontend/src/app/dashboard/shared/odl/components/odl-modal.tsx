'use client'

import { useState, useEffect, useTransition } from 'react'
import { Tool, ParteResponse, ODLResponse, ODLCreate, ODLUpdate, odlApi, toolApi, partiApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Loader2, AlertTriangle, Plus } from 'lucide-react'
import { cn } from "@/lib/utils"
import { Alert, AlertDescription } from '@/components/ui/alert'
import React from 'react'
import { useRouter } from 'next/navigation'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

type ODLModalProps = {
  isOpen: boolean
  onClose: () => void
  item: ODLResponse | null
  onSuccess: () => void
}

const ODLModal = ({ isOpen, onClose, item, onSuccess }: ODLModalProps) => {
  const { toast } = useToast()
  const router = useRouter()
  const [tools, setTools] = useState<Tool[]>([])
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [filteredTools, setFilteredTools] = useState<Tool[]>([])
  const [selectedParte, setSelectedParte] = useState<ParteResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isPending, startTransition] = useTransition()
  
  // Form state
  const [formData, setFormData] = useState<ODLCreate | ODLUpdate>({
    parte_id: 0,
    tool_id: 0,
    priorita: 1,
    status: "Preparazione",
    note: ""
  })

  useEffect(() => {
    if (isOpen) {
      loadDependencies()
      
      // Se stiamo modificando, prendiamo i dati esistenti
      if (item) {
        setFormData({
          parte_id: item.parte_id,
          tool_id: item.tool_id,
          priorita: item.priorita,
          status: item.status,
          note: item.note || ""
        })
      } else {
        // Reset form per nuova creazione
        setFormData({
          parte_id: 0,
          tool_id: 0,
          priorita: 1,
          status: "Preparazione",
          note: ""
        })
        setSelectedParte(null)
        setFilteredTools([])
      }
    }
  }, [isOpen, item])

  // Aggiorna i tool filtrati quando cambia la parte selezionata
  useEffect(() => {
    if (formData.parte_id && parti.length > 0) {
      const parte = parti.find(p => p.id === formData.parte_id)
      setSelectedParte(parte || null)
      
      if (parte) {
        // Filtra i tool associati alla parte selezionata
        const parteTools = parte.tools || []
        const toolIds = parteTools.map(t => t.id)
        const filtered = tools.filter(tool => toolIds.includes(tool.id))
        setFilteredTools(filtered)
        
        // Se il tool attualmente selezionato non è nella lista filtrata, lo resettiamo
        if (formData.tool_id && !toolIds.includes(formData.tool_id)) {
          setFormData(prev => ({...prev, tool_id: 0}))
        }
      } else {
        setFilteredTools([])
      }
    } else {
      setFilteredTools([])
      setSelectedParte(null)
    }
  }, [formData.parte_id, parti, tools])

  const loadDependencies = async () => {
    try {
      setIsLoading(true)
      const [toolsData, partiData] = await Promise.all([
        toolApi.getAll(),
        partiApi.getAll()
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

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async () => {
    // Validazione base
    if (!formData.parte_id || !formData.tool_id) {
      toast({
        variant: 'destructive',
        title: 'Validazione fallita',
        description: 'Seleziona una parte e un tool validi.',
      })
      return
    }

    try {
      setIsSaving(true)
      
      if (item) {
        // Aggiornamento
        await odlApi.update(item.id, formData)
        toast({
          variant: 'success',
          title: 'ODL aggiornato',
          description: `ODL #${item.id} aggiornato con successo.`,
        })
      } else {
        // Creazione
        await odlApi.create(formData as ODLCreate)
        toast({
          variant: 'success',
          title: 'ODL creato',
          description: 'Nuovo ODL creato con successo.',
        })
      }
      
      // ✅ FIX: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX: Usa startTransition per evitare freeze
      startTransition(() => {
        onSuccess()
        onClose()
      })
    } catch (error) {
      console.error('Errore nel salvataggio dell\'ODL:', error)
      
      // ✅ FIX: Gestione errori migliorata
      let errorMessage = 'Impossibile salvare l\'ODL. Verifica i dati e riprova.'
      
      if (error instanceof Error) {
        if (error.message.includes('422')) {
          errorMessage = 'Dati non validi. Controlla i campi inseriti.'
        } else if (error.message.includes('400')) {
          errorMessage = 'Richiesta non valida. Verifica i dati inseriti.'
        } else {
          errorMessage = error.message
        }
      }
      
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
      })
    } finally {
      setIsSaving(false)
    }
  }

  // ✅ NUOVO: Funzione per salvare e resettare il form (solo in modalità creazione)
  const handleSaveAndNew = async () => {
    // Validazione base
    if (!formData.parte_id || !formData.tool_id) {
      toast({
        variant: 'destructive',
        title: 'Validazione fallita',
        description: 'Seleziona una parte e un tool validi.',
      })
      return
    }

    try {
      setIsSaving(true)
      
      // Solo modalità creazione (il pulsante è visibile solo in creazione)
      await odlApi.create(formData as ODLCreate)
      toast({
        variant: 'success',
        title: 'ODL creato e pronto per il prossimo',
        description: 'ODL creato con successo. Form resettato per un nuovo inserimento.',
      })
      
      // Reset del form per un nuovo inserimento
      setFormData({
        parte_id: 0,
        tool_id: 0,
        priorita: 1,
        status: "Preparazione",
        note: ""
      })
      setSelectedParte(null)
      setFilteredTools([])
      
      // ✅ FIX: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX: NON chiamiamo onSuccess() per evitare che il modal si chiuda
      // Invece, forziamo un refresh della lista senza chiudere il modal
      
      // NON chiudiamo il modal - rimane aperto per il prossimo inserimento
      // Il focus viene automaticamente messo sul primo campo
      setTimeout(() => {
        const parteSelect = document.querySelector('[role="combobox"]') as HTMLElement
        if (parteSelect) {
          parteSelect.focus()
        }
      }, 100)
      
    } catch (error) {
      console.error('Errore nel salvataggio dell\'ODL (Salva e nuovo):', error)
      
      // ✅ FIX: Gestione errori migliorata
      let errorMessage = 'Impossibile salvare l\'ODL. Verifica i dati e riprova.'
      
      if (error instanceof Error) {
        if (error.message.includes('422')) {
          errorMessage = 'Dati non validi. Controlla i campi inseriti.'
        } else if (error.message.includes('400')) {
          errorMessage = 'Richiesta non valida. Verifica i dati inseriti.'
        } else {
          errorMessage = error.message
        }
      }
      
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleCreateNewTool = () => {
    window.open('/dashboard/tools/new', '_blank')
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
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
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="parte_id" className="text-right">
                Parte
              </Label>
              <div className="col-span-3">
                <div className="space-y-2">
                  <Select
                    value={formData.parte_id?.toString() || ""}
                    onValueChange={(value) => handleChange('parte_id', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona una parte" />
                    </SelectTrigger>
                    <SelectContent>
                      {parti.length === 0 ? (
                        <div className="px-2 py-4 text-center text-sm">
                          Nessuna parte disponibile
                        </div>
                      ) : (
                        parti
                          .filter(parte => parte?.id && parte?.part_number)
                          .map(parte => (
                            <SelectItem key={parte.id} value={parte.id.toString()}>
                              {parte.part_number} - {parte.descrizione_breve}
                            </SelectItem>
                          ))
                      )}
                    </SelectContent>
                  </Select>
                  
                  {(formData.parte_id === 0 || formData.parte_id === undefined) && (
                    <div className="flex justify-end">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => window.open('/dashboard/parts/new', '_blank')}
                      >
                        + Crea nuova parte
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ✅ Campo descrizione della parte selezionata */}
            {selectedParte && (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right text-muted-foreground">
                  Descrizione
                </Label>
                <div className="col-span-3 space-y-1">
                  <div className="px-3 py-2 bg-muted rounded-md text-sm">
                    {selectedParte.descrizione_breve}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Descrizione della parte selezionata dal catalogo
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool_id" className="text-right">
                Tool
              </Label>
              <div className="col-span-3">
                <div className="space-y-2">
                  {selectedParte && filteredTools.length === 0 ? (
                    <Alert variant="destructive" className="mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Nessun tool associato alla parte selezionata
                      </AlertDescription>
                    </Alert>
                  ) : null}
                  
                  <Select
                    value={formData.tool_id?.toString() || ""}
                    onValueChange={(value) => handleChange('tool_id', parseInt(value))}
                    disabled={!formData.parte_id || filteredTools.length === 0}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona un tool" />
                    </SelectTrigger>
                    <SelectContent>
                      {filteredTools.length === 0 ? (
                        <div className="px-2 py-4 text-center text-sm">
                          {formData.parte_id && formData.parte_id > 0 
                            ? "Nessun tool disponibile per questa parte" 
                            : "Seleziona prima una parte"}
                        </div>
                      ) : (
                        filteredTools
                          .filter(tool => tool?.id && tool?.part_number_tool)
                          .map(tool => (
                            <SelectItem key={tool.id} value={tool.id.toString()}>
                              {tool.part_number_tool} {tool.descrizione ? `- ${tool.descrizione}` : ''}
                            </SelectItem>
                          ))
                      )}
                    </SelectContent>
                  </Select>
                  
                  {formData.parte_id && formData.parte_id > 0 && filteredTools.length === 0 && (
                    <div className="flex justify-end">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleCreateNewTool}
                      >
                        + Crea nuovo tool
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="priorita" className="text-right">
                Priorità
              </Label>
              <Input
                id="priorita"
                type="number"
                min={1}
                value={formData.priorita || 1}
                onChange={(e) => handleChange('priorita', parseInt(e.target.value))}
                className="col-span-3"
              />
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="status" className="text-right">
                Stato
              </Label>
              <div className="col-span-3">
                <Select
                  value={formData.status || "Preparazione"}
                  onValueChange={(value) => handleChange('status', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona lo stato" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Preparazione">Preparazione</SelectItem>
                    <SelectItem value="Laminazione">Laminazione</SelectItem>
                    <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                    <SelectItem value="Cura">Cura</SelectItem>
                    <SelectItem value="Finito">Finito</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="note" className="text-right">
                Note
              </Label>
              <Textarea
                id="note"
                placeholder="Note aggiuntive sull'ordine di lavoro"
                value={formData.note || ""}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleChange('note', e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving || isPending}>
            Annulla
          </Button>
          
          {/* ✅ NUOVO: Pulsante "Salva e nuovo" visibile solo in modalità creazione */}
          {!item && (
            <Button 
              type="button" 
              variant="secondary" 
              onClick={handleSaveAndNew} 
              disabled={isSaving || isPending}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Salva e Nuovo
            </Button>
          )}
          
          <Button onClick={handleSubmit} disabled={isSaving || isPending}>
            {(isSaving || isPending) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {item ? 'Aggiorna' : 'Crea'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ODLModal 