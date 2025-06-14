'use client'

import { useState, useEffect, useTransition } from 'react'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  partsApi,
  catalogApi,
  toolsApi,
  curingCyclesApi,
  ParteCreate,
  ParteUpdate,
  ParteResponse,
  CatalogoResponse,
  Tool,
  CicloCura,
} from '@/lib/api'
import { Loader2, Pencil, AlertTriangle, Plus, Search, X, Save } from 'lucide-react'
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
    num_valvole_richieste: 2,
    note_produzione: null,
    ciclo_cura_id: null,
    tool_ids: []
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isPending, startTransition] = useTransition()
  
  // ✅ FIX 3: Stato per gestire la modifica del part number
  const [isPartNumberEditable, setIsPartNumberEditable] = useState(false)
  
  // Stati per le opzioni
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [cicliCura, setCicliCura] = useState<CicloCura[]>([])
  const [isLoadingOptions, setIsLoadingOptions] = useState(false)
  
  // ✅ NUOVO: Stato per la ricerca dei tools
  const [toolSearchQuery, setToolSearchQuery] = useState('')
  
  const router = useRouter()
  const { toast } = useStandardToast()

  // Stati per i modal di creazione rapida
  const [toolModalOpen, setToolModalOpen] = useState(false)
  const [cicloCuraModalOpen, setCicloCuraModalOpen] = useState(false)
  
  // ✅ NUOVO: Filtro dei tools in base alla ricerca
  const filteredTools = tools.filter(tool => {
    if (!toolSearchQuery) return true
    const query = toolSearchQuery.toLowerCase()
    return (
      tool.part_number_tool?.toLowerCase().includes(query) ||
      tool.descrizione?.toLowerCase().includes(query)
    )
  })
  
  // Carica opzioni per i dropdown
  const loadOptions = async () => {
    setIsLoadingOptions(true)
    try {
      const [catalogoData, toolsData, cicliData] = await Promise.all([
        catalogApi.fetchCatalogItems({ attivo: true }),
        toolsApi.fetchTools(),
        curingCyclesApi.fetchCuringCycles()
      ])
      setCatalogo(catalogoData)
      setTools(toolsData)
      setCicliCura(cicliData)
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({ title: 'Errore', description: 'Impossibile caricare le opzioni. Riprova più tardi.', variant: 'destructive' })
    } finally {
      setIsLoadingOptions(false)
    }
  }

  // Popola form quando si apre in modalità modifica
  useEffect(() => {
    if (isOpen) {
      loadOptions()
      // ✅ Reset della ricerca quando si apre il modal
      setToolSearchQuery('')
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
        num_valvole_richieste: 2,
        note_produzione: null,
        ciclo_cura_id: null,
        tool_ids: []
      })
    }
    setErrors({})
  }, [item, isOpen])

  const handleChange = (field: string, value: string | number | number[] | null) => {
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

  // ✅ FIX 6: Gestione focus per sostituzione contenuto
  const handleFocus = (field: string) => {
    // Se il campo ha un valore di default, lo selezioniamo tutto per facilitare la sostituzione
    const input = document.getElementById(field) as HTMLInputElement | HTMLTextAreaElement
    if (input && input.value) {
      input.select()
    }
  }

  // ✅ FIX 3: Toggle per abilitare/disabilitare modifica part number
  const handleTogglePartNumberEdit = () => {
    if (!isPartNumberEditable) {
      // Mostra conferma prima di abilitare la modifica
      const confirmed = window.confirm(
        "⚠️ Modificare il Part Number può generare inconsistenze. Procedere solo se necessario.\n\nVuoi continuare?"
      )
      if (confirmed) {
        setIsPartNumberEditable(true)
      }
    } else {
      setIsPartNumberEditable(false)
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

    setIsSubmitting(true)
    try {
      if (item) {
        // ✅ FIX 3: Verifica se il part_number è stato modificato
        const partNumberChanged = item.part_number !== formData.part_number
        
        if (partNumberChanged) {
          // Se il part_number è cambiato, usa l'API di propagazione
          await catalogApi.updatePartNumberWithPropagation(item.part_number, formData.part_number)
          toast({
            variant: 'success',
            title: 'Part Number Aggiornato',
            description: `Part Number aggiornato da "${item.part_number}" a "${formData.part_number}" con propagazione globale.`
          })
        }
        
        // Modalità modifica - aggiorna gli altri campi
        const updateData: ParteUpdate = {
          part_number: formData.part_number,
          descrizione_breve: formData.descrizione_breve,
          num_valvole_richieste: formData.num_valvole_richieste,
          note_produzione: formData.note_produzione || undefined,
          ciclo_cura_id: formData.ciclo_cura_id || undefined,
          tool_ids: formData.tool_ids
        }
        await partsApi.updatePart(item.id, updateData)
        
        if (!partNumberChanged) {
          toast({
            variant: 'success',
            title: 'Aggiornata',
            description: `Parte ${item.id} aggiornata con successo.`
          })
        }
      } else {
        // Modalità creazione
        const createData: ParteCreate = {
          part_number: formData.part_number,
          descrizione_breve: formData.descrizione_breve,
          num_valvole_richieste: formData.num_valvole_richieste,
          note_produzione: formData.note_produzione || undefined,
          ciclo_cura_id: formData.ciclo_cura_id || undefined,
          tool_ids: formData.tool_ids
        }
        await partsApi.createPart(createData)
        toast({
          variant: 'success',
          title: 'Creata',
          description: 'Nuova parte creata con successo.'
        })
      }
      
      // ✅ FIX 1: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX 2: Usa startTransition per evitare freeze
      startTransition(() => {
        onSuccess()
        onClose()
      })
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

  // ✅ FIX 2: Funzione per salvare e resettare il form
  const handleSaveAndNew = async () => {
    const validation = validateForm()
    if (!validation.valid) {
      setErrors(validation.errors)
      return
    }

    setIsSubmitting(true)
    try {
      // Solo modalità creazione (il pulsante + è visibile solo in creazione)
      const createData: ParteCreate = {
        part_number: formData.part_number,
        descrizione_breve: formData.descrizione_breve,
        num_valvole_richieste: formData.num_valvole_richieste,
        note_produzione: formData.note_produzione || undefined,
        ciclo_cura_id: formData.ciclo_cura_id || undefined,
        tool_ids: formData.tool_ids
      }
      await partsApi.createPart(createData)
      
      // Reset del form PRIMA del toast per evitare interferenze
      setFormData({
        part_number: '',
        descrizione_breve: '',
        num_valvole_richieste: 2,
        note_produzione: null,
        ciclo_cura_id: null,
        tool_ids: []
      })
      setErrors({})

      toast({
        variant: 'success',
        title: 'Creata e pronta per la prossima',
        description: `Parte ${formData.part_number} creata con successo. Form resettato per un nuovo inserimento.`
      })
      
      // Focus immediato sul primo campo
      setTimeout(() => {
        const partNumberInput = document.getElementById('part_number') as HTMLInputElement
        if (partNumberInput) {
          partNumberInput.focus()
        }
      }, 50)
      
      // NON chiamare refresh o onSuccess() qui per evitare re-render che chiudono il dialog
      
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
        <DialogContent className="sm:max-w-[700px] h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 py-4 border-b shrink-0">
            <DialogTitle>
              {item ? `Modifica Parte: ${item.id}` : 'Crea Nuova Parte'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto px-6 py-4">

          <div className="grid gap-4 py-4">
            {/* ✅ FIX 3: Part Number con possibilità di modifica */}
            {item ? (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="part_number" className="text-right">
                  Part Number
                </Label>
                <div className="col-span-3 space-y-2">
                  <div className="flex gap-2">
                    <Input
                      id="part_number"
                      value={formData.part_number}
                      onChange={e => handleChange('part_number', e.target.value)}
                      onFocus={() => handleFocus('part_number')}
                      disabled={!isPartNumberEditable}
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={handleTogglePartNumberEdit}
                      title={isPartNumberEditable ? "Blocca modifica" : "Abilita modifica"}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {isPartNumberEditable && (
                    <Alert className="border-orange-200 bg-orange-50">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <AlertDescription className="text-orange-800">
                        ⚠️ Modificare il Part Number può generare inconsistenze. Procedere solo se necessario.
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {errors.part_number && (
                    <p className="text-sm text-destructive">{errors.part_number}</p>
                  )}
                </div>
              </div>
            ) : (
              /* Part Number con ricerca smart per creazione */
              <SmartCatalogoSelect
                catalogo={catalogo}
                selectedPartNumber={formData.part_number}
                onSelect={(partNumber) => handleChange('part_number', partNumber)}
                onItemSelect={(item) => {
                  // ✅ Precompila la descrizione quando si seleziona un item dal catalogo
                  if (item.descrizione && !formData.descrizione_breve) {
                    handleChange('descrizione_breve', item.descrizione)
                  }
                }}
                isLoading={isLoadingOptions}
                error={errors.part_number}
                disabled={false}
              />
            )}

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="descrizione_breve" className="text-right">
                Descrizione
              </Label>
              <div className="col-span-3 space-y-1">
                <Input
                  id="descrizione_breve"
                  value={formData.descrizione_breve}
                  onChange={e => handleChange('descrizione_breve', e.target.value)}
                  onFocus={() => handleFocus('descrizione_breve')}
                  placeholder="Descrizione della parte"
                />
                <p className="text-xs text-muted-foreground">
                  Campo precompilato dal catalogo, puoi modificarlo
                </p>
                {errors.descrizione_breve && (
                  <p className="text-sm text-destructive">{errors.descrizione_breve}</p>
                )}
              </div>
            </div>

                      <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="num_valvole_richieste" className="text-right">
              Numero Valvole
            </Label>
            <Input
              id="num_valvole_richieste"
              type="number"
              min="1"
              value={formData.num_valvole_richieste || ''}
              onChange={e => {
                const value = e.target.value
                if (value === '' || value === null) {
                  handleChange('num_valvole_richieste', 2) // Default per campo obbligatorio
                } else {
                  const numValue = parseInt(value)
                  if (!isNaN(numValue)) {
                    handleChange('num_valvole_richieste', numValue)
                  }
                }
              }}
              onFocus={() => handleFocus('num_valvole_richieste')}
              className="col-span-3"
            />
            {errors.num_valvole_richieste && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.num_valvole_richieste}</p>
            )}
          </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="ciclo_cura_id" className="text-right">
                Ciclo Cura
              </Label>
              <Select
                value={formData.ciclo_cura_id?.toString() || "none"}
                onValueChange={(value) => handleChange('ciclo_cura_id', value === "none" ? null : parseInt(value))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Seleziona ciclo cura (opzionale)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nessun ciclo cura</SelectItem>
                  {cicliCura.filter(ciclo => ciclo?.id && ciclo?.nome).map(ciclo => (
                    <SelectItem key={ciclo.id} value={ciclo.id.toString()}>
                      {ciclo.nome} - {ciclo.temperatura_stasi1}°C per {ciclo.durata_stasi1}min
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">
                Tools Associati
              </Label>
              <div className="col-span-3 space-y-2">
                {isLoadingOptions ? (
                  <div className="flex items-center gap-2 p-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Caricamento tools...</span>
                  </div>
                ) : tools.length === 0 ? (
                  <p className="text-sm text-muted-foreground p-2">Nessun tool disponibile</p>
                ) : (
                  <>
                    {/* ✅ NUOVO: Campo di ricerca per i tools */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Cerca tools per part number o descrizione..."
                        value={toolSearchQuery}
                        onChange={(e) => setToolSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                    
                    {/* Lista dei tools con messaggio se nessun risultato */}
                    {filteredTools.length === 0 ? (
                      <p className="text-sm text-muted-foreground p-2 text-center">
                        Nessun tool trovato per "{toolSearchQuery}"
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto border rounded-md p-2">
                        {filteredTools.map(tool => (
                      <label
                        key={tool.id}
                        className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={formData.tool_ids.includes(tool.id)}
                          onChange={() => {
                            const newToolIds = formData.tool_ids.includes(tool.id)
                              ? formData.tool_ids.filter(id => id !== tool.id)
                              : [...formData.tool_ids, tool.id]
                            handleChange('tool_ids', newToolIds)
                          }}
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
                  </>
                )}
                {errors.tool_ids && (
                  <p className="text-sm text-destructive">{errors.tool_ids}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-4 items-start gap-4">
              <Label htmlFor="note_produzione" className="text-right pt-2">
                Note Produzione
              </Label>
              <Textarea
                id="note_produzione"
                value={formData.note_produzione || ''}
                onChange={e => handleChange('note_produzione', e.target.value || null)}
                onFocus={() => handleFocus('note_produzione')}
                placeholder="Note aggiuntive per la produzione (opzionale)"
                className="col-span-3"
                rows={3}
              />
            </div>
          </div>
          </div>
          
          {/* Footer con pulsanti fissi */}
          <div className="px-6 py-4 border-t shrink-0 bg-background">
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting || isPending}
                className="w-full sm:w-auto"
              >
                <X className="h-4 w-4 mr-2" />
                Annulla
              </Button>
              
              {!item && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    handleSaveAndNew()
                  }}
                  disabled={isSubmitting || isPending}
                  className="w-full sm:w-auto"
                >
                  {isSubmitting || isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Salva e Nuovo
                </Button>
              )}
              
              <Button
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleSubmit()
                }}
                disabled={isSubmitting || isPending}
                className="w-full sm:w-auto"
              >
                {isSubmitting || isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {item ? "Aggiorna" : "Crea Parte"}
              </Button>
            </div>
          </div>
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