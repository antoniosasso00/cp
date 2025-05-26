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
  CatalogoResponse,
  Tool,
  CicloCura
} from '@/lib/api'
import SmartCatalogoSelect from './smart-catalogo-select'
import SmartCicloCuraSelect from './smart-ciclo-cura-select'
import SmartToolsSelect from './smart-tools-select'
import ToolQuickModal from './tool-quick-modal'
import CicloCuraQuickModal from './ciclo-cura-quick-modal'

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
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [cicliCura, setCicliCura] = useState<CicloCura[]>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(false)
  
  // Stati per i modal di creazione rapida
  const [toolModalOpen, setToolModalOpen] = useState(false)
  const [cicloCuraModalOpen, setCicloCuraModalOpen] = useState(false)
  
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

      setCatalogo(catalogoRes)
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

  // Gestori per i modal di creazione rapida
  const handleToolCreated = (newTool: Tool) => {
    setTools(prev => [...prev, newTool])
    setFormData(prev => ({ ...prev, tool_ids: [...prev.tool_ids, newTool.id] }))
    setToolModalOpen(false)
    toast({
      variant: 'success',
      title: 'Tool Aggiunto',
      description: `Tool "${newTool.part_number_tool}" aggiunto alla parte.`
    })
  }

  const handleCicloCuraCreated = (newCiclo: CicloCura) => {
    setCicliCura(prev => [...prev, newCiclo])
    setFormData(prev => ({ ...prev, ciclo_cura_id: newCiclo.id }))
    setCicloCuraModalOpen(false)
    toast({
      variant: 'success',
      title: 'Ciclo Aggiunto',
      description: `Ciclo "${newCiclo.nome}" selezionato per la parte.`
    })
  }

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {item ? `Modifica Parte: ${item.id}` : 'Crea Nuova Parte'}
            </DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Part Number con ricerca smart */}
            <SmartCatalogoSelect
              catalogo={catalogo}
              selectedPartNumber={formData.part_number}
              onSelect={(partNumber) => handleChange('part_number', partNumber)}
              isLoading={isLoadingOptions}
              error={errors.part_number}
              disabled={!!item} // Disabilita in modifica
            />

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

            {/* Ciclo di Cura con ricerca smart */}
            <SmartCicloCuraSelect
              cicliCura={cicliCura}
              selectedId={formData.ciclo_cura_id}
              onSelect={(id) => handleChange('ciclo_cura_id', id)}
              onCreateNew={() => setCicloCuraModalOpen(true)}
              isLoading={isLoadingOptions}
              error={errors.ciclo_cura_id}
            />

            {/* Tools con ricerca smart */}
            <SmartToolsSelect
              tools={tools}
              selectedIds={formData.tool_ids}
              onSelect={(ids) => handleChange('tool_ids', ids)}
              onCreateNew={() => setToolModalOpen(true)}
              isLoading={isLoadingOptions}
              error={errors.tool_ids}
            />

            <div className="grid grid-cols-4 items-center gap-4">
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

      {/* Modal per creazione rapida Tool */}
      <ToolQuickModal
        isOpen={toolModalOpen}
        onClose={() => setToolModalOpen(false)}
        onSuccess={handleToolCreated}
      />

      {/* Modal per creazione rapida Ciclo di Cura */}
      <CicloCuraQuickModal
        isOpen={cicloCuraModalOpen}
        onClose={() => setCicloCuraModalOpen(false)}
        onSuccess={handleCicloCuraCreated}
      />
    </>
  )
} 