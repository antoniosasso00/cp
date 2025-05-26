'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { 
  Form, 
  FormControl, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormMessage,
  FormDescription 
} from '@/components/ui/form'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  Settings, 
  Save, 
  RotateCcw, 
  AlertTriangle,
  Info,
  Package,
  Weight,
  Layers
} from 'lucide-react'
import { TwoLevelNestingResponse } from '@/lib/api'

// Schema di validazione per la configurazione del nesting
const nestingConfigSchema = z.object({
  superficie_piano_2_max_cm2: z.number()
    .min(100, "La superficie minima è 100 cm²")
    .max(50000, "La superficie massima è 50000 cm²"),
  note: z.string().optional(),
  piano_assignments: z.record(z.number().min(1).max(2))
})

type NestingConfigFormValues = z.infer<typeof nestingConfigSchema>

interface NestingConfigFormProps {
  nestingData: TwoLevelNestingResponse
  onConfigChange: (config: NestingConfigFormValues) => void
  onSave: () => void
  isLoading?: boolean
}

interface ODLAssignment {
  odl_id: number
  part_number: string
  descrizione: string
  peso_kg: number
  area_cm2: number
  priorita: number
  current_piano: 1 | 2
}

export function NestingConfigForm({ 
  nestingData, 
  onConfigChange, 
  onSave, 
  isLoading = false 
}: NestingConfigFormProps) {
  const { toast } = useToast()
  
  // Combina tutti gli ODL con le loro assegnazioni attuali
  const getAllODLAssignments = (): ODLAssignment[] => {
    const assignments: ODLAssignment[] = []
    
    // Piano 1
    nestingData.piano_1.forEach(odl => {
      assignments.push({
        odl_id: odl.odl_id,
        part_number: odl.part_number,
        descrizione: odl.descrizione,
        peso_kg: odl.peso_kg,
        area_cm2: odl.area_cm2,
        priorita: odl.priorita,
        current_piano: 1
      })
    })
    
    // Piano 2
    nestingData.piano_2.forEach(odl => {
      assignments.push({
        odl_id: odl.odl_id,
        part_number: odl.part_number,
        descrizione: odl.descrizione,
        peso_kg: odl.peso_kg,
        area_cm2: odl.area_cm2,
        priorita: odl.priorita,
        current_piano: 2
      })
    })
    
    return assignments.sort((a, b) => a.priorita - b.priorita)
  }

  const [odlAssignments, setOdlAssignments] = useState<ODLAssignment[]>(getAllODLAssignments())

  // Crea l'oggetto piano_assignments per il form
  const createPianoAssignments = () => {
    const assignments: Record<string, number> = {}
    odlAssignments.forEach(odl => {
      assignments[odl.odl_id.toString()] = odl.current_piano
    })
    return assignments
  }

  const form = useForm<NestingConfigFormValues>({
    resolver: zodResolver(nestingConfigSchema),
    defaultValues: {
      superficie_piano_2_max_cm2: nestingData.statistiche.area_piano_2_cm2 || 5000,
      note: '',
      piano_assignments: createPianoAssignments()
    },
  })

  // Calcola le statistiche aggiornate in base alle assegnazioni correnti
  const calculateUpdatedStats = () => {
    const piano1ODL = odlAssignments.filter(odl => odl.current_piano === 1)
    const piano2ODL = odlAssignments.filter(odl => odl.current_piano === 2)
    
    const peso_piano_1 = piano1ODL.reduce((sum, odl) => sum + odl.peso_kg, 0)
    const peso_piano_2 = piano2ODL.reduce((sum, odl) => sum + odl.peso_kg, 0)
    const peso_totale = peso_piano_1 + peso_piano_2
    
    const area_piano_1 = piano1ODL.reduce((sum, odl) => sum + odl.area_cm2, 0)
    const area_piano_2 = piano2ODL.reduce((sum, odl) => sum + odl.area_cm2, 0)
    
    const carico_valido = peso_totale <= nestingData.autoclave.max_load_kg
    
    return {
      piano1_count: piano1ODL.length,
      piano2_count: piano2ODL.length,
      peso_piano_1,
      peso_piano_2,
      peso_totale,
      area_piano_1,
      area_piano_2,
      carico_valido
    }
  }

  const stats = calculateUpdatedStats()

  // Gestisce il cambio di piano per un ODL
  const handlePianoChange = (odlId: number, newPiano: 1 | 2) => {
    const updatedAssignments = odlAssignments.map(odl => 
      odl.odl_id === odlId ? { ...odl, current_piano: newPiano } : odl
    )
    setOdlAssignments(updatedAssignments)
    
    // Aggiorna il form
    const newAssignments = createPianoAssignments()
    newAssignments[odlId.toString()] = newPiano
    form.setValue('piano_assignments', newAssignments)
    
    // Notifica il parent component
    onConfigChange(form.getValues())
    
    toast({
      title: 'Assegnazione aggiornata',
      description: `ODL spostato al piano ${newPiano}`,
    })
  }

  const onSubmit = (data: NestingConfigFormValues) => {
    onConfigChange(data)
    onSave()
  }

  const resetToOriginal = () => {
    setOdlAssignments(getAllODLAssignments())
    form.reset({
      superficie_piano_2_max_cm2: nestingData.statistiche.area_piano_2_cm2 || 5000,
      note: '',
      piano_assignments: createPianoAssignments()
    })
    onConfigChange(form.getValues())
  }

  return (
    <div className="space-y-6">
      {/* Statistiche aggiornate */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Weight className="h-4 w-4" />
              Peso Totale
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {stats.peso_totale.toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground">
              Max: {nestingData.autoclave.max_load_kg} kg
            </div>
            {stats.carico_valido ? (
              <Badge variant="success" className="mt-1 text-xs">
                Valido
              </Badge>
            ) : (
              <Badge variant="destructive" className="mt-1 text-xs">
                Eccessivo
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4 text-blue-500" />
              Piano 1
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {stats.piano1_count} tools
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.peso_piano_1.toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.area_piano_1.toFixed(0)} cm²
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4 text-green-500" />
              Piano 2
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {stats.piano2_count} tools
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.peso_piano_2.toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.area_piano_2.toFixed(0)} cm²
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Configurazione
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              Superficie P2
            </div>
            <div className="text-lg font-semibold">
              {form.watch('superficie_piano_2_max_cm2')} cm²
            </div>
          </CardContent>
        </Card>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Configurazione superficie piano 2 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Configurazione Piano 2</CardTitle>
              <CardDescription>
                Modifica la superficie massima disponibile per il piano superiore
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="superficie_piano_2_max_cm2"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Superficie Piano 2 (cm²)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        onChange={(e) => {
                          field.onChange(Number(e.target.value))
                          onConfigChange(form.getValues())
                        }}
                        min="100"
                        max="50000"
                        step="100"
                      />
                    </FormControl>
                    <FormDescription>
                      Superficie massima: {(nestingData.autoclave.lunghezza * nestingData.autoclave.larghezza_piano / 100).toFixed(0)} cm²
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="note"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Note (opzionale)</FormLabel>
                    <FormControl>
                      <Textarea
                        {...field}
                        placeholder="Aggiungi note per questa configurazione..."
                        rows={3}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Assegnazioni ODL */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Assegnazioni ODL ai Piani</CardTitle>
              <CardDescription>
                Modifica l'assegnazione di ogni ODL al piano desiderato
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {odlAssignments.map((odl) => (
                  <div key={odl.odl_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{odl.part_number}</div>
                      <div className="text-sm text-muted-foreground">{odl.descrizione}</div>
                      <div className="flex gap-4 text-xs text-muted-foreground mt-1">
                        <span>Peso: {odl.peso_kg}kg</span>
                        <span>Area: {odl.area_cm2.toFixed(0)}cm²</span>
                        <span>Priorità: {odl.priorita}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={odl.current_piano === 1 ? "default" : "secondary"}
                        className={odl.current_piano === 1 ? "bg-blue-500" : "bg-green-500"}
                      >
                        Piano {odl.current_piano}
                      </Badge>
                      <Select
                        value={odl.current_piano.toString()}
                        onValueChange={(value) => handlePianoChange(odl.odl_id, Number(value) as 1 | 2)}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">Piano 1</SelectItem>
                          <SelectItem value="2">Piano 2</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* ODL non pianificabili */}
          {nestingData.odl_non_pianificabili.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  ODL Non Pianificabili ({nestingData.odl_non_pianificabili.length})
                </CardTitle>
                <CardDescription>
                  Questi ODL non possono essere inclusi nel nesting attuale
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {nestingData.odl_non_pianificabili.map((odl) => (
                    <div key={odl.odl_id} className="flex justify-between items-center p-2 bg-orange-50 rounded">
                      <div>
                        <div className="font-medium">{odl.part_number}</div>
                        <div className="text-sm text-muted-foreground">{odl.descrizione}</div>
                      </div>
                      <Badge variant="outline" className="text-orange-700">
                        {odl.motivo}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pulsanti di azione */}
          <div className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={resetToOriginal}
              disabled={isLoading}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Ripristina Originale
            </Button>
            
            <div className="flex gap-2">
              <Button
                type="submit"
                disabled={isLoading || !stats.carico_valido}
              >
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Salvataggio...' : 'Salva Configurazione'}
              </Button>
            </div>
          </div>

          {!stats.carico_valido && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-700">
                Il carico totale supera il limite massimo dell'autoclave. 
                Riduci il numero di ODL o cambia le assegnazioni.
              </span>
            </div>
          )}
        </form>
      </Form>
    </div>
  )
} 