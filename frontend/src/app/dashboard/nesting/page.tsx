'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { NestingResponse, nestingApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { Loader2, RefreshCw, Info } from 'lucide-react'
import { NestingDetails } from './components/nesting-details'
import { Badge } from '@/components/ui/badge'

export default function NestingPage() {
  const [nestings, setNestings] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedNesting, setSelectedNesting] = useState<NestingResponse | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const { toast } = useToast()

  const fetchNestings = async () => {
    try {
      setIsLoading(true)
      const data = await nestingApi.getAll()
      setNestings(data)
    } catch (error) {
      console.error('Errore nel caricamento dei nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i nesting. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchNestings()
  }, [])

  const handleGenerateNesting = async () => {
    try {
      setIsGenerating(true)
      await nestingApi.generateAuto()
      toast({
        title: 'Operazione completata',
        description: 'Nesting generato con successo',
      })
      // Aggiorniamo la tabella dopo la generazione
      fetchNestings()
    } catch (error) {
      console.error('Errore nella generazione del nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile generare il nesting. Riprova più tardi.',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleRowClick = (nesting: NestingResponse) => {
    setSelectedNesting(nesting)
    setDetailsOpen(true)
  }

  // Funzione per formattare il valore di percentuale
  const formatPercent = (value: number, total: number) => {
    if (total === 0) return '0%'
    return `${Math.round((value / total) * 100)}%`
  }

  // Funzione per formattare la lista di ODL
  const formatODLList = (odl_list: NestingResponse['odl_list']) => {
    if (!odl_list || odl_list.length === 0) return 'Nessun ODL'
    
    return (
      <div className="flex flex-wrap gap-1 max-w-xs">
        {odl_list.map(odl => (
          <Badge key={odl.id} variant="outline" className="whitespace-nowrap">
            #{odl.id} {odl.parte.part_number}
          </Badge>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nesting</h1>
          <p className="text-muted-foreground">
            Gestisci i nesting per ottimizzare la produzione
          </p>
        </div>
        <Button 
          onClick={handleGenerateNesting} 
          disabled={isGenerating}
          className="flex items-center gap-2"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generazione in corso...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Genera Nesting Automatico
            </>
          )}
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <>
          {nestings.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 border rounded-lg">
              <p className="text-xl text-muted-foreground mb-4">
                Nessun nesting generato finora
              </p>
              <p className="text-sm text-muted-foreground mb-6">
                Genera un nuovo nesting per ottimizzare l'uso delle autoclavi con gli ODL in attesa di cura
              </p>
              <Button 
                onClick={handleGenerateNesting} 
                disabled={isGenerating}
                className="flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generazione in corso...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    Genera Nesting Automatico
                  </>
                )}
              </Button>
            </div>
          ) : (
            <Table>
              <TableCaption>Lista dei nesting generati</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Data Creazione</TableHead>
                  <TableHead>Autoclave</TableHead>
                  <TableHead>ODL Inclusi</TableHead>
                  <TableHead className="text-center">Area Utilizzata</TableHead>
                  <TableHead className="text-center">Valvole Utilizzate</TableHead>
                  <TableHead className="text-center">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {nestings.map(nesting => (
                  <TableRow 
                    key={nesting.id} 
                    className="hover:bg-muted/50"
                  >
                    <TableCell className="font-medium">{nesting.id}</TableCell>
                    <TableCell>{formatDateIT(new Date(nesting.created_at))}</TableCell>
                    <TableCell>
                      <div className="font-medium">{nesting.autoclave.nome}</div>
                      <div className="text-xs text-muted-foreground">{nesting.autoclave.codice}</div>
                    </TableCell>
                    <TableCell>
                      {formatODLList(nesting.odl_list)}
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex flex-col">
                        <span>{formatPercent(nesting.area_utilizzata, nesting.area_totale)}</span>
                        <span className="text-xs text-muted-foreground">
                          {nesting.area_utilizzata.toFixed(2)} m² / {nesting.area_totale.toFixed(2)} m²
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex flex-col">
                        <span>{formatPercent(nesting.valvole_utilizzate, nesting.valvole_totali)}</span>
                        <span className="text-xs text-muted-foreground">
                          {nesting.valvole_utilizzate} / {nesting.valvole_totali}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRowClick(nesting)
                        }}
                      >
                        <Info className="h-4 w-4" />
                        <span className="sr-only">Dettagli</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </>
      )}

      {selectedNesting && (
        <NestingDetails
          nesting={selectedNesting}
          isOpen={detailsOpen}
          onClose={() => setDetailsOpen(false)}
        />
      )}
    </div>
  )
} 