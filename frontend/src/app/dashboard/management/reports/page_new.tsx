'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { 
  reportsApi, 
  ReportRangeType, 
  ReportIncludeSection, 
  ReportFileInfo, 
  ReportTypeEnum,
  ReportGenerateRequest 
} from '@/lib/api'
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
  ListTodo,
  Filter,
  Search,
  Settings,
  BarChart3,
  CheckCircle,
  Timer,
  Package
} from 'lucide-react'

export default function ReportsPage() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [reportType, setReportType] = useState<ReportTypeEnum>('nesting')
  const [rangeType, setRangeType] = useState<ReportRangeType>('giorno')
  const [includeSections, setIncludeSections] = useState<ReportIncludeSection[]>([])
  const [odlFilter, setOdlFilter] = useState('')
  const [existingReports, setExistingReports] = useState<ReportFileInfo[]>([])
  const [isLoadingReports, setIsLoadingReports] = useState(true)
  
  // Filtri per la lista report
  const [filterReportType, setFilterReportType] = useState<ReportTypeEnum | ''>('')
  const [filterOdl, setFilterOdl] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  
  const { toast } = useToast()

  // Carica la lista dei report esistenti
  const fetchExistingReports = async () => {
    try {
      setIsLoadingReports(true)
      const params: any = {}
      
      if (filterReportType) {
        params.report_type = filterReportType
      }
      if (filterOdl) {
        params.odl_filter = filterOdl
      }
      
      const response = await reportsApi.list(params)
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
  }, [filterReportType, filterOdl])

  // Gestisce la generazione di un report
  const handleGenerateReport = async () => {
    try {
      setIsGenerating(true)
      
      const request: ReportGenerateRequest = {
        report_type: reportType,
        range_type: rangeType,
        include_sections: includeSections.length > 0 ? includeSections : undefined,
        odl_filter: odlFilter || undefined,
        download: false
      }
      
      const response = await reportsApi.generate(request)
      
      toast({
        title: 'Report generato',
        description: `Report ${reportType} creato con successo: ${response.file_name}`,
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
  const handleDownloadReport = async (report: ReportFileInfo) => {
    try {
      const blob = await reportsApi.downloadById(report.id)
      
      // Crea un URL temporaneo per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = report.filename
      
      // Avvia il download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Pulisce l'URL temporaneo
      window.URL.revokeObjectURL(url)
      
      toast({
        title: 'Download completato',
        description: `Report ${report.filename} scaricato con successo`,
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
  const formatFileSize = (bytes?: number) => {
    if (!bytes || bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Icone per i tipi di report
  const getReportTypeIcon = (type: ReportTypeEnum) => {
    switch (type) {
      case 'produzione': return <Package className="h-4 w-4" />
      case 'qualita': return <CheckCircle className="h-4 w-4" />
      case 'tempi': return <Timer className="h-4 w-4" />
      case 'completo': return <BarChart3 className="h-4 w-4" />
      case 'nesting': return <Settings className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  // Badge colore per tipo report
  const getReportTypeBadge = (type: ReportTypeEnum) => {
    const variants: Record<ReportTypeEnum, string> = {
      'produzione': 'bg-blue-100 text-blue-800',
      'qualita': 'bg-green-100 text-green-800',
      'tempi': 'bg-orange-100 text-orange-800',
      'completo': 'bg-purple-100 text-purple-800',
      'nesting': 'bg-indigo-100 text-indigo-800'
    }
    
    return (
      <Badge className={variants[type]}>
        {getReportTypeIcon(type)}
        <span className="ml-1">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports PDF</h1>
          <p className="text-muted-foreground">
            Genera e gestisci report PDF personalizzati per analisi di produzione
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
            Configura e genera un report PDF personalizzato con dati di produzione
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Selezione tipo di report */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="report-type">Tipo di Report</Label>
              <Select value={reportType} onValueChange={(value: ReportTypeEnum) => setReportType(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona tipo di report" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="nesting">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Nesting
                    </div>
                  </SelectItem>
                  <SelectItem value="produzione">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4" />
                      Produzione
                    </div>
                  </SelectItem>
                  <SelectItem value="qualita">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      Qualità
                    </div>
                  </SelectItem>
                  <SelectItem value="tempi">
                    <div className="flex items-center gap-2">
                      <Timer className="h-4 w-4" />
                      Tempi
                    </div>
                  </SelectItem>
                  <SelectItem value="completo">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Completo
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="range-type">Periodo</Label>
              <Select value={rangeType} onValueChange={(value: ReportRangeType) => setRangeType(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona periodo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="giorno">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      Giorno corrente
                    </div>
                  </SelectItem>
                  <SelectItem value="settimana">
                    <div className="flex items-center gap-2">
                      <CalendarDays className="h-4 w-4" />
                      Settimana corrente
                    </div>
                  </SelectItem>
                  <SelectItem value="mese">
                    <div className="flex items-center gap-2">
                      <CalendarRange className="h-4 w-4" />
                      Mese corrente
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Filtro ODL */}
          <div className="space-y-2">
            <Label htmlFor="odl-filter">Filtro ODL/Part Number (opzionale)</Label>
            <Input
              id="odl-filter"
              placeholder="Inserisci ID ODL o Part Number per filtrare i dati..."
              value={odlFilter}
              onChange={(e) => setOdlFilter(e.target.value)}
            />
          </div>

          {/* Sezioni opzionali */}
          <div>
            <Label className="text-sm font-medium mb-3 block">Sezioni Aggiuntive (opzionali)</Label>
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

          <Separator />

          {/* Pulsante generazione */}
          <div className="flex justify-center">
            <Button 
              onClick={handleGenerateReport}
              disabled={isGenerating}
              size="lg"
              className="flex items-center gap-2"
            >
              {isGenerating ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <FileText className="h-5 w-5" />
              )}
              {isGenerating ? 'Generazione in corso...' : 'Genera Report'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Sezione Report Esistenti */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Report Esistenti
              </CardTitle>
              <CardDescription>
                Visualizza e scarica i report generati in precedenza
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filtri
            </Button>
          </div>
          
          {/* Filtri */}
          {showFilters && (
            <div className="mt-4 p-4 border rounded-lg bg-muted/50">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="filter-type">Filtra per Tipo</Label>
                  <Select value={filterReportType || 'all'} onValueChange={(value) => setFilterReportType(value === 'all' ? '' : value as ReportTypeEnum)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tutti i tipi" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tutti i tipi</SelectItem>
                      <SelectItem value="nesting">Nesting</SelectItem>
                      <SelectItem value="produzione">Produzione</SelectItem>
                      <SelectItem value="qualita">Qualità</SelectItem>
                      <SelectItem value="tempi">Tempi</SelectItem>
                      <SelectItem value="completo">Completo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="filter-odl">Filtra per ODL/PN</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="filter-odl"
                      placeholder="Cerca ODL o Part Number..."
                      value={filterOdl}
                      onChange={(e) => setFilterOdl(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
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
                Genera il tuo primo report utilizzando il modulo sopra
              </p>
            </div>
          ) : (
            <Table>
              <TableCaption>Lista dei report PDF disponibili per il download</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Nome File</TableHead>
                  <TableHead>Periodo</TableHead>
                  <TableHead>Dimensione</TableHead>
                  <TableHead>Data Creazione</TableHead>
                  <TableHead className="text-center">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {existingReports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>
                      {getReportTypeBadge(report.report_type)}
                    </TableCell>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-red-500" />
                        {report.filename}
                      </div>
                    </TableCell>
                    <TableCell>
                      {report.period_start && report.period_end ? (
                        <div className="text-sm">
                          <div>{formatDateIT(new Date(report.period_start))}</div>
                          <div className="text-muted-foreground">
                            → {formatDateIT(new Date(report.period_end))}
                          </div>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">N/A</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {formatFileSize(report.file_size_bytes)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {formatDateIT(new Date(report.created_at))}
                    </TableCell>
                    <TableCell className="text-center">
                      <Button
                        onClick={() => handleDownloadReport(report)}
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