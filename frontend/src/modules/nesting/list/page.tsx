'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Loader2, Package2, Calendar, Filter, RefreshCw, Eye, Plus, ChevronDown, ChevronRight } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { batchNestingApi, BatchNestingList } from '@/lib/api'

export default function NestingListPage() {
  const { toast } = useStandardToast()
  const router = useRouter()
  
  // Stati per i dati
  const [batchList, setBatchList] = useState<BatchNestingList[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Stati per i filtri (solo stati disponibili nell'interfaccia)
  const [filtroStato, setFiltroStato] = useState<'sospeso' | 'confermato' | 'tutti'>('tutti')
  const [filtroNome, setFiltroNome] = useState('')
  
  // Stato di apertura/chiusura della lista
  const [isListOpen, setIsListOpen] = useState(true)

  // Caricamento dati iniziali
  useEffect(() => {
    loadBatchList()
  }, [filtroStato, filtroNome])

  const loadBatchList = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Caricamento lista batch nesting...')

      const params = {
        limit: 100, // Aumentiamo per catturare più batch prima di filtrare
        stato: filtroStato !== 'tutti' ? filtroStato : undefined,
        nome: filtroNome || undefined
      }

      const data = await batchNestingApi.getAll(params)
      
      // 🚫 FILTRO BATCH TERMINATI - Non mostrarli mai in pagina nesting
      const activeBatches = data.filter(batch => batch.stato !== 'terminato')
      
      console.log(`✅ Batch nesting caricati: ${data.length} totali, ${activeBatches.length} attivi (esclusi terminati)`)
      setBatchList(activeBatches)

    } catch (error) {
      console.error('❌ Errore nel caricamento batch nesting:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto nel caricamento dati'
      setError(errorMessage)
      toast({
        title: 'Errore di caricamento',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'sospeso':
        return 'secondary'
      case 'confermato':
        return 'default'
      default:
        return 'secondary'
    }
  }

  const getStatoLabel = (stato: string) => {
    switch (stato) {
      case 'sospeso':
        return 'In sospeso'
      case 'confermato':
        return 'Confermato'
      default:
        return stato
    }
  }

  const handleViewBatch = (batchId: string) => {
    router.push(`/dashboard/curing/nesting/result/${batchId}`)
  }

  const handleNewNesting = () => {
    router.push('/dashboard/curing/nesting')
  }

  // Statistiche batch attivi (esclusi terminati)
  const stats = {
    totale: batchList.length,
    sospeso: batchList.filter(b => b.stato === 'sospeso').length,
    confermato: batchList.filter(b => b.stato === 'confermato').length
  }

  // Mostra errore se presente
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Lista Nesting</h1>
            <p className="text-muted-foreground">Gestione batch di nesting generati</p>
          </div>
          <Button onClick={handleNewNesting}>
            <Plus className="mr-2 h-4 w-4" />
            Nuovo Nesting
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package2 className="h-5 w-5 text-destructive" />
              Errore di Caricamento
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button onClick={loadBatchList} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Riprova
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Lista Nesting</h1>
          <p className="text-muted-foreground">Gestione batch di nesting attivi (esclusi terminati)</p>
        </div>
        <Button onClick={handleNewNesting}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Nesting
        </Button>
      </div>

      {/* Statistiche Rapide */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Totale Attivi</p>
                <p className="text-2xl font-bold">{stats.totale}</p>
              </div>
              <Package2 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Sospesi</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.sospeso}</p>
              </div>
              <div className="h-2 w-2 rounded-full bg-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Confermati</p>
                <p className="text-2xl font-bold text-green-600">{stats.confermato}</p>
              </div>
              <div className="h-2 w-2 rounded-full bg-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtri */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label htmlFor="filtro-stato" className="text-sm font-medium">
                Stato
              </label>
              <Select value={filtroStato} onValueChange={(value: any) => setFiltroStato(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona stato" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tutti">Tutti gli stati attivi</SelectItem>
                  <SelectItem value="sospeso">In sospeso</SelectItem>
                  <SelectItem value="confermato">Confermato</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="filtro-nome" className="text-sm font-medium">
                Nome
              </label>
              <Input
                id="filtro-nome"
                placeholder="Cerca per nome..."
                value={filtroNome}
                onChange={(e) => setFiltroNome(e.target.value)}
              />
            </div>

            <div className="flex items-end">
              <Button onClick={loadBatchList} variant="outline" className="w-full">
                <RefreshCw className="mr-2 h-4 w-4" />
                Aggiorna
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista Batch Comprimibile */}
      <Card>
        <Collapsible open={isListOpen} onOpenChange={setIsListOpen}>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package2 className="h-5 w-5" />
                  Batch Nesting Attivi
                  <Badge variant="secondary">{batchList.length}</Badge>
                </CardTitle>
                <div className="flex items-center gap-2">
                  <CardDescription className="hidden md:block">
                    Lista di tutti i batch di nesting attivi (esclusi terminati)
                  </CardDescription>
                  {isListOpen ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </div>
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          
          <CollapsibleContent>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mr-2" />
                  <span>Caricamento batch nesting...</span>
                </div>
              ) : batchList.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Package2 className="h-8 w-8 mx-auto mb-2" />
                  <p>Nessun batch nesting attivo trovato</p>
                  <p className="text-sm">I batch terminati non vengono mostrati in questa vista</p>
                  <Button onClick={handleNewNesting} className="mt-4">
                    <Plus className="mr-2 h-4 w-4" />
                    Crea Nesting
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {batchList.map((batch) => (
                    <div key={batch.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium">
                            {batch.nome || `Nesting #${batch.numero_nesting}`}
                          </span>
                          <Badge variant={getStatoBadgeVariant(batch.stato)}>
                            {getStatoLabel(batch.stato)}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {new Date(batch.created_at).toLocaleDateString('it-IT')}
                          </span>
                          <span>Autoclave: {batch.autoclave_id}</span>
                          <span>Peso: {batch.peso_totale_kg.toFixed(1)} kg</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewBatch(batch.id)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  )
} 