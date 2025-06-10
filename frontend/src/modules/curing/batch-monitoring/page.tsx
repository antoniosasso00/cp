'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/table'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/shared/components/ui/collapsible'
import { Checkbox } from '@/shared/components/ui/checkbox'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  Loader2, 
  Clock, 
  Play, 
  Pause, 
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Eye,
  Thermometer,
  Trash2
} from 'lucide-react'
import { batchNestingApi } from '@/shared/lib/api'
import { formatDateTime } from '@/shared/lib/utils'

interface BatchMonitoringItem {
  id: string
  nome?: string
  stato: 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato'
  autoclave_id: number
  autoclave?: {
    nome: string
    codice: string
    stato: string
  }
  numero_nesting: number
  peso_totale_kg: number
  created_at: string
  updated_at: string
  confermato_da_utente?: string
  data_conferma?: string
  workflow_actions?: {
    next_action: string
    can_proceed: boolean
    last_action?: string
    last_action_time?: string
  }
}

const STATO_WORKFLOW = {
  'sospeso': { 
    label: 'In Sospeso', 
    color: 'bg-yellow-100 text-yellow-800', 
    icon: Pause,
    next: 'Conferma'
  },
  'confermato': { 
    label: 'Confermato', 
    color: 'bg-green-100 text-green-800', 
    icon: CheckCircle,
    next: 'Carica'
  },
  'loaded': { 
    label: 'Caricato', 
    color: 'bg-blue-100 text-blue-800', 
    icon: Clock,
    next: 'Avvia Cura'
  },
  'cured': { 
    label: 'In Cura', 
    color: 'bg-red-100 text-red-800', 
    icon: Thermometer,
    next: 'Termina'
  },
  'terminato': { 
    label: 'Terminato', 
    color: 'bg-gray-100 text-gray-800', 
    icon: CheckCircle,
    next: null
  }
}

export default function BatchMonitoringPage() {
  const router = useRouter()
  const { toast } = useStandardToast()

  const [batches, setBatches] = useState<BatchMonitoringItem[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [actionLoading, setActionLoading] = useState<string[]>([])
  
  const [selectedBatches, setSelectedBatches] = useState<Set<string>>(new Set())
  const [deleteLoading, setDeleteLoading] = useState(false)

  useEffect(() => {
    loadBatches()
    // Auto-refresh ogni 30 secondi
    const interval = setInterval(loadBatches, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadBatches = async () => {
    try {
      setLoading(true)
      const response = await batchNestingApi.getAll({ limit: 100 })
      
      // Filtra solo batch attivi (non terminati da più di 1 giorno)
      const activeBatches = response.filter(batch => {
        if (batch.stato !== 'terminato') return true
        const daysSinceUpdate = (Date.now() - new Date(batch.updated_at).getTime()) / (1000 * 60 * 60 * 24)
        return daysSinceUpdate < 1
      })

      // Convert to monitoring format
      const monitoringBatches: BatchMonitoringItem[] = activeBatches.map(batch => ({
        ...batch,
        stato: batch.stato as BatchMonitoringItem['stato'],
        workflow_actions: {
          next_action: STATO_WORKFLOW[batch.stato as keyof typeof STATO_WORKFLOW]?.next || '',
          can_proceed: batch.stato !== 'terminato',
          last_action: batch.stato === 'confermato' ? 'Confermato' : undefined,
          last_action_time: batch.updated_at
        }
      }))

      setBatches(monitoringBatches)
      setSelectedBatches(prev => {
        const activeBatchIds = new Set(monitoringBatches.map(b => b.id))
        const newSelected = new Set<string>()
        prev.forEach(id => {
          if (activeBatchIds.has(id)) {
            newSelected.add(id)
          }
        })
        return newSelected
      })
    } catch (error) {
      toast({
        title: 'Errore caricamento',
        description: 'Impossibile caricare i batch da monitorare',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSelectBatch = (batchId: string, checked: boolean) => {
    setSelectedBatches(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(batchId)
      } else {
        newSet.delete(batchId)
      }
      return newSet
    })
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedBatches(new Set(batches.map(b => b.id)))
    } else {
      setSelectedBatches(new Set())
    }
  }

  const handleDeleteMultiple = async () => {
    if (selectedBatches.size === 0) return

    try {
      setDeleteLoading(true)
      
      const selectedBatchData = batches.filter(b => selectedBatches.has(b.id))
      const batchesRequireConfirm = selectedBatchData.filter(b => 
        ['confermato', 'loaded', 'cured'].includes(b.stato)  
      ) 
      const batchesSafeToDelete = selectedBatchData.filter(b => 
        ['sospeso', 'draft'].includes(b.stato)
      )
      const batchesCannotDelete = selectedBatchData.filter(b => 
        b.stato === 'terminato'
      )

      let confirmDelete = false
      if (batchesRequireConfirm.length > 0) {
        const confirmMessage = `
ATTENZIONE: Stai per eliminare batch in stati attivi!

Batch che richiedono conferma (${batchesRequireConfirm.length}):
${batchesRequireConfirm.map(b => `• ${b.id} (${b.stato})`).join('\n')}

Batch eliminabili direttamente (${batchesSafeToDelete.length}):
${batchesSafeToDelete.map(b => `• ${b.id} (${b.stato})`).join('\n')}

${batchesCannotDelete.length > 0 ? `
IMPOSSIBILI DA ELIMINARE (${batchesCannotDelete.length}):
${batchesCannotDelete.map(b => `• ${b.id} (${b.stato})`).join('\n')}
` : ''}

Vuoi procedere?`

        confirmDelete = window.confirm(confirmMessage)
        if (!confirmDelete) return
      }

      const idsToDelete = Array.from(selectedBatches)
      const result = await batchNestingApi.deleteMultipleBatch(idsToDelete, confirmDelete)

      toast({
        title: 'Eliminazione completata',
        description: `Eliminati ${result.deleted_count}/${result.total_requested} batch`
      })

      await loadBatches()
      setSelectedBatches(new Set())

    } catch (error: any) {
      toast({
        title: 'Errore eliminazione',
        description: error.message || 'Impossibile eliminare i batch selezionati',
        variant: 'destructive'
      })
    } finally {
      setDeleteLoading(false)
    }
  }

  const toggleExpanded = (batchId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(batchId)) {
      newExpanded.delete(batchId)
    } else {
      newExpanded.add(batchId)
    }
    setExpandedRows(newExpanded)
  }

  const handleWorkflowAction = async (batch: BatchMonitoringItem, action: string) => {
    const batchId = batch.id
    
    try {
      setActionLoading(prev => [...prev, batchId])
      
      const userInfo = {
        confermato_da_utente: 'Sistema',
        confermato_da_ruolo: 'Operatore'
      }

      switch (action) {
        case 'Conferma':
          await batchNestingApi.confirm(batchId, userInfo)
          break
        case 'Carica':
          await batchNestingApi.carica(batchId, userInfo.confermato_da_utente, userInfo.confermato_da_ruolo)
          break
        case 'Avvia Cura':
          await batchNestingApi.avviaCura(batchId, userInfo.confermato_da_utente, userInfo.confermato_da_ruolo)
          break
        case 'Termina':
          await batchNestingApi.termina(batchId, userInfo.confermato_da_utente, userInfo.confermato_da_ruolo)
          break
        default:
          throw new Error(`Azione non supportata: ${action}`)
      }

      toast({
        title: 'Azione completata',
        description: `${action} eseguito con successo per batch ${batch.nome || batchId}`
      })

      // Refresh data
      await loadBatches()
      
    } catch (error: any) {
      toast({
        title: 'Errore azione',
        description: error.message || `Impossibile eseguire ${action}`,
        variant: 'destructive'
      })
    } finally {
      setActionLoading(prev => prev.filter(id => id !== batchId))
    }
  }

  const handleViewBatch = (batchId: string) => {
    router.push(`/nesting/result/${batchId}`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Caricamento monitoraggio batch...</p>
        </div>
      </div>
    )
  }

  // Group batches by status
  const groupedBatches = batches.reduce((acc, batch) => {
    if (!acc[batch.stato]) acc[batch.stato] = []
    acc[batch.stato].push(batch)
    return acc
  }, {} as Record<string, BatchMonitoringItem[]>)

  const isAllSelected = batches.length > 0 && selectedBatches.size === batches.length
  const isPartiallySelected = selectedBatches.size > 0 && selectedBatches.size < batches.length

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio Batch</h1>
          <p className="text-muted-foreground">
            Controllo real-time del workflow di cura
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {selectedBatches.size > 0 && (
            <Button 
              onClick={handleDeleteMultiple}
              variant="destructive"
              disabled={deleteLoading}
            >
              {deleteLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="mr-2 h-4 w-4" />
              )}
              Elimina {selectedBatches.size} selezionati
            </Button>
          )}
          
          <Button onClick={loadBatches} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Aggiorna
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {Object.entries(STATO_WORKFLOW).map(([stato, config]) => {
          const count = groupedBatches[stato]?.length || 0
          const IconComponent = config.icon
          
          return (
            <Card key={stato}>
              <CardContent className="flex items-center p-6">
                <IconComponent className="h-8 w-8 text-muted-foreground" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">{config.label}</p>
                  <p className="text-2xl font-bold">{count}</p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Workflow Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Workflow Batch ({batches.length})</span>
            {batches.length > 0 && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={isAllSelected}
                  onCheckedChange={handleSelectAll}
                  className={isPartiallySelected ? "data-[state=checked]:bg-muted" : ""}
                />
                <span className="text-sm text-muted-foreground">
                  {selectedBatches.size > 0 ? `${selectedBatches.size} selezionati` : 'Seleziona tutto'}
                </span>
              </div>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {batches.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Nessun batch attivo da monitorare</p>
            </div>
          ) : (
            <div className="space-y-2">
              {batches.map((batch) => {
                const isExpanded = expandedRows.has(batch.id)
                const statoConfig = STATO_WORKFLOW[batch.stato]
                const IconComponent = statoConfig.icon
                const isActionLoading = actionLoading.includes(batch.id)
                const isSelected = selectedBatches.has(batch.id)

                return (
                  <Collapsible key={batch.id} open={isExpanded} onOpenChange={() => toggleExpanded(batch.id)}>
                    <div className="border rounded-lg">
                      <CollapsibleTrigger asChild>
                        <div className="flex items-center justify-between p-4 hover:bg-muted/50 cursor-pointer">
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                checked={isSelected}
                                onCheckedChange={(checked) => handleSelectBatch(batch.id, checked as boolean)}
                                onClick={(e) => e.stopPropagation()}
                              />
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                              <IconComponent className="h-5 w-5" />
                            </div>
                            
                            <div>
                              <div className="font-medium">
                                {batch.nome || `Batch #${batch.numero_nesting}`}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                ID: {batch.id} • Autoclave: {batch.autoclave?.nome || `AC${batch.autoclave_id}`}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-4">
                            <Badge className={statoConfig.color}>
                              {statoConfig.label}
                            </Badge>
                            
                            <div className="text-sm text-muted-foreground">
                              {batch.peso_totale_kg}kg
                            </div>

                            {statoConfig.next && (
                              <Button
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleWorkflowAction(batch, statoConfig.next!)
                                }}
                                disabled={isActionLoading}
                              >
                                {isActionLoading ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Play className="h-4 w-4" />
                                )}
                                {statoConfig.next}
                              </Button>
                            )}
                          </div>
                        </div>
                      </CollapsibleTrigger>

                      <CollapsibleContent>
                        <div className="border-t px-4 py-3 bg-muted/25">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <h4 className="font-medium mb-2">Timeline</h4>
                              <div className="text-sm space-y-1">
                                <div>Creato: {formatDateTime(batch.created_at)}</div>
                                <div>Aggiornato: {formatDateTime(batch.updated_at)}</div>
                                {batch.data_conferma && (
                                  <div>Confermato: {formatDateTime(batch.data_conferma)}</div>
                                )}
                              </div>
                            </div>

                            <div>
                              <h4 className="font-medium mb-2">Dettagli</h4>
                              <div className="text-sm space-y-1">
                                <div>Numero: #{batch.numero_nesting}</div>
                                <div>Peso: {batch.peso_totale_kg} kg</div>
                                <div>Autoclave: {batch.autoclave?.nome || `AC${batch.autoclave_id}`}</div>
                              </div>
                            </div>

                            <div>
                              <h4 className="font-medium mb-2">Azioni</h4>
                              <div className="flex space-x-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleViewBatch(batch.id)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  Visualizza
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CollapsibleContent>
                    </div>
                  </Collapsible>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 