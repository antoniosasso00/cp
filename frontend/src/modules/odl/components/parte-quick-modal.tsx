'use client'

import { useState, useEffect } from 'react'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  ParteResponse, 
  ParteCreate, 
  partsApi, 
  catalogApi, 
  toolsApi, 
  curingCyclesApi,
  CatalogoResponse,
  Tool,
  CicloCura
} from '@/lib/api'
import { Loader2, Plus } from 'lucide-react'

interface ParteQuickModalProps {
  isOpen: boolean
  onClose: () => void
  onParteCreated: (parte: ParteResponse) => void
  initialPartNumber?: string
}

// Schema di validazione semplificato per creazione rapida
const parteQuickSchema = z.object({
  part_number: z.string().min(1, "Part Number obbligatorio"),
  descrizione_breve: z.string().min(1, "Descrizione obbligatoria"),
  num_valvole_richieste: z.number().min(1, "Almeno una valvola richiesta"),
  note_produzione: z.string().optional(),
  tool_ids: z.array(z.number()).min(1, "Almeno un tool deve essere selezionato")
})

interface ParteQuickFormData {
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
  note_produzione: string;
  tool_ids: number[];
}

export default function ParteQuickModal({ 
  isOpen, 
  onClose, 
  onParteCreated, 
  initialPartNumber = '' 
}: ParteQuickModalProps) {
  const [formData, setFormData] = useState<ParteQuickFormData>({
    part_number: '',
    descrizione_breve: '',
    num_valvole_richieste: 1,
    note_produzione: '',
    tool_ids: []
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [tools, setTools] = useState<Tool[]>([])
  const [isLoadingTools, setIsLoadingTools] = useState(false)
  
  const router = useRouter()
  const { toast } = useToast()

  // Carica i tool disponibili
  const loadTools = async () => {
    setIsLoadingTools(true)
    try {
      const toolsRes = await toolsApi.fetchTools()
      setTools(toolsRes)
    } catch (error) {
      console.error('Errore nel caricamento dei tool:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i tool disponibili.'
      })
    } finally {
      setIsLoadingTools(false)
    }
  }

  // Inizializza form quando si apre il modal
  useEffect(() => {
    if (isOpen) {
      loadTools()
      setFormData({
        part_number: initialPartNumber,
        descrizione_breve: '',
        num_valvole_richieste: 1,
        note_produzione: '',
        tool_ids: []
      })
      setErrors({})
    }
  }, [isOpen, initialPartNumber])

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Rimuovi errore se il campo viene corretto
    if (errors[field]) {
      setErrors(prev => {
        const updated = { ...prev }
        delete updated[field]
        return updated
      })
    }
  }

  const handleToolToggle = (toolId: number) => {
    setFormData(prev => ({
      ...prev,
      tool_ids: prev.tool_ids.includes(toolId)
        ? prev.tool_ids.filter(id => id !== toolId)
        : [...prev.tool_ids, toolId]
    }))
    
    // Rimuovi errore se almeno un tool è selezionato
    if (errors.tool_ids && formData.tool_ids.length > 0) {
      setErrors(prev => {
        const updated = { ...prev }
        delete updated.tool_ids
        return updated
      })
    }
  }

  const validateForm = () => {
    try {
      const dataToValidate = {
        ...formData,
        num_valvole_richieste: Number(formData.num_valvole_richieste),
        note_produzione: formData.note_produzione || undefined
      }
      
      parteQuickSchema.parse(dataToValidate)
      return { valid: true, errors: {} }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errorMap: Record<string, string> = {}
        error.errors.forEach(err => {
          if (err.path[0]) {
            errorMap[err.path[0].toString()] = err.message
          }
        })
        return { valid: false, errors: errorMap }
      }
      return { valid: false, errors: { form: 'Errore di validazione' } }
    }
  }

  const handleSubmit = async () => {
    const validation = validateForm()
    if (!validation.valid) {
      setErrors(validation.errors)
      return
    }

    const dataToSubmit: ParteCreate = {
      part_number: formData.part_number,
      descrizione_breve: formData.descrizione_breve,
      num_valvole_richieste: Number(formData.num_valvole_richieste),
      tool_ids: formData.tool_ids,
      note_produzione: formData.note_produzione || undefined
    }

    setIsSubmitting(true)
    try {
      const newParte = await partsApi.createPart(dataToSubmit)
      toast({
        title: 'Parte creata',
        description: `Parte ${newParte.part_number} creata con successo.`,
      })
      
      // ✅ FIX 1: Refresh automatico dopo creazione
      router.refresh()
      
      onParteCreated(newParte)
      onClose()
    } catch (error) {
      console.error('Errore nella creazione della parte:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile creare la parte. Verifica che il Part Number non sia già esistente.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Crea Nuova Parte</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Part Number */}
          <div className="space-y-2">
            <Label htmlFor="part_number">Part Number *</Label>
            <Input
              id="part_number"
              value={formData.part_number}
              onChange={(e) => handleChange('part_number', e.target.value)}
              placeholder="Inserisci il part number"
              className={errors.part_number ? 'border-red-500' : ''}
            />
            {errors.part_number && (
              <p className="text-sm text-red-500">{errors.part_number}</p>
            )}
          </div>

          {/* Descrizione */}
          <div className="space-y-2">
            <Label htmlFor="descrizione_breve">Descrizione *</Label>
            <Input
              id="descrizione_breve"
              value={formData.descrizione_breve}
              onChange={(e) => handleChange('descrizione_breve', e.target.value)}
              placeholder="Descrizione breve della parte"
              className={errors.descrizione_breve ? 'border-red-500' : ''}
            />
            {errors.descrizione_breve && (
              <p className="text-sm text-red-500">{errors.descrizione_breve}</p>
            )}
          </div>

          {/* Numero Valvole */}
          <div className="space-y-2">
            <Label htmlFor="num_valvole_richieste">Numero Valvole Richieste *</Label>
            <Input
              id="num_valvole_richieste"
              type="number"
              min="1"
              value={formData.num_valvole_richieste}
              onChange={(e) => handleChange('num_valvole_richieste', parseInt(e.target.value) || 1)}
              className={errors.num_valvole_richieste ? 'border-red-500' : ''}
            />
            {errors.num_valvole_richieste && (
              <p className="text-sm text-red-500">{errors.num_valvole_richieste}</p>
            )}
          </div>

          {/* Tool Selection */}
          <div className="space-y-2">
            <Label>Tool Associati *</Label>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Caricamento tool...
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto border rounded-md p-2">
                {tools.map(tool => (
                  <label
                    key={tool.id}
                    className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.tool_ids.includes(tool.id)}
                      onChange={() => handleToolToggle(tool.id)}
                      className="rounded"
                    />
                    <span className="text-sm">
                      {tool.part_number_tool}
                      {tool.descrizione && (
                        <span className="text-gray-500 ml-1">- {tool.descrizione}</span>
                      )}
                    </span>
                  </label>
                ))}
              </div>
            )}
            {errors.tool_ids && (
              <p className="text-sm text-red-500">{errors.tool_ids}</p>
            )}
          </div>

          {/* Note Produzione */}
          <div className="space-y-2">
            <Label htmlFor="note_produzione">Note Produzione</Label>
            <Textarea
              id="note_produzione"
              value={formData.note_produzione}
              onChange={(e) => handleChange('note_produzione', e.target.value)}
              placeholder="Note aggiuntive per la produzione (opzionale)"
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creazione...
              </>
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" />
                Crea Parte
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 