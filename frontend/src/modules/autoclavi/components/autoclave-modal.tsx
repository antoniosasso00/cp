'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
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
    produttore?: string
    anno_produzione?: number
    note?: string
  } | null
  onSuccess: () => void
}

export function AutoclaveModal({ open, onOpenChange, editingItem, onSuccess }: AutoclaveModalProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<AutoclaveFormValues>({
    resolver: zodResolver(autoclaveSchema),
    defaultValues: {
      nome: editingItem?.nome || '',
      codice: editingItem?.codice || '',
      lunghezza: editingItem?.lunghezza || 0,
      larghezza_piano: editingItem?.larghezza_piano || 0,
      num_linee_vuoto: editingItem?.num_linee_vuoto || 0,
      stato: editingItem?.stato || 'DISPONIBILE',
      temperatura_max: editingItem?.temperatura_max || 0,
      pressione_max: editingItem?.pressione_max || 0,
      // ✅ NUOVO: Carico massimo per nesting su due piani
      max_load_kg: editingItem?.max_load_kg || 1000,
      produttore: editingItem?.produttore || '',
      anno_produzione: editingItem?.anno_produzione || undefined,
      note: editingItem?.note || '',
    },
  })

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
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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