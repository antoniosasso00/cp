'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { 
  CheckCircle2, 
  AlertTriangle, 
  ArrowLeft,
  Factory,
  Package,
  Clock,
  Users,
  FileCheck,
  Loader2,
  PlayCircle,
  CheckCircle,
  AlertCircle,
  Download,
  Eye
} from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { ExtractedNestingData } from './NestingStep1ODLSelection'
import { AutoclaveSelectionData } from './NestingStep2AutoclaveSelection'
import { LayoutCanvasData } from '../layout/NestingDragDropCanvas'
import { ValidationResults } from './NestingStep4Validation'
import { nestingApi } from '@/lib/api'

export interface ConfirmationResults {
  nesting_confirmed: boolean
  nesting_loaded: boolean
  nesting_id: number
  autoclave_status_changed: boolean
  odl_status_changed: number
  confirmation_timestamp: string
  next_actions: string[]
}

interface NestingStep5ConfirmationProps {
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  layoutData: LayoutCanvasData
  validationData: ValidationResults
  onComplete: (results: ConfirmationResults) => void
  onBack: () => void
}

type ConfirmationStage = 'review' | 'confirming' | 'loading' | 'completed'

export function NestingStep5Confirmation({ 
  odlData, 
  autoclaveData, 
  layoutData, 
  validationData,
  onComplete, 
  onBack 
}: NestingStep5ConfirmationProps) {
  const { toast } = useToast()
  
  // State gestione processo
  const [currentStage, setCurrentStage] = useState<ConfirmationStage>('review')
  const [confirmationNotes, setConfirmationNotes] = useState('')
  const [confirmationResults, setConfirmationResults] = useState<ConfirmationResults | null>(null)
  const [processProgress, setProcessProgress] = useState(0)
  const [currentAction, setCurrentAction] = useState('')

  // Calcola statistiche per il riepilogo
  const getSummaryStats = () => {
    return {
      total_odl: odlData.compatibilita_summary.total_odl,
      peso_totale: odlData.peso_totale_kg,
      area_utilizzo: validationData.efficiency_metrics.area_efficiency,
      efficienza: validationData.efficiency_metrics.overall_score,
      autoclave: autoclaveData.autoclave_data.nome,
      cicli_cura: odlData.cicli_cura_coinvolti.length,
      piano_doppio: layoutData.final_positions.some(p => p.piano === 2),
      valvole_utilizzate: odlData.valvole_richieste,
      valvole_totali: autoclaveData.autoclave_data.num_linee_vuoto
    }
  }

  // Gestisce la conferma del nesting
  const handleConfirmNesting = async () => {
    try {
      setCurrentStage('confirming')
      setProcessProgress(25)
      setCurrentAction('Confermando il nesting...')

      // Simula API call per conferma
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Chiama API per confermare il nesting
      const confirmResponse = await nestingApi.confirm(layoutData.nesting_id, {
        confermato_da_ruolo: 'Operatore Produzione',
        note_conferma: confirmationNotes || 'Confermato tramite workflow manuale'
      })

      setProcessProgress(50)
      setCurrentAction('Nesting confermato, preparando per il caricamento...')

      // Procede automaticamente al caricamento
      setTimeout(() => {
        handleLoadNesting()
      }, 1000)

    } catch (error) {
      console.error('❌ Errore conferma nesting:', error)
      toast({
        variant: "destructive",
        title: "Errore conferma",
        description: "Non è stato possibile confermare il nesting"
      })
      setCurrentStage('review')
      setProcessProgress(0)
    }
  }

  // Gestisce il caricamento del nesting con cambio stati
  const handleLoadNesting = async () => {
    try {
      setCurrentStage('loading')
      setProcessProgress(75)
      setCurrentAction('Caricando autoclave e aggiornando stati ODL...')

      // Simula tempo di elaborazione
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Chiama API per caricare il nesting
      const loadResponse = await nestingApi.load(layoutData.nesting_id, {
        caricato_da_ruolo: 'Operatore Produzione',
        note_caricamento: 'Caricamento automatico post-conferma manuale'
      })

      setProcessProgress(100)
      setCurrentAction('Processo completato con successo!')

      // Crea risultati della conferma
      const results: ConfirmationResults = {
        nesting_confirmed: true,
        nesting_loaded: true,
        nesting_id: layoutData.nesting_id,
        autoclave_status_changed: true,
        odl_status_changed: odlData.compatibilita_summary.total_odl,
        confirmation_timestamp: new Date().toISOString(),
        next_actions: [
          'Monitorare il processo di cura in tempo reale',
          'Verificare il caricamento fisico dell\'autoclave',
          'Impostare i parametri del ciclo di cura',
          'Pianificare lo scarico al termine del ciclo'
        ]
      }

      setConfirmationResults(results)
      setCurrentStage('completed')

      toast({
        title: "Nesting completato!",
        description: `${odlData.compatibilita_summary.total_odl} ODL caricati nell'autoclave ${autoclaveData.autoclave_data.nome}`
      })

      // Passa i risultati al componente padre dopo un breve delay
      setTimeout(() => {
        onComplete(results)
      }, 2000)

    } catch (error) {
      console.error('❌ Errore caricamento nesting:', error)
      toast({
        variant: "destructive",
        title: "Errore caricamento",
        description: "Non è stato possibile caricare il nesting"
      })
      setCurrentStage('review')
      setProcessProgress(0)
    }
  }

  const stats = getSummaryStats()

  // Rendering fase review
  if (currentStage === 'review') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Step 5: Conferma e Caricamento</h2>
            <p className="text-gray-600 mt-1">
              Riepilogo finale e conferma del nesting per il caricamento in autoclave
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Progress value={100} className="w-32" />
            <span className="text-sm text-gray-500">100%</span>
          </div>
        </div>

        {/* Riepilogo finale */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-green-600" />
              Riepilogo Finale del Nesting
            </CardTitle>
            <CardDescription>
              Verifica tutti i dettagli prima della conferma definitiva
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Statistiche principali */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{stats.total_odl}</div>
                <div className="text-sm text-blue-800">ODL da Processare</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{stats.efficienza.toFixed(1)}%</div>
                <div className="text-sm text-green-800">Efficienza Totale</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{stats.peso_totale.toFixed(1)}kg</div>
                <div className="text-sm text-purple-800">Peso Totale</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{stats.area_utilizzo.toFixed(1)}%</div>
                <div className="text-sm text-orange-800">Utilizzo Area</div>
              </div>
            </div>

            {/* Dettagli configurazione */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Factory className="h-4 w-4" />
                  Autoclave Assegnata
                </h4>
                <div className="bg-gray-50 p-4 rounded space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Nome:</span>
                    <span className="font-medium">{stats.autoclave}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Codice:</span>
                    <span className="font-medium">{autoclaveData.autoclave_data.codice}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Valvole utilizzate:</span>
                    <span className="font-medium">{stats.valvole_utilizzate}/{stats.valvole_totali}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Stato attuale:</span>
                    <Badge className="bg-green-100 text-green-800">
                      {autoclaveData.autoclave_data.stato}
                    </Badge>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Configurazione Layout
                </h4>
                <div className="bg-gray-50 p-4 rounded space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Cicli di cura:</span>
                    <span className="font-medium">{stats.cicli_cura}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Piano doppio:</span>
                    <span className="font-medium">{stats.piano_doppio ? 'Sì' : 'No'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tool ruotati:</span>
                    <span className="font-medium">
                      {layoutData.final_positions.filter(p => p.rotated).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Conflitti:</span>
                    <Badge variant={layoutData.validation_results.has_conflicts ? "destructive" : "default"}>
                      {layoutData.validation_results.has_conflicts ? 'Presenti' : 'Nessuno'}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            {/* Lista cicli di cura */}
            <div>
              <h4 className="font-medium mb-3">Cicli di Cura Coinvolti</h4>
              <div className="flex flex-wrap gap-2">
                {odlData.cicli_cura_coinvolti.map(ciclo => (
                  <Badge key={ciclo} variant="outline" className="text-sm">
                    {ciclo}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Note operative */}
        <Card>
          <CardHeader>
            <CardTitle>Note Operative (Opzionale)</CardTitle>
            <CardDescription>
              Aggiungi note per il team di produzione o osservazioni sul layout
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="Es: Verificare posizionamento tool su piano superiore, priorità alta per ODL urgenti..."
              value={confirmationNotes}
              onChange={(e) => setConfirmationNotes(e.target.value)}
              rows={3}
            />
          </CardContent>
        </Card>

        {/* Effetti della conferma */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              Cosa Succederà alla Conferma
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Il nesting sarà confermato e pronto per il caricamento</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Gli {stats.total_odl} ODL cambieranno stato da "Attesa Cura" a "Cura"</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>L'autoclave {stats.autoclave} cambierà stato a "IN_USO"</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span>Sarà generato un report di nesting per la documentazione</span>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-blue-600" />
                <span>Il processo di cura potrà essere avviato e monitorato</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pulsanti azione */}
        <div className="flex items-center justify-between pt-6 border-t">
          <Button
            variant="outline"
            onClick={onBack}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Torna alla Validazione
          </Button>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              className="flex items-center gap-2"
            >
              <Eye className="h-4 w-4" />
              Anteprima Layout
            </Button>
            
            <Button
              onClick={handleConfirmNesting}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
            >
              <PlayCircle className="h-4 w-4" />
              Conferma e Carica Nesting
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Rendering fasi di processo
  if (currentStage === 'confirming' || currentStage === 'loading') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {currentStage === 'confirming' ? 'Confermando Nesting...' : 'Caricando in Autoclave...'}
            </h2>
            <p className="text-gray-600 mt-1">
              {currentAction}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Progress value={processProgress} className="w-32" />
            <span className="text-sm text-gray-500">{processProgress}%</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Elaborazione in Corso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <CheckCircle className={cn(
                  "h-4 w-4",
                  processProgress >= 25 ? "text-green-600" : "text-gray-400"
                )} />
                <span className={processProgress >= 25 ? "text-green-900" : "text-gray-500"}>
                  Nesting confermato
                </span>
              </div>
              
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-4 w-4 rounded-full border-2",
                  processProgress >= 75 ? "bg-green-600 border-green-600" : 
                  processProgress >= 50 ? "border-blue-600 animate-pulse" : "border-gray-400"
                )} />
                <span className={processProgress >= 75 ? "text-green-900" : 
                              processProgress >= 50 ? "text-blue-900" : "text-gray-500"}>
                  Aggiornamento stati ODL e autoclave
                </span>
              </div>
              
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-4 w-4 rounded-full border-2",
                  processProgress >= 100 ? "bg-green-600 border-green-600" : "border-gray-400"
                )} />
                <span className={processProgress >= 100 ? "text-green-900" : "text-gray-500"}>
                  Processo completato
                </span>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 rounded text-sm">
              <strong>Nota:</strong> Durante questo processo, gli stati degli ODL e dell'autoclave vengono 
              aggiornati automaticamente nel sistema. Non chiudere questa finestra.
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Rendering completamento
  if (currentStage === 'completed' && confirmationResults) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-green-900">Nesting Completato! 🎉</h2>
            <p className="text-gray-600 mt-1">
              Il nesting è stato confermato e caricato con successo
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Progress value={100} className="w-32" />
            <span className="text-sm text-gray-500">100%</span>
          </div>
        </div>

        {/* Risultati operazione */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              Operazione Completata
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium">Stato Nesting</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>ID Nesting:</span>
                    <Badge variant="outline">#{confirmationResults.nesting_id}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Confermato:</span>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex justify-between">
                    <span>Caricato:</span>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex justify-between">
                    <span>Timestamp:</span>
                    <span className="font-medium">
                      {new Date(confirmationResults.confirmation_timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">Cambiamenti Sistema</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>ODL aggiornati:</span>
                    <span className="font-medium">{confirmationResults.odl_status_changed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Autoclave stato:</span>
                    <Badge className="bg-red-100 text-red-800">IN_USO</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Report generato:</span>
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Prossimi step */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Prossimi Passi
            </CardTitle>
            <CardDescription>
              Azioni raccomandate per il team di produzione
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {confirmationResults.next_actions.map((action, index) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </div>
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Azioni finali */}
        <div className="flex items-center justify-center gap-4 pt-6 border-t">
          <Button
            variant="outline"
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Scarica Report
          </Button>
          
          <Button
            variant="outline"
            className="flex items-center gap-2"
          >
            <Eye className="h-4 w-4" />
            Visualizza Monitoraggio
          </Button>
          
          <Button
            className="flex items-center gap-2"
            onClick={() => window.location.reload()}
          >
            <CheckCircle className="h-4 w-4" />
            Torna alla Dashboard
          </Button>
        </div>
      </div>
    )
  }

  return null
} 