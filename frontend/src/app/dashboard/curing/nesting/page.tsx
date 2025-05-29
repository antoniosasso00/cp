'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { RefreshCw, FileText, Eye, Settings, Layers, CheckCircle, BarChart3 } from 'lucide-react'
import { 
  nestingApi, 
  NestingResponse
} from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { NestingParameters } from '@/components/nesting/NestingParametersPanel'
import { useNestingTabs } from '@/hooks/useNestingTabs'

// Import dei componenti tab
import {
  NestingManualTab,
  PreviewOptimizationTab,
  ParametersTab,
  MultiAutoclaveTab,
  ConfirmedLayoutsTab,
  ReportsTab
} from '@/components/nesting/tabs'

export default function NestingPage() {
  const [nestingList, setNestingList] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  
  // Parametri per il nesting
  const [nestingParameters, setNestingParameters] = useState<NestingParameters>({
    distanza_minima_tool_cm: 2.0,
    padding_bordo_autoclave_cm: 1.5,
    margine_sicurezza_peso_percent: 10.0,
    priorita_minima: 1,
    efficienza_minima_percent: 60.0
  })

  const { toast } = useToast()
  const { activeTab, changeTab, isValidTab } = useNestingTabs()

  // Wrapper per il cambio tab che gestisce la conversione di tipo
  const handleTabChange = (value: string) => {
    if (isValidTab(value)) {
      changeTab(value)
    }
  }

  // Funzione per caricare la lista dei nesting
  const loadNestingList = async () => {
    try {
      setIsLoading(true)
      const data = await nestingApi.getAll()
      setNestingList(data)
    } catch (error) {
      console.error('❌ Errore caricamento nesting:', error)
      toast({
        title: "Errore",
        description: "Impossibile caricare la lista dei nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Funzione per visualizzare i dettagli di un nesting
  const handleViewDetails = async (nestingId: number) => {
    try {
      const details = await nestingApi.getDetails(nestingId)
      toast({
        title: "Dettagli Nesting",
        description: `Nesting #${nestingId} - ${details.autoclave.nome}`,
      })
    } catch (error) {
      console.error('❌ Errore caricamento dettagli:', error)
      toast({
        title: "Errore",
        description: "Impossibile caricare i dettagli del nesting",
        variant: "destructive",
      })
    }
  }

  // Funzione per gestire la conferma di un nesting
  const handleNestingConfirmed = async () => {
    try {
      await loadNestingList()
    } catch (error) {
      console.error('❌ Errore aggiornamento UI dopo conferma:', error)
    }
  }

  // Funzione per gestire la preview con parametri
  const handlePreviewWithParameters = (params: NestingParameters) => {
    setNestingParameters(params)
    toast({
      title: "Parametri Aggiornati",
      description: "I parametri sono stati salvati e possono essere utilizzati per l'ottimizzazione",
    })
  }

  // Carica la lista al primo render
  useEffect(() => {
    loadNestingList()
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header della pagina */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestione Nesting</h1>
          <p className="text-muted-foreground">
            Gestisci e ottimizza i layout di taglio per la produzione con strumenti avanzati di nesting
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadNestingList}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
        </div>
      </div>

      {/* Tabs per organizzare le funzionalità */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="manual" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Nesting Manuali</span>
              <span className="sm:hidden">Manuali</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              <span className="hidden sm:inline">Preview & Ottimizzazione</span>
              <span className="sm:hidden">Preview</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="parameters" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">Parametri</span>
              <span className="sm:hidden">Param</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="multi-autoclave" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              <span className="hidden sm:inline">Multi-Autoclave</span>
              <span className="sm:hidden">Multi</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="confirmed" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Layout Confermati</span>
              <span className="sm:hidden">Confermati</span>
            </span>
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <span className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Report</span>
              <span className="sm:hidden">Report</span>
            </span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Nesting Manuali */}
        <TabsContent value="manual" className="space-y-6">
          <NestingManualTab
            nestingList={nestingList}
            isLoading={isLoading}
            onRefresh={loadNestingList}
          />
        </TabsContent>

        {/* Tab Preview & Ottimizzazione */}
        <TabsContent value="preview" className="space-y-6">
          <PreviewOptimizationTab
            onRefresh={loadNestingList}
            onViewDetails={handleViewDetails}
            onNestingConfirmed={handleNestingConfirmed}
          />
        </TabsContent>

        {/* Tab Parametri */}
        <TabsContent value="parameters" className="space-y-6">
          <ParametersTab
            parameters={nestingParameters}
            onParametersChange={setNestingParameters}
            isLoading={isLoading}
            onPreview={handlePreviewWithParameters}
          />
        </TabsContent>

        {/* Tab Multi-Autoclave */}
        <TabsContent value="multi-autoclave" className="space-y-6">
          <MultiAutoclaveTab />
        </TabsContent>

        {/* Tab Layout Confermati */}
        <TabsContent value="confirmed" className="space-y-6">
          <ConfirmedLayoutsTab
            onViewDetails={handleViewDetails}
          />
        </TabsContent>

        {/* Tab Report */}
        <TabsContent value="reports" className="space-y-6">
          <ReportsTab
            nestingList={nestingList}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
} 