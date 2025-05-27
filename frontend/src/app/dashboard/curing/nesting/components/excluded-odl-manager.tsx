'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ODLResponse, odlApi, nestingApi } from '@/lib/api'
import { 
  Loader2, 
  RefreshCw, 
  AlertTriangle,
  RotateCcw,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  Info
} from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

interface ExcludedODLManagerProps {
  isOpen: boolean
  onClose: () => void
  onODLReintegrated: () => void
}

interface ExcludedODL {
  id: number
  part_number: string
  descrizione: string
  motivo: string
  priorita: number
  num_valvole: number
}

export default function ExcludedODLManager({
  isOpen,
  onClose,
  onODLReintegrated
}: ExcludedODLManagerProps) {
  const [excludedODLs, setExcludedODLs] = useState<ExcludedODL[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [isReintegrating, setIsReintegrating] = useState<number | null>(null)
  const { toast } = useToast()

  // Carica gli ODL esclusi
  const fetchExcludedODLs = async () => {
    try {
      setIsLoading(true)
      
      // Ottieni la preview per vedere gli ODL esclusi
      const preview = await nestingApi.getPreview()
      
      if (preview.success) {
        setExcludedODLs(preview.odl_esclusi)
      } else {
        setExcludedODLs([])
      }
    } catch (error) {
      console.error('Errore nel caricamento degli ODL esclusi:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nel caricamento',
        description: 'Impossibile caricare gli ODL esclusi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Carica i dati quando si apre il modal
  useEffect(() => {
    if (isOpen) {
      fetchExcludedODLs()
    }
  }, [isOpen])

  // Reintegra un ODL modificando il suo stato
  const handleReintegrateODL = async (odlId: number) => {
    try {
      setIsReintegrating(odlId)
      
      // Aggiorna lo stato dell'ODL per renderlo disponibile per il nesting
      await odlApi.updateStatusAdmin(odlId, "Attesa Cura")
      
      toast({
        title: 'ODL reintegrato!',
        description: 'L\'ODL è stato reso nuovamente disponibile per il nesting.',
      })
      
      // Ricarica la lista
      await fetchExcludedODLs()
      onODLReintegrated()
      
    } catch (error) {
      console.error('Errore nella reintegrazione dell\'ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella reintegrazione',
        description: 'Impossibile reintegrare l\'ODL.',
      })
    } finally {
      setIsReintegrating(null)
    }
  }

  // Filtra gli ODL in base al termine di ricerca
  const filteredODLs = excludedODLs.filter(odl =>
    odl.part_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    odl.descrizione.toLowerCase().includes(searchTerm.toLowerCase()) ||
    odl.motivo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    odl.id.toString().includes(searchTerm)
  )

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Gestione ODL Esclusi
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {/* Controlli */}
          <div className="flex-shrink-0 flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Cerca ODL per ID, Part Number, descrizione o motivo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              onClick={fetchExcludedODLs}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Aggiorna
            </Button>
          </div>

          {/* Contenuto principale */}
          <div className="flex-1 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                  <p className="text-muted-foreground">Caricamento ODL esclusi...</p>
                </div>
              </div>
            ) : excludedODLs.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">Nessun ODL escluso!</h3>
                  <p className="text-muted-foreground">
                    Tutti gli ODL in attesa di cura possono essere inclusi nel nesting.
                  </p>
                </div>
              </div>
            ) : filteredODLs.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Search className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
                  <p className="text-lg font-medium">Nessun risultato trovato</p>
                  <p className="text-muted-foreground">
                    Prova a modificare i termini di ricerca
                  </p>
                </div>
              </div>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>ODL Esclusi ({filteredODLs.length})</span>
                    {searchTerm && (
                      <Badge variant="outline">
                        {filteredODLs.length} di {excludedODLs.length}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>ID ODL</TableHead>
                          <TableHead>Part Number</TableHead>
                          <TableHead>Descrizione</TableHead>
                          <TableHead>Motivo Esclusione</TableHead>
                          <TableHead className="text-center">Priorità</TableHead>
                          <TableHead className="text-center">Valvole</TableHead>
                          <TableHead className="text-center">Azioni</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredODLs.map((odl) => (
                          <TableRow key={odl.id}>
                            <TableCell className="font-medium">#{odl.id}</TableCell>
                            <TableCell className="font-mono text-sm">{odl.part_number}</TableCell>
                            <TableCell className="max-w-[200px] truncate" title={odl.descrizione}>
                              {odl.descrizione}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <AlertTriangle className="h-4 w-4 text-orange-500 flex-shrink-0" />
                                <span className="text-sm">{odl.motivo}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  odl.priorita <= 2 ? "destructive" : 
                                  odl.priorita <= 4 ? "default" : "secondary"
                                }
                              >
                                {odl.priorita}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant="outline">{odl.num_valvole}</Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReintegrateODL(odl.id)}
                                disabled={isReintegrating === odl.id}
                                className="text-green-600 hover:text-green-700"
                              >
                                {isReintegrating === odl.id ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <RotateCcw className="h-4 w-4" />
                                )}
                                <span className="sr-only">Reintegra ODL #{odl.id}</span>
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Informazioni sui motivi di esclusione */}
          {excludedODLs.length > 0 && (
            <div className="flex-shrink-0">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  <strong>Motivi comuni di esclusione:</strong>
                  <ul className="mt-2 text-sm space-y-1">
                    <li>• <strong>Spazio insufficiente:</strong> L'ODL è troppo grande per le autoclavi disponibili</li>
                    <li>• <strong>Valvole insufficienti:</strong> L'ODL richiede più valvole di quelle disponibili</li>
                    <li>• <strong>Autoclave occupata:</strong> Tutte le autoclavi compatibili sono già in uso</li>
                    <li>• <strong>Dati mancanti:</strong> L'ODL non ha tutte le informazioni necessarie</li>
                  </ul>
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>

        <DialogFooter className="flex-shrink-0">
          <Button variant="outline" onClick={onClose}>
            Chiudi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 