'use client'

import { useState, useEffect } from 'react'
import { Tool, ParteResponse, ODLResponse, ODLCreate, ODLUpdate, odlApi, toolApi, partiApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Loader2 } from 'lucide-react'
import { cn } from "@/lib/utils"
import React from 'react'

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
  const [tools, setTools] = useState<Tool[]>([])
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
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
      }
    }
  }, [isOpen, item])

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
      
      onSuccess()
    } catch (error) {
      console.error('Errore nel salvataggio dell\'ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile salvare l\'ODL. Verifica i dati e riprova.',
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{item ? `Modifica ODL #${item.id}` : 'Crea nuovo ODL'}</DialogTitle>
          <DialogDescription>
            {item 
              ? 'Modifica i dettagli dell\'ordine di lavoro' 
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
                <Select
                  value={formData.parte_id?.toString() || ""}
                  onValueChange={(value) => handleChange('parte_id', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona una parte" />
                  </SelectTrigger>
                  <SelectContent>
                    {parti.map(parte => (
                      <SelectItem key={parte.id} value={parte.id.toString()}>
                        {parte.part_number} - {parte.descrizione_breve}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="tool_id" className="text-right">
                Tool
              </Label>
              <div className="col-span-3">
                <Select
                  value={formData.tool_id?.toString() || ""}
                  onValueChange={(value) => handleChange('tool_id', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona un tool" />
                  </SelectTrigger>
                  <SelectContent>
                    {tools.map(tool => (
                      <SelectItem key={tool.id} value={tool.id.toString()}>
                        {tool.codice} {tool.descrizione ? `- ${tool.descrizione}` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
          <Button variant="outline" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {item ? 'Aggiorna' : 'Crea'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ODLModal 