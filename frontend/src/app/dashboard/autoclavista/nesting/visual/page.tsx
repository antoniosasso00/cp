'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { 
  Eye, 
  Settings, 
  CheckCircle, 
  Play, 
  Layers, 
  Package,
  AlertTriangle,
  ArrowLeft,
  RefreshCw
} from 'lucide-react'
import { nestingApi, TwoLevelNestingResponse, TwoLevelNestingRequest } from '@/lib/api'
import { useUserRole } from '@/hooks/useUserRole'
import { NestingPreview } from '@/components/nesting/NestingPreview'
import { NestingConfigForm } from '@/components/ui/NestingConfigForm'

interface NestingConfigFormValues {
  superficie_piano_2_max_cm2: number
  note?: string
  piano_assignments: Record<string, number>
}

export default function VisualNestingPage() {
  const router = useRouter()
  const { role } = useUserRole()
  const { toast } = useToast()
  
  const [nestingData, setNestingData] = useState<TwoLevelNestingResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState<'preview' | 'config'>('preview')
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [configChanges, setConfigChanges] = useState<NestingConfigFormValues | null>(null)

  // Verifica autorizzazioni
  useEffect(() => {
    if (role && role !== 'AUTOCLAVISTA' && role !== 'RESPONSABILE') {
      toast({
        variant: 'destructive',
        title: 'Accesso negato',
        description: 'Non hai i permessi per accedere a questa sezione.',
      })
      router.push('/dashboard')
    }
  }, [role, router, toast])

  // Genera un nuovo nesting automaticamente all'avvio
  useEffect(() => {
    if (role === 'AUTOCLAVISTA' || role === 'RESPONSABILE') {
      generateNewNesting()
    }
  }, [role])

  const generateNewNesting = async (customRequest?: TwoLevelNestingRequest) => {
    try {
      setIsGenerating(true)
      console.log('🔄 Generazione nuovo nesting su due piani...')
      
      const request: TwoLevelNestingRequest = customRequest || {
        superficie_piano_2_max_cm2: 5000,
        note: 'Nesting generato dall\'interfaccia visiva'
      }
      
      const result = await nestingApi.generateTwoLevel(request)
      console.log('✅ Nesting generato:', result)
      
      if (result.success) {
        setNestingData(result)
        setActiveTab('preview')
        toast({
          title: 'Nesting generato',
          description: `Nesting #${result.nesting_id} creato con successo`,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore nella generazione',
          description: result.message,
        })
      }
    } catch (error) {
      console.error('❌ Errore nella generazione del nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile generare il nesting. Riprova più tardi.',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleConfigChange = (config: NestingConfigFormValues) => {
    setConfigChanges(config)
    console.log('📝 Configurazione modificata:', config)
  }

  const handleSaveConfig = async () => {
    if (!configChanges || !nestingData) return

    try {
      setIsLoading(true)
      
      // Rigenera il nesting con i nuovi parametri
      const newRequest: TwoLevelNestingRequest = {
        superficie_piano_2_max_cm2: configChanges.superficie_piano_2_max_cm2,
        note: configChanges.note || 'Nesting modificato dall\'autoclavista'
      }
      
      await generateNewNesting(newRequest)
      
      toast({
        title: 'Configurazione salvata',
        description: 'Il nesting è stato rigenerato con i nuovi parametri',
      })
    } catch (error) {
      console.error('❌ Errore nel salvataggio:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile salvare la configurazione.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirmNesting = () => {
    if (!nestingData?.statistiche.carico_valido) {
      toast({
        variant: 'destructive',
        title: 'Carico non valido',
        description: 'Il carico supera il limite massimo dell\'autoclave.',
      })
      return
    }
    
    setShowConfirmDialog(true)
  }

  const handleFinalConfirm = async () => {
    if (!nestingData) return

    try {
      setIsLoading(true)
      
      // Aggiorna lo stato del nesting a "In sospeso"
      await nestingApi.updateStatus(
        nestingData.nesting_id, 
        'In sospeso', 
        'Nesting confermato dall\'autoclavista tramite interfaccia visiva',
        role || undefined
      )
      
      toast({
        title: 'Nesting confermato',
        description: `Nesting #${nestingData.nesting_id} è ora in sospeso e pronto per il carico`,
      })
      
      setShowConfirmDialog(false)
      
      // Reindirizza alla pagina principale del nesting
      router.push('/dashboard/autoclavista/nesting')
      
    } catch (error) {
      console.error('❌ Errore nella conferma:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile confermare il nesting.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleModifyNesting = (modifiedData: TwoLevelNestingResponse) => {
    setNestingData(modifiedData)
    console.log('🔧 Nesting modificato:', modifiedData)
  }

  if (!nestingData && !isGenerating) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Interfaccia Visiva Nesting</h1>
            <p className="text-muted-foreground">
              Visualizza e modifica il nesting su due piani
            </p>
          </div>
          <Button onClick={() => router.back()} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Nessun nesting disponibile</CardTitle>
            <CardDescription>
              Genera un nuovo nesting per iniziare
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => generateNewNesting()}>
              <Package className="h-4 w-4 mr-2" />
              Genera Nuovo Nesting
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isGenerating) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Generazione Nesting in Corso</h2>
            <p className="text-muted-foreground">
              Sto ottimizzando la disposizione dei tool sui due piani...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Interfaccia Visiva Nesting</h1>
          <p className="text-muted-foreground">
            Nesting #{nestingData?.nesting_id} - {nestingData?.autoclave.nome}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => router.back()} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
          <Button 
            onClick={() => generateNewNesting()} 
            variant="outline"
            disabled={isGenerating}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Rigenera
          </Button>
        </div>
      </div>

      {/* Stato del nesting */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Stato del Nesting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Autoclave</div>
              <div className="font-semibold">{nestingData?.autoclave.nome}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Piano 1</div>
              <div className="font-semibold">{nestingData?.piano_1.length} tools</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Piano 2</div>
              <div className="font-semibold">{nestingData?.piano_2.length} tools</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Stato Carico</div>
              {nestingData?.statistiche.carico_valido ? (
                <Badge variant="success">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Valido
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Eccessivo
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs per visualizzazione e configurazione */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'preview' | 'config')}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Visualizzazione 2D
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Configurazione
          </TabsTrigger>
        </TabsList>

        <TabsContent value="preview" className="mt-6">
          {nestingData && (
            <NestingPreview
              nestingData={nestingData}
              onModify={handleModifyNesting}
              onConfirm={handleConfirmNesting}
              isEditable={true}
            />
          )}
        </TabsContent>

        <TabsContent value="config" className="mt-6">
          {nestingData && (
            <NestingConfigForm
              nestingData={nestingData}
              onConfigChange={handleConfigChange}
              onSave={handleSaveConfig}
              isLoading={isLoading}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Pulsante di conferma fisso */}
      {nestingData && (
        <div className="fixed bottom-6 right-6">
          <Button
            size="lg"
            onClick={handleConfirmNesting}
            disabled={!nestingData.statistiche.carico_valido || isLoading}
            className="shadow-lg"
          >
            <CheckCircle className="h-5 w-5 mr-2" />
            Conferma Nesting
          </Button>
        </div>
      )}

      {/* Dialog di conferma */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conferma Nesting</DialogTitle>
            <DialogDescription>
              Sei sicuro di voler confermare questo nesting? Una volta confermato, 
              il nesting passerà in stato "In sospeso" e gli ODL saranno pronti per il carico.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium">Autoclave:</div>
                <div className="text-muted-foreground">{nestingData?.autoclave.nome}</div>
              </div>
              <div>
                <div className="font-medium">Peso totale:</div>
                <div className="text-muted-foreground">
                  {nestingData?.statistiche.peso_totale_kg.toFixed(1)} kg
                </div>
              </div>
              <div>
                <div className="font-medium">Piano 1:</div>
                <div className="text-muted-foreground">
                  {nestingData?.piano_1.length} tools
                </div>
              </div>
              <div>
                <div className="font-medium">Piano 2:</div>
                <div className="text-muted-foreground">
                  {nestingData?.piano_2.length} tools
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowConfirmDialog(false)}
              disabled={isLoading}
            >
              Annulla
            </Button>
            <Button 
              onClick={handleFinalConfirm}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Confermando...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Conferma
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 