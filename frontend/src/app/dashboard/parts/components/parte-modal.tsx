'use client'

import { useState, useEffect } from 'react'
import { z } from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  ParteResponse, 
  ParteCreate, 
  ParteUpdate, 
  partiApi, 
  catalogoApi, 
  toolApi, 
  cicloCuraApi,
  ToolInParteResponse,
  CicloCuraInParteResponse
} from '@/lib/api'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle, Plus } from 'lucide-react'
import debounce from 'lodash.debounce'

interface ParteModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  item: ParteResponse | null
}

// Schema di validazione con zod
const parteSchema = z.object({
  part_number: z.string().min(1, "Part Number obbligatorio"),
  descrizione_breve: z.string().min(1, "Descrizione obbligatoria"),
  num_valvole_richieste: z.number().min(1, "Almeno una valvola richiesta"),
  note_produzione: z.string().optional().nullable(),
  ciclo_cura_id: z.number().optional().nullable(),
  tool_ids: z.array(z.number()).optional().default([])
})

type CatalogoOption = {
  value: string;
  label: string;
  categoria?: string;
}

type ToolOption = {
  id: number;
  codice: string;
  descrizione?: string;
}

type CicloCuraOption = {
  id: number;
  nome: string;
}

// Tipo personalizzato per il form con supporto a campi null
interface ParteFormData {
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
  note_produzione: string | null;
  ciclo_cura_id: number | null;
  tool_ids: number[];
}

export default function ParteModal({ isOpen, onClose, onSuccess, item }: ParteModalProps) {
  const [formData, setFormData] = useState<ParteFormData>({
    part_number: '',
    descrizione_breve: '',
    num_valvole_richieste: 1,
    note_produzione: null,
    ciclo_cura_id: null,
    tool_ids: []
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [catalogo, setCatalogo] = useState<CatalogoOption[]>([])
  const [tools, setTools] = useState<ToolOption[]>([])
  const [cicliCura, setCicliCura] = useState<CicloCuraOption[]>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const { toast } = useToast()

  // Carica opzioni per i dropdown
  const loadOptions = async () => {
    setIsLoadingOptions(true)
    try {
      const [catalogoRes, toolsRes, cicliRes] = await Promise.all([
        catalogoApi.getAll({ attivo: true }),
        toolApi.getAll(),
        cicloCuraApi.getAll()
      ])

      setCatalogo(catalogoRes.map(cat => ({
        value: cat.part_number,
        label: `${cat.part_number} - ${cat.descrizione}`,
        categoria: cat.categoria
      })))
      
      setTools(toolsRes)
      setCicliCura(cicliRes)
    } catch (error) {
      console.error('Errore nel caricamento delle opzioni:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare le opzioni. Riprova più tardi.'
      })
    } finally {
      setIsLoadingOptions(false)
    }
  }

  // Popola form quando si apre in modalità modifica
  useEffect(() => {
    if (isOpen) {
      loadOptions()
    }
  }, [isOpen])

  useEffect(() => {
    if (item) {
      setFormData({
        part_number: item.part_number,
        descrizione_breve: item.descrizione_breve,
        num_valvole_richieste: item.num_valvole_richieste,
        note_produzione: item.note_produzione || null,
        ciclo_cura_id: item.ciclo_cura?.id || null,
        tool_ids: item.tools?.map(t => t.id) || []
      })
    } else {
      // Reset form per una nuova creazione
      setFormData({
        part_number: '',
        descrizione_breve: '',
        num_valvole_richieste: 1,
        note_produzione: null,
        ciclo_cura_id: null,
        tool_ids: []
      })
    }
    setErrors({})
  }, [item, isOpen])

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

  const validateForm = () => {
    try {
      // Converti stringhe in numeri dove necessario
      const dataToValidate = {
        ...formData,
        num_valvole_richieste: Number(formData.num_valvole_richieste),
        ciclo_cura_id: formData.ciclo_cura_id !== null ? Number(formData.ciclo_cura_id) : null,
        tool_ids: formData.tool_ids || []
      }
      
      parteSchema.parse(dataToValidate)
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

    // Prepara i dati da inviare
    const dataToSubmit: ParteCreate | ParteUpdate = {
      part_number: formData.part_number,
      descrizione_breve: formData.descrizione_breve,
      num_valvole_richieste: Number(formData.num_valvole_richieste),
      tool_ids: formData.tool_ids
    }
    
    if (formData.note_produzione) {
      dataToSubmit.note_produzione = formData.note_produzione
    }
    
    if (formData.ciclo_cura_id !== null) {
      dataToSubmit.ciclo_cura_id = Number(formData.ciclo_cura_id)
    }

    setIsSubmitting(true)
    try {
      if (item) {
        // Modalità modifica
        await partiApi.update(item.id, dataToSubmit)
        toast({
          variant: 'success',
          title: 'Aggiornato',
          description: `Parte con ID ${item.id} aggiornata con successo.`
        })
      } else {
        // Modalità creazione
        await partiApi.create(dataToSubmit as ParteCreate)
        toast({
          variant: 'success',
          title: 'Creato',
          description: 'Nuova parte creata con successo.'
        })
      }
      onSuccess()
    } catch (error: unknown) {
      console.error('Errore durante il salvataggio:', error)
      let errorMessage = 'Si è verificato un errore durante il salvataggio.'
      if (error instanceof Error) {
        errorMessage = error.message
      }
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Filtra i tool in base alla ricerca
  const filteredTools = tools.filter(tool => {
    const searchLower = searchQuery.toLowerCase()
    return (
      tool.codice.toLowerCase().includes(searchLower) ||
      (tool.descrizione?.toLowerCase().includes(searchLower) || false)
    )
  })

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {item ? `Modifica Parte: ${item.id}` : 'Crea Nuova Parte'}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="part_number" className="text-right">
              Part Number
            </Label>
            <div className="col-span-3">
              <div className="space-y-2">
                <Select
                  value={formData.part_number}
                  onValueChange={(value) => handleChange('part_number', value)}
                  disabled={!!item || isLoadingOptions}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona Part Number" />
                  </SelectTrigger>
                  <SelectContent>
                    {catalogo.length > 0 ? (
                      catalogo.map(cat => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))
                    ) : (
                      <div className="px-2 py-4 text-center text-sm">
                        Nessun part number disponibile
                      </div>
                    )}
                  </SelectContent>
                </Select>

                {!item && (
                  <div className="flex justify-end">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => window.open('/dashboard/catalog/new', '_blank')}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Crea nuovo part number
                    </Button>
                  </div>
                )}
              </div>
              {errors.part_number && (
                <p className="text-sm text-destructive mt-1">{errors.part_number}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="descrizione_breve" className="text-right">
              Descrizione
            </Label>
            <Input
              id="descrizione_breve"
              value={formData.descrizione_breve}
              onChange={e => handleChange('descrizione_breve', e.target.value)}
              className="col-span-3"
            />
            {errors.descrizione_breve && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.descrizione_breve}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="num_valvole_richieste" className="text-right">
              Valvole
            </Label>
            <Input
              id="num_valvole_richieste"
              type="number"
              min="1"
              value={formData.num_valvole_richieste}
              onChange={e => handleChange('num_valvole_richieste', e.target.value ? Number(e.target.value) : 1)}
              className="col-span-3"
            />
            {errors.num_valvole_richieste && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.num_valvole_richieste}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="ciclo_cura_id" className="text-right">
              Ciclo di Cura
            </Label>
            <div className="col-span-3">
              <Select
                value={formData.ciclo_cura_id?.toString() || ""}
                onValueChange={(value) => handleChange('ciclo_cura_id', value ? Number(value) : null)}
                disabled={isLoadingOptions}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona ciclo di cura" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Nessun ciclo di cura</SelectItem>
                  {cicliCura.map(ciclo => (
                    <SelectItem key={ciclo.id} value={ciclo.id.toString()}>
                      {ciclo.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="tool_ids" className="text-right pt-2">
              Tools/Stampi
            </Label>
            <div className="col-span-3">
              <div className="space-y-2">
                <Input
                  placeholder="Cerca nei tools..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="mb-2"
                />
                <div className="p-2 border rounded-md max-h-40 overflow-y-auto">
                  {filteredTools.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nessun tool disponibile</p>
                  ) : (
                    filteredTools.map(tool => (
                      <div key={tool.id} className="flex items-center gap-2 mb-1">
                        <input
                          type="checkbox"
                          id={`tool-${tool.id}`}
                          checked={formData.tool_ids.includes(tool.id)}
                          onChange={e => {
                            const currentTools = [...formData.tool_ids];
                            const updatedTools = e.target.checked
                              ? [...currentTools, tool.id]
                              : currentTools.filter(id => id !== tool.id)
                            handleChange('tool_ids', updatedTools)
                          }}
                          disabled={isLoadingOptions}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <label htmlFor={`tool-${tool.id}`} className="text-sm">
                          {tool.codice} {tool.descrizione && `- ${tool.descrizione}`}
                        </label>
                      </div>
                    ))
                  )}
                </div>
                <div className="flex justify-end">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => window.open('/dashboard/tools/new', '_blank')}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Crea nuovo tool
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="note_produzione" className="text-right">
              Note Produzione
            </Label>
            <textarea
              id="note_produzione"
              value={formData.note_produzione || ''}
              onChange={e => handleChange('note_produzione', e.target.value || null)}
              className="col-span-3 flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Note opzionali sulla produzione"
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting || isLoadingOptions}>
            Annulla
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting || isLoadingOptions}>
            {isSubmitting ? 'Salvataggio...' : item ? 'Aggiorna' : 'Crea'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 