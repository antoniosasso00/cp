'use client'

import React, { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { ThemeSelector } from '@/components/ui/theme-toggle'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { 
  Settings, 
  Palette, 
  Database, 
  Download, 
  Upload, 
  Zap,
  AlertTriangle,
  CheckCircle,
  Info,
  Loader2,
  Trash2
} from 'lucide-react'
import { useUserRole } from '@/hooks/useUserRole'

export default function ImpostazioniPage() {
  const { toast } = useToast()
  const { role } = useUserRole()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [isExporting, setIsExporting] = useState(false)
  const [isRestoring, setIsRestoring] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [resetConfirmation, setResetConfirmation] = useState('')
  const [showResetDialog, setShowResetDialog] = useState(false)

  /**
   * Gestisce l'esportazione del database
   */
  const handleExportDatabase = async () => {
    setIsExporting(true)
    
    try {
      const response = await fetch('/api/v1/admin/backup', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`)
      }

      // Ottieni il nome del file dall'header Content-Disposition
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'carbonpilot_backup.json'
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      // Scarica il file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: "✅ Backup completato",
        description: `Database esportato con successo: ${filename}`,
      })

    } catch (error) {
      console.error('Errore durante l\'esportazione:', error)
      toast({
        title: "❌ Errore nell'esportazione",
        description: error instanceof Error ? error.message : "Errore sconosciuto",
        variant: "destructive",
      })
    } finally {
      setIsExporting(false)
    }
  }

  /**
   * Gestisce la selezione del file per il ripristino
   */
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.json')) {
        toast({
          title: "❌ File non valido",
          description: "Seleziona un file JSON di backup valido",
          variant: "destructive",
        })
        return
      }
      setSelectedFile(file)
    }
  }

  /**
   * Gestisce il ripristino del database
   */
  const handleRestoreDatabase = async () => {
    if (!selectedFile) {
      toast({
        title: "❌ Nessun file selezionato",
        description: "Seleziona un file di backup prima di procedere",
        variant: "destructive",
      })
      return
    }

    setIsRestoring(true)

    try {
      const formData = new FormData()
      formData.append('backup_file', selectedFile)

      const response = await fetch('/api/v1/admin/restore', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || `Errore HTTP: ${response.status}`)
      }

      toast({
        title: "✅ Ripristino completato",
        description: `Database ripristinato con successo. ${result.total_tables} tabelle ripristinate.`,
      })

      // Reset del file selezionato
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Mostra dettagli se ci sono errori
      if (result.errors && result.errors.length > 0) {
        console.warn('Errori durante il ripristino:', result.errors)
        toast({
          title: "⚠️ Ripristino con avvisi",
          description: `${result.total_errors} errori riscontrati. Controlla la console per i dettagli.`,
          variant: "destructive",
        })
      }

    } catch (error) {
      console.error('Errore durante il ripristino:', error)
      toast({
        title: "❌ Errore nel ripristino",
        description: error instanceof Error ? error.message : "Errore sconosciuto",
        variant: "destructive",
      })
    } finally {
      setIsRestoring(false)
    }
  }

  /**
   * Gestisce il reset completo del database
   */
  const handleResetDatabase = async () => {
    if (resetConfirmation !== 'reset') {
      toast({
        title: "❌ Conferma non valida",
        description: "Inserisci esattamente 'reset' per confermare l'operazione",
        variant: "destructive",
      })
      return
    }

    setIsResetting(true)

    try {
      const response = await fetch('/api/v1/admin/database/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          confirmation: resetConfirmation
        }),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || `Errore HTTP: ${response.status}`)
      }

      toast({
        title: "✅ Database svuotato",
        description: `Database resettato con successo. ${result.total_deleted_records} record eliminati da ${result.total_tables_reset} tabelle.`,
      })

      // Reset del campo di conferma e chiudi dialog
      setResetConfirmation('')
      setShowResetDialog(false)

      // Mostra dettagli se ci sono errori
      if (result.errors && result.errors.length > 0) {
        console.warn('Errori durante il reset:', result.errors)
        toast({
          title: "⚠️ Reset con avvisi",
          description: `${result.total_errors} errori riscontrati. Controlla la console per i dettagli.`,
          variant: "destructive",
        })
      }

    } catch (error) {
      console.error('Errore durante il reset:', error)
      toast({
        title: "❌ Errore nel reset",
        description: error instanceof Error ? error.message : "Errore sconosciuto",
        variant: "destructive",
      })
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Impostazioni</h1>
          <p className="text-muted-foreground">
            Configura le preferenze dell'applicazione Manta Group
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Sezione Tema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Aspetto e Tema
            </CardTitle>
            <CardDescription>
              Personalizza l'aspetto dell'interfaccia utente
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-3">Modalità del tema</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Scegli il tema dell'interfaccia. La modalità "Sistema" seguirà le preferenze del tuo dispositivo.
              </p>
              <ThemeSelector />
            </div>
          </CardContent>
        </Card>

        {/* Sezione Database - Backup e Ripristino */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Gestione Database
            </CardTitle>
            <CardDescription>
              Backup e ripristino del database dell'applicazione
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Informazioni Database */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tipo database:</span>
                <span className="text-sm text-muted-foreground">SQLite (Sviluppo)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Stato connessione:</span>
                <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Connesso
                </span>
              </div>
            </div>

            <Separator />

            {/* Sezione Backup */}
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Esporta Database
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Crea un backup completo del database in formato JSON. Il file conterrà tutti i dati delle tabelle.
                </p>
                <Button 
                  onClick={handleExportDatabase}
                  disabled={isExporting}
                  className="w-full sm:w-auto"
                >
                  {isExporting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Esportazione in corso...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Esporta Database
                    </>
                  )}
                </Button>
              </div>

              <Separator />

              {/* Sezione Ripristino */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Upload className="h-4 w-4" />
                    Ripristina Database
                  </h3>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-yellow-800 dark:text-yellow-200">
                          Attenzione: Operazione irreversibile
                        </p>
                        <p className="text-yellow-700 dark:text-yellow-300 mt-1">
                          Il ripristino sostituirà completamente tutti i dati esistenti nel database. 
                          Assicurati di aver fatto un backup prima di procedere.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="backup-file">Seleziona file di backup (JSON)</Label>
                  <Input
                    id="backup-file"
                    type="file"
                    accept=".json"
                    onChange={handleFileSelect}
                    ref={fileInputRef}
                    className="cursor-pointer"
                  />
                  
                  {selectedFile && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Info className="h-4 w-4" />
                      <span>File selezionato: {selectedFile.name}</span>
                    </div>
                  )}

                  <Button 
                    onClick={handleRestoreDatabase}
                    disabled={!selectedFile || isRestoring}
                    variant="destructive"
                    className="w-full sm:w-auto"
                  >
                    {isRestoring ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Ripristino in corso...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-4 w-4" />
                        Ripristina Database
                      </>
                    )}
                  </Button>
                </div>

                <Separator />

                {/* Sezione Reset Database */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                      <Trash2 className="h-4 w-4 text-red-500" />
                      Reset Database
                    </h3>
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5" />
                        <div className="text-sm">
                          <p className="font-medium text-red-800 dark:text-red-200">
                            ⚠️ ATTENZIONE: Operazione IRREVERSIBILE
                          </p>
                          <p className="text-red-700 dark:text-red-300 mt-1">
                            Il reset eliminerà TUTTI i dati dal database. Questa operazione non può essere annullata.
                            Assicurati di aver fatto un backup prima di procedere.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Dialog open={showResetDialog} onOpenChange={setShowResetDialog}>
                    <DialogTrigger asChild>
                      <Button 
                        variant="destructive"
                        className="w-full sm:w-auto"
                        onClick={() => setShowResetDialog(true)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Reset Database
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                          <Trash2 className="h-5 w-5 text-red-500" />
                          Conferma Reset Database
                        </DialogTitle>
                        <DialogDescription>
                          Questa operazione eliminerà TUTTI i dati dal database in modo permanente.
                          Per confermare, inserisci esattamente la parola <strong>"reset"</strong> nel campo sottostante.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="reset-confirmation">
                            Inserisci "reset" per confermare:
                          </Label>
                          <Input
                            id="reset-confirmation"
                            value={resetConfirmation}
                            onChange={(e) => setResetConfirmation(e.target.value)}
                            placeholder="Scrivi: reset"
                            className="w-full"
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button 
                          variant="outline" 
                          onClick={() => {
                            setShowResetDialog(false)
                            setResetConfirmation('')
                          }}
                        >
                          Annulla
                        </Button>
                        <Button 
                          variant="destructive"
                          onClick={handleResetDatabase}
                          disabled={resetConfirmation !== 'reset' || isResetting}
                        >
                          {isResetting ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Reset in corso...
                            </>
                          ) : (
                            <>
                              <Trash2 className="mr-2 h-4 w-4" />
                              Conferma Reset
                            </>
                          )}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sezione Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Prestazioni e Aggiornamenti
            </CardTitle>
            <CardDescription>
              Configurazioni relative alla velocità e al refresh dell'applicazione
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Aggiornamento automatico:</span>
                <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Attivo
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Refresh cache:</span>
                <span className="text-sm text-muted-foreground">5 secondi</span>
              </div>
              <Separator />
              <p className="text-xs text-muted-foreground">
                📈 Gli ODL e Tool vengono aggiornati automaticamente per mantenere i dati sincronizzati tra le fasi di produzione.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Informazioni Ruolo */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Informazioni Accesso
            </CardTitle>
            <CardDescription>
              Dettagli sul tuo ruolo e permessi attuali
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Ruolo attuale:</span>
                <span className="text-sm font-medium text-primary">
                  {role || 'Nessun ruolo selezionato'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Accesso impostazioni:</span>
                <span className="text-sm text-green-600 font-medium">
                  ✅ Consentito
                </span>
              </div>
              <Separator />
              <p className="text-xs text-muted-foreground">
                💡 Le impostazioni sono accessibili a tutti i ruoli. Le funzionalità di backup e ripristino 
                sono disponibili per la gestione dei dati dell'applicazione.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 