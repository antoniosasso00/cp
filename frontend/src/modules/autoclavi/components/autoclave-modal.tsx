'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from '@/components/ui/form'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { autoclavesApi } from '@/lib/api'

const autoclaveSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  codice: z.string().min(1, 'Il codice è obbligatorio'),
  lunghezza: z.number().min(0, 'La lunghezza deve essere positiva'),
  larghezza_piano: z.number().min(0, 'La larghezza deve essere positiva'),
  num_linee_vuoto: z.number().min(0, 'Il numero di linee deve essere positivo'),
  stato: z.enum(['DISPONIBILE', 'IN_USO', 'GUASTO', 'MANUTENZIONE', 'SPENTA']),
  temperatura_max: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_max: z.number().min(0, 'La pressione deve essere positiva'),
  
  // ✅ NUOVO: Carico massimo per nesting su due piani
  max_load_kg: z.number().min(0, 'Il carico massimo deve essere positivo').optional(),
  
  // ✅ NUOVO: Proprietà relative ai cavalletti (sistema 2L)
  usa_cavalletti: z.boolean().optional(),
  altezza_cavalletto_standard: z.number().min(0, 'L\'altezza cavalletto deve essere positiva').optional(),
  max_cavalletti: z.number().min(0, 'Il numero massimo cavalletti deve essere positivo').optional(),
  clearance_verticale: z.number().min(0, 'Il clearance verticale deve essere positivo').optional(),
  peso_max_per_cavalletto_kg: z.number().min(0, 'Il peso massimo per cavalletto deve essere positivo').optional(),
  
  // ✅ NUOVO: Dimensioni fisiche cavalletti (per risolvere hardcoded nel solver_2l.py)
  cavalletto_width: z.number().min(10, 'La larghezza cavalletto deve essere almeno 10mm').max(200, 'La larghezza massima è 200mm').optional(),
  cavalletto_height: z.number().min(10, 'L\'altezza cavalletto deve essere almeno 10mm').max(200, 'L\'altezza massima è 200mm').optional(),
  
  produttore: z.string().optional(),
  anno_produzione: z.number().optional(),
  note: z.string().optional(),
})

type AutoclaveFormValues = z.infer<typeof autoclaveSchema>

interface AutoclaveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingItem?: {
    id: number
    nome: string
    codice: string
    lunghezza: number
    larghezza_piano: number
    num_linee_vuoto: number
    stato: 'DISPONIBILE' | 'IN_USO' | 'GUASTO' | 'MANUTENZIONE' | 'SPENTA'
    temperatura_max: number
    pressione_max: number
    
    // ✅ NUOVO: Carico massimo per nesting su due piani
    max_load_kg?: number
    
    // ✅ NUOVO: Proprietà relative ai cavalletti (sistema 2L)
    usa_cavalletti?: boolean
    altezza_cavalletto_standard?: number
    max_cavalletti?: number
    clearance_verticale?: number
    peso_max_per_cavalletto_kg?: number
    
    // ✅ NUOVO: Dimensioni fisiche cavalletti (per risolvere hardcoded nel solver_2l.py)
    cavalletto_width?: number
    cavalletto_height?: number
    
    produttore?: string
    anno_produzione?: number
    note?: string
  } | null
  onSuccess: () => void
}

export function AutoclaveModal({ open, onOpenChange, editingItem, onSuccess }: AutoclaveModalProps) {
  const { toast } = useStandardToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<AutoclaveFormValues>({
    resolver: zodResolver(autoclaveSchema),
    defaultValues: {
      nome: '',
      codice: '',
      lunghezza: 0,
      larghezza_piano: 0,
      num_linee_vuoto: 0,
      stato: 'DISPONIBILE',
      temperatura_max: 0,
      pressione_max: 0,
      max_load_kg: 1000,
      
      // ✅ Valori di default per nuove autoclavi - CAVALLETTI DISABILITATI di default
      usa_cavalletti: false,
      altezza_cavalletto_standard: undefined,
      max_cavalletti: undefined,
      clearance_verticale: undefined,
      
      // ✅ NUOVO: Dimensioni cavalletti default (per sostituire hardcoded 80x60mm nel solver)
      cavalletto_width: 80, // mm - era hardcoded nel solver_2l.py
      cavalletto_height: 60, // mm - era hardcoded nel solver_2l.py
      
      produttore: '',
      anno_produzione: undefined,
      note: '',
    },
  })

  // ✅ FIX: Aggiorna i valori del form quando editingItem cambia
  useEffect(() => {
    if (editingItem) {
      form.reset({
        nome: editingItem.nome || '',
        codice: editingItem.codice || '',
        lunghezza: editingItem.lunghezza || 0,
        larghezza_piano: editingItem.larghezza_piano || 0,
        num_linee_vuoto: editingItem.num_linee_vuoto || 0,
        stato: editingItem.stato || 'DISPONIBILE',
        temperatura_max: editingItem.temperatura_max || 0,
        pressione_max: editingItem.pressione_max || 0,
        max_load_kg: editingItem.max_load_kg || 1000,
        
        // ✅ Campi sistema 2L per editing - mantieni valori esistenti o default
        usa_cavalletti: editingItem.usa_cavalletti || false,
        altezza_cavalletto_standard: editingItem.altezza_cavalletto_standard || undefined,
        max_cavalletti: editingItem.max_cavalletti || undefined,
        clearance_verticale: editingItem.clearance_verticale || undefined,
        peso_max_per_cavalletto_kg: editingItem.peso_max_per_cavalletto_kg || undefined,
        
        // ✅ NUOVO: Dimensioni cavalletti per editing
        cavalletto_width: editingItem.cavalletto_width || 80,
        cavalletto_height: editingItem.cavalletto_height || 60,
        
        produttore: editingItem.produttore || '',
        anno_produzione: editingItem.anno_produzione || undefined,
        note: editingItem.note || '',
      })
    } else {
      // Reset per nuovo item - CAVALLETTI DISABILITATI di default
      form.reset({
        nome: '',
        codice: '',
        lunghezza: 0,
        larghezza_piano: 0,
        num_linee_vuoto: 0,
        stato: 'DISPONIBILE',
        temperatura_max: 0,
        pressione_max: 0,
        max_load_kg: 1000,
        
        // ✅ Nuove autoclavi: cavalletti DISABILITATI di default (opzionale)
        usa_cavalletti: false,
        altezza_cavalletto_standard: undefined,
        max_cavalletti: undefined,
        clearance_verticale: undefined,
        peso_max_per_cavalletto_kg: undefined,
        
        // ✅ NUOVO: Dimensioni cavalletti default per reset
        cavalletto_width: 80,
        cavalletto_height: 60,
        
        produttore: '',
        anno_produzione: undefined,
        note: '',
      })
    }
  }, [editingItem, form])

  const onSubmit = async (data: AutoclaveFormValues) => {
    try {
      setIsLoading(true)
      if (editingItem) {
        await autoclavesApi.updateAutoclave(editingItem.id, data)
        toast({
          title: 'Autoclave aggiornata',
          description: 'L\'autoclave è stata aggiornata con successo.',
        })
      } else {
        await autoclavesApi.createAutoclave(data)
        toast({
          title: 'Autoclave creata',
          description: 'La nuova autoclave è stata creata con successo.',
        })
      }
      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error('Errore durante il salvataggio:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Si è verificato un errore durante il salvataggio.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editingItem ? 'Modifica Autoclave' : 'Nuova Autoclave'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 p-1">
            {/* Sezione Identificazione */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium border-b pb-2">🏷️ Identificazione</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="nome"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nome Autoclave</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="es. Autoclave A1" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="codice"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Codice Identificativo</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="es. AC-001" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            {/* Sezione Dimensioni Fisiche */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium border-b pb-2">📐 Dimensioni Fisiche</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="lunghezza"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lunghezza (mm)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="0"
                          placeholder="3000"
                          {...field}
                          value={field.value || ''}
                          onChange={e => {
                            const value = e.target.value
                            if (value === '') {
                              field.onChange(null)
                            } else {
                              const numValue = Number(value)
                              if (!isNaN(numValue) && numValue >= 0) {
                                field.onChange(numValue)
                              }
                            }
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="larghezza_piano"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Larghezza Piano (mm)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="0"
                          placeholder="1500"
                          {...field}
                          value={field.value || ''}
                          onChange={e => {
                            const value = e.target.value
                            if (value === '') {
                              field.onChange(null)
                            } else {
                              const numValue = Number(value)
                              if (!isNaN(numValue) && numValue >= 0) {
                                field.onChange(numValue)
                              }
                            }
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="num_linee_vuoto"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Linee Vuoto</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="0"
                          placeholder="4"
                          {...field}
                          value={field.value || ''}
                          onChange={e => {
                            const value = e.target.value
                            if (value === '') {
                              field.onChange(null)
                            } else {
                              const numValue = Number(value)
                              if (!isNaN(numValue) && numValue >= 0) {
                                field.onChange(numValue)
                              }
                            }
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              
              {/* Preview visivo delle dimensioni */}
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">📊 Superficie calcolata:</p>
                <p className="font-mono text-lg">
                  {((form.watch('lunghezza') || 0) * (form.watch('larghezza_piano') || 0) / 10000).toFixed(2)} cm²
                </p>
              </div>
            </div>

            <FormField
              control={form.control}
              name="stato"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Stato</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleziona lo stato" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="DISPONIBILE">Disponibile</SelectItem>
                      <SelectItem value="IN_USO">In Uso</SelectItem>
                      <SelectItem value="GUASTO">Guasto</SelectItem>
                      <SelectItem value="MANUTENZIONE">In Manutenzione</SelectItem>
                      <SelectItem value="SPENTA">Spenta</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="temperatura_max"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Temperatura Max (°C)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number"
                        {...field}
                        value={field.value || ''}
                        onChange={e => {
                          const value = e.target.value
                          if (value === '') {
                            field.onChange(null)
                          } else {
                            const numValue = Number(value)
                            if (!isNaN(numValue) && numValue >= 0) {
                              field.onChange(numValue)
                            }
                          }
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="pressione_max"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pressione Max (bar)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number"
                        {...field}
                        value={field.value || ''}
                        onChange={e => {
                          const value = e.target.value
                          if (value === '') {
                            field.onChange(null)
                          } else {
                            const numValue = Number(value)
                            if (!isNaN(numValue) && numValue >= 0) {
                              field.onChange(numValue)
                            }
                          }
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* ✅ NUOVO: Campo per carico massimo nesting su due piani */}
            <FormField
              control={form.control}
              name="max_load_kg"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Carico Massimo (kg)</FormLabel>
                  <FormControl>
                    <Input 
                      type="number" 
                      step="0.1"
                      min="0"
                      placeholder="1000"
                      {...field}
                      value={field.value || ''}
                      onChange={e => {
                        const value = e.target.value
                        if (value === '') {
                          field.onChange(null)
                        } else {
                          const numValue = Number(value)
                          if (!isNaN(numValue) && numValue >= 0) {
                            field.onChange(numValue)
                          }
                        }
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* ✅ NUOVO: Sezione Sistema Cavalletti 2L - OPZIONALE */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-medium border-b pb-2 flex-1">🔧 Sistema Cavalletti (Opzionale)</h3>
                <Badge variant="outline" className="text-xs">
                  {form.watch('usa_cavalletti') ? '✅ ABILITATO' : '❌ DISABILITATO'}
                </Badge>
              </div>
              
              <FormField
                control={form.control}
                name="usa_cavalletti"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Abilita Sistema Cavalletti</FormLabel>
                      <FormDescription>
                        🏗️ Permette nesting su due livelli con cavalletti di supporto.<br/>
                        <span className="text-muted-foreground text-xs">
                          ⚠️ Non tutte le autoclavi supportano i cavalletti - lasciare disabilitato se non supportati
                        </span>
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              {form.watch('usa_cavalletti') && (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800 font-medium">
                      ✅ Sistema cavalletti abilitato - Configura i parametri sottostanti
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 p-4 bg-muted/20 rounded-lg">
                    <FormField
                      control={form.control}
                      name="max_cavalletti"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Max Cavalletti</FormLabel>
                          <FormControl>
                            <Input 
                              type="number"
                              min="1"
                              max="10"
                              placeholder="es. 2"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 1) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                            />
                          </FormControl>
                          <FormDescription className="text-xs">
                            Numero supportato dall'autoclave
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="peso_max_per_cavalletto_kg"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Peso Max Cavalletto (kg)</FormLabel>
                          <FormControl>
                            <Input 
                              type="number"
                              min="1"
                              max="1000"
                              step="10"
                              placeholder="es. 250"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 50) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                            />
                          </FormControl>
                          <FormDescription className="text-xs">
                            🏋️ Capacità massima per cavalletto
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                  <FormField
                    control={form.control}
                    name="altezza_cavalletto_standard"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Altezza Cavalletto (mm)</FormLabel>
                        <FormControl>
                          <Input 
                            type="number"
                            min="50"
                            max="500"
                            placeholder="150"
                            {...field}
                            value={field.value || ''}
                            onChange={e => {
                              const value = e.target.value
                              if (value === '') {
                                field.onChange(null)
                              } else {
                                const numValue = Number(value)
                                if (!isNaN(numValue) && numValue >= 50) {
                                  field.onChange(numValue)
                                }
                              }
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="clearance_verticale"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Clearance Verticale (mm)</FormLabel>
                        <FormControl>
                          <Input 
                            type="number"
                            min="10"
                            max="100"
                            placeholder="20"
                            {...field}
                            value={field.value || ''}
                            onChange={e => {
                              const value = e.target.value
                              if (value === '') {
                                field.onChange(null)
                              } else {
                                const numValue = Number(value)
                                if (!isNaN(numValue) && numValue >= 10) {
                                  field.onChange(numValue)
                                }
                              }
                            }}
                          />
                        </FormControl>
                        <FormDescription>
                          Spazio minimo tra tool e livello superiore
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  {/* ✅ NUOVO: Campi dimensioni fisiche cavalletti (per eliminare hardcoded dal solver) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="cavalletto_width"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>📏 Larghezza Cavalletto (mm)</FormLabel>
                          <FormControl>
                            <Input 
                              type="number"
                              min="10"
                              max="200"
                              placeholder="80"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 10) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                            />
                          </FormControl>
                          <FormDescription className="text-xs">
                            Sostituisce il valore hardcoded 80mm nel solver
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="cavalletto_height"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>📐 Altezza Cavalletto (mm)</FormLabel>
                          <FormControl>
                            <Input 
                              type="number"
                              min="10"
                              max="200"
                              placeholder="60"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 10) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                            />
                          </FormControl>
                          <FormDescription className="text-xs">
                            Sostituisce il valore hardcoded 60mm nel solver
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  </div>
                </div>
              )}
            </div>

            <FormField
              control={form.control}
              name="produttore"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Produttore</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="anno_produzione"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Anno Produzione</FormLabel>
                  <FormControl>
                    <Input 
                      type="number"
                      min="1900"
                      max="2030"
                      placeholder="es. 2020"
                      {...field}
                      value={field.value || ''}
                      onChange={e => {
                        const value = e.target.value
                        if (value === '') {
                          field.onChange(null)
                        } else {
                          const numValue = Number(value)
                          if (!isNaN(numValue)) {
                            // Permetti qualsiasi numero durante la digitazione
                            // La validazione finale sarà gestita dallo schema del form
                            field.onChange(numValue)
                          }
                        }
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Note</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Salvataggio...' : editingItem ? 'Aggiorna' : 'Crea'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 