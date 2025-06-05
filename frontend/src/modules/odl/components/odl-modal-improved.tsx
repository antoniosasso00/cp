'use client'

import { useState, useEffect, useMemo } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  ODLCreate, 
  ODLUpdate, 
  ODLResponse, 
  ParteResponse, 
  Tool, 
  odlApi, 
  partsApi, 
  toolsApi 
} from '@/lib/api'
import { 
  Loader2, 
  Search, 
  Plus, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Wrench
} from 'lucide-react'
import { useDebounce } from '@/hooks/useDebounce'
import ParteQuickModal from './parte-quick-modal'

interface ODLModalImprovedProps {
  isOpen: boolean
  onClose: () => void
  onSave: () => void
  editingItem?: ODLResponse | null
}

// Hook personalizzato per debounce
function useDebounceValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

export default function ODLModalImproved({ 
  isOpen, 
  onClose, 
  onSave, 
  editingItem 
}: ODLModalImprovedProps) {
  const [formData, setFormData] = useState<ODLCreate>({
    parte_id: 0,
    tool_id: 0,
    priorita: 1,
    status: "Preparazione",
    note: "",
    motivo_blocco: "",
    include_in_std: true
  })
  
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
  // Stati per ricerca dinamica parti
  const [parteSearchQuery, setParteSearchQuery] = useState('')
  const [isSearchingParti, setIsSearchingParti] = useState(false)
  const [showParteResults, setShowParteResults] = useState(false)
  const [selectedParte, setSelectedParte] = useState<ParteResponse | null>(null)
  
  // Stati per modal creazione parte
  const [showCreateParteModal, setShowCreateParteModal] = useState(false)
  
  // Debounce della ricerca parti
  const debouncedParteSearch = useDebounceValue(parteSearchQuery, 300)
  
  const { toast } = useToast()

  // Carica dati iniziali
  useEffect(() => {
    if (isOpen) {
      loadInitialData()
    }
  }, [isOpen])

  // Precompila form se in modalità edit
  useEffect(() => {
    if (editingItem) {
      setFormData({
        parte_id: editingItem.parte_id,
        tool_id: editingItem.tool_id,
        priorita: editingItem.priorita,
        status: editingItem.status,
        note: editingItem.note || "",
        motivo_blocco: editingItem.motivo_blocco || "",
        include_in_std: editingItem.include_in_std
      })
      setSelectedParte(editingItem.parte as any)
      setParteSearchQuery(editingItem.parte.part_number)
    } else {
      // Reset form per nuovo ODL
      setFormData({
        parte_id: 0,
        tool_id: 0,
        priorita: 1,
        status: "Preparazione",
        note: "",
        motivo_blocco: "",
        include_in_std: true
      })
      setSelectedParte(null)
      setParteSearchQuery('')
    }
  }, [editingItem])

  // Ricerca parti con debounce
  useEffect(() => {
    if (debouncedParteSearch && debouncedParteSearch.length >= 2) {
      searchParti(debouncedParteSearch)
    } else {
      setParti([])
      setShowParteResults(false)
    }
  }, [debouncedParteSearch])

  const loadInitialData = async () => {
    try {
      setIsLoading(true)
      // Carica tools se non sono già caricati
      if (tools.length === 0) {
        const toolsData = await toolsApi.fetchTools()
        setTools(toolsData)
      }
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati necessari.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const searchParti = async (query: string) => {
    try {
      setIsSearchingParti(true)
      // Carica parti se non sono già caricate
      if (parti.length === 0) {
        const partiData = await partsApi.fetchParts()
        setParti(partiData)
      }
      
      // Filtra parti in base alla query
      const filteredParti = parti.filter(parte => 
        parte.part_number.toLowerCase().includes(query.toLowerCase()) ||
        parte.descrizione_breve.toLowerCase().includes(query.toLowerCase())
      )
      
      setShowParteResults(true)
    } catch (error) {
      console.error('Errore nella ricerca parti:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Errore durante la ricerca delle parti.',
      })
    } finally {
      setIsSearchingParti(false)
    }
  }

  const handleParteSelect = (parte: ParteResponse) => {
    setSelectedParte(parte)
    setFormData(prev => ({ ...prev, parte_id: parte.id }))
    setParteSearchQuery(parte.part_number)
    setShowParteResults(false)
    
    // Filtra i tool compatibili con la parte selezionata
    const compatibleTools = tools.filter(tool => 
      parte.tools.some(parteTool => parteTool.id === tool.id)
    )
    
    if (compatibleTools.length === 1) {
      // Se c'è solo un tool compatibile, selezionalo automaticamente
      setFormData(prev => ({ ...prev, tool_id: compatibleTools[0].id }))
    }
  }

  const handleCreateParteShortcut = () => {
    setShowCreateParteModal(true)
  }

  const handleParteCreated = (newParte: ParteResponse) => {
    // Seleziona automaticamente la parte appena creata
    handleParteSelect(newParte)
    setShowCreateParteModal(false)
    
    toast({
      title: 'Parte creata',
      description: `Parte ${newParte.part_number} creata e selezionata automaticamente.`,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validazione
    if (!formData.parte_id || !formData.tool_id) {
      toast({
        variant: 'destructive',
        title: 'Errore di validazione',
        description: 'Seleziona una parte e un tool.',
      })
      return
    }

    try {
      setIsSaving(true)
      
      if (editingItem) {
        await odlApi.updateODL(editingItem.id, formData as ODLUpdate)
        toast({
          title: 'ODL aggiornato',
          description: 'L\'ordine di lavoro è stato aggiornato con successo.',
        })
      } else {
        await odlApi.createODL(formData)
        toast({
          title: 'ODL creato',
          description: 'Nuovo ordine di lavoro creato con successo.',
        })
      }
      
      onSave()
      onClose()
    } catch (error) {
      console.error('Errore nel salvataggio:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile salvare l\'ordine di lavoro.',
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Filtra tool compatibili con la parte selezionata
  const compatibleTools = useMemo(() => {
    if (!selectedParte) return tools
    
    return tools.filter(tool => 
      selectedParte.tools.some(parteTool => parteTool.id === tool.id)
    )
  }, [selectedParte, tools])

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
      "Preparazione": "secondary",
      "Laminazione": "default",
      "In Coda": "warning",
      "Attesa Cura": "warning",
      "Cura": "destructive",
      "Finito": "success"
    }
    return variants[status] || "default"
  }

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? `Modifica ODL #${editingItem.id}` : 'Nuovo Ordine di Lavoro'}
            </DialogTitle>
            <DialogDescription>
              {editingItem 
                ? `Modifica i dettagli dell'ordine di lavoro per ${editingItem.parte.part_number}`
                : 'Crea un nuovo ordine di lavoro specificando parte, tool e priorità'
              }
            </DialogDescription>
          </DialogHeader>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Caricamento dati...</span>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Sezione Parte con ricerca dinamica */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-4 w-4" />
                    Selezione Parte
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="parte-search">Cerca Parte</Label>
                    <div className="relative">
                      <Input
                        id="parte-search"
                        placeholder="Digita part number o descrizione..."
                        value={parteSearchQuery}
                        onChange={(e) => setParteSearchQuery(e.target.value)}
                        className="pr-10"
                      />
                      {isSearchingParti && (
                        <Loader2 className="absolute right-3 top-3 h-4 w-4 animate-spin" />
                      )}
                    </div>
                    
                    {/* Risultati ricerca */}
                    {showParteResults && parti.length > 0 && (
                      <div className="border rounded-md max-h-40 overflow-y-auto">
                        {parti.map((parte) => (
                          <div
                            key={parte.id}
                            className="p-3 hover:bg-muted cursor-pointer border-b last:border-b-0"
                            onClick={() => handleParteSelect(parte)}
                          >
                            <div className="font-medium">{parte.part_number}</div>
                            <div className="text-sm text-muted-foreground">
                              {parte.descrizione_breve}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {parte.num_valvole_richieste} valvole
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {parte.tools.length} tool compatibili
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Shortcut creazione parte */}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleCreateParteShortcut}
                      className="w-full"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      + Crea Nuova Parte
                    </Button>
                  </div>
                  
                  {/* Parte selezionata */}
                  {selectedParte && (
                    <div className="p-3 bg-muted rounded-md">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="font-medium">Parte Selezionata</span>
                      </div>
                      <div className="text-sm">
                        <div><strong>Part Number:</strong> {selectedParte.part_number}</div>
                        <div><strong>Descrizione:</strong> {selectedParte.descrizione_breve}</div>
                        <div><strong>Valvole richieste:</strong> {selectedParte.num_valvole_richieste}</div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Sezione Tool */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wrench className="h-4 w-4" />
                    Selezione Tool
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label htmlFor="tool">Tool</Label>
                    <Select
                      value={formData.tool_id ? formData.tool_id.toString() : ""}
                      onValueChange={(value) => {
                        if (!value || value.trim() === "") {
                          setFormData(prev => ({ ...prev, tool_id: 0 }));
                          return;
                        }
                        const numValue = parseInt(value);
                        if (!isNaN(numValue)) {
                          setFormData(prev => ({ ...prev, tool_id: numValue }));
                        }
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleziona un tool" />
                      </SelectTrigger>
                      <SelectContent>
                        {compatibleTools.length === 0 ? (
                          <div className="p-2 text-sm text-muted-foreground">
                            Nessun tool disponibile
                          </div>
                        ) : (
                          compatibleTools
                            .filter((tool) => tool?.id && tool?.part_number_tool)
                            .map((tool) => (
                              <SelectItem key={tool.id} value={tool.id.toString()}>
                                <div className="flex items-center justify-between w-full">
                                  <span>{tool.part_number_tool}</span>
                                  <Badge 
                                    variant={tool.disponibile ? "success" : "destructive"}
                                    className="ml-2"
                                  >
                                    {tool.disponibile ? "Disponibile" : "Occupato"}
                                  </Badge>
                                </div>
                              </SelectItem>
                            ))
                        )}
                      </SelectContent>
                    </Select>
                    
                    {selectedParte && compatibleTools.length === 0 && (
                      <div className="flex items-center gap-2 text-amber-600 text-sm">
                        <AlertTriangle className="h-4 w-4" />
                        Nessun tool compatibile trovato per questa parte
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Separator />

              {/* Dettagli ODL */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="priorita">Priorità</Label>
                  <Input
                    id="priorita"
                    type="number"
                    min="1"
                    max="10"
                    value={formData.priorita}
                    onChange={(e) => setFormData(prev => ({ ...prev, priorita: parseInt(e.target.value) || 1 }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">Stato</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, status: value as any }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["Preparazione", "Laminazione", "In Coda", "Attesa Cura", "Cura", "Finito"].map((status) => (
                        <SelectItem key={status} value={status}>
                          <div className="flex items-center gap-2">
                            <Badge variant={getStatusBadgeVariant(status)}>
                              {status}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="note">Note</Label>
                <Textarea
                  id="note"
                  placeholder="Note aggiuntive sull'ordine di lavoro..."
                  value={formData.note}
                  onChange={(e) => setFormData(prev => ({ ...prev, note: e.target.value }))}
                  rows={3}
                />
              </div>

              {/* Campo motivo blocco (solo se in stato "In Coda") */}
              {formData.status === "In Coda" && (
                <div className="space-y-2">
                  <Label htmlFor="motivo_blocco">Motivo Blocco</Label>
                  <Textarea
                    id="motivo_blocco"
                    placeholder="Descrivi il motivo per cui l'ODL è in coda..."
                    value={formData.motivo_blocco}
                    onChange={(e) => setFormData(prev => ({ ...prev, motivo_blocco: e.target.value }))}
                    rows={2}
                  />
                </div>
              )}

              <DialogFooter>
                <Button type="button" variant="outline" onClick={onClose}>
                  Annulla
                </Button>
                <Button type="submit" disabled={isSaving || !selectedParte}>
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Salvataggio...
                    </>
                  ) : (
                    editingItem ? 'Aggiorna ODL' : 'Crea ODL'
                  )}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal per creazione parte */}
      <ParteQuickModal
        isOpen={showCreateParteModal}
        onClose={() => setShowCreateParteModal(false)}
        onParteCreated={handleParteCreated}
        initialPartNumber={parteSearchQuery}
      />
    </>
  )
} 