'use client'

import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

// 🚀 LAZY LOADING: Carica la tabella solo quando necessario
const LazyBigTable = dynamic(() => import('@/components/tables/LazyBigTable'), { 
  ssr: false,
  loading: () => (
    <Card>
      <CardContent className="flex items-center justify-center py-12">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="text-muted-foreground">Caricamento tabella...</span>
        </div>
      </CardContent>
    </Card>
  )
})

import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText } from 'lucide-react'
import { odlApi, type ODLResponse } from '@/lib/api'
import Link from 'next/link'

interface ODLHistoryTableLazyProps {
  maxItems?: number
  showFilters?: boolean
  className?: string
  title?: string
  description?: string
}

export function ODLHistoryTableLazy({ 
  maxItems = 20, 
  showFilters = true, 
  className = "",
  title = "Storico ODL",
  description = "Cronologia degli ordini di lavorazione" 
}: ODLHistoryTableLazyProps) {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchODLHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const data = await odlApi.fetchODLs()
      
      // Ordina per data di creazione (più recenti prima)
      data.sort((a, b) => 
        new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      )
      
      setOdlList(data.slice(0, maxItems))
      
    } catch (err) {
      console.error('Errore nel caricamento dello storico ODL:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchODLHistory()
  }, [maxItems])

  // Configurazione colonne per LazyBigTable
  const columns = [
    {
      key: 'id',
      label: 'ODL',
      sortable: true,
      filterable: true,
      width: 'w-20',
      render: (value: any) => (
        <span className="font-medium">#{value}</span>
      )
    },
    {
      key: 'parte',
      label: 'Parte',
      sortable: true,
      filterable: true,
      width: 'w-48',
      render: (value: any) => (
        <div>
          <div className="font-medium text-sm">
            {value?.part_number || 'N/A'}
          </div>
          <div className="text-xs text-muted-foreground truncate max-w-[180px]">
            {value?.descrizione_breve || 'Descrizione non disponibile'}
          </div>
        </div>
      )
    },
    {
      key: 'tool',
      label: 'Tool',
      sortable: true,
      filterable: true,
      width: 'w-32',
      render: (value: any) => (
        <div className="text-sm">
          {value?.part_number_tool || 'N/A'}
        </div>
      )
    },
    {
      key: 'status',
      label: 'Stato',
      sortable: true,
      filterable: true,
      width: 'w-32',
      render: (value: string) => {
        const statusConfig = {
          'Preparazione': { variant: 'secondary', color: 'bg-gray-500' },
          'Laminazione': { variant: 'default', color: 'bg-blue-500' },
          'In Coda': { variant: 'outline', color: 'bg-yellow-500' },
          'Attesa Cura': { variant: 'secondary', color: 'bg-orange-500' },
          'Cura': { variant: 'default', color: 'bg-purple-500' },
          'Finito': { variant: 'default', color: 'bg-green-500' }
        }
        
        const config = statusConfig[value as keyof typeof statusConfig] || 
                      { variant: 'outline', color: 'bg-gray-500' }
        
        return (
          <Badge variant={config.variant as any} className="text-xs">
            {value || 'Sconosciuto'}
          </Badge>
        )
      }
    },
    {
      key: 'priorita',
      label: 'Priorità',
      sortable: true,
      filterable: false,
      width: 'w-20',
      render: (value: number) => (
        <Badge variant="outline" className="text-xs">
          P{value || 0}
        </Badge>
      )
    },
    {
      key: 'created_at',
      label: 'Data',
      sortable: true,
      filterable: false,
      width: 'w-32',
      render: (value: string) => (
        <div className="text-xs text-muted-foreground">
          {value ? new Date(value).toLocaleDateString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }) : 'Data non disponibile'}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Azioni',
      sortable: false,
      filterable: false,
      width: 'w-20',
      render: (value: any, row: any) => (
        <div className="flex gap-1">
          <Link href={`/dashboard/shared/odl/${row.id}`}>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <FileText className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      )
    }
  ]

  // Prepara i dati per la tabella
  const tableData = odlList.map(odl => ({
    id: odl.id,
    parte: odl.parte,
    tool: odl.tool,
    status: odl.status,
    priorita: odl.priorita,
    created_at: odl.created_at,
    actions: null // Placeholder per la colonna azioni
  }))

  return (
    <LazyBigTable
      data={tableData}
      columns={columns}
      title={title}
      description={description}
      loading={loading}
      error={error || undefined}
      searchable={showFilters}
      filterable={showFilters}
      paginated={true}
      pageSize={10}
      className={className}
      onRowClick={(row) => {
        // Opzionale: navigazione al click della riga
        window.location.href = `/dashboard/shared/odl/${row.id}`
      }}
      emptyMessage="Nessun ODL trovato con i filtri selezionati"
    />
  )
} 