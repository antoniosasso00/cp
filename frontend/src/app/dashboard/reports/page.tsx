'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { reportsApi, ReportRangeType, ReportIncludeSection, ReportFileInfo } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { 
  FileText, 
  Download, 
  Calendar, 
  CalendarDays, 
  CalendarRange,
  Loader2,
  RefreshCw,
  Clock,
  ListTodo
} from 'lucide-react'

export default function ReportsPage() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [includeSections, setIncludeSections] = useState<ReportIncludeSection[]>([])
  const [existingReports, setExistingReports] = useState<ReportFileInfo[]>([])
  const [isLoadingReports, setIsLoadingReports] = useState(true)
  const { toast } = useToast()

  // Carica la lista dei report esistenti
  const fetchExistingReports = async () => {
    try {
      setIsLoadingReports(true)
      const response = await reportsApi.list()
      setExistingReports(response.reports)
    } catch (error) {
      console.error('Errore nel caricamento dei report:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare la lista dei report esistenti.',
      })
    } finally {
      setIsLoadingReports(false)
    }
  }

  useEffect(() => {
    fetchExistingReports()
  }, [])

  // Gestisce la generazione e download di un report
  const handleGenerateReport = async (rangeType: ReportRangeType) => {
    try {
      setIsGenerating(true)
      
      // Genera e scarica il report
      const blob = await reportsApi.generate(rangeType, includeSections, true) as Blob
      
      // Crea un URL temporaneo per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // Genera il nome del file
      const today = new Date()
      const dateStr = today.toISOString().split('T')[0]
      link.download = `report_${rangeType}_${dateStr}.pdf`
      
      // Avvia il download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Pulisce l'URL temporaneo
      window.URL.revokeObjectURL(url)
      
      toast({
        title: 'Report generato',
        description: `Report ${rangeType} scaricato con successo`,
      })
      
      // Aggiorna la lista dei report
      fetchExistingReports()
      
    } catch (error) {
      console.error('Errore nella generazione del report:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile generare il report. Riprova più tardi.',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  // Gestisce il download di un report esistente
  const handleDownloadExistingReport = async (filename: string) => {
    try {
      const blob = await reportsApi.download(filename)
      
      // Crea un URL temporaneo per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      
      // Avvia il download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Pulisce l'URL temporaneo
      window.URL.revokeObjectURL(url)
      
      toast({
        title: 'Download completato',
        description: `Report ${filename} scaricato con successo`,
      })
      
    } catch (error) {
      console.error('Errore nel download del report:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile scaricare il report. Riprova più tardi.',
      })
    }
  }

  // Gestisce il toggle delle sezioni da includere
  const handleSectionToggle = (section: ReportIncludeSection, checked: boolean | string) => {
    const isChecked = checked === true || checked === 'indeterminate'
    if (isChecked) {
      setIncludeSections(prev => [...prev, section])
    } else {
      setIncludeSections(prev => prev.filter(s => s !== section))
    }
  }

  // Formatta la dimensione del file
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Genera e scarica report PDF dettagliati sui dati di produzione
          </p>
        </div>
        <Button 
          onClick={fetchExistingReports} 
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Aggiorna Lista
        </Button>
      </div>

      {/* Sezione Generazione Report */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Genera Nuovo Report
          </CardTitle>
          <CardDescription>
            Seleziona il periodo e le sezioni da includere nel report PDF
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Opzioni sezioni da includere */}
          <div>
            <h4 className="text-sm font-medium mb-3">Sezioni Opzionali da Includere</h4>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="include-odl"
                  checked={includeSections.includes('odl')}
                  onCheckedChange={(checked) => handleSectionToggle('odl', checked as boolean)}
                />
                <label 
                  htmlFor="include-odl" 
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-2"
                >
                  <ListTodo className="h-4 w-4" />
                  Dettaglio ODL
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="include-tempi"
                  checked={includeSections.includes('tempi')}
                  onCheckedChange={(checked) => handleSectionToggle('tempi', checked as boolean)}
                />
                <label 
                  htmlFor="include-tempi" 
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-2"
                >
                  <Clock className="h-4 w-4" />
                  Tempi Fase
                </label>
              </div>
            </div>
          </div>

          {/* Pulsanti per generare report */}
          <div>
            <h4 className="text-sm font-medium mb-3">Genera Report per Periodo</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button 
                onClick={() => handleGenerateReport('giorno')}
                disabled={isGenerating}
                className="flex items-center gap-2 h-auto p-4 flex-col"
                variant="outline"
              >
                {isGenerating ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <Calendar className="h-6 w-6" />
                )}
                <div className="text-center">
                  <div className="font-medium">Report Giornaliero</div>
                  <div className="text-xs text-muted-foreground">Dati di oggi</div>
                </div>
              </Button>

              <Button 
                onClick={() => handleGenerateReport('settimana')}
                disabled={isGenerating}
                className="flex items-center gap-2 h-auto p-4 flex-col"
                variant="outline"
              >
                {isGenerating ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <CalendarDays className="h-6 w-6" />
                )}
                <div className="text-center">
                  <div className="font-medium">Report Settimanale</div>
                  <div className="text-xs text-muted-foreground">Settimana corrente</div>
                </div>
              </Button>

              <Button 
                onClick={() => handleGenerateReport('mese')}
                disabled={isGenerating}
                className="flex items-center gap-2 h-auto p-4 flex-col"
                variant="outline"
              >
                {isGenerating ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <CalendarRange className="h-6 w-6" />
                )}
                <div className="text-center">
                  <div className="font-medium">Report Mensile</div>
                  <div className="text-xs text-muted-foreground">Mese corrente</div>
                </div>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sezione Report Esistenti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Report Esistenti
          </CardTitle>
          <CardDescription>
            Scarica report generati in precedenza
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingReports ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Caricamento report...</span>
            </div>
          ) : existingReports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg text-muted-foreground mb-2">
                Nessun report disponibile
              </p>
              <p className="text-sm text-muted-foreground">
                Genera il tuo primo report utilizzando i pulsanti sopra
              </p>
            </div>
          ) : (
            <Table>
              <TableCaption>Lista dei report PDF disponibili per il download</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome File</TableHead>
                  <TableHead>Dimensione</TableHead>
                  <TableHead>Data Creazione</TableHead>
                  <TableHead>Data Modifica</TableHead>
                  <TableHead className="text-center">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {existingReports.map((report) => (
                  <TableRow key={report.filename}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-red-500" />
                        {report.filename}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {formatFileSize(report.size)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {formatDateIT(new Date(report.created_at))}
                    </TableCell>
                    <TableCell>
                      {formatDateIT(new Date(report.modified_at))}
                    </TableCell>
                    <TableCell className="text-center">
                      <Button
                        onClick={() => handleDownloadExistingReport(report.filename)}
                        size="sm"
                        variant="outline"
                        className="flex items-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        Scarica
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 