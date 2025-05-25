'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ODLResponse, odlApi, tempoFasiApi, TempoFaseResponse } from '@/lib/api'
import { formatDateIT, formatDateTime } from '@/lib/utils'
import { BarraAvanzamentoODL, getPriorityInfo } from '@/components/BarraAvanzamentoODL'
import { 
  Loader2, 
  MoreHorizontal, 
  Play,
  Square,
  ListFilter,
  Activity,
  Clock,
  ChevronLeft,
  RefreshCw,
  PlusCircle,
  Pencil,
  Trash2,
  AlertTriangle,
  CalendarClock,
  CheckCircle,
  History
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "default",
    "In Coda": "warning",
    "Attesa Cura": "warning", 
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

// Funzione per formattare la durata in ore e minuti
const formatDuration = (minutes: number | null): string => {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

// Funzione per tradurre il tipo di fase
const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

// Badge varianti per i diversi tipi di fase
const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "laminazione": "default",
    "attesa_cura": "warning",
    "cura": "destructive",
  }
  return variants[fase] || "default"
}

export default function ProduzionePage() {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [tempiFasi, setTempiFasi] = useState<TempoFaseResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedODL, setSelectedODL] = useState<ODLResponse | null>(null)
  const [isAdvancing, setIsAdvancing] = useState(false)
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica ODL
      const odlData = await odlApi.getAll()
      setOdlList(odlData)
      
      // Carica tempi fasi
      const tempiData = await tempoFasiApi.getAll()
      setTempiFasi(tempiData)
      
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati di produzione. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Controlla automaticamente la coda degli ODL
  const checkODLQueue = async () => {
    try {
      const result = await odlApi.checkQueue()
      if (result.updated_odls && result.updated_odls.length > 0) {
        toast({
          title: 'Coda ODL aggiornata',
          description: `${result.updated_odls.length} ODL hanno cambiato stato automaticamente.`,
        })
        fetchData() // Ricarica i dati
      } else {
        toast({
          title: 'Coda verificata',
          description: 'Nessun ODL necessita di cambiamenti di stato.',
        })
      }
    } catch (error) {
      console.error('Errore nel controllo coda ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile verificare la coda ODL.',
      })
    }
  }

  useEffect(() => {
    // Controlla la coda ogni 30 secondi
    const interval = setInterval(checkODLQueue, 30000)
    return () => clearInterval(interval)
  }, [])

  // Filtra ODL attivi (non finiti)
  const odlAttivi = odlList.filter(odl => odl.status !== "Finito")
  
  // Filtra ODL completati
  const odlCompletati = odlList.filter(odl => odl.status === "Finito")

  // Filtra i dati in base alla ricerca
  const filteredOdlAttivi = odlAttivi.filter(odl => {
    const searchLower = searchQuery.toLowerCase()
    return (
      odl.parte?.part_number?.toLowerCase()?.includes(searchLower) ||
      String(odl.id).includes(searchLower) ||
      odl.status.toLowerCase().includes(searchLower) ||
      (odl.note && odl.note.toLowerCase().includes(searchLower))
    )
  })

  const filteredOdlCompletati = odlCompletati.filter(odl => {
    const searchLower = searchQuery.toLowerCase()
    return (
      odl.parte?.part_number?.toLowerCase()?.includes(searchLower) ||
      String(odl.id).includes(searchLower) ||
      (odl.note && odl.note.toLowerCase().includes(searchLower))
    )
  })

  const filteredTempiFasi = tempiFasi.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    const odlInfo = odlList.find(odl => odl.id === item.odl_id)
    
    return (
      (odlInfo?.parte?.part_number?.toLowerCase()?.includes(searchLower)) ||
      String(item.odl_id).includes(searchLower) ||
      translateFase(item.fase).toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    )
  })

  // Ottieni informazioni ODL tramite odl_id
  const getOdlInfo = (odlId: number) => {
    return odlList.find(odl => odl.id === odlId) || null;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Produzione</h1>
          <p className="text-muted-foreground">
            Monitoraggio completo della produzione: ODL attivi, tempi registrati e storico
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={checkODLQueue}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Aggiorna Coda
          </Button>
          <Button onClick={fetchData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Ricarica
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca in tutti i dati di produzione..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <Tabs defaultValue="attivi" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="attivi" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              ODL Attivi ({filteredOdlAttivi.length})
            </TabsTrigger>
            <TabsTrigger value="tempi" className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Tempi Registrati ({filteredTempiFasi.length})
            </TabsTrigger>
            <TabsTrigger value="completati" className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Storico Completati ({filteredOdlCompletati.length})
            </TabsTrigger>
          </TabsList>

          {/* Sezione 1: ODL Attivi */}
          <TabsContent value="attivi" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Stato Avanzamento ODL Attivi
                </CardTitle>
              </CardHeader>
              <CardContent>
                {filteredOdlAttivi.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Nessun ODL attivo trovato
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredOdlAttivi.map(odl => (
                      <Card key={odl.id} className="p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-semibold">ODL #{odl.id}</h3>
                            <p className="text-sm text-muted-foreground">
                              {odl.parte?.part_number} - {odl.parte?.descrizione_breve}
                            </p>
                            {odl.tool && (
                              <p className="text-xs text-muted-foreground">
                                Tool: {odl.tool.part_number_tool}
                              </p>
                            )}
                          </div>
                          <Badge variant={getStatusBadgeVariant(odl.status)}>
                            {odl.status}
                          </Badge>
                        </div>
                        <BarraAvanzamentoODL 
                          status={odl.status} 
                          priorita={odl.priorita} 
                          motivo_blocco={odl.motivo_blocco}
                          variant="compact"
                        />
                        {odl.note && (
                          <p className="text-xs text-muted-foreground mt-2">
                            Note: {odl.note}
                          </p>
                        )}
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sezione 2: Tempi Registrati */}
          <TabsContent value="tempi" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Tempi Registrati
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableCaption>Monitoraggio dei tempi di produzione per ODL</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ODL</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Fase</TableHead>
                      <TableHead>Inizio</TableHead>
                      <TableHead>Fine</TableHead>
                      <TableHead>Durata</TableHead>
                      <TableHead>Note</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTempiFasi.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          Nessun dato di monitoraggio tempi trovato
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredTempiFasi.map(item => {
                        const odlInfo = getOdlInfo(item.odl_id);
                        return (
                          <TableRow key={item.id}>
                            <TableCell className="font-medium">{item.odl_id}</TableCell>
                            <TableCell>
                              {odlInfo?.parte?.part_number || 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Badge variant={getFaseBadgeVariant(item.fase)}>
                                {translateFase(item.fase)}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {formatDateTime(item.inizio_fase)}
                            </TableCell>
                            <TableCell>
                              {item.fine_fase ? formatDateTime(item.fine_fase) : 'In corso'}
                            </TableCell>
                            <TableCell>
                              {formatDuration(item.durata_minuti || null)}
                            </TableCell>
                            <TableCell className="max-w-xs truncate">
                              {item.note || '-'}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sezione 3: Storico ODL Completati */}
          <TabsContent value="completati" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Storico ODL Completati
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableCaption>ODL completati con successo</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ODL</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Descrizione</TableHead>
                      <TableHead>Tool</TableHead>
                      <TableHead>Priorità</TableHead>
                      <TableHead>Data Completamento</TableHead>
                      <TableHead>Note</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOdlCompletati.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          Nessun ODL completato trovato
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredOdlCompletati.map(odl => {
                        const priorityInfo = getPriorityInfo(odl.priorita);
                        return (
                          <TableRow key={odl.id}>
                            <TableCell className="font-medium">#{odl.id}</TableCell>
                            <TableCell>{odl.parte?.part_number || 'N/A'}</TableCell>
                            <TableCell className="max-w-xs truncate">
                              {odl.parte?.descrizione_breve || 'N/A'}
                            </TableCell>
                            <TableCell>
                              {odl.tool?.part_number_tool || 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs">
                                {priorityInfo.emoji} P{odl.priorita}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {formatDateTime(odl.updated_at)}
                            </TableCell>
                            <TableCell className="max-w-xs truncate">
                              {odl.note || '-'}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
} 