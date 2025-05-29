'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { BarChart3, Download, Calendar, TrendingUp, PieChart, RefreshCw, Filter, FileText, Eye, Loader2 } from 'lucide-react'
import { EmptyState } from '@/components/ui/EmptyState'
import { nestingApi, NestingResponse, reportsApi, ReportGenerateRequest, ReportTypeEnum } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface ReportsTabProps {
  nestingList?: NestingResponse[]
  onRefresh?: () => Promise<void>
}

export function ReportsTab({ nestingList, onRefresh }: ReportsTabProps) {
  const [reportData, setReportData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [completedNestings, setCompletedNestings] = useState<NestingResponse[]>([])
  const [filteredNestings, setFilteredNestings] = useState<NestingResponse[]>([])
  const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set())
  
  // Filtri temporali
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  
  // Stati per export
  const [exportingFormat, setExportingFormat] = useState<string | null>(null)
  const [generatingReport, setGeneratingReport] = useState(false)

  const { toast } = useToast()

  // Carica i nesting completati
  const loadCompletedNestings = async () => {
    setIsLoading(true)
    try {
      const allNestings = await nestingApi.getAll()
      
      // Filtra solo i nesting completati o finiti
      const completed = allNestings.filter(nesting => 
        ['finito', 'completato'].includes(nesting.stato.toLowerCase())
      )
      
      setCompletedNestings(completed)
      setFilteredNestings(completed)
      
      // Chiama onRefresh se fornito
      if (onRefresh) {
        await onRefresh()
      }
      
      toast({
        title: "Dati Aggiornati",
        description: `Caricati ${completed.length} nesting completati`,
      })
    } catch (error: any) {
      toast({
        title: "Errore",
        description: error?.message || "Impossibile caricare i dati dei nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Applica filtri
  const applyFilters = () => {
    let filtered = [...completedNestings]

    // Filtro per data
    if (dateFrom) {
      const fromDate = new Date(dateFrom)
      filtered = filtered.filter(nesting => 
        new Date(nesting.created_at) >= fromDate
      )
    }

    if (dateTo) {
      const toDate = new Date(dateTo)
      toDate.setHours(23, 59, 59, 999) // Fine giornata
      filtered = filtered.filter(nesting => 
        new Date(nesting.created_at) <= toDate
      )
    }

    // Filtro per stato
    if (statusFilter !== 'all') {
      filtered = filtered.filter(nesting => 
        nesting.stato.toLowerCase() === statusFilter
      )
    }

    setFilteredNestings(filtered)
  }

  // Funzione per scaricare il report di un nesting
  const handleDownloadReport = async (nesting: NestingResponse) => {
    const nestingId = parseInt(nesting.id)
    
    try {
      setDownloadingReports(prev => new Set(prev).add(nesting.id))
      
      // ✅ COLLEGATO A: POST /nesting/{id}/generate-report + GET /reports/nesting/{id}/download
      const reportInfo = await nestingApi.generateReport(nestingId)
      
      // Poi scarica il report
      const blob = await nestingApi.downloadReport(nestingId)
      
      // Crea un link per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = reportInfo.filename || `nesting_${nesting.id}_report.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Report Scaricato",
        description: `Report del nesting ${nesting.id.substring(0, 8)}... scaricato con successo`,
      })
    } catch (error: any) {
      // Gestione errori API non implementate
      if (error?.status === 404 || error?.status === 501) {
        toast({
          title: "Funzionalità in Sviluppo",
          description: `Il download del report per il nesting ${nesting.id.substring(0, 8)}... sarà disponibile a breve. Le API sono in fase di implementazione.`,
          variant: "default",
        })
      } else {
        toast({
          title: "Errore",
          description: "Impossibile scaricare il report",
          variant: "destructive",
        })
      }
    } finally {
      setDownloadingReports(prev => {
        const newSet = new Set(prev)
        newSet.delete(nesting.id)
        return newSet
      })
    }
  }

  // Carica i dati al primo render
  useEffect(() => {
    loadCompletedNestings()
  }, [])

  // Applica filtri quando cambiano
  useEffect(() => {
    applyFilters()
  }, [dateFrom, dateTo, statusFilter, completedNestings])

  // Calcola statistiche dai dati reali
  const calculateStats = () => {
    const total = completedNestings.length
    const byStatus = completedNestings.reduce((acc, nesting) => {
      const status = nesting.stato.toLowerCase()
      acc[status] = (acc[status] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const totalEfficiency = completedNestings.reduce((sum, nesting) => 
      sum + (nesting.efficienza || 0), 0
    )
    const averageEfficiency = total > 0 ? totalEfficiency / total : 0

    const totalTools = completedNestings.reduce((sum, nesting) => 
      sum + (nesting.odl_inclusi || 0), 0
    )

    const completed = byStatus.finito || byStatus.completato || 0

    return {
      total,
      byStatus,
      averageEfficiency,
      totalTools,
      completed
    }
  }

  const stats = calculateStats()

  // Genera report dettagliato utilizzando l'API reale
  const generateDetailedReport = async () => {
    setGeneratingReport(true)
    
    try {
      // Prepara i parametri per il report
      const reportRequest: ReportGenerateRequest = {
        report_type: 'completo' as ReportTypeEnum,
        range_type: 'mese',
        start_date: dateFrom || undefined,
        end_date: dateTo || undefined,
        include_sections: ['odl', 'tempi', 'header'],
        download: true
      }

      // ✅ COLLEGATO A: POST /reports/generate
      const reportInfo = await reportsApi.generate(reportRequest)
      
      // Scarica automaticamente il report generato
      const blob = await reportsApi.downloadById(reportInfo.report_id)
      
      // Crea un link per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = reportInfo.file_name || 'report_nesting_dettagliato.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Report Generato",
        description: `Report dettagliato scaricato con successo: ${reportInfo.file_name}`,
      })
    } catch (error: any) {
      // ✅ MIGLIORATO: Gestione errori più specifica
      console.error('Dettaglio errore generazione report:', error)
      
      if (error?.status === 404 || error?.status === 501) {
        toast({
          title: "🔧 Funzionalità in Sviluppo",
          description: "La generazione di report dettagliati sarà disponibile a breve. Le API sono in fase di implementazione.",
          variant: "default",
        })
      } else if (error?.status === 500) {
        toast({
          title: "Errore Server",
          description: "Errore interno del server durante la generazione del report. Riprova più tardi.",
          variant: "destructive",
        })
      } else {
        toast({
          title: "Errore",
          description: error?.message || "Impossibile generare il report dettagliato. Verifica che ci siano dati disponibili.",
          variant: "destructive",
        })
      }
    } finally {
      setGeneratingReport(false)
    }
  }

  // Esporta dati in diversi formati utilizzando le API reali
  const exportData = async (format: 'csv' | 'excel' | 'pdf') => {
    setExportingFormat(format)
    
    try {
      let fileName: string
      let blob: Blob
      
      // Prepara i parametri per l'export
      const exportParams = {
        start_date: dateFrom || undefined,
        end_date: dateTo || undefined,
        nesting_ids: filteredNestings.length > 0 ? filteredNestings.map(n => parseInt(n.id)) : undefined
      }

      // Determina il formato e chiama l'API specifica
      switch (format) {
        case 'csv':
          fileName = `nesting_export_${new Date().toISOString().split('T')[0]}.csv`
          blob = await reportsApi.exportCSV(exportParams)
          break
        case 'excel':
          fileName = `nesting_export_${new Date().toISOString().split('T')[0]}.xlsx`
          blob = await reportsApi.exportExcel(exportParams)
          break
        case 'pdf':
          fileName = `nesting_export_${new Date().toISOString().split('T')[0]}.pdf`
          blob = await reportsApi.exportPDF(exportParams)
          break
        default:
          throw new Error(`Formato non supportato: ${format}`)
      }
      
      // Crea un link per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Export Completato",
        description: `File ${format.toUpperCase()} scaricato con successo: ${fileName}`,
      })
    } catch (error: any) {
      // ✅ MIGLIORATO: Gestione errori più specifica per export
      console.error(`Dettaglio errore export ${format}:`, error)
      
      if (error?.status === 404 || error?.status === 501) {
        toast({
          title: "🔧 Funzionalità in Sviluppo",
          description: `L'export in formato ${format.toUpperCase()} sarà disponibile a breve. Stiamo lavorando all'implementazione delle API di esportazione.`,
          variant: "default",
        })
      } else if (error?.status === 500) {
        toast({
          title: "Errore Server", 
          description: `Errore interno durante l'export ${format.toUpperCase()}. Il server potrebbe essere sovraccarico.`,
          variant: "destructive",
        })
      } else if (error?.message?.includes('Failed to fetch')) {
        toast({
          title: "Connessione Persa",
          description: `Impossibile contattare il server per l'export ${format.toUpperCase()}. Verifica la connessione.`,
          variant: "destructive",
        })
      } else {
        toast({
          title: "Errore Export",
          description: error?.message || `Impossibile esportare i dati in formato ${format.toUpperCase()}. Riprova più tardi.`,
          variant: "destructive",
        })
      }
    } finally {
      setExportingFormat(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Statistiche principali */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Totale Nesting</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Efficienza Media</p>
                <p className="text-2xl font-bold">{stats.averageEfficiency.toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Tool Processati</p>
                <p className="text-2xl font-bold">{stats.totalTools}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completati</p>
                <p className="text-2xl font-bold">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-indigo-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Report Disponibili</p>
                <p className="text-2xl font-bold">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtri temporali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri Report
          </CardTitle>
          <CardDescription>
            Filtra i nesting completati per periodo e stato
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="dateFrom">Data Inizio</Label>
              <Input
                id="dateFrom"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="dateTo">Data Fine</Label>
              <Input
                id="dateTo"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="statusFilter">Stato</Label>
              <select
                id="statusFilter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Tutti gli stati</option>
                <option value="finito">Finito</option>
                <option value="completato">Completato</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button
                onClick={loadCompletedNestings}
                disabled={isLoading}
                className="w-full flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Aggiorna
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabella nesting completati con report */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Nesting Completati - Report Disponibili
          </CardTitle>
          <CardDescription>
            Visualizza e scarica i report dei nesting completati ({filteredNestings.length} risultati)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredNestings.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID Nesting</TableHead>
                    <TableHead>Autoclave</TableHead>
                    <TableHead>Stato</TableHead>
                    <TableHead>ODL</TableHead>
                    <TableHead>Peso (kg)</TableHead>
                    <TableHead>Efficienza</TableHead>
                    <TableHead>Data Completamento</TableHead>
                    <TableHead className="text-right">Azioni</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredNestings.map((nesting) => (
                    <TableRow key={nesting.id}>
                      <TableCell className="font-medium">
                        #{nesting.id.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {nesting.autoclave_nome || "Autoclave non specificata"}
                          </span>
                          {nesting.ciclo_cura && (
                            <span className="text-xs text-muted-foreground">
                              {nesting.ciclo_cura}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={nesting.stato.toLowerCase() === 'completato' ? 'default' : 'secondary'}>
                          {nesting.stato}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {nesting.odl_inclusi || 0} inclusi
                          </span>
                          {nesting.odl_esclusi && nesting.odl_esclusi > 0 && (
                            <span className="text-xs text-muted-foreground">
                              {nesting.odl_esclusi} esclusi
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">
                          {nesting.peso_totale ? `${nesting.peso_totale.toFixed(1)} kg` : "Peso non disponibile"}
                        </span>
                      </TableCell>
                      <TableCell>
                        {nesting.efficienza !== undefined && nesting.efficienza > 0 ? (
                          <span className={`font-medium ${
                            nesting.efficienza >= 70 ? 'text-green-600' : 
                            nesting.efficienza >= 50 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {nesting.efficienza.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Efficienza non calcolata</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {new Date(nesting.created_at).toLocaleDateString('it-IT')}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center gap-2 justify-end">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadReport(nesting)}
                            disabled={downloadingReports.has(nesting.id)}
                            className="flex items-center gap-2"
                          >
                            {downloadingReports.has(nesting.id) ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                            {downloadingReports.has(nesting.id) ? 'Generando...' : 'Scarica'}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <EmptyState
              message="Nessun nesting completato"
              description={
                isLoading 
                  ? "Caricamento dati in corso..." 
                  : completedNestings.length === 0 
                    ? "Non ci sono ancora nesting completati nel sistema. Completa alcuni nesting per vedere i report qui." 
                    : "Nessun nesting soddisfa i filtri impostati. Prova a modificare i criteri di ricerca."
              }
              icon="📊"
            />
          )}
        </CardContent>
      </Card>

      {/* Distribuzione per stato */}
      <Card>
        <CardHeader>
          <CardTitle>Distribuzione per Stato</CardTitle>
          <CardDescription>
            Panoramica dello stato attuale di tutti i nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(stats.byStatus).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    status === 'bozza' ? 'bg-gray-400' :
                    status === 'confermato' ? 'bg-orange-500' :
                    status === 'sospeso' ? 'bg-yellow-500' :
                    status === 'cura' || status === 'in_corso' ? 'bg-blue-500' :
                    status === 'finito' || status === 'completato' ? 'bg-green-500' : 'bg-gray-400'
                  }`}></div>
                  <span className="capitalize font-medium">{status.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">{count}</span>
                  <span className="text-sm text-muted-foreground">
                    ({((count / stats.total) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Azioni report */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Generazione Report
            </CardTitle>
            <CardDescription>
              Genera report dettagliati sull'andamento del nesting
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={generateDetailedReport}
              disabled={generatingReport}
              className="w-full"
              size="lg"
            >
              {generatingReport ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Generazione in corso...
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Genera Report Dettagliato
                </>
              )}
            </Button>
            
            <div className="text-sm text-muted-foreground">
              <p>Il report includerà:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Analisi dell'efficienza nel tempo</li>
                <li>Utilizzo delle autoclavi</li>
                <li>Tempi di processamento</li>
                <li>Trend di ottimizzazione</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Esportazione Dati
            </CardTitle>
            <CardDescription>
              Esporta i dati in diversi formati per analisi esterne
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <Button
                variant="outline"
                onClick={() => exportData('csv')}
                disabled={exportingFormat !== null}
                className="flex flex-col items-center gap-1 h-auto py-3"
              >
                {exportingFormat === 'csv' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                <span className="text-xs">
                  {exportingFormat === 'csv' ? 'Generando...' : 'CSV'}
                </span>
              </Button>
              <Button
                variant="outline"
                onClick={() => exportData('excel')}
                disabled={exportingFormat !== null}
                className="flex flex-col items-center gap-1 h-auto py-3"
              >
                {exportingFormat === 'excel' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                <span className="text-xs">
                  {exportingFormat === 'excel' ? 'Generando...' : 'Excel'}
                </span>
              </Button>
              <Button
                variant="outline"
                onClick={() => exportData('pdf')}
                disabled={exportingFormat !== null}
                className="flex flex-col items-center gap-1 h-auto py-3"
              >
                {exportingFormat === 'pdf' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                <span className="text-xs">
                  {exportingFormat === 'pdf' ? 'Generando...' : 'PDF'}
                </span>
              </Button>
            </div>
            
            <div className="text-sm text-muted-foreground">
              <p>Formati disponibili:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>CSV:</strong> Dati grezzi per analisi</li>
                <li><strong>Excel:</strong> Tabelle formattate</li>
                <li><strong>PDF:</strong> Report stampabile</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Informazioni sui report */}
      <Card>
        <CardHeader>
          <CardTitle>Informazioni sui Report</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">📊 Metriche Disponibili</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
              <ul className="space-y-1">
                <li>• Efficienza di utilizzo autoclavi</li>
                <li>• Tempi medi di processamento</li>
                <li>• Distribuzione dei tool per dimensione</li>
                <li>• Trend di ottimizzazione nel tempo</li>
              </ul>
              <ul className="space-y-1">
                <li>• Analisi dei colli di bottiglia</li>
                <li>• Confronto prestazioni per autoclave</li>
                <li>• Statistiche di completamento ODL</li>
                <li>• Indicatori di performance (KPI)</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 