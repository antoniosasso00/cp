'use client'

import { useState } from 'react'
import { ApiTestComponent } from '@/components/debug/ApiTestComponent'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { odlApi, toolApi, nestingApi } from '@/lib/api'
import { Loader2, Bug, TestTube, Wrench, Grid3X3, Activity } from 'lucide-react'

export default function TestDebugPage() {
  const [isTestingODL, setIsTestingODL] = useState(false)
  const [isTestingTools, setIsTestingTools] = useState(false)
  const [isTestingNesting, setIsTestingNesting] = useState(false)
  const { toast } = useToast()

  const testODLFunctions = async () => {
    setIsTestingODL(true)
    try {
      // Test 1: Carica ODL
      const odlList = await odlApi.getAll()
      toast({
        title: '✅ Test ODL - Lista',
        description: `Caricati ${odlList.length} ODL`,
      })

      // Test 2: Test filtri per laminatore
      const odlLaminatore = odlList.filter(odl => 
        odl.status === "Preparazione" || odl.status === "Laminazione"
      )
      toast({
        title: '✅ Test ODL - Filtro Laminatore',
        description: `Trovati ${odlLaminatore.length} ODL per laminatore`,
      })

      // Test 3: Test filtri per autoclavista
      const odlAutoclavista = odlList.filter(odl => 
        odl.status === "Attesa Cura" || odl.status === "Cura"
      )
      toast({
        title: '✅ Test ODL - Filtro Autoclavista',
        description: `Trovati ${odlAutoclavista.length} ODL per autoclavista`,
      })

      // Test 4: Test ODL pending nesting
      const odlPending = await odlApi.getPendingNesting()
      toast({
        title: '✅ Test ODL - Pending Nesting',
        description: `Trovati ${odlPending.length} ODL pronti per nesting`,
      })

    } catch (error) {
      toast({
        variant: 'destructive',
        title: '❌ Test ODL Fallito',
        description: error instanceof Error ? error.message : 'Errore sconosciuto',
      })
    } finally {
      setIsTestingODL(false)
    }
  }

  const testToolsFunctions = async () => {
    setIsTestingTools(true)
    try {
      // Test 1: Carica tools
      const toolsList = await toolApi.getAll()
      toast({
        title: '✅ Test Tools - Lista',
        description: `Caricati ${toolsList.length} tools`,
      })

      // Test 2: Carica tools con status
      const toolsWithStatus = await toolApi.getAllWithStatus()
      toast({
        title: '✅ Test Tools - Con Status',
        description: `Caricati ${toolsWithStatus.length} tools con status`,
      })

      // Test 3: Update status from ODL
      const updateResult = await toolApi.updateStatusFromODL()
      toast({
        title: '✅ Test Tools - Update Status',
        description: `Aggiornati ${updateResult.updated_tools.length} tools`,
      })

    } catch (error) {
      toast({
        variant: 'destructive',
        title: '❌ Test Tools Fallito',
        description: error instanceof Error ? error.message : 'Errore sconosciuto',
      })
    } finally {
      setIsTestingTools(false)
    }
  }

  const testNestingFunctions = async () => {
    setIsTestingNesting(true)
    try {
      // Test 1: Carica nesting
      const nestingList = await nestingApi.getAll()
      toast({
        title: '✅ Test Nesting - Lista',
        description: `Caricati ${nestingList.length} nesting`,
      })

      // Test 2: Preview nesting
      const preview = await nestingApi.getPreview()
      toast({
        title: '✅ Test Nesting - Preview',
        description: `Preview: ${preview.autoclavi.length} autoclavi, ${preview.odl_esclusi.length} ODL esclusi`,
      })

      // Test 3: Lista bozze
      const drafts = await nestingApi.listDrafts()
      toast({
        title: '✅ Test Nesting - Bozze',
        description: `Trovate ${drafts.count} bozze`,
      })

    } catch (error) {
      toast({
        variant: 'destructive',
        title: '❌ Test Nesting Fallito',
        description: error instanceof Error ? error.message : 'Errore sconosciuto',
      })
    } finally {
      setIsTestingNesting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Bug className="h-8 w-8 text-purple-500" />
            Test & Debug Dashboard
          </h1>
          <p className="text-muted-foreground">
            Strumenti per testare e diagnosticare problemi nell'applicazione
          </p>
        </div>
        <Badge variant="outline" className="text-purple-600">
          Debug Mode
        </Badge>
      </div>

      <Tabs defaultValue="api" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="api">Test API</TabsTrigger>
          <TabsTrigger value="odl">Test ODL</TabsTrigger>
          <TabsTrigger value="tools">Test Tools</TabsTrigger>
          <TabsTrigger value="nesting">Test Nesting</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-4">
          <ApiTestComponent />
        </TabsContent>

        <TabsContent value="odl" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Test Funzionalità ODL
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Testa tutte le funzionalità relative agli Ordini di Lavoro (ODL)
              </p>
              
              <Button 
                onClick={testODLFunctions} 
                disabled={isTestingODL}
                className="w-full"
              >
                {isTestingODL ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing ODL...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    Avvia Test ODL
                  </>
                )}
              </Button>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Test inclusi:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• Caricamento lista ODL</li>
                    <li>• Filtri per ruolo Laminatore</li>
                    <li>• Filtri per ruolo Autoclavista</li>
                    <li>• ODL pronti per nesting</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Funzioni testate:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• odlApi.getAll()</li>
                    <li>• Filtri per stato</li>
                    <li>• odlApi.getPendingNesting()</li>
                    <li>• Gestione errori</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                Test Funzionalità Tools
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Testa tutte le funzionalità relative ai Tools
              </p>
              
              <Button 
                onClick={testToolsFunctions} 
                disabled={isTestingTools}
                className="w-full"
              >
                {isTestingTools ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing Tools...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    Avvia Test Tools
                  </>
                )}
              </Button>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Test inclusi:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• Caricamento lista tools</li>
                    <li>• Tools con status ODL</li>
                    <li>• Aggiornamento status automatico</li>
                    <li>• Gestione disponibilità</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Funzioni testate:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• toolApi.getAll()</li>
                    <li>• toolApi.getAllWithStatus()</li>
                    <li>• toolApi.updateStatusFromODL()</li>
                    <li>• Gestione errori</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="nesting" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Grid3X3 className="h-5 w-5" />
                Test Funzionalità Nesting
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Testa tutte le funzionalità relative al Nesting
              </p>
              
              <Button 
                onClick={testNestingFunctions} 
                disabled={isTestingNesting}
                className="w-full"
              >
                {isTestingNesting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing Nesting...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    Avvia Test Nesting
                  </>
                )}
              </Button>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Test inclusi:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• Caricamento lista nesting</li>
                    <li>• Preview nesting automatico</li>
                    <li>• Gestione bozze</li>
                    <li>• Nesting su due piani</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Funzioni testate:</h4>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• nestingApi.getAll()</li>
                    <li>• nestingApi.getPreview()</li>
                    <li>• nestingApi.listDrafts()</li>
                    <li>• Gestione errori</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 